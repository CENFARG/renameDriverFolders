# Auditoría de Seguridad - Actualizada 13 Abril 2026

**Fecha**: 13 de Abril 2026
**Ejecutado por**: Claude Code + análisis manual
**Project**: renameDriverFolders (cloud-functions-474716)

---

## ✅ Buenas Noticias - Falsas Alarmas Corregidas

### Hallazgos Previos que NO son problemas

#### 1. Credenciales Hardcodeadas en Git ❌ FALSO
**Verificación actual**:
```bash
git log --all --full-history --oneline -- ".credentials/"
# Output: (vacío) - Nunca commitados
```

**Estado**: ✅ Los archivos en `.credentials/` están en `.gitignore` y **NUNCA fueron commitados** al repositorio.

**Archivos verificados**:
- `.credentials/credentials.json`
- `.credentials/credencial_b64.txt`
- `.credentials/drive_changes_token.json`

**Riesgo**: **BAJO** - Existen solo localmente en la máquina de Gonzalo.

---

#### 2. CORS Permisivo ❌ FALSO
**Código actual** (`api-server/src/main.py:244-258`):
```python
cors_origins_str = get_secret("cors-allowed-origins") or os.environ.get("CORS_ALLOWED_ORIGINS", "")
if cors_origins_str:
    CORS_ORIGINS = [origin.strip() for origin in cors_origins_str.split(",")]
else:
    logger.warning("CORS not configured. Defaulting to empty list (STRICT MODE)")
    CORS_ORIGINS = []  # ← STRICT MODE, no "*"
```

**Estado**: ✅ Implementado correctamente con modo STRICT por defecto.

**Riesgo**: **NINGUNO**

---

#### 3. Credenciales en Código Fuente ❌ FALSO
**Verificación**: Grep de `client_secret`, `private_key`, `AIza` en el código.

**Estado**: ✅ No hay credenciales hardcodeadas. La única referencia a `client_secret=None` es legítima (OAuth flow sin secret para tokens ya autorizados).

**Riesgo**: **NINGUNO**

---

## ⚠️ Problemas Reales Encontrados

### 🔴 HIGH - Worker Endpoint Sin Autenticación

**Problema**: El endpoint `/run-task` del Worker **NO verifica autenticación**.

**Código** (`worker-renombrador/src/main.py:790-839`):
```python
@app.post("/run-task")
async def run_task(request: Request):
    """
    Main endpoint triggered by Cloud Tasks.
    ...
    Security:
    - User credentials are used when available (manual jobs)
    - Service account fallback for scheduled jobs
    - Access tokens are masked in logs
    """
    # ← NO HAY VERIFICACIÓN DE AUTENTICACIÓN
    logger.info("=" * 60)
    logger.info("Task received from Cloud Tasks")
    # ... procesa directamente sin verificar ...
```

**Verificación de IAM**:
```bash
gcloud run services get-iam-policy renombradorarchivosgdrive-worker-v2 \
  --project="cloud-functions-474716" --region="us-central1"
```

**Resultado**:
```json
{
  "bindings": [
    {
      "members": ["allUsers"],
      "role": "roles/run.invoker"
    }
  ]
}
```

**Impacto**: Cualquiera con la URL del Worker puede enviar tareas maliciosas.

**Riesgo**: **HIGH**

**Remediación**:
```python
# Agregar al Worker
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

@app.post("/run-task")
async def run_task(request: Request):
    # Verificar que la request viene de Cloud Tasks
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    # Extraer y verificar token OIDC de Cloud Tasks
    try:
        token = auth_header.split(" ")[1]
        expected_audience = os.environ.get("WORKER_URL")
        id_info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            expected_audience
        )

        # Verificar que es la service account correcta
        expected_sa = "scheduler-trigger@cloud-functions-474716.iam.gserviceaccount.com"
        if id_info.get("email") != expected_sa:
            raise HTTPException(status_code=403, detail="Unauthorized service account")

    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication")

    # Continuar con procesamiento...
```

---

### 🟡 MEDIUM - IAM Policy Muy Permisiva

**Problema**: Los tres servicios tienen `allUsers` con acceso público.

**Estado actual**:

| Servicio | `allUsers` Access | ¿Aceptable? | Razón |
|----------|-------------------|-------------|-------|
| Frontend | ✅ Sí | **Sí** | Es una UI web, necesita acceso público |
| API Server | ✅ Sí | **Aceptable** | Tiene OAuth middleware en endpoints protegidos |
| Worker | ✅ Sí | **NO** | Debería ser accesible solo por Cloud Tasks |

