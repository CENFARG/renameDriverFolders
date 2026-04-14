# RenameDriverFolders - OpenCode Handover Document

**Fecha**: 31 de Marzo 2026
**Usuario**: gonzalo.f.recalde@gmail.com
**Session ID**: #C0001#P0007+renameDriverFolders
**Estado**: OAuth fix implementado, pendiente deploy y test

---

## 📋 Resumen Ejecutivo

Sistema de renombrado automático de documentos usando IA (Gemini) que opera sobre Google Drive del usuario. **Problema crítico**: OAuth user credentials flow fallaba con error de auto-refresh. **Solución implementada**: Inyección manual de Bearer token evitando `google_auth_httplib2.AuthorizedHttp`.

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐
│  Frontend       │  Angular + TypeScript
│  (Google Picker)│  OAuth scope: drive
└────────┬────────┘
         │ POST /api/v1/jobs/manual
         ↓
┌─────────────────┐
│  API Server     │  FastAPI (Python)
│  (OAuthSecurity) │  Valida access_token
└────────┬────────┘
         │ Cloud Tasks Queue
         ↓
┌─────────────────┐
│  Worker         │  Python + googleapiclient
│  (Process Docs) │  Inyecta Bearer token manualmente
└────────┬────────┘
         │ Drive API v3
         ↓
┌─────────────────┐
│  Google Drive   │  Archivos del usuario
│  (User Files)   │  Renombrado con permisos
└─────────────────┘
```

---

## 🔑 CRITICAL: OAuth Fix Implementado

### El Problema (3 niveles de profundidad)

**Nivel 1 - Scope Mismatch**:
- Frontend solicitaba `drive.readonly`
- Worker necesita `drive` para renombrar
- **Fix**: Cambiado en `services/frontend/src/app/app.component.ts` línea 104

**Nivel 2 - Credentials Class**:
- `OAuthCredentials` con auto-refresh vs `oauth2_credentials.Credentials` sin refresh
- **Fix**: Usar `oauth2_credentials.Credentials` con `expiry=None, token_uri=None`
- **Ubicación**: `services/worker-renombrador/src/main.py` líneas 240-270

**Nivel 3 - google_auth_httplib2 (CAUSA RAÍZ)**:
```python
# ❌ ESTO NO FUNCIONA - AuthorizedHttp SIEMPRE hace refresh en 401
authorized_http = google_auth_httplib2.AuthorizedHttp(credentials, http=http)
drive_service = build("drive", "v3", http=authorized_http)

# ✅ SOLUCIÓN - Inyectar token manualmente
class TokenInjectorRequest(HttpRequest):
    def add_credentials(self, credentials):
        self.headers['Authorization'] = f'Bearer {access_token}'

drive_service = build("drive", "v3", http=http,
                      requestBuilder=TokenInjectorRequest)
```

### Código del Fix

**Archivo**: `services/worker-renombrador/src/main.py` (líneas 273-299)

```python
def build_drive_service_with_credentials(credentials):
    """
    Build Drive service with custom HTTP request that injects Bearer token manually.

    CRITICAL: google_auth_httplib2.AuthorizedHttp ALWAYS attempts to refresh
    credentials on 401/403, regardless of how credentials are configured.

    Solution: Create custom HttpRequest that manually injects the Bearer token
    without using AuthorizedHttp at all.
    """
    import httplib2
    from googleapiclient.http import HttpRequest

    access_token = credentials.token
    http = httplib2.Http()

    class TokenInjectorRequest(HttpRequest):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def add_credentials(self, credentials):
            """Override to inject Bearer token manually without refresh logic."""
            self.headers['Authorization'] = f'Bearer {access_token}'

    drive_service = build("drive", "v3", http=http,
                          requestBuilder=TokenInjectorRequest)
    return drive_service
```

---

## 🚀 Próximos Pasos - ACCIÓN INMEDIATA

### 1. Deploy del Worker (PENDIENTE)

```bash
cd C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders
gcloud builds submit --config="services/worker-renombrador/cloudbuild.yaml" \
  --project="cloud-functions-474716" \
  --region="us-central1"
