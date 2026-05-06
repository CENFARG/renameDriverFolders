"""Tests for server-side token exchange module."""
from datetime import datetime, timedelta, timezone

import pytest
from unittest.mock import MagicMock, patch

from core_renombrador.token_store import TokenData


@pytest.fixture
def mock_store():
    """Create a mock TokenStore."""
    store = MagicMock()
    return store


@pytest.fixture
def sample_token_data():
    now = datetime.now(timezone.utc)
    return TokenData(
        access_token="ya29.test-token",
        refresh_token="1//refresh",
        token_type="Bearer",
        expires_at=now + timedelta(hours=1),
        scope=["openid", "email"],
        user_id="user@test.com",
        email="user@test.com",
        issued_at=now,
    )


class TestExchangeAndStore:
    def test_stores_token_successfully(self, mock_store, sample_token_data):
        import token_exchange
        token_exchange._token_store = mock_store

        result = token_exchange.exchange_and_store(
            user_email="user@test.com",
            id_token="ya29.test-token",
            expires_in=3600,
        )

        assert result is not None
        assert result.email == "user@test.com"
        mock_store.store_token.assert_called_once()

    def test_returns_none_without_store(self):
        import token_exchange
        token_exchange._token_store = None

        result = token_exchange.exchange_and_store(
            user_email="user@test.com",
            id_token="token",
        )
        assert result is None

    def test_returns_none_without_email(self, mock_store):
        import token_exchange
        token_exchange._token_store = mock_store

        result = token_exchange.exchange_and_store(
            user_email="",
            id_token="token",
        )
        assert result is None

    def test_returns_none_without_id_token(self, mock_store):
        import token_exchange
        token_exchange._token_store = mock_store

        result = token_exchange.exchange_and_store(
            user_email="user@test.com",
            id_token="",
        )
        assert result is None

    def test_returns_none_on_store_failure(self, mock_store):
        import token_exchange
        token_exchange._token_store = mock_store
        mock_store.store_token.side_effect = Exception("DB error")

        result = token_exchange.exchange_and_store(
            user_email="user@test.com",
            id_token="token",
        )
        assert result is None


class TestGetStoredToken:
    def test_retrieves_token(self, mock_store, sample_token_data):
        import token_exchange
        token_exchange._token_store = mock_store
        mock_store.get_token.return_value = sample_token_data

        result = token_exchange.get_stored_token("user@test.com")
        assert result is not None
        assert result.email == "user@test.com"

    def test_returns_none_without_store(self):
        import token_exchange
        token_exchange._token_store = None

        result = token_exchange.get_stored_token("user@test.com")
        assert result is None

    def test_returns_none_on_failure(self, mock_store):
        import token_exchange
        token_exchange._token_store = mock_store
        mock_store.get_token.side_effect = Exception("DB error")

        result = token_exchange.get_stored_token("user@test.com")
        assert result is None


class TestInitTokenStore:
    def test_init_sets_store(self, mock_store):
        import token_exchange
        token_exchange.init_token_store(mock_store)
        assert token_exchange._token_store is mock_store
