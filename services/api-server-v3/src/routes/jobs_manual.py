"""
Jobs Manual — Manual job submission endpoint.
==============================================

Handles manual job submission with OAuth credentials,
auto-seeding of job configurations, and execution logging.

:created:   2026-05-06
:filename:  jobs_manual.py
:path:      services/api-server-v3/src/routes/jobs_manual.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from api_models import JobResponse
from cloud_tasks import sanitize_payload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["jobs"])

# Injected by main.py
db_manager = None
algorithms_manager = None
executions_manager = None
create_cloud_task = None


def _resolve_access_token(job_request, request: Request) -> str:
    """Extract OAuth access token from request body or Authorization header."""
    if job_request.access_token:
        logger.info(f"Using OAuth Access Token from request body: {job_request.access_token[:20]}...")
        return job_request.access_token

    logger.warning("No access_token in request body, falling back to Authorization header")
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="OAuth Access Token required (in request body or Authorization header)",
        )
    return auth_header.split("Bearer ")[1].strip()


def _find_or_seed_job_config(job_id: str, job_type: str):
    """Find existing job config or auto-seed from document_algorithms."""
    existing = db_manager.find("id", job_id)
    if existing:
        return

    logger.info(f"Job config '{job_id}' not found. Checking document_algorithms for '{job_type}'.")
    algorithm = algorithms_manager.find("id", job_type)

    if algorithm:
        _seed_from_algorithm(job_id, algorithm[0])
    else:
        _seed_default_config(job_id, job_type)


def _seed_from_algorithm(job_id: str, algo_config: dict):
    """Create job config from a document algorithm."""
    job_config = {
        "id": job_id,
        "name": algo_config["name"],
        "description": algo_config["description"],
        "active": True,
        "trigger_type": "manual",
        "schedule": None,
        "source_folder_id": "DYNAMIC",
        "target_folder_names": ["*"],
        "agent_config": {
            "model": {"name": "gemini-2.0-flash-exp", "temperature": 0.3, "max_tokens": 4096},
            "prompt_template": algo_config["extraction_prompt"],
            "filename_format": algo_config["filename_format"],
            "output_schema": algo_config["output_schema"],
            "instructions": algo_config["classification_criteria"],
        },
    }
    try:
        db_manager.insert(job_config)
        logger.info(f"Seeded algorithm-specific config for '{job_id}'")
    except Exception as e:
        logger.error(f"Failed to seed algorithm job config: {e}")


def _seed_default_config(job_id: str, job_type: str):
    """Create generic job config for unknown job types."""
    default_config = {
        "id": job_id,
        "name": f"Manual Job {job_type.capitalize()}",
        "description": "Auto-generated job configuration for manual triggers",
        "active": True,
        "trigger_type": "manual",
        "schedule": None,
        "source_folder_id": "DYNAMIC",
        "target_folder_names": ["*"],
        "agent_config": {
            "model": {"name": "gemini-2.0-flash-exp", "temperature": 0.3, "max_tokens": 4096},
            "instructions": "Analiza el documento y extrae la fecha y palabras clave principales para renombrado.",
            "output_schema": {"date": "str", "keywords": "list"},
            "prompt_template": "Analiza el documento '{original_filename}'. Contenido: {file_content}. Extrae la fecha (YYYY-MM-DD) y 3 keywords descriptivos. JSON output keys: date, keywords.",
            "filename_format": "{date}_{keywords}_{ext}",
        },
    }
    try:
        db_manager.insert(default_config)
        logger.info(f"Seeded default configuration for '{job_id}'")
    except Exception as e:
        logger.error(f"Failed to seed default job config: {e}")


def _create_execution_log(user: dict, job_request, job_id: str) -> dict:
    """Create an execution log entry for audit trail."""
    execution_id = f"exec-{int(time.time() * 1000)}"
    return {
        "id": execution_id,
        "user_email": user["email"],
        "user_name": user.get("name", "Unknown"),
        "folder_id": job_request.folder_id,
        "job_type": job_request.job_type,
        "job_config_id": job_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "submitted",
        "task_id": None,
    }


def _build_task_payload(job_id: str, job_request, user: dict, access_token: str, execution_id: str) -> dict:
    """Build the Cloud Task payload with user credentials."""
    return {
        "job_id": job_id,
        "folder_id": job_request.folder_id,
        "trigger_type": "manual",
        "submitted_by": user["email"],
        "execution_id": execution_id,
        "user_credentials": {
            "access_token": access_token,
            "email": user["email"],
            "name": user.get("name", "Unknown"),
            "scope": "https://www.googleapis.com/auth/drive",
        },
    }


@router.post("/jobs/manual", response_model=JobResponse)
async def submit_manual_job(job_request, request: Request, user: dict):
    """
    Submit a manual job for processing with user OAuth credentials.

    Flow:
    1. Resolve OAuth access token (body > header)
    2. Find or auto-seed job config
    3. Log execution for audit trail
    4. Create Cloud Task for worker
    """
    logger.info(f"Manual job submission from {user['email']}")

    access_token = _resolve_access_token(job_request, request)
    job_id = f"job-manual-{job_request.job_type}"
    _find_or_seed_job_config(job_id, job_request.job_type)

    execution_log = _create_execution_log(user, job_request, job_id)
    payload = _build_task_payload(job_id, job_request, user, access_token, execution_log["id"])

    logger.info(f"Creating task with sanitized payload: {sanitize_payload(payload)}")

    try:
        executions_manager.insert(execution_log)
        logger.info(f"Job execution logged: {execution_log['id']}")
    except Exception as e:
        logger.error(f"Failed to log execution (non-fatal): {e}")

    try:
        task_id = create_cloud_task(payload)
        try:
            executions_manager.update("id", execution_log["id"], {"task_id": task_id})
        except Exception as e:
            logger.error(f"Failed to update execution with task_id (non-fatal): {e}")

        logger.info(f"Manual job accepted. User: {user['email']}, Task: {task_id}")
        return JobResponse(
            status="accepted",
            message="Job submitted successfully and is being processed",
            job_id=job_id,
            task_id=task_id,
        )
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")
