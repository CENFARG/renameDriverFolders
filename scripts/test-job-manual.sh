#!/bin/bash

# Script para probar manualmente el endpoint /api/v1/jobs/manual
# y ver los logs detallados del API Server

set -e  # Exit on error

API_SERVER="https://renombradorarchivosgdrive-api-server-v2-702567224563.us-central1.run.app"
FOLDER_ID="1Q4by0XHi5S_4qOdZH_Fl4jBaX5flIXjn"
JOB_TYPE="generic"

echo "🔧 TEST MANUAL JOB SUBMISSION"
echo "================================"
echo ""

# Paso 1: Obtener token de OAuth (debes estar logueado en Google)
echo "1️⃣ Para obtener el OAuth token:"
echo "   - Abre la aplicación: https://renombradorarchivosgdrive-frontend-v2-702567224563.us-central1.run.app"
echo "   - Loguéate con tu cuenta"
echo "   - Abre la consola del navegador (F12)"
echo "   - Ejecuta: localStorage.getItem('auth_token')"
echo "   - Copia el token"
echo ""
read -p "📝 Pega aquí el OAuth token: " OAUTH_TOKEN

if [ -z "$OAUTH_TOKEN" ]; then
    echo "❌ No se proporcionó token. Saliendo..."
    exit 1
fi

echo ""
echo "✅ Token recibido (primeros 20 chars): ${OAUTH_TOKEN:0:20}..."
echo ""

# Paso 2: Enviar request manual
echo "2️⃣ Enviando request POST a /api/v1/jobs/manual..."
echo ""

PAYLOAD=$(cat <<EOF
{
  "folder_id": "$FOLDER_ID",
  "job_type": "$JOB_TYPE"
}
EOF
)

echo "📦 Payload:"
echo "$PAYLOAD"
echo ""

# Enviar request y capturar respuesta
RESPONSE=$(curl -X POST "${API_SERVER}/api/v1/jobs/manual" \
  -H "Authorization: Bearer ${OAUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  -w "\nHTTP_CODE:%{http_code}" \
  -s)

echo "📋 Response:"
echo "$RESPONSE"
echo ""

# Extraer HTTP status code
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d':' -f2)
echo ""
echo "================================"
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "202" ]; then
    echo "✅ REQUEST EXITOSO (HTTP $HTTP_CODE)"
else
    echo "❌ REQUEST FALLÓ (HTTP $HTTP_CODE)"
    echo ""
    echo "📝 Ver los logs del API Server:"
    echo ""
    echo "   gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=renombradorarchivosgdrive-api-server-v2 AND severity>=INFO AND timestamp>=$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%SZ)\" \\"
    echo "     --project=cloud-functions-474716 \\"
    echo "     --limit=50 \\"
    echo "     --format='value(timestamp,severity,textPayload)' \\"
    echo "     --freshness=1h"
    echo ""
    echo "   O en el browser:"
    echo "   https://console.cloud.google.com/logs/query;query=resource.labels.service_name%3D%22renombradorarchivosgdrive-api-server-v2%22"
    echo ""
fi
