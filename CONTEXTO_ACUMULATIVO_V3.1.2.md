# 📋 CONTEXTO ACUMULATIVO - Proyecto Renombrador (#amBotHsOS)
## Versión V3.1.2 "Estudio Inteligente" - Última actualización: 2026-03-12

---

## 🎯 RESUMEN EJECUTIVO

**Propósito del Proyecto:**
Sistema de automatización inteligente de documentos en Google Drive que utiliza IA (Google Gemini 2.0/2.5 Flash) para analizar, categorizar y renombrar archivos automáticamente según su contenido visual y textual.

**Estado Actual:**
- ✅ **Versión V3.1.2 desplegada y estable** en Google Cloud Run
- ✅ **Arquitectura de microservicios** completa (API Server + Worker + Frontend)
- ✅ **Hotfixes aplicados:** Errores 422, validación de folder IDs, seguridad GIS
- ✅ **Sistema listo para entrega** al cliente (Estudio Cutignola)

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA COMPLETO                          │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │──────│  API Server  │──────│ Cloud Tasks  │
│  (OAuth UI)  │      │  (Gateway)   │      │   (Queue)    │
│  Angular 19  │      │   FastAPI    │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
                             │                      │
                             │                      ▼
                             │              ┌──────────────┐
                             │              │    Worker    │
                             │              │ (Processor)  │
                             │              │   FastAPI    │
                             ▼              └──────────────┘
                      ┌──────────────┐              │
                      │   Supabase   │              ▼
                      │  (Jobs DB)   │      ┌──────────────┐
                      └──────────────┘      │ Google Drive │
                             │              │   (Files)    │
                             ▼              └──────────────┘
                      ┌──────────────┐
                      │ Cloud Vision │
                      │    (OCR)     │
                      └──────────────┘
```

### Servicios Desplegados

| Servicio | URL | Estado | Versión |
|----------|-----|--------|---------|
| **API Server** | `renombradorarchivosgdrive-api-server-v2` | ✅ Activo | v2-00034 |
| **Worker** | `renombradorarchivosgdrive-worker-v2` | ✅ Activo | v2-00024 |
| **Frontend** | `renombradorarchivosgdrive-frontend-v2` | ✅ Activo | Angular 19 |

---

## 📦 CORE PACKAGE (Módulos Compartidos)

**Ubicación:** `packages/core-renombrador/`

### Módulos Implementados (13 módulos):

1. **`agent_factory.py`** - Factoría para crear agentes Agno dinámicamente
2. **`content_extractor.py`** - Extracción de contenido con OCR
3. **`config_manager.py`** - Gestión de configuración híbrida (Env > DB > File)
4. **`database_manager.py`** - Interfaz unificada (JSON/GCS/Supabase)
5. **`drive_handler.py`** - Integración con Google Drive
6. **`oauth_security.py`** - Seguridad OAuth2 y domain whitelisting
7. **`file_manager.py`** - Operaciones de archivos
8. **`logger_manager.py`** - Logging centralizado
9. **`error_handler.py`** - Manejo de errores
10. **`models.py`** - Modelos Pydantic para structured outputs
11. **`toon_converter.py`** - Optimización de tokens
12. **`documentation_manager.py`** - Gestión de documentación
13. **`__init__.py`** - Inicializador del paquete

---

## 🔧 ENDPOINTS API

### API Server (FastAPI)

**Autenticación:** OAuth 2.0 con Google Sign-In

#### Endpoints Principales:

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/jobs/manual` | Envío de jobs manuales | OAuth |
| `POST` | `/api/v1/jobs/scheduled` | Trigger de jobs programados | OIDC |
| `GET` | `/api/v1/jobs` | Listar configuraciones | OAuth |
| `GET` | `/api/v1/audit-logs` | Logs de auditoría | OAuth |
| `GET` | `/api/v1/auth/whoami` | Verificar autenticación | OAuth |
| `GET` | `/health` | Health check | Público |

### Worker (FastAPI)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/run-task` | Procesa tarea desde Cloud Tasks |
| `POST` | `/run-job` | Ejecución manual de job |
| `GET` | `/health` | Health check |

