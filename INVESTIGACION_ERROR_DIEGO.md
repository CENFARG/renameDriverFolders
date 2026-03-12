# 🔍 INVESTIGACIÓN: Error con Cliente Diego - Tarea 1.1
## Proyecto Renombrador (#amBotHsOS) - V3.1.2

---

## 📋 RESUMEN EJECUTIVO

**Fecha de Investigación:** 12 de Marzo, 2026
**Investigador:** Claude (AI Assistant) + Gonzalo (Orquestador)
**Estado:** 🟡 EN PROGRESO - Requiere más información del cliente

---

## 🎯 PROBLEMA REPORTADO

**Síntoma Principal:**
- ✅ Gonzalo (@gmail.com) puede: Enviar carpeta → Sistema renombra archivos correctamente
- ❌ Diego (@estudioanc.com.ar) NO puede: Enviar carpeta → Sistema NO renombra archivos

**Problema Adicional:**
- Los renombrados no se ven en el dashboard de auditoría
- Solo se pueden ver yendo manualmente a la carpeta de Drive

**Último Error Conocido:**
- Error 400 relacionado con email/dominio (según reporte del cliente)

---

## ✅ VERIFICACIONES REALIZADAS

### 1. Configuración de OAuth Dominios ✅
```bash
# Secreto verificado: oauth-allowed-domains
Resultado: estudioanc.com.ar,gmail.com
```
**Conclusión:** ✅ El dominio `@estudioanc.com.ar` ESTÁ en la whitelist. NO es el problema.

### 2. Código de OAuth Security ✅
**Archivo:** `packages/core-renombrador/src/core_renombrador/oauth_security.py`

**Análisis:**
- ✅ Validación de token implementada correctamente
- ✅ Verificación de dominio funciona como esperado
- ✅ Rate limiting configurado (10 req/min)
- ✅ Manejo de errores robusto

**Conclusión:** ✅ El código de OAuth está bien implementado. NO es el problema.

### 3. Validación de Folder ID ✅
**Archivo:** `services/api-server/src/main.py` (líneas 277-282)

**Análisis:**
```python
@validator('folder_id')
def validate_folder_id(cls, v):
    # Relaxed logic: Google Drive IDs are alphanumeric with - and _
    if not re.match(r'^[a-zA-Z0-9_-]+$', v):
        raise ValueError('Invalid folder_id format')
    return v
```

**Conclusión:** ✅ La validación de folder_id es correcta. Acepta IDs de Google Drive válidos.

### 4. Logs de Google Cloud ✅
**Búsqueda realizada:**
```bash
# Logs de API Server (últimos 3 días)
# Logs de Worker (últimos 3 días)
# Búsqueda de errores 400
# Búsqueda de mención a "estudioanc"
```

**Resultado:** ❌ No se encontraron logs con:
- Error 400 específico
- Mención a @estudioanc.com.ar
- Errores de autenticación recientes

**Conclusión:** ⚠️ Los logs no muestran el error. Puede ser que:
- El error es en el frontend (antes de llegar al API)
- Los logs se han purgado
- El error no está siendo logueado correctamente

---

## 🔍 HIPÓTESIS DE CAUSA RAÍZ

### Hipótesis 1: Error en el Frontend (Más Probable) 🎯

**Qué puede estar pasando:**
- El frontend NO está enviando el folder_id correctamente
- El frontend tiene un error de validación antes de enviar
- El Google Drive Picker de Diego retorna un formato diferente

**Evidencia que soporta esta hipótesis:**
- El usuario mencionó "error 400" que es un error de "Bad Request"
- Los logs del backend NO muestran el error
- Gonzalo (@gmail.com) funciona, lo que sugiere que el backend está bien

**Cómo verificar:**
- Revisar logs de la consola del navegador de Diego
- Verificar el código del frontend (app.component.ts)
- Capturar network requests desde el browser

---

### Hipótesis 2: Permisos de Google Drive (Menos Probable)

**Qué puede estar pasando:**
- Diego NO tiene permisos de escritura en su carpeta
- La carpeta de Diego está compartida con permisos limitados
- El OAuth token de Diego no tiene scope para Drive

**Evidencia que NO soporta esta hipótesis:**
- El dominio está whitelisteado correctamente
- El código de OAuth valida correctamente
- Si fuera un problema de permisos, veríamos un error 403, no 400

**Cómo verificar:**
- Verificar que Diego puede acceder a la carpeta manualmente
- Verificar los scopes del OAuth token
- Probar con una carpeta de prueba

---

### Hipótesis 3: Error de Validación de Input (Posible)

**Qué puede estar pasando:**
- El folder_id que Diego selecciona tiene caracteres inválidos
- El frontend envía el folder_id en un formato diferente
- Hay un error de encoding en el request

**Evidencia que soporta esta hipótesis:**
- El validador de folder_id usa un regex estricto
- Error 400 es típico de validación de input

**Cómo verificar:**
- Verificar qué folder_id está enviando el frontend
- Comparar con el folder_id que envía Gonzalo
- Verificar si hay caracteres especiales

---

## 📋 PRÓXIMOS PASOS RECOMENDADOS

