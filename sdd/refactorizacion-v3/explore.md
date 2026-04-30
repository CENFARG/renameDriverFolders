# Exploration: refactorizacion-v3

**Date**: 2026-04-22
**Project**: renameDriverFolders - Document renaming system using AI
**Current State**: v2 working but has technical debt
**Goal**: Complete refactor to v3 with clean architecture, Strict TDD Mode, all issues resolved

---

## Current State

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
│                    (Angular Frontend)                           │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         │ Google OAuth (ID Token)
                         │ Google Picker (Access Token)
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    API Server (FastAPI)                         │
│  - Authentication: IAP (prod) / OAuth (dev)                    │
│  - Authorization: Domain whitelist (OAuthSecurityManager)      │
│  - Job CRUD: jobs table (active configs)                       │
│  - Algorithm CRUD: document_algorithms table (patterns)        │
│  - Task Dispatch: Cloud Tasks with OIDC token                  │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         │ Cloud Tasks (OIDC authenticated)
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Worker (FastAPI)                             │
│  - OIDC Auth: Verify scheduler-trigger service account         │
│  - Credentials: User OAuth (manual) / Service Account (sched)  │
│  - Processing: Agno Agent + Gemini AI                          │
│  - Drive API: Rename files with custom HTTP transport          │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ↓
                   ┌──────────┐
                   │ Supabase │
                   │ - jobs   │
                   │ - doc_   │
                   │   algo   │
                   │ - job_   │
                   │   exec   │
                   └──────────┘
```

### Data Flow: Manual Job (User-triggered)

1. **User Signs In**: Frontend gets Google ID Token via Sign-In button
2. **User Requests Access Token**: `requestAccessToken()` with `prompt: 'consent'` ⚠️ **(ISSUE: prompts 3x)**
3. **User Selects Folder**: Google Picker returns `folder_id`
4. **User Submits Job**: Frontend sends POST `/api/v1/jobs/manual` with:
   - `folder_id`: Selected folder ID
   - `access_token`: User's OAuth access token
   - `job_type`: "auto-classify" or specific algorithm
5. **API Server**:
   - Verifies ID Token (IAP or OAuth)
   - Checks domain whitelist (OAuthSecurityManager)
   - Creates execution log in `job_executions` (status: "submitted")
   - Loads job config from `jobs` or converts from `document_algorithms`
   - Creates Cloud Task with OIDC token + user credentials in payload
6. **Cloud Tasks**: Queues task with OIDC authentication
7. **Worker**:
   - Verifies OIDC token (must be from scheduler-trigger SA)
   - Extracts user credentials from payload
   - Builds custom HTTP with Bearer token injection
   - Lists files in folder
   - Downloads content (with OCR if needed)
   - Sends to Agno Agent + Gemini AI
   - Parses structured response (Pydantic model)
   - Renames file in Google Drive
   - Updates execution log (status: "completed" / "failed")

### Data Flow: Scheduled Job (Cron-triggered)

1. **Cloud Scheduler**: Triggers `/api/v1/jobs/scheduled` every X minutes
2. **API Server**:
   - Verifies OIDC token (scheduler service account)
   - Queries `jobs` table for `trigger_type='scheduled'` and `active=true`
   - Creates Cloud Task for each scheduled job (OIDC authenticated)
3. **Worker**:
   - Processes job with SERVICE ACCOUNT credentials (no user token)
   - Same processing flow as manual job

### Database Schema

#### Table: `jobs`
**Purpose**: Active execution configurations (manual or scheduled)

```sql
id VARCHAR255 PK
name VARCHAR500
description TEXT
active BOOLEAN
trigger_type VARCHAR50  -- 'manual' or 'scheduled'
schedule VARCHAR100      -- cron expression (scheduled only)
source_folder_id VARCHAR500  -- Drive folder ID or "DYNAMIC"
target_folder_names TEXT[]   -- ⚠️ AMBIGUOUS (see issues)
agent_config JSONB
  ├── model (name, temperature, max_tokens)
  ├── instructions TEXT
  ├── prompt_template TEXT
  ├── filename_format TEXT
  └── output_schema JSONB (optional)
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

#### Table: `document_algorithms`
**Purpose**: Classification patterns (templates for document types)

