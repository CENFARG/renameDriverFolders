# Testing - STRICT TDD MODE

**Protocol:** ENABLED ✅
**All new code MUST be written test-first.**

---

## Quick Start

```bash
# Install dependencies
pip install -r ../requirements.txt

# Run fast unit tests (TDD loop)
pytest -m unit

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Lint and type check
ruff check .
mypy .
```

---

## STRICT TDD WORKFLOW

### 1. RED Phase - Write Test First
```python
# tests/test_jobs.py
@pytest.mark.unit
def test_create_manual_job_missing_field():
    """Should raise error when folder_id is missing."""
    with pytest.raises(HTTPException) as exc:
        create_manual_job(job_type="generic", folder_id=None)
    assert exc.value.status_code == 400
```

### 2. Run Test - Must FAIL 🔴
```bash
$ pytest tests/test_jobs.py::test_create_manual_job_missing_field
FAILED - function not implemented yet
```

### 3. GREEN Phase - Write Minimal Code
```python
# main.py
def create_manual_job(job_type: str, folder_id: Optional[str]):
    if not folder_id:
        raise HTTPException(status_code=400, detail="folder_id required")
    # ... rest of implementation
```

### 4. Run Test - Must PASS ✅
```bash
$ pytest tests/test_jobs.py::test_create_manual_job_missing_field
PASSED
```

### 5. REFACTOR Phase - Improve Code
- Keep tests green
- Clean up code
- Extract abstractions
- Run tests again

---

## Test Organization

### Markers
- `@pytest.mark.unit` - Fast, no external deps (default for TDD)
- `@pytest.mark.integration` - May touch database/external APIs
- `@pytest.mark.slow` - Slow tests (skip with `-m "not slow"`)

### Structure
```
tests/
├── test_main.py           # Example tests
├── test_jobs.py           # Job management tests
├── test_oauth.py          # OAuth flow tests
└── conftest.py            # Shared fixtures
```

---

## Guidelines

✅ **DO:**
- Write test BEFORE implementation
- Keep unit tests fast (< 0.1s each)
- Mock external dependencies (Google APIs, Supabase)
- Use descriptive test names
- Test ONE thing per test

❌ **DON'T:**
- Write code without test
- Test multiple things in one test
- Call real Google APIs in unit tests
- Skip writing tests "for now"

---

## Coverage Goals

- **Unit tests**: > 80% coverage
- **Critical paths**: 100% coverage (OAuth, job creation)
- **Integration tests**: Key flows only

---

## Troubleshooting

**Tests not found?**
```bash
pytest --collect-only  # See what tests are discovered
```

**Import errors?**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

**Too slow?**
```bash
pytest -m unit  # Only fast unit tests
```
