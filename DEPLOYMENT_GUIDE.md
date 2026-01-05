# 🚀 Guía de Deployment a Google Cloud Run

## 📋 Pre-requisitos

Antes de empezar, asegúrate de tener:
- [ ] Cuenta de Google Cloud con billing habilitado
- [ ] `gcloud` CLI instalado y configurado
- [ ] Proyecto de GCP creado
- [ ] Docker instalado (para build local, opcional)

---

## 🔧 PASO 1: Configuración Inicial

### **1.1 Configurar gcloud**

```bash
# Login
gcloud auth login

# Configurar proyecto
gcloud config set project YOUR_PROJECT_ID

# Habilitar APIs necesarias
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  cloudtasks.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  vision.googleapis.com \
  drive.googleapis.com

# Verificar que se habilitaron
gcloud services list --enabled
```

**⏱️ Tiempo:** ~3 minutos

---

### **1.2 Crear Secrets en Secret Manager**

```bash
# OAuth Client ID
echo -n "YOUR_OAUTH_CLIENT_ID.apps.googleusercontent.com" | \
  gcloud secrets create oauth-client-id --data-file=-

# Gemini API Key
echo -n "YOUR_GEMINI_API_KEY" | \
  gcloud secrets create gemini-api-key --data-file=-

# Supabase URL (si usas Supabase)
echo -n "https://xxx.supabase.co" | \
  gcloud secrets create supabase-url --data-file=-

# Supabase Key
echo -n "YOUR_SUPABASE_ANON_KEY" | \
  gcloud secrets create supabase-key --data-file=-

# Verificar
gcloud secrets list
```

**⏱️ Tiempo:** ~2 minutos

---

### **1.3 Crear Service Accounts**

```bash
# Service Account para Worker
gcloud iam service-accounts create worker-renombrador \
  --display-name="Worker Renombrador Service Account"

# Service Account para API Server
gcloud iam service-accounts create api-server \
  --display-name="API Server Service Account"

# Service Account para Cloud Scheduler
gcloud iam service-accounts create scheduler-trigger \
  --display-name="Cloud Scheduler Trigger"

# Dar permisos al Worker para acceder a Drive y Vision
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:worker-renombrador@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/drive.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:worker-renombrador@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudvision.user"

# Dar permisos al API Server para crear tareas
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:api-server@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudtasks.enqueuer"

# Dar permisos a Scheduler para invocar API Server
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:scheduler-trigger@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

**⏱️ Tiempo:** ~2 minutos

---

## 📦 PASO 2: Build y Deploy del Core Package

### **2.1 Preparar Core Package**

```bash
cd packages/core-renombrador

# Verificar que pyproject.toml está correcto
cat pyproject.toml

# Build del package (opcional, para testing local)
pip install -e .
```

**Nota:** El core package se instalará automáticamente en los Dockerfiles.

---

## 🏗️ PASO 3: Deploy Worker

### **3.1 Build Worker Image**

```bash
# Desde el ROOT del proyecto
cd /path/to/renameDriverFolders

# Build usando Cloud Build (recomendado)
gcloud builds submit \
  --tag gcr.io/YOUR_PROJECT_ID/worker-renombrador:latest \
  --timeout=20m \
  services/worker-renombrador

# O build local (alternativa)
# docker build -f services/worker-renombrador/Dockerfile -t gcr.io/YOUR_PROJECT_ID/worker-renombrador:latest .
# docker push gcr.io/YOUR_PROJECT_ID/worker-renombrador:latest
```

**⏱️ Tiempo:** ~5-10 minutos

---

### **3.2 Deploy Worker a Cloud Run**

```bash
gcloud run deploy worker-renombrador \
  --image gcr.io/YOUR_PROJECT_ID/worker-renombrador:latest \
  --platform managed \
  --region us-central1 \
  --service-account worker-renombrador@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars \
    USE_SUPABASE=true,\
    ENABLE_OCR=true \
  --set-secrets \
    GEMINI_API_KEY=gemini-api-key:latest,\
    SUPABASE_URL=supabase-url:latest,\
    SUPABASE_KEY=supabase-key:latest \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900s \
  --max-instances 10 \
  --no-allow-unauthenticated
```

**Importante:** `--no-allow-unauthenticated` porque solo Cloud Tasks puede invocar el worker.

**⏱️ Tiempo:** ~3 minutos

---

### **3.3 Obtener Worker URL**

```bash
# Guardar la URL del worker
WORKER_URL=$(gcloud run services describe worker-renombrador \
  --region us-central1 \
  --format 'value(status.url)')

echo "Worker URL: $WORKER_URL"
# Ejemplo: https://worker-renombrador-xxx-uc.a.run.app
```

---

## 🌐 PASO 4: Deploy API Server

### **4.1 Build API Server Image**

```bash
# Desde el ROOT del proyecto
gcloud builds submit \
  --tag gcr.io/YOUR_PROJECT_ID/api-server:latest \
  --timeout=20m \
  services/api-server
