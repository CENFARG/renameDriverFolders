# Estado de Tareas - RenameDriverFolders

**Actualizado**: 31 de Marzo 2026
**Session**: #C0001#P0007+renameDriverFolders

---

## 🔴 TAREAS CRÍTICAS - Pendientes

### 1. Deploy Worker Revisión 00051-qqr ⏳
**Estado**: Código implementado, NO deployado
**Prioridad**: CRÍTICA

**Acción**:
```bash
cd C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders
gcloud builds submit --config="services/worker-renombrador/cloudbuild.yaml" \
  --project="cloud-functions-474716" \
  --region="us-central1"
```

**Qué hace**: Deploya fix de inyección manual de Bearer token

**Esperado**: Worker ya no intenta refresh automático en 401

---

### 2. Test OAuth Fix con Folder Problemático 🧪
**Estado**: Pendiente deploy
**Prioridad**: CRÍTICA

**Test Folder**: `1JD-53D0ONkRvyqW9TbquA9Z15Z8WyKLH`
**Usuario**: gonzalo.f.recalde@gmail.com

**Pasos**:
1. Ir a Frontend: `https://renombradorarchivosgdrive-frontend-v2-...`
2. Seleccionar folder con Google Picker
3. Ejecutar job manual
4. Verificar que se renombran archivos

**Success Criteria**:
- ✅ No error "Refreshing credentials due to a 401"
- ✅ No error "credentials do not contain necessary fields"
- ✅ Archivos se renombran correctamente
- ✅ Status cambia de "submitted" a "completed"

---

## 🟡 TAREAS MEDIUM - Parcialmente Resueltas

### 3. Fix Audit Status Updates ⚠️
**Estado**: Fix existe en código pero parece no ejecutarse
**Prioridad**: MEDIUM

**Ubicación**: `services/worker-renombrador/src/main.py:833-837`

**Código**:
```python
if task.execution_id:
    executions_manager.update("id", task.execution_id, {
        "status": "completed" if result.get("status") == "success" else "failed",
        "details": f"Processed {result.get('stats', {}).get('renamed', 0)} files. Folder: {task.folder_id}"
    })
```

**Problema**: Jobs quedan stuck en "submitted"

**Investigar**:
- ¿Está llegando a este código?
- ¿Hay error en el update?
- ¿Es problema de Supabase?

---

### 4. Google Picker "App Not Verified" Popup ⚠️
**Estado**: Conocido, no prioridad alta
**Prioridad**: LOW

**Problema**: Muestra popup de verificación de Google

**Solución**: Considerar deployment como organización Google Workspace

**Impacto**: UX negativo pero no bloquea funcionalidad

---

## 🟢 TAREAS COMPLETED ✅

### 5. OAuth Scope Fix ✅
**Archivo**: `services/frontend/src/app/app.component.ts:104`
**Cambio**: `drive.readonly` → `drive`
**Deploy**: Revisión 00034-zvf

---

### 6. Database Algorithms Creation ✅
**Archivo**: `scripts/create_and_insert_algorithms.sql`
**Estado**: Ejecutado en Supabase
**Resultado**: 6 algoritmos creados

---

### 7. API Algorithms Endpoint ✅
**Archivo**: `services/api-server/src/main.py:601-622`
**Fix**: Removido parámetro inválido `supabase_client`
**Deploy**: Revisión 00049-m97

---

### 8. Docker Build Cache Fix ✅
**Archivos**:
- `Dockerfile.build:28-32` - .pyc cleanup
- `cloudbuild.yaml:5` - --no-cache flag
**Deploy**: Revisión 00051-qqr (pendiente ejecutar deploy)

---

### 9. Diagnostic Endpoint ✅
**Archivo**: `services/worker-renombrador/src/main.py:720-730`
**Función**: `/debug/code` retorna código fuente desplegado
**Verificación**: Confirmó que código era correcto

---

