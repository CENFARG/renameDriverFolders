# WORKER PATCH - OAuth User Credentials
# ===========================================
#
# Cambios necesarios en services/worker-renombrador/src/main.py
# para recibir y usar credenciales OAuth del usuario.
#

## =============================================================================
## CAMBIO 1: Actualizar TaskPayload model (línea ~169)
## =============================================================================

# ANTES (código actual):
class TaskPayload(BaseModel):
    """
    Payload for Cloud Tasks.
    """
    job_id: Optional[str] = None
    folder_id: Optional[str] = None
    user_token: Optional[str] = None
    trigger_type: str = "scheduled"  # "scheduled" or "manual"
    execution_id: Optional[str] = None


# DESPUÉS (código modificado):
class UserCredentials(BaseModel):
    """
    User OAuth credentials passed from API Server.

    Security:
    - access_token is validated by API Server before being sent
    - Token is short-lived (~60 min)
    - Scope is limited to drive API
    """
    access_token: str
    email: str
    name: Optional[str] = None
    scope: str = "https://www.googleapis.com/auth/drive"

    class Config:
        # Extra fields for future compatibility
        extra = "ignore"


class TaskPayload(BaseModel):
    """
    Payload for Cloud Tasks.

    Contains job configuration and optionally user credentials.
    """
    job_id: Optional[str] = None
    folder_id: Optional[str] = None
    trigger_type: str = "scheduled"  # "scheduled" or "manual"
    execution_id: Optional[str] = None

    # NEW: User OAuth credentials (optional, for manual jobs)
    user_credentials: Optional[UserCredentials] = None

    # Deprecated: user_token (kept for backward compatibility)
    user_token: Optional[str] = None


# =============================================================================
## CAMBIO 2: Agregar función get_user_credentials() (después de línea ~208)
## =============================================================================

from google.oauth2.credentials import Credentials as OAuthCredentials


def get_user_credentials(access_token: str, scope: str):
    """
    Create OAuth credentials from user access token.

    This creates credentials that the Worker can use to access Google Drive
    on behalf of the user, instead of using service account credentials.

    Args:
        access_token: User's OAuth access token (validated by API Server)
        scope: OAuth scope (e.g., https://www.googleapis.com/auth/drive)

    Returns:
        OAuth credentials object for Google API calls

    Security:
    - Access token is short-lived (~60 min)
    - No refresh token is stored
    - Credentials are only used in memory
    """
    return OAuthCredentials(
        token=access_token,
        scopes=[scope],
        token_uri="https://oauth2.googleapis.com/token",
        # client_id and client_secret not needed for access token usage
        client_id="",
        client_secret=""
    )


def mask_access_token(token: str) -> str:
    """
    Mask access token for safe logging.

    Shows only first 4 and last 4 characters.

    Args:
        token: Access token to mask

    Returns:
        Masked token string
    """
    if len(token) > 8:
        return f"{token[:4]}...{token[-4:]}"
    return "****"


# =============================================================================
## CAMBIO 3: Modificar run_task endpoint (línea ~641)
## =============================================================================

