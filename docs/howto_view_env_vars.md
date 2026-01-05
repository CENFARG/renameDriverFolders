# Cómo Ver las Variables de Entorno en Google Cloud Console

Para verificar que las variables `GCP_PROJECT`, `GCP_LOCATION`, `TASKS_QUEUE`, `WORKER_URL` y `WORKER_SERVICE_ACCOUNT` estén configuradas correctamente, seguí estos pasos:

## 1. Acceder al Servicio

1. Ir a **Google Cloud Console**: https://console.cloud.google.com/run?project=cloud-functions-474716
2. En la lista de servicios, hacer click en: `renombradorarchivosgdrive-api-server-v2`

## 2. Ir a la Revisión Actual

1. Una vez dentro del servicio, buscá la pestaña **REVISIONES** (o **REVISIONS**) en la parte superior.
2. Verás una lista. La que tiene el ícono de "Check verde" ✅ o dice "100%" de tráfico es la activa.
3. Click en esa revisión (ej: `renombradorarchivosgdrive-api-server-v2-00005-qn9`).

## 3. Ver Variables y Secretos

1. En los detalles de la revisión, buscá la pestaña **VARIABLES Y SECRETOS** (o **VARIABLES & SECRETS**).
2. Deberías ver una tabla con las siguientes claves y valores:

| Nombre Variable | Valor Esperado (aprox) |
|-----------------|------------------------|
| `GCP_PROJECT` | `cloud-functions-474716` |
| `GCP_LOCATION` | `us-central1` |
| `TASKS_QUEUE` | `document-processing-queue` |
| `WORKER_URL` | `https://renombrador...worker-v2...run.app` |
| `WORKER_SERVICE_ACCOUNT` | `drive-902@....iam.gserviceaccount.com` |

---

## Opción Alternativa: Pestaña YAML

1. En la página del servicio, click en la pestaña **YAML**.
2. Buscá la sección `env:` dentro del código.
3. Ahí verás la lista en formato texto:

```yaml
- name: GCP_PROJECT
  value: cloud-functions-474716
- name: WORKER_SERVICE_ACCOUNT
  value: drive-902@...
...
```

---

**Nota:** Si falta alguna, el servicio fallará al intentar crear tareas.
