"""
Token Store — Abstract interface and SQLite implementation.
=============================================================

TokenStore interface for OAuth token persistence.
SQLiteTokenStore provides encrypted local storage.

:created:   2026-04-22
:filename:  token_store.py
:path:      packages/core-renombrador/src/core_renombrador/token_store.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""
import aiosqlite
import base64
import hashlib
from abc import ABC, abstractmethod
from cryptography.fernet import Fernet
from datetime import datetime
from typing import Optional

from core_renombrador.models.token import TokenData


class TokenStore(ABC):
    """
    Abstract interface for token persistence

    This interface defines the contract for token storage implementations.
    Concrete implementations must provide methods for storing, retrieving,
    and invalidating OAuth tokens.
    """

    @abstractmethod
    async def get_token(self, user_id: str) -> Optional[TokenData]:
        """
        Retrieve token for user

        Args:
            user_id: Unique user identifier

        Returns:
            TokenData if found, None otherwise
        """
        pass

    @abstractmethod
    async def store_token(self, user_id: str, token: TokenData) -> None:
        """
        Store token for user

        Args:
            user_id: Unique user identifier
            token: TokenData to store
        """
        pass

    @abstractmethod
    async def invalidate(self, user_id: str) -> None:
        """
        Invalidate token on logout

        Args:
            user_id: Unique user identifier
        """
        pass


class SQLiteTokenStore(TokenStore):
    """
    SQLite-backed token store for development/testing

    This implementation stores OAuth tokens in a SQLite database with
    AES-256 encryption for refresh tokens. Designed for development
    and testing environments.

    Attributes:
        db_path: Path to SQLite database file
        _encryption_key: Fernet key for encrypting refresh tokens
        _conn: Persistent aiosqlite connection (for in-memory databases)
    """

    def __init__(self, db_path: str = "oauth_tokens.db"):
        """
        Initialize SQLiteTokenStore

        Args:
            db_path: Path to SQLite database file (default: oauth_tokens.db)
                     Use ":memory:" for in-memory database (testing only)
        """
        self.db_path = db_path
        # Generate encryption key from db_path (for development)
        # In production, use a proper key management system
        key_material = hashlib.sha256(db_path.encode()).digest()
        self._encryption_key = base64.urlsafe_b64encode(key_material)
        self._cipher = Fernet(self._encryption_key)
        self._conn = None

    async def init_db(self) -> None:
        """
        Create database table if not exists

        This method creates the oauth_tokens table with the following schema:
        - user_id: Primary key
        - access_token: OAuth access token
        - refresh_token: Encrypted OAuth refresh token
        - token_type: Token type (default: "Bearer")
        - expires_at: Token expiration timestamp (ISO format string)
        - scope: Comma-separated list of scopes
        - email: User email
        - issued_at: Token issuance timestamp (ISO format string)
        - created_at: Row creation timestamp
        """
        # For in-memory databases, keep a persistent connection
        if self.db_path == ":memory:":
            self._conn = await aiosqlite.connect(self.db_path)
            db = self._conn
        else:
            db = await aiosqlite.connect(self.db_path)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS oauth_tokens (
                user_id TEXT PRIMARY KEY,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                token_type TEXT DEFAULT 'Bearer',
                expires_at TEXT NOT NULL,
                scope TEXT NOT NULL,
                email TEXT NOT NULL,
                issued_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

        # Close connection if not in-memory
        if self.db_path != ":memory:":
            await db.close()

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get a database connection (persistent for in-memory DB)"""
        if self.db_path == ":memory:" and self._conn is not None:
            return self._conn
        return await aiosqlite.connect(self.db_path)

    async def get_token(self, user_id: str) -> Optional[TokenData]:
        """
        Retrieve token for user

        Args:
            user_id: Unique user identifier

        Returns:
            TokenData if found, None otherwise
        """
        db = await self._get_connection()
        async with db.execute(
            "SELECT * FROM oauth_tokens WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            # Decrypt refresh token
            encrypted_refresh = row[2]
            decrypted_refresh = self._cipher.decrypt(encrypted_refresh.encode()).decode()

            return TokenData(
                access_token=row[1],
                refresh_token=decrypted_refresh,
                token_type=row[3],
                expires_at=datetime.fromisoformat(row[4]),
                scope=row[5].split(","),
                user_id=row[0],
                email=row[6],
                issued_at=datetime.fromisoformat(row[7])
            )

    async def store_token(self, user_id: str, token: TokenData) -> None:
        """
        Store token for user

        Args:
            user_id: Unique user identifier
            token: TokenData to store
        """
        # Encrypt refresh token before storing
        encrypted_refresh = self._cipher.encrypt(
            token.refresh_token.encode()
        ).decode()

        db = await self._get_connection()
        await db.execute("""
            INSERT OR REPLACE INTO oauth_tokens
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            token.access_token,
            encrypted_refresh,
            token.token_type,
            token.expires_at.isoformat(),
            ",".join(token.scope),
            token.email,
            token.issued_at.isoformat()
        ))
        await db.commit()

        # Close connection if not in-memory
        if self.db_path != ":memory:":
            await db.close()

    async def invalidate(self, user_id: str) -> None:
        """
        Invalidate token on logout

        Args:
            user_id: Unique user identifier
        """
        db = await self._get_connection()
        await db.execute(
            "DELETE FROM oauth_tokens WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

        # Close connection if not in-memory
        if self.db_path != ":memory:":
            await db.close()

        # Also close connection for in-memory if needed
        if self.db_path == ":memory:" and self._conn is not None:
            await self._conn.close()
            self._conn = None