```

**Estado actual**: Revisión `00051-qqr` está en código fuente pero NO deployada

### 2. Test con Folder Problemático

**Folder ID**: `1JD-53D0ONkRvyqW9TbquA9Z15Z8WyKLH`

**Qué verificar:
1. Job se crea sin error 401
2. Archivos se renombran correctamente
3. No aparece "Refreshing credentials due to a 401 response" en logs

### 3. Verificación de Código Deployado

```bash
# Endpoint para verificar código que está corriendo
curl https://renombradorarchivosgdrive-worker-v2-702567224563.us-central1.run.app/debug/code
```

---

## 📁 Estructura del Proyecto

```
C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders\
│
├── services/
│   ├── frontend/                        # Angular UI
│   │   └── src/app/app.component.ts     # ✅ OAuth scope fix (line 104)
│   │
│   ├── api-server/                      # FastAPI backend
│   │   └── src/main.py                  # ✅ /api/v1/algorithms + user_credentials
│   │
│   └── worker-renombrador/              # Python Worker
│       ├── src/main.py                  # ✅ OAuth credentials + HTTP transport
│       ├── Dockerfile.build             # ✅ .pyc cleanup (lines 28-32)
│       └── cloudbuild.yaml              # ✅ --no-cache flag (line 5)
│
├── scripts/
│   └── create_and_insert_algorithms.sql # ✅ Supabase database schema
│
└── logs/
    └── downloaded-logs-20260331-130314.json # ❌ Error logs para debugging
```

---

## 🔧 Fixes Aplicados

### 1. OAuth Scope (Frontend)
- **Archivo**: `services/frontend/src/app/app.component.ts:104`
- **Cambio**: `drive.readonly` → `drive`
- **Deploy**: Revisión 00034-zvf ✅

### 2. Database Algorithms (API Server)
- **Archivo**: `services/api-server/src/main.py:601-622`
- **Fix**: Removido parámetro inválido `supabase_client`
- **Deploy**: Revisión 00049-m97 ✅

### 3. Docker Build Cache (Worker)
- **Archivos**:
  - `Dockerfile.build:28-32` - Agregado .pyc cleanup
  - `cloudbuild.yaml:5` - Agregado --no-cache flag
- **Deploy**: Revisión 00051-qqr ⏳ (PENDIENTE)

### 4. Manual Bearer Token Injection (Worker)
- **Archivo**: `services/worker-renombrador/src/main.py:273-299`
- **Fix**: Custom HttpRequest que inyecta token sin AuthorizedHttp
- **Deploy**: Revisión 00051-qqr ⏳ (PENDIENTE)

---

## 🗄️ Base de Datos (Supabase)

### Tables
1. **jobs** - Configuraciones de jobs (manual/scheduled)
2. **job_executions** - Logs de ejecución (audit trail)
3. **document_algorithms** - Algoritmos preconfigurados (6 registros)

### Algorithms Disponibles
1. Estudio Cutignola (IVA, Comprobantes)
2. Estudio LZ (Servicios, Legales)
3. Estudio MAS (Impuestos, Nómina)
4. Documentos Genéricos (Varios)
5. Estudio RECA (Contables, Impositivos)
6. IVA General (Compras, Ventas)

---

## ☁️ Infraestructura GCP

### Services Deployed (us-central1)
- **Frontend**: `renombradorarchivosgdrive-frontend-v2` (rev 00034-zvf)
- **API Server**: `renombradorarchivosgdrive-api-server-v2` (rev 00049-m97)
- **Worker**: `renombradorarchivosgdrive-worker-v2` (rev 00051-qqr ⏳)

### Resources
- **Project**: cloud-functions-474716
- **Region**: us-central1
- **Cloud Tasks Queue**: document-processing-queue
- **GCS Bucket**: renamedriverfolderbucket
- **Database**: Supabase (external)

### Environment Variables
```bash
GCP_PROJECT=cloud-functions-474716
GCP_LOCATION=us-central1
TASKS_QUEUE=document-processing-queue
WORKER_URL=https://renombradorarchivosgdrive-worker-v2-...
USE_SUPABASE=true
```

---

## 🐛 Problemas Conocidos

### 🔴 CRITICAL - Pendiente Resolución
- **Worker Deploy**: Revisión 00051-qqr NO está deployada
- **Test Folder**: `1JD-53D0ONkRvyqW9TbquA9Z15Z8WyKLH` sigue fallando
- **Error**: "Refreshing credentials due to a 401 response"

### 🟡 MEDIUM - Audit Status
- **Problema**: Jobs quedan stuck en "submitted" status
- **Fix en código**: Existe pero parece no ejecutarse
- **Ubicación**: `services/worker-renombrador/src/main.py:833-837`

### 🟢 LOW - Google Picker
- **Problema**: Muestra popup "App not verified"
- **Solución**: Considerar Google Workspace organization deployment

### 🟢 LOW - Scheduled Jobs UI
- **Problema**: Usuario pide date/time picker user-friendly
- **Actual**: Usa formato CRON (menos user-friendly)
- **Prioridad**: Baja - funcionalidad básica funciona

---

## 📊 Logs y Debugging

### Ver Logs Recientes
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=renombradorarchivosgdrive-worker-v2" \
  --project="cloud-functions-474716" \
  --limit=50 \
  --freshness=1h
```

