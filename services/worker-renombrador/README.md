# Worker Renombrador - Guía de Uso v2.0

## 🎯 Qué Cambió

El worker ahora soporta **multi-job processing**:
- ✅ Carga jobs desde base de datos (JSON local o Supabase)
- ✅ Cada job tiene su propia configuración de agente
- ✅ Soporta triggers automáticos (scheduled) y manuales
- ✅ OCR integrado para imágenes y PDFs escaneados
- ✅ AgentFactory crea agentes Agno dinámicamente

---

## 🚀 Setup Local

### **1. Preparar Datos de Jobs**

El worker lee jobs desde `data/jobs.json` (modo local).

```bash
cd services/worker-renombrador
cat data/jobs.json
```

Edita el archivo y reemplaza `REPLACE_WITH_YOUR_FOLDER_ID` con un ID real de Google Drive.

### **2. Configurar Variables de Entorno**

Crea `.env` en la carpeta del worker:

```bash
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GCP_PROJECT_ID=your-project-id

# Gemini API
GEMINI_API_KEY=your-gemini-key

# Database mode
USE_SUPABASE=false  # true para Supabase, false para JSON local

# OCR
ENABLE_OCR=true

# Supabase (si USE_SUPABASE=true)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
```

### **3. Instalar Core Package**

El worker depende de `core-renombrador`:

```bash
# Desde el root del proyecto
cd packages/core-renombrador
pip install -e .

# Volver al worker
cd ../../services/worker-renombrador
pip install -r requirements.txt
```

### **4. Ejecutar Localmente**

```bash
python src/main.py
```

El servidor arrancará en `http://localhost:8080`

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
  "service": "worker-renombrador",
  "version": "2.0.0"
}
```

---

### **2. Run Task (Triggered by Cloud Tasks)**
```bash
curl -X POST http://localhost:8080/run-task \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "job-daily-test",
    "folder_id": "1AbCdEf...",
    "trigger_type": "manual"
  }'
```

**Payload Opciones:**
- `job_id`: (opcional) ID del job a ejecutar. Si no se provee, ejecuta todos los jobs activos scheduled.
- `folder_id`: (opcional) Override del folder_id (para jobs manuales).
- `trigger_type`: `"scheduled"` o `"manual"`

**Respuesta Exitosa:**
```json
{
  "status": "success",
  "job_id": "job-daily-test",
  "job_name": "Test Job - Diario",
  "stats": {
    "files_processed": 5,
    "files_renamed": 4,
    "errors": 0
  }
}
```

---

### **3. Run Job (Manual Trigger)**
```bash
curl -X POST http://localhost:8080/run-job \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "job-daily-test",
    "folder_id": "1AbCdEf..."
  }'
```

Útil para testing o triggers manuales.

---

## 🔄 Flujo de Procesamiento

```
1. Cloud Scheduler → Cloud Tasks → Worker (/run-task)
   ↓
2. Worker lee jobs desde DB (JSON o Supabase)
   ↓
3. Para cada job activo:
   a. Carga configuración del job
   b. Crea agente Agno con AgentFactory
   c. Encuentra carpeta(s) objetivo en Drive
   d. Lista archivos en carpeta
   e. Para cada archivo:
      - Descarga contenido
      - Extrae texto (con OCR si es necesario)
      - Analiza con agente (prompt personalizado)
      - Construye nuevo nombre desde análisis
      - Renombra archivo en Drive
   ↓
