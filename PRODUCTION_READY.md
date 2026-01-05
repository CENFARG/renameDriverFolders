# 🚀 SISTEMA LISTO PARA PRODUCCIÓN

## ✅ Estado Actual

**TODOS LOS SERVICIOS DESPLEGADOS Y FUNCIONANDO:**

| Servicio | Versión | Estado | URL |
|----------|---------|--------|-----|
| Frontend | v00003-ndx | ✅ ACTIVO | https://renombradorarchivosgdrive-frontend-v2-702567224563.us-central1.run.app |
| API Server | v00012-j6h | ✅ ACTIVO | https://renombradorarchivosgdrive-api-server-v2-702567224563.us-central1.run.app |
| Worker | v00006-679 | ✅ ACTIVO | https://renombradorarchivosgdrive-worker-v2-702567224563.us-central1.run.app |

**Infraestructura:**
- ✅ Cloud Tasks Queue: `renombrador-queue` (us-central1)
- ✅ GCS Bucket: `renamedriverfolderbucket`
- ✅ Job Config: `gs://renamedriverfolderbucket/data/jobs.json`

---

## 🐛 Problemas Resueltos

### 1. Worker URL Incorrecta
**Problema**: Cloud Tasks enviaba tareas a URL inexistente  
**Fix**: Actualizada variable `WORKER_URL` en API Server  
**Resultado**: Worker ahora recibe tareas correctamente

### 2. Bug en build_filename()
**Problema**: Conflicto de argumentos `**analysis` causaba  errores en 6/6 archivos  
**Fix**: Eliminado `**analysis`, creadas variables explícitas en template  
**Resultado**: Renombrado de archivos funciona correctamente

### 3. Job Config Faltante
**Problema**: GCS database vacía, Worker no encontraba configuración  
**Fix**: Subido `jobs.json` manualmente a GCS  
**Resultado**: Job `job-manual-generic` disponible

---

## 📋 Cómo Usar en Producción

### Opción 1: Interfaz Web (Recomendado)
1. Abre: https://renombradorarchivosgdrive-frontend-v2-702567224563.us-central1.run.app
2. Inicia sesión con tu cuenta de Google (debe ser `@estudioanc.com.ar` o `@gmail.com`)
3. Ingresa el ID de la carpeta de Drive (ej: `1Q4by0XHi5S_4qOdZH_Fl4jBaX5flIXjn`)
4. Presiona "Procesar"
5. Espera 30-60 segundos
6. Verifica los archivos renombrados en Drive

### Opción 2: API Directa (Para automatización)
```bash
# Obtener token
TOKEN=$(gcloud auth print-identity-token)

# Enviar job
curl -X POST \
  https://renombradorarchivosgdrive-api-server-v2-702567224563.us-central1.run.app/api/v1/jobs/manual \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_id": "1Q4by0XHi5S_4qOdZH_Fl4jBaX5flIXjn",
    "job_type": "generic"
  }'
```

---

## 📂 Formato de Nombres (Configurable)

**Formato actual:**
```
{date}_{keywords}{ext}
```

**Ejemplo:**
- Original: `Galicia Securities.pdf`
- Renombrado: `2024-12-20_galicia_securities_informe.pdf`

**Para cambiar el formato:**
1. Edita `jobs.json` (ver `docs/FILENAME_FORMATS.md` para opciones)
2. Sube a GCS: `gcloud storage cp jobs.json gs://renamedriverfolderbucket/data/jobs.json`
3. ¡Listo! El próximo job usará el nuevo formato

---

## 🧪 Cómo Probar

### Test Manual Rápido
1. Sube un archivo PDF a la carpeta Drive de prueba
2. Usa la interfaz web para procesar
3. Verifica que el archivo se renombró correctamente

### Verificar Logs
```bash
# Logs del Worker (ver si procesó archivos)
gcloud logging read "resource.labels.service_name=renombradorarchivosgdrive-worker-v2" \
  --limit 50 --freshness=10m --format="value(textPayload)" | findstr "Processed"

# Logs del API Server (ver si recibió solicitudes)
gcloud logging read "resource.labels.service_name=renombradorarchivosgdrive-api-server-v2" \
  --limit 20 --freshness=10m
```

---

## ⚠️ Troubleshooting

### Problema: "401 Unauthorized"
**Causa**: Token de Google OAuth expirado (duración: 1 hora)  
**Solución**: Cerrar sesión y volver a iniciar sesión en el Frontend

### Problema: Archivos no se renombran
**Revisar:**
1. ¿El Worker tiene permisos en esa carpeta de Drive? (debe aparecer `drive-902@cloud-functions-474716...`)
2. ¿Hay archivos procesables? (solo PDFs, Excel, Word por ahora)
3. Revisar logs del Worker para errores específicos

### Problema: "No files found"
**Causa**: La carpeta está vacía o subcarpetas no configuradas  
**Solución**: Asegurarse de que los archivos estén en la carpeta raíz (no en subcarpetas)

---

## 🔧 Mantenimiento

### Actualizar Job Config
```bash
# 1. Editar jobs.json localmente
# 2. Subir a GCS
gcloud storage cp jobs.json gs://renamedriverfolderbucket/data/jobs.json
```

### Redesplegar Servicios
```bash
# Worker (después de cambios en código)
gcloud builds submit --config services/worker-renombrador/cloudbuild.yaml .
gcloud run deploy renombradorarchivosgdrive-worker-v2 \
  --image gcr.io/cloud-functions-474716/renombradorarchivosgdrive-worker-v2:latest \
  --region us-central1 --platform managed

# API Server
gcloud builds submit --config services/api-server/cloudbuild.yaml .

# Frontend
gcloud builds submit --config services/frontend/cloudbuild.yaml .
```

---

## 📖 Documentación Adicional

- **Formatos de Nombres**: `docs/FILENAME_FORMATS.md`
- **OAuth Setup**: `docs/oauth_update_instructions.md`
- **Environment Variables**: `docs/howto_view_env_vars.md`
- **Lecciones Aprendidas**: `.lessons/lesson_20251219_cloud_run_secrets_gcs.md`

---

## 🎯 Próximos Pasos Sugeridos

1. **Probar con archivos reales de producción**
2. **Ajustar formato de nombres** si es necesario (ver `FILENAME_FORMATS.md`)
3. **Monitorear primeros jobs** para casos edge
4. **Documentar procesos internos** del cliente

---

**SISTEMA 100% OPERATIVO Y LISTO PARA USO EN PRODUCCIÓN** 🚀
