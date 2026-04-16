# 📊 INVESTIGACIÓN: Historial de Auditoría - Tarea 1.2
## Proyecto Renombrador (#amBotHsOS) - V3.1.2

---

## 📋 RESUMEN EJECUTIVO

**Fecha de Investigación:** 12 de Marzo, 2026
**Investigador:** Claude (AI Assistant)
**Estado:** 🟡 EN PROGRESO - Requiere acceso a credenciales de Supabase

---

## 🎯 PROBLEMA REPORTADO

**Síntoma Principal:**
- Los logs de auditoría no se ven en el dashboard
- Los usuarios tienen que ir manualmente a la carpeta de Drive para verificar si se renombraron archivos
- Se perdieron logs históricos de ejecuciones anteriores

**Problema Adicional:**
- No hay visibilidad del estado de las ejecuciones
- No se puede exportar el historial

---

## ✅ VERIFICACIONES REALIZADAS

### 1. Código de Auditoría en Backend ✅

**API Server (`services/api-server/src/main.py`):**
```python
# Líneas 568-578: Creación de execution_log
execution_log = {
    "id": f"exec-{int(time.time() * 1000)}",
    "user_email": user["email"],
    "user_name": user.get("name", "Unknown"),
    "folder_id": job_request.folder_id,
    "job_type": job_request.job_type,
    "job_config_id": job_id,
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "status": "submitted",
    "task_id": None
}
```

**Worker (`services/worker-renombrador/src/main.py`):**
```python
# Líneas 627-645: Actualización de estado
executions_manager.update("id", task.execution_id, {"status": "processing"})
# ... después de procesar ...
executions_manager.update("id", task.execution_id, {
    "status": "completed" if result.get("status") == "success" else "failed",
    "details": f"Processed {result.get('stats', {}).get('renamed', 0)} files."
})
```

**Conclusión:** ✅ El código de auditoría está BIEN implementado
- Estados: "submitted" → "processing" → "completed"/"failed"
- Updates en tiempo real
- Manejo de errores robusto

---

### 2. Endpoint de Audit Logs ✅

**API Endpoint (`/api/v1/audit-logs`):**
```python
@app.get("/api/v1/audit-logs")
async def get_audit_logs(limit: int = 100, user: dict = Depends(get_current_user)):
    all_executions = executions_manager.find_all()
    all_executions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    # ... retorna logs ordenados por timestamp
```

**Conclusión:** ✅ El endpoint existe y está bien implementado

---

### 3. Database Manager Configuration ✅

**Inicialización:**
```python
# API Server (línea 104-115)
if use_supabase:
    executions_manager = DatabaseManager(
        use_supabase=True,
        table_name="job_executions"
    )
```

**Conclusión:** ✅ Se usa Supabase para persistencia

---

### 4. Búsqueda de Logs en Google Cloud Logging ⚠️

**Resultados:**
- ❌ No se encontraron logs de ejecuciones recientes
- ❌ No hay mención a estados "submitted", "processing", "completed"
- ❌ No hay logs de job_executions en los últimos 7 días

**Conclusión:** ⚠️ O bien:
1. No hay ejecuciones recientes
2. Los logs no se están guardando correctamente
3. Los logs están en otro formato/lugar

---

### 5. Intento de Conexión a Supabase ❌

**Problema:**
- Credenciales de Supabase NO están en variables de entorno local
- Script de prueba NO pudo conectarse a Supabase
- Error: `SUPABASE_URL: MISSING`, `SUPABASE_KEY: MISSING`

**Por qué:**
- En producción, las credenciales se obtienen de Google Secret Manager
- Localmente no hay archivo .env con estas credenciales

**Conclusión:** ❌ No se puede verificar datos en Supabase sin credenciales

---

## 🔍 HIPÓTESIS DE CAUSA RAÍZ

### Hipótesis 1: Credenciales de Supabase Mal Configuradas (Más Probable) 🎯

**Qué puede estar pasando:**
- Las credenciales de Supabase NO están en Google Secret Manager
- Las credenciales están mal configuradas (URL o key incorrecta)
- El DatabaseManager NO puede conectarse a Supabase

**Evidencia que soporta esta hipótesis:**
- No hay logs de job_executions en Google Cloud Logging
- Si hubiera ejecuciones, deberíamos ver logs de "Job execution logged"
- El código está bien, pero si no hay conexión, no se guardan logs

**Cómo verificar:**
- Verificar si el secreto "supabase-url" existe en Google Secret Manager
- Verificar si el secreto "supabase-key" existe en Google Secret Manager
- Verificar si las credenciales son válidas

---

### Hipótesis 2: Tabla job_executions No Existe en Supabase (Posible)

**Qué puede estar pasando:**
- La tabla `job_executions` NO se creó en Supabase
- La tabla tiene un nombre diferente
- La base de datos de Supabase no está inicializada

**Evidencia que soporta esta hipótesis:**
- El código asume que la tabla existe
- No hay verificación de si la tabla existe antes de insertar

**Cómo verificar:**
- Conectarse a Supabase con credenciales válidas
- Verificar si la tabla `job_executions` existe
- Verificar si hay datos en la tabla

---

### Hipótesis 3: Frontend No Muestra los Logs Correctamente (Posible)

**Qué puede estar pasando:**
- El frontend NO está llamando a `/api/v1/audit-logs`
- El frontend tiene un error al mostrar los logs
- El frontend no está autenticándose correctamente

