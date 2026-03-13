# 🔍 INVESTIGACIÓN: Error 400 Persistente en Cloud Tasks
## Proyecto Renombrador (#amBotHsOS) - V3.1.2

---

## 📋 RESUMEN

**Fecha:** 13 de Marzo, 2026
**Investigador:** Claude (AI Assistant)
**Estado:** 🟡 EN PROGRESO - Error 400 persiste

---

## 🎯 PROBLEMA

Diego (@gmail.com) y Gonzalo (@gmail.com) obtienen error al ejecutar jobs:

```
POST https://renombradorarchivosgdrive-api-server-v2-702567224563.us-central1.run.app/api/v1/jobs/manual
500 Internal Server Error

Error en frontend:
{detail: 'Failed to create task: 400 Request contains an invalid argument.'}
```

**Nota:** El error es un **HTTP 400** de Cloud Tasks API, no del API Server.

---

## ✅ INVESTIGACIÓN REALIZADA

### 1. Código de create_cloud_task() ✅

**Archivo:** `services/api-server/src/main.py` (líneas 345-408)

**Código actual:**
```python
def create_cloud_task(payload: dict) -> str:
    if not tasks_client:
        raise HTTPException(status_code=500, detail="Cloud Tasks client not initialized")

    if not all([GCP_PROJECT, GCP_LOCATION, TASKS_QUEUE, WORKER_URL]):
        raise HTTPException(status_code=500, detail="Cloud Tasks configuration incomplete")

    # Build task
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{WORKER_URL}/run-task",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(payload).encode(),
        }
    }

    # Add OIDC token for authentication
    worker_sa = os.environ.get("WORKER_SERVICE_ACCOUNT")
    if not worker_sa:
        import google.auth
        try:
            credentials, project = google.auth.default()
            worker_sa = getattr(credentials, 'service_account_email', None)
            if not worker_sa:
                worker_sa = f"{GCP_PROJECT}@appspot.gserviceaccount.com"
        except Exception as e:
            logger.warning(f"Could not auto-discover SA: {e}. Using App Engine default.")
            worker_sa = f"{GCP_PROJECT}@appspot.gserviceaccount.com"

    task["http_request"]["oidc_token"] = {
        "service_account_email": worker_sa,
        "audience": WORKER_URL
    }

    # Create task
    parent = tasks_client.queue_path(GCP_PROJECT, GCP_LOCATION, TASKS_QUEUE)
    response = tasks_client.create_task(request={"parent": parent, "task": task})

    task_id = response.name.split("/")[-1]
    logger.info(f"Task created: {task_id} for worker {WORKER_URL}")

    return task_id
```

**Análisis:** Código parece correcto según la documentación de Cloud Tasks v2.

---

### 2. Variables de Entorno ✅

**Configuración del API Server (v2-00037-s2m):**
- ✅ GCP_PROJECT = cloud-functions-474716
- ✅ GCP_LOCATION = us-central1
- ✅ TASKS_QUEUE = document-processing-queue
- ✅ WORKER_URL = https://renombradorarchivosgdrive-worker-v2-orxs26nc4a-uc.a.run.app

**Cola de Cloud Tasks:**
- ✅ State: RUNNING
- ✅ Rate limits configurados
- ✅ Retry config activado

---

### 3. Logs de Errores ⚠️

**API Server:**
```
2026-03-13T17:21:19.105124Z	ERROR
2026-03-13T17:21:07.988506Z	ERROR
```

**Cloud Tasks Queue:**
- Sin errores reportados
- Cola está RUNNING

**Worker:**
- Sin logs recientes (no está recibiendo tareas)

---

## 🔍 POSIBLES CAUSAS DEL ERROR 400

### Causa 1: Service Account sin Permisos en Cloud Tasks

**Hipótesis:**
El service account que está usando (auto-discovered o App Engine default) no tiene permisos para crear tareas en Cloud Tasks.

**Verificación necesaria:**
```bash
# Verificar permisos de la service account
gcloud iam service-accounts get-iam-policy <SERVICE_ACCOUNT> --project=cloud-functions-474716

# Debería incluir:
# - roles/cloudtasks.enqueuer
# - roles/cloudtasks.taskCreator
```

---

### Causa 2: Formato Incorrecto del Request

**Hipótesis:**
El formato del task request podría no ser compatible con la API v2 de Cloud Tasks.

**Campos a verificar:**
- `http_method`: Debe ser `POST` (✅ correcto)
- `url`: Debe ser el endpoint del Worker (✅ correcto)
- `headers`: Content-Type (✅ correcto)
- `body`: JSON encoded (✅ correcto)
- `oidc_token`:
  - `service_account_email` (✅ correcto)
  - `audience`: Debe ser el URL del Worker (✅ correcto)

---

### Causa 3: Payload Invalido

**Hipótesis:**
El payload que se está enviando podría no cumplir con el formato esperado por el Worker.

