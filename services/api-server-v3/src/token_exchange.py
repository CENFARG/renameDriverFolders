"""Server-side token exchange for OAuth token caching."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from core_renombrador.token_store import TokenData

logger = logging.getLogger(__name__)

# TokenStore is injected at startup
_token_store = None


def init_token_store(store):
    global _token_store
    _token_store = store


def exchange_and_store(user_email: str, id_token: str, expires_in: int = 3600) -> Optional[TokenData]:
    """Store the ID token info in TokenStore for later use by the worker.

    In a full implementation, this would exchange the auth code for
    access + refresh tokens via Google's token endpoint. For now,
    we store the ID token as the access token (valid for API calls)
    and mark it with expiration.

    Args:
        user_email: Email extracted from the verified ID token.
        id_token: The Google ID token (JWT).
        expires_in: Token lifetime in seconds (default 1h).

    Returns:
        TokenData if stored successfully, None on failure.
    """
    if not _token_store:
        logger.error("TokenStore not initialized")
        return None

    if not user_email or not id_token:
        logger.warning("exchange_and_store: missing user_email or id_token")
        return None

    now = datetime.now(timezone.utc)
    token_data = TokenData(
        access_token=id_token,
        refresh_token="",
        token_type="Bearer",
        expires_at=now + timedelta(seconds=expires_in),
        scope=["openid", "email", "profile"],
        user_id=user_email,
        email=user_email,
        issued_at=now,
    )

    try:
        _token_store.store_token(user_email, token_data)
        logger.info("Token stored for user %s (expires in %ds)", user_email, expires_in)
        return token_data
    except Exception:
        logger.exception("Failed to store token for user %s", user_email)
        return None


def get_stored_token(user_email: str) -> Optional[TokenData]:
    """Retrieve a previously stored token for the given user."""
    if not _token_store:
        logger.error("TokenStore not initialized")
        return None

    try:
        return _token_store.get_token(user_email)
    except Exception:
        logger.exception("Failed to retrieve token for user %s", user_email)
        return None
