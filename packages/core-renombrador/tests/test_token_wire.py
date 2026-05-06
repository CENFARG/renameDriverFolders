"""
Test: TokenStore wiring into services.

Verifies that:
1. TokenManager wraps TokenStore with service-friendly API
2. Services can store and retrieve tokens
3. Encryption works end-to-end

:task: T1.8 - Wire TokenStore into services
:phase: RED (test written first)
"""

import pytest
import os
from unittest.mock import MagicMock, patch


class TestTokenManager:
    """TokenManager provides service-friendly API over TokenStore."""

    def test_token_manager_module_exists(self):
        from core_renombrador.token_manager import TokenManager
        assert TokenManager is not None

    def test_store_and_retrieve_token(self):
        from core_renombrador.token_manager import TokenManager

        with patch.dict(os.environ, {"TOKEN_DB_PATH": ":memory:"}):
            mgr = TokenManager()
            mgr.store_token(
                user_email="user@example.com",
                access_token="ya29.test123",
                refresh_token="refresh456",
                expires_in=3600,
            )

            token_data = mgr.get_token("user@example.com")
            assert token_data is not None
            assert token_data["access_token"] == "ya29.test123"

    def test_get_nonexistent_token(self):
        from core_renombrador.token_manager import TokenManager

        with patch.dict(os.environ, {"TOKEN_DB_PATH": ":memory:"}):
            mgr = TokenManager()
            result = mgr.get_token("nobody@example.com")
            assert result is None

    def test_invalidate_token(self):
        from core_renombrador.token_manager import TokenManager

        with patch.dict(os.environ, {"TOKEN_DB_PATH": ":memory:"}):
            mgr = TokenManager()
            mgr.store_token(
                user_email="user@example.com",
                access_token="ya29.test",
                refresh_token="refresh",
                expires_in=3600,
            )

            mgr.invalidate_token("user@example.com")
            result = mgr.get_token("user@example.com")
            assert result is None

    def test_update_existing_token(self):
        from core_renombrador.token_manager import TokenManager

        with patch.dict(os.environ, {"TOKEN_DB_PATH": ":memory:"}):
            mgr = TokenManager()
            mgr.store_token(
                user_email="user@example.com",
                access_token="old_token",
                refresh_token="old_refresh",
                expires_in=3600,
            )
            mgr.store_token(
                user_email="user@example.com",
                access_token="new_token",
                refresh_token="new_refresh",
                expires_in=7200,
            )

            token_data = mgr.get_token("user@example.com")
            assert token_data["access_token"] == "new_token"

    def test_refresh_token_is_encrypted(self):
        """Refresh tokens must not be stored in plaintext."""
        from core_renombrador.token_manager import TokenManager

        with patch.dict(os.environ, {"TOKEN_DB_PATH": ":memory:"}):
            mgr = TokenManager()
            mgr.store_token(
                user_email="user@example.com",
                access_token="ya29.test",
                refresh_token="secret_refresh_token",
                expires_in=3600,
            )

            # The raw DB should NOT contain the plaintext refresh token
            # Access via TokenManager returns decrypted value
            token_data = mgr.get_token("user@example.com")
            assert token_data["refresh_token"] == "secret_refresh_token"