---

## 🔐 SEGURIDAD IMPLEMENTADA

### Características de Seguridad:
- ✅ **OAuth 2.0** con Google Sign-In
- ✅ **Domain Whitelisting** (`estudioanc.com.ar`, `gmail.com`)
- ✅ **Rate Limiting** (10 req/min)
- ✅ **OIDC** para Cloud Scheduler
- ✅ **CORS** configurado para orígenes permitidos
- ✅ **Security Headers** middleware

### Dominios Autorizados:
- `estudioanc.com.ar`
- `gmail.com`

---

## 🤖 STACK TECNOLÓGICO

### Backend:
- **Python 3.11+**
- **FastAPI** - Framework web para APIs
- **Agno 2.3.9** (antes Phidata) - Framework de agentes IA
- **Google Gemini 2.0/2.5** - Modelos de lenguaje
- **Google Cloud Vision API** - OCR para imágenes y PDFs

### Frontend:
- **TypeScript** - Angular 19.0.0
- **Angular Material** - UI components
- **TailwindCSS** - Estilos

### Infraestructura:
- **Docker** - Contenedores
- **Google Cloud Run** - Plataforma serverless
- **Google Cloud Tasks** - Cola de tareas
- **Google Cloud Scheduler** - Programación de tareas
- **Google Cloud Storage** - Almacenamiento
- **Supabase** - Base de datos PostgreSQL

---

## 📝 FUNCIONALIDADES PRINCIPALES

### 1. Sistema Multi-Job

**Frecuencias Soportadas:**
- ✅ Diario (ej: 8:00 AM)
- ✅ Semanal (ej: Lunes 9:00 AM)
- ✅ Mensual (ej: Día 1, 10:00 AM)
- ✅ Trimestral (ej: 15 Marzo)
- ✅ Anual (ej: 31 Diciembre)
- ✅ Temporal/Estacional (ej: Todo Abril cada 4h)
- ✅ Manual (desde UI)

### 2. Algoritmos Predefinidos (Estilo Cutignola)

**Algoritmos Configurados:**
- ✅ `facturas-rg830` - Facturas RG 830
- ✅ `sueldos-digitales` - Sueldos Digitales
- ✅ `resumenes-bancarios` - Resúmenes Bancarios
- ✅ `estados-contables` - Estados Contables

### 3. Google Drive Picker Integrado

**Características:**
- ✅ Eliminación de IDs manuales
- ✅ Navegación visual en Google Drive
- ✅ Captura automática de folder IDs

### 4. Magic Selection de Etiquetas

**Formato de Nombres:**
- Soporta placeholders: `{date}`, `{type}`, `{issuer}`, `{entity}`, `{concept}`, `{ext}`
- Formato sugerido: `FECHA_TIPO_EMISOR_DETALLE`
- Case-insensitive con aliases

---

## 🔥 HOTFIX V3.1.2: Estabilidad y Validación

### Problemas Detectados:

1. **Error 422 (Unprocessable Entity):**
   - El backend esperaba un parámetro `job_id` en la URL que el frontend no enviaba
   - **Solución:** Remover parámetro fantasma de la firma de `submit_manual_job`

2. **Error `google is not defined`:**
   - La librería de Google (GIS) se carga asíncronamente
   - **Solución:** Guardrails con `typeof google !== 'undefined'` y reintentos (hasta 5)

3. **Validación de Folder ID:**
   - El regex era demasiado estricto (20-50 caracteres)
   - **Solución:** Cambiar a `^[a-zA-Z0-9_-]+$` (sin límite de longitud)

4. **Visualización de Errores:**
   - Mensaje `[object Object]` en pantalla
   - **Solución:** Mejorar captura de errores para extraer mensaje legible

### Archivos Modificados:

**Backend (`services/api-server/src/main.py`):**
- Remover parámetro `job_id: str` de `submit_manual_job`
- Relajar validación de `folder_id` a `^[a-zA-Z0-9_-]+$`
- Corregir orden de definición de `execution_log`

