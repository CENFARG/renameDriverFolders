#!/bin/bash

# Script para arreglar permisos de Cloud Tasks para la Service Account
# Causa raíz del error 400: Service account sin permisos en Cloud Tasks

set -e  # Exit on error

PROJECT_ID="cloud-functions-474716"
SERVICE_ACCOUNT="cloud-functions-474716@appspot.gserviceaccount.com"

echo "🔧 Configurando permisos de Cloud Tasks para: ${SERVICE_ACCOUNT}"
echo ""

# 1. Agregar role Cloud Tasks Enqueuer
echo "1️⃣ Agregando role: Cloud Tasks Enqueuer..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/cloudtasks.enqueuer" \
  --project=${PROJECT_ID}

if [ $? -eq 0 ]; then
  echo "   ✅ Role Cloud Tasks Enqueuer agregado"
else
  echo "   ❌ Error agregando role Cloud Tasks Enqueuer"
  exit 1
fi

# 2. Agregar role Cloud Tasks Task Creator
echo ""
echo "2️⃣ Agregando role: Cloud Tasks Task Creator..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/cloudtasks.taskCreator" \
  --project=${PROJECT_ID}

if [ $? -eq 0 ]; then
  echo "   ✅ Role Cloud Tasks Task Creator agregado"
else
  echo "   ❌ Error agregando role Cloud Tasks Task Creator"
  exit 1
fi

echo ""
echo "🎉 Permisos configurados exitosamente!"
echo ""
echo "📋 Permisos agregados:"
echo "   - roles/cloudtasks.enqueuer (para encolar tareas)"
echo "   - roles/cloudtasks.taskCreator (para crear tareas)"
echo ""
echo "🔄 Próximo paso:"
echo "   Reiniciar el servicio de API Server para que use los nuevos permisos"
echo ""
echo "⏱️ Los permisos pueden tomar 1-2 minutos en propagarse"
