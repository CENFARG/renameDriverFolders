# 🔐 IMPLEMENTACIÓN SEGURA: OAuth User Credentials Flow
# ===================================================================
#
# Implementación de flujo de credenciales OAuth de usuario para acceso
# a Google Drive con las mejores prácticas de seguridad.
#
# Fecha: 19 de Marzo, 2026
# Versión: 1.0.0
# ===================================================================

## 📋 TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura Actual vs. Nueva](#arquitectura-actual-vs-nueva)
3. [Consideraciones de Seguridad](#consideraciones-de-seguridad)
4. [Plan de Implementación](#plan-de-implementación)
5. [Código y Cambios](#código-y-cambios)
6. [Testing y Validación](#testing-y-validación)
7. [Deploy y Rollback](#deploy-y-rollback)

---

## 1. RESUMEN EJECUTIVO

### 🎯 Objetivo
Implementar el flujo de credenciales OAuth del usuario para que el Worker pueda acceder a Google Drive en nombre del usuario, sin requerir que los usuarios compartan sus carpetas con la service account.

### ✅ Beneficios
- **Privacidad**: Cada usuario accede solo a sus propios archivos
- **Escalabilidad**: Funciona para cualquier número de usuarios
- **Seguridad**: Principio de least privilege, aislamiento entre usuarios
- **Compliance**: Cumple con estándares de la industria

### ⚠️ Riesgos Mitigados
- Service account como superusuario con acceso a todo
- Problemas de privacidad y compliance
- No escalable con múltiples usuarios

---

## 2. ARQUITECTURA ACTUAL vs. NUEVA

### Arquitectura Actual (PROBLEMÁTICA):

```
┌─────────┐  OAuth Token  ┌─────────────┐  OIDC Token    ┌──────────────┐
│ Frontend│ ────────────→  │ API Server  │ ─────────────→ │ Cloud Tasks  │
│ (Diego) │  (IAP验证)    │             │  (Service SA)  │              │
└─────────┘               └─────────────┘                 └──────┬───────┘
                                                                  │
                                                                  ↓
                                                          ┌──────────────┐
                                                          │ Worker       │
                                                          │ (Service SA) │ ──→ ❌ 0 archivos
                                                          └──────────────┘     (SA no tiene permisos)
```

**Problema:** Worker usa credenciales de service account que no tienen acceso a las carpetas de Diego.

### Nueva Arquitectura (SEGURA):

```
┌─────────┐  OAuth Token  ┌─────────────┐  Access Token   ┌──────────────┐
│ Frontend│ ────────────→  │ API Server  │ ─────────────→ │ Cloud Tasks  │
│ (Diego) │  (IAP验证)    │             │  (User Token)   │              │
└─────────┘               └─────────────┘                 └──────┬───────┘
                                                                  │
                                                                  ↓
                                                          ┌──────────────┐
                                                          │ Worker       │
                                                          │ (User Token) │ ──→ ✅ Archivos de Diego
                                                          └──────────────┘     (acceso con credenciales de usuario)
```

**Solución:** Worker usa credenciales OAuth del usuario para acceder a sus archivos.

---

## 3. CONSIDERACIONES DE SEGURIDAD

### 🔒 Principios de Seguridad Implementados

| Principio | Implementación |
|-----------|----------------|
| **Least Privilege** | Cada usuario solo accede a sus propios archivos |
| **Token Lifetime** | Access tokens expiran en ~60 min (no refresh tokens) |
| **Scope Limitado** | Solo `https://www.googleapis.com/auth/drive` (no cloud-platform) |
| **No Persistencia** | Tokens solo en memoria, nunca en disco/base de datos |
| **Sanitización de Logs** | Tokens nunca se loguean (máscaras en logs) |
| **Validación de Tokens** | API Server valida token antes de pasarlo al Worker |
| **HTTPS Obligatorio** | Todo el tráfico está encriptado (IAP + Cloud Tasks) |
| **Auditoría** | Cada acción attributable al usuario específico |

### ⚠️ Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Token leakage en logs | Sanitización de logs, no loguear credenciales |
| Token en tránsito | HTTPS, encriptación endpoint-to-end |
| Token expirado | Validación de token en API Server antes de crear task |
| Token comprometido | Lifetime corto (60 min), scope limitado |
| IAP bypass | IAP ya está configurado y validando tokens |

### 🛡️ Protección contra Ataques

1. **Token Injection Attack**
   - Mitigación: Validar token en API Server antes de pasarlo
   - Implementación: `oauth_manager.verify_token()`

2. **Token Logging Attack**
   - Mitigación: Sanitización de logs
   - Implementación: Máscaras en logs (mostrar solo primeros/últimos 4 caracteres)

3. **Token Replay Attack**
   - Mitigación: Access tokens de corta duración
   - Implementación: Google OAuth tokens expiran en ~60 min

4. **Privilege Escalation**
   - Mitigación: Scope limitado a drive, no cloud-platform
   - Implementación: Validar scope del token

---

## 4. PLAN DE IMPLEMENTACIÓN

### Paso 1: Modificar API Server (services/api-server/src/main.py)

#### 1.1 Extraer access token del request
```python
# En la función submit_manual_job()
# Después de validar el usuario con get_current_user

async def submit_manual_job(
    job_request: ManualJobRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Submit manual job with user OAuth token."""

    # Extraer access token del header Authorization
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")

    access_token = auth_header.split("Bearer ")[1]

    # Validar que el token sea válido (doble verificación)
    try:
        user_info = oauth_manager.verify_token(access_token)
        logger.info(f"✅ Access token validated for user: {user_info['email']}")
    except Exception as e:
        logger.error(f"❌ Invalid access token: {e}")
        raise HTTPException(status_code=401, detail="Invalid access token")

    # Resto del código...
```

#### 1.2 Incluir access token en el payload de la Cloud Task
```python
# Modificar el payload para incluir access token (seguro)
payload = {
    "job_id": job_id,
    "folder_id": job_request.folder_id,
    "trigger_type": "manual",
    "submitted_by": user["email"],
    "execution_id": execution_log["id"],
    "user_credentials": {  # ← NUEVO: Credenciales del usuario
        "access_token": access_token,
        "email": user["email"],
        "scope": "https://www.googleapis.com/auth/drive"
    }
}
```

#### 1.3 Sanitización de logs (NO loguear tokens)
```python
# Modificar los logs para no exponer el access token
logger.info(f"📦 Building task with payload: {sanitize_payload(payload)}")

def sanitize_payload(payload: dict) -> dict:
    """Remove sensitive data from payload for logging."""
    sanitized = payload.copy()
    if "user_credentials" in sanitized and "access_token" in sanitized["user_credentials"]:
        token = sanitized["user_credentials"]["access_token"]
        # Mostrar solo primeros 4 y últimos 4 caracteres
        masked = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "****"
        sanitized["user_credentials"]["access_token"] = masked
    return sanitized
```

### Paso 2: Modificar Worker (services/worker-renombrador/src/main.py)

#### 2.1 Actualizar TaskPayload model
```python
class UserCredentials(BaseModel):
    """User OAuth credentials."""
    access_token: str
    email: str
    scope: str = "https://www.googleapis.com/auth/drive"

class TaskPayload(BaseModel):
    """Payload for Cloud Tasks."""
    job_id: Optional[str] = None
    folder_id: Optional[str] = None
    trigger_type: str = "scheduled"
    execution_id: Optional[str] = None
    user_credentials: Optional[UserCredentials] = None  # ← NUEVO
```

#### 2.2 Crear credenciales OAuth desde access token
```python
from google.oauth2.credentials import Credentials as OAuthCredentials

def get_user_credentials(access_token: str, scope: str):
    """
    Create OAuth credentials from user access token.

    Args:
        access_token: User's OAuth access token
        scope: OAuth scope (e.g., https://www.googleapis.com/auth/drive)

    Returns:
        OAuth credentials object
    """
    return OAuthCredentials(
        token=access_token,
        scopes=[scope],
        token_uri="https://oauth2.googleapis.com/token",
        client_id="",  # Not needed for access token
        client_secret=""  # Not needed for access token
    )
```

#### 2.3 Modificar run_task endpoint
```python
@app.post("/run-task")
async def run_task(request: Request):
    """Main endpoint triggered by Cloud Tasks."""

    try:
        payload = await request.json()
        task = TaskPayload(**payload)
    except Exception as e:
        logger.error(f"Invalid task payload: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    # Usar credenciales del usuario si están disponibles
    if task.user_credentials and task.user_credentials.access_token:
        logger.info(f"🔐 Using user OAuth credentials for: {task.user_credentials.email}")

        # Crear credenciales OAuth desde el access token
        credentials = get_user_credentials(
            access_token=task.user_credentials.access_token,
            scope=task.user_credentials.scope
        )

        # Sanitizar log (no mostrar token completo)
        token_preview = f"{task.user_credentials.access_token[:4]}...{task.user_credentials.access_token[-4:]}"
        logger.info(f"   Access token: {token_preview}")
    else:
        # Fallback a credenciales de service account (para scheduled jobs)
        logger.info("⚠️ No user credentials provided, using service account (scheduled job)")
        credentials = get_credentials()

    # Process job with appropriate credentials
    # ...
```

#### 2.4 Modificar process_job para pasar credenciales
```python
def process_job(
    job_config: Dict[str, Any],
    folder_id: Optional[str] = None,
    credentials = None  # ← Asegurar que se pasan las credenciales
) -> Dict[str, Any]:
    """Process a single job."""

    # ...

    # Initialize Drive service with user credentials
    drive_service = build("drive", "v3", credentials=credentials)
    storage_client = storage.Client(credentials=credentials)

    # ...
```

### Paso 3: Testing y Validación

#### 3.1 Tests Unitarios
```python
# tests/test_oauth_credentials.py

def test_sanitize_payload():
    """Test that access tokens are masked in logs."""
    payload = {
        "user_credentials": {
            "access_token": "ya29.a0AfH6SMBx...very_long_token...xyz123"
        }
    }
    sanitized = sanitize_payload(payload)
    assert "ya29" not in sanitized["user_credentials"]["access_token"]
    assert "..." in sanitized["user_credentials"]["access_token"]

def test_user_credentials_creation():
    """Test OAuth credentials creation from access token."""
    access_token = "test_token_123"
    credentials = get_user_credentials(access_token, "https://www.googleapis.com/auth/drive")
    assert credentials.token == access_token
    assert len(credentials.scopes) == 1
```

#### 3.2 Tests de Integración
1. Ejecutar job manual con credenciales de Gonzalo
2. Verificar que Worker usa credenciales de Gonzalo
3. Verificar que Gonzalo puede acceder a sus archivos
4. Ejecutar job manual con credenciales de Diego
5. Verificar que Worker usa credenciales de Diego
6. Verificar que Diego puede acceder a sus archivos

---

## 5. CÓDIGO Y CAMBIOS

### Archivos a Modificar

1. **services/api-server/src/main.py**
   - Línea ~579: `submit_manual_job()` - Extraer access token
   - Línea ~648: Payload de task - Incluir user_credentials
   - Línea ~385: `sanitize_payload()` - Nueva función

2. **services/worker-renombrador/src/main.py**
   - Línea ~169: `TaskPayload` - Agregar user_credentials
   - Línea ~190: `get_user_credentials()` - Nueva función
   - Línea ~641: `run_task()` - Usar credenciales de usuario
   - Línea ~277: `process_job()` - Asegurar paso de credenciales

### Orden de Cambios

1. Primero modificar Worker (para no romper compatibilidad backward)
2. Luego modificar API Server
3. Deployar Worker primero
4. Deployar API Server después
5. Testing con ambos usuarios

---

## 6. TESTING Y VALIDACIÓN

### Test Plan

#### Fase 1: Unit Tests
- [ ] Test `sanitize_payload()` máscaras correctamente
- [ ] Test `get_user_credentials()` crea credenciales válidas
- [ ] Test `TaskPayload` valida user_credentials

#### Fase 2: Integration Tests (Local)
- [ ] Levantar API Server localmente
- [ ] Levantar Worker localmente
- [ ] Enviar request manual con mock token
- [ ] Verificar que Worker recibe user_credentials
- [ ] Verificar que Worker crea credenciales OAuth

#### Fase 3: Integration Tests (Producción - Staging)
- [ ] Deployar a staging (si existe)
- [ ] Test con Gonzalo (su cuenta funciona)
- [ ] Test con Diego (su cuenta ahora funciona)

#### Fase 4: Production Deployment
- [ ] Deployar Worker a producción
- [ ] Deployar API Server a producción
- [ ] Test con Gonzalo
- [ ] Test con Diego
- [ ] Verificar logs para confirmar uso de user credentials

### Casos de Test

| Caso | Usuario | Esperado | Validación |
|------|---------|----------|------------|
| Job manual - Gonzalo | Gonzalo | ✅ Procesa archivos de Gonzalo | Worker usa credenciales de Gonzalo |
| Job manual - Diego | Diego | ✅ Procesa archivos de Diego | Worker usa credenciales de Diego |
| Job scheduled (sin user) | N/A | ✅ Procesa con service account | Fallback a service account |
| Token expirado | Cualquiera | ❌ Error 401 en API Server | Token validado antes de crear task |
| Token inválido | Cualquiera | ❌ Error 401 en API Server | Token rechazado |

---

## 7. DEPLOY Y ROLLBACK

### Estrategia de Deploy

#### Opción A: Blue-Green Deploy (RECOMENDADO)

1. **Deploy Worker (v2-00043-oauth)**
   ```bash
   cd services/worker-renombrador
   gcloud builds submit --config cloudbuild.yaml --project cloud-functions-474716 .
   ```

2. **Verificar Worker nuevo**
   ```bash
   gcloud run services describe renombradorarchivosgdrive-worker-v2 \
     --region us-central1 --project cloud-functions-474716
   ```

3. **Deploy API Server (v2-00043-oauth)**
   ```bash
   cd services/api-server
   gcloud builds submit --config cloudbuild.yaml --project cloud-functions-474716 .
   ```

4. **Verificar API Server nuevo**
   ```bash
   gcloud run services describe renombradorarchivosgdrive-api-server-v2 \
     --region us-central1 --project cloud-functions-474716
   ```

5. **Smoke Tests**
   - Test con Gonzalo
   - Test con Diego

#### Opción B: Canary Deploy (AVANZADO)

1. Crear nuevo servicio Worker (worker-v2-canary)
2. Crear nuevo servicio API Server (api-server-v2-canary)
3. Routing 10% tráfico a canary
4. Monitorear métricas
5. Incrementar tráfico gradualmente (25%, 50%, 100%)
6. Migrar completa cuando canary esté estable

### Plan de Rollback

#### Si algo falla en producción:

1. **Identificar el problema**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND timestamp>=\"2026-03-19T00:00:00Z\"" \
     --project cloud-functions-474716 --limit 50 --freshness=10m
   ```

2. **Rollback a versión anterior**
   ```bash
   # Rollback Worker
   gcloud run services update-traffic renombradorarchivosgdrive-worker-v2 \
     --to-revisions=v2-00042-d6r=100 --region us-central1

   # Rollback API Server
   gcloud run services update-traffic renombradorarchivosgdrive-api-server-v2 \
     --to-revisions=v2-00042-d6r=100 --region us-central1
   ```

3. **Verificar que funciona**
   - Test con Gonzalo
   - Verificar que scheduled jobs funcionan

4. **Investigar logs y corregir**

---

## ✅ CHECKLIST FINAL DE SEGURIDAD

### Antes de Deploy

- [ ] Access tokens validados en API Server antes de crear task
- [ ] Access tokens no persistidos (solo en memoria)
- [ ] Access tokens no logueados (máscaras implementadas)
- [ ] Scope limitado a `https://www.googleapis.com/auth/drive`
- [ ] Refresh tokens NO pasados al Worker
- [ ] IAP sigue validando tokens
- [ ] Tests unitarios pasan
- [ ] Tests de integración pasan
- [ ] Logs sanitizados verificados
- [ ] Documentación actualizada

### Después de Deploy

- [ ] Verificar que Gonzalo puede procesar sus archivos
- [ ] Verificar que Diego puede procesar sus archivos (antes fallaba)
- [ ] Verificar que scheduled jobs funcionan (sin user credentials)
- [ ] Verificar logs no muestran tokens completos
- [ ] Verificar métricas de error < 1%
- [ ] Monitorear por 24 horas

---

## 📞 CONTACTO Y SOPORTE

**Autor:** Claude + amBotHs
**Fecha:** 19 de Marzo, 2026
**Versión:** 1.0.0
**Estado:** Ready for Implementation

---

## 📚 REFERENCIAS

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Cloud Run Security Best Practices](https://cloud.google.com/run/docs/security)
- [IAP Authentication](https://cloud.google.com/iap/docs/authentication-howto)
- [Least Privilege Principle](https://cloud.google.com/security-principles#least-privilege)

---

**FIN DE DOCUMENTO**
