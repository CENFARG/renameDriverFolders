"""
API Server - RenameDriverFolders
=================================

API Gateway for document processing jobs.
Handles manual (OAuth) and scheduled (OIDC) requests.

:created:   2025-12-05
:filename:  main.py
:author:    amBotHs + CENF
:version:   2.0.0
:status:    Development
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import json
import os
import re
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, validator
from google.cloud import tasks_v2, secretmanager
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

# Core modules
from core_renombrador.config_manager import ConfigManager
from core_renombrador.logger_manager import LoggerManager
from core_renombrador.database_manager import DatabaseManager
from core_renombrador.file_manager import FileManager
from core_renombrador.oauth_security import (
    OAuthSecurityManager,
    create_oauth_manager_from_config
)

# --- Initialization ---
config_manager = ConfigManager(config_path="config.json")
LoggerManager.initialize(config_manager)
logger = LoggerManager.get_logger(__name__)

# Dual-Mode Secret Retrieval
def get_secret(secret_id: str) -> str:
    """
    Get secret from Secret Manager (production) or .env (local)
    
    Priority:
    1. Environment variable (for local dev)
    2. Secret Manager (for production)
    """
    # Check if running locally (has .env file)
    env_var = secret_id.upper().replace("-", "_")
    local_value = os.environ.get(env_var)
    
    if local_value:
        logger.info(f"Using local config for {secret_id}")
        return local_value.strip()
    
    # Production: use Secret Manager
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get("GCP_PROJECT_ID", "cloud-functions-474716")
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        logger.info(f"Using Secret Manager for {secret_id}")
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        logger.warning(f"Failed to get secret {secret_id}: {e}")
        return ""

# Database Manager
file_manager = FileManager(base_path="./data", config_manager=config_manager)
use_supabase = os.environ.get("USE_SUPABASE", "false").lower() == "true"

use_gcs = os.environ.get("USE_GCS", "false").lower() == "true" or "GCS_BUCKET_NAME" in os.environ

# Load Supabase credentials from Secret Manager if using Supabase
if use_supabase:
    supabase_url = get_secret("supabase-url")
    supabase_key = get_secret("supabase-key")

    if supabase_url and supabase_key:
        os.environ["SUPABASE_URL"] = supabase_url
        os.environ["SUPABASE_KEY"] = supabase_key
        logger.info("Supabase credentials loaded from Secret Manager")
    else:
        logger.warning("Supabase credentials not found in Secret Manager, falling back to JSON mode")
        use_supabase = False

# Job Configurations Manager
if use_supabase:
    db_manager = DatabaseManager(use_supabase=True, table_name="jobs")
    logger.info("DatabaseManager initialized in Supabase mode")
elif use_gcs:
    db_manager = DatabaseManager(
        use_gcs=True,
        table_name="jobs"
    )
    logger.info("DatabaseManager initialized in GCS mode")
else:
    db_manager = DatabaseManager(
        file_manager=file_manager,
        db_path="data/jobs.json"
    )
    logger.info("DatabaseManager initialized in JSON mode")

# Job Executions Manager (for audit logs)
if use_supabase:
    executions_manager = DatabaseManager(use_supabase=True, table_name="job_executions")
    logger.info("Executions DatabaseManager initialized in Supabase mode")
elif use_gcs:
    executions_manager = DatabaseManager(
        use_gcs=True,
        table_name="job_executions"
    )
    logger.info("Executions DatabaseManager initialized in GCS mode")
else:
    executions_manager = DatabaseManager(
        file_manager=file_manager,
        db_path="data/job_executions.json"
    )
    logger.info("Executions DatabaseManager initialized in JSON mode")

# --- Seeding Diego Cutignola's Study Algorithms ---
def seed_default_algorithms():
    """Seeds professional study algorithms if they don't exist."""
    diego_algorithms = [
        {
            "id": "facturas-rg830",
            "name": "Facturas RG 830 (Detección Auto)",
            "description": "Estilo Diego Cutignola: [FECHA]_[TIPO]_[EMISOR]_[DETALLE]",
            "active": True,
            "trigger_type": "manual",
            "source_folder_id": "DYNAMIC",
            "target_folder_names": ["Procesados"],
            "agent_config": {
                "model": {"name": "gemini-2.5-flash", "temperature": 0.1, "max_tokens": 4096},
                "instructions": "Analiza el documento. Si es factura, usa TIPO=FACTURA. Emisor: Empresa externa. Detalle: Concepto breve.",
                "prompt_template": "Analiza: {content}. Formato: YYYY-MM-DD_FACTURA_EMISOR_DETALLE. Devuelve solo el nombre.",
                "filename_format": "{date}_FACTURA_{issuer}_{detail}"
            }
        },
        {
            "id": "sueldos-digitales",
            "name": "Sueldos y Liquidaciones RRHH",
            "description": "Estilo Diego Cutignola: AAAA-MM_SUELDO_EMPRESA_DETALLE",
            "active": True,
            "trigger_type": "manual",
            "source_folder_id": "DYNAMIC",
            "target_folder_names": ["Recibos_Procesados"],
            "agent_config": {
                "model": {"name": "gemini-2.5-pro", "temperature": 0.1, "max_tokens": 4096},
                "instructions": "Analiza recibos de sueldo. Usa TIPO=SUELDO. Emisor: Nombre de la empresa. Detalle: Apellido empleado o concepto.",
                "prompt_template": "Analiza: {content}. Formato: YYYY-MM_SUELDO_EMPRESA_DETALLE.",
                "filename_format": "{date}_SUELDO_{issuer}_{detail}"
            }
        },
        {
            "id": "resumenes-bancarios",
            "name": "Resúmenes y Tenencias",
            "description": "Estilo Diego Cutignola: AAAA-MM_RESUMEN_BANCO_DETALLE",
            "active": True,
            "trigger_type": "manual",
            "source_folder_id": "DYNAMIC",
            "target_folder_names": ["Extractos"],
            "agent_config": {
                "model": {"name": "gemini-2.5-flash", "temperature": 0.1, "max_tokens": 4096},
                "instructions": "Analiza resúmenes. Usa TIPO=RESUMEN. Emisor: Banco o Broker. Detalle: Tipo de cuenta.",
                "prompt_template": "Analiza: {content}. Formato: YYYY-MM_RESUMEN_BANCO_DETALLE.",
                "filename_format": "{date}_RESUMEN_{issuer}_{detail}"
            }
        },
        {
            "id": "estados-contables",
            "name": "Estados Contables y Balances",
            "description": "Estilo Diego Cutignola: AAAA_CONTABLE_CLIENTE_DETALLE",
            "active": True,
            "trigger_type": "manual",
            "source_folder_id": "DYNAMIC",
            "target_folder_names": ["Balances_Oficiales"],
            "agent_config": {
                "model": {"name": "gemini-3-pro-preview", "temperature": 0.1, "max_tokens": 4096},
                "instructions": "Analiza Balances. Usa TIPO=CONTABLE. Emisor: Nombre del Cliente. Detalle: Estados Contables.",
                "prompt_template": "Analiza: {content}. Formato: YYYY_CONTABLE_CLIENTE_Estados_Contables.",
                "filename_format": "{date}_CONTABLE_{issuer}_Estados_Contables"
            }
        }
    ]
    
    for algo in diego_algorithms:
        try:
            if not db_manager.find("id", algo["id"]):
                db_manager.insert(algo)
                logger.info(f"Seeded algorithm: {algo['id']}")
        except Exception as e:
            logger.error(f"Failed to seed {algo['id']}: {e}")