```

**⏱️ Tiempo:** ~5-10 minutos

---

### **4.2 Deploy API Server a Cloud Run**

```bash
gcloud run deploy api-server \
  --image gcr.io/YOUR_PROJECT_ID/api-server:latest \
  --platform managed \
  --region us-central1 \
  --service-account api-server@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars \
    GCP_PROJECT=YOUR_PROJECT_ID,\
    GCP_LOCATION=us-central1,\
    TASKS_QUEUE=document-processing-queue,\
    WORKER_URL=$WORKER_URL,\
    WORKER_SERVICE_ACCOUNT=worker-renombrador@YOUR_PROJECT_ID.iam.gserviceaccount.com,\
    USE_SUPABASE=true \
  --set-secrets \
    RENOMBRADOR_OAUTH_CLIENT_ID=oauth-client-id:latest,\
    SUPABASE_URL=supabase-url:latest,\
    SUPABASE_KEY=supabase-key:latest \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60s \
  --max-instances 10 \
  --allow-unauthenticated
```

**Importante:** `--allow-unauthenticated` porque OAuth se maneja en el código.

**⏱️ Tiempo:** ~3 minutos

---

### **4.3 Obtener API Server URL**

```bash
# Guardar la URL del API server
API_URL=$(gcloud run services describe api-server \
  --region us-central1 \
  --format 'value(status.url)')

echo "API Server URL: $API_URL"
# Ejemplo: https://api-server-xxx-uc.a.run.app
```

---

## 📋 PASO 5: Configurar Cloud Tasks

### **5.1 Crear Queue**

```bash
gcloud tasks queues create document-processing-queue \
  --location=us-central1 \
  --max-concurrent-dispatches=10 \
  --max-dispatches-per-second=5 \
  --max-attempts=3 \
  --min-backoff=60s \
  --max-backoff=3600s

# Verificar
gcloud tasks queues describe document-processing-queue --location=us-central1
```

**⏱️ Tiempo:** ~1 minuto

---

### **5.2 Dar Permisos a Cloud Tasks para invocar Worker**

```bash
gcloud run services add-iam-policy-binding worker-renombrador \
  --region=us-central1 \
  --member=serviceAccount:api-server@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/run.invoker
```

---

## ⏰ PASO 6: Configurar Cloud Scheduler

### **6.1 Crear Job para Procesamiento Diario**

```bash
gcloud scheduler jobs create http daily-processing \
  --schedule="0 8 * * *" \
  --time-zone="America/Argentina/Buenos_Aires" \
  --uri="$API_URL/api/v1/jobs/scheduled" \
  --http-method=POST \
  --oidc-service-account-email=scheduler-trigger@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --oidc-token-audience=$API_URL \
  --location=us-central1 \
  --description="Trigger daily document processing"

# Verificar
gcloud scheduler jobs describe daily-processing --location=us-central1
```

**⏱️ Tiempo:** ~1 minuto

---

### **6.2 Crear Jobs Adicionales (Opcional)**

```bash
# Procesamiento Semanal (Lunes 9am)
gcloud scheduler jobs create http weekly-processing \
  --schedule="0 9 * * 1" \
  --time-zone="America/Argentina/Buenos_Aires" \
  --uri="$API_URL/api/v1/jobs/scheduled" \
  --http-method=POST \
  --oidc-service-account-email=scheduler-trigger@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --oidc-token-audience=$API_URL \
  --location=us-central1

# Procesamiento Mensual (Día 1, 10am)
gcloud scheduler jobs create http monthly-processing \
  --schedule="0 10 1 * *" \
  --time-zone="America/Argentina/Buenos_Aires" \
  --uri="$API_URL/api/v1/jobs/scheduled" \
  --http-method=POST \
  --oidc-service-account-email=scheduler-trigger@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --oidc-token-audience=$API_URL \
  --location=us-central1
```

---

## 🗄️ PASO 7: Configurar Base de Datos (Supabase)

### **7.1 Crear Tablas en Supabase**

Ve a tu proyecto de Supabase y ejecuta este SQL:

```sql
-- Tabla de configuración
CREATE TABLE app_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key TEXT NOT NULL UNIQUE,
  value JSONB NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de jobs