**Payload enviado:**
```json
{
  "job_id": "job-manual-generic",
  "folder_id": "<FOLDER_ID>",
  "trigger_type": "manual",
  "submitted_by": "user@email.com",
  "execution_id": "exec-<timestamp>"
}
```

**Verificar con Worker:**
- El Worker `/run-task` endpoint espera este formato
- Todos los campos son strings válidos

---

### Causa 4: Problema con el URL del Worker

**Hipótesis:**
El WORKER_URL que está configurado podría no ser el correcto para autenticación OIDC.

**URL configurado:**
```
https://renombradorarchivosgdrive-worker-v2-orxs26nc4a-uc.a.run.app
```

**URL correcto para OIDC audience:**
Para Cloud Run, el `audience` debería ser:
- `https://renombradorarchivosgdrive-worker-v2-orxs26nc4a-uc.a.run.app` (sin `/run-task`)

---

## 📋 PRÓXIMOS PASOS DE INVESTIGACIÓN

### Paso 1: Verificar Permisos IAM de la Service Account

```bash
# Verificar permisos actuales
gcloud iam service-accounts get-iam-policy \
  cloud-functions-474716@appspot.gserviceaccount.com \
  --project=cloud-functions-474716

# Si faltan permisos, agregar:
gcloud projects add-iam-policy-binding \
  cloud-functions-474716@appspot.gserviceaccount.com \
  --role=roles/cloudtasks.taskCreator \
  --project=cloud-functions-474716

gcloud projects add-iam-policy-binding \
  cloud-functions-474716@appspot.gserviceaccount.com \
  --role=roles/cloudtasks.enqueuer \
  --project=cloud-functions-474716
```

---

### Paso 2: Verificar URL del Worker Deployado

```bash
# Obtener URL correcto del Worker
gcloud run services describe renombradorarchivosgdrive-worker-v2 \
  --project=cloud-functions-474716 \
  --region=us-central1 \
  --format="value(status.url)"

# Comparar con WORKER_URL configurado en API Server
```

---

### Paso 3: Probar Creación de Tarea Manualmente

```bash
# Usar gcloud para crear una tarea directamente
gcloud tasks create \
  document-processing-queue \
  us-central1 \
  --message-body='{"job_id":"test","folder_id":"test"}' \
  --http-uri=https://renombradorarchivosgdrive-worker-v2-orxs26nc4a-uc.a.run.app/run-task \
  --oidc-service-account-email=cloud-functions-474716@appspot.gserviceaccount.com \
  --oidc-token-audience=https://renombradorarchivosgdrive-worker-v2-orxs26nc4a-uc.a.run.app
```

---

### Paso 4: Revisar Documentación de Cloud Tasks v2 API

[Documentación de Google Cloud Tasks v2](https://cloud.google.com/tasks/docs/reference/rpc/google.cloud.tasks.v2/Queue/CreateTask)

Verificar:
- Formato correcto de `OidcToken`
- Permisos necesarios
- Headers requeridos

---

## 📊 MATRIZ DE INVESTIGACIÓN

| Causa Posible | Probabilidad | Verificación Necesaria | Acción |
|-----------------|--------------|----------------------|--------|
| Service account sin permisos en Cloud Tasks | 🟡 MEDIA | ✅ IAM | Agregar roles |
| Formato incorrecto del request | 🟢 BAJA | ❌ Código correcto | N/A |
| Payload inválido para Worker | 🟢 BAJA | ⚠️ Prueba manual | N/A |
| Worker URL incorrecto para OIDC | 🟡 MEDIA | ✅ Descripción | Verificar URL |
| Otra causa no identificada | ❓ DESCONOCIDA | ⚠️ Logs | Continuar |

---

## 🎯 SOLUCIÓN PROPUESTA (Si es IAM)

Si el problema son permisos de IAM:

**Solución 1: Usar la Service Account del API Server en lugar de auto-discover**

```python
# En lugar de auto-discover, usar explícitamente
import google.auth

credentials, project = google.auth.default.from_service_account_file(
    'path/to/key.json',
    scopes=['https://www.googleapis.com/auth/cloud-tasks']
)
worker_sa = credentials.service_account_email
```

**Solución 2: Agregar roles IAM necesarios**

```bash
# Agregar permisos a la service account del API Server
gcloud iam service-accounts add-iam-policy-binding \
  cloud-functions-474716@appspot.gserviceaccount.com \
  --role=roles/cloudtasks.taskCreator \
  --project=cloud-functions-474716
```

---

## 📝 NOTAS

1. **El fix de `audience` fue implementado pero no resolvió el problema** - El error persiste.

2. **El código actual debería funcionar según la documentación** de Cloud Tasks v2.

3. **Posiblemente es un problema de permisos IAM** que no es visible en el código.

4. **El error 400 viene de Cloud Tasks API, no del código del API Server.**

---

**Documento creado:** 13 de Marzo, 2026
**Versión:** 1.0