# Run seeding
seed_default_algorithms()

# OAuth Security Manager
oauth_manager = None
try:
    oauth_client_id = get_secret("oauth-client-id")
    if oauth_client_id:
        allowed_domains = get_secret("oauth-allowed-domains").split(",")

        # Try to get allowed_emails, but handle if secret doesn't exist
        try:
            allowed_emails = get_secret("oauth-allowed-emails").split(",")
        except Exception:
            # Secret doesn't exist or other error - default to empty list
            allowed_emails = []

        oauth_manager = OAuthSecurityManager(
            client_id=oauth_client_id,
            allowed_domains=[d.strip() for d in allowed_domains if d.strip()],
            allowed_emails=[e.strip() for e in allowed_emails if e.strip()],
            require_domain_match=True
        )
        logger.info(f"OAuth Security Manager initialized:")
        logger.info(f"  - Domains: {allowed_domains}")
        logger.info(f"  - Specific emails: {allowed_emails if allowed_emails else 'None'}")
    else:
        logger.warning("OAuth not configured - client_id not found")
except Exception as e:
    logger.warning(f"OAuth not configured: {e}. OAuth endpoints will be disabled.")
    oauth_manager = None

# Cloud Tasks Configuration
GCP_PROJECT = os.environ.get("GCP_PROJECT")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
TASKS_QUEUE = os.environ.get("TASKS_QUEUE", "document-processing-queue")
WORKER_URL = os.environ.get("WORKER_URL")