CREATE TABLE jobs (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  active BOOLEAN DEFAULT true,
  trigger_type TEXT NOT NULL,
  schedule TEXT,
  source_folder_id TEXT NOT NULL,
  target_folder_names JSONB NOT NULL,
  agent_config JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_jobs_active ON jobs(active);
CREATE INDEX idx_jobs_trigger_type ON jobs(trigger_type);

-- Insertar job de ejemplo
INSERT INTO jobs (id, name, description, active, trigger_type, schedule, source_folder_id, target_folder_names, agent_config)
VALUES (
  'job-daily-test',
  'Test Job - Diario',
  'Job de prueba para desarrollo',
  true,
  'scheduled',
  '0 8 * * *',
  'YOUR_FOLDER_ID_HERE',
  '["*"]'::jsonb,
  '{
    "model": {
      "name": "gemini-2.0-flash-exp",
      "temperature": 0.7,
      "max_tokens": 4096
    },
    "instructions": "Analiza el documento y extrae la fecha y palabras clave principales.",
    "output_schema": {
      "date": "str",
      "keywords": "list"
    },
    "prompt_template": "Analiza este documento: ''{original_filename}''. Contenido: {file_content}. Extrae la fecha (formato YYYY-MM-DD) y máximo 3 palabras clave relevantes.",
    "filename_format": "DOCPROCESADO_{date}_{keywords}.{ext}"
  }'::jsonb
);
```

**⏱️ Tiempo:** ~2 minutos

---

## ✅ PASO 8: Verificación y Testing

### **8.1 Health Checks**

```bash
# API Server
curl $API_URL/health

# Worker (requiere auth, pero podemos ver si responde)
# curl $WORKER_URL/health  # Dará 403 (esperado)
```

---

### **8.2 Test Manual Job (con OAuth)**

```bash
# Primero necesitas un OAuth token real
# Opción 1: Usar Google OAuth Playground
# Opción 2: Implementar frontend con Google Sign-In

# Con token:
TOKEN="eyJhbGciOiJSUzI1NiIs..."

curl -X POST $API_URL/api/v1/jobs/manual \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_id": "YOUR_FOLDER_ID",
    "job_type": "generic"
  }'
```

---

### **8.3 Test Scheduled Job (Manual Trigger)**

```bash
# Trigger manualmente el scheduler job
gcloud scheduler jobs run daily-processing --location=us-central1

# Ver logs del API Server
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=api-server" \
  --limit 20 \
  --format json

# Ver logs del Worker
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=worker-renombrador" \
  --limit 20 \
  --format json
```

---

## 📊 PASO 9: Monitoring

### **9.1 Ver Métricas en Console**

```bash
# Abrir Cloud Run console
echo "https://console.cloud.google.com/run?project=YOUR_PROJECT_ID"

# Abrir Cloud Tasks console
echo "https://console.cloud.google.com/cloudtasks?project=YOUR_PROJECT_ID"

# Abrir Cloud Scheduler console
echo "https://console.cloud.google.com/cloudscheduler?project=YOUR_PROJECT_ID"
```

---

### **9.2 Configurar Alertas (Opcional)**

```bash
# Alerta si error rate > 5%
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="High Error Rate - API Server" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s
```

---

## 🎯 RESUMEN DE URLs

Al final del deployment, tendrás:

```bash
echo "=== DEPLOYMENT COMPLETO ==="
echo "API Server: $API_URL"
echo "Worker: $WORKER_URL"
echo ""
echo "=== ENDPOINTS PÚBLICOS ==="
echo "Health: $API_URL/health"
echo "Manual Jobs: $API_URL/api/v1/jobs/manual"
echo "List Jobs: $API_URL/api/v1/jobs"
echo ""
echo "=== CONFIGURACIÓN ==="
echo "Project: YOUR_PROJECT_ID"
echo "Region: us-central1"
echo "Queue: document-processing-queue"
```

---

## ✅ CHECKLIST FINAL

- [ ] APIs habilitadas
- [ ] Secrets creados
- [ ] Service Accounts creados y con permisos
- [ ] Worker deployed
- [ ] API Server deployed
- [ ] Cloud Tasks queue creada
- [ ] Cloud Scheduler job(s) creado(s)
- [ ] Supabase tablas creadas
- [ ] Job de ejemplo insertado
- [ ] Health checks OK
- [ ] Test manual job (con OAuth)
- [ ] Test scheduled job

---

## 🔧 TROUBLESHOOTING

### **Error: "Permission denied"**
```bash
# Verificar service account tiene permisos
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:worker-renombrador@*"
```

### **Error: "Secret not found"**
```bash
# Listar secrets
gcloud secrets list

# Ver versiones de un secret
gcloud secrets versions list oauth-client-id
```

### **Error: "Cloud Run service not found"**
```bash
# Listar servicios
gcloud run services list --region=us-central1
```

---

## 📝 NOTAS IMPORTANTES

1. **Costos:**
   - Cloud Run: Pay-per-use (primeros 2M requests gratis/mes)
   - Cloud Vision: 1,000 unidades gratis/mes
   - Cloud Tasks: Primeros 1M ops gratis/mes
   - Cloud Scheduler: $0.10/job/mes

2. **Seguridad:**
   - Worker es privado (no-allow-unauthenticated)
   - API Server usa OAuth para usuarios
   - Scheduler usa OIDC
   - Secrets en Secret Manager

3. **Escalabilidad:**
   - Auto-scaling configurado
   - Max 10 instancias por servicio
   - Queue con rate limiting

---

**¡Deployment completo!** 🎉

**Tiempo total estimado:** ~30-40 minutos
