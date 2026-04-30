# Change Proposal: refactorizacion-v3

**Date**: 2026-04-22
**Project**: renameDriverFolders - Document renaming system using AI
**Status**: Proposed
**Version**: v3.0

---

## Executive Summary

### Why Refactor to v3?

The renameDriverFolders system (v2) is functionally working but accumulated technical debt that impacts user experience and maintainability. Users report OAuth consent fatigue (3 prompts per session), database schema has duplication issues with no referential integrity, and test coverage is near-zero despite Strict TDD Mode being enabled.

### What Problems Are We Solving?

1. **User Experience**: OAuth consent screen appears 3x per session due to `prompt: 'consent'` forcing re-authorization every time
2. **Data Integrity**: `jobs` and `document_algorithms` tables contain duplicate entries with no foreign key relationship
3. **Developer Experience**: `target_folder_names` field has ambiguous semantics that confuse developers
4. **Maintainability**: ~0% test coverage on critical paths (OAuth, job creation, file processing)
5. **Architecture**: Worker is tightly coupled to API Server for algorithm discovery

### ROI

- **User Impact**: Reduce OAuth prompts from 3x to 1x per session (66% reduction in friction)
- **Development Speed**: Foreign key constraints prevent silent data corruption bugs
- **Confidence**: >70% test coverage enables rapid iteration without fear of regressions
- **Time Investment**: 4-5 weeks total effort for a system that processes thousands of documents monthly

---

## Intent & Scope

### IN SCOPE

| Area | Changes |
|------|---------|
| **OAuth Flow** | Token persistence (Redis + SQLite fallback), remove consent prompt after first auth |
| **Database Schema** | Add FK relationship (`algorithm_ids` to `jobs`), remove `seed_default_algorithms()` duplication |
| **Field Clarity** | Rename `target_folder_names` to `subfolder_filter` with documented semantics |
| **Worker Independence** | ServiceRegistry for algorithm discovery, DI container for loose coupling |
| **Test Coverage** | Foundation suite for OAuth, job CRUD, algorithm loading, file processing (>=70% coverage) |
| **Error Handling** | Standard error response format (RFC 7807), correlation IDs across services |

### OUT OF SCOPE

| Area | Reason | Deferred to |
|------|--------|-------------|
| Complete microservices rewrite | Current architecture is solid (see exploration) | v4+ |
| UI redesign | Frontend works, issue is backend OAuth flow | v4+ |
| Performance optimization beyond OAuth | System is fast enough, latency is in AI calls | v4+ |
| Multi-cloud support | No business requirement | Future |
| Alternative AI providers | Gemini works well | Future |

---

## Proposed Solutions

### Problem 1: OAuth Consent Prompt (3x)

**Root Cause**: `services/frontend/src/app/app.component.ts:163`
```typescript
tokenClient.requestAccessToken({ prompt: 'consent', mode: 'select' });
```
- `prompt: 'consent'` ALWAYS shows consent screen, even if user previously authorized
- Token expiry logic (lines 108-120) may trigger re-prompt every 55 minutes

**Solution**:
1. **Token Persistence Layer**: Add `TokenStore` interface with Redis (prod) + SQLite (dev) fallback
2. **Silent Refresh**: Remove `prompt: 'consent'` on subsequent requests, use `prompt: ''`
3. **Token Lifecycle**:
   - First login: User sees consent screen (expected, one-time)
   - Subsequent logins: Silent refresh using stored refresh token
   - Token expiry: Background refresh 5 minutes before expiry

**Migration**:
- Users re-authenticate ONCE after deployment
- Existing tokens continue working until expiry
- Frontend gracefully falls back to consent prompt if refresh fails

**Breaking Changes**: YES - Users must re-authorize once after v3 deployment

**Rollback**: Restore old code, users re-auth again (acceptable for quick rollback)

---

### Problem 2: Database Duplication (Jobs vs Algorithms)

**Root Cause**: `services/api-server/src/main.py:142-216`
- `seed_default_algorithms()` creates job configs in `jobs` table
- These configs DUPLICATE data already in `document_algorithms` table
- No source of truth