if not all([GCP_PROJECT, WORKER_URL]):
    logger.warning("Cloud Tasks not fully configured. Task dispatch will fail.")

# FastAPI App
app = FastAPI(
    title="API Server - RenameDriverFolders",
    description="API Gateway for document processing jobs",
    version="2.0.0"
)

# CORS Configuration
cors_origins_str = get_secret("cors-allowed-origins") or os.environ.get("CORS_ALLOWED_ORIGINS", "")
if cors_origins_str:
    CORS_ORIGINS = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
else:
    logger.warning("CORS not configured. Defaulting to empty list (STRRICT MODE)")
    # Default to empty list instead of "*" for security
    CORS_ORIGINS = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Goog-IAP-JWT-Assertion"],
)
logger.info(f"CORS configured for origins: {CORS_ORIGINS}")

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

app.add_middleware(SecurityHeadersMiddleware)
logger.info("Security headers middleware enabled")

# Cloud Tasks Client
try:
    tasks_client = tasks_v2.CloudTasksClient()
except Exception as e:
    logger.warning(f"Cloud Tasks client initialization failed: {e}")
    tasks_client = None


# --- Request/Response Models ---

class ManualJobRequest(BaseModel):
    """Request for manual job submission with input validation."""
    folder_id: str
    job_type: Optional[str] = "generic"
    
    @validator('folder_id')
    def validate_folder_id(cls, v):
        # Relaxed logic: Google Drive IDs are alphanumeric with - and _
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid folder_id format')
        return v

class ModelConfig(BaseModel):
    # Support modern Gemini models 2.5, 3.0 series
    name: str = "gemini-2.5-flash"
    temperature: float = 0.1
    max_tokens: int = 4096

class AgentConfig(BaseModel):
    model: ModelConfig
    instructions: str
    prompt_template: str
    filename_format: str
    output_schema: Optional[dict] = None

class JobConfig(BaseModel):
    """Strict model for job configuration to prevent mass assignment."""
    id: str
    name: str
    description: Optional[str] = ""
    active: bool = True
    trigger_type: str = "manual"
    schedule: Optional[str] = None
    source_folder_id: str
    target_folder_names: list[str] = ["Procesados"]
    agent_config: AgentConfig

    @validator('id', 'source_folder_id')
    def validate_ids(cls, v):
        if v != "DYNAMIC" and not re.match(r'^[a-zA-Z0-9_-]{5,50}$', v):
            raise ValueError(f'Invalid ID format: {v}')
        return v
    
    @validator('trigger_type')
    def validate_trigger(cls, v):
        if v not in ["manual", "scheduled"]:
            raise ValueError('trigger_type must be manual or scheduled')
        return v


class JobResponse(BaseModel):
    """Response for job submission."""
    status: str
    message: str
    job_id: Optional[str] = None
    task_id: Optional[str] = None


# --- Helper Functions ---

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