### 🔴 PASO 1: Obtener Logs del Frontend (CRÍTICO)

**Acción Requerida del Cliente:**
1. Diego debe abrir la consola del browser (F12)
2. Ir a la pestaña "Console"
3. Intentar enviar un job
4. Capturar/screenshot cualquier error rojo
5. Ir a la pestaña "Network"
6. Buscar la request a `/api/v1/jobs/manual`
7. Capturar/screenshot:
   - URL de la request
   - Headers (Authorization)
   - Payload (folder_id, job_type)
   - Response (status code, body)

**Información Crítica Necesaria:**
- ¿Qué folder_id se está enviando?
- ¿Qué status code retorna el API?
- ¿Qué mensaje de error aparece?
- ¿Hay errores en la consola del browser?

---

### 🟡 PASO 2: Verificar el Código del Frontend

**Archivos a Revisar:**
```
services/frontend/src/app/app.component.ts
services/frontend/src/app/job.service.ts
```

**Qué Buscar:**
- Cómo se envía el folder_id
- Cómo se maneja el error
- Validaciones antes de enviar

---

### 🟢 PASO 3: Testing Controlado

**Plan de Testing:**
1. Crear una carpeta de prueba en Drive de Diego
2. Obtener el folder_id manualmente
3. Enviar request con curl:
```bash
curl -X POST https://renombradorarchivosgdrive-api-server-v2-.../api/v1/jobs/manual \
  -H "Authorization: Bearer <TOKEN_DE_DIEGO>" \
  -H "Content-Type: application/json" \
  -d '{"folder_id": "<FOLDER_ID>", "job_type": "generic"}'
```
4. Verificar respuesta

---

## ❓ PREGUNTAS PARA EL CLIENTE

1. **¿Cuándo fue la última vez que Diego probó?** (para buscar logs más específicos)

2. **¿Qué mensaje de error ve Diego exactamente?**
   - ¿En pantalla?
   - ¿En la consola del browser?
   - ¿En algún popup?

3. **¿Diego puede seleccionar la carpeta con Google Drive Picker?**
   - ¿Se abre el picker?
   - ¿Puede navegar?
   - ¿Puede seleccionar?

4. **¿Qué pasa después de hacer clic en "Procesar"?**
   - ¿Ve algún mensaje?
   - ¿El botón se queda en "loading"?
   - ¿Aparece algún error?

5. **¿Diego verificó manualmente la carpeta de Drive?**
   - ¿Los archivos aparecen renombrados?
   - ¿O no se renombran para nada?

---

## 💡 SOLUCIONES PROPUESTAS (Según Hipótesis)

### Solución 1: Si es Error del Frontend
```typescript
// Verificar que el frontend envíe correctamente el folder_id
submitJob() {
  const payload = {
    folder_id: this.selectedFolderId,  // Verificar que no sea null/undefined
    job_type: this.selectedJobType || 'generic'
  };

  console.log('Enviando payload:', payload);  // Debug log

  this.jobService.submitManualJob(payload).subscribe(...);
}
```

### Solución 2: Si es Error de Permisos
- Verificar que Diego tenga permisos de escritura en la carpeta
- Re-autenticar a Diego con scopes correctos:
```typescript
const scope = 'https://www.googleapis.com/auth/drive';
```

### Solución 3: Si es Error de Validación
- Relajar el validador de folder_id (aunque ya está relajado)
- Agregar mejor manejo de errores en el frontend

---

## 📊 IMPACTO

**Usuarios Afectados:** 1 (Diego @estudioanc.com.ar)
**Usuarios Funcionales:** 1 (Gonzalo @gmail.com)
**Tasa de Éxito:** 50%
**Severidad:** 🔴 ALTA (Cliente no puede usar el sistema)

---

## 🔄 ESTADO DE LA INVESTIGACIÓN

| Paso | Descripción | Estado |
|------|-------------|--------|
| 1 | Verificar configuración de dominios | ✅ Completado |
| 2 | Verificar código de OAuth | ✅ Completado |
| 3 | Verificar validación de folder_id | ✅ Completado |
| 4 | Buscar logs de Google Cloud | ✅ Completado |
| 5 | Obtener logs del frontend de Diego | ⏳ Pendiente - Requiere cliente |
| 6 | Verificar código del frontend | ⏳ Pendiente |
| 7 | Testing controlado con curl | ⏳ Pendiente |

---

## 📝 NOTAS PARA EL DESARROLLADOR

**Memoria Engram Guardada:**
- ID: #3
- Título: "Investigación Error Diego - Tarea 1.1"
- Progreso: Verificaciones backend completadas, requiere info de frontend

**Commit Relacionado:**
- No hay commit todavía (investigación en curso)

**Próxima Acción:**
Esperar respuesta del cliente con:
1. Logs de la consola del browser
2. Screenshot de Network request
3. Timestamp de cuando probó por última vez

---

**Documento Creado:** 12 de Marzo, 2026
**Versión:** 1.0
**Próxima Revisión:** Cuando se tenga información del cliente

---

*Este documento es parte de la investigación de la Tarea 1.1 del Implementation Plan*
