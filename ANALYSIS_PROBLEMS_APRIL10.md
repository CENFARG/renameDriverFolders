# Análisis de Problemas - 10 Abril 2026

**Fecha**: 10 de Abril 2026
**Usuario**: Diego Cutignola + equipo
**Problemas reportados**: 3

---

## 🔴 Problema 1: Permisos de Usuario - yhernandez@estudionc.com.ar

### Síntoma
Diego puede renombrar archivos, pero **otros usuarios no**:
- Carga la carpeta correctamente
- Registra en el log
- Pero **NO modifica ningún archivo**

### Causa Raíz
**OAuthSecurityManager con whitelist de dominios**

Ubicación: `services/api-server/src/main.py:214-218`

```python
allowed_domains = get_secret("oauth-allowed-domains").split(",")
oauth_manager = OAuthSecurityManager(
    client_id=oauth_client_id,
    allowed_domains=[d.strip() for d in allowed_domains if d.strip()],
    require_domain_match=True  # ← ESTE ES EL PROBLEMA
)
```

### Qué Pasó
1. Usuario `yhernandez@estudionc.com.ar` intenta renombrar
2. API Server valida su token con `verify_token()` ✅
3. API Server llama a `is_authorized()` (línea 131-163 de oauth_security.py)
4. Si el dominio `estudionc.com.ar` NO está en `allowed_domains` → **403 Forbidden**
5. Request nunca llega al Worker, por lo tanto no se renombran archivos

### Verificación Necesaria
Ejecutar en Google Cloud Console:

```bash
# Ver secret oauth-allowed-domains
gcloud secrets versions access latest --secret="oauth-allowed-domains" --project="cloud-functions-474716"
```

### Solución
**Opción A**: Agregar dominio a whitelist
```bash
# Actualizar el secret
gcloud secrets versions add oauth-allowed-domains --data-file=- --project="cloud-functions-474716" <<< "estudionc.com.ar,cenf.com.ar,otrodominio.com"
```

**Opción B**: Usar emails específicos (más seguro)
```python
# Modificar código en api-server/src/main.py para agregar allowed_emails
allowed_emails = get_secret("oauth-allowed-emails").split(",")
oauth_manager = OAuthSecurityManager(
    client_id=oauth_client_id,
    allowed_domains=[d.strip() for d in allowed_domains if d.strip()],
    allowed_emails=[e.strip() for e in allowed_emails if e.strip()],  # ← AGREGAR ESTO
    require_domain_match=True
)
```

**Opción C**: Deshabilitar domain matching (NO RECOMENDADO)
```python
require_domain_match=False  # Cualquier usuario de Google puede usar la app
```

### Recomendación
**Opción B** - Crear whitelist de emails específicos para mayor seguridad.

---

## ✅ SOLUCIONADO - 13 Abril 2026

### Problema Detectado
El dominio en la whitelist era **incorrecto**:
- Usuario: yhernandez@**estudionc**.com.ar
- Whitelist tenía: estudio**nc**.com.ar (faltaba letra "O")

### Solución Aplicada
**Opción A ejecutada**: Agregar dominio correcto a whitelist

```bash
# Secret actualizado de:
estudioanc.com.ar,gmail.com

# A:
estudioanc.com.ar,estudionc.com.ar,gmail.com

# Secret versión 5 creada
```

### Cambios Adicionales
- **API Server redeploy** requerido para recargar Secret Manager
- Deploy iniciado: 13 Abril 2026 15:22 UTC

### Estado Actual
- ✅ Dominio agregado a whitelist
- ⏳ API Server redeploy en progreso
- 🧪 Pendiente: Test con usuario yhernandez@estudionc.com.ar

### Próximos Pasos
1. Verificar que API Server deploy termine exitosamente
2. Test con usuario yhernandez@estudionc.com.ar
3. Verificar que puede renombrar archivos
4. Si falla, revisar permisos de carpeta en Google Drive

---

## 🟡 Problema 2: Procesamiento Parcial - Archivos Parcialmente Renombrados

### Síntoma
- Dos carpetas procesadas en simultáneo (solapadas)
- Ambas quedaron **parcialmente renombradas**
- Algunos archivos sí se renombraron, otros no
- Diego: "iniciamos dos procesos a la vez, capaz eso influyó"

### Causa Raíz
**Posibles causas (necesito logs para confirmar)**:

1. **Token Expira Durante Procesamiento**
   - Access tokens duran ~60 minutos
   - Si el folder tiene MUCHOS archivos, el token puede expirar
   - Archivos después de la expiración fallan con 401

2. **Google API Rate Limiting**
   - Drive API tiene límites de requests por segundo
   - Demasiados requests seguidos → 429 Too Many Requests
   - Worker no tiene retry logic con exponential backoff

3. **Error en Archivos Específicos**
   - Algunos archivos pueden estar corruptos
   - Algunos pueden tener permisos diferentes
   - try-except catchea error por archivo pero continúa

### Código Problemático
Ubicación: `services/worker-renombrador/src/main.py:505-598`

```python
def process_folder_files(...):
    for file in files:
        try:
            # Procesar archivo
            download_file(...)
            rename_file(...)
            stats["files_renamed"] += 1
        except Exception as e:
            logger.error(f"Error processing file {file['name']}: {e}")
            stats["errors"] += 1
            # ← CONTINÚA CON SIGUIENTE ARCHIVO
```

### Solución Propuesta
**Agregar refresh de token + retry logic**:

```python
def process_folder_files(...):
    for file in files:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Verificar si token está por expirar
                if time.time() - token_start_time > 3000:  # 50 minutos
                    logger.warning("Token near expiration, refreshing...")
                    # Refresh token si es posible, o fallar gracefully
                
                download_file(...)
                rename_file(...)
                stats["files_renamed"] += 1
                break  # ← Success, salir del retry loop
                
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Error processing file {file['name']}: {e}")
                    stats["errors"] += 1
                else:
                    logger.warning(f"Retry {attempt+1}/{max_retries} for {file['name']}")
                    time.sleep(2 ** attempt)  # Exponential backoff
```

### Verificación Necesita
**LOGS CRÍTICOS** - Buscar en logs del Worker:

```bash
# Buscar errores de renombrado
gcloud logging read "
  resource.type=cloud_run_revision AND 
  resource.labels.service_name=renombradorarchivosgdrive-worker-v2 AND
  jsonPayload.message:'Error processing file'
" --project="cloud-functions-474716" --limit=100 --freshness=48h
```

**Qué buscar**:
- ¿Hay errores 401/403? → Token expira
- ¿Hay errores 429? → Rate limiting
- ¿Qué archivos fallaron específicamente?
- ¿A qué hora del proceso empezaron a fallar?

### Recomendación
1. **Verificar logs** primero para confirmar causa raíz
2. **Si es token expiration**: Agregar token refresh logic
3. **Si es rate limiting**: Agregar exponential backoff
4. **Si es error específico**: Investigar archivos específicos

---

## 🟢 Problema 3: Audit Status Nunca Cambia de "Submitted"

### Síntoma
- Jobs siempre muestran status "submitted"
- Nunca cambian a "processing" → "completed" o "failed"
- Diego quiere: "submitted en verde cuando termine"

### Causa Raíz
**El código para actualizar status SÍ existe**, pero puede que:
1. No se esté ejecutando (error en try-except)
2. `executions_manager.update()` está fallando silenciosamente
3. Frontend no está actualizando después del status change

### Código Existente
Ubicación: `services/worker-renombrador/src/main.py:895-914`

```python
# Update to "processing"
try:
    executions_manager.update("id", task.execution_id, {"status": "processing"})
    logger.info(f"Execution {task.execution_id} status updated: processing")
except Exception as e:
    logger.warning(f"Failed to update execution status (non-fatal): {e}")

# Update to "completed" or "failed"
try:
    executions_manager.update("id", task.execution_id, {
        "status": "completed" if result.get("status") == "success" else "failed",
        "details": f"Processed {result.get('stats', {}).get('renamed', 0)} files. Folder: {task.folder_id}"
    })
except Exception as e:
    logger.warning(f"Failed to update execution status (non-fatal): {e}")
```

### Posibles Problemas

1. **Silent Failure**: El `try-except` catchea errores pero solo loguea warning
2. **executions_manager no está inicializado**: Supabase connection issue?
3. **Frontend no polling**: UI no consulta actualizaciones de status

### Solución Propuesta

**Paso 1**: Verificar si se está actualizando en Supabase
```sql
-- Consultar en Supabase SQL Editor
SELECT * FROM job_executions 
WHERE timestamp >= '2026-04-10' 
ORDER BY timestamp DESC 
LIMIT 20;
```