```sql
id VARCHAR255 PK
name VARCHAR500
description TEXT
classification_criteria TEXT  -- Rules to identify document type
extraction_prompt TEXT        -- Prompt to extract specific data
output_schema JSONB           -- Expected JSON structure
filename_format VARCHAR500    -- Naming pattern
is_active BOOLEAN
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

#### Table: `job_executions`
**Purpose**: Audit log for job runs

```sql
id VARCHAR255 PK
user_email VARCHAR500
user_name VARCHAR500
folder_id VARCHAR500
job_type VARCHAR50
job_config_id VARCHAR255
timestamp TIMESTAMPTZ
status VARCHAR50  -- 'submitted', 'processing', 'completed', 'failed'
task_id VARCHAR500
details TEXT
stats JSONB      -- {files_processed, files_renamed, errors}
```

### Authentication & Authorization

#### Two Flows

1. **IAP (Identity-Aware Proxy)**: Production
   - Google Cloud proxy sits in front of API Server
   - Validates user via Google Cloud console
   - Adds `X-Goog-IAP-JWT-Assertion` header
   - API Server verifies JWT with `id_token.verify_oauth2_token()`
   - No OAuthSecurityManager needed

2. **OAuth with Domain Whitelist**: Development
   - Frontend: Google Sign-In button (ID Token)
   - API Server: OAuthSecurityManager
   - Domain whitelist: `allowed_domains` from Secret Manager
   - Email whitelist: `allowed_emails` (optional)
   - Rate limiting: 30 requests per minute per user

#### Worker Security

- **OIDC Authentication**: Only Cloud Tasks service account can invoke `/run-task`
- **Service Account**: `scheduler-trigger@cloud-functions-474716.iam.gserviceaccount.com`
- **User Credentials**: Passed in task payload (manual jobs only)
- **Token Masking**: Access tokens masked in logs (`token[:4]...token[-4:]`)

---

## Technical Debt Found

### 1. 🔴 OAuth Consent Prompt (3x Re-prompts)

**Location**: `services/frontend/src/app/app.component.ts:163`

```typescript
tokenClient.requestAccessToken({ prompt: 'consent', mode: 'select' });
```

**Problem**:
- `prompt: 'consent'` ALWAYS shows consent screen, even if user previously authorized
- `mode: 'select'` shows account dropdown (good UX) BUT combined with `consent` (bad UX)
- Users see 3 prompts: 1) Sign-In, 2) Account selection, 3) Consent screen
- Token expiry logic (lines 108-120) may trigger re-prompt every 55 minutes

**Evidence**:
- User complaint: "me pide elegir cuenta 3 veces"
- Code comment line 81: "Solicitar OAuth token INMEDIATAMENTE después del login (acción directa del usuario)"

**Impact**: HIGH - Poor UX, users frustrated

**Solution**: Remove `prompt: 'consent'``, use `prompt: ''` for silent auth when token exists

---

### 2. 🔴 Database Duplication (Jobs vs Algorithms)

**Location**: `services/api-server/src/main.py:142-216`

**Problem**:
- `seed_default_algorithms()` (lines 142-216) creates job configs in `jobs` table
- These configs DUPLICATE data already in `document_algorithms` table
- Example: "facturas-rg830" exists in BOTH tables with same `filename_format`

**Evidence**:
```python
# Lines 142-216 (DISABLED but code exists)
diego_algorithms = [
    {
        "id": "facturas-rg830",
        "agent_config": {
            "filename_format": "{date}_FACTURA_{issuer}_{detail}"
        }
    }
]
```

**Impact**: HIGH - Data inconsistency, unclear source of truth

**Solution**:
- Remove `seed_default_algorithms()` entirely
- Jobs should REFERENCE algorithms via `algorithm_id` FK (new field)
- Auto-classify job loads algorithms from `document_algorithms` dynamically

---

### 3. 🟡 target_folder_names Ambiguity

**Location**: Multiple files

**Problem**:
- Field name suggests "destination folder" but semantics are unclear
- In `jobs` table: `target_folder_names` = ["*"] or ["specific folder name"]
- In `document_algorithms`: DOES NOT EXIST (correct - algorithms are patterns)
- In Worker (line 469-514): Used to SEARCH for folders by name within `source_folder_id`
- But search logic is confusing: `find_target_folders()` searches SUBFOLDERS by name

**Evidence**:
```python
# worker-renombrador/main.py:469-514
def find_target_folders(drive_service, root_folder_id, target_names):
    # Searches for folders WITHIN root_folder_id that match target_names
    # If target_names=["*"], processes root_folder_id directly (line 505-507)
```