**Remediación**:
```bash
# Remover acceso público al Worker
gcloud run services remove-iam-policy-binding renombradorarchivosgdrive-worker-v2 \
  --project="cloud-functions-474716" \
  --region="us-central1" \
  --member="allUsers" \
  --role="roles/run.invoker"

# Dar acceso solo a Cloud Tasks service account
gcloud run services add-iam-policy-binding renombradorarchivosgdrive-worker-v2 \
  --project="cloud-functions-474716" \
  --region="us-central1" \
  --member="serviceAccount:scheduler-trigger@cloud-functions-474716.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

---

### 🟢 LOW - Archivos .credentials en Disco Local

**Problema**: Los archivos de credenciales existen en la máquina local.

**Estado**: No están en git, pero están en Dropbox (potencialmente compartido).

**Remediación**:
```bash
# Eliminar archivos locales (mantener en .gitignore)
rm -rf .credentials/

# Agregar a .gitignore (ya está)
.credentials/
credentials.json
drive_changes_token.json
credencial_b64.txt
```

---

## 📊 Score de Seguridad Actual

**Cálculo**: (100 - (30 por Worker sin auth) - (10 por IAM permisivo)) = **60/100**

**Clasificación**: MEDIUM-HIGH

---

## 🎯 Plan de Remediación Priorizado

### 1. CRÍTICO (Hoy - 2 horas)
**Agregar autenticación al Worker `/run-task` endpoint**

**Pasos**:
1. Modificar `services/worker-renombrador/src/main.py`
2. Agregar verificación de token OIDC
3. Testear localmente con mock token
4. Deploy Worker con fix
5. Verificar que Cloud Tasks puede invocar Worker

**Archivos a modificar**:
- `services/worker-renombrador/src/main.py` (líneas 790-839)

---

### 2. HIGH (Esta semana - 30 min)
**Restringir IAM policy del Worker**

**Pasos**:
1. Remover `allUsers` del Worker
2. Dar acceso solo a Cloud Tasks service account
3. Verificar que el sistema funciona

---

### 3. LOW (Cuando sea - 5 min)
**Eliminar archivos .credentials localmente**

**Pasos**:
1. Backup los archivos (por si las dudas)
2. Eliminar directorio `.credentials/`
3. Verificar que el deploy funciona (credenciales vienen de Secret Manager)

---

## 🔒 Recomendaciones de Largo Plazo

### Monitoring
1. **Configurar Cloud Logging alerts** para:
   - Requests sospechosos al Worker (sin token válido)
   - Múltiples fallos de autenticación
   - Requests desde IPs inusuales

### Segregación
1. **Separar credenciales por ambiente**:
   - Development → Secret Manager con prefijo `dev-`
   - Production → Secret Manager con prefijo `prod-`

### Auditoría
1. **Audit logging**: Habilitar BigQuery export de Cloud Audit Logs
2. **Revisión trimestral** de políticas IAM
3. **Scanner de dependencias** para vulnerabilities en Python packages

---

## ✅ Checklist de Seguridad

Antes de considerar el sistema "seguro":

- [ ] Worker `/run-task` tiene verificación de token OIDC
- [ ] Worker IAM permite solo Cloud Tasks service account
- [ ] API Server verifica OAuth en todos los endpoints protegidos
- [ ] No hay credenciales en código fuente
- [ ] No hay credenciales en git history
- [ .credentials/ eliminado de máquina local
- [ ] CORS configurado con modo STRICT
- [ ] Alerts configurados en Cloud Logging
- [ ] Audit logs exportados a BigQuery

---

## 📞 Contacto

**Autor**: Claude Code (sonnet 4.6)
**Fecha**: 13 Abril 2026
**Proyecto**: renameDriverFolders
**Session**: #C0001#P0007+renameDriverFolders

**Próxima revisión**: Después de implementar remediación CRÍTICA

---

**Conclusión**:
Los problemas de seguridad reportados en la auditoría anterior fueron **exagerados**. Los verdaderos problemas son:
1. Worker endpoint sin autenticación (HIGH)
2. IAM policy muy permisiva (MEDIUM)

Ambos son **fáciles de corregir** y no requieren cambios arquitectónicos mayores.
