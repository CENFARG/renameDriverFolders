# 🏗️ 04. TECHNICAL DESIGN
## Proyecto Renombrador (#amBotHsOS) - V3.1.2 "Estudio Inteligente"

---

## 🎯 PROPÓSITO DEL DOCUMENTO

Describir la arquitectura técnica, stack tecnológico, patrones de diseño y decisiones arquitectónicas del sistema **Renombrador** V3.1.2.

---

## 🏗️ ARQUITECTURA GENERAL

### Patrón Arquitectónico: Microservicios Serverless

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER: PRESENTATION                       │
│                  Frontend (Angular 19)                      │
│         OAuth UI + Google Drive Picker + Dashboard           │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS (OAuth)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     LAYER: API GATEWAY                       │
│                  API Server (FastAPI)                        │
│    Security + Rate Limiting + Dispatch + Validation          │
└──────────────────────────┬──────────────────────────────────┘
                           │ Cloud Tasks
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      LAYER: WORKER                           │
│                  Worker (FastAPI)                            │
│           Processing + AI Analysis + Renaming                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   LAYER: INFRASTRUCTURE                      │
│  Supabase │ GCS │ Gemini │ Cloud Vision │ Drive │ Tasks    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 COMPONENTES DEL SISTEMA

### 1. Frontend (Angular 19)

**Ubicación:** `services/frontend/`

**Responsabilidades:**
- Google Sign-In integration
- Google Drive Picker integration
- UI de gestión de algoritmos
- Dashboard de auditoría

**Stack:**
- **Framework:** Angular 19.0.0
- **Language:** TypeScript
- **UI Library:** Angular Material
- **Styling:** TailwindCSS 3.4.17
- **State Management:** RxJS BehaviorSubjects

**Componentes Principales:**
```typescript
AppComponent          // Componente principal
├── AuthService       // Google Sign-In
├── JobService        // CRUD de algoritmos
├── AuditService      // Logs de auditoría
├── PickerService     // Google Drive Picker
└── NotificationService // Toast messages
```

**Endpoints Consumidos:**
```typescript
GET  /api/v1/auth/whoami
POST /api/v1/jobs/manual
GET  /api/v1/jobs
GET  /api/v1/audit-logs
```

---

### 2. API Server (FastAPI)

**Ubicación:** `services/api-server/`

**Responsabilidades:**
- OAuth 2.0 validation
- Domain whitelisting
- Rate limiting
- Cloud Tasks dispatch
- Job configuration management

**Stack:**
- **Framework:** FastAPI
- **Language:** Python 3.11+
- **Auth:** Google Identity Services
- **Queue:** Google Cloud Tasks

**Endpoints:**
```python
# Health
GET  /health

# Authentication
GET  /api/v1/auth/whoami

# Jobs
GET    /api/v1/jobs
POST   /api/v1/jobs/manual     # OAuth required
POST   /api/v1/jobs/scheduled  # OIDC required (Cloud Scheduler)

# Audit Logs
GET  /api/v1/audit-logs
```

**Middlewares:**
```python
CORSMiddleware       # CORS configuration
SecurityMiddleware   # Security headers
RateLimitMiddleware  # 10 req/min per user
OAuthMiddleware      # Token validation
DomainMiddleware     # Domain whitelisting
```

---

### 3. Worker (FastAPI)

**Ubicación:** `services/worker-renombrador/`

**Responsabilidades:**
- Process tasks from Cloud Tasks
- Create Agno agents dynamically
- Extract content (OCR if needed)
- Analyze with Gemini
- Rename files in Google Drive

**Stack:**
- **Framework:** FastAPI
- **AI Framework:** Agno 2.3.9
- **LLM:** Google Gemini 2.0/2.5 Flash
- **OCR:** Google Cloud Vision API

**Endpoints:**
```python
POST /run-task   # Process from Cloud Tasks
POST /run-job    # Manual execution
GET  /health
```

**Processing Pipeline:**
```python
1. Load job configuration from Supabase
2. Create Agno agent from config
3. List files in Google Drive folder
4. For each file:
   a. Extract content (OCR if PDF/image)
   b. Analyze with Gemini
   c. Extract metadata (date, type, issuer, etc.)
   d. Generate new filename
   e. Rename file in Google Drive
   f. Log execution
5. Return summary (processed, renamed, errors)
```

---

### 4. Core Package

**Ubicación:** `packages/core-renombrador/`

**Responsabilidades:**
- Shared functionality across services
- Configuration management
- Database abstraction
- Logging
- Error handling

**Módulos (13):**

