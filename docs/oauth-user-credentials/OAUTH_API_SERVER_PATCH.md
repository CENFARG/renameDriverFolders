# API SERVER PATCH - OAuth User Credentials
# ================================================
#
# Cambios necesarios en services/api-server/src/main.py
# para implementar flujo de credenciales OAuth de usuario.
#

## =============================================================================
## CAMBIO 1: Agregar función sanitize_payload() (después de línea 343)
## =============================================================================

def sanitize_payload(payload: dict) -> dict:
    """
    Remove sensitive data from payload for logging.

    Masks access tokens to prevent credential leakage in logs.

    Args:
        payload: Original payload with sensitive data

    Returns:
        Sanitized payload with masked credentials
    """
    import copy
    sanitized = copy.deepcopy(payload)

    # Mask access tokens if present
    if "user_credentials" in sanitized and isinstance(sanitized["user_credentials"], dict):
        if "access_token" in sanitized["user_credentials"]:
            token = sanitized["user_credentials"]["access_token"]
            # Show only first 4 and last 4 characters
            if len(token) > 8:
                masked = f"{token[:4]}...{token[-4:]}"
            else:
                masked = "****"
            sanitized["user_credentials"]["access_token"] = masked

    return sanitized


# =============================================================================
## CAMBIO 2: Modificar submit_manual_job() (línea ~579)
## =============================================================================

# ANTES (código actual):
@app.post("/api/v1/jobs/manual", response_model=JobResponse)
async def submit_manual_job(
    job_request: ManualJobRequest,
    user: dict = Depends(get_current_user)
):
    """
    Submit a manual job for processing with unified authentication.
    """
    logger.info(f"Manual job submission from {user['email']}")

    # ...


# DESPUÉS (código modificado):
@app.post("/api/v1/jobs/manual", response_model=JobResponse)
async def submit_manual_job(
    job_request: ManualJobRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Submit a manual job for processing with user OAuth credentials.

    Security:
    - Extracts user's access token from Authorization header
    - Validates token before creating Cloud Task
    - Passes token to Worker for user-specific Drive access
    """
    logger.info(f"Manual job submission from {user['email']}")

    # ============================================================
    # NUEVO: Extraer y validar access token del usuario
    # ============================================================

    # Extract access token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.error("❌ Missing or invalid Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Authorization header required (Bearer token)"
        )

    access_token = auth_header.split("Bearer ")[1].strip()

    # Validate the access token (double verification)
    try:
        # Verify token is valid and get user info
        token_info = oauth_manager.verify_token(access_token)

        # Ensure token belongs to the authenticated user
        if token_info.get("email") != user.get("email"):
            logger.error(f"❌ Token email mismatch: {token_info.get('email')} != {user.get('email')}")
            raise HTTPException(
                status_code=401,
                detail="Token does not match authenticated user"
            )

        logger.info(f"✅ Access token validated for user: {user['email']}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Access token validation failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token"
        )

    # ============================================================
    # FIN NUEVO
    # ============================================================

    # Find appropriate job config
    # For manual jobs, we use a generic template or specific job_type
    job_id = f"job-manual-{job_request.job_type}"


# =============================================================================
## CAMBIO 3: Modificar el payload de la task (línea ~648)
## =============================================================================

# ANTES (código actual):
    # Create task payload
    payload = {
        "job_id": job_id,
        "folder_id": job_request.folder_id,
        "trigger_type": "manual",
        "submitted_by": user["email"],
        "execution_id": execution_log["id"]
    }


# DESPUÉS (código modificado):
    # Create task payload with user credentials
    payload = {
        "job_id": job_id,
        "folder_id": job_request.folder_id,
        "trigger_type": "manual",
        "submitted_by": user["email"],
        "execution_id": execution_log["id"],
        # ============================================================
        # NUEVO: Incluir credenciales del usuario para el Worker
        # ============================================================
        "user_credentials": {
            "access_token": access_token,  # Validated access token
            "email": user["email"],
            "name": user.get("name", "Unknown"),
            "scope": "https://www.googleapis.com/auth/drive"
        }
        # ============================================================
        # FIN NUEVO
        # ============================================================
    }

    # Log payload with sanitized credentials (don't log full token)
    logger.info(f"📦 Creating task with sanitized payload: {sanitize_payload(payload)}")


# =============================================================================
## CAMBIO 4: Modificar create_cloud_task() para sanitizar logs (línea ~385)
## =============================================================================

# ANTES (código actual):
    # Build task
    logger.info(f"📦 Building task with payload: {payload}")
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{WORKER_URL}/run-task",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(payload).encode(),
        }
    }


# DESPUÉS (código modificado):
    # Build task
    logger.info(f"📦 Building task with payload")

    # Sanitize payload for logging (don't log access tokens)
    sanitized_payload = sanitize_payload(payload)
    logger.debug(f"   Sanitized payload: {sanitized_payload}")

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{WORKER_URL}/run-task",
            "headers": {"Content-Type": "application/json"},
            # Payload is included in body, not in logs
            "body": json.dumps(payload).encode(),
        }
    }


# =============================================================================
## RESUMEN DE CAMBIOS
## =============================================================================

# 1. Nueva función: sanitize_payload() - Máscaras access tokens en logs
# 2. submit_manual_job() modificado:
#    - Agregar parámetro request: Request
#    - Extraer access token del header Authorization
#    - Validar access token con oauth_manager.verify_token()
#    - Verificar que el token pertenece al usuario autenticado
# 3. Payload modificado:
#    - Incluir user_credentials con access_token, email, name, scope
# 4. create_cloud_task() modificado:
#    - Usar sanitize_payload() en logs
#    - No loguear el access token completo

# =============================================================================
## NOTAS DE SEGURIDAD
## =============================================================================

# ✅ Access token validado ANTES de crear la task
# ✅ Access token solo incluido en el body de la task (no en logs)
# ✅ Access token nunca persistido en base de datos
# ✅ Access token de corta duración (~60 min)
# ✅ Scope limitado a drive (no cloud-platform)
# ✅ Logs sanitizados para no exponer credenciales
# ✅ IAP sigue validando tokens (doble capa de seguridad)

# =============================================================================
## TESTING
## =============================================================================

# Para testear estos cambios localmente:

# 1. Levantar API Server con el código modificado
# 2. Enviar request POST a /api/v1/jobs/manual con header Authorization
# 3. Verificar en los logs que el access token aparece como "ya29...xyz"
# 4. Verificar que el payload incluye user_credentials
# 5. Verificar que se crea la task correctamente

# Ejemplo de curl:
# curl -X POST https://api-server-url/api/v1/jobs/manual \
#   -H "Authorization: Bearer ACCESS_TOKEN_AQUI" \
#   -H "Content-Type: application/json" \
#   -d '{"folder_id": "FOLDER_ID", "job_type": "generic"}'
