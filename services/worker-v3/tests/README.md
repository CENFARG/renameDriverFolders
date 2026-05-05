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
# tests/test_file_processing.py
@pytest.mark.unit
def test_extract_pdf_text():
    """Should extract text from PDF content."""
    content = b"%PDF-1.4...test data..."
    result = extract_text_from_pdf(content)
    assert "test data" in result
```

### 2. Run Test - Must FAIL 🔴
```bash
$ pytest tests/test_file_processing.py::test_extract_pdf_text
FAILED - function not implemented yet
```

### 3. GREEN Phase - Write Minimal Code
```python
# main.py
def extract_text_from_pdf(pdf_content: bytes) -> str:
    # Extract text from PDF
    return pypdf.PdfReader(io.BytesIO(pdf_content)).pages[0].extract_text()
```

### 4. Run Test - Must PASS ✅
```bash
$ pytest tests/test_file_processing.py::test_extract_pdf_text
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
- `@pytest.mark.integration` - May touch Google APIs/DB
- `@pytest.mark.slow` - Slow tests (skip with `-m "not slow"`)

### Structure
```
tests/
├── test_main.py           # Example tests
├── test_file_processing.py # File renaming logic
├── test_agent.py          # AI agent tests
├── test_oauth.py          # OAuth tests
└── conftest.py            # Shared fixtures
```

---

## Guidelines

✅ **DO:**
- Write test BEFORE implementation
- Keep unit tests fast (< 0.1s each)
- Mock Google APIs (Drive, Gemini)
- Mock AI agent responses
- Use descriptive test names
- Test ONE thing per test

❌ **DON'T:**
- Write code without test
- Test multiple things in one test
- Call real Google APIs in unit tests
- Call real Gemini API in unit tests
- Skip writing tests "for now"

---

## Coverage Goals

- **Unit tests**: > 80% coverage
- **Critical paths**: 100% coverage (file processing, OAuth)
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
