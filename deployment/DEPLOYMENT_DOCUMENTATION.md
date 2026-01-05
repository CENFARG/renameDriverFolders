# 📚 Documentación Completa de Despliegue - renameDriverFolders

## 🎯 Tabla de Contenidos

1. [Visión General del Proyecto](#visión-general)
2. [Arquitectura y Componentes](#arquitectura)
3. [Configuración del Entorno](#configuración)
4. [Despliegue Local](#despliegue-local)
5. [Despliegue en Producción (Google Cloud Run)](#despliegue-producción)
6. [Monitoreo y Mantenimiento](#monitoreo)
7. [Solución de Problemas](#solución-de-problemas)
8. [Referencia de API](#api)

---

## 🌟 Visión General del Proyecto

### Propósito
`renameDriverFolders` es un procesador automatizado de archivos para Google Drive que:
- Monitorea carpetas específicas en Google Drive
- Analiza nuevos archivos usando IA (Gemini 2.0 Flash)
- Renombra archivos con formato estandarizado
- Mantiene un archivo `index.html` para seguimiento
- Se ejecuta como servidorless en Google Cloud Run

### Estado Actual
- **✅ Producción Activa:** https://rename-driver-folders-v1-07112025-702567224563.us-central1.run.app
- **📊 Última Revisión:** rename-driver-folders-v1-07112025-00018-2sr
- **🤖 Modelo IA:** gemini-2.0-flash-exp
- **📁 Carpetas Monitoreadas:** ["doc de respaldo", "test_integrado"]

---

## 🏗️ Arquitectura y Componentes

### Estructura del Proyecto
```
renameDriverFolders/
├── core/                    # Módulos centrales reutilizables
│   ├── config_manager.py    # Gestión de configuración
│   ├── logger_manager.py    # Sistema de logging
│   ├── file_manager.py      # Operaciones de archivos
│   ├── content_extractor.py # Extracción de contenido
│   └── error_handler.py     # Manejo de errores
├── memory-bank/            # Documentación del proyecto
│   ├── activeContext.md    # Estado actual
│   ├── decisionLog.md      # Registro de decisiones
│   ├── progress.md         # Progreso del proyecto
│   └── systemPatterns.md   # Patrones de sistema
├── deployment/             # Scripts de despliegue
├── tests/                  # Pruebas unitarias y de integración
├── logs/                   # Logs de ejecución
├── main.py                 # Aplicación principal (Flask)
├── Dockerfile             # Configuración de contenedor
├── requirements.txt       # Dependencias de Python
└── config.json            # Configuración local
```

### Flujo de Procesamiento
1. **Detección:** Identifica archivos nuevos en carpetas objetivo
2. **Análisis:** Extrae contenido y lo envía a Gemini IA
3. **Renombrado:** Aplica formato estandarizado basado en análisis
4. **Indexación:** Actualiza `index.html` con metadatos
5. **Persistencia:** Guarda estado en Google Cloud Storage

---

## ⚙️ Configuración del Entorno

### Variables de Entorno Requeridas
```bash
# Google Drive Configuration
ROOT_FOLDER_ID="1Q4by0XHi5S_4qOdZH_Fl4jBaX5flIXjn"  # ID carpeta raíz
TARGET_FOLDER_NAMES='["doc de respaldo", "test_integrado"]'  # Carpetas a monitorear

# Google Cloud Platform
GCP_PROJECT_ID="rename-driver-folders-v1-07112025"
GCP_REGION="us-central1"
GCS_BUCKET_NAME="rename-driver-folders-state"

# Authentication
SERVICE_ACCOUNT_KEY_B64="<BASE64_ENCODED_JSON_KEY>"
GEMINI_API_KEY="<GEMINI_API_KEY>"

# Application
FLASK_ENV="production"
LOG_LEVEL="DEBUG"
```

### Proceso de Configuración

#### 1. Crear Cuenta de Servicio
```bash
# En Google Cloud Console
gcloud iam service-accounts create rename-driver-service \
    --display-name="Rename Driver Service" \
    --project=rename-driver-folders-v1-07112025

# Asignar roles necesarios
gcloud projects add-iam-policy-binding rename-driver-folders-v1-07112025 \
    --member="serviceAccount:rename-driver-service@rename-driver-folders-v1-07112025.iam.gserviceaccount.com" \
    --role="roles/drive.file"

gcloud projects add-iam-policy-binding rename-driver-folders-v1-07112025 \
    --member="serviceAccount:rename-driver-service@rename-driver-folders-v1-07112025.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding rename-driver-folders-v1-07112025 \
    --member="serviceAccount:rename-driver-service@rename-driver-folders-v1-07112025.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

#### 2. Generar Clave JSON
```bash
gcloud iam service-accounts keys create ~/key.json \
    --iam-account=rename-driver-service@rename-driver-folders-v1-07112025.iam.gserviceaccount.com \
    --project=rename-driver-folders-v1-07112025
```

#### 3. Codificar a Base64
```powershell
# Windows PowerShell
$keyContent = Get-Content -Raw ~/key.json
$base64Key = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($keyContent))
$base64Key | Set-Clipboard
```

#### 4. Crear Bucket de Estado
```bash
gsutil mb gs://rename-driver-folders-state \
    --project=rename-driver-folders-v1-07112025 \
    --location=us-central1
```

---

## 💻 Despliegue Local

### Prerrequisitos
- Python 3.9+
- Google Cloud SDK
- Cuenta de servicio configurada

### Pasos de Instalación

#### 1. Clonar Repositorio
```bash
git clone https://github.com/CENFARG/renameDriverFolders.git
cd renameDriverFolders
```

#### 2. Entorno Virtual
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
```

#### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

#### 4. Configurar Variables de Entorno
```bash
# Crear archivo .env
copy .env.example .env
# Editar .env con tus valores
```

#### 5. Ejecutar Localmente
```bash
python main.py
```

#### 6. Probar Funcionamiento
```bash
curl -X POST http://localhost:8080/
```

---

## 🚀 Despliegue en Producción (Google Cloud Run)

### Método 1: Despliegue Automatizado
```bash
# Usar script de despliegue
deployment\deploy.bat
```

### Método 2: Despliegue Manual (Recomendado para evitar caché)

#### Paso 1: Construir Imagen
```bash
gcloud builds submit \
    --tag gcr.io/rename-driver-folders-v1-07112025/rename-driver-folders \
    --project=rename-driver-folders-v1-07112025
```

#### Paso 2: Desplegar en Cloud Run
```bash
gcloud run deploy rename-driver-folders \
    --image gcr.io/rename-driver-folders-v1-07112025/rename-driver-folders \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300s \
    --set-env-vars="ROOT_FOLDER_ID=1Q4by0XHi5S_4qOdZH_Fl4jBaX5flIXjn" \
    --set-env-vars="TARGET_FOLDER_NAMES=[\"doc de respaldo\", \"test_integrado\"]" \
    --set-env-vars="GCP_PROJECT_ID=rename-driver-folders-v1-07112025" \
    --set-env-vars="GCP_REGION=us-central1" \
    --set-env-vars="GCS_BUCKET_NAME=rename-driver-folders-state" \
    --set-env-vars="SERVICE_ACCOUNT_KEY_B64=<BASE64_KEY>" \
    --set-env-vars="GEMINI_API_KEY=<GEMINI_KEY>" \
    --set-env-vars="LOG_LEVEL=DEBUG" \
    --project=rename-driver-folders-v1-07112025
```

### Configuración de Producción
- **Memoria:** 512Mi
- **CPU:** 1 vCPU
- **Timeout:** 300s (5 minutos)
- **Región:** us-central1
- **Escalado:** 0-3 instancias

---

## 📊 Monitoreo y Mantenimiento

### Logs y Diagnósticos
```bash
# Ver logs de ejecución
gcloud logs read "resource.type=cloud_run_revision" \
    --limit 50 \
    --format "table(timestamp,textPayload)" \
    --project=rename-driver-folders-v1-07112025

# Ver logs específicos de la aplicación
gcloud logs tail "resource.type=cloud_run_revision" \
    --filter 'resource.labels.service_name="rename-driver-folders"' \
    --project=rename-driver-folders-v1-07112025
```

### Métricas Clave
- **Tiempo de Respuesta:** < 5 segundos
- **Tasa de Éxito:** > 95%
- **Uso de Memoria:** < 400Mi
- **Uso de CPU:** < 0.5 vCPU

### Alertas Sugeridas
```bash
# Configurar alerta de errores
gcloud monitoring policies create \
    --notification-channels=<EMAIL_CHANNEL_ID> \
    --condition-display-name="High Error Rate" \
    --condition-filter='metric.type="run.googleapis.com/request_count"' \
    --condition-aggregations="alignmentPeriod=300s","perSeriesAligner=ALIGN_RATE" \
    --condition-threshold-value=10 \
    --condition-threshold-comparison=COMPARISON_GT \
    --duration=300s
```

---

## 🔧 Solución de Problemas

### Problemas Comunes y Soluciones

#### 1. Error: "Invalid Service Account Key"
**Causa:** Clave mal codificada o expirada
**Solución:**
```bash
# Regenerar clave
gcloud iam service-accounts keys create ~/new-key.json \
    --iam-account=rename-driver-service@rename-driver-folders-v1-07112025.iam.gserviceaccount.com

# Recodificar y actualizar variable de entorno
```

#### 2. Error: "Folder not found"
**Causa:** ROOT_FOLDER_ID incorrecto o sin permisos
**Solución:**
```bash
# Verificar ID y permisos
python -c "
from googleapiclient.discovery import build
import os
service = build('drive', 'v3')
results = service.files().get(fileId='1Q4by0XHi5S_4qOdZH_Fl4jBaX5flIXjn', fields='name,permissions').execute()
print(results)
"
```

#### 3. Error: "Gemini API quota exceeded"
**Causa:** Límite de cuota alcanzado
**Solución:**
- Verificar cuota en Google Cloud Console
- Considerar upgrade de plan
- Implementar retry con exponential backoff

#### 4. Error: "Container startup timeout"
**Causa:** Dependencias faltantes o variables de entorno incorrectas
**Solución:**
```bash
# Verificar logs de startup
gcloud logs read "resource.type=cloud_run_revision" \
    --filter 'textPayload="Starting application"' \
    --project=rename-driver-folders-v1-07112025
```

### Debugging Avanzado
```bash
# Ejecutar contenedor localmente para debugging
docker run -it --rm \
    -e ROOT_FOLDER_ID="1Q4by0XHi5S_4qOdZH_Fl4jBaX5flIXjn" \
    -e SERVICE_ACCOUNT_KEY_B64="<BASE64_KEY>" \
    -e GEMINI_API_KEY="<GEMINI_KEY>" \
    gcr.io/rename-driver-folders-v1-07112025/rename-driver-folders \
    /bin/bash
```

---

## 📡 Referencia de API

### Endpoint Principal
```
POST /
```

#### Headers
- `Content-Length: 0` (Opcional)
- `Content-Type: application/json` (Opcional)

#### Response
```json
{
    "status": "success",
    "message": "Change review process completed.",
    "processed_files": 3,
    "execution_time": 4.5
}
```

#### Ejemplos de Uso

##### cURL
```bash
curl -X POST https://rename-driver-folders-v1-07112025-702567224563.us-central1.run.app \
    -H "Content-Length: 0"
```

##### PowerShell
```powershell
Invoke-WebRequest -Method POST \
    -Uri "https://rename-driver-folders-v1-07112025-702567224563.us-central1.run.app"
```

##### Python
```python
import requests
response = requests.post(
    "https://rename-driver-folders-v1-07112025-702567224563.us-central1.run.app"
)
print(response.text)
```

### Códigos de Estado
- **200 OK:** Ejecución exitosa
- **400 Bad Request:** Parámetros inválidos
- **401 Unauthorized:** Error de autenticación
- **403 Forbidden:** Permisos insuficientes
- **500 Internal Server Error:** Error del servidor
- **503 Service Unavailable:** Servicio temporalmente no disponible

---

## 📝 Checklist de Despliegue

### Pre-Despliegue
- [ ] Cuenta de servicio configurada con roles necesarios
- [ ] Clave JSON generada y codificada en Base64
- [ ] Bucket de estado creado
- [ ] Variables de entorno verificadas
- [ ] Tests locales pasando

### Post-Despliegue
- [ ] Endpoint respondiendo con HTTP 200
- [ ] Logs mostrando ejecución correcta
- [ ] Monitoreo configurado
- [ ] Alertas establecidas
- [ ] Documentación actualizada

### Mantenimiento Mensual
- [ ] Revisar cuotas de Gemini API
- [ ] Verificar uso de Cloud Run
- [ ] Actualizar dependencias si es necesario
- [ ] Revisar y rotar claves de servicio
- [ ] Actualizar documentación

---

## 🆘 Soporte y Contacto

### Recursos
- **Documentación del Proyecto:** `/memory-bank/`
- **Logs de Ejecución:** `/logs/`
- **Tests:** `/tests/`

### Comandos de Diagnóstico Rápidos
```bash
# Verificar estado del servicio
gcloud run services describe rename-driver-folders \
    --region us-central1 \
    --format "table(status.url,latestReadyRevision.name)"

# Ver métricas recientes
gcloud monitoring metrics list \
    --filter 'metric.type="run.googleapis.com/*"' \
    --project=rename-driver-folders-v1-07112025
```

---

**Última Actualización:** 25 de Noviembre de 2025  
**Versión:** v1.07.11.2025  
**Estado:** ✅ Producción Activa