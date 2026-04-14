# Quick Reference - RenameDriverFolders

**Para OpenCode y trabajo continuado**

---

## 🚀 Comandos de Deploy

### Worker (OAuth Fix)
```bash
cd C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders
gcloud builds submit --config="services/worker-renombrador/cloudbuild.yaml" \
  --project="cloud-functions-474716" \
  --region="us-central1"
```

### API Server
```bash
cd C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders
gcloud builds submit --config="services/api-server/cloudbuild.yaml" \
  --project="cloud-functions-474716" \
  --region="us-central1"
```

### Frontend
```bash
cd C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders
gcloud builds submit --config="services/frontend/cloudbuild.yaml" \
  --project="cloud-functions-474716" \
  --region="us-central1"
```

---

## 📊 Logs y Debugging

### Ver Logs Recientes (Worker)
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=renombradorarchivosgdrive-worker-v2" \
  --project="cloud-functions-474716" \
  --limit=50 \
  --freshness=1h \
  --format="table(timestamp,severity,jsonPayload.message)"
```

### Ver Logs Recientes (API Server)
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=renombradorarchivosgdrive-api-server-v2" \
  --project="cloud-functions-474716" \
  --limit=50 \
  --freshness=1h \
  --format="table(timestamp,severity,jsonPayload.message)"
```

### Ver Código Deployado
```bash
curl https://renombradorarchivosgdrive-worker-v2-702567224563.us-central1.run.app/debug/code | python -m json.tool
```

### Ver Revisión Actual
```bash
gcloud run services describe renombradorarchivosgdrive-worker-v2 \
  --project="cloud-functions-474716" \
  --region="us-central1" \
  --format="value(status.latestReadyRevisionName)"
```

---

## 📁 Paths Importantes

### Proyecto
```
C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders
```

### Archivos Críticos
```
services/worker-renombrador/src/main.py           # Worker principal
services/api-server/src/main.py                   # API Server principal
services/frontend/src/app/app.component.ts        # Frontend OAuth config
services/worker-renombrador/Dockerfile.build      # Docker Worker
services/worker-renombrador/cloudbuild.yaml       # Build config Worker
scripts/create_and_insert_algorithms.sql          # Database schema
logs/downloaded-logs-20260331-130314.json        # Último error log
```

### Configuración
```
memory/user_profile.md                 # Perfil de usuario
OPENCODE_HANDOVER.md                   # Documento principal
TASKS_STATUS.md                        # Estado de tareas
QUICK_REFERENCE.md                     # Este archivo
```

---

## 🔐 Endpoints Importantes

### Worker
- **Health**: `https://renombradorarchivosgdrive-worker-v2-.../health`
- **Run Task**: `https://renombradorarchivosgdrive-worker-v2-.../run-task`
- **Debug Code**: `https://renombradorarchivosgdrive-worker-v2-.../debug/code`

### API Server
- **Base**: `https://renombradorarchivosgdrive-api-server-v2-...`
- **Algorithms**: `/api/v1/algorithms`
- **Manual Job**: `/api/v1/jobs/manual`
- **Scheduled Job**: `/api/v1/jobs/scheduled`

### Frontend
- **App**: `https://renombradorarchivosgdrive-frontend-v2-...`

---

## 🧪 Testing

### Folder Problemático
```
ID: 1JD-53D0ONkRvyqW9TbquA9Z15Z8WyKLH
Usuario: gonzalo.f.recalde@gmail.com
Archivos: 3 archivos PDF
```

### Pasos de Test
1. Abrir Frontend
2. Click en "Elegir Carpeta"
3. Seleccionar folder con Google Picker
4. Seleccionar algoritmo (opcional)
5. Click en "Procesar"
6. Verificar que se renombran archivos

### Success Criteria
- ✅ No error 401/403
- ✅ No "Refreshing credentials"
- ✅ Archivos renombrados
- ✅ Status = "completed"

---

## 🗄️ Database (Supabase)

### Conectar
```bash
# URL: https://app.supabase.com
# Project: cloud-functions-474716
# Tables: jobs, job_executions, document_algorithms
```

### Queries Útiles
```sql
-- Ver jobs recientes
SELECT * FROM job_executions ORDER BY timestamp DESC LIMIT 10;

-- Ver algorithms
SELECT * FROM document_algorithms WHERE is_active = true;

-- Ver ejecuciones fallidas
SELECT * FROM job_executions WHERE status = 'failed';
```

---

## 🔧 Troubleshooting

### Error: "Refreshing credentials due to a 401"
**Significa**: google_auth_httplib2 está intentando refresh
**Solución**: Verificar que Worker usa `TokenInjectorRequest`
**Deploy**: Revisión 00051-qqr o posterior

### Error: "credentials do not contain necessary fields"
**Significa**: OAuthCredentials intenta refresh sin refresh_token
**Solución**: Usar `oauth2_credentials.Credentials` con `expiry=None`

### Error: "relation does not exist"
**Significa**: Table no existe en Supabase
**Solución**: Ejecutar `scripts/create_and_insert_algorithms.sql`

### Error: "App not verified" popup
**Significa**: Google OAuth app no verificado
**Solución**: Normal en desarrollo, considerar organización Google Workspace

---

## 📞 Contacto y Soporte

### Usuario
- **Nombre**: Gonzalo Recalde
- **Email**: gonzalo.f.recalde@gmail.com
- **Idioma**: Español (voseo)
- **Nivel**: Senior Developer

### Session
- **ID**: #C0001#P0007+renameDriverFolders
- **Fecha**: 31 Marzo 2026
- **Estado**: OAuth fix implementado, pendiente deploy

### Ayuda
- **Doc Principal**: `OPENCODE_HANDOVER.md`
- **Tasks**: `TASKS_STATUS.md`
- **Profile**: `memory/user_profile.md`

---

## ✅ Checklist para Deploy

Antes de hacer deploy:
- [ ] Verificar que código es correcto
- [ ] Leer archivo modificado
- [ ] Confirmar que Dockerfile tiene .pyc cleanup
- [ ] Confirmar que cloudbuild.yaml tiene --no-cache
- [ ] Tener logs del último error a mano

Después de deploy:
- [ ] Verificar número de revisión
- [ ] llamar `/debug/code` endpoint
- [ ] Verificar que código es correcto
- [ ] Testear con folder problemático

Antes de avisar al usuario:
- [ ] Verificar que NO hay errors en logs
- [ ] Confirmar que archivos se renombran
- [ ] Tener evidencia (logs, screenshots)
- [ ] Preparar explicación técnica

---

## 🎯 Quick Tips

### Comunicación con Usuario
- Usar "vos" no "tú"
- Ser directo: "Fantástico, funcionó" no "Creo que funcionó"
- Explicar technical porqué
- No usar sarcasmo

### Debugging
- Leer PRIMERO el log completo
- Buscar "Refreshing credentials" → OAuth problem
- Buscar "Error listing files" → Permissions problem
- Buscar "401" or "403" → Auth problem

### Deployments
- Siempre verificar número de revisión
- Usar `/debug/code` para confirmar código
- No asumir que deploy funcionó
- Testear en producción con datos reales

### Código
- Leer archivo ANTES de editar
- Verificar que edit es correcto
- No hacer cambios innecesarios
- Mantener logging extensivo

---

**Última actualización**: 31 de Marzo 2026
**Próxima acción**: Deploy Worker revisión 00051-qqr y testear
**Success**: Usuario confirma que funciona con folder problemático
