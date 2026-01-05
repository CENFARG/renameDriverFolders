#!/bin/bash

# Configuración de Monitoreo para renameDriverFolders
# Proyecto: cloud-functions-474716
# Servicio: rename-driver-folders

echo "🔧 Configurando monitoreo para renameDriverFolders..."

# 1. Crear métrica de logs para errores
echo "📊 Creando métrica de errores..."
gcloud logging metrics create rename-driver-errors \
    --project=cloud-functions-474716 \
    --description="Count of errors in renameDriverFolders" \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="rename-driver-folders" AND severity="ERROR"'

# 2. Crear métrica de logs para ejecuciones exitosas
echo "✅ Creando métrica de ejecuciones exitosas..."
gcloud logging metrics create rename-driver-success \
    --project=cloud-functions-474716 \
    --description="Count of successful executions" \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="rename-driver-folders" AND textPayload="Change review process completed."'

# 3. Crear métrica de logs para tiempo de respuesta
echo "⏱️ Creando métrica de tiempo de respuesta..."
gcloud logging metrics create rename-driver-response-time \
    --project=cloud-functions-474716 \
    --description="Response time tracking" \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="rename-driver-folders" AND jsonPayload.execution_time' \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="rename-driver-folders" AND jsonPayload.execution_time' \
    --metric-kind=GAUGE \
    --value-type=DOUBLE

echo "✅ Métricas de logging creadas exitosamente!"

# 4. Crear dashboard personalizado
echo "📈 Creando dashboard de monitoreo..."

cat > dashboard-config.json << EOF
{
  "displayName": "renameDriverFolders Monitoring",
  "gridLayout": {
    "columns": "2",
    "widgets": [
      {
        "title": "Request Count",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "prometheusQuerySource": {
                  "prometheusQuery": "rate(run.googleapis.com/request_count[5m])"
                }
              },
              "plotType": "LINE",
              "legendTemplate": "{{resource.labels.service_name}}"
            }
          ],
          "timeshiftDuration": "0s",
          "yAxis": {
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "Error Rate",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "prometheusQuerySource": {
                  "prometheusQuery": "rate(run.googleapis.com/request_count[5m])"
                }
              },
              "plotType": "LINE",
              "legendTemplate": "Errors"
            }
          ],
          "timeshiftDuration": "0s",
          "yAxis": {
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "Response Time",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "prometheusQuerySource": {
                  "prometheusQuery": "histogram_quantile(0.95, rate(run.googleapis.com/request_latencies[5m]))"
                }
              },
              "plotType": "LINE",
              "legendTemplate": "95th percentile"
            }
          ],
          "timeshiftDuration": "0s",
          "yAxis": {
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "Memory Usage",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "prometheusQuerySource": {
                  "prometheusQuery": "run.googleapis.com/container/instance/memory/used_bytes"
                }
              },
              "plotType": "LINE",
              "legendTemplate": "Memory Used"
            }
          ],
          "timeshiftDuration": "0s",
          "yAxis": {
            "scale": "LINEAR"
          }
        }
      }
    ]
  }
}
EOF

echo "📋 Dashboard configuration created in dashboard-config.json"
echo "🌐 Para crear el dashboard manualmente:"
echo "1. Ve a Google Cloud Console > Monitoring > Dashboards"
echo "2. Click 'Create Dashboard'"
echo "3. Importa el archivo dashboard-config.json"

# 5. Configurar alertas básicas (requiere canales de notificación)
echo "🚨 Configurando alertas básicas..."

# Alerta de alta tasa de errores
cat > error-rate-alert.json << EOF
{
  "displayName": "High Error Rate - renameDriverFolders",
  "userLabels": {},
  "conditions": [
    {
      "displayName": "Error rate > 10%",
      "conditionThreshold": {
        "filter": "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\" AND metric.labels.response_code_class!=\"2xx\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_RATE"
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0.1,
        "duration": "300s",
        "trigger": {
          "count": 1
        }
      }
    }
  ],
  "alertStrategy": {
    "autoClose": "3600s"
  },
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": []
}
EOF

# Alerta de tiempo de respuesta alto
cat > response-time-alert.json << EOF
{
  "displayName": "High Response Time - renameDriverFolders",
  "userLabels": {},
  "conditions": [
    {
      "displayName": "95th percentile > 10s",
      "conditionThreshold": {
        "filter": "metric.type=\"run.googleapis.com/request_latencies\" AND resource.type=\"cloud_run_revision\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_PERCENTILE_95"
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 10,
        "duration": "300s",
        "trigger": {
          "count": 1
        }
      }
    }
  ],
  "alertStrategy": {
    "autoClose": "3600s"
  },
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": []
}
EOF

echo "📁 Archivos de configuración de alertas creados:"
echo "  - error-rate-alert.json"
echo "  - response-time-alert.json"
echo ""
echo "🔧 Para completar la configuración:"
echo "1. Crea canales de notificación (email, Slack, etc.)"
echo "2. Importa los archivos JSON en Monitoring > Alerting"
echo "3. Asigna los canales de notificación a las alertas"
echo ""
echo "✅ Configuración de monitoreo completada!"