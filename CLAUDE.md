# renameDriverFolders — Project Rules

## 250-Line Hard Limit

Every Python source file (excluding tests, `__init__.py`, `conftest.py`) MUST be under 250 lines. No exceptions. If a file grows beyond 250 lines, it MUST be decomposed into smaller modules.

This is enforced by:
- CI pipeline file-size-check job (fails the build)
- `infra/tests/test_cleanup_verification.py` (65 parametrized checks)

Reasoning: files over 250 lines are harder to debug, harder to test, and harder to review. A good structured logger in each module makes debugging fast. Small files + structured logging > monolith + print statements.

## Architecture

- **Core package** (`packages/core-renombrador/`): framework-agnostic, no Flask, no FastAPI
- **Services** (`services/api-server-v3/`, `services/worker-v3/`): FastAPI only
- **v2 is frozen**: never modify `services/api-server/`, `services/worker-renombrador/`
- **Facade pattern**: original files delegate to decomposed modules

## Testing

- Strict TDD: Red → Green → Refactor
- Every module gets its own test file
- No `print()` in production code — use `logging.getLogger(__name__)`

## Git

- GitFlow: `main` → `develop` → `feature/p{N}-{component}-{change}` → squash merge
- Conventional commits
- No AI attribution (no Co-Authored-By)
