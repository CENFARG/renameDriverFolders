@echo off
REM deployment/deploy.bat
REM English: This script builds and pushes the Docker image to Google Container Registry.
REM Español: Este script construye y sube la imagen de Docker a Google Container Registry.

REM English: Ensure gcloud CLI is authenticated and configured.
REM Español: Asegúrate de que gcloud CLI esté autenticado y configurado.

REM English: Get GCP_PROJECT_ID from environment variables.
REM Español: Obtener GCP_PROJECT_ID de las variables de entorno.
IF "%GCP_PROJECT_ID%"=="" (
    echo Error: La variable de entorno GCP_PROJECT_ID no está configurada.
    echo Por favor, configúrala antes de ejecutar este script.
    goto :eof
)

REM English: Define image name.
REM Español: Definir el nombre de la imagen.
SET IMAGE_NAME=gcr.io/%GCP_PROJECT_ID%/renamedriverfolders

REM English: Build the Docker image.
REM Español: Construir la imagen de Docker.
echo Building Docker image...
docker build -t %IMAGE_NAME% ..

IF %ERRORLEVEL% NEQ 0 (
    echo Error al construir la imagen de Docker.
    goto :eof
)

REM English: Push the Docker image to Google Container Registry.
REM Español: Subir la imagen de Docker a Google Container Registry.
echo Pushing Docker image to GCR...
docker push %IMAGE_NAME%

IF %ERRORLEVEL% NEQ 0 (
    echo Error al subir la imagen de Docker.
    goto :eof
)

echo Docker image built and pushed successfully: %IMAGE_NAME%
echo Ahora puedes desplegar en Cloud Run usando Cloud Code en VS Code.