def create_cloud_task(payload: dict) -> str:
    """
    Create a task in Google Cloud Tasks.
    Crea una tarea en Google Cloud Tasks.

    Args:
        payload: Task payload to send to worker.

    Returns:
        Task ID.
    """
    logger.info("="*80)
    logger.info("🔧 CREATING CLOUD TASK - STARTING DEBUG")
    logger.info("="*80)

    if not tasks_client:
        logger.error("❌ tasks_client is None")
        raise HTTPException(
            status_code=500,
            detail="Cloud Tasks client not initialized"
        )
    logger.info(f"✅ tasks_client initialized: {type(tasks_client)}")

    if not all([GCP_PROJECT, GCP_LOCATION, TASKS_QUEUE, WORKER_URL]):
        logger.error(f"❌ Cloud Tasks configuration incomplete:")
        logger.error(f"   GCP_PROJECT: {GCP_PROJECT}")
        logger.error(f"   GCP_LOCATION: {GCP_LOCATION}")
        logger.error(f"   TASKS_QUEUE: {TASKS_QUEUE}")
        logger.error(f"   WORKER_URL: {WORKER_URL}")
        raise HTTPException(
            status_code=500,
            detail="Cloud Tasks configuration incomplete"
        )
    logger.info(f"✅ Cloud Tasks config validated:")
    logger.info(f"   GCP_PROJECT: {GCP_PROJECT}")
    logger.info(f"   GCP_LOCATION: {GCP_LOCATION}")
    logger.info(f"   TASKS_QUEUE: {TASKS_QUEUE}")
    logger.info(f"   WORKER_URL: {WORKER_URL}")

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
    logger.info(f"✅ Task structure created:")
    logger.info(f"   http_method: {task['http_request']['http_method']}")
    logger.info(f"   url: {task['http_request']['url']}")
    logger.info(f"   headers: {task['http_request']['headers']}")
    logger.info(f"   body length: {len(task['http_request']['body'])} bytes")

    # Add OIDC token for authentication
    # Use WORKER_SERVICE_ACCOUNT env var, or fall back to default compute SA
    # Compute Engine default SA usually has Cloud Tasks permissions
    worker_sa = os.environ.get("WORKER_SERVICE_ACCOUNT")
    if not worker_sa:
        worker_sa = f"{GCP_PROJECT}@developer.gserviceaccount.com"
        logger.info(f"Using Compute Engine default SA: {worker_sa}")
    else:
        logger.info(f"Using configured SA: {worker_sa}")

    task["http_request"]["oidc_token"] = {
        "service_account_email": worker_sa,
        "audience": WORKER_URL
    }
    logger.info(f"✅ OIDC Token configured:")
    logger.info(f"   service_account_email: {task['http_request']['oidc_token']['service_account_email']}")
    logger.info(f"   audience: {task['http_request']['oidc_token']['audience']}")

    # Log the full task structure (be careful with sensitive data)
    logger.info(f"📋 Full task structure (JSON):")
    logger.info(f"{json.dumps(task, indent=2, default=str)}")

    # Create task
    try:
        logger.info("🚀 Calling tasks_client.create_task()...")
        parent = tasks_client.queue_path(GCP_PROJECT, GCP_LOCATION, TASKS_QUEUE)
        logger.info(f"   Queue path constructed: {parent}")

        # Log expected format for debugging
        expected_path = f"projects/{GCP_PROJECT}/locations/{GCP_LOCATION}/queues/{TASKS_QUEUE}"
        logger.info(f"   Expected path format: {expected_path}")
        logger.info(f"   Path matches expected: {parent == expected_path}")

        logger.info("   Sending request to Cloud Tasks API...")
        response = tasks_client.create_task(request={"parent": parent, "task": task})

        logger.info(f"✅ Cloud Tasks API response received")
        logger.info(f"   response type: {type(response)}")
        logger.info(f"   response.name: {response.name}")

        task_id = response.name.split("/")[-1]
        logger.info(f"✅ Task created successfully: {task_id}")
        logger.info("="*80)

        return task_id

    except Exception as e:
        logger.error(f"❌ ERROR in tasks_client.create_task():")
        logger.error(f"   Exception type: {type(e).__name__}")
        logger.error(f"   Exception message: {str(e)}")
        logger.error(f"   Exception args: {e.args}")

        # Log full traceback if available
        import traceback
        logger.error(f"   Full traceback:\n{traceback.format_exc()}")

        logger.info("="*80)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create task: {str(e)}"
        )


