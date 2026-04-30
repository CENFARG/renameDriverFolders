# Implementation Tasks: refactorizacion-v3

**Date**: 2026-04-22
**Project**: renameDriverFolders - Document renaming system using AI
**Status**: Tasks Complete
**Version**: v3.0

**Total Estimated Hours**: 171
**Total Tasks**: 68

---

## Task Legend

- **Priority**: P0 (critical), P1 (important), P2 (nice-to-have)
- **Time**: Hours estimate
- **Dependencies**: Task IDs that must complete first
- **TDD Steps**: Red (write failing test) → Green (make it pass) → Refactor (clean up)

---

## Phase 1: Critical Fixes (Week 1)
**Estimated Time**: 80 hours

### 1.1 OAuth Token Caching System
**Estimated Time**: 40 hours

#### Task 1.1.1: Create TokenData Pydantic Model ✅
- **Description**: Create the TokenData data model with validation for OAuth tokens
- **Files**:
  - `core_renombrador/models/token.py` (new) ✅
  - `core_renombrador/tests/test_token.py` (new) ✅
- **Dependencies**: None
- **Time**: 2 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_token_data_valid_creation() ✅
  test_token_data_missing_required_fields() ✅
  test_token_data_expires_in_future() ✅
  test_token_data_serialization() ✅
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (model doesn't exist)
  2. ✅ Implement TokenData model → PASSES
  3. ✅ Add validation for expires_at → Still GREEN
- **Acceptance**: TokenData model with all fields, validation, and Pydantic serialization ✅

#### Task 1.1.2: Create TokenStore Abstract Interface ✅
- **Description**: Define the abstract interface for token persistence (get, store, invalidate)
- **Files**:
  - `core_renombrador/token_store.py` (new) ✅
  - `core_renombrador/tests/test_token_store.py` (new) ✅
- **Dependencies**: 1.1.1 ✅
- **Time**: 2 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_token_store_is_abstract() ✅
  test_token_store_has_required_methods() ✅
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (interface doesn't exist)
  2. ✅ Implement TokenStore ABC → PASSES
  3. ✅ Add type hints → Still GREEN
- **Acceptance**: Abstract TokenStore class with get_token, store_token, invalidate methods ✅

#### Task 1.1.3: Implement SQLiteTokenStore
- **Description**: Create SQLite-based token store for development with encryption for refresh tokens
- **Files**:
  - `core_renombrador/token_store.py` (extend)
- **Dependencies**: 1.1.2
- **Time**: 6 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_sqlite_store_initializes_database()
  test_sqlite_store_token()
  test_sqlite_store_retrieves_token()
  test_sqlite_store_updates_existing_token()
  test_sqlite_store_invalidates_token()
  test_sqlite_store_handles_missing_token()
  test_sqlite_store_encrypts_refresh_token()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (implementation doesn't exist)
  2. ✅ Implement SQLiteTokenStore.init_db() → PASSES
  3. ✅ Implement SQLiteTokenStore.get_token() → Still GREEN
  4. ✅ Implement SQLiteTokenStore.store_token() → Still GREEN
  5. ✅ Implement SQLiteTokenStore.invalidate() → Still GREEN
  6. ✅ Add AES-256 encryption for refresh tokens → Still GREEN
- **Acceptance**: SQLiteTokenStore with full CRUD, encryption, and error handling

#### Task 1.1.4: Implement RedisTokenStore
- **Description**: Create Redis-based token store for production with distributed locking
- **Files**:
  - `core_renombrador/token_store.py` (extend)
- **Dependencies**: 1.1.2
- **Time**: 6 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_redis_store_token()
  test_redis_store_retrieves_token()
  test_redis_store_sets_ttl()
  test_redis_store_invalidates_token()
  test_redis_store_acquires_refresh_lock()
  test_redis_store_release_refresh_lock()
  test_redis_store_handles_connection_failure()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (implementation doesn't exist)
  2. ✅ Implement RedisTokenStore with Redis connection → PASSES
  3. ✅ Implement token storage with TTL → Still GREEN
  4. ✅ Implement distributed locking → Still GREEN
  5. ✅ Add connection retry logic → Still GREEN
- **Acceptance**: RedisTokenStore with token caching, TTL, and distributed locks

#### Task 1.1.5: Create TokenManager Service
- **Description**: Implement high-level token management with automatic refresh logic
- **Files**:
  - `core_renombrador/token_manager.py` (new)
- **Dependencies**: 1.1.3, 1.1.4
- **Time**: 8 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_token_manager_returns_valid_token()
  test_token_manager_refreshes_expiring_token()
  test_token_manager_uses_distributed_lock()
  test_token_manager_handles_refresh_failure()
  test_token_manager_stores_oauth_callback()
  test_token_manager_logout_invalidates()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (service doesn't exist)
  2. ✅ Implement TokenManager.get_valid_token() → PASSES
  3. ✅ Implement TokenManager._refresh_token() with lock → Still GREEN
  4. ✅ Implement TokenManager.store_oauth_callback() → Still GREEN
  5. ✅ Implement TokenManager.logout() → Still GREEN
  6. ✅ Add error handling for refresh failures → Still GREEN
- **Acceptance**: TokenManager with automatic refresh, locking, and error handling

#### Task 1.1.6: Create OAuth API Endpoints
- **Description**: Implement FastAPI endpoints for OAuth flow (login, callback, token, refresh, logout)
- **Files**:
  - `api/v1/endpoints/auth.py` (new)
  - `api/v1/api.py` (register routes)
- **Dependencies**: 1.1.5
- **Time**: 8 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_auth_login_returns_auth_url()
  test_auth_callback_stores_token()
  test_auth_token_returns_cached_token()
  test_auth_token_refreshes_when_expiring()
  test_auth_refresh_manually_refreshes()
  test_auth_logout_invalidates()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (endpoints don't exist)
  2. ✅ Implement POST /auth/login → PASSES
  3. ✅ Implement GET /auth/callback → Still GREEN
  4. ✅ Implement GET /auth/token → Still GREEN
  5. ✅ Implement POST /auth/refresh → Still GREEN
  6. ✅ Implement POST /auth/logout → Still GREEN
  7. ✅ Add error handling and validation → Still GREEN
- **Acceptance**: All OAuth endpoints working with TokenManager integration

#### Task 1.1.7: Frontend - Update OAuth Flow
- **Description**: Update Angular frontend to use new token cache endpoints
- **Files**:
  - `frontend/src/app/services/auth.service.ts` (modify)
  - `frontend/src/app/interceptors/token.interceptor.ts` (new)
- **Dependencies**: 1.1.6
- **Time**: 6 hours
- **Priority**: P0
- **TDD Tests**:
  ```typescript
  testAuthServiceChecksTokenCache()
  testAuthServiceAutoRefreshesToken()
  testTokenInterceptorAddsAuthorizationHeader()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (service doesn't check cache)
  2. ✅ Implement token cache check in AuthService → PASSES
  3. ✅ Implement auto-refresh logic → Still GREEN
  4. ✅ Create HTTP interceptor for auth headers → Still GREEN
- **Acceptance**: Frontend uses token cache, auto-refreshes, no repeated prompts

#### Task 1.1.8: Integration Tests for OAuth
- **Description**: Write integration tests for complete OAuth flow
- **Files**:
  - `tests/integration/test_oauth_flow.py` (new)
- **Dependencies**: 1.1.6
- **Time**: 4 hours
- **Priority**: P1
- **TDD Tests**:
  ```python
  test_full_oauth_flow_login_to_token()
  test_token_refresh_distributed_lock()
  test_concurrent_token_refresh()
  test_oauth_rollback_to_consent()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (flow not tested end-to-end)
  2. ✅ Set up test infrastructure with mock Google OAuth → PASSES
  3. ✅ Implement flow tests → Still GREEN
- **Acceptance**: Integration tests covering full OAuth flow with 80% coverage

---

### 1.2 Database FK Constraints
**Estimated Time**: 40 hours

#### Task 1.2.1: Create users table migration
- **Description**: Create migration to add users table with proper constraints
- **Files**:
  - `supabase/migrations/20260422_create_users_table.sql` (new)
- **Dependencies**: None
- **Time**: 3 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_users_table_created()
  test_users_table_has_email_unique()
  test_users_table_has_id_primary_key()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (table doesn't exist)
  2. ✅ Create migration SQL → PASSES
  3. ✅ Add indexes on email → Still GREEN
- **Acceptance**: users table created with proper schema and constraints

#### Task 1.2.2: Add user_id to jobs (nullable)
- **Description**: Add user_id column to jobs table as nullable first
- **Files**:
  - `supabase/migrations/20260422_add_user_id_to_jobs.sql` (new)
- **Dependencies**: 1.2.1
- **Time**: 2 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_jobs_has_user_id_column()
  test_user_id_is_nullable()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (column doesn't exist)
  2. ✅ Create migration to add column → PASSES
- **Acceptance**: user_id column added as nullable

#### Task 1.2.3: Backfill user_id from existing data
- **Description**: Create data migration to backfill user_id from job_executions
- **Files**:
  - `supabase/migrations/20260422_backfill_user_id.sql` (new)
- **Dependencies**: 1.2.2
- **Time**: 4 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_backfill_creates_users()
  test_backfill_maps_jobs_to_users()
  test_backfill_handles_missing_emails()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (data not migrated)
  2. ✅ Create backfill migration → PASSES
  3. ✅ Handle edge cases (null emails, duplicates) → Still GREEN
- **Acceptance**: All existing jobs have user_id populated

#### Task 1.2.4: Make user_id NOT NULL
- **Description**: Alter jobs table to make user_id required
- **Files**:
  - `supabase/migrations/20260422_make_user_id_required.sql` (new)
- **Dependencies**: 1.2.3
- **Time**: 2 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_user_id_not_null_constraint()
  test_cannot_insert_job_without_user()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (constraint doesn't exist)
  2. ✅ Add NOT NULL constraint → PASSES
- **Acceptance**: user_id is required on jobs table

#### Task 1.2.5: Create jobs_archive table
- **Description**: Create archive table for rollback safety
- **Files**:
  - `supabase/migrations/20260422_create_jobs_archive.sql` (new)
- **Dependencies**: 1.2.1
- **Time**: 2 hours
- **Priority**: P1
- **TDD Tests**:
  ```python
  test_jobs_archive_created()
  test_jobs_archive_has_same_schema()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (archive doesn't exist)
  2. ✅ Create archive table → PASSES
- **Acceptance**: jobs_archive table created for rollback

#### Task 1.2.6: Add validation triggers
- **Description**: Add triggers for updated_at and schedule validation
- **Files**:
  - `supabase/migrations/20260422_add_triggers.sql` (new)
- **Dependencies**: 1.2.1
- **Time**: 3 hours
- **Priority**: P1
- **TDD Tests**:
  ```python
  test_updated_at_trigger_fires()
  test_schedule_validates_scheduled_jobs()
  test_schedule_allows_null_for_manual()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (triggers don't exist)
  2. ✅ Create updated_at trigger → PASSES
  3. ✅ Create schedule validation trigger → Still GREEN
- **Acceptance**: Triggers created for updated_at and schedule validation

#### Task 1.2.7: Test migration on staging
- **Description**: Run full migration on staging and validate data integrity
- **Files**:
  - `scripts/test_migration.py` (new)
- **Dependencies**: 1.2.1 - 1.2.6
- **Time**: 6 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_migration_runs_on_staging()
  test_no_orphaned_jobs()
  test_all_jobs_have_users()
  test_jobs_archive_matches()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (migration not tested on staging)
  2. ✅ Create staging test script → PASSES
  3. ✅ Run migration on staging → Still GREEN
  4. ✅ Validate data integrity → Still GREEN
- **Acceptance**: Migration successful on staging with validation

---

## Phase 2: Database Normalization (Week 2)
**Estimated Time**: 29 hours

### 2.1 Remove Duplication
**Estimated Time**: 16 hours

#### Task 2.1.1: Remove seed_default_algorithms()
- **Description**: Remove algorithm seeding from Worker initialization
- **Files**:
  - `worker/renombrador.py` (modify)
- **Dependencies**: None
- **Time**: 2 hours
- **Priority**: P1
- **TDD Tests**:
  ```python
  test_worker_initializes_without_seeding()
  test_worker_loads_algorithms_from_db()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (worker still seeds)
  2. ✅ Remove seed_default_algorithms() call → PASSES
  3. ✅ Worker loads from DB instead → Still GREEN
- **Acceptance**: Worker doesn't seed algorithms, loads from DB

#### Task 2.1.2: Create job_algorithms junction table
- **Description**: Create junction table for job-algorithm relationships
- **Files**:
  - `supabase/migrations/20260422_create_job_algorithms.sql` (new)
- **Dependencies**: 1.2.1
- **Time**: 3 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_job_algorithms_table_created()
  test_job_algorithms_has_composite_pk()
  test_job_algorithms_has_fk_constraints()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (table doesn't exist)
  2. ✅ Create junction table migration → PASSES
  3. ✅ Add FK constraints → Still GREEN
- **Acceptance**: job_algorithms table with proper constraints

#### Task 2.1.3: Migrate existing relationships
- **Description**: Migrate algorithm_ids from jobs.agent_config to junction table
- **Files**:
  - `supabase/migrations/20260422_migrate_job_algorithms.sql` (new)
- **Dependencies**: 2.1.2
- **Time**: 4 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_migrates_existing_relationships()
  test_handles_jobs_with_no_algorithms()
  test_handles_duplicate_algorithm_ids()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (data not migrated)
  2. ✅ Create migration script → PASSES
  3. ✅ Handle edge cases → Still GREEN
- **Acceptance**: All job-algorithm relationships migrated

#### Task 2.1.4: Add FK constraints
- **Description**: Add foreign key constraints to junction table
- **Files**:
  - `supabase/migrations/20260422_add_junction_fks.sql` (new)
- **Dependencies**: 2.1.3
- **Time**: 2 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_cannot_delete_job_with_relationships()
  test_cannot_delete_algorithm_used_by_job()
  test_cascade_deletes_job_relationships()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (constraints don't exist)
  2. ✅ Add FK constraints → PASSES
- **Acceptance**: FK constraints prevent orphaned records

#### Task 2.1.5: Validate migration
- **Description**: Validate migration and create check queries
- **Files**:
  - `scripts/validate_migration.py` (new)
- **Dependencies**: 2.1.4
- **Time**: 3 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_no_orphaned_job_algorithms()
  test_all_jobs_have_algorithms()
  test_validation_view_works()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (no validation)
  2. ✅ Create validation script → PASSES
  3. ✅ Create validation view → Still GREEN
- **Acceptance**: Migration validated, no orphaned records

#### Task 2.1.6: Update API to use junction table
- **Description**: Update job CRUD to use job_algorithms table
- **Files**:
  - `api/v1/endpoints/jobs.py` (modify)
- **Dependencies**: 2.1.5
- **Time**: 4 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_create_job_creates_relationships()
  test_update_job_updates_relationships()
  test_delete_job_deletes_relationships()
  test_get_job_includes_algorithms()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (API uses old format)
  2. ✅ Update POST /jobs to create relationships → PASSES
  3. ✅ Update PUT /jobs to update relationships → Still GREEN
  4. ✅ Update DELETE /jobs to cascade → Still GREEN
  5. ✅ Update GET /jobs to include algorithms → Still GREEN
- **Acceptance**: API endpoints use junction table correctly

---

### 2.2 ConfigManager
**Estimated Time**: 13 hours

#### Task 2.2.1: Create Config class structure
- **Description**: Create Pydantic models for configuration
- **Files**:
  - `core_renombrador/config.py` (new)
- **Dependencies**: None
- **Time**: 3 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_app_config_validates()
  test_database_config_validates()
  test_oauth_config_validates()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (models don't exist)
  2. ✅ Create Pydantic config models → PASSES
  3. ✅ Add validation → Still GREEN
- **Acceptance**: All config models with validation

#### Task 2.2.2: Implement YAML loader
- **Description**: Implement YAML file loading with merge logic
- **Files**:
  - `core_renombrador/config_manager.py` (new)
- **Dependencies**: 2.2.1
- **Time**: 3 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_loads_base_config()
  test_merges_environment_config()
  test_handles_missing_file()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (loader doesn't exist)
  2. ✅ Implement YAML loader → PASSES
  3. ✅ Implement deep merge → Still GREEN
- **Acceptance**: YAML loader with merge logic

#### Task 2.2.3: Add environment override logic
- **Description**: Add environment variable overrides
- **Files**:
  - `core_renombrador/config_manager.py` (extend)
- **Dependencies**: 2.2.2
- **Time**: 3 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_env_var_overrides_yaml()
  test_type_conversion_string_to_int()
  test_type_conversion_string_to_bool()
  test_type_conversion_string_to_list()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (no override logic)
  2. ✅ Implement env var mapping → PASSES
  3. ✅ Implement type conversion → Still GREEN
- **Acceptance**: Environment variables override YAML values

#### Task 2.2.4: Add validation with Pydantic
- **Description**: Add Pydantic validation for all config values
- **Files**:
  - `core_renombrador/config_manager.py` (extend)
- **Dependencies**: 2.2.3
- **Time**: 2 hours
- **Priority**: P1
- **TDD Tests**:
  ```python
  test_validates_required_fields()
  test_validates_url_format()
  test_validates_port_range()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (no validation)
  2. ✅ Add Pydantic validators → PASSES
- **Acceptance**: All config validated with Pydantic

#### Task 2.2.5: Add hot reload signal handler
- **Description**: Add SIGHUP handler for config reload
- **Files**:
  - `core_renombrador/config_manager.py` (extend)
- **Dependencies**: 2.2.4
- **Time**: 2 hours
- **Priority**: P2
- **TDD Tests**:
  ```python
  test_sighup_reloads_config()
  test_reload_updates_cached_config()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (no signal handler)
  2. ✅ Implement SIGHUP handler → PASSES
- **Acceptance**: Config reloads on SIGHUP signal

#### Task 2.2.6: Update Worker to use ConfigManager
- **Description**: Replace hardcoded config with ConfigManager
- **Files**:
  - `worker/renombrador.py` (modify)
- **Dependencies**: 2.2.5
- **Time**: 4 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_worker_uses_config_manager()
  test_worker_reads_database_config()
  test_worker_reads_algorithm_config()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (worker uses hardcoded config)
  2. ✅ Initialize ConfigManager in Worker → PASSES
  3. ✅ Replace all config reads → Still GREEN
- **Acceptance**: Worker uses ConfigManager for all configuration

---

## Phase 3: Worker Independence (Week 3)
**Estimated Time**: 18 hours

### 3.1 ServiceRegistry
**Estimated Time**: 10 hours

#### Task 3.1.1: Create ServiceRegistry class
- **Description**: Create abstract ServiceRegistry interface
- **Files**:
  - `core_renombrador/service_registry.py` (new)
- **Dependencies**: None
- **Time**: 2 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_service_registry_is_abstract()
  test_service_registry_has_required_methods()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (interface doesn't exist)
  2. ✅ Create ServiceRegistry ABC → PASSES
- **Acceptance**: Abstract ServiceRegistry interface defined

#### Task 3.1.2: Implement SupabaseServiceRegistry
- **Description**: Create production ServiceRegistry with Supabase and Redis
- **Files**:
  - `core_renombrador/service_registry.py` (extend)
- **Dependencies**: 3.1.1, 2.2.6, 1.1.5
- **Time**: 4 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_singleton_pattern()
  test_initialize_all_services()
  test_get_database_manager()
  test_get_token_store()
  test_shutdown_all()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (implementation doesn't exist)
  2. ✅ Implement SupabaseServiceRegistry → PASSES
  3. ✅ Implement singleton pattern → Still GREEN
  4. ✅ Implement initialize_all() → Still GREEN
  5. ✅ Implement service getters → Still GREEN
  6. ✅ Implement shutdown_all() → Still GREEN
- **Acceptance**: SupabaseServiceRegistry with all services

#### Task 3.1.3: Add health checks
- **Description**: Add health check endpoints for all services
- **Files**:
  - `api/v1/endpoints/health.py` (new)
- **Dependencies**: 3.1.2
- **Time**: 2 hours
- **Priority**: P1
- **TDD Tests**:
  ```python
  test_health_check_returns_200()
  test_health_check_checks_database()
  test_health_check_checks_redis()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (no health check)
  2. ✅ Implement health check endpoint → PASSES
  3. ✅ Add DB check → Still GREEN
  4. ✅ Add Redis check → Still GREEN
- **Acceptance**: Health check endpoint monitoring all services

#### Task 3.1.4: Update Worker initialization
- **Description**: Update Worker to use ServiceRegistry
- **Files**:
  - `worker/renombrador.py` (modify)
- **Dependencies**: 3.1.2
- **Time**: 2 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_worker_uses_service_registry()
  test_worker_initializes_with_registry()
  test_worker_shutdowns_registry()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (worker doesn't use registry)
  2. ✅ Initialize Worker with ServiceRegistry → PASSES
  3. ✅ Replace direct service access → Still GREEN
- **Acceptance**: Worker uses ServiceRegistry for all dependencies

---

### 3.2 Algorithm Loader
**Estimated Time**: 8 hours

#### Task 3.2.1: Create AlgorithmLoader interface
- **Description**: Define abstract interface for algorithm loading
- **Files**:
  - `core_renombrador/algorithm_loader.py` (new)
- **Dependencies**: None
- **Time**: 2 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_algorithm_loader_is_abstract()
  test_algorithm_loader_has_load_method()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (interface doesn't exist)
  2. ✅ Create AlgorithmLoader ABC → PASSES
- **Acceptance**: Abstract AlgorithmLoader interface

#### Task 3.2.2: Implement SupabaseAlgorithmLoader
- **Description**: Create Supabase-based algorithm loader
- **Files**:
  - `core_renombrador/algorithm_loader.py` (extend)
- **Dependencies**: 3.2.1, 3.1.2
- **Time**: 3 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_loads_all_algorithms()
  test_loads_active_algorithms_only()
  test_caches_loaded_algorithms()
  test_handles_database_error()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (implementation doesn't exist)
  2. ✅ Implement SupabaseAlgorithmLoader → PASSES
  3. ✅ Add caching logic → Still GREEN
  4. ✅ Add error handling → Still GREEN
- **Acceptance**: SupabaseAlgorithmLoader with caching

#### Task 3.2.3: Update Worker to use loader
- **Description**: Replace algorithm injection with AlgorithmLoader
- **Files**:
  - `worker/renombrador.py` (modify)
- **Dependencies**: 3.2.2, 3.1.4
- **Time**: 2 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_worker_uses_algorithm_loader()
  test_worker_loads_algorithms_on_init()
  test_worker_validates_algorithms()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (worker doesn't use loader)
  2. ✅ Initialize Worker with AlgorithmLoader → PASSES
  3. ✅ Replace algorithm injection → Still GREEN
- **Acceptance**: Worker uses AlgorithmLoader for algorithms

#### Task 3.2.4: Test Worker independence
- **Description**: Write integration tests for Worker independence
- **Files**:
  - `tests/integration/test_worker_independence.py` (new)
- **Dependencies**: 3.2.3
- **Time**: 2 hours
- **Priority**: P1
- **TDD Tests**:
  ```python
  test_worker_runs_without_api_server()
  test_worker_connects_to_supabase_directly()
  test_worker_processes_job_successfully()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (not tested)
  2. ✅ Create integration test → PASSES
- **Acceptance**: Worker runs independently with integration tests

---

## Phase 4: Error Handling & Polish (Week 4)
**Estimated Time**: 44 hours

### 4.1 Unified Error Handling
**Estimated Time**: 16 hours

#### Task 4.1.1: Create exception hierarchy
- **Description**: Create custom exception classes with error types
- **Files**:
  - `core_renombrador/exceptions.py` (new)
- **Dependencies**: None
- **Time**: 3 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_app_exception_has_error_type()
  test_oauth_token_expired_exception()
  test_validation_exception()
  test_resource_not_found_exception()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (exceptions don't exist)
  2. ✅ Create AppException base → PASSES
  3. ✅ Create specific exceptions → Still GREEN
- **Acceptance**: Exception hierarchy with error types

#### Task 4.1.2: Implement RFC 7807 middleware
- **Description**: Create error handler middleware with ProblemDetail responses
- **Files**:
  - `api/v1/middleware/error_handler.py` (new)
- **Dependencies**: 4.1.1
- **Time**: 5 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_handles_app_exception()
  test_handles_generic_exception()
  test_returns_problem_detail()
  test_includes_correlation_id()
  test_logs_error()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (middleware doesn't exist)
  2. ✅ Implement ErrorHandlerMiddleware → PASSES
  3. ✅ Create ProblemDetail model → Still GREEN
  4. ✅ Add error logging → Still GREEN
- **Acceptance**: Error handler middleware with RFC 7807 responses

#### Task 4.1.3: Add correlation ID middleware
- **Description**: Add middleware to inject correlation IDs
- **Files**:
  - `api/v1/middleware/correlation_id.py` (new)
- **Dependencies**: None
- **Time**: 2 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_generates_correlation_id()
  test_uses_existing_correlation_id()
  test_adds_correlation_id_to_response()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (middleware doesn't exist)
  2. ✅ Implement CorrelationIDMiddleware → PASSES
- **Acceptance**: Correlation ID middleware

#### Task 4.1.4: Update all endpoints to use new errors
- **Description**: Replace error handling in all endpoints with custom exceptions
- **Files**:
  - `api/v1/endpoints/*.py` (modify all)
- **Dependencies**: 4.1.2, 4.1.3
- **Time**: 4 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_auth_endpoint_raises_oauth_exception()
  test_jobs_endpoint_raises_validation_exception()
  test_algorithms_endpoint_raises_not_found_exception()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (endpoints use old errors)
  2. ✅ Update auth endpoints → PASSES
  3. ✅ Update jobs endpoints → Still GREEN
  4. ✅ Update algorithms endpoints → Still GREEN
- **Acceptance**: All endpoints use custom exceptions

#### Task 4.1.5: Test error responses
- **Description**: Test error responses and correlation ID propagation
- **Files**:
  - `tests/integration/test_error_handling.py` (new)
- **Dependencies**: 4.1.4
- **Time**: 2 hours
- **Priority**: P1
- **TDD Tests**:
  ```python
  test_error_response_follows_rfc_7807()
  test_correlation_id_propagates()
  test_retryable_errors_marked_correctly()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (errors not tested)
  2. ✅ Create integration tests → PASSES
- **Acceptance**: Error responses validated

---

### 4.2 Testing & Documentation
**Estimated Time**: 20 hours

#### Task 4.2.1: Write unit tests (TokenCache)
- **Description**: Complete unit tests for TokenCache and TokenManager
- **Files**:
  - `tests/unit/test_token_manager.py` (new)
  - `tests/unit/test_token_store.py` (new)
- **Dependencies**: 1.1.8
- **Time**: 4 hours
- **Priority**: P1
- **TDD Tests**:
  ```python
  # (Already covered in task 1.1.1 - 1.1.5)
  ```
- **TDD Steps**:
  1. ✅ Review existing tests → FAILS (missing coverage)
  2. ✅ Add missing unit tests → PASSES
  3. ✅ Achieve 80% coverage → Still GREEN
- **Acceptance**: 80%+ coverage for TokenCache

#### Task 4.2.2: Write unit tests (ConfigManager)
- **Description**: Complete unit tests for ConfigManager
- **Files**:
  - `tests/unit/test_config_manager.py` (new)
- **Dependencies**: 2.2.6
- **Time**: 3 hours
- **Priority**: P1
- **TDD Tests**:
  ```python
  # (Already covered in task 2.2.1 - 2.2.5)
  ```
- **TDD Steps**:
  1. ✅ Review existing tests → FAILS (missing coverage)
  2. ✅ Add missing unit tests → PASSES
  3. ✅ Achieve 80% coverage → Still GREEN
- **Acceptance**: 80%+ coverage for ConfigManager

#### Task 4.2.3: Write unit tests (ServiceRegistry)
- **Description**: Complete unit tests for ServiceRegistry
- **Files**:
  - `tests/unit/test_service_registry.py` (new)
- **Dependencies**: 3.1.4
- **Time**: 2 hours
- **Priority**: P1
- **TDD Tests**:
  ```python
  # (Already covered in task 3.1.2 - 3.1.4)
  ```
- **TDD Steps**:
  1. ✅ Review existing tests → FAILS (missing coverage)
  2. ✅ Add missing unit tests → PASSES
  3. ✅ Achieve 80% coverage → Still GREEN
- **Acceptance**: 80%+ coverage for ServiceRegistry

#### Task 4.2.4: Write integration tests
- **Description**: Complete integration test suite
- **Files**:
  - `tests/integration/test_database_integration.py` (new)
  - `tests/integration/test_oauth_integration.py` (new)
  - `tests/integration/test_worker_integration.py` (new)
- **Dependencies**: 4.1.5
- **Time**: 5 hours
- **Priority**: P1
- **TDD Tests**:
  ```python
  test_database_constraints_work()
  test_oauth_flow_end_to_end()
  test_worker_processes_job()
  test_service_registry_integration()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (integration not tested)
  2. ✅ Create integration tests → PASSES
- **Acceptance**: Integration tests covering critical flows

#### Task 4.2.5: Write E2E tests
- **Description**: Create E2E tests with Playwright
- **Files**:
  - `tests/e2e/test_user_flow_e2e.py` (new)
- **Dependencies**: 4.2.4
- **Time**: 4 hours
- **Priority**: P2
- **TDD Tests**:
  ```python
  test_user_signs_in_and_creates_job()
  test_user_edits_job()
  test_user_views_job_executions()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (E2E not tested)
  2. ✅ Create Playwright tests → PASSES
- **Acceptance**: E2E tests for critical user flows

#### Task 4.2.6: Update API documentation
- **Description**: Update OpenAPI spec and create API docs
- **Files**:
  - `docs/api/openapi.yaml` (update)
  - `docs/api/getting-started.md` (new)
- **Dependencies**: 4.1.4
- **Time**: 3 hours
- **Priority**: P1
- **TDD Tests**: N/A
- **TDD Steps**: N/A (documentation task)
- **Acceptance**: Complete API documentation with examples

#### Task 4.2.7: Create deployment guide
- **Description**: Create guide for deploying v3
- **Files**:
  - `docs/deployment/v3-deployment.md` (new)
- **Dependencies**: 4.2.6
- **Time**: 3 hours
- **Priority**: P1
- **TDD Tests**: N/A
- **TDD Steps**: N/A (documentation task)
- **Acceptance**: Deployment guide with migrations and rollback

---

### 4.3 Deployment
**Estimated Time**: 16 hours

#### Task 4.3.1: Set up v3 Cloud Run services
- **Description**: Create Cloud Run services for v3 (API, Worker, Frontend)
- **Files**:
  - `infra/cloud-run/v3-api.yaml` (new)
  - `infra/cloud-run/v3-worker.yaml` (new)
  - `infra/cloud-run/v3-frontend.yaml` (new)
- **Dependencies**: 4.2.7
- **Time**: 3 hours
- **Priority**: P0
- **TDD Tests**: N/A (infrastructure)
- **TDD Steps**: N/A
- **Acceptance**: Cloud Run services deployed (0% traffic)

#### Task 4.3.2: Configure feature flags
- **Description**: Set up feature flags for v3 rollout
- **Files**:
  - `config/feature_flags.yaml` (new)
- **Dependencies**: 4.3.1
- **Time**: 2 hours
- **Priority**: P0
- **TDD Tests**:
  ```python
  test_v3_disabled_routes_to_v2()
  test_v3_enabled_routes_to_v3()
  ```
- **TDD Steps**:
  1. ✅ Write test → FAILS (no feature flags)
  2. ✅ Create feature flag system → PASSES
- **Acceptance**: Feature flags configured, v3 disabled

#### Task 4.3.3: Deploy v3 alongside v2 (0% traffic)
- **Description**: Deploy v3 services with 0% traffic
- **Files**: N/A (deployment)
- **Dependencies**: 4.3.2
- **Time**: 2 hours
- **Priority**: P0
- **TDD Tests**: N/A
- **TDD Steps**: N/A
- **Acceptance**: v3 deployed, all traffic to v2

#### Task 4.3.4: Test rollback procedures
- **Description**: Test rollback scenarios and document procedures
- **Files**:
  - `docs/deployment/rollback-procedures.md` (new)
- **Dependencies**: 4.3.3
- **Time**: 3 hours
- **Priority**: P0
- **TDD Tests**: N/A
- **TDD Steps**: N/A (documentation and manual testing)
- **Acceptance**: Rollback procedures tested and documented

#### Task 4.3.5: Gradual rollout (10% → 50% → 100%)
- **Description**: Execute gradual rollout over 2 weeks
- **Files**: N/A (deployment)
- **Dependencies**: 4.3.4
- **Time**: 4 hours (monitoring time)
- **Priority**: P0
- **TDD Tests**: N/A
- **TDD Steps**: N/A
- **Acceptance**: v3 at 100% traffic, stable

#### Task 4.3.6: Monitor and validate
- **Description**: Monitor metrics and validate v3 stability
- **Files**: N/A (monitoring)
- **Dependencies**: 4.3.5
- **Time**: 2 hours
- **Priority**: P0
- **TDD Tests**: N/A
- **TDD Steps**: N/A
- **Acceptance**: Metrics show <1% error rate

#### Task 4.3.7: Decommission v2
- **Description**: Shut down v2 services and clean up
- **Files**: N/A (deployment)
- **Dependencies**: 4.3.6
- **Time**: 2 hours
- **Priority**: P1
- **TDD Tests**: N/A
- **TDD Steps**: N/A
- **Acceptance**: v2 services decommissioned

---

## Task Summary

### By Phase
| Phase | Tasks | Hours |
|-------|-------|-------|
| Phase 1: Critical Fixes | 16 | 80 |
| Phase 2: Database Normalization | 13 | 29 |
| Phase 3: Worker Independence | 8 | 18 |
| Phase 4: Error Handling & Polish | 23 | 44 |
| **Total** | **68** | **171** |

### By Priority
| Priority | Tasks | Hours |
|----------|-------|-------|
| P0 (Critical) | 42 | 133 |
| P1 (Important) | 21 | 34 |
| P2 (Nice-to-have) | 5 | 4 |

### Critical Path
The critical path for this refactor is:
1. **Week 1**: Phase 1 (OAuth + Database FK) → 80 hours
2. **Week 2**: Phase 2 (Normalization + ConfigManager) → 29 hours
3. **Week 3**: Phase 3 (Worker Independence) → 18 hours
4. **Week 4**: Phase 4 (Error Handling + Deployment) → 44 hours

**Total Timeline**: 4 weeks (171 hours)

---

## Dependencies Graph

```
Phase 1.1 (OAuth)
├── 1.1.1 (TokenData)
├── 1.1.2 (TokenStore interface)
│   ├── 1.1.3 (SQLite)
│   └── 1.1.4 (Redis)
│       └── 1.1.5 (TokenManager)
│           ├── 1.1.6 (OAuth API)
│           │   ├── 1.1.7 (Frontend)
│           │   └── 1.1.8 (Integration Tests)
│           └── 4.1.2 (Error Handler)

Phase 1.2 (Database FK)
├── 1.2.1 (users table)
├── 1.2.2 (add user_id)
├── 1.2.3 (backfill)
├── 1.2.4 (make NOT NULL)
├── 1.2.5 (jobs_archive)
├── 1.2.6 (triggers)
└── 1.2.7 (test on staging)

Phase 2.1 (Normalization)
├── 2.1.1 (remove seeding)
├── 2.1.2 (junction table)
├── 2.1.3 (migrate relationships)
├── 2.1.4 (FK constraints)
├── 2.1.5 (validate)
└── 2.1.6 (update API)

Phase 2.2 (ConfigManager)
├── 2.2.1 (Config models)
├── 2.2.2 (YAML loader)
├── 2.2.3 (env overrides)
├── 2.2.4 (validation)
├── 2.2.5 (hot reload)
└── 2.2.6 (Worker integration)

Phase 3.1 (ServiceRegistry)
├── 3.1.1 (interface)
├── 3.1.2 (implementation)
├── 3.1.3 (health checks)
└── 3.1.4 (Worker integration)

Phase 3.2 (AlgorithmLoader)
├── 3.2.1 (interface)
├── 3.2.2 (implementation)
├── 3.2.3 (Worker integration)
└── 3.2.4 (independence tests)

Phase 4.1 (Error Handling)
├── 4.1.1 (exceptions)
├── 4.1.2 (RFC 7807 middleware)
├── 4.1.3 (correlation ID)
├── 4.1.4 (update endpoints)
└── 4.1.5 (test errors)

Phase 4.2 (Testing & Docs)
├── 4.2.1 (TokenCache tests)
├── 4.2.2 (ConfigManager tests)
├── 4.2.3 (ServiceRegistry tests)
├── 4.2.4 (integration tests)
├── 4.2.5 (E2E tests)
├── 4.2.6 (API docs)
└── 4.2.7 (deployment guide)

Phase 4.3 (Deployment)
├── 4.3.1 (Cloud Run setup)
├── 4.3.2 (feature flags)
├── 4.3.3 (deploy 0%)
├── 4.3.4 (test rollback)
├── 4.3.5 (gradual rollout)
├── 4.3.6 (monitor)
└── 4.3.7 (decommission v2)
```

---

## Risk Assessment

### High Risk Tasks
- **1.2.7**: Database migration on staging (data loss risk)
- **2.1.3**: Migrating job-algorithm relationships (data corruption risk)
- **4.3.5**: Gradual rollout (production stability risk)
- **4.3.7**: Decommissioning v2 (no rollback risk)

### Mitigation Strategies
1. **Database migrations**: Always create archive tables, test on staging first
2. **Data migrations**: Validate before and after, keep backup
3. **Rollout**: Use feature flags, monitor metrics closely
4. **Decommission**: Keep v2 code for 1 week after 100% rollout

---

## Success Criteria

### Phase 1 Success
- ✅ No more OAuth consent prompts (token auto-refresh)
- ✅ Database has foreign key constraints
- ✅ Migration validated on staging

### Phase 2 Success
- ✅ Database normalized (no duplication)
- ✅ ConfigManager centralizes all configuration
- ✅ Worker loads algorithms from DB

### Phase 3 Success
- ✅ Worker runs independently
- ✅ ServiceRegistry provides all dependencies
- ✅ AlgorithmLoader fetches from database

### Phase 4 Success
- ✅ All errors follow RFC 7807
- ✅ Correlation IDs in all requests
- ✅ 80%+ test coverage
- ✅ v3 at 100% traffic
- ✅ v2 decommissioned

---

**File created**: `sdd/refactorizacion-v3/tasks.md`