# ANTES (código actual):
@app.post("/run-task")
async def run_task(request: Request):
    """
    Main endpoint triggered by Cloud Tasks.
    """
    logger.info("Task received from Cloud Tasks")

    try:
        payload = await request.json()
        task = TaskPayload(**payload)
    except Exception as e:
        logger.error(f"Invalid task payload: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    credentials = get_credentials()


# DESPUÉS (código modificado):
@app.post("/run-task")
async def run_task(request: Request):
    """
    Main endpoint triggered by Cloud Tasks.

    Processes jobs with user OAuth credentials (manual jobs) or
    service account credentials (scheduled jobs).

    Security:
    - User credentials are used when available (manual jobs)
    - Service account fallback for scheduled jobs
    - Access tokens are masked in logs
    """
    logger.info("Task received from Cloud Tasks")

    try:
        payload = await request.json()
        task = TaskPayload(**payload)
    except Exception as e:
        logger.error(f"Invalid task payload: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    # ============================================================
    # NUEVO: Determinar qué credenciales usar
    # ============================================================

    if task.user_credentials and task.user_credentials.access_token:
        # Manual job with user credentials
        user_email = task.user_credentials.email
        access_token = task.user_credentials.access_token
        scope = task.user_credentials.scope

        logger.info(f"🔐 Using USER OAuth credentials")
        logger.info(f"   User: {user_email}")

        # Mask token for logging (don't log full token)
        masked_token = mask_access_token(access_token)
        logger.info(f"   Access token: {masked_token}")
        logger.info(f"   Scope: {scope}")

        # Create OAuth credentials from user's access token
        credentials = get_user_credentials(access_token, scope)

        logger.info(f"   ✅ User OAuth credentials created")

    else:
        # Scheduled job with service account credentials
        logger.info("🔧 Using SERVICE ACCOUNT credentials (scheduled job)")
        logger.info("   ⚠️  No user credentials provided")

        credentials = get_credentials()

    # ============================================================
    # FIN NUEVO
    # ============================================================


# =============================================================================
## CAMBIO 4: Asegurar que process_job pasa credenciales (línea ~676)
## =============================================================================

# Verificar que process_job() recibe y usa las credenciales correctas

# El código debería verse así (verificar que no esté hardcodeado):

# En run_task(), después de crear las credenciales:

        try:
            # Pass the appropriate credentials (user or service account)
            result = process_job(
                job_config,
                task.folder_id,
                credentials  # ← Asegurar que se pasan las credenciales
            )


# =============================================================================
## CAMBIO 5: Modificar process_job para loggear credenciales (opcional)
## =============================================================================

# En la función process_job(), agregar logging para saber qué credenciales se usan:

def process_job(
    job_config: Dict[str, Any],
    folder_id: Optional[str] = None,
    credentials = None
) -> Dict[str, Any]:
    """
    Process a single job.

    Args:
        job_config: Job configuration
        folder_id: Target folder ID (optional for scheduled jobs)
        credentials: Google credentials (user OAuth or service account)
    """
    job_id = job_config.get("id")
    job_name = job_config.get("name", "Unknown")

    logger.info(f"Starting job '{job_name}' (ID: {job_id})")

    # ============================================================
    # NUEVO: Log qué tipo de credenciales se están usando
    # ============================================================

    # Detect credential type
    from google.oauth2.credentials import Credentials as OAuthCredentials
    from google.oauth2.service_account import Credentials as SACredentials

    if isinstance(credentials, OAuthCredentials):
        logger.info(f"🔐 Using USER OAUTH credentials")
        logger.info(f"   Token: {mask_access_token(credentials.token) if hasattr(credentials, 'token') else 'N/A'}")
    elif isinstance(credentials, SACredentials):
        logger.info(f"🔧 Using SERVICE ACCOUNT credentials")
    else:
        logger.info(f"⚠️  Using UNKNOWN credential type")

    # ============================================================
    # FIN NUEVO
    # ============================================================

    # ... resto del código ...

    # Initialize Drive service with the appropriate credentials
    drive_service = build("drive", "v3", credentials=credentials)
    storage_client = storage.Client(credentials=credentials)


# =============================================================================
## CAMBIO 6: Agregar import al inicio del archivo (línea ~24)
## =============================================================================

# ANTES:
from google.oauth2 import service_account

# DESPUÉS:
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as OAuthCredentials  # NEW


# =============================================================================
## RESUMEN DE CAMBIOS
## =============================================================================

# 1. TaskPayload model actualizado:
#    - Nuevo modelo UserCredentials
#    - Campo user_credentials opcional en TaskPayload
#
# 2. Nueva función: get_user_credentials()
#    - Crea credenciales OAuth desde access token
#
# 3. Nueva función: mask_access_token()
#    - Máscara para safe logging de tokens
#
# 4. run_task() modificado:
#    - Detecta si hay user_credentials
#    - Usa credenciales de usuario si están disponibles
#    - Fallback a service account para scheduled jobs
#    - Loguea qué tipo de credenciales se usan
#
# 5. process_job() modificado (opcional):
#    - Detecta tipo de credenciales
#    - Loguea información de credenciales (sin token completo)
#
# 6. Import agregado:
#    - from google.oauth2.credentials import Credentials as OAuthCredentials

# =============================================================================
## NOTAS DE SEGURIDAD
## =============================================================================

# ✅ Access token recibido ya validado por API Server
# ✅ Access token solo usado en memoria (nunca persistido)
# ✅ Access token de corta duración (~60 min)
# ✅ Scope limitado a drive API
# ✅ Logs sanitizados (tokens máscarados)
# ✅ Backward compatible con scheduled jobs (service account)
# ✅ Clear logging de qué credenciales se usan

# =============================================================================
## TESTING
## =============================================================================

# Para testear estos cambios:

# 1. Crear un task manual con user_credentials:
#    {
#      "job_id": "job-manual-test",
#      "folder_id": "TEST_FOLDER_ID",
#      "trigger_type": "manual",
#      "user_credentials": {
#        "access_token": "VALID_ACCESS_TOKEN",
#        "email": "test@example.com",
#        "scope": "https://www.googleapis.com/auth/drive"
#      }
#    }

# 2. Enviar task al Worker:
# curl -X POST http://localhost:8080/run-task \
#   -H "Content-Type: application/json" \
#   -d '{"job_id":"job-manual-test","folder_id":"FOLDER_ID","user_credentials":{"access_token":"TOKEN","email":"test@example.com"}}'

# 3. Verificar en logs:
#    - "Using USER OAUTH credentials"
#    - "Access token: ya29...xyz" (máscarado)
#    - "User OAuth credentials created"

# 4. Verificar que el Worker puede acceder a archivos del usuario

# =============================================================================
## DIAGNÓSTICO DE PROBLEMAS
## =============================================================================

# Si Diego sigue viendo "Found 0 files":

# 1. Verificar que el access token se está pasando:
#    Log debería mostrar: "Using USER OAUTH credentials"
#
# 2. Verificar que el access token es válido:
#    Log debería mostrar: "User OAuth credentials created"
#
# 3. Verificar que el Drive service usa las credenciales correctas:
#    Log debería mostrar: "Using USER OAUTH credentials" en process_job()
#
# 4. Verificar el folder_id:
#    Log debería mostrar: "Found X files in folder FOLDER_ID"
#
# 5. Si sigue sin funcionar, verificar:
#    - Access token tiene scope de drive
#    - Folder ID es correcto
#    - Usuario tiene permisos en esa carpeta

# =============================================================================
## EJEMPLO DE LOGS ESPERADOS
## =============================================================================

# ✅ CASO EXITOSO (Diego):
# 2026-03-19 10:00:00 INFO Task received from Cloud Tasks
# 2026-03-19 10:00:00 INFO 🔐 Using USER OAUTH credentials
# 2026-03-19 10:00:00 INFO    User: cutignolad@estudioanc.com.ar
# 2026-03-19 10:00:00 INFO    Access token: ya29...xyz
# 2026-03-19 10:00:00 INFO    ✅ User OAuth credentials created
# 2026-03-19 10:00:01 INFO Starting job 'Manual Job - Estudio Cutignola'
# 2026-03-19 10:00:01 INFO 🔐 Using USER OAUTH credentials
# 2026-03-19 10:00:02 INFO Found 15 files in folder 10tSqrRY-QaTyIl_8qOQFO98zcLQQbFFP
# 2026-03-19 10:00:10 INFO Job completed. Processed: 15, Renamed: 15

# ✅ CASO EXITOSO (Scheduled job sin usuario):
# 2026-03-19 10:00:00 INFO Task received from Cloud Tasks
# 2026-03-19 10:00:00 INFO 🔧 Using SERVICE ACCOUNT credentials (scheduled job)
# 2026-03-19 10:00:01 INFO Starting job 'Scheduled Job'
# 2026-03-19 10:00:01 INFO 🔧 Using SERVICE ACCOUNT credentials
# 2026-03-19 10:00:02 INFO Found 5 files in folder FOLDER_ID
# 2026-03-19 10:00:10 INFO Job completed. Processed: 5, Renamed: 5

# ❌ CASO PROBLEMÁTICO (Token inválido):
# 2026-03-19 10:00:00 INFO Task received from Cloud Tasks
# 2026-03-19 10:00:00 INFO 🔐 Using USER OAUTH credentials
# 2026-03-19 10:00:00 INFO    User: cutignolad@estudioanc.com.ar
# 2026-03-19 10:00:00 INFO    Access token: ya29...xyz
# 2026-03-19 10:00:01 ERROR Google API error: 401 Invalid Credentials
# 2026-03-19 10:00:01 ERROR Job failed

# ❌ CASO PROBLEMÁTICO (Sin credenciales de usuario):
# 2026-03-19 10:00:00 INFO Task received from Cloud Tasks
# 2026-03-19 10:00:00 INFO 🔧 Using SERVICE ACCOUNT credentials (scheduled job)
# 2026-03-19 10:00:01 INFO Starting job 'Manual Job'
# 2026-03-19 10:00:02 INFO Found 0 files in folder 10tSqrRY-QaTyIl_8qOQFO98zcLQQbFFP
# 2026-03-19 10:00:02 WARNING Job completed. Processed: 0, Renamed: 0
