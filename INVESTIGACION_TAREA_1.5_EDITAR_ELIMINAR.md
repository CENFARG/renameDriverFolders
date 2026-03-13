# 🔍 INVESTIGACIÓN: Tarea 1.5 - Arreglar Editar/Eliminar Algoritmo
## Proyecto Renombrador (#amBotHsOS) - V3.1.2

---

## 📋 RESUMEN EJECUTIVO

**Fecha de Investigación:** 13 de Marzo, 2026
**Investigador:** Claude (AI Assistant)
**Estado:** 🟡 EN PROGRESO - Análisis de código completado

---

## 🎯 PROBLEMA REPORTADO

Al editar o eliminar un algoritmo, tira error.

---

## ✅ VERIFICACIONES REALIZADAS

### 1. Endpoints de API ✅
**Archivo:** `services/api-server/src/main.py`

**Endpoints encontrados:**
- ✅ `GET /api/v1/jobs` (línea 715) - Listar jobs
- ✅ `POST /api/v1/jobs` (línea 760) - Crear job
- ✅ `GET /api/v1/jobs/{job_id}` (línea 784) - Obtener job
- ✅ `PUT /api/v1/jobs/{job_id}` (línea 802) - **Actualizar job**
- ✅ `DELETE /api/v1/jobs/{job_id}` (línea 828) - **Eliminar job**

**Conclusión:** ✅ Los endpoints EXISTEN y están correctamente implementados.

---

### 2. Código del Frontend ✅
**Archivo:** `services/frontend/src/app/app.component.ts`

**Funciones encontradas:**
- ✅ `editJob(job)` (línea 264) - Carga job para editar
- ✅ `saveJob()` (línea 279) - Guarda cambios (update o create)
- ✅ `deleteJob(id)` (línea 297) - Elimina job

**Conclusión:** ✅ El código del frontend está correctamente implementado.

---

### 3. API Service ✅
**Archivo:** `services/frontend/src/app/services/api.service.ts`

**Métodos encontrados:**
- ✅ `getJob(id)` (línea 53) - GET individual
- ✅ `updateJob(id, job)` (línea 67) - PUT con headers
- ✅ `deleteJob(id)` (línea 76) - DELETE con headers

**Conclusión:** ✅ El API service está correctamente implementado.

---

## 🔍 ANÁLISIS DE POSIBLES CAUSAS

### Causa 1: Validación de IDs en Backend ⚠️

**Código en línea 813 del backend:**
```python
if job_config.id != job_id:
    raise HTTPException(status_code=400, detail="Path ID and body ID mismatch")
```

**Problema:**
Si el frontend envía un ID en el body que no coincide con el ID en la URL, falla con 400.

**Validador de IDs (línea 322-326):**
```python
@validator('id', 'source_folder_id')
def validate_ids(cls, v):
    if v != "DYNAMIC" and not re.match(r'^[a-zA-Z0-9_-]{5,50}$', v):
        raise ValueError(f'Invalid ID format: {v}')
    return v
```

**Problema:**
Si el ID no cumple con el regex `^[a-zA-Z0-9_-]{5,50}$`, falla con 422.

---

### Causa 2: Campos Faltantes en Body ⚠️

**JobConfig model (línea 310-320):**
```python
class JobConfig(BaseModel):
    id: str                      # REQUIRED
    name: str                    # REQUIRED
    description: Optional[str] = ""
    active: bool = True
    trigger_type: str = "manual"
    schedule: Optional[str] = None
    source_folder_id: str        # REQUIRED
    target_folder_names: list[str] = ["Procesados"]
    agent_config: AgentConfig    # REQUIRED
```

**Problema:**
Si el frontend no envía todos los campos REQUIRED, falla con 422.

---

### Causa 3: Problemas con Supabase/JSON ⚠️

**Código update (línea 816):**
```python
db_manager.update("id", job_id, job_config.dict())
```

**Problema:**
Si db_manager no está conectado a Supabase correctamente, el update falla silenciosamente.

---

## 🧪 PLAN DE TESTING

### Paso 1: Verificar Logs de Error
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=renombradorarchivosgdrive-api-server-v2 AND httpRequest.requestUrl CONTAINS '/api/v1/jobs/' AND (httpRequest.requestMethod='PUT' OR httpRequest.requestMethod='DELETE') AND severity>=ERROR" --project=cloud-functions-474716 --limit=20 --freshness=7d
```

### Paso 2: Probar Manualmente con curl
```bash
# Test UPDATE
curl -X PUT https://api-server-url/api/v1/jobs/test-job-id \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-job-id",
    "name": "Test Job Updated",
    "description": "Test",
    "active": true,
    "trigger_type": "manual",
    "source_folder_id": "test_folder_id",
    "target_folder_names": ["Procesados"],
    "agent_config": {
      "model": {"name": "gemini-2.5-flash", "temperature": 0.1, "max_tokens": 4096},
      "instructions": "Test",
      "prompt_template": "Test",
      "filename_format": "test"
    }
  }'

# Test DELETE
curl -X DELETE https://api-server-url/api/v1/jobs/test-job-id \
  -H "Authorization: Bearer <TOKEN>"
```

### Paso 3: Verificar Response de getJob()
```bash
curl -X GET https://api-server-url/api/v1/jobs/test-job-id \
  -H "Authorization: Bearer <TOKEN>" | jq .
```

---

## 📋 PRÓXIMOS PASOS

1. **Buscar logs de error reales** para ver qué está fallando
2. **Verificar que el job cargado por getJob() tiene todos los campos necesarios**
3. **Probar manualmente** con un job de prueba
4. **Corregir el problema** una vez identificado

---

**Documento Creado:** 13 de Marzo, 2026
**Versión:** 1.0