def verify_auth(request: Request) -> dict:
    """
    Unified authentication with IAP priority and legacy OAuth fallback.
    Enforces domain authorization and rate limiting globally.
    """
    user_info = None
    
    # 1. Try IAP (Priority)
    iap_jwt = request.headers.get("X-Goog-IAP-JWT-Assertion")
    if iap_jwt:
        try:
            from google.auth.transport import requests as auth_requests
            from google.oauth2 import id_token
            expected_audience = os.getenv("IAP_AUDIENCE")
            
            payload = id_token.verify_oauth2_token(
                iap_jwt, 
                auth_requests.Request(),
                audience=expected_audience
            )
            
            if payload.get("iss") != "https://cloud.google.com/iap":
                raise ValueError("Invalid issuer")
                
            user_info = {
                "email": payload.get("email"),
                "sub": payload.get("sub"),
                "name": payload.get("name", ""),
                "domain": payload.get("email", "").split("@")[-1],
                "auth_type": "iap"
            }
        except Exception as e:
            logger.error(f"IAP verification failed: {e}")
            if os.environ.get("ENV") == "production":
                raise HTTPException(status_code=401, detail="Missing or invalid IAP assertion")

    # 2. Try legacy OAuth (Fallback/Dev)
    if not user_info:
        if not oauth_manager:
            raise HTTPException(status_code=503, detail="Authentication server unavailable")
            
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required (IAP or Bearer)")
            
        token = auth_header.split("Bearer ")[1]
        try:
            user_info = oauth_manager.verify_token(token)
            user_info["auth_type"] = "oauth"
        except Exception as e:
            logger.warning(f"OAuth verification failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid session")

    # 3. Enforce Authorization (Domain check)
    if not oauth_manager.is_authorized(user_info):
        logger.warning(f"Access denied for domain: {user_info.get('domain')}")
        raise HTTPException(status_code=403, detail="Unauthorized domain access")

    # 4. Enforce Rate Limiting (increased from 10 to 30 for frontend refresh patterns)
    if not oauth_manager.check_rate_limit(user_info["email"], max_requests=30):
        logger.warning(f"Rate limit exceeded: {user_info['email']}")
        raise HTTPException(status_code=429, detail="Too many requests. Please wait 1 minute.")
        
    return user_info

def get_current_user(request: Request) -> dict:
    """Unified authentication dependency for protected endpoints."""
    return verify_auth(request)


# --- API Endpoints ---

@app.get("/api/v1/auth/whoami")
async def whoami(request: Request):
    """
    Returns the current authenticated user info.
    Retorna la información del usuario autenticado actual.
    Does not raise 401 if unauthenticated to avoid console noise.
    """
    try:
        user = verify_auth(request)
        return {
            "status": "success",
            "user": user
        }
    except HTTPException:
        return {
            "status": "success",
            "authenticated": False,
            "user": None
        }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "api-server",
        "version": "2.0.0",
        "iap_enabled": "X-Goog-IAP-JWT-Assertion" in os.environ,
        "auth_enabled": oauth_manager is not None
    }

@app.get("/api/v1/algorithms")
async def list_algorithms(user: dict = Depends(get_current_user)):
    """
    List all available document classification algorithms.
    """
    try:
        # Crear un DatabaseManager temporal para la tabla document_algorithms
        algorithms_manager = DatabaseManager(
            table_name="document_algorithms",
            use_supabase=True
        )
        algorithms = algorithms_manager.find_all()
        # Filtrar solo activos
        active_algorithms = [alg for alg in algorithms if alg.get("is_active", True)]
        return active_algorithms
    except Exception as e:
        logger.error(f"Failed to fetch algorithms: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch algorithms: {str(e)}"
        )