### Ver Código Deployado
```bash
curl https://renombradorarchivosgdrive-worker-v2-702567224563.us-central1.run.app/debug/code
```

### Error Log File
- **Path**: `logs/downloaded-logs-20260331-130314.json`
- **Contenido**: Logs del último test fallido (16:02:27 UTC)

---

## 👤 Perfil del Usuario

### Comunicación
- **Idioma**: Español Rioplatense (voseo)
- **Tono**: Directo, técnico, sin "filler"
- **Prefiere**: Explicaciones profundas sobre soluciones superficiales
- **NO usar**: Sarcasmo, tono condescendiente

### Técnico
- **Nivel**: Senior Developer / Architect
- **Valora**: Root cause analysis, evidence-based debugging
- **Odio**: Cargo cult programming, solutions without understanding
- **OS**: Windows 11 con Git Bash
- **Email**: gonzalo.f.recalde@gmail.com

### Comandos que Usa
```bash
# Deploy
cd C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders
gcloud builds submit --config="services/worker-renombrador/cloudbuild.yaml"

# Logs
gcloud logging read "resource.type=cloud_run_revision..." --limit=50

# Git
git status
git diff
```

---

## 🔐 Security Considerations

### OAuth Tokens
- **Access Token**: Short-lived (~60 min)
- **Storage**: Solo en memoria del Worker
- **Transmission**: HTTPS entre servicios
- **Scope**: `drive` (no readonly) para poder renombrar

### Validation
- **API Server**: Valida token con `OAuthSecurityManager.verify_token()`
- **Email matching**: Verifica que token pertenezca al usuario autenticado
- **No refresh_token**: No se almacena refresh token (security by design)

---

## 📝 Notas para OpenCode

### Leer Primero
1. **Session Summary**: Usar `mem_context` para ver todo lo hecho
2. **User Profile**: Ver `memory/user_profile.md` para estilo de comunicación
3. **Logs**: Siempre leer logs antes de proponer fixes

### No Asumir
- Código deployado ≠ código fuente (verificar con `/debug/code`)
- Docker cache puede persistir (limpiar .pyc files)
- "Debe ser X" sin verificar (probar primero)

### Explicar Siempre
- Por qué del problema (root cause)
- Por qué de la solución (technical rationale)
- Cómo verificar que funciona (testing steps)

### Comunicación
- Usar voseo: "¿se entiende?", "¿podés probar?"
- Ser cálido y directo: "Fantástico", "Buenísimo", "Listo"
- Evitar filler: "Déjame verificar" → verificar y mostrar resultado

---

## ✅ Checklist para OpenCode

- [ ] Leer session summary en Engram
- [ ] Leer user profile (`memory/user_profile.md`)
- [ ] Verificar código deployado con `/debug/code`
- [ ] Revisar logs del último test fallido
- [ ] Ejecutar deploy del Worker (revisión 00051-qqr)
- [ ] Testear con folder `1JD-53D0ONkRvyqW9TbquA9Z15Z8WyKLH`
- [ ] Verificar que NO aparezca "Refreshing credentials" en logs
- [ ] Confirmar que archivos se renombran correctamente

---

## 📞 Contacto y Session Info

- **Usuario**: gonzalo.f.recalde@gmail.com
- **Session ID**: #C0001#P0007+renameDriverFolders
- **Proyecto**: renameDriverFolders
- **Path**: `C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders`
- **Fecha Handover**: 31 de Marzo 2026
- **Estado**: OAuth fix implementado, pendiente deploy + test

---

## 🎯 Success Criteria

OpenCode habrá completado exitosamente cuando:

1. ✅ Worker revisión 00051-qqr esté deployada
2. ✅ Test con folder `1JD-53D0ONkRvyqW9TbquA9Z15Z8WyKLH` funcione
3. ✅ Archivos se renombran sin error 401
4. ✅ Logs NO muestran "Refreshing credentials due to a 401"
5. ✅ Usuario confirma: "Fantástico, funciona"

**Buena suerte! 🚀**