**Solution**:
1. **Remove Seeding**: Delete `seed_default_algorithms()` function entirely
2. **Add Foreign Key**: Add `algorithm_ids JSONB` to `jobs` table
3. **Data Migration Script**:
   ```sql
   -- Step 1: Archive existing duplicate jobs
   CREATE TABLE jobs_archive AS SELECT * FROM jobs WHERE id LIKE '%-%';

   -- Step 2: Add new column
   ALTER TABLE jobs ADD COLUMN algorithm_ids JSONB DEFAULT '[]'::jsonb;

   -- Step 3: Create junction for future referential integrity
   CREATE TABLE job_algorithms (
       job_id VARCHAR(255) REFERENCES jobs(id) ON DELETE CASCADE,
       algorithm_id VARCHAR(255) REFERENCES document_algorithms(id) ON DELETE RESTRICT,
       PRIMARY KEY (job_id, algorithm_id)
   );
   ```

**Migration**:
- Dry-run on staging first (validate no active jobs broken)
- Production migration at low-traffic window
- Keep `jobs_archive` table for 30 days (emergency rollback)

**Breaking Changes**: NO (if migration done correctly)

**Rollback**: Restore from `jobs_archive` table, drop `job_algorithms` junction

---

### Problem 3: target_folder_names Ambiguity

**Root Cause**: Field name suggests "destination folder" but semantics are unclear
- In `jobs` table: `target_folder_names` = ["*"] or ["specific folder name"]
- In Worker: Used to SEARCH for folders by name within `source_folder_id`
- Search logic is confusing: `find_target_folders()` searches SUBFOLDERS by name

**Solution**:
1. **Rename Field**: `target_folder_names` → `subfolder_filter` in `jobs` table
2. **Document Semantics**:
   ```
   subfolder_filter: List of subfolder names to process within source_folder_id
   - ["*"] = Process root folder directly (no subfolder filtering)
   - ["facturas", "contratos"] = Only process subfolders matching these names
   - [] = No filtering (deprecated, use ["*"])
   ```
3. **Remove from Auto-Classify**: Auto-classify job config should always use `["*"]`
4. **Update Worker**: Simplify `find_target_folders()` to `filter_subfolders()`

**Migration**:
- Database migration: `ALTER TABLE jobs RENAME COLUMN target_folder_names TO subfolder_filter;`
- Code migration: Update all references (API Server, Worker, Frontend)
- Frontend display: Update label to "Subfolder Filter" with tooltip

**Breaking Changes**: NO (rename only, semantics unchanged)

**Rollback**: Rename back to `target_folder_names`

---

### Problem 4: Missing Foreign Key Relationship

**Root Cause**: No `algorithm_id` field in `jobs` table
- No way to track WHICH algorithms a job uses
- Deleting an active algorithm breaks auto-classify silently

**Solution**:
1. **Add Junction Table**: `job_algorithms` (see Problem 2 for schema)
2. **Add ON DELETE RESTRICT**: Prevent deletion of algorithms used by active jobs
3. **Update Auto-Classify Logic**:
   ```python
   # Before: Loads all active algorithms regardless of job
   active_algorithms = [alg for alg in all_algorithms if alg.get("is_active")]

   # After: Loads only algorithms associated with auto-classify job
   auto_classify_job = db_manager.find("auto-classify")
   associated_algorithms = load_job_algorithms(auto_classify_job["id"])
   ```

**Migration**: Combined with Problem 2 migration

**Breaking Changes**: NO (backward compatible)

**Rollback**: Drop `job_algorithms` table, remove ON DELETE RESTRICT

---

### Problem 5: Worker Tight Coupling

**Root Cause**: `services/worker-renombrador/src/main.py:106-111`
- Worker initializes ONLY `db_manager` (jobs table)
- NO access to `algorithms_manager` (document_algorithms table)
- Depends on API Server to inject algorithms into job config