**Frontend (`services/frontend/src/app/app.component.ts`):**
- Guardrails para GIS con chequeos y reintentos
- Mejorar captura de errores en `submitJob`

---

## 📊 FLUJO COMPLETO END-TO-END

### Modo Manual (Usuario desde UI):

```
1. Usuario → Google Sign-In
   ↓
2. Frontend → API Server
   POST /api/v1/jobs/manual
   Headers: Authorization: Bearer <oauth_token>
   Body: {folder_id, job_type}
   ↓
3. API Server:
   ✓ Verifica OAuth token
   ✓ Verifica dominio (@estudioanc.com.ar)
   ✓ Verifica rate limit
   ✓ Crea tarea en Cloud Tasks
   ↓
4. Cloud Tasks → Worker
   POST /run-task
   Body: {job_id, folder_id, trigger_type: "manual"}
   ↓
5. Worker:
   ✓ Carga job config desde DB
   ✓ Crea agente Agno
   ✓ Procesa archivos (OCR si es necesario)
   ✓ Analiza con IA
   ✓ Renombra archivos
   ↓
6. Usuario recibe: {status: "accepted", task_id: "..."}
```

### Modo Automático (Scheduled):

```
1. Cloud Scheduler (cron: "0 8 * * *")
   ↓
2. Cloud Scheduler → API Server
   POST /api/v1/jobs/scheduled
   ↓
3. API Server:
   ✓ Verifica OIDC token
   ✓ Carga jobs activos desde DB
   ✓ Crea tarea por cada job
   ↓
4. Worker procesa cada job independientemente
```

---

## 📚 LECCIONES APRENDIDAS (Directivas Algorítmicas)

### 1. Contexto de Compilación Docker en Monorepos

**Regla:** SIEMPRE ejecutar el comando de build desde la **raíz (root)** del repositorio

**Razón:** Si se ejecuta dentro de la subcarpeta, Docker no puede "ver" carpetas hermanas o superiores, resultando en errores de `COPY`.

### 2. Validación de Esquemas Gemini/Vertex AI

**Regla:** PROHIBIDO incluir `json_schema_extra` o `examples` en el `ConfigDict` de modelos Pydantic

**Razón:** La API de Vertex/Gemini rechaza esquemas con metadatos adicionales no estándar.

### 3. Robustez en Generación de Nombres

**Regla:** SIEMPRE usar un `defaultdict` o mapeador **case-insensitive** con valores por defecto

**Razón:** Las IAs pueden omitir campos o cambiar el casing. El sistema debe ser resiliente.

---

## 🚨 ERRORES COMUNES Y SOLUCIONES

### Error: `service_account_email must be set`

**Causa:** Cloud Tasks no tiene configurada la cuenta de servicio

**Solución:**
```bash
gcloud tasks queues update [QUEUE_NAME] \
  --project=cloud-functions-474716 \
  --location=us-central1 \
  --service-account-email=[SERVICE_ACCOUNT_EMAIL]
```

### Error: `google is not defined`

**Causa:** Google Identity Services se carga asíncronamente

**Solución:** Implementar guardrails con reintentos:
```typescript
if (typeof google === 'undefined') {
  // Retry logic
}
```

### Error: `KeyError: 'issuer'`

**Causa:** La IA no devolvió el campo esperado

**Solución:** Usar `CaseInsensitiveDict` con valores por defecto

---

## 📋 ESTADO DEL PROYECTO

| Componente | Estado | % |
|------------|--------|-----|
| **Core Package** | ✅ | 100% |
| **API Server** | ✅ | 100% |
| **Worker** | ✅ | 100% |
| **Frontend** | ✅ | 100% |
| **OAuth Security** | ✅ | 100% |
| **Multi-Job System** | ✅ | 100% |
| **OCR Support** | ✅ | 100% |
| **Database (Dual Mode)** | ✅ | 100% |
| **AgentFactory** | ✅ | 100% |
| **Documentación** | ✅ | 100% |
| **Tests** | ⏳ | 0% |
| **CI/CD** | ⏳ | 0% |

