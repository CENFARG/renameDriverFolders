# Renombrador Archivos GDrive (#amBotHsOS)

Sistema de procesamiento inteligente de documentos en Google Drive. Utiliza IA (Gemini 2.0 Flash) para analizar, categorizar y renombrar archivos automáticamente basándose en su contenido visual y textual.

## Arquitectura v3

Refactoring completo desde 3 monolitos (1298, 851, 826 líneas) a módulos modulares <250 líneas cada uno.

```
packages/core-renombrador/     Framework-agnostic core (16 modules)
  src/core_renombrador/
    config_manager.py          (250 lines) Configuration management
    content_extractor.py       (246 lines) PDF/image content extraction
    toon_converter.py          (241 lines) Document format conversion
    oauth_security.py          (239 lines) OAuth2 + security facade
    token_store.py             (233 lines) Async SQLite token storage
    schemas.py                 (222 lines) Pydantic models
    drive_handler.py           (189 lines) Drive API facade
    drive_reader.py            (187 lines) Drive read operations
    drive_writer.py            (181 lines) Drive write operations
    db_connection.py           (147 lines) Database connection mgmt
    agent_builder.py           (128 lines) AI agent construction
    token_manager.py           (114 lines) Token lifecycle manager
    documentation_manager.py   (114 lines) Documentation handler
    db_queries.py              (100 lines) Database CRUD operations
    agent_config.py            (77 lines)  Agent configuration
    ...facades (agent_factory, database_manager, file_manager, logger_manager)

services/api-server-v3/        FastAPI REST API
  src/
    main.py                    (monolith - pending decomposition)
    auth.py                    (147 lines) IAP + OAuth verification
    api_config.py              (138 lines) Config + secret manager
    cloud_tasks.py             (89 lines)  Cloud Tasks dispatch
    api_models.py              (80 lines)  Pydantic request/response models
    token_exchange.py          (74 lines)  Server-side token caching
    middleware.py              (59 lines)  Security headers + CORS
    routes/
      health.py                (28 lines)  /health
      auth_routes.py           (32 lines)  /api/v1/auth/whoami
      token_routes.py          (53 lines)  /api/v1/auth/exchange
      algorithms.py            (35 lines)  /api/v1/algorithms
      jobs.py                  (66 lines)  /api/v1/jobs

services/worker-v3/            Document processing worker
  src/
    main.py                    (monolith - pending decomposition)
    job_processor.py           (188 lines) Job orchestration
    config.py                  (146 lines) Config + secret manager
    filename_builder.py        (105 lines) Template-based filename builder
    ai_classifier.py           (99 lines)  AI response parser
    drive_operations.py        (97 lines)  Drive API operations
    models.py                  (49 lines)  Pydantic models
    logger.py                  (38 lines)  Dev/prod logging

services/frontend/             Angular standalone components
  src/app/
    components/
      auth/                    Google Sign-In + user header
      dashboard/               Folder picker + job submission
      algorithms/              Algorithm listing
      audit/                   Grouped audit logs
      settings/                Session + token status
```

## Test Suite

| Package | Tests | Status |
|---------|-------|--------|
| Core (core-renombrador) | 77 | 75 pass, 2 pre-existing |
| API Server v3 | 58 | All pass |
| Worker v3 | 69 | All pass |
| Infrastructure | 44 | All pass |
| Frontend | 6 specs | All pass |

## Deployment

### V3 (Parallel — recommended)

```bash
# Deploy both v3 services
./infra/deploy-v3.sh all

# Shift traffic gradually
./infra/deploy-v3.sh traffic 10   # 10% to v3
./infra/deploy-v3.sh traffic 50   # 50% to v3
./infra/deploy-v3.sh traffic 100  # 100% to v3
```

### V2 (Legacy)

```powershell
gcloud builds submit --config services/worker-renombrador/cloudbuild.yaml --project=cloud-functions-474716
gcloud builds submit --config services/api-server/cloudbuild.yaml --project=cloud-functions-474716
```

## CI/CD

GitHub Actions pipeline (`.github/workflows/ci.yml`):
1. **Lint** (ruff) on all v3 Python source
2. **Test** core, api-v3, worker-v3 in parallel
3. **File size check** — fails if any source file >250 lines

## Database Migrations

```sql
-- Run in Supabase SQL Editor
infra/migrations/001_add_foreign_keys.sql           -- FK: job_executions → jobs
infra/migrations/002_rename_active_to_is_active.sql -- Standardize naming
infra/migrations/003_add_indexes.sql                -- Performance indexes
```

Each migration has a `_rollback.sql` counterpart.

## Design Decisions

- **Framework-agnostic core**: `core-renombrador` imports no web framework
- **No Flask**: v3 uses FastAPI exclusively
- **Separate folders**: v3 lives in `*-v3/` directories, v2 is never touched
- **Facade pattern**: Original files delegate to decomposed modules
- **Strict TDD**: Red → Green → Refactor for every task
- **GitFlow**: `main` → `develop` → `feature/p{N}-{component}-{change}` → squash merge

---
*Desarrollado por CENF*