**Solution**:
1. **ServiceRegistry Pattern**:
   ```python
   # core_renombrador/service_registry.py
   class ServiceRegistry:
       def get_database_manager(self, table_name: str) -> DatabaseManager
       def get_algorithms_manager(self) -> DatabaseManager
       def get_config_manager(self) -> ConfigManager
   ```

2. **DI Container**:
   ```python
   # Worker initialization
   registry = ServiceRegistry(env=os.getenv("ENVIRONMENT"))
   db_manager = registry.get_database_manager("jobs")
   algorithms_manager = registry.get_algorithms_manager()
   ```

3. **Worker Independence**:
   - Worker can load algorithms directly from `document_algorithms` for validation
   - Keep injection for auto-classify (performance optimization)
   - Worker can run in isolation for testing

**Migration**:
- Add `ServiceRegistry` to `core-renombrador` package
- Update Worker initialization
- Add environment variable `ALGORITHM_SOURCE: "injected" | "direct"` (feature flag)

**Breaking Changes**: NO (backward compatible with feature flag)

**Rollback**: Remove ServiceRegistry, restore old initialization

---

### Problem 6: Low Test Coverage (~0% Backend)

**Root Cause**: No tests written despite STRICT_TDD_MODE.md being enabled
- Only 11 test files total (mostly integration/manual tests)
- No unit tests for OAuth, job creation, algorithm loading

**Solution**:
1. **Foundation Test Suite** (Strict TDD):
   ```
   tests/
   ├── unit/
   │   ├── test_oauth_flow.py
   │   ├── test_job_crud.py
   │   ├── test_algorithm_loading.py
   │   ├── test_token_store.py
   │   └── test_service_registry.py
   ├── integration/
   │   ├── test_oauth_e2e.py
   │   ├── test_job_execution_e2e.py
   │   └── test_worker_e2e.py
   └── fixtures/
       ├── oauth_tokens.json
       ├── sample_jobs.json
       └── mock_algorithms.json
   ```

2. **Coverage Targets**:
   - API Server: >=70%
   - Worker: >=70%
   - Frontend: >=50% (harder to test, lower target)

3. **Test Pyramid**:
   - 70% unit tests (fast, isolated)
   - 20% integration tests (medium speed, real DB)
   - 10% E2E tests (slow, full stack)

**Migration**: Write tests FIRST for all v3 changes (Strict TDD protocol)

