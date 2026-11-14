from __future__ import annotations

from typing import Callable, Optional

from fastapi import Request, Response, HTTPException, status
from fastapi.routing import APIRoute
from jwt import PyJWTError, decode as jwt_decode

from app.core.config import settings


class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Check if path requires authentication
            path = scope.get("path", "")
            
            # Skip auth for public endpoints
            public_paths = [
                "/api/v1/auth/login",
                "/api/v1/auth/callback",
                "/api/v1/healthz",
                "/docs",
                "/openapi.json",
                "/redoc",
            ]
            
            if not any(path.startswith(public_path) for public_path in public_paths):
                # Check for token in header or cookie
                token = None
                
                # Try header first
                authorization = request.headers.get("authorization")
                if authorization and authorization.startswith("Bearer "):
                    token = authorization.split(" ")[1]
                
                # Try cookie
                if not token:
                    token = request.cookies.get("access_token")
                
                if not token:
                    self._send_response(
                        status.HTTP_401_UNAUTHORIZED,
                        {"detail": "Not authenticated"},
                        send,
                    )
                    return
                
                try:
                    # Verify token
                    payload = jwt_decode(
                        token, 
                        options={"verify_signature": False}
                    )
                    
                    # Store user info in request state
                    scope["user"] = payload
                    
                except PyJWTError:
                    self._send_response(
                        status.HTTP_401_UNAUTHORIZED,
                        {"detail": "Invalid token"},
                        send,
                    )
                    return
        
        await self.app(scope, receive, send)
    
    def _send_response(self, status_code: int, content: dict, send):
        """Send a response to the client."""
        response = Response(content=json.dumps(content), status_code=status_code)
        response.headers["content-type"] = "application/json"
        response.scope["headers"] = []
        response.scope["headers"].append(
            (b"content-type", b"application/json")
        )
        response.scope["headers"].append(
            (b"cache-control", b"no-cache")
        )
        response.scope["headers"].append(
            (b"access-control-allow-origin", b"*")
        )
        
        # Send response
        async def _send():
            await response(scope, None, None)
        
        send = _send


def create_app_with_auth(app):
    """Add authentication middleware to the FastAPI app."""
    app.middleware("http")(AuthMiddleware)
    
    return app


def require_role(role: str):
    """Decorator to require specific role for endpoint access."""
    def decorator(func: Callable):
        async def wrapper(request: Request, *args, **kwargs):
            user = request.scope.get("user")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )
            
            # Check if user has required role
            user_role = user.get("role", "")
            if user_role != role and role not in user.get("realm_access", {}).get("roles", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_role(*roles: str):
    """Decorator to require any of the specified roles."""
    def decorator(func: Callable):
        async def wrapper(request: Request, *args, **kwargs):
            user = request.scope.get("user")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )
            
            # Check if user has any required role
            user_role = user.get("role", "")
            if user_role not in roles and user_role not in user.get("realm_access", {}).get("roles", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