4. Retorna stats (archivos procesados, renombrados, errores)
```

---

## 📊 Estructura de Jobs

Un job en la base de datos tiene esta estructura:

```json
{
  "id": "unique-job-id",
  "name": "Nombre Descriptivo",
  "description": "Qué hace este job",
  "active": true,
  "trigger_type": "scheduled",  // o "manual"
  "schedule": "0 8 * * *",      // cron expression
  "source_folder_id": "1AbCdEf...",
  "target_folder_names": ["subcarpeta1", "subcarpeta2"],  // o ["*"] para toda la carpeta
  "agent_config": {
    "model": {
      "name": "gemini-2.0-flash-exp",
      "temperature": 0.7,
      "max_tokens": 4096
    },
    "instructions": "Instrucciones para el agente...",
    "output_schema": {
      "fecha": "str",
      "keywords": "list"
    },
    "prompt_template": "Template del prompt con {placeholders}",
    "filename_format": "PREFIX_{date}_{keywords}.{ext}"
  }
}
```

---

## 🧪 Testing

### **Test Manual con Curl**
```bash
# 1. Verificar health
curl http://localhost:8080/health

# 2. Ejecutar job de test
curl -X POST http://localhost:8080/run-job \
  -H "Content-Type: application/json" \
  -d '{"job_id": "job-daily-test"}'

# 3. Ver logs
# Los logs aparecerán en la terminal donde ejecutaste el worker
```

### **Test con Python**
```python
import requests

response = requests.post(
    "http://localhost:8080/run-job",
    json={"job_id": "job-daily-test"}
)

print(response.json())
```

---

## 🐳 Deployment

El worker se despliega como contenedor Docker en Cloud Run.

### **Build Image**
```bash
# Desde el root del proyecto
docker build -f services/worker-renombrador/Dockerfile -t worker-renombrador .

# Test localmente
docker run -p 8080:8080 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/creds.json \
  -e GEMINI_API_KEY=your-key \
  -v /path/to/creds.json:/app/creds.json \
  worker-renombrador
```

### **Deploy to Cloud Run**
```bash
# Tag para GCR
docker tag worker-renombrador gcr.io/PROJECT_ID/worker-renombrador:latest

# Push
docker push gcr.io/PROJECT_ID/worker-renombrador:latest

# Deploy
gcloud run deploy worker-renombrador \
  --image gcr.io/PROJECT_ID/worker-renombrador:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars GEMINI_API_KEY=your-key,USE_SUPABASE=true,ENABLE_OCR=true \
  --set-secrets SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest \
  --memory 2Gi \
  --timeout 900s \
  --no-allow-unauthenticated
```

---

## 🔍 Troubleshooting

### **Error: "Job 'xxx' not found"**
- Verificar que el job existe en `data/jobs.json` o Supabase
- Verificar que `active: true`

### **Error: "No folder_id provided"**
- Para jobs manuales, debes proveer `folder_id` en el request
- Para jobs scheduled, debe estar en la config del job

### **Error: "ContentExtractor failed"**
- Verificar que `ENABLE_OCR=true` si procesas imágenes/PDFs escaneados
- Verificar credenciales de Google Cloud (Vision API habilitado)

### **Error: "Agent creation failed"**
- Verificar `GEMINI_API_KEY` configurado
- Verificar estructura de `agent_config` en el job

### **OCR muy lento**
- Normal: OCR puede tardar 2-5 segundos por imagen
- Considerar aumentar timeout en Cloud Run (`--timeout 900s`)
- Monitorear uso de memoria (`--memory 2Gi`)

---

## 📈 Monitoring

### **Ver Logs en Cloud Run**
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=worker-renombrador" \
  --limit 50 \
  --format json
```

### **Métricas Clave**
- Request count (cuántos jobs se ejecutan)
- Request latency (tiempo de procesamiento)
- Error rate (tasa de errores)
- Memory usage (especialmente con OCR)

---

## ✅ Checklist Pre-Producción

- [ ] Jobs configurados en Supabase
- [ ] Secrets configurados en Secret Manager
- [ ] Vision API habilitada
- [ ] Worker desplegado en Cloud Run
- [ ] Cloud Scheduler configurado
- [ ] Cloud Tasks queue creada
- [ ] Monitoring configurado
- [ ] Test manual exitoso
- [ ] Test automático scheduled exitoso

---

**¡Worker v2.0 listo para multi-job processing!** 🚀