# Global Error Handler for Security (Anti-Leakage)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"UNHANDLED EXCEPTION: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected error occurred. Please contact the administrator."
        }
    )


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
    
    # Check if job config exists in DB, if not create it (Auto-seeding)
    existing_jobs = db_manager.find("id", job_id)
    if not existing_jobs:
        logger.info(f"Job config '{job_id}' not found. Seeding default configuration.")
        
        # Default configuration for manual generic job
        default_job_config = {
            "id": job_id,
            "name": f"Manual Job {job_request.job_type.capitalize()}",
            "description": "Auto-generated job configuration for manual triggers",
            "active": True,
            "trigger_type": "manual",
            "schedule": None,
            "source_folder_id": "DYNAMIC",
            "target_folder_names": ["*"],
            "agent_config": {
                "model": {
                    "name": "gemini-2.0-flash-exp",
                    "temperature": 0.3,
                    "max_tokens": 4096
                },
                "instructions": "Analiza el documento y extrae la fecha y palabras clave principales para renombrado.",
                "output_schema": {
                    "date": "str",
                    "keywords": "list"
                },
                "prompt_template": "Analiza el documento '{original_filename}'. Contenido: {file_content}. Extrae la fecha (YYYY-MM-DD) y 3 keywords descriptivos. JSON output keys: date, keywords.",
                "filename_format": "{date}_{keywords}_{ext}"
            }
        }
        
        try:
            db_manager.insert(default_job_config)
            logger.info(f"Seeded default configuration for '{job_id}'")
        except Exception as e:
            logger.error(f"Failed to seed default job config: {e}")
            # Continue anyway, maybe it exists but find failed? Or worker will fail.
            
    # Log execution for audit trail (before task creation)
    import time
    from datetime import datetime
    
    execution_log = {
        "id": f"exec-{int(time.time() * 1000)}",  # timestamp-based ID
        "user_email": user["email"],
        "user_name": user.get("name", "Unknown"),
        "folder_id": job_request.folder_id,
        "job_type": job_request.job_type,
        "job_config_id": job_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "submitted",
        "task_id": None  # Will be updated after task creation
    }

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
    
    try:
        executions_manager.insert(execution_log)
        logger.info(f"Job execution logged: {execution_log['id']}")
    except Exception as e:
        logger.error(f"Failed to log execution (non-fatal): {e}")
        # Continue anyway - logging failure shouldn't block job submission
    
    try:
        task_id = create_cloud_task(payload)
        
        # Update execution log with task_id
        try:
            executions_manager.update("id", execution_log["id"], {"task_id": task_id})
        except Exception as e:
            logger.error(f"Failed to update execution with task_id (non-fatal): {e}")
        
        logger.info(
            f"Manual job accepted. User: {user['email']}, "
            f"Folder: {job_request.folder_id}, Task: {task_id}"
        )
        
        return JobResponse(
            status="accepted",
            message="Job submitted successfully and is being processed",
            job_id=job_id,
            task_id=task_id
        )
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create task: {str(e)}"
        )


