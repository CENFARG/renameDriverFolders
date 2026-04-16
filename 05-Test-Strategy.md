# 🧪 05. TEST STRATEGY
## Proyecto Renombrador (#amBotHsOS) - V3.1.2 "Estudio Inteligente"

---

## 🎯 PROPÓSITO DEL DOCUMENTO

Definir la estrategia de testing para el sistema **Renombrador** V3.1.2, incluyendo tipos de tests, frameworks, y cobertura objetivo.

---

## 📊 ESTADO ACTUAL

| Tipo de Test | Cobertura | Estado |
|--------------|-----------|--------|
| **Unit Tests** | 0% | ❌ No implementados |
| **Integration Tests** | 0% | ❌ No implementados |
| **E2E Tests** | 0% | ❌ No implementados |
| **Manual Tests** | Manual | ✅ Parcial |

---

## 🎯 ESTRATEGIA DE TESTING

### Pirámide de Testing

```
        ▲
       /E\      E2E Tests (10%)
      /---\     - Playwright / Cypress
     /-----\    - Flujos críticos de usuario
    /-------\
   / Unitary \  Unit Tests (70%)
  /  Tests    \ - pytest
 /-------------\ - Módulos individuales
/   Integration \ Integration Tests (20%)
\    Tests      / - API + Database
\---------------/ - Worker + Cloud Services
```

---

## 🧪 FRAMEWORKS Y HERRAMIENTAS

### Backend (Python)

**Framework:** pytest

**Librerías:**
```python
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
pytest-mock==3.11.1
httpx==0.24.1  # Para testear FastAPI
```

**Configuración:**
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --cov=services/api-server/src
    --cov=services/worker/src
    --cov=packages/core/src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

### Frontend (TypeScript/Angular)

**Framework:** Jasmine + Karma (Angular default)

**Librerías:**
```json
{
  "devDependencies": {
    "@angular-devkit/build-angular": "^19.0.0",
    "jasmine-core": "^5.1.0",
    "jasmine-spec-reporter": "^7.0.0",
    "karma": "^6.4.0",
    "karma-chrome-launcher": "^3.2.0",
    "karma-coverage": "^2.2.0"
  }
}
```

### E2E Tests

**Framework:** Playwright

**Librerías:**
```json
{
  "devDependencies": {
    "@playwright/test": "^1.40.0"
  }
}
```

---

## 📋 PLAN DE TESTING

### Fase 1: Unit Tests (70% de cobertura objetivo)

#### Backend - API Server

**Tests a Implementar:**
```python
# tests/api-server/test_auth.py
def test_whoami_unauthenticated():
    """Test que /whoami retorna 401 sin token"""
    response = client.get("/api/v1/auth/whoami")
    assert response.status_code == 401

def test_whoami_authenticated():
    """Test que /whoami retorna user info con token válido"""
    response = client.get(
        "/api/v1/auth/whoami",
        headers={"Authorization": "Bearer valid_token"}
    )
    assert response.status_code == 200
    assert response.json()["authenticated"] == True

def test_domain_whitelist_invalid():
    """Test que rechaza dominios no autorizados"""
    response = client.post(
        "/api/v1/jobs/manual",
        json={"folder_id": "abc123"},
        headers={"Authorization": "Bearer invalid_domain_token"}
    )
    assert response.status_code == 403

def test_rate_limiting():
    """Test que respeta rate limit de 10 req/min"""
    for i in range(11):
        response = client.get("/api/v1/jobs")
    assert response.status_code == 429
```

**Cobertura Objetivo:** 80%

#### Backend - Worker

**Tests a Implementar:**
```python
# tests/worker/test_agent_factory.py
def test_create_agent_from_config():
    """Test creación de agente desde config"""
    config = JobConfig(
        name="Test Job",
        algorithm={"prompt": "Test prompt"}
    )
    agent = AgentFactory.create_agent(config)
    assert agent.name == "Test Job"

# tests/worker/test_content_extractor.py
def test_extract_text_from_pdf():
    """Test extracción de texto desde PDF"""
    content = ContentExtractor.extract("test.pdf")
    assert "Factura" in content

def test_extract_text_from_scanned_pdf():
    """Test OCR en PDF escaneado"""
    content = ContentExtractor.extract("scanned.pdf")
    assert len(content) > 0
```

**Cobertura Objetivo:** 75%

#### Backend - Core Package

