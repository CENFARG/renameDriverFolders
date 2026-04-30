# STRICT TDD MODE - ENABLED ✅

**Project**: renameDriverFolders
**Status**: ACTIVE (as of 2026-04-21)

---

## What This Means

**ALL new code MUST be written using Test-Driven Development.**

No exceptions. No "I'll add tests later". Tests FIRST, implementation SECOND.

---

## The Protocol

### 1. RED 🔴
Write a test that FAILS.
```python
@pytest.mark.unit
def test_job_create_requires_folder_id():
    with pytest.raises(ValueError):
        create_job(folder_id=None)
```

### 2. GREEN ✅
Write MINIMAL code to make test pass.
```python
def create_job(folder_id):
    if not folder_id:
        raise ValueError("folder_id required")
    return {"id": "job-1", "folder_id": folder_id}
```

### 3. REFACTOR ♻️
Improve code while keeping tests GREEN.
```python
def create_job(folder_id: str) -> dict:
    if not folder_id:
        raise ValueError("folder_id required")
    return Job(id=f"job-{uuid4()}", folder_id=folder_id)
```

---

## Quick Commands

```bash
# API Server
cd services/api-server
pytest -m unit              # TDD loop (fast tests)
pytest                      # All tests
pytest --cov=.              # With coverage

# Worker
cd services/worker-renombrador
pytest -m unit
pytest --cov=.

# Frontend
cd services/frontend
npm test                    # Vitest
```

---

## Tools Installed

### Backend (Both Services)
- ✅ pytest 7.4.0 (test runner)
- ✅ pytest-asyncio (async tests)
- ✅ pytest-cov (coverage)
- ✅ coverage 7.3.0
- ✅ ruff 0.1.0 (linter + formatter)
- ✅ mypy 1.7.0 (type checker)

### Frontend
- ✅ Vitest 4.0.8
- ✅ Prettier (formatter)
- ✅ TypeScript (type checker)

---

## Rules

### ✅ DO
1. Write test FIRST
2. Run test immediately (must FAIL)
3. Write code to pass test
4. Run test again (must PASS)
5. Refactor if needed
6. Repeat

### ❌ DON'T
1. Write code without test
2. Write multiple tests at once
3. Skip test writing "for now"
4. Commit untested code
5. Disable failing tests

---

## Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| API Server | >80% | ~0% (start writing!) |
| Worker | >80% | ~0% (start writing!) |
| Frontend | >60% | ~5% (basic test) |
| Critical paths | 100% | 0% (OAuth, job creation) |

---

## Next Steps

1. Install dependencies: `pip install -r requirements.txt` (in each service)
2. Run `pytest -m unit` to verify setup
3. Start writing tests for v3 refactor
4. NEVER go back to writing untested code

---

## Documentation

- API Server Tests: `services/api-server/tests/README.md`
- Worker Tests: `services/worker-renombrador/tests/README.md`
- pytest.ini: Configuration in each service

---

**Remember:** Tests are not optional. They are mandatory. 🚀
