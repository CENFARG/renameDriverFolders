"""Tests for SQLiteTokenStore implementation"""

import os
import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from core_renombrador.token_store import SQLiteTokenStore
from core_renombrador.models.token import TokenData


@pytest.fixture
async def sqlite_store(tmp_path):
    """Create a SQLiteTokenStore instance for testing with a temp file."""
    db_file = str(tmp_path / "test_tokens.db")
    store = SQLiteTokenStore(db_file)
    await store.init_db()
    yield store


@pytest.fixture
def sample_token():
    """Create a sample TokenData for testing"""
    return TokenData(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_type="Bearer",
        expires_at=datetime.now() + timedelta(hours=1),
        scope=["email", "drive.readonly"],
        user_id="user123",
        email="user@example.com",
        issued_at=datetime.now()
    )


@pytest.mark.unit
class TestSQLiteTokenStore:
    """Test suite for SQLiteTokenStore"""

    async def test_sqlite_store_initializes_database(self, sqlite_store):
        """Should create oauth_tokens table on initialization"""
        # Verify table exists by querying sqlite_master
        import aiosqlite
        async with aiosqlite.connect(sqlite_store.db_path) as db:
            # Query to check if table exists
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='oauth_tokens'"
            ) as cursor:
                result = await cursor.fetchone()
                assert result is not None, "oauth_tokens table should exist"
                assert result[0] == "oauth_tokens"

    async def test_sqlite_store_token(self, sqlite_store, sample_token):
        """Should store token in database"""
        await sqlite_store.store_token("user123", sample_token)

        # Verify token was stored
        retrieved = await sqlite_store.get_token("user123")

        assert retrieved is not None
        assert retrieved.access_token == "test_access_token"
        assert retrieved.refresh_token == "test_refresh_token"
        assert retrieved.user_id == "user123"
        assert retrieved.email == "user@example.com"

    async def test_sqlite_store_retrieves_token(self, sqlite_store, sample_token):
        """Should retrieve previously stored token"""
        await sqlite_store.store_token("user123", sample_token)

        retrieved = await sqlite_store.get_token("user123")

        assert retrieved is not None
        assert retrieved.access_token == sample_token.access_token
        assert retrieved.refresh_token == sample_token.refresh_token
        assert retrieved.expires_at == sample_token.expires_at
        assert retrieved.scope == sample_token.scope

    async def test_sqlite_store_updates_existing_token(self, sqlite_store, sample_token):
        """Should update token when storing again for same user"""
        # Store initial token
        await sqlite_store.store_token("user123", sample_token)

        # Create updated token
        updated_token = TokenData(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(hours=2),
            scope=["email", "drive.readonly"],
            user_id="user123",
            email="user@example.com",
            issued_at=datetime.now()
        )

        # Store updated token
        await sqlite_store.store_token("user123", updated_token)

        # Retrieve and verify update
        retrieved = await sqlite_store.get_token("user123")

        assert retrieved.access_token == "new_access_token"
        assert retrieved.refresh_token == "new_refresh_token"

    async def test_sqlite_store_invalidates_token(self, sqlite_store, sample_token):
        """Should delete token on invalidate"""
        await sqlite_store.store_token("user123", sample_token)

        # Verify token exists
        retrieved = await sqlite_store.get_token("user123")
        assert retrieved is not None

        # Invalidate token
        await sqlite_store.invalidate("user123")

        # Verify token is deleted
        retrieved = await sqlite_store.get_token("user123")
        assert retrieved is None

    async def test_sqlite_store_handles_missing_token(self, sqlite_store):
        """Should return None for non-existent user"""
        retrieved = await sqlite_store.get_token("nonexistent_user")
        assert retrieved is None

    async def test_sqlite_store_encrypts_refresh_token(self, sqlite_store, sample_token):
        """Should encrypt refresh token before storing"""
        await sqlite_store.store_token("user123", sample_token)

        # Query database directly to verify encryption
        import aiosqlite
        async with aiosqlite.connect(sqlite_store.db_path) as db:
            async with db.execute(
                "SELECT refresh_token FROM oauth_tokens WHERE user_id = ?",
                ("user123",)
            ) as cursor:
                result = await cursor.fetchone()
                stored_refresh_token = result[0]

                # Verify encrypted (not stored as plaintext)
                assert stored_refresh_token != "test_refresh_token"
                assert stored_refresh_token is not None
                assert len(stored_refresh_token) > 0

    async def test_sqlite_store_concurrent_access(self, sqlite_store, sample_token):
        """Should handle concurrent store operations"""
        # Create multiple tasks storing tokens for different users
        tasks = []
        for i in range(10):
            token = TokenData(
                access_token=f"access_token_{i}",
                refresh_token=f"refresh_token_{i}",
                token_type="Bearer",
                expires_at=datetime.now() + timedelta(hours=1),
                scope=["email"],
                user_id=f"user{i}",
                email=f"user{i}@example.com",
                issued_at=datetime.now()
            )
            tasks.append(sqlite_store.store_token(f"user{i}", token))

        # Execute all stores concurrently
        await asyncio.gather(*tasks)

        # Verify all tokens were stored
        for i in range(10):
            retrieved = await sqlite_store.get_token(f"user{i}")
            assert retrieved is not None
            assert retrieved.access_token == f"access_token_{i}"