**Tests a Implementar:**
```python
# tests/core/test_config_manager.py
def test_config_priority():
    """Test que ENV > DB > File"""
    os.environ["TEST_VAR"] = "env_value"
    config = ConfigManager.get("TEST_VAR")
    assert config == "env_value"

# tests/core/test_database_manager.py
def test_supabase_connection():
    """Test conexión a Supabase"""
    db = DatabaseManager(SupabaseBackend)
    assert db.ping() == True

# tests/core/test_models.py
def test_file_analysis_schema():
    """Test validación de Pydantic model"""
    data = {
        "date": "2025-03-12",
        "type": "Factura",
        "issuer": "Morgan Stanley"
    }
    analysis = FileAnalysis(**data)
    assert analysis.date == "2025-03-12"
```

**Cobertura Objetivo:** 85%

### Fase 2: Integration Tests (20% de cobertura objetivo)

#### API + Database

```python
# tests/integration/test_api_supabase.py
def test_create_job_persists_to_supabase():
    """Test que crear job se persiste en Supabase"""
    response = client.post(
        "/api/v1/jobs/manual",
        json={"folder_id": "abc123"},
        headers={"Authorization": "Bearer valid_token"}
    )
    assert response.status_code == 200

    # Verificar en Supabase
    job = supabase.table("jobs").select("*").eq("id", response.json()["job_id"]).execute()
    assert len(job.data) == 1
```

#### Worker + Google Services

```python
# tests/integration/test_worker_gemini.py
@pytest.mark.integration
def test_worker_analyzed_document_with_gemini():
    """Test que worker analiza doc con Gemini real"""
    task = {
        "job_id": "test_job",
        "folder_id": "test_folder",
        "trigger_type": "manual"
    }
    response = client.post("/run-job", json=task)
    assert response.status_code == 200
    assert response.json()["files_renamed"] > 0
```

**Cobertura Objetivo:** 60%

### Fase 3: E2E Tests (10% de cobertura objetivo)

#### Playwright Tests

```typescript
// tests/e2e/spec.ts
test('flujo completo: login -> crear job -> ejecutar', async ({ page }) => {
  // 1. Login con Google
  await page.goto('https://renombrador-frontend-url');
  await page.click('button:has-text("Iniciar Sesión")');
  await page.fill('input[name="email"]', 'test@estudioanc.com.ar');
  await page.click('button:has-text("Siguiente")');

  // 2. Crear nuevo algoritmo
  await page.click('button:has-text("Nuevo Algoritmo")');
  await page.fill('input[name="name"]', 'Test Job');
  await page.click('button:has-text("Seleccionar Carpeta")');
  // Google Drive Picker...

  // 3. Ejecutar manualmente
  await page.click('button:has-text("Procesar Ahora")');
  await page.waitForSelector('text=Tarea enviada');

  // 4. Verificar en dashboard
  await page.click('a:has-text("Auditoría")');
  await page.waitForSelector('text=COMPLETED');
});
```

**Cobertura Objetivo:** 40% (solo flujos críticos)

---

## 📊 MATRIZ DE COBERTURA OBJETIVO

| Componente | Unit | Integration | E2E | Total |
|------------|------|-------------|-----|-------|
| **API Server** | 80% | 70% | 0% | 75% |
| **Worker** | 75% | 60% | 0% | 65% |
| **Core Package** | 85% | 50% | 0% | 75% |
| **Frontend** | 70% | 0% | 40% | 55% |
| **TOTAL** | 77% | 60% | 10% | **70%** |

---

## 🚀 EJECUCIÓN DE TESTS

### Comandos

```bash
# Backend - Unit tests
pytest tests/unit/ -v --cov=services --cov-report=html

# Backend - Integration tests
pytest tests/integration/ -v --integration

# Frontend - Unit tests
ng test --code-coverage

# E2E tests
playwright test

# Todos los tests
pytest tests/ -v && ng test && playwright test
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: ng test --code-coverage
```

---

## 📋 CRITERIOS DE ACEPTACIÓN

### Para V3.2 (Q2 2026)

- [ ] Cobertura total >70%
- [ ] Todos los tests unitarios pasan
- [ ] Todos los tests de integración pasan
- [ ] Todos los tests E2E pasan
- [ ] Tests ejecutan en <5 minutos
- [ ] Tests ejecutan en CI/CD

---

**Creado:** 12 de Marzo, 2026
**Versión:** 1.0
**Próxima revisión:** V3.2 (Q2 2026)

---

*Este documento es parte de los 10 documentos de gestión CENF v2.3.0*
