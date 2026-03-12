# 📊 08. MONITORING
## Proyecto Renombrador (#amBotHsOS) - V3.1.2 "Estudio Inteligente"

---

## 🎯 PROPÓSITO DEL DOCUMENTO

Definir la estrategia de monitoreo, alertas y observabilidad para el sistema **Renombrador** V3.1.2.

---

## 📊 ESTADO ACTUAL

| Aspecto | Estado | Herramienta |
|---------|--------|-------------|
| **Logging** | ✅ Parcial | Google Cloud Logging |
| **Metrics** | ❌ No | No implementado |
| **Dashboards** | ❌ No | No implementado |
| **Alerts** | ❌ No | No implementado |
| **Tracing** | ❌ No | No implementado |

---

## 🎯 ESTRATEGIA DE MONITOREO

### 1. Logging (Actual)

**Niveles de Log:**
```python
DEBUG   - Desarrollo: Información detallada de step-by-step
INFO    - Producción: Eventos de negocio
WARNING - Anomalías no críticas
ERROR   - Errores que requieren atención
CRITICAL - Caídas de servicio
```

**Formato Estructurado:**
```python
logger.info(
    "job_executed",
    extra={
        "job_id": job_id,
        "user_email": user_email,
        "files_processed": 100,
        "files_renamed": 95,
        "errors": 5,
        "duration_ms": 35000
    }
)
```

**Consultas Útiles:**
```bash
# Logs de API Server
gcloud logs tail /projects/cloud-functions-474716/logs/renombradorarchivosgdrive-api-server-v2

# Logs de Worker
gcloud logs tail /projects/cloud-functions-474716/logs/renombradorarchivosgdrive-worker-v2

# Logs con filtro
gcloud logs read \
  --project=cloud-functions-474716 \
  --filter="resource.type=cloud_run_revision AND severity>=ERROR"
```

---

### 2. Metrics (Propuesto)

#### KPIs de Negocio

**Métricas Clave:**
```python
# Jobs ejecutados
jobs_executed_total{trigger_type="manual|scheduled"}

# Archivos procesados
files_processed_total{status="renamed|error|skipped"}

# Tasa de éxito
success_rate = files_renamed / files_processed * 100

# Tiempo de procesamiento
processing_duration_seconds{job_id, folder_id}

# Errores por tipo
errors_total{error_type="ocr|gemini|drive|validation"}
```

#### KPIs Técnicos

**Métricas de Infraestructura:**
```python
# Latencia de API
api_request_duration_seconds{endpoint="/api/v1/jobs/manual", status="200|422|500"}

# Tasa de errores
api_error_rate{endpoint, status}

# Uso de recursos
container_memory_usage_bytes{service="api-server|worker"}
cpu_utilization{service="api-server|worker"}

# Cantidad de requests
requests_total{endpoint, method}
```

---

### 3. Dashboards (Propuesto)

#### Dashboard Principal

**Widgets:**
1. **Jobs Ejecutados (Hoy)**
   - Gráfico de línea: jobs por hora
   - Desglosado por: manual vs scheduled

2. **Tasa de Éxito (7 días)**
   - Gauge: 0-100%
   - Meta: >95%

3. **Archivos Procesados (Semana)**
   - Gráfico de barras: archivos por día
   - Desglosado por: renombrados vs errores

4. **Errores por Tipo (24hs)**
   - Gráfico de torta: OCR, Gemini, Drive, Validación
   - Click para ver detalles

5. **Latencia Promedio (1 hora)**
   - Gráfico de línea: ms por job
   - Meta: <30s para 100 archivos

6. **Estado de Servicios**
   - Status: API Server, Worker, Frontend
   - Último deployment

---

### 4. Alerts (Propuesto)

#### Alerts Críticos (Página)

**Alerta 1: Worker Down**
```yaml
name: Worker Down
condition: uptime < 5 min
severity: CRITICAL
notification: Email + SMS
channels:
  - gonzalo.f.recalde@gmail.com
```

**Alerta 2: Tasa de Éxito < 90%**
```yaml
name: High Error Rate
condition: success_rate < 90% for 15min
severity: CRITICAL
notification: Email + Slack
channels:
  - gonzalo.f.recalde@gmail.com
  - #alerts channel
```

**Alerta 3: Errores 500 > 10%**
```yaml
name: API 500 Errors Spike
condition: error_rate_500 > 10% for 5min
severity: CRITICAL
notification: Email + SMS
```

