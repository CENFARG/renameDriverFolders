# 🚨 ERROR ACTUAL Y PLAN DE SOLUCIÓN
## Proyecto Renombrador (#amBotHsOS) - V3.1.2

---

## 🔴 ERROR IDENTIFICADO

### Error Principal:
```
Cloud Tasks not fully configured. Task dispatch will fail.
```

**Timestamp:** 2026-02-19 22:21:37

**Ubicación:** `services/api-server/src/main.py`

**Severidad:** CRÍTICA - El sistema no puede despachar tareas al Worker

---

## 🔍 ANÁLISIS DEL PROBLEMA

### Causa Raíz:
El servicio Cloud Tasks no tiene configurada la cuenta de servicio (`service_account_email`), lo que impide que el API Server pueda crear tareas en la cola.

### Impacto:
- ❌ Los jobs manuales desde la UI fallan
- ❌ Los jobs programados no se ejecutan
- ❌ El Worker no recibe tareas para procesar

### Síntomas:
- Error 500 al intentar enviar jobs manuales
- Logs muestran: "Error creating task: 400 service_account_email must be set."
- La UI queda en estado de carga indefinido

---

## ✅ SOLUCIÓN PROPUESTA

### Paso 1: Configurar la cuenta de servicio en Cloud Tasks

```bash
# Obtener el email de la cuenta de servicio del API Server
gcloud iam service-accounts list \
  --project=cloud-functions-474716 \
  --filter="displayName:renombradorarchivosgdrive-api-server"

# Actualizar la cola de Cloud Tasks
gcloud tasks queues update rename-queue \
  --project=cloud-functions-474716 \
  --location=us-central1 \
  --service-account-email=API_SERVER_SERVICE_ACCOUNT@cloud-functions-474716.iam.gserviceaccount.com
```

### Paso 2: Verificar la configuración

```bash
# Verificar que la cola tenga la cuenta de servicio configurada
gcloud tasks queues describe rename-queue \
  --project=cloud-functions-474716 \
  --location=us-central1
```

### Paso 3: Verificar permisos

Asegurarse de que la cuenta de servicio tenga los permisos necesarios:
- `cloudtasks.enqueuer` - Para crear tareas en la cola
- `cloudtasks.taskRunner` - Para ejecutar tareas

```bash
# Otorgar permisos si es necesario
gcloud projects add-iam-policy-binding cloud-functions-474716 \
  --member="serviceAccount:API_SERVER_SERVICE_ACCOUNT@cloud-functions-474716.iam.gserviceaccount.com" \
  --role="roles/cloudtasks.enqueuer"
```

### Paso 4: Redesplegar el API Server

```bash
python deployment/deploy_runner.py
```

---

## 🧪 PLAN DE VERIFICACIÓN

### Test 1: Verificar configuración de Cloud Tasks

```bash
# Listar colas de Cloud Tasks
gcloud tasks queues list \
  --project=cloud-functions-474716 \
  --location=us-central1
```

**Resultado esperado:**
```
QUEUE_NAME          STATE
rename-queue        RUNNING
```

### Test 2: Verificar cuenta de servicio

```bash
# Describir la cola para ver la cuenta de servicio
gcloud tasks queues describe rename-queue \
  --project=cloud-functions-474716 \
  --location=us-central1 \
  --format="value(queue.serviceAccountEmail)"
```

**Resultado esperado:**
```
API_SERVER_SERVICE_ACCOUNT@cloud-functions-474716.iam.gserviceaccount.com
```

### Test 3: Ejecutar un job manual

1. Acceder a: `https://renombradorarchivosgdrive-frontend-v2-702567224563.us-central1.run.app`
2. Iniciar sesión con Google
3. Seleccionar una carpeta de Google Drive
4. Hacer clic en "Procesar"

**Resultado esperado:**
- ✅ Estado: "accepted"
- ✅ Task ID generado
- ✅ No hay errores en consola

### Test 4: Verificar que el Worker recibe la tarea

```bash
# Ver logs del Worker
gcloud logs tail /projects/cloud-functions-474716/logs/renombradorarchivosgdrive-worker-v2
```

