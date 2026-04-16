#!/bin/bash

# Script para ver los logs más recientes del API Server
# Busca logs con el nuevo logging extensivo

echo "📋 API SERVER LOGS - Últimos 5 minutos"
echo "========================================"
echo ""

# Buscar logs de los últimos 5 minutos
FIVE_MIN_AGO=$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%SZ)

gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=renombradorarchivosgdrive-api-server-v2 AND timestamp>=\"${FIVE_MIN_AGO}\"" \
  --project=cloud-functions-474716 \
  --limit=100 \
  --format="value(timestamp,severity,textPayload)" \
  --freshness=5m

echo ""
echo "========================================"
echo "💡 Para ver todos los logs en el browser:"
echo "   https://console.cloud.google.com/logs/query;query=resource.labels.service_name%3D%22renombradorarchivosgdrive-api-server-v2%22"