**Breaking Changes**: NO (tests don't affect production)

**Rollback**: Delete test files (harmless)

---

### Problem 7: Inconsistent Error Handling

**Root Cause**: No standard error response format
- Some functions raise exceptions, others return error dicts
- No correlation IDs to trace errors across services

**Solution**:
1. **Standard Error Response** (RFC 7807 Problem Details):
   ```python
   class ProblemDetail(BaseModel):
       type: str  # URI to error type documentation
       title: str  # Short human-readable title
       status: int  # HTTP status code
       detail: str  # Detailed explanation
       instance: str  # URI to specific occurrence
       correlation_id: str  # Trace ID
   ```

2. **Middleware Components**:
   - `CorrelationIDMiddleware`: Inject `X-Correlation-ID` header
   - `ErrorHandlerMiddleware`: Convert exceptions to `ProblemDetail`
   - Service-specific handlers: OAuth, Database, Drive API

3. **Retry Logic**:
   - Retryable errors: 429 (rate limit), 503 (service unavailable)
   - Fatal errors: 400 (bad request), 404 (not found)
   - Exponential backoff with jitter

**Migration**:
- Add middleware to API Server and Worker
- Update all error returns to use `ProblemDetail`
- Add logging for correlation IDs

**Breaking Changes**: NO (error format changes are backward compatible)

**Rollback**: Remove middleware, restore old error handling

---

## Implementation Phases

### Phase 1: Critical Fixes (Week 1)

**Goal**: Fix highest-impact user-facing issues

| Task | Owner | Days | Status |
|------|-------|------|--------|
| OAuth token persistence (Redis + SQLite) | Backend | 2 | Pending |
| Remove `prompt: 'consent'` after first auth | Frontend | 1 | Pending |
| FK constraints (`job_algorithms` junction table) | Backend | 2 | Pending |
| Orphan cleanup script (remove duplicate jobs) | Backend | 1 | Pending |
| Unit tests for OAuth flow | Backend | 2 | Pending |

**Deliverables**:
- OAuth prompts reduced from 3x to 1x
- Database migration scripts (dry-run on staging)
- Test coverage: OAuth >=80%

**Success Criteria**:
- Users only see consent screen ONCE per session
- Zero orphaned jobs in database
- All OAuth tests passing

---

### Phase 2: Database Normalization (Week 2)

**Goal**: Clean up schema, remove duplication

| Task | Owner | Days | Status |
|------|-------|------|--------|
| Remove `seed_default_algorithms()` function | Backend | 1 | Pending |
| Data migration script (archive duplicates) | Backend | 2 | Pending |
| Rename `target_folder_names` → `subfolder_filter` | Backend | 1 | Pending |
| Update all code references | Full Stack | 2 | Pending |
| Unit tests for database operations | Backend | 2 | Pending |

**Deliverables**:
- Clean database schema with FK constraints
- Migration scripts tested on staging
- Documentation for `subfolder_filter` semantics

**Success Criteria**:
- Zero duplicate entries between `jobs` and `document_algorithms`
- All database tests passing
- Migration successful on production

---

### Phase 3: Worker Independence (Week 3)

**Goal**: Decouple Worker from API Server

| Task | Owner | Days | Status |
|------|-------|------|--------|
| ServiceRegistry implementation | Backend | 2 | Pending |
| DI container for Worker initialization | Backend | 1 | Pending |
| Worker algorithm validation | Backend | 2 | Pending |
| Integration tests for Worker | Backend | 2 | Pending |
| Documentation for ServiceRegistry | Backend | 1 | Pending |

**Deliverables**:
- Worker can run in isolation
- ServiceRegistry pattern documented
- Feature flag for `ALGORITHM_SOURCE`

**Success Criteria**:
- Worker starts independently without API Server
- All Worker tests passing
- Documentation complete

---

### Phase 4: Polish & Deployment (Week 4)

**Goal**: Production-ready deployment

| Task | Owner | Days | Status |
|------|-------|------|--------|
| Standard error responses (RFC 7807) | Backend | 2 | Pending |
| Correlation ID middleware | Backend | 1 | Pending |
| End-to-end testing (full stack) | QA | 2 | Pending |
| Deployment documentation | DevOps | 1 | Pending |
| Blue-green deployment | DevOps | 1 | Pending |

**Deliverables**:
- Production-ready v3 system
- Deployment runbooks
- Rollback procedures

**Success Criteria**:
- All E2E tests passing
- Zero downtime deployment
- User acceptance testing passed

---

## Success Criteria

### User-Facing Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| OAuth prompts per session | 3 | 1 | Frontend analytics |
| User-reported OAuth issues | 2/week | 0 | Support tickets |
| Time to first file rename | ~2 min | ~30 sec | Job execution logs |

### Technical Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Test coverage (backend) | ~0% | >=70% | pytest-cov |
| Test coverage (frontend) | ~5% | >=50% | Karma/Istanbul |
| Orphaned jobs | Unknown | 0 | DB query |
| Data integrity issues | 2/month | 0 | Error logs |

### Deployment Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Downtime | <5 min | Deployment logs |
| Rollback time | <10 min | Runbook test |
| User re-auth required | 1x per user | OAuth logs |

---

## Risks & Mitigation

### HIGH Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Data migration failure** | HIGH (data loss) | LOW | Dry-run on staging, keep `jobs_archive` for 30 days |
| **User re-auth required** | MEDIUM (friction) | HIGH (certain) | Advance communication (1 week notice), support ready |
| **Breaking existing integrations** | HIGH (business impact) | LOW | Feature flags, gradual rollout |

### MEDIUM Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Test coverage not met** | MEDIUM (regressions) | MEDIUM | Hire QA contractor, extend Phase 4 by 1 week |
| **Worker deployment issues** | MEDIUM (failed jobs) | LOW | Staged rollout (dev → staging → prod) |
| **OAuth token persistence bugs** | HIGH (users locked out) | LOW | Fallback to consent prompt, monitor error logs |

### LOW Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Field rename confusion** | LOW (dev time) | LOW | Code search, documentation |
| **Performance regression** | LOW (slower jobs) | LOW | Load testing on staging |
| **Deployment delays** | MEDIUM (timeline slip) | MEDIUM | Buffer time in Phase 4 |

---

## Rollback Plan

### Scenario 1: Critical Bug Found Immediately (Day 1-2)

**Trigger**: >5% error rate in job executions

**Actions**:
1. Deploy v2 from previous commit
2. Users re-authenticate again (acceptable)
3. Investigate bug in v3 staging

**Time**: <10 minutes

### Scenario 2: Data Migration Failure (Day 7-14)

**Trigger**: Migration script fails on production

**Actions**:
1. Restore `jobs` table from `jobs_archive`
2. Roll back database schema changes
3. Investigate staging issue

**Time**: <30 minutes

### Scenario 3: User Uproar Over Re-Auth (Day 1-7)

**Trigger**: >10 support tickets about OAuth

**Actions**:
1. Communicate clearly: "One-time re-auth for better UX"
2. Offer support for OAuth issues
3. Consider extending token expiry time

**Time**: Ongoing communication

---

## Open Questions for Spec Phase

1. **User Experience**: Is re-authorization acceptable after OAuth fix? (ASSUME: YES, communicate in advance)
2. **Data Migration**: Should we migrate existing jobs to use new `algorithm_ids` field? (ASSUME: YES, use migration script)
3. **Algorithm Loading**: Should Worker use injection (current) or direct access (new)? (ASSUME: BOTH, feature flag)
4. **Subfolder Processing**: Keep `find_target_folders()` logic or simplify to root-only? (ASSUME: KEEP, rename to `filter_subfolders`)
5. **Test Coverage Priority**: Which paths to test first? (ASSUME: OAuth, job CRUD, algorithm loading)
6. **Deployment Strategy**: Blue-green deployment or rolling update? (ASSUME: Blue-green for safety)
7. **Rollback Plan**: Can v3 rollback to v2 if critical bugs found? (ASSUME: YES, <10 min rollback time)

---

## Dependencies

### External Dependencies

| Dependency | Version | Required For |
|------------|---------|--------------|
| Redis (prod) | >=7.0 | Token persistence |
| SQLite (dev) | >=3.35 | Token persistence fallback |
| Supabase | - | Database (existing) |
| Google Cloud Tasks | - | Task queue (existing) |

### Internal Dependencies

| Component | Status | Blocker For |
|-----------|--------|-------------|
| Exploration phase | ✅ Complete | Proposal |
| Proposal phase | 🔄 In Progress | Spec |
| Spec phase | Pending | Design |
| Design phase | Pending | Tasks |
| Tasks phase | Pending | Apply |

---

## Next Steps

1. **Approve this proposal**: Stakeholder sign-off on scope and timeline
2. **Proceed to Spec phase**: Write detailed specifications for each change
3. **Create Design document**: Architecture diagrams and technical approach
4. **Break down tasks**: Implementable task checklist for development team

---

## Appendix: Decision Log

| Decision | Date | Rationale |
|----------|------|-----------|
| Token persistence with Redis + SQLite | 2026-04-22 | Fast prod access, simple dev setup |
| Junction table instead of JSON array for algorithms | 2026-04-22 | Better referential integrity, easier querying |
| Rename `target_folder_names` → `subfolder_filter` | 2026-04-22 | Clearer semantics, documented behavior |
| ServiceRegistry for Worker independence | 2026-04-22 | Proven pattern, enables testing |
| Blue-green deployment | 2026-04-22 | Zero-downtime requirement, safe rollback |
| Test coverage >=70% | 2026-04-22 | Realistic target for 4-week timeline |
