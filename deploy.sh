#!/bin/bash
# Deployment Script para renameDriverFolders
# Automatiza el deployment completo a Google Cloud Run

set -e  # Exit on error

# Colors para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "DEPLOYMENT_GUIDE.md" ]; then
    print_error "Este script debe ejecutarse desde el root del proyecto"
    exit 1
fi

# Cargar configuración desde .env.deploy si existe
if [ -f ".env.deploy" ]; then
    print_status "Cargando configuración desde .env.deploy"
    source .env.deploy
fi

# Solicitar configuración si no está en .env
if [ -z "$GCP_PROJECT_ID" ]; then
    read -p "Project ID de Google Cloud: " GCP_PROJECT_ID
fi

if [ -z "$GCP_REGION" ]; then
    GCP_REGION="us-central1"
fi

print_status "Proyecto: $GCP_PROJECT_ID"
print_status "Región: $GCP_REGION"

# Confirmar antes de continuar
read -p "¿Continuar con el deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelado"
    exit 0
fi

# ============================================================================
# PASO 1: Habilitar APIs
# ============================================================================
print_status "Habilitando APIs necesarias..."

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  cloudtasks.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  vision.googleapis.com \
  drive.googleapis.com \
  --project=$GCP_PROJECT_ID

print_status "APIs habilitadas"

# ============================================================================
# PASO 2: Crear Service Accounts
# ============================================================================
print_status "Creando Service Accounts..."

# Worker
gcloud iam service-accounts create worker-renombrador \
  --display-name="Worker Renombrador Service Account" \
  --project=$GCP_PROJECT_ID \
  2>/dev/null || print_warning "Service Account worker-renombrador ya existe"

# API Server
gcloud iam service-accounts create api-server \
  --display-name="API Server Service Account" \
  --project=$GCP_PROJECT_ID \
  2>/dev/null || print_warning "Service Account api-server ya existe"

# Scheduler
gcloud iam service-accounts create scheduler-trigger \
  --display-name="Cloud Scheduler Trigger" \
  --project=$GCP_PROJECT_ID \
  2>/dev/null || print_warning "Service Account scheduler-trigger ya existe"

print_status "Service Accounts creados"

# ============================================================================
# PASO 3: Asignar Permisos
# ============================================================================
print_status "Asignando permisos..."

# Worker permisos
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:worker-renombrador@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudvision.user" \
  --condition=None

# API Server permisos
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:api-server@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudtasks.enqueuer" \
  --condition=None

# Scheduler permisos
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:scheduler-trigger@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --condition=None

print_status "Permisos asignados"

# ============================================================================
# PASO 4: Build y Deploy Worker
# ============================================================================
print_status "Building Worker image..."

gcloud builds submit \
  --tag gcr.io/$GCP_PROJECT_ID/worker-renombrador:latest \
  --timeout=20m \
  --project=$GCP_PROJECT_ID \
  services/worker-renombrador

print_status "Worker image built"

print_status "Deploying Worker..."

gcloud run deploy worker-renombrador \
  --image gcr.io/$GCP_PROJECT_ID/worker-renombrador:latest \
  --platform managed \
  --region $GCP_REGION \
  --service-account worker-renombrador@$GCP_PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars USE_SUPABASE=true,ENABLE_OCR=true \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900s \
  --max-instances 10 \
  --no-allow-unauthenticated \
  --project=$GCP_PROJECT_ID

WORKER_URL=$(gcloud run services describe worker-renombrador \
  --region $GCP_REGION \
  --project=$GCP_PROJECT_ID \
  --format 'value(status.url)')

print_status "Worker deployed: $WORKER_URL"

# ============================================================================
# PASO 5: Build y Deploy API Server
# ============================================================================
print_status "Building API Server image..."

gcloud builds submit \
  --tag gcr.io/$GCP_PROJECT_ID/api-server:latest \
  --timeout=20m \
  --project=$GCP_PROJECT_ID \
  services/api-server