```python
core_renombrador/
├── agent_factory.py       # Create Agno agents dynamically
├── content_extractor.py   # Extract content with OCR
├── config_manager.py      # Hybrid config (Env > DB > File)
├── database_manager.py    # Multi-backend (JSON/GCS/Supabase)
├── drive_handler.py       # Google Drive integration
├── oauth_security.py      # OAuth validation
├── file_manager.py        # File operations
├── logger_manager.py      # Logging
├── error_handler.py       # Error handling
├── models.py              # Pydantic models
├── toon_converter.py      # Token optimization
├── documentation_manager.py # Docs management
└── __init__.py
```

---

### 5. Infraestructura

#### 5.1 Google Cloud Run

**Servicios Desplegados:**
- `renombradorarchivosgdrive-api-server-v2`
- `renombradorarchivosgdrive-worker-v2`
- `renombradorarchivosgdrive-frontend-v2`

**Configuración:**
```yaml
Region: us-central1
Instance type: Serverless
Min instances: 0
Max instances: 100
Memory: 512Mi - 1Gi
CPU: 1 - 2 vCPUs
Timeout: 60s (API), 15m (Worker)
```

#### 5.2 Google Cloud Tasks

**Cola:** `rename-queue`

**Configuración:**
```yaml
Location: us-central1
Rate limits: 1000/s
Max attempts: 3 (with exponential backoff)
Max dispatch duration: 15m
```

#### 5.3 Google Cloud Scheduler

**Jobs:**
- `rename-jobs-trigger` (cron: `0 8 * * *`)

**Configuración:**
```yaml
Schedule: Daily at 8:00 AM
Timezone: America/Argentina/Buenos_Aires
Target: API Server /api/v1/jobs/scheduled
Auth: OIDC token
```

#### 5.4 Supabase PostgreSQL

**Tablas:**
```sql
jobs
├── id (UUID, PK)
├── name (VARCHAR)
├── folder_id (VARCHAR)
├── frequency (VARCHAR)
├── format (VARCHAR)
├── algorithm (JSONB)
├── is_active (BOOLEAN)
└── created_at (TIMESTAMP)

job_executions
├── id (UUID, PK)
├── job_id (UUID, FK)
├── status (VARCHAR)  -- SUBMITTED, IN_PROGRESS, COMPLETED, FAILED
├── trigger_type (VARCHAR)  -- MANUAL, SCHEDULED
├── files_processed (INT)
├── files_renamed (INT)
├── errors (JSONB)
└── created_at (TIMESTAMP)
```

---

## 🔄 FLUJO DE DATOS END-TO-END

### Manual Execution Flow

```
┌─────────┐
│ Usuario │
└────┬────┘
     │ 1. Click "Procesar Ahora"
     ▼
┌─────────────────────────────────────┐
│ Frontend (Angular)                  │
│ - Get OAuth token                   │
│ - Validate folder_id                │
└────┬────────────────────────────────┘
     │ 2. POST /api/v1/jobs/manual
     │    {folder_id, job_type}
     ▼
┌─────────────────────────────────────┐
│ API Server (FastAPI)                │
│ - Validate OAuth token              │
│ - Check domain whitelist            │
│ - Enforce rate limit                │
│ - Create task in Cloud Tasks        │
└────┬────────────────────────────────┘
     │ 3. Task enqueued
     ▼
┌─────────────────────────────────────┐
│ Cloud Tasks Queue                   │
│ - Buffer tasks                      │
│ - Retry on failure                  │
└────┬────────────────────────────────┘
     │ 4. POST /run-task
     ▼
┌─────────────────────────────────────┐
│ Worker (FastAPI)                    │
│ - Load job config from Supabase     │
│ - Create Agno agent                 │
│ - List files in Drive               │
│ - Process each file:                │
│   1. Extract content (OCR)          │
│   2. Analyze with Gemini            │
│   3. Generate name                  │
│   4. Rename in Drive                │
│ - Log to Supabase                   │
└────┬────────────────────────────────┘
     │ 5. Update job_execution status
     ▼
┌─────────────────────────────────────┐
│ Supabase (PostgreSQL)               │
│ - Insert execution log              │
│ - Update job status                 │
└─────────────────────────────────────┘
     │
     ▼
┌─────────┐
│ Usuario │  <-- Frontend polls /api/v1/audit-logs
└─────────┘
```

---

## 🤖 IA ARCHITECTURE

### Agno Agent Configuration

**Framework:** Agno 2.3.9 (antes Phidata)

**Agent Factory Pattern:**
```python
class AgentFactory:
    @staticmethod
    def create_agent(job_config: JobConfig) -> Agent:
        return Agent(
            name=job_config.name,
            role="Contador Experto en RG 830",
            llm=Google(
                id="gemini-2.0-flash-exp",
                api_key=os.getenv("GEMINI_API_KEY")
            ),
            instructions=job_config.algorithm["prompt"],
            output_type=FileAnalysis,  # Pydantic model
            tools=[GoogleDriveTool(), CloudVisionTool()]
        )
```

