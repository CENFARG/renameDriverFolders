"""
API Server - RenameDriverFolders
=================================

API Gateway for document processing jobs.
Thin orchestrator — all logic lives in extracted modules.

:created:   2025-12-05
:filename:  main.py
:path:      services/api-server-v3/src/main.py
:author:    amBotHs + CENF
:version:   3.0.0
:status:    Development
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from google.cloud import tasks_v2

from core_renombrador.config_manager import ConfigManager
from core_renombrador.logger_manager import LoggerManager
from core_renombrador.oauth_security import OAuthSecurityManager

from api_config import ApiConfig, get_secret
from cloud_tasks import create_cloud_task as _create_cloud_task
from error_handlers import register_error_handlers
from middleware import setup_middleware
from routes.algorithms import router as algorithms_router
from routes.audit import router as audit_router
from routes.auth_routes import router as auth_router
from routes.health import router as health_router
from routes.jobs import router as jobs_router
from routes.jobs_manual import router as jobs_manual_router
from routes.jobs_scheduled import router as jobs_scheduled_router
from routes.token_routes import router as token_router

load_dotenv()

# --- Initialization ---
config_manager = ConfigManager(config_path="config.json")
LoggerManager.initialize(config_manager)
logger = logging.getLogger(__name__)

api_config = ApiConfig()

# OAuth Security Manager
oauth_manager = None
try:
    oauth_client_id = get_secret("oauth-client-id")
    if oauth_client_id:
        allowed_domains = get_secret("oauth-allowed-domains").split(",")
        try:
            allowed_emails = get_secret("oauth-allowed-emails").split(",")
        except Exception:
            allowed_emails = []

        oauth_manager = OAuthSecurityManager(
            client_id=oauth_client_id,
            allowed_domains=[d.strip() for d in allowed_domains if d.strip()],
            allowed_emails=[e.strip() for e in allowed_emails if e.strip()],
            require_domain_match=True,
        )
        logger.info("OAuth Security Manager initialized")
    else:
        logger.warning("OAuth not configured - client_id not found")
except Exception as e:
    logger.warning(f"OAuth not configured: {e}")
    oauth_manager = None


# --- FastAPI App ---
app = FastAPI(
    title="API Server - RenameDriverFolders",
    description="API Gateway for document processing jobs",
    version="3.0.0",
)

setup_middleware(app, api_config)
register_error_handlers(app)

# Cloud Tasks client
try:
    _tasks_client = tasks_v2.CloudTasksClient()
except Exception as e:
    logger.warning(f"Cloud Tasks client initialization failed: {e}")
    _tasks_client = None


def create_cloud_task_wrapped(payload: dict) -> str:
    """Wrapper that injects config and handles client init."""
    if not _tasks_client:
        raise Exception("Cloud Tasks client not initialized")
    result = _create_cloud_task(payload, config=api_config)
    return result.name.split("/")[-1]


# --- Inject dependencies into route modules ---
from routes import (
    algorithms, audit, jobs, jobs_manual, jobs_scheduled,
)

algorithms.algorithms_manager = api_config.algorithms_manager
jobs.db_manager = api_config.db_manager
jobs.algorithms_manager = api_config.algorithms_manager
jobs_manual.db_manager = api_config.db_manager
jobs_manual.algorithms_manager = api_config.algorithms_manager
jobs_manual.executions_manager = api_config.executions_manager
jobs_manual.create_cloud_task = create_cloud_task_wrapped
jobs_scheduled.db_manager = api_config.db_manager
jobs_scheduled.create_cloud_task = create_cloud_task_wrapped
audit.executions_manager = api_config.executions_manager

# --- Include routers ---
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(token_router)
app.include_router(algorithms_router)
app.include_router(jobs_router)
app.include_router(jobs_manual_router)
app.include_router(jobs_scheduled_router)
app.include_router(audit_router)


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API server in development mode")
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