print_status "API Server image built"

print_status "Deploying API Server..."

gcloud run deploy api-server \
  --image gcr.io/$GCP_PROJECT_ID/api-server:latest \
  --platform managed \
  --region $GCP_REGION \
  --service-account api-server@$GCP_PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars \
    GCP_PROJECT=$GCP_PROJECT_ID,\
    GCP_LOCATION=$GCP_REGION,\
    TASKS_QUEUE=document-processing-queue,\
    WORKER_URL=$WORKER_URL,\
    WORKER_SERVICE_ACCOUNT=worker-renombrador@$GCP_PROJECT_ID.iam.gserviceaccount.com,\
    USE_SUPABASE=true \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60s \
  --max-instances 10 \
  --allow-unauthenticated \
  --project=$GCP_PROJECT_ID

API_URL=$(gcloud run services describe api-server \
  --region $GCP_REGION \
  --project=$GCP_PROJECT_ID \
  --format 'value(status.url)')

print_status "API Server deployed: $API_URL"

# ============================================================================
# PASO 6: Crear Cloud Tasks Queue
# ============================================================================
print_status "Creando Cloud Tasks queue..."

gcloud tasks queues create document-processing-queue \
  --location=$GCP_REGION \
  --max-concurrent-dispatches=10 \
  --max-dispatches-per-second=5 \
  --max-attempts=3 \
  --min-backoff=60s \
  --max-backoff=3600s \
  --project=$GCP_PROJECT_ID \
  2>/dev/null || print_warning "Queue ya existe"

print_status "Cloud Tasks queue creada"

# ============================================================================
# PASO 7: Dar permisos a Cloud Tasks
# ============================================================================
print_status "Configurando permisos de Cloud Tasks..."

gcloud run services add-iam-policy-binding worker-renombrador \
  --region=$GCP_REGION \
  --member=serviceAccount:api-server@$GCP_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/run.invoker \
  --project=$GCP_PROJECT_ID

print_status "Permisos configurados"

# ============================================================================
# PASO 8: Crear Cloud Scheduler Job
# ============================================================================
print_status "Creando Cloud Scheduler job..."

gcloud scheduler jobs create http daily-processing \
  --schedule="0 8 * * *" \
  --time-zone="America/Argentina/Buenos_Aires" \
  --uri="$API_URL/api/v1/jobs/scheduled" \
  --http-method=POST \
  --oidc-service-account-email=scheduler-trigger@$GCP_PROJECT_ID.iam.gserviceaccount.com \
  --oidc-token-audience=$API_URL \
  --location=$GCP_REGION \
  --description="Trigger daily document processing" \
  --project=$GCP_PROJECT_ID \
  2>/dev/null || print_warning "Scheduler job ya existe"

print_status "Cloud Scheduler job creado"

# ============================================================================
# RESUMEN
# ============================================================================
echo ""
echo "========================================="
echo "  DEPLOYMENT COMPLETO ✓"
echo "========================================="
echo ""
echo "URLs:"
echo "  API Server: $API_URL"
echo "  Worker:     $WORKER_URL"
echo ""
echo "Endpoints:"
echo "  Health:      $API_URL/health"
echo "  Manual Jobs: $API_URL/api/v1/jobs/manual"
echo "  List Jobs:   $API_URL/api/v1/jobs"
echo ""
echo "Configuración:"
echo "  Project:  $GCP_PROJECT_ID"
echo "  Region:   $GCP_REGION"
echo "  Queue:    document-processing-queue"
echo ""
echo "Próximos pasos:"
echo "  1. Configurar secrets en Secret Manager"
echo "  2. Configurar Supabase (crear tablas)"
echo "  3. Insertar jobs de ejemplo"
echo "  4. Test health check: curl $API_URL/health"
echo ""
echo "Ver guía completa en: DEPLOYMENT_GUIDE.md"
echo "========================================="