@app.post("/api/v1/jobs/scheduled")
async def process_scheduled_jobs(request: Request):
    """
    Process all scheduled jobs.
    Procesar todos los trabajos programados.
    
    Triggered by Cloud Scheduler with OIDC authentication.
    No OAuth required (service-to-service).
    """
    logger.info("Scheduled jobs trigger received")
    
    # Verify OIDC token from Cloud Scheduler
    verify_scheduler_token(request)
    
    # Get all active scheduled jobs from database
    try:
        all_jobs = db_manager.find_all()
        scheduled_jobs = [
            job for job in all_jobs
            if job.get("active", True) and job.get("trigger_type") == "scheduled"
        ]
        
        logger.info(f"Found {len(scheduled_jobs)} active scheduled jobs")
        
        if not scheduled_jobs:
            return {
                "status": "success",
                "message": "No scheduled jobs configured",
                "jobs_processed": 0
            }
        
        # Create tasks for each job
        results = []
        for job in scheduled_jobs:
            job_id = job.get("id")
            
            payload = {
                "job_id": job_id,
                "trigger_type": "scheduled"
            }
            
            try:
                task_id = create_cloud_task(payload)
                results.append({
                    "job_id": job_id,
                    "status": "task_created",
                    "task_id": task_id
                })
                logger.info(f"Task created for scheduled job: {job_id}")
                
            except Exception as e:
                logger.error(f"Error creating task for job {job_id}: {e}")
                results.append({
                    "job_id": job_id,
                    "status": "error",
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r["status"] == "task_created")
        
        return {
            "status": "success",
            "message": f"Processed {len(scheduled_jobs)} scheduled jobs",
            "jobs_processed": len(scheduled_jobs),
            "tasks_created": success_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error processing scheduled jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process scheduled jobs: {str(e)}"
        )


@app.get("/api/v1/jobs")
async def list_jobs(user: dict = Depends(get_current_user)):
    """
    List all available job configurations.
    """
    try:
        all_jobs = db_manager.find_all()
        
        # Filter sensitive info and ensure ID is present
        jobs_summary = []
        for job in all_jobs:
            # Defensive check: ensure id is present
            job_id = job.get("id") or job.get("job_id")
            
            # Fallback if both are missing (e.g., corrupted or old data)
            if not job_id and job.get("source_folder_id"):
                job_id = f"job-folder-{job.get('source_folder_id')[:8]}"
            
            if not job_id:
                logger.warning(f"Skipping job configuration with missing ID: {job}")
                continue
                
            jobs_summary.append({
                "id": job_id,
                "name": job.get("name", job_id),
                "description": job.get("description", ""),
                "active": job.get("active", True),
                "trigger_type": job.get("trigger_type", "manual"),
                "schedule": job.get("schedule")
            })
        
        return {
            "status": "success",
            "jobs": jobs_summary,
            "total": len(jobs_summary)
        }
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list jobs: {str(e)}"
        )


@app.post("/api/v1/jobs")
async def create_job(job_config: JobConfig, user: dict = Depends(get_current_user)):
    """
    Create a new job configuration with strict validation.
    """
    try:
        # Check if already exists
        existing = db_manager.find("id", job_config.id)
        if existing:
            raise HTTPException(status_code=409, detail=f"ID '{job_config.id}' already exists")
            
        # Insert into database using dict representation of validated model
        db_manager.insert(job_config.dict())
        
        logger.info(f"Job '{job_config.id}' created by {user['email']}")
        return {"status": "success", "message": f"Job '{job_config.id}' created"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail="Failed to persist configuration")


