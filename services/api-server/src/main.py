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

# OAuth Security Manager
oauth_manager = None
try:
    oauth_client_id = get_secret("oauth-client-id")
    if oauth_client_id:
        allowed_domains = get_secret("oauth-allowed-domains").split(",")
        oauth_manager = OAuthSecurityManager(
            client_id=oauth_client_id,
            allowed_domains=[d.strip() for d in allowed_domains if d.strip()],
            require_domain_match=True
        )
        logger.info(f"OAuth Security Manager initialized for domains: {allowed_domains}")
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
    logger.warning("No CORS origins configured, allowing all (INSECURE)")
    CORS_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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
        # Google Drive folder IDs are alphanumeric + hyphens/underscores
        if not re.match(r'^[a-zA-Z0-9_-]{20,50}$', v):
            raise ValueError('Invalid folder_id format')
        return v
    
    @validator('job_type')
    def validate_job_type(cls, v):
        if v and len(v) > 50:
            raise ValueError('job_type too long')
        # Sanitize special characters
        return re.sub(r'[^\w\s-]', '', v) if v else v


class JobResponse(BaseModel):
    """Response for job submission."""
    status: str
    message: str
    job_id: Optional[str] = None
    task_id: Optional[str] = None


# --- Helper Functions ---

def create_cloud_task(payload: dict) -> str:
    """
    Create a task in Google Cloud Tasks.
    Crea una tarea en Google Cloud Tasks.
    
    Args:
        payload: Task payload to send to worker.
        
    Returns:
        Task ID.
    """
    if not tasks_client:
        raise HTTPException(
            status_code=500,
            detail="Cloud Tasks client not initialized"
        )
    
    if not all([GCP_PROJECT, GCP_LOCATION, TASKS_QUEUE, WORKER_URL]):
        raise HTTPException(
            status_code=500,
            detail="Cloud Tasks configuration incomplete"
        )
    
    # Build task
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{WORKER_URL}/run-task",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(payload).encode(),
        }
    }
    
    # Add OIDC token for authentication
    task["http_request"]["oidc_token"] = {
        "service_account_email": os.environ.get("WORKER_SERVICE_ACCOUNT")
    }
    
    # Create task
    parent = tasks_client.queue_path(GCP_PROJECT, GCP_LOCATION, TASKS_QUEUE)
    response = tasks_client.create_task(request={"parent": parent, "task": task})
    
    task_id = response.name.split("/")[-1]
    logger.info(f"Task created: {task_id} for worker {WORKER_URL}")
    
    return task_id


def verify_oauth_token(request: Request) -> dict:
    """
    Verify OAuth token from request.
    Verifica token OAuth desde request.
    
    Returns:
        User info dict.
    """
    if not oauth_manager:
        raise HTTPException(
            status_code=503,
            detail="OAuth not configured on server"
        )
    
    # Extract token from Authorization header (FastAPI compatible)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )
    
    token = auth_header.split("Bearer ")[1]
    
    # Verify token directly
    try:
        user_info = oauth_manager.verify_token(token)
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token"
        )
    
    if not oauth_manager.is_authorized(user_info):
        raise HTTPException(
            status_code=403,
            detail=f"Domain {user_info.get('domain')} is not authorized"
        )
    
    # Check rate limit
    if not oauth_manager.check_rate_limit(user_info["email"], max_requests=10, window_minutes=1):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before making more requests."
        )
    
    return user_info


def verify_scheduler_token(request: Request) -> dict:
    """
    Verify OIDC token from Cloud Scheduler.
    Verifica token OIDC desde Cloud Scheduler.
    
    Returns:
        Token info dict.
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    try:
        # Extract token
        token = auth_header.split("Bearer ")[1]
        
        # Verify OIDC token
        # Expected audience is this service URL (FastAPI: use base_url instead of url_root)
        audience = str(request.base_url).rstrip("/")
        
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience
        )
        
        # Verify it's from a Google service account
        email = idinfo.get("email", "")
        if not email.endswith("gserviceaccount.com"):
            raise HTTPException(
                status_code=403,
                detail="Invalid service account"
            )
        
        logger.info(f"Scheduler request authenticated from {email}")
        return idinfo
        
    except Exception as e:
        logger.error(f"OIDC verification failed: {e}")
        raise HTTPException(
            status_code=403,
            detail=f"OIDC verification failed: {str(e)}"
        )


def get_current_user(request: Request) -> dict:
    """
    Authentication dependency for protected endpoints.
    Verifies OAuth token and enforces rate limiting.
    
    Returns:
        User info dict if authenticated.
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if unauthorized, 429 if rate limited.
    """
    if not oauth_manager:
        raise HTTPException(
            status_code=503,
            detail="OAuth not configured"
        )
    
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning(f"Missing or invalid Authorization header from {request.client.host}")
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )
    
    token = auth_header.split("Bearer ")[1]
    
    # Verify token directly
    try:
        user = oauth_manager.verify_token(token)
    except Exception as e:
        logger.warning(f"Token verification failed from {request.client.host}: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    if not user:
        logger.warning(f"Authentication failed from {request.client.host}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing token"
        )
    
    # Check authorization (domain whitelist)
    if not oauth_manager.is_authorized(user):
        logger.warning(f"Unauthorized access attempt: {user['email']} (domain: {user.get('domain')})")
        raise HTTPException(
            status_code=403,
            detail=f"Unauthorized domain: {user.get('domain')}"
        )
    
    # Check rate limit
    if not oauth_manager.check_rate_limit(user["email"]):
        logger.warning(f"Rate limit exceeded: {user['email']}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 10 requests per minute."
        )
    
    # Log successful authentication
    logger.info(f"Authenticated user: {user['email']} from {request.client.host}")
    return user


# --- API Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "api-server",
        "version": "2.0.0",
        "oauth_enabled": oauth_manager is not None,
        "tasks_enabled": tasks_client is not None
    }


@app.post("/api/v1/jobs/manual", response_model=JobResponse)
async def submit_manual_job(
    job_request: ManualJobRequest,
    request: Request,
    user: dict = Depends(get_current_user)  # Enforces OAuth authentication
):
    """
    Submit a manual job for processing.
    Enviar un trabajo manual para procesamiento.
    
    Requires OAuth authentication.
    User must be from authorized domain.
    
    Headers:
        Authorization: Bearer <google_oauth_token>
    
    Body:
        {
            "folder_id": "1AbCdEf...",
            "job_type": "invoice" | "report" | "generic"
        }
    """
    logger.info("Manual job submission received")
    
    # Verify OAuth token
    user_info = verify_oauth_token(request)
    
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
            
    # Create task payload
    payload = {
        "job_id": job_id,
        "folder_id": job_request.folder_id,
        "trigger_type": "manual",
        "submitted_by": user_info["email"]
    }
    
    try:
        task_id = create_cloud_task(payload)
        
        logger.info(
            f"Manual job accepted. User: {user_info['email']}, "
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
async def list_jobs(request: Request):
    """
    List all available jobs.
    Listar todos los trabajos disponibles.
    
    Requires OAuth authentication.
    """
    user_info = verify_oauth_token(request)
    
    try:
        all_jobs = db_manager.find_all()
        
        # Filter sensitive info
        jobs_summary = [
            {
                "id": job.get("id"),
                "name": job.get("name"),
                "description": job.get("description"),
                "active": job.get("active"),
                "trigger_type": job.get("trigger_type"),
                "schedule": job.get("schedule")
            }
            for job in all_jobs
        ]
        
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