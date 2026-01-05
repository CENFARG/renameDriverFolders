# API Server - Guía de Uso v2.0

## 🎯 Descripción

El API Server es el **gateway público** del sistema. Maneja:
- ✅ Requests manuales desde UI (con OAuth)
- ✅ Triggers automáticos desde Cloud Scheduler (con OIDC)
- ✅ Dispatch de jobs a Cloud Tasks → Worker

---

## 🚀 Setup Local

### **1. Instalar Dependencias**

```bash
cd services/api-server

# Instalar core package
cd ../../packages/core-renombrador
pip install -e .

# Volver al API server
cd ../../services/api-server
pip install -r requirements.txt
```

### **2. Configurar Variables de Entorno**

Crear `.env`:

```bash
# Google Cloud
GCP_PROJECT=your-project-id
GCP_LOCATION=us-central1
TASKS_QUEUE=document-processing-queue
WORKER_URL=https://worker-renombrador-xxx.run.app
WORKER_SERVICE_ACCOUNT=worker@project.iam.gserviceaccount.com

# OAuth
RENOMBRADOR_OAUTH_CLIENT_ID=123456-abc.apps.googleusercontent.com
RENOMBRADOR_OAUTH_ALLOWED_DOMAINS='["miempresa.com", "cenf.com.ar"]'
RENOMBRADOR_OAUTH_ALLOWED_EMAILS='["admin@miempresa.com"]'

# Database
USE_SUPABASE=false  # true para Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-key

# CORS
RENOMBRADOR_CORS_ALLOWED_ORIGINS='["https://tu-frontend.com", "http://localhost:3000"]'
```

### **3. Configurar config.json**

Crear `config.json`:

```json
{
  "oauth": {
    "client_id": "123456-abc.apps.googleusercontent.com",
    "allowed_domains": ["miempresa.com", "cenf.com.ar"],
    "allowed_emails": ["admin@miempresa.com"]
  },
  "cors": {
    "allowed_origins": ["https://tu-frontend.com", "http://localhost:3000"]
  }
}
```

### **4. Ejecutar Localmente**

```bash
python src/main.py
```

Servidor en `http://localhost:8080`

---

## 📡 API Endpoints

### **1. Health Check**
```bash
curl http://localhost:8080/health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "service": "api-server",
  "version": "2.0.0",
  "oauth_enabled": true,
  "tasks_enabled": true
}
```

---

### **2. Submit Manual Job** 🔒 OAuth Required

**Endpoint:** `POST /api/v1/jobs/manual`

**Headers:**
```
Authorization: Bearer <google_oauth_token>
Content-Type: application/json
```

**Body:**
```json
{
  "folder_id": "1AbCdEfGhIjKlMnOpQrStUvWxYz",
  "job_type": "invoice"
}
```

**Respuesta Exitosa (202):**
```json
{
  "status": "accepted",
  "message": "Job submitted successfully and is being processed",
  "job_id": "job-manual-invoice",
  "task_id": "12345678901234567890"
}
```

**Errores:**
- `401`: Token inválido o faltante
- `403`: Dominio no autorizado
- `429`: Rate limit excedido
- `500`: Error creando tarea

---

### **3. Trigger Scheduled Jobs** 🔒 OIDC Required

**Endpoint:** `POST /api/v1/jobs/scheduled`

**Headers:**
```
Authorization: Bearer <oidc_token_from_scheduler>
```

**Body:** Ninguno

**Respuesta Exitosa:**
```json
{
  "status": "success",
  "message": "Processed 5 scheduled jobs",
  "jobs_processed": 5,
  "tasks_created": 5,
  "results": [
    {
      "job_id": "job-daily-invoices",
      "status": "task_created",
      "task_id": "123..."
    },
    ...
  ]
}
```

---

### **4. List Jobs** 🔒 OAuth Required

**Endpoint:** `GET /api/v1/jobs`

**Headers:**
```
Authorization: Bearer <google_oauth_token>
```

**Respuesta:**
```json
{
  "status": "success",
  "jobs": [
    {
      "id": "job-daily-invoices",
      "name": "Facturas Diarias",
      "description": "Procesamiento diario de facturas",
      "active": true,
      "trigger_type": "scheduled",
      "schedule": "0 8 * * *"
    },
    ...
  ],
  "total": 5
}
```

---

## 🔐 Seguridad

### **OAuth (Manual Jobs)**
- Usuario se autentica con Google Sign-In
- Token se envía en header `Authorization: Bearer <token>`
- API verifica:
  1. Token válido (firma, expiración)
  2. Email verificado
  3. Dominio en whitelist
  4. Rate limit OK

### **OIDC (Scheduled Jobs)**
- Cloud Scheduler envía token OIDC automáticamente
- API verifica:
  1. Token válido
  2. Service account autorizado
  3. Audience correcto

### **Rate Limiting**
- Manual jobs: 10 requests/minuto por usuario
- Configurable por endpoint

---

## 🔄 Flujo de Datos

### **Manual Job Flow:**
```
1. Usuario → Frontend → Google Sign-In
   ↓
2. Frontend → API Server (/jobs/manual)
   Headers: Authorization: Bearer <oauth_token>
   Body: {folder_id, job_type}
   ↓
3. API Server:
   - Verifica OAuth token
   - Verifica dominio autorizado
   - Verifica rate limit
   - Crea tarea en Cloud Tasks
   ↓
4. Cloud Tasks → Worker (/run-task)
   ↓
5. Worker procesa archivos
   ↓
6. Frontend recibe: {status: "accepted", task_id: "..."}
```