#### Alerts de Advertencia (Warning)

**Alerta 4: Latencia > 60s**
```yaml
name: High Latency
condition: processing_duration > 60s for 10min
severity: WARNING
notification: Email
```

**Alerta 5: Memoria > 80%**
```yaml
name: High Memory Usage
condition: memory_usage > 80% for 5min
severity: WARNING
notification: Email
```

---

### 5. Tracing (Propuesto)

**Distributed Tracing con Google Cloud Trace:**

```python
# Inicializar tracing
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

tracer = trace.get_tracer(__name__)

# Ejemplo de span
with tracer.start_as_current_span("process_job") as span:
    span.set_attribute("job_id", job_id)
    span.set_attribute("user_email", user_email)

    with tracer.start_as_current_span("analyze_document"):
        # Lógica de análisis
        pass
```

---

## 🛠️ HERRAMIENTAS PROPUESTAS

### Opción A: Google Cloud Operations Suite (Recomendado)

**Ventajas:**
- ✅ Integración nativa con Cloud Run
- ✅ Logging ya configurado
- ✅ Monitoring sin infra adicional
- ✅ Gratis hasta cierto límite

**Costo:**
- Logging: ~$0.50/GB ingested
- Monitoring: ~$0.25/instance/month

### Opción B: Prometheus + Grafana

**Ventajas:**
- ✅ Open source
- ✅ Dashboards personalizables
- ✅ Alertas flexibles

**Desventajas:**
- ❌ Requiere infra adicional
- ❌ Mantenimiento de servidores

### Opción C: Datadog

**Ventajas:**
- ✅ Todo-en-uno
- ✅ Excelente UX

**Desventajas:**
- ❌ Costoso ($15/host/month)

---

## 📊 IMPLEMENTACIÓN ROADMAP

### Fase 1: Logging Mejorado (V3.1.3)
- [ ] Estandarizar formato de logs
- [ ] Agregar logs estructurados
- [ ] Crear consultas guardadas
- [ ] Documentar troubleshooting

### Fase 2: Dashboard Básico (V3.2)
- [ ] Google Cloud Operations Dashboard
- [ ] Widgets principales
- [ ] Consultas útiles
- [ ] Compartir con equipo

### Fase 3: Alerts (V3.2)
- [ ] Configurar alerts críticos
- [ ] Configurar channels de notificación
- [ ] Documentar runbooks
- [ ] Test de alerts

### Fase 4: Metrics Avanzados (V4.0)
- [ ] Prometheus + custom metrics
- [ ] Grafana dashboards
- [ ] Distributed tracing

---

## 📋 RUNBOOKS

### Runbook 1: Worker Down

**Síntoma:** No se ejecutan jobs, dashboard muestra "Worker Offline"

**Diagnóstico:**
```bash
# 1. Verificar estado del servicio
gcloud run services describe renombradorarchivosgdrive-worker-v2

# 2. Verificar logs recientes
gcloud logs tail /projects/cloud-functions-474716/logs/renombradorarchivosgdrive-worker-v2 --limit=50

# 3. Verificar errores
gcloud logs read --filter="severity>=ERROR" --limit=20
```

**Solución:**
```bash
# Si el servicio está crash loop
gcloud run services update renombradorarchivosgdrive-worker-v2 \
  --region=us-central1 \
  --memory=1Gi \
  --cpu=2
```

---

### Runbook 2: Alta Tasa de Errores

**Síntoma:** Tasa de éxito < 90%

**Diagnóstico:**
```bash
# 1. Verificar tipos de errores
gcloud logs read --filter='jsonPayload.error_type' --limit=100

# 2. Verificar si es error de Gemini
gcloud logs read --filter='jsonPayload.error_type="gemini"' --limit=50

# 3. Verificar si es error de OCR
gcloud logs read --filter='jsonPayload.error_type="ocr"' --limit=50
```

**Solución:**
- Si es Gemini: Verificar API key, quota, modelo
- Si es OCR: Verificar permisos de Cloud Vision
- Si es Drive: Verificar permisos de carpeta

---

**Creado:** 12 de Marzo, 2026
**Versión:** 1.0
**Próxima revisión:** V3.2 (Q2 2026)

---

*Este documento es parte de los 10 documentos de gestión CENF v2.3.0*
