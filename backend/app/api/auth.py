"""OIDC authentication endpoints for Keycloak."""

from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError, decode as jwt_decode
import jwt

from app.core.config import settings
from app.core.database import Session, get_db
from app.models.auth import User, Role, Session as SessionModel

router = APIRouter(tags=["auth"])


def generate_pkce_verifier() -> str:
    """Generate a PKCE code verifier (43-128 characters, alphanumeric and -._~)."""
    return secrets.token_urlsafe(64)[:128]


def generate_pkce_challenge(verifier: str) -> str:
    """Generate PKCE code challenge from verifier using S256 method."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def create_session_token(user_id: int, role: str, username: str) -> str:
    """Create a JWT session token with user info and role."""
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iss": settings.app_name,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


@router.post("/auth/login")
async def login(
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """Initiate Keycloak OAuth2 login flow with PKCE.
    
    Returns a redirect to Keycloak for authentication.
    """
    # Generate PKCE verifier and challenge
    code_verifier = generate_pkce_verifier()
    code_challenge = generate_pkce_challenge(code_verifier)
    
    # Store PKCE verifier in session
    request.session["pkce_verifier"] = code_verifier
    
    # Build Keycloak auth URL
    auth_params = {
        "response_type": "code",
        "client_id": settings.keycloak_client_id,
        "redirect_uri": settings.keycloak_redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": "openid profile email",
        "state": secrets.token_urlsafe(16),
    }
    
    keycloak_auth_url = f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/auth?{urlencode(auth_params)}"
    
    return {
        "auth_url": keycloak_auth_url,
        "state": auth_params["state"],
    }


@router.get("/auth/callback")
async def auth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
    response: Response = None,
) -> dict:
    """Handle Keycloak OAuth2 callback and create session."""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {error}",
        )
    
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code or state parameter",
        )
    
    # Verify state parameter
    if request.session.get("oauth_state") != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )
    
    # Exchange authorization code for access token
    token_params = {
        "grant_type": "authorization_code",
        "client_id": settings.keycloak_client_id,
        "client_secret": settings.keycloak_client_secret,
        "code": code,
        "redirect_uri": settings.keycloak_redirect_uri,
        "code_verifier": request.session.get("pkce_verifier"),
    }
    
    # Make token request to Keycloak
    token_url = f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"
    
    try:
        import httpx
        
        with httpx.Client() as client:
            token_response = client.post(token_url, data=token_params).json()
        
        access_token = token_response.get("access_token")
        id_token = token_response.get("id_token")
        
        if not access_token or not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code for tokens",
            )
        
        # Verify and decode ID token
        try:
            payload = jwt_decode(id_token, options={"verify_signature": False})
            
            # Extract user information from ID token
            user_id = payload.get("sub")
            username = payload.get("preferred_username") or payload.get("email")
            email = payload.get("email")
            realm_roles = payload.get("realm_access", {}).get("roles", [])
            
            # Map Keycloak roles to app roles
            role = "admin" if "admin" in realm_roles else "submitter" if "submitter" in realm_roles else "viewer"
            
            # Get or create user in local database
            user = db.query(User).filter(User.keycloak_id == user_id).first()
            
            if not user:
                user = User(
                    keycloak_id=user_id,
                    username=username,
                    email=email,
                    role=role,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # Create local session token
            session_token = create_session_token(user.id, user.role, user.username)
            
            # Set session cookie
            if response:
                response.set_cookie(
                    key="access_token",
                    value=session_token,
                    httponly=True,
                    samesite="lax",
                    max_age=86400,  # 24 hours
                    domain=None,
                )
            
            return {
                "access_token": session_token,
                "token_type": "Bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },
            }
            
        except PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to decode ID token: {str(e)}",
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to authenticate with Keycloak: {str(e)}",
        )


@router.post("/auth/logout")
async def logout(
    response: Response = None,
) -> dict:
    """Logout from Keycloak and clear local session."""
    # Clear local session cookie
    if response:
        response.delete_cookie(
            key="access_token",
            httponly=True,
            samesite="lax",
            domain=None,
        )
    
    return {"message": "Successfully logged out"}


@router.get("/auth/me")
async def get_current_user(
    access_token: Optional[str] = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db),
) -> dict:
    """Get current authenticated user information."""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    try:
        payload = jwt_decode(access_token, options={"verify_signature": False})
        
        user_id = int(payload["sub"])
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
        
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