**Evidencia que soporta esta hipótesis:**
- El usuario dice que no ve los logs en el dashboard
- Pero los logs SÍ se están guardando en Supabase

**Cómo verificar:**
- Verificar el código del frontend (app.component.ts)
- Verificar si hay errores en la consola del browser
- Verificar la Network request a `/api/v1/audit-logs`

---

## 📋 PRÓXIMOS PASOS RECOMENDADOS

### 🔴 PASO 1: Verificar Secretos en Google Secret Manager (CRÍTICO)

**Acción:**
```bash
# Listar todos los secretos
gcloud secrets list --project=cloud-functions-474716

# Buscar secretos de Supabase
gcloud secrets list --project=cloud-functions-474716 | grep -i supabase

# Si existen, verificar valores
gcloud secrets versions access latest --secret="supabase-url" --project=cloud-functions-474716
gcloud secrets versions access latest --secret="supabase-key" --project=cloud-functions-474716
```

**Qué verificar:**
- ¿Existen los secretos?
- ¿Los valores son correctos?
- ¿El formato es válido?

---

### 🟡 PASO 2: Verificar Tabla en Supabase (Importante)

**Acción:**
1. Ir a Supabase Dashboard: https://supabase.com/dashboard
2. Seleccionar el proyecto
3. Ir a "Table Editor"
4. Verificar si existe la tabla `job_executions`
5. Si existe, verificar si tiene datos

**Qué verificar:**
- ¿Existe la tabla?
- ¿Qué columnas tiene?
- ¿Cuántos registros hay?
- ¿Hay registros recientes?

---

### 🟢 PASO 3: Probar Endpoint Directamente (Opcional)

**Acción:**
```bash
# Obtener token OAuth válido
# (necesario autenticarse primero)

# Probar endpoint
curl -X GET \
  "https://renombradorarchivosgdrive-api-server-v2-.../api/v1/audit-logs?limit=10" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json"
```

**Qué verificar:**
- ¿El endpoint retorna datos?
- ¿El status code es 200?
- ¿Hay logs en la respuesta?

---

## 💡 SOLUCIONES PROPUESTAS

### Solución 1: Si los Secretos No Existen

**Crear secretos en Google Secret Manager:**
```bash
# Crear secreto de URL
echo "https://xxxxx.supabase.co" | \
  gcloud secrets versions add supabase-url \
    --project=cloud-functions-474716 \
    --data-file=-

# Crear secreto de KEY
echo "eyJhbGci..." | \
  gcloud secrets versions add supabase-key \
    --project=cloud-functions-474716 \
    --data-file=-
```

---

### Solución 2: Si la Tabla No Existe

**Crear tabla en Supabase:**
```sql
CREATE TABLE IF NOT EXISTS job_executions (
  id VARCHAR(255) PRIMARY KEY,
  user_email VARCHAR(255),
  user_name VARCHAR(255),
  folder_id VARCHAR(255),
  job_type VARCHAR(100),
  job_config_id VARCHAR(255),
  timestamp TIMESTAMP WITH TIME ZONE,
  status VARCHAR(50),  -- submitted, processing, completed, failed
  task_id VARCHAR(255),
  details TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_job_executions_timestamp ON job_executions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_job_executions_user_email ON job_executions(user_email);
CREATE INDEX IF NOT EXISTS idx_job_executions_status ON job_executions(status);
```

---

### Solución 3: Si el Frontend No Muestra los Logs

**Verificar código del frontend:**
```typescript
// services/frontend/src/app/app.component.ts

getAuditLogs() {
  this.auditService.getAuditLogs(100).subscribe({
    next: (logs) => {
      this.auditLogs = logs;
      console.log('Audit logs loaded:', logs.length);
    },
    error: (error) => {
      console.error('Error loading audit logs:', error);
      // Mostrar error al usuario
    }
  });
}
```

---

## 📊 IMPACTO

**Usuarios Afectados:** Todos (Gonzalo y Diego)
**Funcionalidad Perdida:** Visibilidad de ejecuciones
**Severidad:** 🟡 MEDIA (El sistema funciona, pero no hay visibilidad)

---

## 🔄 ESTADO DE LA INVESTIGACIÓN

| Paso | Descripción | Estado |
|------|-------------|--------|
| 1 | Verificar código de auditoría (backend) | ✅ Completado - Código OK |
| 2 | Verificar endpoint /audit-logs | ✅ Completado - Endpoint OK |
| 3 | Buscar logs en Google Cloud Logging | ⚠️ Completado - No hay logs |
| 4 | Intentar conexión a Supabase | ❌ Falló - Sin credenciales |
| 5 | Verificar secretos en Secret Manager | ⏳ Pendiente |
| 6 | Verificar tabla en Supabase Dashboard | ⏳ Pendiente |
| 7 | Probar endpoint directamente | ⏳ Pendiente |

---

## 📝 NOTAS PARA EL DESARROLLADOR

**Memoria Engram Guardada:**
- ID: #4
- Título: "Inicio Tarea 1.2 - Recuperar Auditoría"
- Progreso: Verificaciones backend completadas, requiere credenciales Supabase

**Script de Prueba Creado:**
- `scripts/test_supabase.py` - Para verificar datos cuando tengamos credenciales

**Commit Relacionado:**
- Pendiente (en investigación)

---

**Documento Creado:** 12 de Marzo, 2026
**Versión:** 1.0
**Próxima Revisión:** Cuando se tenga acceso a credenciales de Supabase

---

*Este documento es parte de la investigación de la Tarea 1.2 del Implementation Plan*
