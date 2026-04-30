# Technical Design: refactorizacion-v3

**Date**: 2026-04-22
**Project**: renameDriverFolders - Document renaming system using AI
**Status**: Design Complete
**Version**: v3.0

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Design](#component-design)
3. [API Design](#api-design)
4. [Deployment Architecture](#deployment-architecture)
5. [Testing Strategy](#testing-strategy)
6. [Design Decisions](#design-decisions)

---

## Architecture Overview

### v3 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              v3 System Architecture                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌──────────────────────┐              ┌──────────────────────────────────────┐   │
│  │     Client Layer     │              │         External Services            │   │
│  ├──────────────────────┤              ├──────────────────────────────────────┤   │
│  │  Angular Frontend    │              │  ┌────────────┐  ┌──────────────┐    │   │
│  │  - OAuth Client      │◄─────────────┼─▶│Google OAuth│  │ Google Drive │    │   │
│  │  - Token Cache (mem) │              │  │   Provider  │  │     API      │    │   │
│  │  - Error Handler     │─────────────▶│─┤            │  │              │    │   │
│  └──────────────────────┘              │  └────────────┘  └──────────────┘    │   │
│           │                            └──────────────────────────────────────┘   │
│           │                                                                       │
│           ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                        API Layer (FastAPI)                                   │ │
│  ├─────────────────────────────────────────────────────────────────────────────┤ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │ │
│  │  │  Auth Middleware │─▶│ Correlation ID   │  │   Error Handler         │  │ │
│  │  │  - IAP (prod)    │  │  Middleware      │  │   (RFC 7807)            │  │ │
│  │  │  - OAuth (dev)   │  │                  │  │                          │  │ │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │ │
│  │           │                      │                         │               │ │
│  │  ┌────────▼──────────────────────▼─────────────────────────▼───────────┐   │ │
│  │  │                   Service Layer                                     │   │ │
│  │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐   │   │ │
│  │  │  │TokenManager│  │ConfigMgr   │  │JobService  │  │AlgorithmSvc  │   │   │ │
│  │  │  │            │  │            │  │            │  │              │   │   │ │
│  │  │  │- get_token │  │- load()    │  │- create()  │  │- list()      │   │   │ │
│  │  │  │- refresh() │  │- reload()  │  │- update()  │  │- validate()  │   │   │ │
│  │  │  │- invalidate│  │- get()     │  │- delete()  │  │              │   │   │ │
│  │  │  └────────────┘  └────────────┘  └────────────┘  └──────────────┘   │   │ │
│  │  └─────────────────────────────────────────────────────────────────────┘   │ │
│  │           │                                                               │ │
│  └───────────┼───────────────────────────────────────────────────────────────┘ │
│              │                                                                 │
│              │ Cloud Tasks (OIDC)                                              │
│              ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                    Worker Layer (FastAPI)                                   │ │
│  ├─────────────────────────────────────────────────────────────────────────────┤ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │ │
│  │  │  OIDC Middleware │─▶│ServiceRegistry   │  │   Error Handler         │  │ │
│  │  │  (scheduler SA)  │  │  - get_db_mgr()  │  │   (RFC 7807)            │  │ │
│  │  └──────────────────┘  │  - get_alg_mgr() │  │                          │  │ │
│  │                        │  - get_config()  │  └──────────────────────────┘  │ │
│  │                        └──────────────────┘            │                   │ │
│  │                                 │                     │                   │ │
│  │                        ┌────────▼─────────────────────▼─────────────────┐  │ │
│  │                        │              Processing Layer                  │  │ │
│  │                        │  ┌────────────┐  ┌────────────┐  ┌───────────┐ │  │ │
│  │                        │  │AgentFactory│  │ContentExtractor│DriveAPI │ │  │ │
│  │                        │  │            │  │            │  │           │ │  │ │
│  │                        │  │- create()  │  │- get_content│- rename() │ │  │ │
│  │                        │  └────────────┘  └────────────┘  └───────────┘ │  │ │
│  │                        └─────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                        Infrastructure Layer                                  │ │
│  ├─────────────────────────────────────────────────────────────────────────────┤ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │ │
│  │  │    Redis     │  │  Supabase    │  │Cloud Tasks   │  │  Cloud       │   │ │
│  │  │ (Token Cache)│  │  (Database)  │  │   (Queue)    │  │  Scheduler   │   │ │
│  │  │              │  │              │  │              │  │              │   │ │
│  │  │- oauth:token │  │- users       │  │- OIDC auth   │  │- cron jobs   │   │ │
│  │  │- oauth:lock  │  │- jobs        │  │- payloads    │  │              │   │ │
│  │  │              │  │- job_algs    │  │              │  │              │   │ │
│  │  │              │  │- doc_algo    │  │              │  │              │   │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### v3 Data Flow: Token Refresh

```
┌──────────┐      ┌───────────┐      ┌──────────┐      ┌─────────┐      ┌──────────┐
│  User    │─────▶│ Frontend  │─────▶│  API     │─────▶│ Redis   │─────▶│  Google  │
│ Browser  │      │ (Angular) │      │ Server   │      │Cache    │      │  OAuth   │
└──────────┘      └───────────┘      └──────────┘      └─────────┘      └──────────┘
     │                 │                   │                  │                 │
     │ 1. Access App   │                   │                  │                 │
     │─────────────────▶│                   │                  │                 │
     │                 │                   │                  │                 │
     │                 │ 2. Check Token    │                  │                 │
     │                 │ (in memory)       │                  │                 │
     │                 │──────────────────▶│                  │                 │
     │                 │                   │                  │                 │
     │                 │ 3. GET /auth/token│                  │                 │
     │                 │                   │                  │                 │
     │                 │                   │ 4. Check cache   │                 │
     │                 │                   │─────────────────▶│                 │
     │                 │                   │                  │                 │
     │                 │                   │ 5. Token found   │                 │
     │                 │                   │◀─────────────────│                 │
     │                 │                   │                  │                 │
     │                 │                   │ 6. Expiring soon? │                 │
     │                 │                   │ (expires < 5min)  │                 │
     │                 │                   │                  │                 │
     │                 │                   │ 7. Acquire lock  │                 │
     │                 │                   │─────────────────▶│                 │
     │                 │                   │                  │                 │
     │                 │                   │ 8. Lock acquired │                 │
     │                 │                   │◀─────────────────│                 │
     │                 │                   │                  │                 │
     │                 │                   │ 9. Refresh token │                 │
     │                 │                   │────────────────────────────────────▶│
     │                 │                   │                  │                 │
     │                 │                   │ 10. New token    │                 │
     │                 │                   │◀────────────────────────────────────│
     │                 │                   │                  │                 │
     │                 │                   │ 11. Store new    │                 │
     │                 │                   │─────────────────▶│                 │
     │                 │                   │                  │                 │
     │                 │                   │ 12. Saved        │                 │
     │                 │                   │◀─────────────────│                 │
     │                 │                   │                  │                 │
     │                 │ 13. Return token  │                  │                 │
     │                 │◀──────────────────│                  │                 │
     │                 │                   │                  │                 │
     │ 14. Auto-auth   │                   │                  │                 │
     │◀─────────────────│                   │                  │                 │
     │                 │                   │                  │                 │
     │ NO PROMPT! ✅    │                   │                  │                 │
```

### v3 Data Flow: Job Processing

```
┌──────────┐   ┌───────────┐   ┌──────────┐   ┌─────────────┐   ┌──────────┐   ┌──────────┐
│  User    │──▶│ Frontend  │──▶│  API     │──▶│Cloud Tasks  │──▶│ Worker   │──▶│   Drive  │
│ Browser  │   │ (Angular) │   │ Server   │   │   (Queue)   │   │          │   │    API   │
└──────────┘   └───────────┘   └──────────┘   └─────────────┘   └──────────┘   └──────────┘
    │              │               │                  │                │            │
    │ 1. Sign In   │               │                  │                │            │
    │ (once only)  │               │                  │                │            │
    │─────────────▶│               │                  │                │            │
    │              │               │                  │                │            │
    │              │ 2. OAuth ID Token                │                │            │
    │              │──────────────▶│                  │                │            │
    │              │               │                  │                │            │
    │              │               │ 3. Verify + Create Token Cache                   │
    │              │               │────────────────────────────────────────────────▶│
    │              │               │                  │                │            │
    │              │ 4. Auth Success│                  │                │            │
    │              │◀──────────────│                  │                │            │
    │              │               │                  │                │            │
    │ 5. Select Folder + Create Job                  │                │            │
    │─────────────────────────────────────────────▶│                  │            │
    │              │               │                  │                │            │
    │              │               │ 6. Load Job Config (with algorithms)             │
    │              │               │────────────────────────────────────────────────▶│
    │              │               │                  │                │            │
    │              │               │ 7. Create Task (OIDC + user credentials)          │
    │              │               │─────────────────▶│                │            │
    │              │               │                  │                │            │
    │              │ 8. Job Created│                  │                │            │
    │              │◀──────────────│                  │                │            │
    │              │               │                  │                │            │
    │ 9. Task Queued               │                  │                │            │
    │              │               │                  │ 10. Poll Queue │            │
    │              │               │                  │◀───────────────│            │
    │              │               │                  │                │            │
    │              │               │                  │ 11. Verify OIDC│            │
    │              │               │                  │───────────────▶│            │
    │              │               │                  │                │            │
    │              │               │                  │ 12. Process Files            │
    │              │               │                  │─────────────────────────────▶│
    │              │               │                  │                │            │
    │              │               │                  │ 13. Rename Files            │
    │              │               │                  │─────────────────────────────▶│
    │              │               │                  │                │            │
    │              │               │                  │ 14. Update Execution Log                  │
    │              │               │                  │──────────────────────────────────────────▶
    │              │               │                  │                │            │
    │ 15. Job Complete            │                  │                │            │
    │◀────────────────────────────│                  │                │            │
```

---

## Component Design

### Feature 1: OAuth Token Caching System

#### Component Architecture

```
TokenCache (Service)
├── TokenStore (Interface)
│   ├── RedisTokenStore (Production)
│   │   ├── redis_client (Connection pooling)
│   │   ├── retry logic (3 attempts with backoff)
│   │   └── lock_manager (Distributed locking)
│   └── SQLiteTokenStore (Development/Fallback)
│       ├── sqlite_connection (aiosqlite)
│       ├── encryption (AES-256 for refresh tokens)
│       └── file_locking (For concurrent access)
└── TokenRefresher
    ├── distributed_lock (Redis)
    ├── google_oauth_client
    └── fallback_to_consent (On refresh failure)
```

#### Class Structure

```python
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional
import redis.asyncio as redis
import aiosqlite

# Data Models
class TokenData(BaseModel):
    """OAuth token data structure"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    scope: list[str]
    user_id: str
    email: str
    issued_at: datetime

# Abstract Interface
class TokenStore(ABC):
    """Abstract interface for token persistence"""

    @abstractmethod
    async def get_token(self, user_id: str) -> Optional[TokenData]:
        """Retrieve token for user"""
        pass

    @abstractmethod
    async def store_token(self, user_id: str, token: TokenData) -> None:
        """Store token for user"""
        pass

    @abstractmethod
    async def invalidate(self, user_id: str) -> None:
        """Invalidate token on logout"""
        pass

# Redis Implementation
class RedisTokenStore(TokenStore):
    """Redis-backed token store for production"""

    TOKEN_PREFIX = "oauth:token:"
    LOCK_PREFIX = "oauth:lock:"
    TOKEN_TTL = 604800  # 7 days

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )

    async def get_token(self, user_id: str) -> Optional[TokenData]:
        key = f"{self.TOKEN_PREFIX}{user_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        return TokenData.model_validate_json(data)

    async def store_token(self, user_id: str, token: TokenData) -> None:
        key = f"{self.TOKEN_PREFIX}{user_id}"
        await self.redis.setex(
            key,
            self.TOKEN_TTL,
            token.model_dump_json()
        )

    async def acquire_refresh_lock(self, user_id: str, timeout: int = 30) -> bool:
        """Acquire distributed lock for token refresh"""
        lock_key = f"{self.LOCK_PREFIX}{user_id}"
        return await self.redis.set(
            lock_key,
            "1",
            nx=True,
            ex=timeout
        )

    async def release_refresh_lock(self, user_id: str) -> None:
        """Release distributed lock"""
        lock_key = f"{self.LOCK_PREFIX}{user_id}"
        await self.redis.delete(lock_key)

    async def invalidate(self, user_id: str) -> None:
        key = f"{self.TOKEN_PREFIX}{user_id}"
        await self.redis.delete(key)

# SQLite Implementation (Fallback)
class SQLiteTokenStore(TokenStore):
    """SQLite token store for development/testing"""

    def __init__(self, db_path: str = "oauth_tokens.db"):
        self.db_path = db_path

    async def init_db(self) -> None:
        """Create table if not exists"""
        async with aiosqlite.connect(self.db_path) as db:
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

    async def get_token(self, user_id: str) -> Optional[TokenData]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM oauth_tokens WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return TokenData(
                    access_token=row[1],
                    refresh_token=row[2],
                    token_type=row[3],
                    expires_at=datetime.fromisoformat(row[4]),
                    scope=row[5].split(","),
                    user_id=row[0],
                    email=row[6],
                    issued_at=datetime.fromisoformat(row[7])
                )

    async def store_token(self, user_id: str, token: TokenData) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO oauth_tokens
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                token.access_token,
                token.refresh_token,
                token.token_type,
                token.expires_at.isoformat(),
                ",".join(token.scope),
                token.email,
                token.issued_at.isoformat()
            ))
            await db.commit()

    async def invalidate(self, user_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM oauth_tokens WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()

# Token Manager Service
class TokenManager:
    """High-level token management service"""

    def __init__(
        self,
        store: TokenStore,
        google_client_id: str,
        google_client_secret: str
    ):
        self.store = store
        self.google_client_id = google_client_id
        self.google_client_secret = google_client_secret
        self.refresh_threshold = timedelta(minutes=5)

    async def get_valid_token(self, user_id: str) -> TokenData:
        """Get valid token, refreshing if needed"""
        token = await self.store.get_token(user_id)

        if not token:
            raise ValueError("No token found for user")

        # Check if refresh needed
        if token.expires_at > datetime.now() + self.refresh_threshold:
            return token

        # Refresh token
        return await self._refresh_token(user_id, token)

    async def _refresh_token(self, user_id: str, token: TokenData) -> TokenData:
        """Refresh token with distributed locking"""

        # Try to acquire lock
        if isinstance(self.store, RedisTokenStore):
            lock_acquired = await self.store.acquire_refresh_lock(user_id)
            if not lock_acquired:
                # Wait for another process to refresh
                await asyncio.sleep(1)
                return await self.get_valid_token(user_id)

        try:
            # Double-check after acquiring lock
            current = await self.store.get_token(user_id)
            if current.expires_at > datetime.now() + self.refresh_threshold:
                return current

            # Perform refresh
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.google_client_id,
                        "client_secret": self.google_client_secret,
                        "refresh_token": token.refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                response.raise_for_status()
                data = response.json()

            # Build new token data
            new_token = TokenData(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", token.refresh_token),
                token_type=data.get("token_type", "Bearer"),
                expires_at=datetime.now() + timedelta(seconds=data["expires_in"]),
                scope=token.scope,
                user_id=user_id,
                email=token.email,
                issued_at=datetime.now()
            )

            # Store new token
            await self.store.store_token(user_id, new_token)
            return new_token

        except httpx.HTTPStatusError as e:
            # Refresh failed - invalidate and require re-auth
            await self.store.invalidate(user_id)
            raise OAuthTokenExpiredError("Token refresh failed, re-authentication required")
        finally:
            if isinstance(self.store, RedisTokenStore):
                await self.store.release_refresh_lock(user_id)

    async def store_oauth_callback(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        scope: list[str],
        email: str
    ) -> TokenData:
        """Store token from OAuth callback"""
        now = datetime.now()
        token = TokenData(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=now + timedelta(seconds=expires_in),
            scope=scope,
            user_id=user_id,
            email=email,
            issued_at=now
        )
        await self.store.store_token(user_id, token)
        return token

    async def logout(self, user_id: str) -> None:
        """Invalidate token on logout"""
        await self.store.invalidate(user_id)
```

#### Token Refresh Sequence Diagram

```
User      Frontend      API      TokenManager      RedisTokenStore      Google
 │           │            │            │                 │               │
 │───────────▶│            │            │                 │               │ Access app
 │           │────────────▶│            │                 │               │ GET /token
 │           │            │────────────▶│                 │               │ Check cache
 │           │            │            │─────────────────▶│               │ GET token
 │           │            │            │◀─────────────────│               │ Found (expiring)
 │           │            │            │                 │               │
 │           │            │            │─┐               │               │ Need refresh
 │           │            │            │ │ Acquire lock   │               │
 │           │            │            │├────────────────▶│               │ SET lock
 │           │            │            ││◀────────────────│               │ Got lock
 │           │            │            │┘               │               │
 │           │            │            │──────────────────────────────────────▶│ POST refresh
 │           │            │            │                 │               │
 │           │            │            │◀──────────────────────────────────────│ New token
 │           │            │            │                 │               │
 │           │            │            │─────────────────▶│               │ Store new
 │           │            │            │◀─────────────────│               │ Saved
 │           │            │            │─┐               │               │
 │           │            │            │ │ Release lock   │               │
 │           │            │            │├────────────────▶│               │ DEL lock
 │           │            │            ││◀────────────────│               │ Released
 │           │            │            │┘               │               │
 │           │            │◀───────────│                 │               │ Return token
 │           │◀──────────│            │                 │               │
 │◀──────────│            │            │                 │               │
```

### Feature 2: Database Schema Normalization

#### v3 Schema

```sql
-- =====================================================
-- v3 Database Schema - Normalized with Foreign Keys
-- =====================================================

-- Users table (NEW - for user management)
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Document algorithms (EXISTING - unchanged except for FKs)
CREATE TABLE document_algorithms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    classification_criteria TEXT,
    extraction_prompt TEXT,
    output_schema JSONB,
    filename_format TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Jobs table (MODIFIED - normalized)
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    user_id TEXT REFERENCES users(id) ON DELETE RESTRICT,
    trigger_type TEXT NOT NULL CHECK (trigger_type IN ('manual', 'scheduled')),
    schedule TEXT,  -- cron expression (scheduled only)
    source_folder_id TEXT NOT NULL,
    subfolder_filter JSONB DEFAULT '["*"]'::jsonb,  -- RENAMED from target_folder_names
    agent_config JSONB NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_schedule CHECK (
        trigger_type = 'manual' OR schedule IS NOT NULL
    )
);

-- Job algorithms junction table (NEW)
CREATE TABLE job_algorithms (
    job_id TEXT NOT NULL,
    algorithm_id TEXT NOT NULL,
    assigned_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (job_id, algorithm_id),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (algorithm_id) REFERENCES document_algorithms(id) ON DELETE RESTRICT
);

-- Jobs archive (NEW - for rollback safety)
CREATE TABLE jobs_archive AS
SELECT * FROM jobs;

-- Job executions (EXISTING - unchanged)
CREATE TABLE job_executions (
    id TEXT PRIMARY KEY,
    user_email TEXT NOT NULL,
    user_name TEXT,
    folder_id TEXT NOT NULL,
    job_type TEXT NOT NULL,
    job_config_id TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    status TEXT CHECK (status IN ('submitted', 'processing', 'completed', 'failed')),
    task_id TEXT,
    details TEXT,
    stats JSONB
);

-- =====================================================
-- Indexes for Performance
-- =====================================================

CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_active ON jobs(active) WHERE active = true;
CREATE INDEX idx_jobs_trigger_type ON jobs(trigger_type);

CREATE INDEX idx_job_algorithms_job_id ON job_algorithms(job_id);
CREATE INDEX idx_job_algorithms_algorithm_id ON job_algorithms(algorithm_id);

CREATE INDEX idx_job_executions_user_email ON job_executions(user_email);
CREATE INDEX idx_job_executions_timestamp ON job_executions(timestamp DESC);
CREATE INDEX idx_job_executions_status ON job_executions(status);

-- =====================================================
-- Triggers
-- =====================================================

-- Updated at trigger for jobs
CREATE OR REPLACE FUNCTION update_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_jobs_updated_at();

-- Updated at trigger for document_algorithms
CREATE TRIGGER document_algorithms_updated_at
    BEFORE UPDATE ON document_algorithms
    FOR EACH ROW
    EXECUTE FUNCTION update_jobs_updated_at();

-- Updated at trigger for users
CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_jobs_updated_at();

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- Active jobs with their algorithms
CREATE VIEW v_active_jobs_with_algorithms AS
SELECT
    j.id,
    j.name,
    j.trigger_type,
    j.active,
    json_agg(
        json_build_object(
            'id', da.id,
            'name', da.name,
            'is_active', da.is_active
        )
    ) AS algorithms
FROM jobs j
LEFT JOIN job_algorithms ja ON j.id = ja.job_id
LEFT JOIN document_algorithms da ON ja.algorithm_id = da.id
WHERE j.active = true
GROUP BY j.id;

-- Jobs by user
CREATE VIEW v_user_jobs AS
SELECT
    u.id AS user_id,
    u.email,
    u.name,
    json_agg(
        json_build_object(
            'id', j.id,
            'name', j.name,
            'trigger_type', j.trigger_type,
            'active', j.active
        )
    ) AS jobs
FROM users u
LEFT JOIN jobs j ON u.id = j.user_id
GROUP BY u.id;
```

#### Migration Sequence

```python
"""
Migration v2 -> v3: Database Schema Normalization

This migration:
1. Creates users table from unique emails in jobs
2. Normalizes jobs table (removes duplicates)
3. Creates job_algorithms junction table
4. Adds foreign key constraints
5. Creates archive for rollback safety
"""

import asyncio
from typing import Dict, Any, List
from supabase import create_client, Client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MigrationV2ToV3:
    """Migration from v2 to v3 database schema"""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.dry_run = True

    async def execute(self) -> Dict[str, Any]:
        """Execute full migration"""
        results = {
            "steps": [],
            "errors": [],
            "warnings": [],
            "start_time": datetime.now()
        }

        try:
            # Phase 1: Safety & Preparation
            await self._phase_1_safety(results)

            # Phase 2: Create users table
            await self._phase_2_users(results)

            # Phase 3: Normalize jobs table
            await self._phase_3_normalize_jobs(results)

            # Phase 4: Create junction table
            await self._phase_4_junction(results)

            # Phase 5: Add constraints
            await self._phase_5_constraints(results)

            # Phase 6: Validation
            await self._phase_6_validate(results)

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            results["errors"].append(str(e))
            await self._rollback(results)

        results["end_time"] = datetime.now()
        results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()

        return results

    async def _phase_1_safety(self, results: Dict[str, Any]):
        """Phase 1: Create archive and validate preconditions"""
        logger.info("Phase 1: Safety & Preparation")

        # Create jobs archive
        await self._execute_sql("""
            CREATE TABLE IF NOT EXISTS jobs_archive AS
            SELECT * FROM jobs;
        """, results, "Create jobs_archive table")

        # Check for orphaned records
        result = await self._execute_sql("""
            SELECT COUNT(*) as count FROM jobs
            WHERE source_folder_id IS NULL OR source_folder_id = '';
        """, results, "Check for null source_folder_ids")

        if result[0]["count"] > 0:
            results["warnings"].append(f"Found {result[0]['count']} jobs with null source_folder_id")

    async def _phase_2_users(self, results: Dict[str, Any]):
        """Phase 2: Create users table from unique emails"""
        logger.info("Phase 2: Create users table")

        # Create users table
        await self._execute_sql("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                name TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """, results, "Create users table")

        # Get unique emails from job_executions
        emails_result = await self._execute_sql("""
            SELECT DISTINCT user_email, user_name
            FROM job_executions
            WHERE user_email IS NOT NULL
            GROUP BY user_email, user_name;
        """, results, "Extract unique user emails")

        # Insert users
        for row in emails_result:
            user_id = row["user_email"].split("@")[0]  # Simple ID generation
            await self._execute_sql("""
                INSERT INTO users (id, email, name)
                VALUES ($1, $2, $3)
                ON CONFLICT (email) DO NOTHING;
            """, results, f"Insert user {row['user_email']}", params=[
                user_id, row["user_email"], row["user_name"]
            ])

    async def _phase_3_normalize_jobs(self, results: Dict[str, Any]):
        """Phase 3: Normalize jobs table"""
        logger.info("Phase 3: Normalize jobs table")

        # Add user_id column (nullable first)
        await self._execute_sql("""
            ALTER TABLE jobs
            ADD COLUMN IF NOT EXISTS user_id TEXT;
        """, results, "Add user_id column to jobs")

        # Backfill user_id
        await self._execute_sql("""
            UPDATE jobs j
            SET user_id = u.id
            FROM users u
            WHERE j.name LIKE '%' || u.email || '%'
            AND j.user_id IS NULL;
        """, results, "Backfill user_id from users table")

        # Rename target_folder_names to subfolder_filter
        await self._execute_sql("""
            ALTER TABLE jobs
            RENAME COLUMN target_folder_names TO subfolder_filter_deprecated;
        """, results, "Rename target_folder_names (step 1)")

        await self._execute_sql("""
            ALTER TABLE jobs
            ADD COLUMN subfolder_filter JSONB DEFAULT '["*"]'::jsonb;
        """, results, "Add subfolder_filter column")

        await self._execute_sql("""
            UPDATE jobs
            SET subfolder_filter = subfolder_filter_deprecated;
        """, results, "Migrate data to subfolder_filter")

        await self._execute_sql("""
            ALTER TABLE jobs
            DROP COLUMN subfolder_filter_deprecated;
        """, results, "Drop deprecated column")

    async def _phase_4_junction(self, results: Dict[str, Any]):
        """Phase 4: Create job_algorithms junction table"""
        logger.info("Phase 4: Create junction table")

        # Create junction table
        await self._execute_sql("""
            CREATE TABLE IF NOT EXISTS job_algorithms (
                job_id TEXT NOT NULL,
                algorithm_id TEXT NOT NULL,
                assigned_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (job_id, algorithm_id),
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                FOREIGN KEY (algorithm_id) REFERENCES document_algorithms(id) ON DELETE RESTRICT
            );
        """, results, "Create job_algorithms junction table")

        # Create indexes
        await self._execute_sql("""
            CREATE INDEX IF NOT EXISTS idx_job_algorithms_job_id
            ON job_algorithms(job_id);
        """, results, "Create index on job_algorithms.job_id")

        await self._execute_sql("""
            CREATE INDEX IF NOT EXISTS idx_job_algorithms_algorithm_id
            ON job_algorithms(algorithm_id);
        """, results, "Create index on job_algorithms.algorithm_id")

        # Migrate existing relationships from algorithm_ids in jobs
        await self._execute_sql("""
            INSERT INTO job_algorithms (job_id, algorithm_id)
            SELECT
                j.id as job_id,
                alg.value::text as algorithm_id
            FROM jobs j,
                 jsonb_array_elements_text(
                     COALESCE(j.agent_config->'algorithm_ids', '[]'::jsonb)
                 ) as alg
            WHERE alg.value IS NOT NULL
            ON CONFLICT DO NOTHING;
        """, results, "Migrate job-algorithm relationships")

    async def _phase_5_constraints(self, results: Dict[str, Any]):
        """Phase 5: Add foreign key constraints"""
        logger.info("Phase 5: Add constraints")

        # Add user_id FK
        await self._execute_sql("""
            ALTER TABLE jobs
            DROP CONSTRAINT IF EXISTS jobs_user_id_fkey;
        """, results, "Drop existing user_id FK (if any)")

        await self._execute_sql("""
            ALTER TABLE jobs
            ADD CONSTRAINT jobs_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;
        """, results, "Add user_id foreign key constraint")

        # Add check constraints
        await self._execute_sql("""
            ALTER TABLE jobs
            ADD CONSTRAINT jobs_valid_schedule
            CHECK (trigger_type = 'manual' OR schedule IS NOT NULL);
        """, results, "Add schedule validation constraint")

    async def _phase_6_validate(self, results: Dict[str, Any]):
        """Phase 6: Validate migration"""
        logger.info("Phase 6: Validation")

        # Check for orphaned jobs
        orphaned = await self._execute_sql("""
            SELECT COUNT(*) as count
            FROM jobs j
            LEFT JOIN users u ON j.user_id = u.id
            WHERE j.user_id IS NOT NULL AND u.id IS NULL;
        """, results, "Check for orphaned jobs (user_id not in users)")

        if orphaned[0]["count"] > 0:
            results["errors"].append(f"Found {orphaned[0]['count']} orphaned jobs")
            raise ValueError("Validation failed: orphaned jobs detected")

        # Check for orphaned job_algorithms
        orphaned_algs = await self._execute_sql("""
            SELECT COUNT(*) as count
            FROM job_algorithms ja
            LEFT JOIN jobs j ON ja.job_id = j.id
            LEFT JOIN document_algorithms da ON ja.algorithm_id = da.id
            WHERE j.id IS NULL OR da.id IS NULL;
        """, results, "Check for orphaned job_algorithms")

        if orphaned_algs[0]["count"] > 0:
            results["errors"].append(f"Found {orphaned_algs[0]['count']} orphaned job_algorithms")
            raise ValueError("Validation failed: orphaned job_algorithms detected")

        # Create validation view
        await self._execute_sql("""
            CREATE OR REPLACE VIEW v_migration_validation AS
            SELECT
                j.id as job_id,
                j.name as job_name,
                j.subfolder_filter,
                u.email as user_email,
                COUNT(ja.algorithm_id) as algorithm_count
            FROM jobs j
            LEFT JOIN users u ON j.user_id = u.id
            LEFT JOIN job_algorithms ja ON j.id = ja.job_id
            GROUP BY j.id, u.email;
        """, results, "Create migration validation view")

    async def _rollback(self, results: Dict[str, Any]):
        """Rollback migration on failure"""
        logger.error("Rolling back migration")

        steps = [
            "DROP VIEW IF EXISTS v_migration_validation;",
            "ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_valid_schedule;",
            "ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_user_id_fkey;",
            "DROP TABLE IF EXISTS job_algorithms;",
            "DROP INDEX IF EXISTS idx_job_algorithms_algorithm_id;",
            "DROP INDEX IF EXISTS idx_job_algorithms_job_id;",
            "-- Restore jobs from archive: This must be done manually",
            "-- DELETE FROM jobs; INSERT INTO jobs SELECT * FROM jobs_archive;",
        ]

        for step in steps:
            try:
                await self._execute_sql(step, results, f"Rollback: {step[:50]}")
            except Exception as e:
                logger.warning(f"Rollback step failed: {e}")

    async def _execute_sql(
        self,
        sql: str,
        results: Dict[str, Any],
        description: str,
        params: List[Any] = None
    ) -> List[Dict[str, Any]]:
        """Execute SQL and track results"""
        logger.info(f"Executing: {description}")

        if self.dry_run:
            results["steps"].append(f"[DRY RUN] {description}")
            return []

        # Note: Supabase Python client doesn't support raw SQL execution
        # This is pseudocode - actual implementation would use psycopg2 directly
        # or Supabase RPC functions
        try:
            # result = self.supabase.rpc('execute_sql', {'sql': sql}).execute()
            results["steps"].append(description)
            return []  # result.data
        except Exception as e:
            results["errors"].append(f"{description}: {str(e)}")
            raise
```

### Feature 3: ConfigManager Service

#### Configuration Hierarchy

```
config/
├── base.yaml              # Base configuration (all environments)
├── development.yaml       # Development overrides
├── staging.yaml           # Staging overrides
└── production.yaml        # Production overrides

Environment Variables (highest priority - override all files)
├── DATABASE_PASSWORD
├── REDIS_URL
├── OAUTH_GOOGLE_CLIENT_SECRET
└── ...

Priority Order (low to high):
1. base.yaml
2. {environment}.yaml (merges with base)
3. Environment Variables (override YAML values)
```

#### ConfigManager Class

```python
import yaml
import os
import signal
from pathlib import Path
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field, validator
from logging import getLogger

logger = getLogger(__name__)

# Configuration Models
class DatabaseConfig(BaseModel):
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "renamedriverfolders"
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # Loaded from env var
    pool_size: int = 10
    pool_timeout: int = 30

class RedisConfig(BaseModel):
    """Redis configuration"""
    url: str = "redis://localhost:6379/0"
    ttl: int = 604800  # 7 days
    pool_size: int = 10

class OAuthConfig(BaseModel):
    """OAuth configuration"""
    google_client_id: str
    google_client_secret: str
    redirect_uri: str
    scopes: list[str] = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    token_store: str = "sqlite"  # "redis" or "sqlite"
    refresh_threshold_minutes: int = 5

class AlgorithmConfig(BaseModel):
    """Algorithm configuration"""
    source: str = "injected"  # "injected" or "direct"
    validation_enabled: bool = True
    cache_ttl: int = 3600

class WorkerConfig(BaseModel):
    """Worker configuration"""
    poll_interval: int = 30
    max_retries: int = 3
    retry_backoff: int = 5
    batch_size: int = 10

class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = "INFO"
    format: str = "json"  # "json" or "text"
    output: str = "stdout"  # "stdout" or "file"
    file_path: Optional[str] = None

class AppConfig(BaseModel):
    """Root application configuration"""
    environment: str = "development"
    debug: bool = False

    database: DatabaseConfig
    redis: RedisConfig
    oauth: OAuthConfig
    algorithms: AlgorithmConfig
    worker: WorkerConfig
    logging: LoggingConfig

    @validator("environment")
    def validate_environment(cls, v, values):
        """Ensure debug mode in development"""
        if v == "development" and not values.get("debug"):
            values["debug"] = True
        return v

class ConfigManager:
    """Centralized configuration management"""

    ENV_VAR_MAPPING = {
        "DATABASE_HOST": ("database", "host"),
        "DATABASE_PORT": ("database", "port"),
        "DATABASE_PASSWORD": ("database", "password"),
        "DATABASE_USERNAME": ("database", "username"),
        "REDIS_URL": ("redis", "url"),
        "OAUTH_GOOGLE_CLIENT_ID": ("oauth", "google_client_id"),
        "OAUTH_GOOGLE_CLIENT_SECRET": ("oauth", "google_client_secret"),
        "OAUTH_REDIRECT_URI": ("oauth", "redirect_uri"),
        "ALGORITHM_SOURCE": ("algorithms", "source"),
        "LOG_LEVEL": ("logging", "level"),
    }

    def __init__(
        self,
        config_dir: str = "config",
        environment: Optional[str] = None
    ):
        self.config_dir = Path(config_dir)
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self._config: Optional[AppConfig] = None
        self._load_time: Optional[float] = None

        # Setup signal handler for reload
        signal.signal(signal.SIGHUP, self._handle_reload)

        # Load initial config
        self.load()

    def load(self) -> AppConfig:
        """Load configuration from file and environment"""
        logger.info(f"Loading configuration for environment: {self.environment}")

        # Load base config
        config_data = self._load_yaml(self.config_dir / "base.yaml")

        # Merge with environment-specific config
        env_config_path = self.config_dir / f"{self.environment}.yaml"
        if env_config_path.exists():
            env_data = self._load_yaml(env_config_path)
            config_data = self._deep_merge(config_data, env_data)

        # Override with environment variables
        config_data = self._load_env_overrides(config_data)

        # Validate and parse config
        self._config = AppConfig(**config_data)
        self._load_time = time.time()

        logger.info(f"Configuration loaded successfully (environment={self.environment})")
        return self._config

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML configuration file"""
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r") as f:
            return yaml.safe_load(f) or {}

    def _deep_merge(self, base: Dict, override: Dict) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _load_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override config with environment variables"""
        for env_var, config_path in self.ENV_VAR_MAPPING.items():
            value = os.getenv(env_var)
            if value is None:
                continue

            # Navigate to nested config path
            current = config
            for key in config_path[:-1]:
                current = current.setdefault(key, {})

            # Set value with type conversion
            final_key = config_path[-1]
            current[final_key] = self._convert_env_value(value)

        return config

    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        # Boolean
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Integer
        if value.isdigit():
            return int(value)

        # List (comma-separated)
        if "," in value:
            return [v.strip() for v in value.split(",")]

        # Default: string
        return value

    def get(self) -> AppConfig:
        """Get current configuration"""
        if self._config is None:
            raise RuntimeError("Configuration not loaded")
        return self._config

    def reload(self) -> AppConfig:
        """Reload configuration from disk"""
        logger.info("Reloading configuration")
        return self.load()

    def _handle_reload(self, signum, frame):
        """Handle SIGHUP signal for config reload"""
        logger.info(f"Received signal {signum}, reloading configuration")
        try:
            self.reload()
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")

    def get_masked_config(self) -> Dict[str, Any]:
        """Get configuration with sensitive values masked"""
        config_dict = self.get().model_dump()

        # Mask sensitive values
        sensitive_keys = [
            ("database", "password"),
            ("oauth", "google_client_secret"),
        ]

        for key_path in sensitive_keys:
            current = config_dict
            for key in key_path[:-1]:
                current = current.get(key, {})
            if key_path[-1] in current:
                current[key_path[-1]] = "***MASKED***"

        return config_dict

    @property
    def config_age_seconds(self) -> float:
        """Get age of current configuration in seconds"""
        if self._load_time is None:
            return 0
        return time.time() - self._load_time
```

### Feature 4: Worker ServiceRegistry

#### ServiceRegistry Pattern

```
ServiceRegistry (Singleton)
├── Services
│   ├── DatabaseManager (jobs table)
│   ├── DatabaseManager (document_algorithms table)
│   ├── DatabaseManager (users table)
│   ├── ConfigManager
│   ├── TokenStore (Redis or SQLite)
│   └── HTTPClient (for external APIs)
└── Lifecycle
    ├── initialize_all()  # Called on startup
    └── shutdown_all()    # Called on shutdown
```

#### ServiceRegistry Implementation

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from supabase import create_client, Client
import redis.asyncio as redis

class ServiceRegistry(ABC):
    """Service registry interface for dependency injection"""

    @abstractmethod
    def get_database_manager(self, table_name: str) -> "DatabaseManager":
        """Get database manager for specific table"""
        pass

    @abstractmethod
    def get_algorithms_manager(self) -> "DatabaseManager":
        """Get algorithms database manager"""
        pass

    @abstractmethod
    def get_config_manager(self) -> "ConfigManager":
        """Get configuration manager"""
        pass

    @abstractmethod
    def get_token_store(self) -> "TokenStore":
        """Get token store implementation"""
        pass

    @abstractmethod
    def initialize_all(self) -> None:
        """Initialize all services"""
        pass

    @abstractmethod
    async def shutdown_all(self) -> None:
        """Shutdown all services gracefully"""
        pass

class SupabaseServiceRegistry(ServiceRegistry):
    """Production service registry with Supabase and Redis"""

    _instance: Optional["SupabaseServiceRegistry"] = None

    def __init__(self, config: AppConfig):
        if SupabaseServiceRegistry._instance is not None:
            raise RuntimeError("ServiceRegistry already initialized. Use get_instance().")

        self.config = config
        self._supabase: Optional[Client] = None
        self._redis: Optional[redis.Redis] = None
        self._config_manager: Optional[ConfigManager] = None
        self._token_store: Optional[TokenStore] = None

        # Cache for database managers
        self._db_managers: Dict[str, DatabaseManager] = {}

        SupabaseServiceRegistry._instance = self

    @classmethod
    def get_instance(cls) -> "SupabaseServiceRegistry":
        """Get singleton instance"""
        if cls._instance is None:
            raise RuntimeError("ServiceRegistry not initialized. Call __init__ first.")
        return cls._instance

    def initialize_all(self) -> None:
        """Initialize all services"""
        logger.info("Initializing ServiceRegistry")

        try:
            # Initialize Supabase client
            if self.config.database.supabase_url:
                self._supabase = create_client(
                    self.config.database.supabase_url,
                    self.config.database.supabase_key
                )
                logger.info("Supabase client initialized")

            # Initialize Redis (if needed)
            if self.config.oauth.token_store == "redis":
                self._redis = redis.from_url(
                    self.config.redis.url,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Redis client initialized")

            # Initialize TokenStore
            if self.config.oauth.token_store == "redis":
                from core_renombrador.token_store import RedisTokenStore
                self._token_store = RedisTokenStore(self.config.redis.url)
            else:
                from core_renombrador.token_store import SQLiteTokenStore
                self._token_store = SQLiteTokenStore("oauth_tokens.db")
                asyncio.create_task(self._token_store.init_db())

            logger.info("ServiceRegistry initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ServiceRegistry: {e}")
            raise

    def get_database_manager(self, table_name: str) -> DatabaseManager:
        """Get database manager for specific table"""
        if table_name not in self._db_managers:
            from core_renombrador.database_manager import DatabaseManager
            self._db_managers[table_name] = DatabaseManager(
                use_supabase=True,
                table_name=table_name
            )
        return self._db_managers[table_name]

    def get_algorithms_manager(self) -> DatabaseManager:
        """Get algorithms database manager"""
        return self.get_database_manager("document_algorithms")

    def get_jobs_manager(self) -> DatabaseManager:
        """Get jobs database manager"""
        return self.get_database_manager("jobs")

    def get_users_manager(self) -> DatabaseManager:
        """Get users database manager"""
        return self.get_database_manager("users")

    def get_config_manager(self) -> ConfigManager:
        """Get configuration manager"""
        if self._config_manager is None:
            self._config_manager = ConfigManager()
        return self._config_manager

    def get_token_store(self) -> TokenStore:
        """Get token store"""
        if self._token_store is None:
            raise RuntimeError("TokenStore not initialized. Call initialize_all() first.")
        return self._token_store

    def get_supabase_client(self) -> Client:
        """Get Supabase client directly (for raw queries)"""
        if self._supabase is None:
            raise RuntimeError("Supabase client not initialized")
        return self._supabase

    async def shutdown_all(self) -> None:
        """Shutdown all services gracefully"""
        logger.info("Shutting down ServiceRegistry")

        # Close Redis connection
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")

        # Clear caches
        self._db_managers.clear()

        logger.info("ServiceRegistry shutdown complete")

# Worker Integration
class WorkerRenombrador:
    """Worker for document renaming tasks"""

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.db_manager: Optional[DatabaseManager] = None
        self.algorithms_manager: Optional[DatabaseManager] = None
        self.config_manager: Optional[ConfigManager] = None
        self.token_store: Optional[TokenStore] = None

    async def initialize(self) -> None:
        """Initialize worker with service registry"""
        logger.info("Initializing Worker")

        # Get services from registry
        self.db_manager = self.registry.get_jobs_manager()
        self.algorithms_manager = self.registry.get_algorithms_manager()
        self.config_manager = self.registry.get_config_manager()
        self.token_store = self.registry.get_token_store()

        # Validate algorithms (if direct access enabled)
        config = self.config_manager.get()
        if config.algorithms.source == "direct":
            await self._validate_algorithms()

        logger.info("Worker initialized successfully")

    async def _validate_algorithms(self) -> None:
        """Validate algorithms from database"""
        algorithms = await self.algorithms_manager.list_all()

        if not algorithms:
            raise ValueError("No algorithms found in database")

        active_count = sum(1 for alg in algorithms if alg.get("is_active", True))
        logger.info(f"Validated {len(algorithms)} algorithms ({active_count} active)")

    async def process_job(self, job_id: str) -> None:
        """Process a single job"""
        job = await self.db_manager.get(job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        # Get algorithms for job
        job_algorithms = await self._load_job_algorithms(job_id)

        logger.info(f"Processing job: {job['name']} with {len(job_algorithms)} algorithms")

        # Process job...
        # (Rest of processing logic)

    async def _load_job_algorithms(self, job_id: str) -> list[dict]:
        """Load algorithms for job from junction table"""
        config = self.config_manager.get()

        if config.algorithms.source == "injected":
            # Use algorithms injected in job config
            job = await self.db_manager.get(job_id)
            return job.get("agent_config", {}).get("algorithm_ids", [])
        else:
            # Load algorithms from database directly
            supabase = self.registry.get_supabase_client()
            response = supabase.table("job_algorithms")\
                .select("algorithm_id")\
                .eq("job_id", job_id)\
                .execute()

            algorithm_ids = [row["algorithm_id"] for row in response.data]

            # Load algorithm details
            algorithms = []
            for alg_id in algorithm_ids:
                alg = await self.algorithms_manager.get(alg_id)
                if alg:
                    algorithms.append(alg)

            return algorithms

    async def shutdown(self) -> None:
        """Shutdown worker gracefully"""
        logger.info("Shutting down Worker")
        await self.registry.shutdown_all()
```

### Feature 5: Unified Error Handling

#### Error Handling Architecture

```
Request Flow with Error Handling:
┌─────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Client  │──▶│ CorrelationID│──▶│     API      │──▶│   Service    │
│         │   │  Middleware  │   │   Endpoint   │   │   Layer      │
└─────────┘   └──────────────┘   └──────────────┘   └──────────────┘
                                           │                   │
                                    ┌──────▼──────┐           │
                                    │    Error    │◀──────────│ Exception
                                    │  Handler    │           │
                                    └──────┬──────┘           │
                                           │                   │
                                    ┌──────▼──────┐           │
                                    │ ProblemDetail│          │
                                    │   Builder    │           │
                                    └──────┬──────┘           │
                                           │                   │
                                    ┌──────▼──────┐           │
                                    │     Log     │           │
                                    │  (with CID) │           │
                                    └──────┬──────┘           │
                                           │                   │
                                           ▼                   │
                                    ┌──────────────┐           │
                                    │  HTTP Response│          │
                                    │  (RFC 7807)  │           │
                                    └──────┬──────┘           │
                                           │                   │
                                           ▼                   │
                                    ┌──────────────┐           │
                                    │    Client    │           │
                                    │  (Error JSON)│           │
                                    └──────────────┘           │
```

#### Error Handler Implementation

```python
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import uuid
import logging

logger = logging.getLogger(__name__)

# Error Types
class ErrorType(str, Enum):
    """Standard error types"""
    # OAuth errors
    OAUTH_TOKEN_EXPIRED = "oauth:token-expired"
    OAUTH_INVALID_GRANT = "oauth:invalid-grant"
    OAUTH_REFRESH_FAILED = "oauth:refresh-failed"

    # Database errors
    DATABASE_QUERY_FAILED = "database:query-failed"
    DATABASE_CONNECTION_FAILED = "database:connection-failed"
    DATABASE_CONSTRAINT_VIOLATION = "database:constraint-violation"

    # Validation errors
    VALIDATION_ERROR = "validation:error"
    VALIDATION_MISSING_FIELD = "validation:missing-field"
    VALIDATION_INVALID_FORMAT = "validation:invalid-format"

    # Resource errors
    RESOURCE_NOT_FOUND = "resource:not-found"
    RESOURCE_ALREADY_EXISTS = "resource:already-exists"
    RESOURCE_LOCKED = "resource:locked"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "rate-limit:exceeded"

    # Server errors
    INTERNAL_SERVER_ERROR = "server:internal-error"
    SERVICE_UNAVAILABLE = "service:unavailable"
    BAD_GATEWAY = "server:bad-gateway"

class ErrorCategory(str, Enum):
    """Error category for retry logic"""
    RETRYABLE = "retryable"
    FATAL = "fatal"
    UNKNOWN = "unknown"

# Problem Detail Model
class ProblemDetail(BaseModel):
    """RFC 7807 Problem Details error response"""
    type: str = Field(
        description="URI reference to error type documentation"
    )
    title: str = Field(
        description="Short human-readable title"
    )
    status: int = Field(
        description="HTTP status code"
    )
    detail: str = Field(
        description="Detailed explanation of the error"
    )
    instance: Optional[str] = Field(
        default=None,
        description="URI to specific occurrence"
    )
    correlation_id: str = Field(
        description="Unique identifier for tracing"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the error occurred"
    )
    errors: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Additional error details"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "https://api.example.com/errors/oauth/token-expired",
                "title": "Token Expired",
                "status": 401,
                "detail": "The OAuth token expired. Please refresh.",
                "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2026-04-22T15:30:00Z"
            }
        }

# Custom Exceptions
class AppException(Exception):
    """Base application exception"""

    def __init__(
        self,
        message: str,
        error_type: ErrorType,
        status_code: int = 500,
        details: Optional[Dict] = None
    ):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class OAuthTokenExpiredError(AppException):
    def __init__(self, message: str = "OAuth token expired"):
        super().__init__(
            message=message,
            error_type=ErrorType.OAUTH_TOKEN_EXPIRED,
            status_code=401
        )

class ValidationError(AppException):
    def __init__(self, message: str, errors: List[Dict]):
        super().__init__(
            message=message,
            error_type=ErrorType.VALIDATION_ERROR,
            status_code=400,
            details={"errors": errors}
        )
        self.errors = errors

class ResourceNotFoundError(AppException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            error_type=ErrorType.RESOURCE_NOT_FOUND,
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )

class RateLimitError(AppException):
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            error_type=ErrorType.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details={"retry_after": retry_after}
        )

# Error Categorization
def categorize_error(error_type: ErrorType, status_code: int) -> ErrorCategory:
    """Categorize error based on type and status code"""

    retryable_types = {
        ErrorType.OAUTH_TOKEN_EXPIRED,
        ErrorType.OAUTH_REFRESH_FAILED,
        ErrorType.DATABASE_CONNECTION_FAILED,
        ErrorType.RATE_LIMIT_EXCEEDED,
        ErrorType.SERVICE_UNAVAILABLE,
        ErrorType.BAD_GATEWAY,
    }

    retryable_status_codes = {408, 429, 500, 502, 503, 504}

    if error_type in retryable_types or status_code in retryable_status_codes:
        return ErrorCategory.RETRYABLE
    elif 400 <= status_code < 500:
        return ErrorCategory.FATAL
    else:
        return ErrorCategory.UNKNOWN

# Middleware
class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Inject correlation ID into all requests"""

    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        """Process request with correlation ID"""

        # Extract existing correlation ID or generate new one
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Store in request state
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Convert exceptions to ProblemDetail responses"""

    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        """Process request with error handling"""

        try:
            response = await call_next(request)
            return response

        except AppException as exc:
            return await self._handle_app_exception(request, exc)

        except Exception as exc:
            return await self._handle_generic_exception(request, exc)

    async def _handle_app_exception(
        self,
        request: Request,
        exc: AppException
    ) -> JSONResponse:
        """Handle application exceptions"""

        correlation_id = getattr(request.state, "correlation_id", "unknown")

        # Log error with correlation ID
        logger.error(
            f"Application error (correlation_id={correlation_id}): {exc.message}",
            extra={
                "correlation_id": correlation_id,
                "error_type": exc.error_type.value,
                "status_code": exc.status_code
            }
        )

        # Build ProblemDetail
        problem_detail = ProblemDetail(
            type=f"https://api.example.com/errors/{exc.error_type.value}",
            title=exc.error_type.value.replace(":", " ").title(),
            status=exc.status_code,
            detail=exc.message,
            correlation_id=correlation_id,
            metadata=exc.details
        )

        return JSONResponse(
            status_code=problem_detail.status,
            content=problem_detail.model_dump()
        )

    async def _handle_generic_exception(
        self,
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle generic exceptions"""

        correlation_id = getattr(request.state, "correlation_id", "unknown")

        # Log error with correlation ID
        logger.error(
            f"Unexpected error (correlation_id={correlation_id}): {exc}",
            exc_info=exc,
            extra={"correlation_id": correlation_id}
        )

        # Build ProblemDetail
        problem_detail = ProblemDetail(
            type="https://api.example.com/errors/server/internal-error",
            title="Internal Server Error",
            status=500,
            detail="An unexpected error occurred",
            correlation_id=correlation_id
        )

        return JSONResponse(
            status_code=500,
            content=problem_detail.model_dump()
        )

# Retry Logic
import asyncio

async def retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
):
    """Retry function with exponential backoff"""

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func()

        except AppException as exc:
            last_exception = exc
            category = categorize_error(exc.error_type, exc.status_code)

            if category != ErrorCategory.RETRYABLE or attempt == max_retries:
                raise

            # Calculate delay with exponential backoff
            delay = min(base_delay * (2 ** attempt), max_delay)

            # Add jitter to avoid thundering herd
            if jitter:
                import random
                delay = delay * (0.5 + random.random())

            logger.info(
                f"Retryable error (attempt {attempt + 1}/{max_retries}), "
                f"retrying in {delay:.2f}s: {exc.message}"
            )

            await asyncio.sleep(delay)

    raise last_exception
```

---

## API Design

### OpenAPI 3.0 Specification

```yaml
openapi: 3.0.0
info:
  title: RenameDriverFolders v3 API
  version: 3.0.0
  description: Document renaming system using AI

servers:
  - url: http://localhost:8080/api/v1
    description: Development server
  - url: https://api.example.com/api/v1
    description: Production server

paths:
  # =====================================================
  # Authentication Endpoints
  # =====================================================
  /auth/login:
    post:
      summary: Initiate OAuth flow
      tags: [Authentication]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [redirect_uri]
              properties:
                redirect_uri:
                  type: string
                  format: uri
                  example: "http://localhost:4200/auth/callback"
                state:
                  type: string
                  format: uuid
                  example: "550e8400-e29b-41d4-a716-446655440000"
      responses:
        '200':
          description: OAuth URL generated
          content:
            application/json:
              schema:
                type: object
                properties:
                  auth_url:
                    type: string
                    format: uri
                  state:
                    type: string

  /auth/callback:
    get:
      summary: OAuth callback handler
      tags: [Authentication]
      parameters:
        - name: code
          in: query
          required: true
          schema:
            type: string
        - name: state
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Tokens stored successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  user_id:
                    type: string
                  email:
                    type: string
                  access_token:
                    type: string
                  expires_in:
                    type: integer
                  is_new_user:
                    type: boolean
        '401':
          description: OAuth error
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/ProblemDetail'

  /auth/token:
    get:
      summary: Retrieve cached token
      tags: [Authentication]
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Token retrieved
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  expires_at:
                    type: string
                    format: date-time
                  expires_in:
                    type: integer
                  email:
                    type: string
        '401':
          description: No valid token
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/ProblemDetail'

  /auth/refresh:
    post:
      summary: Manual token refresh
      tags: [Authentication]
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Token refreshed
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  expires_at:
                    type: string
                    format: date-time
                  expires_in:
                    type: integer
                  refreshed:
                    type: boolean
        '401':
          description: Refresh failed
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/ProblemDetail'

  /auth/logout:
    post:
      summary: Invalidate token
      tags: [Authentication]
      security:
        - bearerAuth: []
      responses:
        '204':
          description: Token invalidated

  # =====================================================
  # Jobs Endpoints
  # =====================================================
  /jobs:
    get:
      summary: List all jobs
      tags: [Jobs]
      security:
        - bearerAuth: []
      parameters:
        - name: active
          in: query
          schema:
            type: boolean
        - name: trigger_type
          in: query
          schema:
            type: string
            enum: [manual, scheduled]
      responses:
        '200':
          description: Jobs retrieved
          content:
            application/json:
              schema:
                type: object
                properties:
                  jobs:
                    type: array
                    items:
                      $ref: '#/components/schemas/Job'

    post:
      summary: Create a new job
      tags: [Jobs]
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/JobCreate'
      responses:
        '201':
          description: Job created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Job'
        '400':
          description: Validation error
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/ProblemDetail'

  /jobs/{job_id}:
    get:
      summary: Get job by ID
      tags: [Jobs]
      security:
        - bearerAuth: []
      parameters:
        - name: job_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Job retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Job'
        '404':
          description: Job not found
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/ProblemDetail'

    put:
      summary: Update job
      tags: [Jobs]
      security:
        - bearerAuth: []
      parameters:
        - name: job_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/JobUpdate'
      responses:
        '200':
          description: Job updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Job'
        '404':
          description: Job not found
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/ProblemDetail'

    delete:
      summary: Delete job
      tags: [Jobs]
      security:
        - bearerAuth: []
      parameters:
        - name: job_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '204':
          description: Job deleted
        '404':
          description: Job not found
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/ProblemDetail'

  /jobs/{job_id}/algorithms:
    get:
      summary: Get job algorithms
      tags: [Jobs]
      security:
        - bearerAuth: []
      parameters:
        - name: job_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Job algorithms retrieved
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Algorithm'

    put:
      summary: Set job algorithms
      tags: [Jobs]
      security:
        - bearerAuth: []
      parameters:
        - name: job_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [algorithm_ids]
              properties:
                algorithm_ids:
                  type: array
                  items:
                    type: string
      responses:
        '200':
          description: Job algorithms updated
          content:
            application/json:
              schema:
                type: object
                properties:
                  job_id:
                    type: string
                  algorithm_ids:
                    type: array
                    items:
                      type: string

  # =====================================================
  # Algorithms Endpoints
  # =====================================================
  /algorithms:
    get:
      summary: List all algorithms
      tags: [Algorithms]
      security:
        - bearerAuth: []
      parameters:
        - name: is_active
          in: query
          schema:
            type: boolean
      responses:
        '200':
          description: Algorithms retrieved
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Algorithm'

    post:
      summary: Create a new algorithm
      tags: [Algorithms]
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AlgorithmCreate'
      responses:
        '201':
          description: Algorithm created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Algorithm'

  /algorithms/{algorithm_id}:
    get:
      summary: Get algorithm by ID
      tags: [Algorithms]
      security:
        - bearerAuth: []
      parameters:
        - name: algorithm_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Algorithm retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Algorithm'
        '404':
          description: Algorithm not found
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/ProblemDetail'

    put:
      summary: Update algorithm
      tags: [Algorithms]
      security:
        - bearerAuth: []
      parameters:
        - name: algorithm_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AlgorithmUpdate'
      responses:
        '200':
          description: Algorithm updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Algorithm'

    delete:
      summary: Delete algorithm
      tags: [Algorithms]
      security:
        - bearerAuth: []
      parameters:
        - name: algorithm_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '204':
          description: Algorithm deleted
        '409':
          description: Algorithm used by active jobs
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/ProblemDetail'

# =====================================================
# Components / Schemas
# =====================================================
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    ProblemDetail:
      type: object
      required: [type, title, status, detail, correlation_id]
      properties:
        type:
          type: string
          format: uri
          example: "https://api.example.com/errors/validation/error"
        title:
          type: string
          example: "Validation Error"
        status:
          type: integer
          example: 400
        detail:
          type: string
          example: "Request validation failed"
        instance:
          type: string
          format: uri
        correlation_id:
          type: string
          format: uuid
        timestamp:
          type: string
          format: date-time
        errors:
          type: array
          items:
            type: object
        metadata:
          type: object

    Job:
      type: object
      required: [id, name, trigger_type, source_folder_id, agent_config]
      properties:
        id:
          type: string
        name:
          type: string
        description:
          type: string
        user_id:
          type: string
        trigger_type:
          type: string
          enum: [manual, scheduled]
        schedule:
          type: string
        source_folder_id:
          type: string
        subfolder_filter:
          type: array
          items:
            type: string
        agent_config:
          type: object
        active:
          type: boolean
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    JobCreate:
      type: object
      required: [name, trigger_type, source_folder_id, agent_config]
      properties:
        name:
          type: string
        description:
          type: string
        trigger_type:
          type: string
          enum: [manual, scheduled]
        schedule:
          type: string
        source_folder_id:
          type: string
        subfolder_filter:
          type: array
          items:
            type: string
        agent_config:
          type: object
        algorithm_ids:
          type: array
          items:
            type: string

    JobUpdate:
      type: object
      properties:
        name:
          type: string
        description:
          type: string
        active:
          type: boolean
        subfolder_filter:
          type: array
          items:
            type: string
        agent_config:
          type: object

    Algorithm:
      type: object
      required: [id, name, is_active]
      properties:
        id:
          type: string
        name:
          type: string
        description:
          type: string
        classification_criteria:
          type: string
        extraction_prompt:
          type: string
        output_schema:
          type: object
        filename_format:
          type: string
        is_active:
          type: boolean
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    AlgorithmCreate:
      type: object
      required: [id, name, output_schema, filename_format]
      properties:
        id:
          type: string
        name:
          type: string
        description:
          type: string
        classification_criteria:
          type: string
        extraction_prompt:
          type: string
        output_schema:
          type: object
        filename_format:
          type: string

    AlgorithmUpdate:
      type: object
      properties:
        name:
          type: string
        description:
          type: string
        classification_criteria:
          type: string
        extraction_prompt:
          type: string
        output_schema:
          type: object
        filename_format:
          type: string
        is_active:
          type: boolean
```

---

## Deployment Architecture

### v2/v3 Coexistence Strategy

```
                   Cloud Run
                   ┌─────┐
                   │Router│
                   └──┬──┘
                      │
           ┌──────────┴──────────┐
           │   Feature Flags     │
           │  (LaunchDarkly/DB)  │
           └──────────┬──────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
   ┌────▼────┐                 ┌────▼────┐
   │   v2    │                 │   v3    │
   │  Apps   │                 │  Apps   │
   │         │                 │         │
   │- API    │                 │- API    │
   │- Worker │                 │- Worker │
   │- Front  │                 │- Front  │
   └────┬────┘                 └────┬────┘
        │                           │
        └───────────┬───────────────┘
                    │
             ┌──────▼────────┐
             │  Supabase DB   │
             │  (v3 schema)   │
             └────────────────┘
```

### Rollout Strategy

```
Week 1: Deploy v3 services (0% traffic)
├── Deploy v3 API Server, Worker, Frontend
├── Run smoke tests
├── Feature flag: v3_enabled = false
└── All traffic to v2

Week 2: Route 10% traffic to v3
├── Feature flag: v3_enabled = true for 10% users
├── Monitor metrics: error rate, latency
├── Watch for OAuth issues
└── Prepare rollback plan

Week 3: Route 50% traffic to v3
├── Feature flag: v3_enabled = true for 50% users
├── Full monitoring and alerting
├── User feedback collection
└── Stabilize v3

Week 4: Route 100% to v3
├── Feature flag: v3_enabled = true for all users
├── Monitor for 1 week
├── Decommission v2 services
└── Clean up old code
```

### Rollback Plan

```
Scenario 1: v3 Critical Bug (Day 1-2)
┌─────────────────────────────────────┐
│ Trigger: >5% error rate             │
│ Actions:                            │
│ 1. Set v3_enabled = false           │
│ 2. All traffic → v2                 │
│ 3. Users re-auth (acceptable)       │
│ Time: <1 minute                     │
└─────────────────────────────────────┘

Scenario 2: Data Migration Issue (Day 7-14)
┌─────────────────────────────────────┐
│ Trigger: Migration validation fail  │
│ Actions:                            │
│ 1. Stop v3 services                 │
│ 2. Restore jobs from jobs_archive   │
│ 3. DROP job_algorithms table        │
│ 4. All traffic → v2                 │
│ Time: <10 minutes                   │
└─────────────────────────────────────┘

Scenario 3: OAuth Issues (Day 1-7)
┌─────────────────────────────────────┐
│ Trigger: >10 support tickets        │
│ Actions:                            │
│ 1. Set use_token_cache = false      │
│ 2. Fall back to consent prompt      │
│ 3. Communicate with users           │
│ Time: <1 minute                     │
└─────────────────────────────────────┘
```

### Infrastructure Components

```
Production Infrastructure:
├── Google Cloud Run
│   ├── api-server-v3 (2 instances, 1 CPU, 2GB RAM)
│   ├── worker-renombrador-v3 (2 instances, 2 CPU, 4GB RAM)
│   └── frontend-v3 (1 instance, 1 CPU, 2GB RAM)
├── Cloud Memorystore (Redis)
│   ├── 1 GB instance
│   └── Token cache, distributed locks
├── Cloud Tasks
│   ├── Queue: job-queue
│   └── OIDC authentication
├── Cloud Scheduler
│   └── Triggers scheduled jobs
├── Supabase (PostgreSQL)
│   ├── 3 database instances
│   └── v3 schema with FK constraints
└── Cloud Monitoring
    ├── Metrics: token refresh rate, job processing time
    ├── Logging: correlation IDs, error tracking
    └── Alerts: high error rate, Redis down
```

---

## Testing Strategy

### Test Pyramid

```
         ┌─────────┐
         │   E2E   │  10%  (Slow, full stack)
         │  Tests  │  - User flow tests
         └────┬────┘  - OAuth flow end-to-end
              │
        ┌─────▼─────┐
        │Integration │ 20%  (Medium speed, real dependencies)
        │   Tests    │  - Database integration
        │            │  - Redis integration
        └─────┬─────┘  - OAuth callback tests
              │
    ┌─────────▼─────────┐
    │    Unit Tests     │ 70%  (Fast, isolated)
    │                   │  - TokenManager tests
    │  - TokenStore     │  - ConfigManager tests
    │  - ConfigManager  │  - ServiceRegistry tests
    │  - ErrorHandler   │  - Error handler tests
    │  - Business Logic │  - Job service tests
    └───────────────────┘
```

### Unit Tests

```python
# tests/unit/test_token_manager.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from core_renombrador.token_manager import TokenManager, TokenData

@pytest.fixture
def mock_store():
    store = Mock()
    store.get_token = AsyncMock()
    store.store_token = AsyncMock()
    store.invalidate = AsyncMock()
    return store

@pytest.fixture
def token_manager(mock_store):
    return TokenManager(
        store=mock_store,
        google_client_id="test_client_id",
        google_client_secret="test_secret"
    )

@pytest.fixture
def valid_token():
    return TokenData(
        access_token="valid_token",
        refresh_token="refresh_token",
        expires_at=datetime.now() + timedelta(hours=1),
        scope=["email", "drive.readonly"],
        user_id="user123",
        email="user@example.com",
        issued_at=datetime.now()
    )

@pytest.mark.unit
class TestTokenManager:
    async def test_get_valid_token_returns_cached_when_fresh(self, token_manager, mock_store, valid_token):
        """Should return cached token if not expiring soon"""
        mock_store.get_token.return_value = valid_token

        result = await token_manager.get_valid_token("user123")

        assert result.access_token == "valid_token"
        mock_store.get_token.assert_called_once_with("user123")

    async def test_get_valid_token_refreshes_when_expiring(self, token_manager, mock_store):
        """Should refresh token expiring within threshold"""
        expiring_token = TokenData(
            access_token="expiring_token",
            refresh_token="refresh_token",
            expires_at=datetime.now() + timedelta(minutes=2),  # < 5 min threshold
            scope=["email"],
            user_id="user123",
            email="user@example.com",
            issued_at=datetime.now()
        )
        mock_store.get_token.return_value = expiring_token

        with patch.object(token_manager, '_refresh_token', new_callable=AsyncMock) as mock_refresh:
            mock_refresh.return_value = valid_token
            await token_manager.get_valid_token("user123")
            mock_refresh.assert_called_once()

    async def test_logout_invalidates_token(self, token_manager, mock_store):
        """Should invalidate token on logout"""
        await token_manager.logout("user123")

        mock_store.invalidate.assert_called_once_with("user123")

    async def test_store_oauth_callback_saves_token(self, token_manager, mock_store):
        """Should save token from OAuth callback"""
        await token_manager.store_oauth_callback(
            user_id="user123",
            access_token="new_token",
            refresh_token="new_refresh",
            expires_in=3600,
            scope=["email"],
            email="user@example.com"
        )

        mock_store.store_token.assert_called_once()
        call_args = mock_store.store_token.call_args[0]
        assert call_args[0] == "user123"
        assert call_args[1].access_token == "new_token"

# tests/unit/test_config_manager.py
import pytest
from pathlib import Path
from core_renombrador.config_manager import ConfigManager, AppConfig
import yaml
import tempfile
import os

@pytest.fixture
def temp_config_dir():
    """Create temporary config directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create base config
        base_config = {
            "environment": "development",
            "debug": True,
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "test_db"
            },
            "oauth": {
                "google_client_id": "test_id",
                "google_client_secret": "test_secret",
                "redirect_uri": "http://localhost:4200/auth/callback"
            }
        }

        base_path = Path(tmpdir) / "base.yaml"
        with open(base_path, "w") as f:
            yaml.dump(base_config, f)

        # Create production override
        prod_config = {
            "environment": "production",
            "debug": False,
            "database": {
                "host": "${DATABASE_HOST}",
                "pool_size": 20
            }
        }

        prod_path = Path(tmpdir) / "production.yaml"
        with open(prod_path, "w") as f:
            yaml.dump(prod_config, f)

        yield tmpdir

@pytest.mark.unit
class TestConfigManager:
    def test_load_base_config(self, temp_config_dir):
        """Should load base configuration"""
        manager = ConfigManager(
            config_dir=temp_config_dir,
            environment="development"
        )

        config = manager.get()

        assert config.environment == "development"
        assert config.database.host == "localhost"
        assert config.oauth.google_client_id == "test_id"

    def test_merge_environment_config(self, temp_config_dir):
        """Should merge environment-specific config"""
        manager = ConfigManager(
            config_dir=temp_config_dir,
            environment="production"
        )

        config = manager.get()

        assert config.environment == "production"
        assert config.debug == False  # Overridden by production.yaml
        assert config.database.pool_size == 20  # From production.yaml
        assert config.database.port == 5432  # From base.yaml (inherited)

    def test_env_var_override(self, temp_config_dir):
        """Should override config with environment variables"""
        os.environ["DATABASE_HOST"] = "prod-db.example.com"
        os.environ["LOG_LEVEL"] = "DEBUG"

        try:
            manager = ConfigManager(
                config_dir=temp_config_dir,
                environment="production"
            )

            config = manager.get()

            assert config.database.host == "prod-db.example.com"
            assert config.logging.level == "DEBUG"
        finally:
            del os.environ["DATABASE_HOST"]
            del os.environ["LOG_LEVEL"]

    def test_mask_sensitive_values(self, temp_config_dir):
        """Should mask sensitive values in masked config"""
        manager = ConfigManager(config_dir=temp_config_dir)

        masked = manager.get_masked_config()

        assert masked["oauth"]["google_client_secret"] == "***MASKED***"

# tests/unit/test_service_registry.py
import pytest
from unittest.mock import Mock
from core_renombrador.service_registry import SupabaseServiceRegistry

@pytest.fixture
def mock_config():
    config = Mock()
    config.database.supabase_url = "https://test.supabase.co"
    config.database.supabase_key = "test_key"
    config.oauth.token_store = "sqlite"
    config.redis.url = "redis://localhost:6379"
    return config

@pytest.mark.unit
class TestServiceRegistry:
    def test_singleton_pattern(self, mock_config):
        """Should enforce singleton pattern"""
        registry1 = SupabaseServiceRegistry(mock_config)
        registry2 = SupabaseServiceRegistry.get_instance()

        assert registry1 is registry2

    def test_get_database_manager_caches(self, mock_config):
        """Should cache database managers"""
        registry = SupabaseServiceRegistry(mock_config)

        manager1 = registry.get_database_manager("jobs")
        manager2 = registry.get_database_manager("jobs")

        assert manager1 is manager2

    def test_get_database_manager_different_tables(self, mock_config):
        """Should create different managers for different tables"""
        registry = SupabaseServiceRegistry(mock_config)

        jobs_manager = registry.get_database_manager("jobs")
        algs_manager = registry.get_database_manager("document_algorithms")

        assert jobs_manager is not algs_manager
```

### Integration Tests

```python
# tests/integration/test_oauth_flow_integration.py
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta

@pytest.mark.integration
class TestOAuthFlowIntegration:
    async def test_full_oauth_flow(self, api_client: AsyncClient, mock_google_oauth):
        """Test complete OAuth flow: login -> callback -> token retrieval"""
        # Step 1: Initiate OAuth
        response = await api_client.post(
            "/api/v1/auth/login",
            json={"redirect_uri": "http://localhost:4200/auth/callback"}
        )
        assert response.status_code == 200
        assert "auth_url" in response.json()

        # Step 2: Simulate Google callback
        auth_code = "test_authorization_code"
        response = await api_client.get(
            f"/api/v1/auth/callback?code={auth_code}&state=test_state"
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "email" in data

        # Step 3: Retrieve token from cache
        response = await api_client.get(
            "/api/v1/auth/token",
            headers={"Authorization": f"Bearer {data['access_token']}"}
        )
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data

# tests/integration/test_database_integration.py
import pytest
from supabase import create_client

@pytest.mark.integration
class TestDatabaseIntegration:
    async def test_job_with_algorithms_relationship(self, supabase_client):
        """Test creating job and assigning algorithms"""
        # Create algorithm
        algorithm = {
            "id": "test-alg-1",
            "name": "Test Algorithm",
            "is_active": True,
            "output_schema": {"type": "object"},
            "filename_format": "{date}_{type}"
        }
        supabase_client.table("document_algorithms").insert(algorithm).execute()

        # Create job
        job = {
            "id": "test-job-1",
            "name": "Test Job",
            "trigger_type": "manual",
            "source_folder_id": "test-folder",
            "agent_config": {"model": "gemini-pro"},
            "active": True
        }
        supabase_client.table("jobs").insert(job).execute()

        # Assign algorithm to job
        supabase_client.table("job_algorithms").insert({
            "job_id": "test-job-1",
            "algorithm_id": "test-alg-1"
        }).execute()

        # Verify relationship
        result = supabase_client.table("job_algorithms").select("*").eq("job_id", "test-job-1").execute()
        assert len(result.data) == 1
        assert result.data[0]["algorithm_id"] == "test-alg-1"

        # Cleanup
        supabase_client.table("job_algorithms").delete().eq("job_id", "test-job-1").execute()
        supabase_client.table("jobs").delete().eq("id", "test-job-1").execute()
        supabase_client.table("document_algorithms").delete().eq("id", "test-alg-1").execute()
```

### E2E Tests

```python
# tests/e2e/test_user_flow_e2e.py
import pytest
from playwright.async_api import async_playwright

@pytest.mark.e2e
class TestUserFlowE2E:
    async def test_user_signs_in_and_creates_job(self):
        """Test complete user flow: sign in -> create job -> verify execution"""
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Navigate to app
            await page.goto("http://localhost:4200")

            # Click sign in
            await page.click("button[data-testid='sign-in-button']")

            # Verify OAuth redirect (mock in test environment)
            await page.wait_for_url("**/auth/callback*")

            # Verify user is logged in
            await page.wait_for_selector("[data-testid='user-email']")

            # Navigate to jobs page
            await page.click("a[href='/jobs']")

            # Create new job
            await page.click("button[data-testid='create-job-button']")
            await page.fill("[data-testid='job-name-input']", "E2E Test Job")
            await page.click("button[data-testid='save-job-button']")

            # Verify job created
            await page.wait_for_selector("text=E2E Test Job")

            # Verify job appears in list
            job_elements = await page.locator("[data-testid^='job-']").count()
            assert job_elements > 0

            await browser.close()
```

### Coverage Targets

| Component | Target | Tool |
|-----------|--------|------|
| API Server | >=70% | pytest-cov |
| Worker | >=70% | pytest-cov |
| Core Library | >=80% | pytest-cov |
| Frontend | >=50% | Karma/Istanbul |

---

## Design Decisions

### Decision Log

| ID | Decision | Rationale | Trade-offs |
|----|----------|-----------|------------|
| D1 | **Redis + SQLite fallback for token cache** | Redis for production (fast, scalable), SQLite for dev (simple, no infrastructure) | Added complexity in fallback logic |
| D2 | **Distributed locking for token refresh** | Prevents multiple concurrent refreshes for same user | Redis dependency for production |
| D3 | **Junction table for job-algorithms relationship** | Better referential integrity, easier querying | Additional join required for queries |
| D4 | **Rename target_folder_names to subfolder_filter** | Clearer semantics, matches actual behavior | Migration required for existing data |
| D5 | **ServiceRegistry pattern for Worker** | Enables independent operation, better testing | More upfront complexity |
| D6 | **RFC 7807 for error responses** | Standard format, better client error handling | Requires custom middleware |
| D7 | **Feature flags for rollout** | Safe gradual rollout, instant rollback | Additional infrastructure complexity |
| D8 | **Blue-green deployment strategy** | Zero downtime, safe rollback | Double infrastructure cost during rollout |
| D9 | **70% test coverage target** | Balance between confidence and effort | Lower than some standards (80-90%) |
| D10 | **SQLite encryption for refresh tokens** | Security for development environment | Performance overhead for encryption |

### Architecture Trade-offs

#### 1. Token Store Strategy

**Chosen**: Redis (production) + SQLite (development/fallback)

**Alternatives Considered**:
- Redis only (too complex for local development)
- Database only (too slow for high-frequency access)
- In-memory only (no persistence across restarts)

**Trade-offs**:
- Pros: Fast production access, simple dev setup, automatic fallback
- Cons: Need to maintain two implementations, fallback logic adds complexity

#### 2. Database Junction Table

**Chosen**: Separate `job_algorithms` junction table with FK constraints

**Alternatives Considered**:
- JSON array in `jobs.agent_config.algorithm_ids` (current v2 approach)
- Embedded array in document_algorithms

**Trade-offs**:
- Pros: Referential integrity, prevents orphaned relationships, easier queries
- Cons: Additional join required for some queries, migration complexity

#### 3. Worker Independence

**Chosen**: ServiceRegistry with feature flag for algorithm source

**Alternatives Considered**:
- Keep Worker coupled to API Server (current v2 approach)
- Full microservices with message queue

**Trade-offs**:
- Pros: Worker can run independently, better testing, more flexible
- Cons: More upfront complexity, need to manage service lifecycle

#### 4. Error Handling Strategy

**Chosen**: RFC 7807 Problem Details with correlation IDs

**Alternatives Considered**:
- Custom error format
- Google Cloud Error Reporting format
- Simple JSON error messages

**Trade-offs**:
- Pros: Standard format, better client integration, traceability
- Cons: Requires custom middleware, learning curve for developers

---

## Summary

This technical design document provides:

1. **Architecture Overview**: Complete v3 architecture with component diagrams
2. **Component Design**: Detailed class structures and sequence diagrams for all 5 features
3. **API Design**: Complete OpenAPI 3.0 specification
4. **Deployment Architecture**: v2/v3 coexistence strategy and rollback plans
5. **Testing Strategy**: Test pyramid with unit, integration, and E2E tests
6. **Design Decisions**: 10 key architectural decisions with trade-offs

**Next Steps**: Proceed to task breakdown phase to create implementation checklist.

---

**File created**: `sdd/refactorizacion-v3/design.md`