@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: str, user: dict = Depends(get_current_user)):
    """
    Get a single job configuration by ID.
    Obtener una configuración de trabajo individual por ID.
    """
    try:
        jobs = db_manager.find("id", job_id)
        if not jobs:
            raise HTTPException(status_code=404, detail="Configuration not found")
        return jobs[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Database retrieval failed")


@app.put("/api/v1/jobs/{job_id}")
async def update_job(job_id: str, job_config: JobConfig, user: dict = Depends(get_current_user)):
    """
    Update configuration using JobConfig model for hardening.
    """
    try:
        existing = db_manager.find("id", job_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        # Enforce ID consistency
        if job_config.id != job_id:
            raise HTTPException(status_code=400, detail="Path ID and body ID mismatch")
        
        db_manager.update("id", job_id, job_config.dict())
        logger.info(f"Job '{job_id}' updated by {user['email']}")
        
        return {"status": "success", "message": f"Job '{job_id}' updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Update failed")


@app.delete("/api/v1/jobs/{job_id}")
async def delete_job(job_id: str, user: dict = Depends(get_current_user)):
    """
    Delete a job configuration.
    """
    try:
        existing = db_manager.find("id", job_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Configuration not found")
            
        db_manager.delete("id", job_id)
        logger.info(f"Job '{job_id}' deleted by {user['email']}")
        return {"status": "success", "message": f"Job '{job_id}' deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Deletion failed")


@app.get("/api/v1/audit-logs")
async def get_audit_logs(limit: int = 100, user: dict = Depends(get_current_user)):
    """
    Get audit logs for system activity.
    """
    
    # Validate limit
    if limit > 1000:
        limit = 1000
    
    try:
        # Get all job executions (newest first)
        all_executions = executions_manager.find_all()
        
        # Sort by timestamp (newest first)
        all_executions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Limit results
        limited_executions = all_executions[:limit]
        
        # Convert to audit log format
        audit_logs = []
        for exec in limited_executions:
            audit_logs.append({
                "id": exec.get("id"),
                "timestamp": exec.get("timestamp"),
                "user_email": exec.get("user_email"),
                "user_name": exec.get("user_name"),
                "action": "job_submitted",
                "status": exec.get("status", "submitted"),
                "details": f"Folder: {exec.get('folder_id')} | Type: {exec.get('job_type')}"
            })
        
        logger.info(f"Audit logs requested by {user['email']}, limit={limit}, returned {len(audit_logs)} logs")
        
        return {
            "status": "success",
            "logs": audit_logs,
            "total": len(audit_logs)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )


# --- Error Handlers ---

@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=401,
        content={
            "error": "Unauthorized",
            "message": "Valid authentication token required",
            "detail": exc.detail
        }
    )


@app.get("/api/v1/executions/{execution_id}/logs")
async def export_execution_logs(execution_id: str, user: dict = Depends(get_current_user)):
    """
    Export execution logs as TXT file for download.

    Security:
    - User must be authenticated
    - User can only export their own executions
    """
    logger.info(f"User {user['email']} requesting logs for execution {execution_id}")

    try:
        executions = executions_manager.find("id", execution_id)
        if not executions:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

        execution = executions[0]

        # Verify user owns this execution
        if execution.get("user_email") != user.get("email"):
            logger.warning(f"User {user['email']} attempted to access logs of execution owned by {execution.get('user_email')}")
            raise HTTPException(status_code=403, detail="You can only export your own executions")

        # Build TXT log content
        log_lines = []
        log_lines.append("=" * 80)
        log_lines.append("LOG DE EJECUCIÓN - RENAME DRIVER FOLDERS")
        log_lines.append("=" * 80)
        log_lines.append(f"ID de Ejecución: {execution['id']}")
        log_lines.append(f"Fecha: {execution.get('timestamp', 'N/A')}")
        log_lines.append(f"Usuario: {execution.get('user_email', 'N/A')}")
        log_lines.append(f"Folder ID: {execution.get('folder_id', 'N/A')}")
        log_lines.append(f"Status: {execution.get('status', 'N/A')}")
        log_lines.append("")

        log_lines.append("-" * 80)
        log_lines.append("DETALLES")
        log_lines.append("-" * 80)
        log_lines.append(execution.get('details', 'Sin detalles disponibles'))
        log_lines.append("")

        stats = execution.get('stats', {})
        if stats:
            log_lines.append("-" * 80)
            log_lines.append("ESTADÍSTICAS")
            log_lines.append("-" * 80)
            log_lines.append(f"Archivos Procesados: {stats.get('files_processed', 0)}")
            log_lines.append(f"Archivos Renombrados: {stats.get('files_renamed', 0)}")
            log_lines.append(f"Errores: {stats.get('errors', 0)}")
            log_lines.append("")

        log_lines.append("-" * 80)
        log_lines.append("TIMESTAMPS")
        log_lines.append("-" * 80)
        log_lines.append(f"Created: {execution.get('timestamp', 'N/A')}")
        log_lines.append(f"Submitted: {execution.get('submitted_at', 'N/A')}")
        log_lines.append("")

        log_lines.append("=" * 80)
        log_lines.append("FIN DEL LOG")
        log_lines.append("=" * 80)

        log_content = "\n".join(log_lines)

        from fastapi.responses import Response
        return Response(
            content=log_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=logs_{execution_id}.txt"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting logs for {execution_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export logs: {str(e)}"
        )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=403,
        content={
            "error": "Forbidden",
            "message": "Your domain is not authorized to access this resource",
            "detail": exc.detail
        }
    )


@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": "Rate limit exceeded",
            "detail": exc.detail
        }
    )


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API server in development mode")
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)