**Estado General:** ✅ **BACKEND 100% COMPLETO Y ESTABLE**

---

## 🎯 PRÓXIMOS PASOS (Prioridades)

### Alta Prioridad:
1. ✅ **Deploy V3.1.2** - COMPLETADO
2. ✅ **Verificación final** - COMPLETADO

### Media Prioridad:
3. ⏳ **Tests automatizados** con pytest
4. ⏳ **CI/CD pipeline** con GitHub Actions

### Baja Prioridad:
5. ⏳ **Scripts de deployment** automatizados
6. ⏳ **Monitoring dashboards**

---

## 🔗 DOCUMENTACIÓN RELACIONADA

### Guías Principales:
- `README.md` - Descripción general
- `SISTEMA_COMPLETO.md` - Arquitectura completa
- `GEMINI.md` - Contexto para Gemini CLI
- `DEPLOYMENT_GUIDE.md` - Guía de despliegue

### Memory Bank:
- `.memorybank/productContext.md` - Visión del producto
- `.memorybank/activeContext.md` - Contexto actual
- `.memorybank/progress.md` - Estado del progreso
- `.memorybank/decisionLog.md` - Registro de decisiones
- `.memorybank/systemPatterns.md` - Patrones del sistema

### Lecciones Aprendidas:
- `.lessons/lesson_20260105_full_stabilization.md` - Estabilización V2.0.0
- `.lessons/lesson_20260129_cloud_build_deployment.md` - Deployment Cloud Build

### Estándares:
- `.standards_cenf/CODING_STANDARDS_V2.md` - Estándares de código
- `.standards_cenf/AGENT_ARCHITECTURE_METHODOLOGY.md` - Metodología de agentes

---

## 🎨 UX Contable Implementada (V3.1)

### Nomenclatura No Técnica:
- "Job" → "Algoritmo de Estudio"
- "Trigger" → "Frecuencia"
- "Folder ID" → Selección visual con Google Drive Picker

### Magic Selection:
- Etiquetas disponibles: `{date}`, `{type}`, `{issuer}`, `{entity}`, `{concept}`, `{ext}`
- Formato sugerido: `FECHA_TIPO_EMISOR_DETALLE`

---

## 📊 AUDITORÍA CAJA NEGRA

### Lifecycle Completo de Logs:

1. **SUBMITTED** - Cuando el usuario inicia la tarea
2. **IN_PROGRESS** - Cuando el worker toma la tarea
3. **COMPLETED** / **FAILED** - Resultado final

### Persistencia Robusta:
- JSON local (desarrollo)
- Google Cloud Storage (Cloud Run)
- Supabase PostgreSQL (producción)

---

## 🚀 COMANDOS ÚTILES

### Deployment:
```bash
# Deploy Worker
gcloud builds submit --config services/worker-renombrador/cloudbuild.yaml \
  --substitutions=_IMAGE_NAME=gcr.io/cloud-functions-474716/renombradorarchivosgdrive-worker-v2 . \
  --project=cloud-functions-474716

# Deploy API Server
python deployment/deploy_runner.py
```

### Verificación:
```bash
# Ver logs
gcloud logs tail /projects/cloud-functions-474716/logs/renombradorarchivosgdrive-api-server-v2

# Ver servicios
gcloud run services list --project=cloud-functions-474716
```

---

## 🎓 ANTI-GRAVITY INSIGHTS

**"La robustez de un sistema de IA no está en la precisión del prompt, sino en la elasticidad del código que recibe su salida."**

Fallar con elegancia (mapeo de alias, casing-insensitivity) ahorró más tiempo que re-intentar prompts.

---

**Estado Final:** ✅ **VERSIÓN 3.1.2 "ESTUDIO INTELIGENTE" DESPLEGADA Y ESTABLE**

**Fecha de última actualización:** 2026-03-12

**Próxima revisión:** Según necesidad del cliente

---

*Este documento es un contexto acumulativo que sintetiza toda la información relevante del proyecto para facilitar la continuidad del trabajo en futuras sesiones.*