### **Scheduled Job Flow:**
```
1. Cloud Scheduler (cron) → API Server (/jobs/scheduled)
   Headers: Authorization: Bearer <oidc_token>
   ↓
2. API Server:
   - Verifica OIDC token
   - Carga jobs activos desde DB
   - Crea tarea por cada job
   ↓
3. Cloud Tasks → Worker (múltiples tareas)
   ↓
4. Worker procesa cada job
```

---

## 🐳 Deployment

### **Build Docker Image**
```bash
# Desde el root del proyecto
docker build -f services/api-server/Dockerfile -t api-server .

# Test local
docker run -p 8080:8080 \
  -e GCP_PROJECT=your-project \
  -e WORKER_URL=http://localhost:8081 \
  -e RENOMBRADOR_OAUTH_CLIENT_ID=your-client-id \
  api-server
```

### **Deploy to Cloud Run**
```bash
# Tag
docker tag api-server gcr.io/PROJECT_ID/api-server:latest

# Push
docker push gcr.io/PROJECT_ID/api-server:latest

# Deploy
gcloud run deploy api-server \
  --image gcr.io/PROJECT_ID/api-server:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars \
    GCP_PROJECT=your-project,\
    GCP_LOCATION=us-central1,\
    TASKS_QUEUE=document-processing-queue,\
    WORKER_URL=https://worker-xxx.run.app,\
    USE_SUPABASE=true \
  --set-secrets \
    RENOMBRADOR_OAUTH_CLIENT_ID=oauth-client-id:latest,\
    SUPABASE_URL=supabase-url:latest,\
    SUPABASE_KEY=supabase-key:latest \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 60s
```

**Importante:** `--allow-unauthenticated` porque OAuth se maneja en el código.

---

## ⚙️ Configurar Cloud Scheduler

### **Crear Job para Scheduled Processing**

```bash
gcloud scheduler jobs create http scheduled-processing \
  --schedule="0 8 * * *" \
  --uri="https://api-server-xxx.run.app/api/v1/jobs/scheduled" \
  --http-method=POST \
  --oidc-service-account-email=scheduler@project.iam.gserviceaccount.com \
  --oidc-token-audience=https://api-server-xxx.run.app \
  --location=us-central1
```

**Schedule Examples:**
- `0 8 * * *` - Diario 8am
- `0 9 * * 1` - Lunes 9am
- `0 10 1 * *` - Día 1 de mes 10am

---

## ⚙️ Configurar Cloud Tasks Queue

```bash
gcloud tasks queues create document-processing-queue \
  --location=us-central1 \
  --max-concurrent-dispatches=10 \
  --max-dispatches-per-second=5
```

---

## 🧪 Testing

### **Test OAuth Endpoint**
```bash
# 1. Obtener OAuth token (usar Google OAuth Playground)
TOKEN="eyJhbGciOiJSUzI1NiIs..."

# 2. Submit manual job
curl -X POST http://localhost:8080/api/v1/jobs/manual \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_id": "1AbCdEf...",
    "job_type": "invoice"
  }'
```

### **Test Scheduled Endpoint (Local)**
```bash
# Simular OIDC token (solo para testing local)
curl -X POST http://localhost:8080/api/v1/jobs/scheduled \
  -H "Authorization: Bearer fake-token-for-local-testing"
```

**Nota:** En producción, Cloud Scheduler envía el OIDC token automáticamente.

---

## 🔍 Troubleshooting

### **Error: "OAuth not configured on server"**
- Verificar `RENOMBRADOR_OAUTH_CLIENT_ID` configurado
- Verificar `config.json` tiene sección `oauth`

### **Error: "Cloud Tasks configuration incomplete"**
- Verificar todas las env vars: `GCP_PROJECT`, `WORKER_URL`, etc.

### **Error: "Domain xxx is not authorized"**
- Agregar dominio a `allowed_domains` en config
- O agregar email específico a `allowed_emails`

### **Error: "Rate limit exceeded"**
- Usuario excedió 10 requests/minuto
- Esperar 1 minuto o aumentar límite en código

### **Error: "OIDC verification failed"**
- Verificar que Cloud Scheduler usa OIDC token
- Verificar service account correcto
- Verificar audience coincide con URL del servicio

---

## 📈 Monitoring

### **Métricas Clave**
- Request count por endpoint
- OAuth success/failure rate
- Task creation success rate
- Response latency
- Error rate

### **Logs**
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=api-server" \
  --limit 50
```

---

## ✅ Checklist Pre-Producción

- [ ] OAuth Client ID configurado
- [ ] Dominios autorizados configurados
- [ ] Worker URL configurado
- [ ] Cloud Tasks queue creada
- [ ] Cloud Scheduler job creado
- [ ] Service accounts con permisos correctos
- [ ] CORS configurado
- [ ] Secrets en Secret Manager
- [ ] Test manual job exitoso
- [ ] Test scheduled job exitoso

---

**¡API Server v2.0 listo para producción!** 🚀