**Paso 2**: Agregar más logging forzado
```python
logger.info(f"🔄 ATTEMPTING status update to 'processing' for {task.execution_id}")
try:
    result = executions_manager.update("id", task.execution_id, {"status": "processing"})
    logger.info(f"✅ Status updated successfully: {result}")
except Exception as e:
    logger.error(f"❌ FAILED to update status: {e}", exc_info=True)
    logger.error(f"executions_manager type: {type(executions_manager)}")
```

**Paso 3**: Implementar frontend polling
```typescript
// En Angular component
setInterval(() => {
  this.loadJobExecutions(); // Recargar ejecuciones cada 30 segundos
}, 30000);
```

**Paso 4**: Color verde para completed
```typescript
// En UI template
<span [class.green]="execution.status === 'completed'">
  {{ execution.status }}
</span>
```

### Exportar Logs a TXT

**Nueva feature solicitada por Diego**:

```python
# Endpoint para exportar logs
@app.get("/api/v1/executions/{execution_id}/logs")
async def export_execution_logs(execution_id: str):
    execution = executions_manager.find("id", execution_id)[0]
    
    # Generar TXT con logs del job
    log_content = f"""
=== LOG DE EJECUCIÓN ===
ID: {execution['id']}
Fecha: {execution['timestamp']}
Usuario: {execution['user_email']}
Folder: {execution['folder_id']}
Status: {execution['status']}
Detalles: {execution.get('details', 'N/A')}

=== ARCHIVOS PROCESADOS ===
{execution.get('files_processed', 'N/A')}

=== ARCHIVOS RENOMBRADOS ===
{execution.get('files_renamed', 'N/A')}

=== ERRORES ===
{execution.get('errors', 'N/A')}
"""
    
    from fastapi.responses import Response
    return Response(
        content=log_content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=logs_{execution_id}.txt"}
    )
```

---

## 🎯 Prioridades de Solución

### 🔴 CRÍTICA - Problema 1 (Permisos)
**Impacto**: Usuarios NO pueden usar el sistema
**Tiempo estimado**: 30 minutos
**Solución**: Agregar `estudionc.com.ar` a whitelist de dominios

### 🟡 MEDIUM - Problema 2 (Procesamiento Parcial)
**Impacto**: Renombrado incompleto, mala UX
**Tiempo estimado**: 2-4 horas (depende de causa raíz)
**Solución**: 
1. Verificar logs primero (30 min)
2. Agregar retry logic (2-3 horas)

### 🟢 LOW - Problema 3 (Audit Status + Export Logs)
**Impacto**: UX menor, difícil de debuggear
**Tiempo estimado**: 2 horas
**Solución**:
1. Verificar Supabase (30 min)
2. Agregar polling frontend (1 hora)
3. Agregar export logs (30 min)

---

## 📊 Logs Necesarios Para Diagnosticar

Por favor, exportar estos logs a archivos JSON:

### 1. Logs del Worker (Últimas 48 horas)
```bash
gcloud logging read "
  resource.type=cloud_run_revision AND 
  resource.labels.service_name=renombradorarchivosgdrive-worker-v2 AND
  timestamp>=\"2026-04-10T00:00:00Z\"
" --project="cloud-functions-474716" --limit=200 --format=json > worker-logs-april10.json
```

### 2. Logs del API Server (Errores 403)
```bash
gcloud logging read "
  resource.type=cloud_run_revision AND 
  resource.labels.service_name=renombradorarchivosgdrive-api-server-v2 AND
  httpRequest.status>=400
" --project="cloud-functions-474716" --limit=100 --format=json > api-server-errors.json
```

### 3. Logs con "yhernandez" o "estudionc"
```bash
gcloud logging read "
  resource.type=cloud_run_revision AND
  jsonPayload.message:'yhernandez'
" --project="cloud-functions-474716" --limit=50 --format=json > user-yhernandez-logs.json
```

---

## ✅ Next Steps

1. **Verificar whitelist de dominios** en Secret Manager
2. **Exportar logs** del Worker para diagnosticar procesamiento parcial
3. **Verificar Supabase** para ver si status se está actualizando
4. **Priorizar**: Problema 1 (permisos) > Problema 2 (parcial) > Problema 3 (audit)

¿Podés pasarme los logs cuando los tengas? Con los logs puedo dar soluciones más precisas.
