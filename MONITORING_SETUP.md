# 📊 Configuración de Monitoreo - renameDriverFolders

## ✅ Estado Actual del Monitoreo

### Métricas de Logging Creadas
- **`rename-driver-errors`** - Cuenta errores en la aplicación
- **`rename-driver-success`** - Cuenta ejecuciones exitosas

### Proyecto de Monitoreo
- **ID:** `cloud-functions-474716`
- **Servicio:** `rename-driver-folders`
- **Región:** `us-central1`

## 🚨 Configuración de Alertas

### 1. Alerta de Alta Tasa de Errores
```json
{
  "displayName": "High Error Rate - renameDriverFolders",
  "conditions": [
    {
      "displayName": "Error rate > 10%",
      "filter": "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\" AND metric.labels.response_code_class!=\"2xx\"",
      "aggregations": [
        {
          "alignmentPeriod": "300s",
          "perSeriesAligner": "ALIGN_RATE"
        }
      ],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 0.1,
      "duration": "300s"
    }
  ]
}
```

### 2. Alerta de Tiempo de Respuesta Alto
```json
{
  "displayName": "High Response Time - renameDriverFolders",
  "conditions": [
    {
      "displayName": "95th percentile > 10s",
      "filter": "metric.type=\"run.googleapis.com/request_latencies\" AND resource.type=\"cloud_run_revision\"",
      "aggregations": [
        {
          "alignmentPeriod": "300s",
          "perSeriesAligner": "ALIGN_PERCENTILE_95"
        }
      ],
      "comparison": "COMPARISON_GT",
      "thresholdValue": 10,
      "duration": "300s"
    }
  ]
}
```

## 📈 Dashboard de Monitoreo

### Widgets Recomendados
1. **Request Count** - Número total de solicitudes
2. **Error Rate** - Tasa de errores (porcentaje)
3. **Response Time** - Tiempo de respuesta (percentil 95)
4. **Memory Usage** - Uso de memoria del contenedor
5. **CPU Usage** - Uso de CPU del contenedor
6. **Success Rate** - Tasa de éxito basada en logs

### Filtros para el Dashboard
```
resource.type="cloud_run_revision"
resource.labels.service_name="rename-driver-folders"
```

## 🔧 Comandos de Monitoreo

### Ver Logs en Tiempo Real
```bash
gcloud logs tail "resource.type=cloud_run_revision" \
    --filter 'resource.labels.service_name="rename-driver-folders"' \
    --project=cloud-functions-474716
```

### Ver Métricas de Logging
```bash
gcloud logging metrics list --project=cloud-functions-474716
```

### Ver Logs de Errores
```bash
gcloud logs read "resource.type=cloud_run_revision" \
    --filter 'resource.labels.service_name="rename-driver-folders" AND severity="ERROR"' \
    --limit 50 \
    --project=cloud-functions-474716
```

### Ver Logs de Éxito
```bash
gcloud logs read "resource.type=cloud_run_revision" \
    --filter 'resource.labels.service_name="rename-driver-folders" AND textPayload="Change review process completed."' \
    --limit 50 \
    --project=cloud-functions-474716
```

## 📊 Métricas Disponibles de Cloud Run

### Request Metrics
- `run.googleapis.com/request_count` - Número de solicitudes
- `run.googleapis.com/request_latencies` - Latencia de solicitudes
- `run.googleapis.com/response_count` - Número de respuestas

### Instance Metrics  
- `run.googleapis.com/container/instance/memory/used_bytes` - Memoria usada
- `run.googleapis.com/container/instance/memory/limit_bytes` - Límite de memoria
- `run.googleapis.com/container/instance/cpu/utilization` - Uso de CPU

### Custom Metrics
- `logging.googleapis.com/user/rename-driver-errors` - Errores personalizados
- `logging.googleapis.com/user/rename-driver-success` - Éxitos personalizados

## 🎯 Umbrales Recomendados

### Performance
- **Response Time P95:** < 5 segundos (alerta > 10s)
- **Error Rate:** < 5% (alerta > 10%)
- **Memory Usage:** < 400Mi (alerta > 450Mi)
- **CPU Usage:** < 70% (alerta > 85%)

### Availability
- **Success Rate:** > 95% (alerta < 90%)
- **Uptime:** > 99% (alerta < 95%)

## 📱 Configuración de Canales de Notificación

### Email Channel
```bash
gcloud beta monitoring channels create \
    --display-name="Email Alert" \
    --type=email \
    --channel-labels=email_address="your-email@example.com" \
    --project=cloud-functions-474716
```

### Slack Channel (requiere webhook)
```bash
gcloud beta monitoring channels create \
    --display-name="Slack Alert" \
    --type=slack \
    --channel-labels=channel_name="#alerts",auth_token="xoxb-..." \
    --project=cloud-functions-474716
```

## 🔍 Troubleshooting de Monitoreo

### Problemas Comunes
1. **Métricas no aparecen:** Verificar filtros y permisos
2. **Alertas no disparan:** Revisar umbrales y duración
3. **Dashboard vacío:** Confirmar proyecto y servicio correctos

### Verificación de Estado
```bash
# Verificar estado del servicio
gcloud run services describe rename-driver-folders \
    --region us-central1 \
    --format "table(status.url,latestReadyRevision.name)" \
    --project=cloud-functions-474716

# Verificar últimas revisiones
gcloud run revisions list \
    --service rename-driver-folders \
    --region us-central1 \
    --limit 5 \
    --project=cloud-functions-474716
```

## 📋 Checklist de Monitoreo

### Configuración Inicial
- [x] Métricas de logging creadas
- [ ] Dashboard configurado
- [ ] Canales de notificación creados
- [ ] Alertas configuradas
- [ ] Umbrales ajustados

### Mantenimiento Mensual
- [ ] Revisar efectividad de alertas
- [ ] Ajustar umbrales si es necesario
- [ ] Verificar costos de monitoreo
- [ ] Actualizar dashboards
- [ ] Revisar logs de auditoría

---

**Estado:** ✅ Métricas básicas configuradas  
**Próximos pasos:** Configurar dashboard y alertas completas