**Structured Outputs (Pydantic):**
```python
class FileAnalysis(BaseModel):
    """Modelo para salida estructurada de Gemini"""

    date: str = Field(
        description="Fecha del documento en formato YYYY-MM-DD"
    )
    type: str = Field(
        description="Tipo: Factura, Recibo, Resumen, etc."
    )
    issuer: str = Field(
        description="Empresa que emite el documento"
    )
    entity: str = Field(
        description="Cliente o Proveedor"
    )
    concept: str = Field(
        description="Descripción breve del concepto"
    )
    amount: Optional[float] = Field(
        description="Monto del documento (si aplica)"
    )
    currency: Optional[str] = Field(
        description="Moneda: ARS, USD, EUR"
    )
```

**Prompt Template:**
```python
PROMPT_TEMPLATE = """
Eres un contador experto argentino especializado en RG 830.

Analiza el documento y extrae la siguiente información:
- Fecha: Fecha del documento (prioriza fecha de factura, no de recepción)
- Tipo: Factura A/B/C, Recibo, Resumen, etc.
- Emisor: Empresa que emite (ej: "Morgan Stanley")
- Entidad: Cliente o Proveedor
- Concepto: Descripción breve (ej: "Servicios de Consultoría")
- Monto: Monto total (si aplica)
- Moneda: ARS, USD, EUR

Genera un nombre de archivo siguiendo el formato:
{date}_{type}_{issuer}_{concept}.{ext}

Ejemplo: 2025-03-12_Factura_B_MorganStanley_ServiciosConsultoria.pdf

Restricciones:
- Usa camelCase para emisores y conceptos (sin espacios ni caracteres especiales)
- Fecha en formato YYYY-MM-DD (ISO)
- Tipo sin espacios (ej: "FacturaB", no "Factura B")
- Extensión en minúsculas
"""
```

---

## 🔒 SEGURIDAD

### OAuth 2.0 Flow

```
┌─────────┐
│ Usuario │
└────┬────┘
     │ 1. Click "Iniciar Sesión con Google"
     ▼
┌─────────────────────────────────────┐
│ Frontend (Angular)                  │
│ - Load GIS (Google Identity Service)│
│ - Request OAuth token               │
└────┬────────────────────────────────┘
     │ 2. OAuth token
     ▼
┌─────────────────────────────────────┐
│ API Server (FastAPI)                │
│ - Validate token with Google        │
│ - Extract email from token          │
│ - Check domain whitelist            │
│ - Return 200 + {authenticated, user}│
└─────────────────────────────────────┘
```

### Domain Whitelisting

**Configuración:**
```python
ALLOWED_DOMAINS = [
    "estudioanc.com.ar",
    "gmail.com"
]

def validate_domain(email: str) -> bool:
    domain = email.split("@")[1]
    return domain in ALLOWED_DOMAINS
```

### Rate Limiting

**Configuración:**
```python
MAX_REQUESTS_PER_MINUTE = 10

@lru_cache(maxsize=1000)
def check_rate_limit(user_email: str) -> bool:
    key = f"rate_limit:{user_email}:{datetime.now().minute}"
    count = redis.incr(key)
    redis.expire(key, 60)
    return count <= MAX_REQUESTS_PER_MINUTE
```

---

## 📊 MONITORING Y LOGGING

### Logging Strategy

**Niveles de Log:**
```python
DEBUG   - Desarrollo: Información detallada
INFO    - Producción: Eventos de negocio
WARNING - Anomalías no críticas
ERROR   - Errores que requieren atención
```

**Formato:**
```python
[timestamp] - [module] - [level] - [file:line] - message
```

**Ejemplo:**
```
2026-03-12 18:45:00 - api-server.main - INFO - [main.py:50] - POST /api/v1/jobs/manual - user: diego@estudioanc.com.ar
2026-03-12 18:45:01 - worker.main - DEBUG - [main.py:100] - Processing task: task-123
2026-03-12 18:45:15 - worker.agent - INFO - [agent.py:50] - File analyzed: morgan_stanley.pdf -> 2025-03-12_Factura_B_MorganStanley_Servicios.pdf
```

### Metrics

**KPIs Monitoreados:**
- Requests per minute
- Average response time
- Error rate
- Worker processing time
- Files processed per job
- Files renamed successfully
- OCR success rate
- Gemini API latency

---

## 🔄 CI/CD (FUTURO)

### Pipeline Propuesto

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main, develop]

jobs:
  test:
    - Run pytest
    - Run ESLint
    - Run TSLint

  build:
    - Build Docker images
    - Push to GCR

  deploy:
    - Deploy to Cloud Run
    - Run smoke tests
```

---

**Creado:** 12 de Marzo, 2026
**Versión:** 1.0
**Próxima revisión:** V4.0 (Multi-tenancy)

---

*Este documento es parte de los 10 documentos de gestión CENF v2.3.0*
