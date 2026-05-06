"""
Token Manager — Service-friendly OAuth token persistence.
==========================================================

Wraps TokenStore/SQLiteTokenStore with a synchronous, dict-based API
that services (api-server, worker) can use without dealing with
async operations or encryption details.

:created:   2026-05-05
:filename:  token_manager.py
:path:      packages/core-renombrador/src/core_renombrador/token_manager.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from .models.token import TokenData
from .token_store import SQLiteTokenStore

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Synchronous wrapper over SQLiteTokenStore.

    Services call store_token/get_token/invalidate_token
    without worrying about async or encryption.
    """

    def __init__(self, db_path: Optional[str] = None):
        path = db_path or os.environ.get("TOKEN_DB_PATH", "data/tokens.db")
        self._store = SQLiteTokenStore(db_path=path)
        # Initialize DB synchronously
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We're inside an async context, schedule init
            asyncio.ensure_future(self._store.init_db())
        else:
            asyncio.run(self._store.init_db())

    def store_token(
        self,
        user_email: str,
        access_token: str,
        refresh_token: str,
        expires_in: int = 3600,
        scope: Optional[list] = None,
    ) -> None:
        """Store OAuth tokens for a user."""
        now = datetime.now()
        expires_at = now + timedelta(seconds=expires_in)

        token_data = TokenData(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            scope=scope or ["openid", "email"],
            user_id=user_email,
            email=user_email,
            issued_at=now,
        )

        try:
            asyncio.run(self._store.store_token(user_email, token_data))
            logger.info(f"Token stored for {user_email}")
        except RuntimeError:
            logger.warning(f"Could not store token for {user_email} (async context issue)")

    def get_token(self, user_email: str) -> Optional[dict]:
        """Retrieve stored token data for a user. Returns dict or None."""
        try:
            token_data = asyncio.run(self._store.get_token(user_email))
        except RuntimeError:
            logger.warning(f"Could not retrieve token for {user_email}")
            return None

        if not token_data:
            return None

        return {
            "access_token": token_data.access_token,
            "refresh_token": token_data.refresh_token,
            "expires_at": token_data.expires_at.isoformat() if token_data.expires_at else None,
            "user_email": token_data.email,
        }

    def invalidate_token(self, user_email: str) -> None:
        """Remove stored tokens for a user."""
        try:
            asyncio.run(self._store.invalidate(user_email))
            logger.info(f"Token invalidated for {user_email}")
        except RuntimeError:
            logger.warning(f"Could not invalidate token for {user_email}")

    def is_token_expired(self, user_email: str) -> bool:
        """Check if stored token is expired."""
        token_data = self.get_token(user_email)
        if not token_data or not token_data.get("expires_at"):
            return True

        expires_at = datetime.fromisoformat(token_data["expires_at"])
        return datetime.now() >= expires_at
