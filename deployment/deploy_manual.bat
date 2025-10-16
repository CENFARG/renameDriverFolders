@echo off
SETLOCAL

REM --- Configuración ---
SET GCP_PROJECT_ID=cloud-functions
SET GCP_REGION=southamerica-east1
SET SERVICE_NAME=rename-drive-folders
SET IMAGE_NAME=gcr.io/%GCP_PROJECT_ID%/%SERVICE_NAME%

REM --- Variables de Entorno para Cloud Run (deben coincidir con .env) ---
REM ADVERTENCIA: No incluyas secretos directamente aquí. Usa Secret Manager o variables de entorno seguras.
REM Para este ejemplo, asumimos que las variables ya están configuradas en tu entorno de shell
REM o que las pasarás manualmente con --set-env-vars o --set-secrets.

REM --- Autenticación (si no estás ya autenticado) ---
REM gcloud auth login
REM gcloud config set project %GCP_PROJECT_ID%

ECHO.
ECHO --- Construyendo y desplegando %SERVICE_NAME% en Google Cloud Run ---
ECHO Proyecto: %GCP_PROJECT_ID%
ECHO Región: %GCP_REGION%
ECHO Servicio: %SERVICE_NAME%
ECHO Imagen: %IMAGE_NAME%
ECHO.

REM --- Paso 1: Construir la imagen de Docker y subirla a Google Container Registry ---
ECHO Construyendo imagen Docker...
gcloud builds submit --tag %IMAGE_NAME% --project %GCP_PROJECT_ID%
IF %ERRORLEVEL% NEQ 0 (
    ECHO Error al construir la imagen Docker. Abortando.
    GOTO :EOF
)
ECHO Imagen Docker construida y subida exitosamente.
ECHO.

REM --- Paso 2: Desplegar el servicio en Google Cloud Run ---
ECHO Desplegando servicio en Cloud Run...

REM Construir la lista de variables de entorno a partir de las variables de tu shell
SET ENV_VARS_LIST=

REM Aquí deberías listar todas las variables de entorno que tu aplicación necesita
REM y que están definidas en tu archivo .env local.
REM Por ejemplo:
REM SET ENV_VARS_LIST=%ENV_VARS_LIST%ROOT_FOLDER_ID=%ROOT_FOLDER_ID%,
REM SET ENV_VARS_LIST=%ENV_VARS_LIST%TARGET_FOLDER_NAMES="%TARGET_FOLDER_NAMES%",
REM SET ENV_VARS_LIST=%ENV_VARS_LIST%GCS_BUCKET_NAME=%GCS_BUCKET_NAME%,
REM SET ENV_VARS_LIST=%ENV_VARS_LIST%GCP_PROJECT_ID=%GCP_PROJECT_ID%,
REM SET ENV_VARS_LIST=%ENV_VARS_LIST%GCP_REGION=%GCP_REGION%,
REM SET ENV_VARS_LIST=%ENV_VARS_LIST%GEMINI_API_KEY=%GEMINI_API_KEY%

REM Para SERVICE_ACCOUNT_KEY_B64, es mejor usar Secret Manager o pasarlo como un secreto.
REM Por simplicidad en este script, lo pasaremos como variable de entorno.
REM SET ENV_VARS_LIST=%ENV_VARS_LIST%SERVICE_ACCOUNT_KEY_B64="%SERVICE_ACCOUNT_KEY_B64%"

REM --- IMPORTANTE: Configura tus variables de entorno aquí ---
REM Reemplaza los valores de ejemplo con tus variables reales.
REM Para variables que contienen espacios o caracteres especiales, usa comillas dobles.

SET ENV_VARS_LIST=ROOT_FOLDER_ID="%ROOT_FOLDER_ID%",TARGET_FOLDER_NAMES="%TARGET_FOLDER_NAMES%",GCS_BUCKET_NAME="%GCS_BUCKET_NAME%",GCP_PROJECT_ID="%GCP_PROJECT_ID%",GCP_REGION="%GCP_REGION%",GEMINI_API_KEY="%GEMINI_API_KEY%",SERVICE_ACCOUNT_KEY_B64="%SERVICE_ACCOUNT_KEY_B64%"


gcloud run deploy %SERVICE_NAME% ^
    --image %IMAGE_NAME% ^
    --platform managed ^
    --region %GCP_REGION% ^
    --allow-unauthenticated ^
    --set-env-vars %ENV_VARS_LIST% ^
    --project %GCP_PROJECT_ID%

IF %ERRORLEVEL% NEQ 0 (
    ECHO Error al desplegar el servicio en Cloud Run. Abortando.
    GOTO :EOF
)
ECHO Servicio %SERVICE_NAME% desplegado exitosamente en Google Cloud Run.

ENDLOCAL
