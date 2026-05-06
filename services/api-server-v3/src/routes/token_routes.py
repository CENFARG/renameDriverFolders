"""Token exchange endpoint for server-side OAuth token caching."""
import logging

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from token_exchange import exchange_and_store, get_stored_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/exchange")
async def exchange_token(user: dict = Depends(get_current_user)):
    """Exchange verified ID token for server-side cached token.

    Frontend sends ID token via Authorization header (verified by get_current_user).
    API server stores it in TokenStore for worker to retrieve later.
    """
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Missing user email in token")

    token = exchange_and_store(
        user_email=email,
        id_token=user.get("sub", ""),
        expires_in=3600,
    )

    if not token:
        raise HTTPException(status_code=500, detail="Token storage failed")

    return {"status": "ok", "email": email, "expires_at": token.expires_at}


@router.get("/token-status")
async def token_status(user: dict = Depends(get_current_user)):
    """Check if a cached token exists for the current user."""
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Missing user email in token")

    stored = get_stored_token(email)
    if not stored:
        return {"has_token": False, "email": email}

    import time
    remaining = stored.expires_at - time.time()
    return {
        "has_token": True,
        "email": email,
        "expires_in": max(0, int(remaining)),
    }