### 10. OAuth Credentials Function ✅
**Archivo**: `services/worker-renombrador/src/main.py:240-270`
**Función**: `get_user_credentials()` con `oauth2_credentials.Credentials`
**Deploy**: Revisión 00051-qqr (pendiente ejecutar deploy)

---

### 11. Old Service Cleanup ✅
**Acción**: Eliminado `worker-renombrador` en us-east1
**Estado**: Completado

---

### 12. User Credentials Payload ✅
**Archivo**: `services/api-server/src/main.py:754-772`
**Función**: API Server pasa `user_credentials` en payload
**Deploy**: Revisión 00049-m97

---

## 📋 TAREAS LOW - Futuras

### 13. Scheduled Jobs UI Improvement 📅
**Problema**: Usuario pide date/time picker user-friendly
**Actual**: Usa formato CRON
**Prioridad**: LOW - funcionalidad básica funciona

**Idea**: Reemplazar input CRON con datetime-local picker

---

### 14. Extension Context Invalidated Error 🔌
**Problema**: Browser error en consola
**Contexto**: Chrome extension development
**Prioridad**: LOW - no afecta funcionalidad principal

---

## 🎯 Next Steps for OpenCode

### Inmediato (Hoy)
1. **Deploy Worker** con revisión 00051-qqr
2. **Test** con folder `1JD-53D0ONkRvyqW9TbquA9Z15Z8WyKLH`
3. **Verificar logs** para confirmar que no hay auto-refresh
4. **Confirmar** con usuario que archivos se renombran

### Corto Plazo (Esta Semana)
1. **Investigar** audit status updates si sigue fallando
2. **Considerar** solución para Google Picker verification
3. **Documentar** flujo completo de OAuth para futuros devs

### Medio Plazo (Próximo Sprint)
1. **Implementar** scheduled jobs UI mejorada
2. **Investigar** extension context error
3. **Optimizar** Docker build process

---

## 📊 Métricas de Éxito

### OAuth Fix Success
- [ ] Worker deploya sin errores
- [ ] Test con folder problemático funciona
- [ ] Logs muestran: "✅ Drive service built successfully (manual token injection)"
- [ ] NO logs de "Refreshing credentials due to a 401"
- [ ] Usuario confirma: "Fantástico, funciona"

### Audit Status Success
- [ ] Jobs cambian de "submitted" → "processing" → "completed"
- [ ] job_executions table se actualiza correctamente
- [ ] UI muestra status actualizado en tiempo real

### Overall Success
- [ ] Usuario puede renombrar archivos sin intervención manual
- [ ] Sistema funciona con sus propias credenciales OAuth
- [ ] No hay errores de autenticación en logs
- [ ] Performance aceptable (< 30s por folder)

---

## 🆘 Help & Debugging

### Si OAuth Fix Falla
1. **Verificar deploy**: ¿Es realmente revisión 00051-qqr?
2. **Verificar código**: Usar `/debug/code` endpoint
3. **Verificar logs**: Buscar "Building Drive service with custom HTTP transport"
4. **Verificar token**: Logs muestran "Access token: eyJh..."?

### Si Audit Status No Actualiza
1. **Verificar Supabase**: ¿Table job_executions existe?
2. **Verificar permissions**: ¿API tiene write access?
3. **Verificar logs**: ¿Hay error en update operation?
4. **Verificar UI**: ¿Está polling for updates?

### Si Deploy Falla
1. **Verificar cloudbuild.yaml**: ¿Formato YAML correcto?
2. **Verificar Dockerfile**: ¿Sintaxis correcta?
3. **Verificar permissions**: ¿Tienes permisos de Cloud Build?
4. **Verificar quota**: ¿Has alcanzado límite de builds?

---

## 📞 Contact

**Usuario**: gonzalo.f.recalde@gmail.com
**Session**: #C0001#P0007+renameDriverFolders
**Project**: renameDriverFolders
**Path**: `C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders`

**Para más contexto**: Ver `OPENCODE_HANDOVER.md` y `memory/user_profile.md`
