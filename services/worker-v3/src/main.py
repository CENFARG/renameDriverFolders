"""
Worker Renombrador - Multi-Job Processing
==========================================

Worker service for document renaming jobs.
Thin orchestrator — all logic in extracted modules.

:created:   2025-12-05
:filename:  main.py
:path:      services/worker-v3/src/main.py
:author:    amBotHs + CENF
:version:   3.0.0
:status:    Development
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from core_renombrador.config_manager import ConfigManager
from core_renombrador.database_manager import DatabaseManager
from core_renombrador.logger_manager import LoggerManager
from core_renombrador.file_manager import FileManager
from core_renombrador.agent_factory import AgentFactory
from core_renombrador.content_extractor import ContentExtractor

from config import WorkerConfig, get_credentials, create_credentials_from_token
from models import TaskPayload, JobRunRequest
from job_loader import load_job_config, get_all_active_jobs
from job_processor import process_job

# --- Initialization ---
config_manager = ConfigManager(config_path="config.json")
LoggerManager.initialize(config_manager)
logger = LoggerManager.get_logger(__name__)

worker_config = WorkerConfig()

file_manager = FileManager(base_path="./data", config_manager=config_manager)

if worker_config.use_supabase:
    db_manager = DatabaseManager(use_supabase=True, table_name="jobs")
    executions_manager = DatabaseManager(use_supabase=True, table_name="job_executions")
elif worker_config.use_gcs:
    db_manager = DatabaseManager(use_gcs=True, table_name="jobs")
    executions_manager = DatabaseManager(use_gcs=True, table_name="job_executions")
else:
    db_manager = DatabaseManager(file_manager=file_manager, db_path="data/jobs.json")
    executions_manager = DatabaseManager(file_manager=file_manager, db_path="data/job_executions.json")

agent_factory = AgentFactory(database_manager=db_manager, config_manager=config_manager)
content_extractor = ContentExtractor(enable_ocr=worker_config.enable_ocr)

# Inject dependencies into modules
import job_loader
job_loader.db_manager = db_manager

import job_processor
job_processor.agent_factory = agent_factory
job_processor.content_extractor = content_extractor

logger.info(f"Worker initialized (OCR: {worker_config.enable_ocr})")


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Worker starting... Config loaded.")
    yield
    logger.info("Shutting down Worker...")


app = FastAPI(
    title="Worker Renombrador",
    description="Multi-job document processing worker",
    version="3.0.0",
    lifespan=lifespan,
)


# --- Endpoints ---

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "worker-renombrador", "version": "3.0.0"}


@app.post("/run-task")
async def run_task(request: Request):
    """Main endpoint triggered by Cloud Tasks."""
    logger.info("Task received from Cloud Tasks")

    try:
        payload = await request.json()
        task = TaskPayload(**payload)
    except Exception as e:
        logger.error(f"Invalid task payload: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    if task.user_credentials:
        logger.info(f"Using user OAuth credentials for {task.user_credentials.email}")
        credentials = create_credentials_from_token(task.user_credentials.access_token)
    else:
        logger.info("Using Application Default Credentials (scheduled job)")
        credentials = get_credentials()

    if task.job_id:
        job_config = load_job_config(task.job_id)
        if not job_config:
            raise HTTPException(status_code=404, detail=f"Job '{task.job_id}' not found or inactive")

        if task.execution_id:
            try:
                executions_manager.update("id", task.execution_id, {"status": "processing"})
            except Exception as e:
                logger.warning(f"Failed to update execution status (non-fatal): {e}")

        try:
            result = process_job(job_config, task.folder_id, credentials)
            if task.execution_id:
                executions_manager.update("id", task.execution_id, {
                    "status": "completed" if result.get("status") == "success" else "failed",
                    "details": f"Processed {result.get('stats', {}).get('files_renamed', 0)} files",
                })
            return result
        except Exception as e:
            logger.error(f"Error in process_job: {e}")
            if task.execution_id:
                executions_manager.update("id", task.execution_id, {"status": "failed", "details": str(e)})
            raise HTTPException(status_code=500, detail=str(e))
    else:
        active_jobs = get_all_active_jobs()
        scheduled_jobs = [j for j in active_jobs if j.get("trigger_type") == "scheduled"]
        results = [process_job(job, credentials=credentials) for job in scheduled_jobs]
        return {"status": "success", "jobs_processed": len(results), "results": results}


@app.post("/run-job")
async def run_job(request: JobRunRequest):
    """Run a specific job by ID (manual trigger)."""
    logger.info(f"Manual job run requested: {request.job_id}")

    job_config = load_job_config(request.job_id)
    if not job_config:
        raise HTTPException(status_code=404, detail=f"Job '{request.job_id}' not found or inactive")

    credentials = get_credentials()
    return process_job(job_config, request.folder_id, credentials)


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting worker in development mode")
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