**Impact**: MEDIUM - Confusing semantics, inconsistent usage

**Solution**:
- Rename to `subfolder_filter` in jobs table (clarifies it's a filter, not destination)
- Remove from auto-classify job config (always process root folder directly)
- Document: "subfolder_filter: List of subfolder names to process (['*'] = all)"

---

### 4. 🟡 Missing Foreign Key Relationship

**Location**: Database schema

**Problem**:
- No `algorithm_id` field in `jobs` table
- No way to track WHICH algorithms a job uses
- Deleting an active algorithm breaks auto-classify silently

**Impact**: MEDIUM - No referential integrity, silent failures

**Solution**:
- Add `algorithm_ids JSONB` to `jobs` (array of algorithm references)
- Or create junction table `job_algorithms` (many-to-many)
- Add ON DELETE RESTRICT constraint

---

### 5. 🟡 Worker Does Not Access document_algorithms

**Location**: `services/worker-renombrador/src/main.py:106-111`

**Problem**:
- Worker initializes ONLY `db_manager` (jobs table)
- NO access to `algorithms_manager` (document_algorithms table)
- Depends on API Server to inject algorithms into job config
- Tight coupling: Worker can't discover algorithms independently

**Evidence**:
```python
# Lines 106-111: Only jobs manager initialized
db_manager = DatabaseManager(use_supabase=True, table_name="jobs")
# NO algorithms_manager initialized
```

**Impact**: MEDIUM - Tight coupling, reduced flexibility

**Solution**:
- Initialize `algorithms_manager` in Worker
- Allow Worker to load algorithms independently for validation
- Keep injection for auto-classify (performance optimization)

---

### 6. 🟢 Low Test Coverage (~0% backend)

**Location**: `tests/` directory

**Problem**:
- Only 11 test files total (mostly integration/manual tests)
- No unit tests for critical paths: OAuth, job creation, algorithm loading
- STRICT_TDD_MODE.md enabled 2026-04-21 but tests not written
- Coverage: API Server ~0%, Worker ~0%, Frontend ~5%

**Evidence**:
```bash
# Only 11 test files
./tests/test_gemini_integration.py
./tests/test_integration.py
./tests/test_production.py
./tests/manual/check_env.py
./tests/manual/check_gemini_analysis.py
...
```

**Impact**: LOW - High risk of regressions, but system works

**Solution**:
- Write unit tests FIRST for all v3 changes (Strict TDD)
- Target: >80% coverage for backend, >60% frontend
- Use pytest marks: @pytest.mark.unit, @pytest.mark.integration

---

### 7. 🟢 Inconsistent Error Handling

**Location**: Multiple files

**Problem**:
- Some functions raise exceptions, others return error dicts
- Worker catches all exceptions in `process_folder_files()` (line 616-617)
- No standard error response format across services
- Global exception handler in API Server (line 645-654) but not comprehensive

**Evidence**:
```python
# worker-renombrador/main.py:616-617
except Exception as e:
    logger.error(f"Error processing file {file['name']}: {e}")
    stats["errors"] += 1  # Continues processing

# api-server/main.py:645-654
@app.exception_handler(Exception)
async def global_exception_handler(request, Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "An unexpected error occurred"})
```

**Impact**: LOW - System resilient but debugging is hard

**Solution**:
- Define standard error response schema (RFC 7807 Problem Details)
- Distinguish between retryable (429, 503) and fatal (400, 404) errors
- Add correlation IDs to trace errors across services

---

## What Works Well

### 1. ✅ Clean Microservices Architecture

**Why it's solid**:
- Clear separation: Frontend (UI), API Server (orchestration), Worker (processing)
- Independent deployment: Each service has own Dockerfile
- Async communication: Cloud Tasks decouples API Server from Worker
- Stateless services: No session state, scalable horizontally

**Preserve in v3**: YES - Keep this architecture

---

### 2. ✅ AgentFactory + Agno Framework

**Why it's solid**:
- Centralized agent creation logic (`agent_factory.py`)
- Pydantic models for structured AI outputs (type-safe, validated)
- Agno handles Gemini API calls, retries, streaming
- `output_schema` defines contract between Agent and Worker

**Evidence**:
```python
# agent_factory.py:119-163
def create_agent_from_job_config(job_config):
    model_config = job_config["agent_config"]["model"]
    agent_params = {
        "instructions": job_config["agent_config"]["instructions"],
        "output_schema": job_config["agent_config"].get("output_schema"),
        ...
    }
    return create_document_agent(**agent_params)
```

**Preserve in v3**: YES - Excellent abstraction layer

---

### 3. ✅ DatabaseManager Abstraction

**Why it's solid**:
- Single interface for JSON, GCS, Supabase backends
- Environment-based switching (`USE_SUPABASE`, `USE_GCS`)
- Consistent CRUD API: `find()`, `find_all()`, `insert()`, `update()`, `delete()`
- Easy local development with JSON, production with Supabase

**Evidence**:
```python
# database_manager.py:31-86
class DatabaseManager:
    def __init__(self, use_supabase=False, use_gcs=False, file_manager=None, db_path=None):
        if use_supabase:
            self._init_supabase(...)
        elif use_gcs:
            self._init_gcs(...)
        else:
            self._ensure_json_db()
```

**Preserve in v3**: YES - Great flexibility for dev/prod environments

---

### 4. ✅ OIDC Authentication for Worker

**Why it's solid**:
- Only Cloud Tasks service account can invoke `/run-task`
- Prevents unauthorized access to Worker endpoint
- No shared secrets (OIDC token verified with Google public keys)
- Clear separation: User credentials for Drive API (payload), OIDC for endpoint auth (header)

**Evidence**:
```python
# worker-renombrador/main.py:852-897
try:
    id_info = id_token.verify_oauth2_token(token, google_requests.Request(), expected_audience)
    expected_sa = "scheduler-trigger@cloud-functions-474716.iam.gserviceaccount.com"
    if id_info.get("email") != expected_sa:
        raise HTTPException(status_code=403, detail="Unauthorized service account")
```

**Preserve in v3**: YES - Security best practice

---

### 5. ✅ Auto-Classify Design

**Why it's solid**:
- Single job ("auto-classify") loads ALL active algorithms
- AI decides which algorithm to apply based on document content
- No manual algorithm selection needed
- Easy to add new algorithms: Just insert into `document_algorithms` with `is_active=true`

**Evidence**:
```python
# api-server/main.py:729-748
all_algorithms = algorithms_manager.find_all()
active_algorithms = [alg for alg in all_algorithms if alg.get("is_active", True)]

for algo in active_algorithms:
    algorithm_blocks.append(f"""
    <ALGORITHM id="{algo['id']}" name="{algo['name']}">
    {algo['classification_criteria']}
    EXTRACTION_SCHEMA: {algo['output_schema']}
    FILENAME_FORMAT: {algo['filename_format']}
    </ALGORITHM>
    """)
```

**Preserve in v3**: YES - Clever design, scales well

---

### 6. ✅ ContentExtractor with OCR

**Why it's solid**:
- Unified interface: `get_content(filename, bytes)`
- Supports multiple formats: PDF, images, Office docs
- OCR fallback via pdf2image + pytesseract
- Content caching to avoid re-processing

**Preserve in v3**: YES - Critical for document understanding

---

### 7. ✅ Audit Trail (job_executions)

**Why it's solid**:
- Every job submission logged with timestamp, user, folder
- Status tracking: submitted → processing → completed/failed
- Statistics: files_processed, files_renamed, errors
- Export logs endpoint for user download

**Preserve in v3**: YES - Essential for debugging and compliance

---

## Key Files

### Entry Points

- `services/api-server/src/main.py` (1297 lines)
  - FastAPI app with OAuth/OIDC auth
  - Job CRUD endpoints
  - Cloud Tasks dispatch
  - Seed algorithms (DISABLED but code exists)

- `services/worker-renombrador/src/main.py` (1092 lines)
  - FastAPI app with OIDC auth
  - `/run-task` endpoint (main entry)
  - File processing logic
  - Drive API integration

- `services/frontend/src/main.ts` (Angular bootstrap)
  - `services/frontend/src/app/app.component.ts` (main UI logic)

### Core Business Logic

- `packages/core-renombrador/src/core_renombrador/agent_factory.py`
  - Creates Agno agents from job configs
  - Handles Pydantic output schemas

- `packages/core-renombrador/src/core_renombrador/database_manager.py`
  - Unified DB interface (JSON/GCS/Supabase)
  - CRUD operations

- `packages/core-renombrador/src/core_renombrador/oauth_security.py`
  - OAuth token verification
  - Domain whitelist authorization
  - Rate limiting

- `packages/core-renombrador/src/core_renombrador/content_extractor.py`
  - File content extraction
  - OCR support

### Configuration

- `config.json` - Local development config
- `.env` - Environment variables (not in repo)
- `services/frontend/src/environments/environment.ts` - Frontend config
- `services/frontend/src/environments/environment.prod.ts` - Production config

### Deployment

- `Dockerfile.worker` - Worker container
- `cloudbuild-api.yaml` - API Server build
- `cloudbuild-worker.yaml` - Worker build
- `deploy.sh` - Deployment script

### Documentation

- `STRICT_TDD_MODE.md` - TDD protocol (enabled 2026-04-21)
- `ANALYSIS_PROBLEMS_APRIL10.md` - Known issues analysis
- `sdd/database-structure-exploration/exploration.md` - DB schema exploration
- `docs/oauth-user-credentials/OAUTH_SETUP_GUIDE.md` - OAuth setup

---

## Risks

### HIGH Risks

1. **OAuth Consent Prompt Frustration**
   - Users may abandon system due to 3x prompts
   - Productivity impact: Users delay tasks to avoid re-auth

2. **Database Duplication Causing Bugs**
   - If `seed_default_algorithms()` is re-enabled, creates duplicate entries
   - Updating algorithm in `document_algorithms` doesn't update `jobs` table
   - Source of truth confusion leads to inconsistent behavior

3. **No Test Coverage for Critical Paths**
   - OAuth flow not tested → breaking changes go undetected
   - Job creation not tested → data corruption possible
   - Worker processing not tested → file renaming bugs in production

### MEDIUM Risks

4. **target_folder_names Ambiguity**
   - Developers misunderstand field purpose
   - Incorrect configurations lead to wrong folders processed
   - Debugging takes longer due to unclear semantics

5. **No Foreign Key Constraints**
   - Deleting active algorithm breaks auto-classify silently
   - No way to audit which jobs use which algorithms
   - Data integrity relies on application logic (fragile)

6. **Worker Tight Coupling to API Server**
   - Worker can't discover algorithms independently
   - Can't test Worker in isolation without full API Server
   - Harder to reuse Worker for other processing tasks

### LOW Risks

7. **Inconsistent Error Handling**
   - Debugging production issues takes longer
   - Users see generic error messages
   - No correlation IDs to trace requests across services

---

## Ready for Proposal

**YES** - Current state is well-understood with clear technical debt items.

### What's Clear

✅ Architecture: 3 microservices with clear responsibilities
✅ Data flow: OAuth → API Server → Cloud Tasks → Worker → Drive
✅ Database schema: jobs, document_algorithms, job_executions
✅ Authentication: IAP (prod) / OAuth (dev) + OIDC (Worker)
✅ Technical debt: 7 identified issues with clear solutions
✅ Solid patterns: AgentFactory, DatabaseManager, auto-classify

### What Needs Clarification

❓ **Priority of fixes**: Which issues to tackle first in v3?
❓ **Migration strategy**: How to handle existing production data during schema changes?
❓ **Breaking changes**: Are we okay with requiring users to re-authorize after fixing OAuth prompts?
❓ **Foreign key migration**: Add `algorithm_ids` to `jobs` or create junction table?
❓ **Worker responsibilities**: Should Worker discover algorithms independently or keep injection?

### Recommended Next Steps

1. **Phase 1**: Fix OAuth consent prompt (quick win, high user impact)
2. **Phase 2**: Remove database duplication + add foreign keys
3. **Phase 3**: Rename `target_folder_names` → `subfolder_filter`
4. **Phase 4**: Add comprehensive test suite (Strict TDD)
5. **Phase 5**: Worker independence (load algorithms directly)

---

## Appendix: Open Questions for Proposal Phase

1. **User Experience**: Is re-authorization acceptable after OAuth fix?
2. **Data Migration**: Should we migrate existing jobs to use new `algorithm_ids` field?
3. **Algorithm Loading**: Should Worker use injection (current) or direct access (new)?
4. **Subfolder Processing**: Keep `find_target_folders()` logic or simplify to root-only?
5. **Test Coverage Priority**: Which paths to test first? (OAuth, job creation, file processing)
6. **Deployment Strategy**: Blue-green deployment or rolling update for v3?
7. **Rollback Plan**: Can v3 rollback to v2 if critical bugs found?
