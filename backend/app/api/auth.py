"""OIDC authentication endpoints for Keycloak (authorization code flow + PKCE).

This module contains the two pieces of the flow that are testable without a
live identity provider:

* :func:`generate_pkce_pair` — RFC 7636 verifier/challenge generation.
* :func:`validate_callback_params` — RFC 6749 §4.1.2 callback validation,
  including the ``state`` CSRF check and PKCE verifier presence.

The full login/callback/logout HTTP wiring (token exchange, ID-token
verification, cookie issuance) is intentionally *not* implemented yet; see
PLAN.md for the remaining auth-oidc work.
"""

from __future__ import annotations

import base64
import hashlib
import random
import secrets
from dataclasses import dataclass
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["auth"])

# RFC 7636 §4.1: code_verifier is 43-128 chars of [A-Za-z0-9-._~].
PKCE_MIN_VERIFIER_LENGTH = 43
PKCE_MAX_VERIFIER_LENGTH = 128
_VERIFIER_ALPHABET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '.', '_', '~']


@dataclass(frozen=True)
class PKCEPair:
    """A verifier and its S256 code challenge."""

    verifier: str
    challenge: str
    method: str = "S256"


def generate_pkce_verifier() -> str:
    """Return a cryptographically random PKCE ``code_verifier`` per RFC 7636 §4.1.

    The verifier is randomly drawn from the ``[A-Za-z0-9-._~]`` alphabet
    with a length between ``PKCE_MIN_VERIFIER_LENGTH`` and
    ``PKCE_MAX_VERIFIER_LENGTH`` (inclusive).
    """
    length = random.randrange(PKCE_MIN_VERIFIER_LENGTH, PKCE_MAX_VERIFIER_LENGTH + 1)
    return ''.join(secrets.choice(_VERIFIER_ALPHABET) for _ in range(length))


def generate_pkce_challenge(verifier: str) -> str:
    """Return the S256 ``code_challenge`` for ``verifier`` (RFC 7636 §4.2).

    ``BASE64URL-ENCODE(SHA256(ASCII(code_verifier)))`` with padding stripped.
    """
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def generate_pkce_pair() -> PKCEPair:
    """Generate a fresh verifier/challenge pair for an authorization request."""
    verifier = generate_pkce_verifier()
    return PKCEPair(
        verifier=verifier,
        challenge=generate_pkce_challenge(verifier),
    )


def verify_pkce(verifier: str, challenge: str, method: str = "S256") -> bool:
    """Check ``verifier`` against a stored ``challenge`` (constant-time).

    Only ``S256`` is supported: the ``plain`` method is rejected outright
    because it offers no protection if the authorization request leaks.
    """
    if method.upper() != "S256":
        return False
    return secrets.compare_digest(generate_pkce_challenge(verifier), challenge)


def validate_callback_params(
    *,
    state: str | None,
    expected_state: str | None,
    code_verifier: str | None,
    error: str | None = None,
    error_description: str | None = None,
) -> None:
    """Validate an authorization-code callback (RFC 6749 §4.1.2 / §10.12).

    Raises ``HTTPException(400)`` with a client-safe message; never echoes
    provider error text back to the client.

    * ``state`` must be present, non-empty and match the value bound to the
      authorization request. A missing/absent ``expected_state`` is rejected
      rather than skipped, so callers cannot silently disable CSRF defence.
    * A ``code_verifier`` must be present so the callback can complete the
      PKCE exchange.
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {error}",
        )
    if not expected_state:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth state was never stored; authorization request is invalid",
        )
    if not state or not secrets.compare_digest(state, expected_state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )
    if not code_verifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing PKCE code verifier",
        )


def parse_callback_params(query_string: str) -> dict[str, str | None]:
    """Parse a redirect query string into single-valued callback params.

    Only the first value of each key is kept; duplicated parameters are a
    request-smuggling vector and are never merged.
    """
    parsed: dict[str, str | None] = {}
    for key, values in parse_qs(query_string, keep_blank_values=True).items():
        parsed[key] = values[0] if values else None
    return parsed
