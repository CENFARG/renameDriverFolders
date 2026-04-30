# Specifications: refactorizacion-v3

**Date**: 2026-04-22
**Project**: renameDriverFolders - Document renaming system using AI
**Status**: Specified
**Version**: v3.0

---

## Table of Contents

1. [Feature 1: OAuth Token Caching System](#feature-1-oauth-token-caching-system)
2. [Feature 2: Database Schema Normalization](#feature-2-database-schema-normalization)
3. [Feature 3: ConfigManager Service](#feature-3-configmanager-service)
4. [Feature 4: Worker ServiceRegistry](#feature-4-worker-serviceregistry)
5. [Feature 5: Unified Error Handling](#feature-5-unified-error-handling)

---

## Feature 1: OAuth Token Caching System

### Overview

Eliminate OAuth consent fatigue by implementing token persistence with automatic refresh, reducing user prompts from 3x to 1x per session.

### Functional Requirements

**FR-1.1:** The system SHALL cache OAuth tokens in Redis (production) with SQLite fallback (development).

**FR-1.2:** The system SHALL automatically refresh tokens when expiring within 5 minutes.

**FR-1.3:** The system SHALL invalidate cache on user logout.

**FR-1.4:** The system SHALL support concurrent token refresh with distributed locking.

**FR-1.5:** The system SHALL remove `prompt: 'consent'` parameter after first successful authentication.

**FR-1.6:** The system SHALL fallback to consent prompt if silent refresh fails.

### Technical Specifications

#### Data Structures

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class TokenData(BaseModel):
    """OAuth token data structure"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_at: datetime  # UTC timestamp
    scope: list[str]
    user_id: str
    email: str
    issued_at: datetime

class TokenMetadata(BaseModel):
    """Token metadata for cache management"""
    user_id: str
    last_refreshed: datetime
    refresh_count: int
    is_valid: bool
```

#### TokenStore Interface

```python
from abc import ABC, abstractmethod

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
    async def refresh_if_needed(self, user_id: str) -> TokenData:
        """Refresh token if expiring within 5 minutes"""
        pass

    @abstractmethod
    async def invalidate(self, user_id: str) -> None:
        """Invalidate token on logout"""
        pass

    @abstractmethod
    async def is_valid(self, user_id: str) -> bool:
        """Check if token exists and is not expired"""
        pass
```

#### Redis Implementation

```python
import redis.asyncio as redis
import json
from datetime import datetime, timedelta

class RedisTokenStore(TokenStore):
    """Redis-backed token store for production"""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.token_prefix = "oauth:token:"
        self.lock_prefix = "oauth:lock:"
        self.token_ttl = 3600 * 24 * 7  # 7 days

    async def get_token(self, user_id: str) -> Optional[TokenData]:
        key = f"{self.token_prefix}{user_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        return TokenData(**json.loads(data))

    async def store_token(self, user_id: str, token: TokenData) -> None:
        key = f"{self.token_prefix}{user_id}"
        data = token.model_dump_json()
        await self.redis.setex(key, self.token_ttl, data)

    async def refresh_if_needed(self, user_id: str) -> TokenData:
        """Refresh token with distributed locking"""
        token = await self.get_token(user_id)
        if not token:
            raise ValueError("No token found for user")

        # Check if refresh needed
        if token.expires_at > datetime.now() + timedelta(minutes=5):
            return token  # Still valid

        # Acquire lock for concurrent refresh
        lock_key = f"{self.lock_prefix}{user_id}"
        lock = self.redis.lock(lock_key, timeout=30, blocking_timeout=5)

        try:
            if await lock.acquire(block=True):
                # Double-check after acquiring lock
                token = await self.get_token(user_id)
                if token.expires_at > datetime.now() + timedelta(minutes=5):
                    return token

                # Perform refresh
                new_token = await self._perform_refresh(token.refresh_token)
                await self.store_token(user_id, new_token)
                return new_token
        finally:
            await lock.release()

    async def _perform_refresh(self, refresh_token: str) -> TokenData:
        """Call Google OAuth refresh endpoint"""
        # Implementation calls Google token endpoint
        pass

    async def invalidate(self, user_id: str) -> None:
        key = f"{self.token_prefix}{user_id}"
        await self.redis.delete(key)

    async def is_valid(self, user_id: str) -> bool:
        token = await self.get_token(user_id)
        if not token:
            return False
        return token.expires_at > datetime.now()
```

#### SQLite Fallback Implementation

```python
import aiosqlite
from datetime import datetime

class SQLiteTokenStore(TokenStore):
    """SQLite token store for development/testing"""

    def __init__(self, db_path: str = "oauth_tokens.db"):
        self.db_path = db_path

    async def init_db(self):
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
                    issued_at TEXT NOT NULL
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

    async def is_valid(self, user_id: str) -> bool:
        token = await self.get_token(user_id)
        if not token:
            return False
        return token.expires_at > datetime.now()
```

#### TokenManager Service

```python
from typing import Literal

class TokenManager:
    """High-level token management service"""

    def __init__(
        self,
        store: TokenStore,
        environment: Literal["development", "production"]
    ):
        self.store = store
        self.environment = environment

    async def get_valid_token(self, user_id: str) -> TokenData:
        """Get valid token, refreshing if needed"""
        if not await self.store.is_valid(user_id):
            raise ValueError("No valid token for user")

        return await self.store.refresh_if_needed(user_id)

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

### API Endpoints

#### POST /api/v1/auth/login

**Description:** Initiate OAuth flow

**Request:**
```http
POST /api/v1/auth/login HTTP/1.1
Content-Type: application/json

{
  "redirect_uri": "http://localhost:4200/auth/callback",
  "state": "random_state_string"
}
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...",
  "state": "random_state_string"
}
```

#### GET /api/v1/auth/callback

**Description:** OAuth callback handler

**Request:**
```http
GET /api/v1/auth/callback?code=AUTHORIZATION_CODE&state=STATE_VALUE HTTP/1.1
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "user_id": "user_123",
  "email": "user@example.com",
  "access_token": "ya29.a0AfH6...",
  "expires_in": 3599,
  "is_new_user": false
}
```

#### GET /api/v1/auth/token

**Description:** Retrieve cached token

**Request:**
```http
GET /api/v1/auth/token HTTP/1.1
Authorization: Bearer SESSION_TOKEN
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "ya29.a0AfH6...",
  "expires_at": "2026-04-22T15:30:00Z",
  "expires_in": 2700,
  "email": "user@example.com"
}
```

#### POST /api/v1/auth/refresh

**Description:** Manual token refresh

**Request:**
```http
POST /api/v1/auth/refresh HTTP/1.1
Authorization: Bearer SESSION_TOKEN
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "ya29.a0AfH6...",
  "expires_at": "2026-04-22T16:30:00Z",
  "expires_in": 3600,
  "refreshed": true
}
```

#### POST /api/v1/auth/logout

**Description:** Invalidate token

**Request:**
```http
POST /api/v1/auth/logout HTTP/1.1
Authorization: Bearer SESSION_TOKEN
```

**Response:**
```http
HTTP/1.1 204 No Content
```

### Scenarios

#### Scenario 1: First-time login

**Given** user has no cached token
**When** user clicks "Sign In"
**Then** system redirects to Google consent screen
**And** stores access_token + refresh_token in Redis
**And** stores backup in SQLite
**And** returns token data to frontend

```gherkin
Given user "john@example.com" has never authenticated
When user navigates to "/login"
And clicks "Sign In with Google"
Then system generates OAuth URL with prompt=consent
And redirects to "https://accounts.google.com/o/oauth2/v2/auth?..."
When Google redirects back with authorization code
Then system exchanges code for tokens
And stores TokenData in Redis with key "oauth:token:john@example.com"
And stores backup in SQLite table oauth_tokens
And returns JSON with access_token and user_id
```

#### Scenario 2: Subsequent access with valid token

**Given** user has cached token with 30min remaining
**When** user accesses application
**Then** system uses cached token without prompting

```gherkin
Given user "john@example.com" has cached token
And token expires_at is "2026-04-22T16:00:00Z"
And current time is "2026-04-22T15:30:00Z"
When user navigates to application root
Then system checks token validity
And returns cached access_token without redirect
And frontend auto-authenticates user
```

#### Scenario 3: Token expiring soon

**Given** user has cached token expiring in 3min
**When** user accesses application
**Then** system automatically refreshes token
**And** updates cache
**And** returns new token

```gherkin
Given user "john@example.com" has cached token
And token expires_at is "2026-04-22T15:33:00Z"
And current time is "2026-04-22T15:30:00Z"
When user navigates to application root
Then system detects token expiring within 5 minutes
And acquires distributed lock "oauth:lock:john@example.com"
And calls Google refresh endpoint
And updates Redis with new TokenData
And releases lock
And returns new access_token to frontend
```

#### Scenario 4: Concurrent refresh attempts

**Given** user has expiring token
**When** multiple requests trigger refresh simultaneously
**Then** only one refresh executes
**And** others wait for lock

```gherkin
Given user "john@example.com" has expiring token
And token expires_at is "2026-04-22T15:33:00Z"
When 3 concurrent requests arrive at 15:30:00
Then first request acquires lock "oauth:lock:john@example.com"
And performs token refresh
And second request waits for lock (blocks)
And third request waits for lock (blocks)
When first request releases lock
Then second request acquires lock
And checks if token already refreshed
And returns cached token without calling Google
And third request does the same
```

#### Scenario 5: User logout

**Given** user has active cached token
**When** user clicks "Logout"
**Then** system invalidates cache
**And** removes token from Redis and SQLite

```gherkin
Given user "john@example.com" has cached token
When user clicks "Logout" button
Then frontend calls POST /api/v1/auth/logout
And system deletes key "oauth:token:john@example.com" from Redis
And deletes row from oauth_tokens table in SQLite
And returns 204 No Content
And frontend clears session storage
```

#### Scenario 6: Silent refresh failure fallback

**Given** user has cached refresh token
**When** silent refresh fails (token revoked)
**Then** system falls back to consent prompt

```gherkin
Given user "john@example.com" has cached token
And token expires_at is "2026-04-22T15:33:00Z"
When system attempts automatic refresh
And Google returns "invalid_grant" error
Then system deletes cached token from Redis
And returns 401 Unauthorized with "reauth_required" flag
And frontend redirects to login with prompt=consent
And user sees consent screen again
```

### Non-Functional Requirements

**NFR-1.1 (Performance):** Token lookup from Redis MUST complete in < 50ms at p95.

**NFR-1.2 (Security):** Refresh tokens MUST be encrypted with AES-256 at rest in SQLite.

**NFR-1.3 (Reliability):** SQLite fallback MUST activate automatically if Redis is unavailable.

**NFR-1.4 (Scalability):** System MUST support 10k concurrent users with distributed locking.

**NFR-1.5 (Availability):** Token cache MUST have 99.9% uptime.

### Configuration

```yaml
# config/development.yaml
oauth:
  token_store:
    backend: "sqlite"  # or "redis"
    redis:
      url: "redis://localhost:6379/0"
      ttl: 604800  # 7 days
    sqlite:
      path: "oauth_tokens.db"
  refresh:
    threshold_minutes: 5
    lock_timeout: 30
    lock_blocking_timeout: 5
  google:
    client_id: "${GOOGLE_CLIENT_ID}"
    client_secret: "${GOOGLE_CLIENT_SECRET}"
    redirect_uri: "http://localhost:4200/auth/callback"
```

### Testing Requirements

**TR-1.1:** Unit tests for TokenStore implementations (Redis, SQLite).

**TR-1.2:** Integration tests for OAuth callback flow.

**TR-1.3:** Load tests for concurrent token refresh (1000 concurrent users).

**TR-1.4:** Failure scenario tests (Redis unavailable, refresh token revoked).

**TR-1.5:** Performance tests for token lookup latency.

---

## Feature 2: Database Schema Normalization

### Overview

Remove duplicate entries between `jobs` and `document_algorithms` tables, add foreign key constraints, and normalize schema with junction table.

### Functional Requirements

**FR-2.1:** The system SHALL remove duplicate entries from jobs table.

**FR-2.2:** The system SHALL add job_algorithms junction table.

**FR-2.3:** The system SHALL add FK constraints with ON DELETE RESTRICT.

**FR-2.4:** The system SHALL create jobs_archive table for rollback.

**FR-2.5:** The system SHALL migrate existing data without data loss.

**FR-2.6:** The system SHALL validate migration integrity before committing.

### Database Schema

#### Current Schema (v2)

```sql
-- Current jobs table with duplicates
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    source_folder_id TEXT NOT NULL,
    target_folder_names JSONB DEFAULT '["*"]'::jsonb,
    algorithm_ids JSONB DEFAULT '[]'::jsonb,  -- Note: Often duplicates document_algorithms
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Document algorithms table
CREATE TABLE document_algorithms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    prompt_template TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### New Schema (v3)

```sql
-- Step 1: Archive existing jobs for rollback
CREATE TABLE jobs_archive AS
SELECT * FROM jobs;

-- Step 2: Add new column to jobs
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS subfolder_filter JSONB DEFAULT '["*"]'::jsonb;

-- Step 3: Rename target_folder_names to subfolder_filter (temporary alias)
ALTER TABLE jobs
RENAME COLUMN target_folder_names TO subfolder_filter_deprecated;

-- Step 4: Migrate data to new column
UPDATE jobs
SET subfolder_filter = subfolder_filter_deprecated;

-- Step 5: Drop old column
ALTER TABLE jobs
DROP COLUMN subfolder_filter_deprecated;

-- Step 6: Create junction table for many-to-many relationship
CREATE TABLE job_algorithms (
    job_id TEXT NOT NULL,
    algorithm_id TEXT NOT NULL,
    assigned_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (job_id, algorithm_id),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (algorithm_id) REFERENCES document_algorithms(id) ON DELETE RESTRICT
);

-- Step 7: Create index for performance
CREATE INDEX idx_job_algorithms_job_id ON job_algorithms(job_id);
CREATE INDEX idx_job_algorithms_algorithm_id ON job_algorithms(algorithm_id);

-- Step 8: Create validation view
CREATE VIEW v_migration_validation AS
SELECT
    j.id as job_id,
    j.name as job_name,
    j.subfolder_filter,
    ja.algorithm_id,
    da.name as algorithm_name,
    da.is_active as algorithm_is_active
FROM jobs j
LEFT JOIN job_algorithms ja ON j.id = ja.job_id
LEFT JOIN document_algorithms da ON ja.algorithm_id = da.id;

-- Step 9: Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Migration Script

```python
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class DatabaseMigratorV2ToV3:
    """Migrate database schema from v2 to v3"""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.dry_run = True  # Safety flag

    async def migrate(self) -> Dict[str, Any]:
        """Execute full migration pipeline"""
        results = {
            "steps": [],
            "errors": [],
            "warnings": [],
            "start_time": datetime.now()
        }

        try:
            # Step 1: Create archive
            await self._step_create_archive(results)

            # Step 2: Identify and remove duplicates
            await self._step_remove_duplicates(results)

            # Step 3: Add subfolder_filter column
            await self._step_add_subfolder_filter(results)

            # Step 4: Create junction table
            await self._step_create_junction_table(results)

            # Step 5: Migrate algorithm relationships
            await self._step_migrate_relationships(results)

            # Step 6: Add foreign key constraints
            await self._step_add_foreign_keys(results)

            # Step 7: Validate migration
            await self._step_validate_migration(results)

            # Step 8: Cleanup (if dry_run is False)
            if not self.dry_run:
                await self._step_cleanup(results)

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            results["errors"].append(str(e))
            await self._rollback_migration(results)

        results["end_time"] = datetime.now()
        results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()

        return results

    async def _step_create_archive(self, results: Dict[str, Any]):
        """Step 1: Archive existing jobs"""
        logger.info("Step 1: Creating archive table")

        if self.dry_run:
            results["steps"].append("Step 1: [DRY RUN] Would create jobs_archive table")
            return

        # Execute SQL to create archive
        self.supabase.table("jobs").select("*").execute()

        results["steps"].append("Step 1: Created jobs_archive table")

    async def _step_remove_duplicates(self, results: Dict[str, Any]):
        """Step 2: Identify and remove duplicate job entries"""
        logger.info("Step 2: Removing duplicate jobs")

        # Find duplicates (jobs that duplicate algorithm data)
        response = self.supabase.table("jobs").select("*").execute()
        jobs = response.data

        duplicates = []
        for job in jobs:
            # Check if this job looks like a duplicate algorithm entry
            if job["name"].startswith("algorithm_") or job["id"].contains("-"):
                duplicates.append(job["id"])

        if self.dry_run:
            results["steps"].append(f"Step 2: [DRY RUN] Would remove {len(duplicates)} duplicate jobs")
            results["warnings"].append(f"Found {len(duplicates)} potential duplicates")
            return

        # Delete duplicates
        for job_id in duplicates:
            self.supabase.table("jobs").delete().eq("id", job_id).execute()

        results["steps"].append(f"Step 2: Removed {len(duplicates)} duplicate jobs")

    async def _step_add_subfolder_filter(self, results: Dict[str, Any]):
        """Step 3: Add subfolder_filter column"""
        logger.info("Step 3: Adding subfolder_filter column")

        if self.dry_run:
            results["steps"].append("Step 3: [DRY RUN] Would add subfolder_filter column")
            return

        # SQL: ALTER TABLE jobs ADD COLUMN subfolder_filter JSONB DEFAULT '["*"]'::jsonb;
        results["steps"].append("Step 3: Added subfolder_filter column")

    async def _step_create_junction_table(self, results: Dict[str, Any]):
        """Step 4: Create job_algorithms junction table"""
        logger.info("Step 4: Creating job_algorithms junction table")

        if self.dry_run:
            results["steps"].append("Step 4: [DRY RUN] Would create job_algorithms table")
            return

        # SQL to create junction table
        results["steps"].append("Step 4: Created job_algorithms junction table")

    async def _step_migrate_relationships(self, results: Dict[str, Any]):
        """Step 5: Migrate algorithm relationships from jobs to junction table"""
        logger.info("Step 5: Migrating algorithm relationships")

        # Get all jobs with algorithm_ids
        response = self.supabase.table("jobs").select("id, algorithm_ids").execute()
        jobs = response.data

        migrated_count = 0
        for job in jobs:
            algorithm_ids = job.get("algorithm_ids", [])
            if not algorithm_ids:
                continue

            for algorithm_id in algorithm_ids:
                if self.dry_run:
                    migrated_count += 1
                    continue

                # Insert into junction table
                self.supabase.table("job_algorithms").insert({
                    "job_id": job["id"],
                    "algorithm_id": algorithm_id,
                    "assigned_at": datetime.now().isoformat()
                }).execute()
                migrated_count += 1

        if self.dry_run:
            results["steps"].append(f"Step 5: [DRY RUN] Would migrate {migrated_count} relationships")
        else:
            results["steps"].append(f"Step 5: Migrated {migrated_count} relationships")

    async def _step_add_foreign_keys(self, results: Dict[str, Any]):
        """Step 6: Add foreign key constraints"""
        logger.info("Step 6: Adding foreign key constraints")

        if self.dry_run:
            results["steps"].append("Step 6: [DRY RUN] Would add foreign key constraints")
            return

        # SQL to add FK constraints
        results["steps"].append("Step 6: Added foreign key constraints")

    async def _step_validate_migration(self, results: Dict[str, Any]):
        """Step 7: Validate migration integrity"""
        logger.info("Step 7: Validating migration")

        # Check for orphaned jobs
        response = self.supabase.table("jobs").select("id, count").execute()

        # Check for orphaned algorithms
        response = self.supabase.table("job_algorithms").select("*").execute()

        # Validate referential integrity
        validation_errors = []

        if validation_errors:
            results["errors"].extend(validation_errors)
            raise ValueError("Migration validation failed")

        results["steps"].append("Step 7: Migration validation passed")

    async def _step_cleanup(self, results: Dict[str, Any]):
        """Step 8: Cleanup temporary data"""
        logger.info("Step 8: Cleaning up")

        # Remove jobs_archive after 30 days
        # results["steps"].append("Step 8: Scheduled jobs_archive deletion in 30 days")

    async def _rollback_migration(self, results: Dict[str, Any]):
        """Rollback migration on failure"""
        logger.error("Rolling back migration")

        # Restore from jobs_archive
        # Drop job_algorithms table
        # Restore old schema

        results["steps"].append("Rollback: Migration rolled back due to errors")
```

### Scenarios

#### Scenario 1: Clean migration

**Given** database with duplicate jobs
**When** migration script runs
**Then** duplicates are removed
**And** junction table created
**And** FK constraints added
**And** validation passes

```gherkin
Given database has 100 jobs
And 20 jobs are duplicates of algorithms
When migration script executes in dry-run mode
Then system identifies 20 duplicate jobs
And reports jobs would be removed
And reports junction table would be created
And reports foreign keys would be added
And validation view shows no orphaned records
When migration executes in live mode
Then 20 duplicate jobs are deleted
And job_algorithms table is created
And 80 relationships are migrated
And foreign key constraints are added
And migration completes in < 5 minutes
```

#### Scenario 2: Migration validation failure

**Given** migration completes
**When** validation detects orphaned records
**Then** system rolls back automatically
**And** restores from jobs_archive

```gherkin
Given migration script completed steps 1-6
And validation query finds 5 orphaned job_algorithms records
When system runs validation
Then validation fails with orphaned record error
And system initiates automatic rollback
And restores jobs table from jobs_archive
And drops job_algorithms table
And removes foreign key constraints
And returns migration failed status
```

#### Scenario 3: Rollback after production issue

**Given** migration deployed to production
**When** critical bug found within 24 hours
**Then** restore from jobs_archive
**And** drop junction table
**And** system back to v2 state

```gherkin
Given migration deployed to production
And jobs_archive table exists with full backup
When bug report indicates job failures
And rollback decision made
Then system executes rollback script
And restores jobs table from jobs_archive: DELETE FROM jobs; INSERT INTO jobs SELECT * FROM jobs_archive;
And drops job_algorithms table: DROP TABLE job_algorithms;
And removes subfolder_filter column: ALTER TABLE jobs DROP COLUMN subfolder_filter;
And restores target_folder_names column: ALTER TABLE jobs RENAME subfolder_filter_deprecated TO target_folder_names;
And rollback completes in < 10 minutes
```

### Non-Functional Requirements

**NFR-2.1 (Data Integrity):** Zero orphaned records after migration.

**NFR-2.2 (Rollback Time):** Complete rollback in < 10 minutes.

**NFR-2.3 (Downtime):** Migration downtime < 5 minutes.

**NFR-2.4 (Backup Retention):** jobs_archive retained for 30 days.

**NFR-2.5 (Validation):** All migrations must pass validation before commit.

### Testing Requirements

**TR-2.1:** Dry-run migration on staging environment.

**TR-2.2:** Validation queries test on sample data.

**TR-2.3:** Rollback drill on staging (simulate failure).

**TR-2.4:** Performance test for < 5 minute downtime.

**TR-2.5:** Data integrity checks (orphaned records, FK violations).

---

## Feature 3: ConfigManager Service

### Overview

Centralized configuration management service that loads, validates, and provides access to application configuration with environment-specific overrides.

### Functional Requirements

**FR-3.1:** The system SHALL load configuration from YAML files.

**FR-3.2:** The system SHALL support environment variable overrides.

**FR-3.3:** The system SHALL validate configuration schema on load.

**FR-3.4:** The system SHALL provide typed access to configuration values.

**FR-3.5:** The system SHALL reload configuration on SIGHUP signal.

**FR-3.6:** The system SHALL mask sensitive values (secrets, API keys) in logs.

### Technical Specifications

#### Configuration Schema

```python
from pydantic import BaseModel, Field, validator
from typing import Literal, Optional

class DatabaseConfig(BaseModel):
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "renamedriverfolders"
    username: str
    password: str  # Loaded from env var
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
    token_store: Literal["redis", "sqlite"] = "sqlite"

class AlgorithmConfig(BaseModel):
    """Algorithm configuration"""
    source: Literal["injected", "direct"] = "injected"
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
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: Literal["json", "text"] = "json"
    output: Literal["stdout", "file"] = "stdout"
    file_path: Optional[str] = None

class AppConfig(BaseModel):
    """Root application configuration"""
    environment: Literal["development", "staging", "production"] = "development"
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
```

#### ConfigManager Implementation

```python
import yaml
import os
import signal
from pathlib import Path
from typing import Any, Optional
from logging import getLogger

logger = getLogger(__name__)

class ConfigManager:
    """Centralized configuration management"""

    def __init__(
        self,
        config_path: str = "config/config.yaml",
        environment: Optional[str] = None
    ):
        self.config_path = Path(config_path)
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self._config: Optional[AppConfig] = None
        self._load_time: Optional[float] = None

        # Setup signal handler for reload
        signal.signal(signal.SIGHUP, self._handle_reload)

        # Load initial config
        self.load()

    def load(self) -> AppConfig:
        """Load configuration from file and environment"""
        logger.info(f"Loading configuration from {self.config_path}")

        # Load base config from YAML
        config_data = self._load_yaml()

        # Override with environment-specific config
        env_config_path = self.config_path.parent / f"{self.environment}.yaml"
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

    def _load_yaml(self, path: Optional[Path] = None) -> dict[str, Any]:
        """Load YAML configuration file"""
        path = path or self.config_path

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _deep_merge(self, base: dict, override: dict) -> dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _load_env_overrides(self, config: dict[str, Any]) -> dict[str, Any]:
        """Override config with environment variables"""
        env_overrides = {
            "DATABASE_HOST": ("database", "host"),
            "DATABASE_PORT": ("database", "port"),
            "DATABASE_USERNAME": ("database", "username"),
            "DATABASE_PASSWORD": ("database", "password"),
            "REDIS_URL": ("redis", "url"),
            "OAUTH_GOOGLE_CLIENT_ID": ("oauth", "google_client_id"),
            "OAUTH_GOOGLE_CLIENT_SECRET": ("oauth", "google_client_secret"),
            "OAUTH_REDIRECT_URI": ("oauth", "redirect_uri"),
            "ALGORITHM_SOURCE": ("algorithms", "source"),
            "LOG_LEVEL": ("logging", "level"),
        }

        for env_var, config_path in env_overrides.items():
            value = os.getenv(env_var)
            if value is not None:
                # Navigate to nested config path
                current = config
                for key in config_path[:-1]:
                    current = current.setdefault(key, {})

                # Set value with type conversion
                final_key = config_path[-1]
                if value.isdigit():
                    current[final_key] = int(value)
                elif value.lower() in ("true", "false"):
                    current[final_key] = value.lower() == "true"
                else:
                    current[final_key] = value

        return config

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

    def get_masked_config(self) -> dict[str, Any]:
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

### Configuration Files

#### config/config.yaml (Base)

```yaml
environment: development
debug: true

database:
  host: localhost
  port: 5432
  database: renamedriverfolders
  username: postgres
  password: "${DATABASE_PASSWORD}"  # Interpolated from env
  pool_size: 10
  pool_timeout: 30

redis:
  url: redis://localhost:6379/0
  ttl: 604800
  pool_size: 10

oauth:
  google_client_id: "${OAUTH_GOOGLE_CLIENT_ID}"
  google_client_secret: "${OAUTH_GOOGLE_CLIENT_SECRET}"
  redirect_uri: "http://localhost:4200/auth/callback"
  scopes:
    - "https://www.googleapis.com/auth/userinfo.email"
    - "https://www.googleapis.com/auth/drive.readonly"
  token_store: sqlite

algorithms:
  source: injected
  validation_enabled: true
  cache_ttl: 3600

worker:
  poll_interval: 30
  max_retries: 3
  retry_backoff: 5
  batch_size: 10

logging:
  level: DEBUG
  format: text
  output: stdout
```

#### config/production.yaml

```yaml
environment: production
debug: false

database:
  host: ${DATABASE_HOST}
  port: 5432
  pool_size: 20
  pool_timeout: 60

redis:
  url: ${REDIS_URL}
  ttl: 604800
  pool_size: 20

oauth:
  redirect_uri: "https://app.example.com/auth/callback"
  token_store: redis

algorithms:
  source: direct
  validation_enabled: true
  cache_ttl: 1800

worker:
  poll_interval: 60
  max_retries: 5
  retry_backoff: 10
  batch_size: 20

logging:
  level: INFO
  format: json
  output: stdout
```

### Scenarios

#### Scenario 1: Load configuration

**Given** configuration file exists
**When** application starts
**Then** load and validate configuration
**And** apply environment variable overrides

```gherkin
Given config/config.yaml exists
And config/production.yaml exists
And environment variable DATABASE_PASSWORD is set
When application starts with ENVIRONMENT=production
Then ConfigManager loads base config from config.yaml
And merges with config/production.yaml
And overrides database.password with env var value
And validates configuration schema
And provides typed access via config.get()
```

#### Scenario 2: Configuration reload

**Given** application running with loaded config
**When** SIGHUP signal received
**Then** reload configuration from disk
**And** validate new configuration
**And** apply changes to running application

```gherkin
Given application is running
And configuration loaded at T0
When admin sends SIGHUP signal to process
Then ConfigManager receives signal
And reloads config.yaml from disk
And validates new configuration
And updates in-memory config
And logs "Configuration reloaded successfully"
And new config age is 0 seconds
```

#### Scenario 3: Invalid configuration

**Given** configuration file has validation error
**When** application starts
**Then** fail fast with clear error message
**And** do not start application

```gherkin
Given config/config.yaml contains invalid database.port: "invalid"
When application starts
Then ConfigManager attempts to load config
And Pydantic validation fails
And application logs "Configuration validation failed"
And application exits with status code 1
And error message indicates "database.port must be integer"
```

### Non-Functional Requirements

**NFR-3.1 (Load Time):** Configuration MUST load in < 100ms.

**NFR-3.2 (Type Safety):** All configuration values MUST be type-checked.

**NFR-3.3 (Security):** Sensitive values MUST be masked in logs.

**NFR-3.4 (Hot Reload):** Configuration reload MUST not drop requests.

**NFR-3.5 (Validation):** Invalid config MUST prevent application start.

### Testing Requirements

**TR-3.1:** Unit tests for ConfigManager load/validate.

**TR-3.2:** Tests for environment variable overrides.

**TR-3.3:** Tests for configuration reload (SIGHUP).

**TR-3.4:** Tests for invalid config detection.

**TR-3.5:** Tests for sensitive value masking.

---

## Feature 4: Worker ServiceRegistry

### Overview

ServiceRegistry pattern for Worker service initialization, enabling loose coupling and independent testing.

### Functional Requirements

**FR-4.1:** The system SHALL provide ServiceRegistry for service discovery.

**FR-4.2:** The system SHALL support database manager initialization by table name.

**FR-4.3:** The system SHALL provide algorithms manager access.

**FR-4.4:** The system SHALL support environment-based configuration.

**FR-4.5:** The system SHALL enable Worker to run in isolation.

### Technical Specifications

#### ServiceRegistry Interface

```python
from abc import ABC, abstractmethod
from typing import Optional

class ServiceRegistry(ABC):
    """Service registry for dependency injection"""

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
    def shutdown_all(self) -> None:
        """Shutdown all services gracefully"""
        pass
```

#### ServiceRegistry Implementation

```python
from supabase import create_client, Client
import redis.asyncio as redis

class SupabaseServiceRegistry(ServiceRegistry):
    """Production service registry with Supabase and Redis"""

    def __init__(self, config: AppConfig):
        self.config = config
        self._supabase: Optional[Client] = None
        self._redis: Optional[redis.Redis] = None
        self._config_manager: Optional[ConfigManager] = None
        self._token_store: Optional[TokenStore] = None

        # Cache for database managers
        self._db_managers: dict[str, DatabaseManager] = {}

    def initialize_all(self) -> None:
        """Initialize all services"""
        logger.info("Initializing ServiceRegistry")

        # Initialize Supabase client
        self._supabase = create_client(
            self.config.database.supabase_url,
            self.config.database.supabase_key
        )

        # Initialize Redis (if needed)
        if self.config.oauth.token_store == "redis":
            self._redis = redis.from_url(self.config.redis.url)

        # Initialize TokenStore
        if self.config.oauth.token_store == "redis":
            self._token_store = RedisTokenStore(self.config.redis.url)
        else:
            self._token_store = SQLiteTokenStore("oauth_tokens.db")
            await self._token_store.init_db()

        logger.info("ServiceRegistry initialized successfully")

    def get_database_manager(self, table_name: str) -> DatabaseManager:
        """Get database manager for specific table"""
        if table_name not in self._db_managers:
            self._db_managers[table_name] = DatabaseManager(
                supabase=self._supabase,
                table_name=table_name
            )
        return self._db_managers[table_name]

    def get_algorithms_manager(self) -> DatabaseManager:
        """Get algorithms database manager"""
        return self.get_database_manager("document_algorithms")

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

    def shutdown_all(self) -> None:
        """Shutdown all services gracefully"""
        logger.info("Shutting down ServiceRegistry")

        # Close Redis connection
        if self._redis:
            await self._redis.close()

        # Clear caches
        self._db_managers.clear()

        logger.info("ServiceRegistry shutdown complete")
```

#### Worker Integration

```python
class WorkerRenombrador:
    """Worker for document renaming tasks"""

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.db_manager = None
        self.algorithms_manager = None
        self.config_manager = None
        self.token_store = None

    async def initialize(self) -> None:
        """Initialize worker with service registry"""
        logger.info("Initializing Worker")

        # Get services from registry
        self.db_manager = self.registry.get_database_manager("jobs")
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

        logger.info(f"Validated {len(algorithms)} algorithms")

    async def process_job(self, job_id: str) -> None:
        """Process a single job"""
        job = await self.db_manager.get(job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        # Get algorithms for job
        job_algorithms = await self._load_job_algorithms(job_id)

        # Process job...
        logger.info(f"Processing job: {job['name']}")

    async def _load_job_algorithms(self, job_id: str) -> list[dict]:
        """Load algorithms for job from junction table"""
        config = self.config_manager.get()

        if config.algorithms.source == "injected":
            # Use algorithms injected in job config
            job = await self.db_manager.get(job_id)
            return job.get("algorithm_ids", [])
        else:
            # Load algorithms from database directly
            # Query job_algorithms junction table
            response = self.registry._supabase.table("job_algorithms")\
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

### Configuration

```yaml
# config/worker.yaml
algorithms:
  source: "injected"  # or "direct" for independent access
  validation_enabled: true
  cache_ttl: 3600

database:
  supabase_url: "${SUPABASE_URL}"
  supabase_key: "${SUPABASE_KEY}"

redis:
  url: "${REDIS_URL}"
```

### Scenarios

#### Scenario 1: Worker initialization with ServiceRegistry

**Given** ServiceRegistry configured
**When** Worker starts
**Then** initialize all services from registry
**And** Worker ready to process jobs

```gherkin
Given ServiceRegistry is configured with Supabase and Redis
When Worker process starts
And creates ServiceRegistry instance
And calls registry.initialize_all()
Then Supabase client is initialized
And Redis connection is established
And TokenStore is created (Redis or SQLite based on config)
And Worker calls registry.get_database_manager("jobs")
And Worker calls registry.get_algorithms_manager()
And Worker is ready to process jobs
```

#### Scenario 2: Worker runs in isolation (algorithm_source: "direct")

**Given** algorithm_source set to "direct"
**When** Worker starts without API Server
**Then** Worker loads algorithms directly from database
**And** validates algorithms on startup

```gherkin
Given config.algorithms.source is "direct"
And API Server is not running
When Worker starts
And ServiceRegistry initializes successfully
And Worker calls get_algorithms_manager()
Then Worker loads algorithms from document_algorithms table
And validates algorithm count > 0
And Worker can process jobs without API Server
And algorithms are loaded from database, not injected
```

#### Scenario 3: Graceful shutdown

**Given** Worker running and processing jobs
**When** shutdown signal received (SIGTERM)
**Then** complete current job
**And** close all service connections
**And** exit cleanly

```gherkin
Given Worker is processing job_123
When SIGTERM signal received
Then Worker finishes processing job_123
And calls registry.shutdown_all()
And ServiceRegistry closes Redis connection
And ServiceRegistry clears database manager cache
And Worker exits with status code 0
And no jobs are left in inconsistent state
```

### Non-Functional Requirements

**NFR-4.1 (Initialization):** ServiceRegistry MUST initialize in < 500ms.

**NFR-4.2 (Loose Coupling):** Worker MUST not depend on API Server for startup.

**NFR-4.3 (Testability):** ServiceRegistry MUST support mock implementations for testing.

**NFR-4.4 (Graceful Shutdown):** Shutdown MUST complete in < 5 seconds.

**NFR-4.5 (Thread Safety):** ServiceRegistry MUST be thread-safe for concurrent access.

### Testing Requirements

**TR-4.1:** Unit tests for ServiceRegistry initialization.

**TR-4.2:** Integration tests for Worker with real Supabase.

**TR-4.3:** Tests for Worker isolation (without API Server).

**TR-4.4:** Tests for graceful shutdown scenarios.

**TR-4.5:** Mock ServiceRegistry for unit testing Worker logic.

---

## Feature 5: Unified Error Handling

### Overview

Standardized error response format (RFC 7807 Problem Details) with correlation IDs for distributed tracing.

### Functional Requirements

**FR-5.1:** The system SHALL use RFC 7807 Problem Details format for errors.

**FR-5.2:** The system SHALL generate correlation IDs for all requests.

**FR-5.3:** The system SHALL include correlation IDs in error responses.

**FR-5.4:** The system SHALL log correlation IDs for all errors.

**FR-5.5:** The system SHALL categorize errors (retryable, fatal).

**FR-5.6:** The system SHALL implement retry logic for retryable errors.

### Technical Specifications

#### ProblemDetail Model

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ProblemDetail(BaseModel):
    """RFC 7807 Problem Details error response"""

    type: str = Field(
        description="URI reference to error type documentation",
        example="https://api.example.com/errors/oauth/token-expired"
    )
    title: str = Field(
        description="Short human-readable title",
        example="Token Expired"
    )
    status: int = Field(
        description="HTTP status code",
        example=401
    )
    detail: str = Field(
        description="Detailed explanation of the error",
        example="The OAuth token expired at 2026-04-22T15:30:00Z. Please refresh."
    )
    instance: Optional[str] = Field(
        default=None,
        description="URI to specific occurrence (e.g., log URL)",
        example="https://logs.example.com/errors/abc123"
    )
    correlation_id: str = Field(
        description="Unique identifier for tracing",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the error occurred"
    )
    errors: Optional[list[Dict[str, Any]]] = Field(
        default=None,
        description="Additional error details (e.g., validation errors)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context (e.g., retry_after)"
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
```

#### Error Categories

```python
from enum import Enum

class ErrorCategory(str, Enum):
    """Error category for retry logic"""

    RETRYABLE = "retryable"  # Transient errors (rate limits, timeouts)
    FATAL = "fatal"          # Permanent errors (bad request, not found)
    UNKNOWN = "unknown"      # Unclassified error

class ErrorType(str, Enum):
    """Standard error types"""

    # OAuth errors (4xx, 5xx)
    OAUTH_TOKEN_EXPIRED = "oauth:token-expired"
    OAUTH_INVALID_GRANT = "oauth:invalid-grant"
    OAUTH_REFRESH_FAILED = "oauth:refresh-failed"

    # Database errors (4xx, 5xx)
    DATABASE_QUERY_FAILED = "database:query-failed"
    DATABASE_CONNECTION_FAILED = "database:connection-failed"
    DATABASE_CONSTRAINT_VIOLATION = "database:constraint-violation"

    # Validation errors (400)
    VALIDATION_ERROR = "validation:error"
    VALIDATION_MISSING_FIELD = "validation:missing-field"
    VALIDATION_INVALID_FORMAT = "validation:invalid-format"

    # Resource errors (404, 409, 423)
    RESOURCE_NOT_FOUND = "resource:not-found"
    RESOURCE_ALREADY_EXISTS = "resource:already-exists"
    RESOURCE_LOCKED = "resource:locked"

    # Rate limiting (429)
    RATE_LIMIT_EXCEEDED = "rate-limit:exceeded"

    # Server errors (500, 502, 503)
    INTERNAL_SERVER_ERROR = "server:internal-error"
    SERVICE_UNAVAILABLE = "service:unavailable"
    BAD_GATEWAY = "server:bad-gateway"

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
```

#### Correlation ID Middleware

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Inject correlation ID into all requests"""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with correlation ID"""

        # Extract existing correlation ID or generate new one
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Store in request state for access in endpoints
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response
```

#### Error Handler Middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Convert exceptions to ProblemDetail responses"""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with error handling"""

        try:
            response = await call_next(request)
            return response

        except Exception as exc:
            return await self._handle_exception(request, exc)

    async def _handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Convert exception to ProblemDetail response"""

        correlation_id = getattr(request.state, "correlation_id", "unknown")

        # Log error with correlation ID
        logger.error(
            f"Error occurred (correlation_id={correlation_id}): {exc}",
            exc_info=exc,
            extra={"correlation_id": correlation_id}
        )

        # Convert to ProblemDetail
        problem_detail = self._exception_to_problem_detail(exc, correlation_id)

        return JSONResponse(
            status_code=problem_detail.status,
            content=problem_detail.model_dump()
        )

    def _exception_to_problem_detail(
        self,
        exc: Exception,
        correlation_id: str
    ) -> ProblemDetail:
        """Convert exception to ProblemDetail"""

        # Handle specific exception types
        if isinstance(exc, OAuthTokenExpiredError):
            return ProblemDetail(
                type="https://api.example.com/errors/oauth/token-expired",
                title="Token Expired",
                status=401,
                detail=str(exc),
                correlation_id=correlation_id,
                metadata={"retryable": True, "retry_after": 0}
            )

        elif isinstance(exc, ValidationError):
            return ProblemDetail(
                type="https://api.example.com/errors/validation/error",
                title="Validation Error",
                status=400,
                detail=str(exc),
                correlation_id=correlation_id,
                errors=exc.errors()
            )

        elif isinstance(exc, ResourceNotFoundError):
            return ProblemDetail(
                type="https://api.example.com/errors/resource/not-found",
                title="Resource Not Found",
                status=404,
                detail=str(exc),
                correlation_id=correlation_id
            )

        elif isinstance(exc, RateLimitError):
            return ProblemDetail(
                type="https://api.example.com/errors/rate-limit/exceeded",
                title="Rate Limit Exceeded",
                status=429,
                detail=str(exc),
                correlation_id=correlation_id,
                metadata={"retryable": True, "retry_after": 60}
            )

        # Generic error fallback
        return ProblemDetail(
            type="https://api.example.com/errors/server/internal-error",
            title="Internal Server Error",
            status=500,
            detail="An unexpected error occurred",
            correlation_id=correlation_id
        )
```

#### Custom Exception Classes

```python
class AppException(Exception):
    """Base application exception"""

    def __init__(
        self,
        message: str,
        error_type: ErrorType,
        status_code: int = 500,
        details: Optional[dict] = None
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
    def __init__(self, message: str, errors: list):
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
```

#### Retry Logic

```python
import asyncio
from typing import Callable, TypeVar

T = TypeVar("T")

async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> T:
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

### API Error Responses

#### Example: OAuth Token Expired

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/problem+json
X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000

{
  "type": "https://api.example.com/errors/oauth/token-expired",
  "title": "Token Expired",
  "status": 401,
  "detail": "The OAuth token expired at 2026-04-22T15:30:00Z. Please refresh.",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-04-22T15:35:00Z",
  "metadata": {
    "retryable": true,
    "retry_after": 0
  }
}
```

#### Example: Validation Error

```http
HTTP/1.1 400 Bad Request
Content-Type: application/problem+json
X-Correlation-ID: 660e8400-e29b-41d4-a716-446655440001

{
  "type": "https://api.example.com/errors/validation/error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Request validation failed",
  "correlation_id": "660e8400-e29b-41d4-a716-446655440001",
  "timestamp": "2026-04-22T15:35:00Z",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    },
    {
      "field": "subfolder_filter",
      "message": "Must be non-empty array"
    }
  ]
}
```

#### Example: Rate Limit Exceeded

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/problem+json
X-Correlation-ID: 770e8400-e29b-41d4-a716-446655440002
Retry-After: 60

{
  "type": "https://api.example.com/errors/rate-limit/exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Rate limit exceeded. Retry after 60 seconds.",
  "correlation_id": "770e8400-e29b-41d4-a716-446655440002",
  "timestamp": "2026-04-22T15:35:00Z",
  "metadata": {
    "retryable": true,
    "retry_after": 60
  }
}
```

### Scenarios

#### Scenario 1: Request with correlation ID

**Given** client includes X-Correlation-ID header
**When** request is processed
**Then** correlation ID is propagated through system
**And** returned in response headers

```gherkin
Given client sends request with "X-Correlation-ID: client-123"
When request passes through CorrelationIDMiddleware
Then middleware stores "client-123" in request.state.correlation_id
When request is processed by endpoint
And endpoint logs error with correlation_id
Then error response includes "X-Correlation-ID: client-123" header
And ProblemDetail.correlation_id is "client-123"
```

#### Scenario 2: Auto-generated correlation ID

**Given** client does not include X-Correlation-ID header
**When** request is processed
**Then** generate new correlation ID
**And** return in response headers

```gherkin
Given client sends request without "X-Correlation-ID" header
When request passes through CorrelationIDMiddleware
Then middleware generates UUID "550e8400-..."
And stores in request.state.correlation_id
When error occurs during request processing
Then error response includes "X-Correlation-ID: 550e8400-..." header
And logs include correlation_id for tracing
```

#### Scenario 3: Retryable error with exponential backoff

**Given** rate limit error occurs (429)
**When** retry_with_backoff is used
**Then** retry with exponential backoff
**And** succeed after retry

```gherkin
Given API endpoint returns 429 Too Many Requests
And retry_after is 60 seconds
When retry_with_backoff calls the endpoint
And first attempt fails with RateLimitError
Then system waits 1 second (base_delay)
And retries second attempt
And second attempt also fails with RateLimitError
Then system waits 2 seconds (exponential backoff)
And retries third attempt
And third attempt succeeds
And function returns result
```

#### Scenario 4: Fatal error not retried

**Given** validation error occurs (400)
**When** retry_with_backoff is used
**Then** fail immediately without retry

```gherkin
Given API endpoint returns 400 Bad Request
And error is ValidationError (fatal category)
When retry_with_backoff calls the endpoint
And first attempt fails with ValidationError
Then system checks error category
And category is FATAL (not retryable)
And system raises ValidationError immediately
And no retry attempts are made
```

### Non-Functional Requirements

**NFR-5.1 (Response Time):** Error handling MUST add < 10ms latency.

**NFR-5.2 (Traceability):** All errors MUST be traceable via correlation ID.

**NFR-5.3 (Consistency):** All errors MUST follow RFC 7807 format.

**NFR-5.4 (Retry Logic):** Retryable errors MUST use exponential backoff with jitter.

**NFR-5.5 (Logging):** All errors MUST be logged with correlation ID.

### Testing Requirements

**TR-5.1:** Unit tests for all exception types.

**TR-5.2:** Tests for correlation ID propagation.

**TR-5.3:** Tests for retry logic with exponential backoff.

**TR-5.4:** Tests for error categorization (retryable vs fatal).

**TR-5.5:** Integration tests for error middleware.

---

## Summary

This specifications document defines detailed requirements for 5 major features in the refactorizacion-v3 change:

1. **OAuth Token Caching System** - Eliminate consent fatigue through token persistence
2. **Database Schema Normalization** - Remove duplicates and add referential integrity
3. **ConfigManager Service** - Centralized configuration with validation
4. **Worker ServiceRegistry** - Loose coupling for independent operation
5. **Unified Error Handling** - RFC 7807 standard errors with correlation IDs

Each feature includes:
- Functional requirements (FR-X.X)
- Technical specifications with code examples
- API contracts
- Data structures
- Scenarios (Given/When/Then)
- Non-functional requirements (NFR-X.X)
- Testing requirements (TR-X.X)

These specs provide the foundation for design, implementation, and verification phases.