**Resultado esperado:**
```
INFO - Processing task: task_id
INFO - Job loaded: job_id
INFO - Processing files...
```

---

## 📋 CHECKLIST DE SOLUCIÓN

- [ ] Identificar email de la cuenta de servicio del API Server
- [ ] Configurar la cuenta de servicio en la cola de Cloud Tasks
- [ ] Verificar permisos de IAM
- [ ] Redesplegar el API Server
- [ ] Ejecutar test manual desde la UI
- [ ] Verificar logs del Worker
- [ ] Confirmar que el archivo se renombra correctamente

---

## 🔄 ALTERNATIVAS SI LA SOLUCIÓN FALLA

### Opción A: Recrear la cola de Cloud Tasks

```bash
# Eliminar la cola existente
gcloud tasks queues delete rename-queue \
  --project=cloud-functions-474716 \
  --location=us-central1

# Crear una nueva cola con la configuración correcta
gcloud tasks queues create rename-queue \
  --project=cloud-functions-474716 \
  --location=us-central1 \
  --service-account-email=API_SERVER_SERVICE_ACCOUNT@cloud-functions-474716.iam.gserviceaccount.com
```

### Opción B: Usar una cola diferente

Si la cola `rename-queue` tiene problemas persistentes, crear una nueva cola:

```bash
# Crear una nueva cola
gcloud tasks queues create rename-queue-v2 \
  --project=cloud-functions-474716 \
  --location=us-central1 \
  --service-account-email=API_SERVER_SERVICE_ACCOUNT@cloud-functions-474716.iam.gserviceaccount.com

# Actualizar la variable de entorno CLOUD_TASKS_QUEUE en el API Server
```

---

## 📊 DIAGNÓSTICO COMPLETO

### Estado Actual de los Servicios:

| Servicio | Estado | Configuración Cloud Tasks |
|----------|--------|---------------------------|
| **API Server** | ✅ Running | ❌ Sin cuenta de servicio |
| **Worker** | ✅ Running | N/A |
| **Frontend** | ✅ Running | N/A |
| **Cloud Tasks Queue** | ✅ Running | ❌ Sin cuenta de servicio |

### Variables de Entorno Requeridas:

```env
# Cloud Tasks
CLOUD_TASKS_QUEUE=rename-queue
CLOUD_TASKS_LOCATION=us-central1
CLOUD_TASKS_PROJECT=cloud-functions-474716

# Service Account (para Cloud Tasks)
SERVICE_ACCOUNT_EMAIL=API_SERVER_SERVICE_ACCOUNT@cloud-functions-474716.iam.gserviceaccount.com
```

---

## 🎯 PRÓXIMOS PASOS INMEDIATOS

1. **Ejecutar el comando para configurar la cuenta de servicio** (5 min)
2. **Verificar la configuración** (2 min)
3. **Redesplegar el API Server** (5 min)
4. **Ejecutar test manual** (5 min)
5. **Verificar logs del Worker** (2 min)

**Tiempo estimado total:** ~20 minutos

---

## 📞 SOPORTE

Si la solución no funciona, verificar:

1. **Permisos de IAM:**
   - La cuenta de servicio tiene `roles/cloudtasks.enqueuer`
   - La cuenta de servicio tiene `roles/cloudtasks.taskRunner`

2. **Configuración de la cola:**
   - La cola está en estado `RUNNING`
   - La cola tiene la cuenta de servicio configurada

3. **Variables de entorno:**
   - `CLOUD_TASKS_QUEUE` está configurada correctamente
   - `CLOUD_TASKS_LOCATION` está configurada correctamente
   - `CLOUD_TASKS_PROJECT` está configurada correctamente

---

**Estado del Error:** 🔴 **CRÍTICO - Requiere solución inmediata**

**Prioridad:** 🚨 **ALTA** - El sistema no puede procesar archivos sin esta configuración

**Tiempo estimado de solución:** 20-30 minutos

---

*Este documento será actualizado conforme se resuelva el error.*
