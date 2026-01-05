# 🚀 Guía Rápida de Despliegue - renameDriverFolders

## ⚡ Despliegue Inmediato en Producción

### Comandos Esenciales
```bash
# 1. Verificar estado actual
gcloud run services describe rename-driver-folders \
    --region us-central1 \
    --format "table(status.url,latestReadyRevision.name)"

# 2. Ejecutar aplicación en producción
curl -X POST https://rename-driver-folders-v1-07112025-702567224563.us-central1.run.app \
    -H "Content-Length: 0"

# 3. Ver logs en tiempo real
gcloud logs tail "resource.type=cloud_run_revision" \
    --filter 'resource.labels.service_name="rename-driver-folders"' \
    --project=rename-driver-folders-v1-07112025
```

## 📋 Variables de Entorno Críticas
```bash
ROOT_FOLDER_ID="1Q4by0XHi5S_4qOdZH_Fl4jBaX5flIXjn"
TARGET_FOLDER_NAMES='["doc de respaldo", "test_integrado"]'
GCP_PROJECT_ID="rename-driver-folders-v1-07112025"
GCS_BUCKET_NAME="rename-driver-folders-state"
SERVICE_ACCOUNT_KEY_B64="<BASE64_ENCODED_JSON_KEY>"
GEMINI_API_KEY="<GEMINI_API_KEY>"
```

## 🔧 Despliegue Manual (Recomendado)
```bash
# Construir imagen
gcloud builds submit \
    --tag gcr.io/rename-driver-folders-v1-07112025/rename-driver-folders \
    --project=rename-driver-folders-v1-07112025

# Desplegar
gcloud run deploy rename-driver-folders \
    --image gcr.io/rename-driver-folders-v1-07112025/rename-driver-folders \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --timeout 300s \
    --project=rename-driver-folders-v1-07112025
```

## 📊 Estado Actual
- **URL:** https://rename-driver-folders-v1-07112025-702567224563.us-central1.run.app
- **Revisión:** rename-driver-folders-v1-07112025-00018-2sr
- **Modelo:** gemini-2.0-flash-exp
- **Estado:** ✅ Activo

## 🆘 Problemas Comunes
1. **Error 401:** Verificar SERVICE_ACCOUNT_KEY_B64
2. **Error 403:** Revisar permisos de Drive API
3. **Timeout:** Aumentar memoria a 512Mi
4. **Folder not found:** Verificar ROOT_FOLDER_ID

---
**Para documentación completa, ver `DEPLOYMENT_DOCUMENTATION.md`**