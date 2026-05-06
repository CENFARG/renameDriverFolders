"""
Authentication utilities for API Server v3.
=============================================

Provides OIDC token verification for Cloud Scheduler requests
and unified authentication helpers.

:created:   2026-05-05
:filename:  auth.py
:path:      services/api-server-v3/src/auth.py
:author:    CENF
:version:   1.0.0
:status:    Development
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
import os

from fastapi import HTTPException, Request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

logger = logging.getLogger(__name__)

VALID_GOOGLE_ISSUERS = {
    "https://accounts.google.com",
    "accounts.google.com",
}


def verify_scheduler_token(request: Request) -> dict:
    """
    Verify OIDC bearer token from Cloud Scheduler.

    Cloud Scheduler sends an OIDC token in the Authorization header.
    This function validates the token's signature, issuer, and audience.

    Args:
        request: FastAPI Request object with headers.

    Returns:
        Token payload dict if valid.

    Raises:
        HTTPException 401: If token is missing, malformed, or invalid.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        logger.warning("Scheduler request missing Authorization header")
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("Scheduler request has invalid Authorization format")
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = parts[1]

    expected_audience = os.environ.get(
        "API_AUDIENCE",
        "renombradorarchivosgdrive-api-v2"
    )

    try:
        payload = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=expected_audience,
        )
    except ValueError as e:
        logger.warning(f"OIDC token verification failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    issuer = payload.get("iss", "")
    if issuer not in VALID_GOOGLE_ISSUERS:
        logger.warning(f"OIDC token has invalid issuer: {issuer}")
        raise HTTPException(status_code=401, detail="Invalid token issuer")

    token_aud = payload.get("aud", "")
    if token_aud != expected_audience:
        logger.warning(f"OIDC token audience mismatch: got {token_aud}, expected {expected_audience}")
        raise HTTPException(status_code=401, detail="Invalid token audience")

    logger.info(f"Scheduler token verified for: {payload.get('email', 'unknown')}")
    return payload


def verify_auth(request: Request) -> dict:
    """
    Unified authentication: IAP priority, OAuth fallback.

    Checks for IAP token first (Cloud Run), then falls back
    to Google OAuth2 token verification.

    Args:
        request: FastAPI Request object.

    Returns:
        User info dict with email and name.

    Raises:
        HTTPException 401: If no valid auth found.
    """
    # Try IAP first
    iap_token = request.headers.get("X-Goog-Iap-Jwt-Assertion")
    if iap_token:
        try:
            payload = id_token.verify_oauth2_token(
                iap_token,
                google_requests.Request(),
                audience=os.environ.get("API_AUDIENCE", ""),
            )
            email = payload.get("email", "")
            if email:
                return {"email": email, "name": payload.get("name", email)}
        except Exception:
            pass

    # Fallback: Bearer token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Not authenticated")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = parts[1]
    try:
        payload = id_token.verify_oauth2_token(
            token, google_requests.Request(), audience=None
        )
        email = payload.get("email", "")
        if not email:
            raise HTTPException(status_code=401, detail="Token has no email")
        return {"email": email, "name": payload.get("name", email)}
    except Exception as e:
        logger.warning(f"OAuth token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(request: Request) -> dict:
    """Dependency wrapper for verify_auth."""
    return verify_auth(request)
