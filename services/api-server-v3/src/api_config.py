"""
API Server Config — Configuration and initialization.
======================================================

Centralizes API server initialization: secrets, database managers,
Cloud Tasks config, and OAuth manager setup.

:created:   2026-05-05
:filename:  api_config.py
:path:      services/api-server-v3/src/api_config.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
import os

from google.cloud import secretmanager

from core_renombrador.config_manager import ConfigManager
from core_renombrador.logger_manager import LoggerManager
from core_renombrador.database_manager import DatabaseManager
from core_renombrador.file_manager import FileManager

logger = logging.getLogger(__name__)

DEFAULT_GCP_PROJECT = "cloud-functions-474716"


def get_secret(secret_id: str) -> str:
    """
    Retrieve a secret from env vars (local) or Google Secret Manager (prod).

    Args:
        secret_id: Secret identifier, e.g. "supabase-url".

    Returns:
        Secret value as string, or empty string on failure.
    """
    env_var = secret_id.upper().replace("-", "_")
    local_value = os.environ.get(env_var)

    if local_value:
        logger.info(f"Using local config for {secret_id}")
        return local_value.strip()

    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get("GCP_PROJECT_ID", DEFAULT_GCP_PROJECT)
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        logger.info(f"Using Secret Manager for {secret_id}")
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        logger.warning(f"Failed to get secret {secret_id}: {e}")
        return ""


class ApiConfig:
    """
    Centralized API server configuration.

    Initializes database managers, Cloud Tasks config, and OAuth.

    Attributes:
        db_manager: Jobs database manager.
        algorithms_manager: Algorithms database manager.
        executions_manager: Job executions database manager.
        gcp_project: GCP project ID for Cloud Tasks.
        gcp_location: GCP location for Cloud Tasks.
        tasks_queue: Cloud Tasks queue name.
        worker_url: Worker service URL.
        allowed_origins: CORS allowed origins.
    """

    def __init__(self):
        self.config_manager = ConfigManager(config_path="config.json")

        file_manager = FileManager(
            base_path="./data", config_manager=self.config_manager
        )

        use_supabase = os.environ.get("USE_SUPABASE", "false").lower() == "true"
        use_gcs = (
            os.environ.get("USE_GCS", "false").lower() == "true"
            or "GCS_BUCKET_NAME" in os.environ
        )

        if use_supabase:
            supabase_url = get_secret("supabase-url")
            supabase_key = get_secret("supabase-key")
            if supabase_url and supabase_key:
                os.environ["SUPABASE_URL"] = supabase_url
                os.environ["SUPABASE_KEY"] = supabase_key
            else:
                use_supabase = False

        self.db_manager = self._create_db_manager(
            use_supabase, use_gcs, file_manager, "jobs"
        )
        self.algorithms_manager = self._create_db_manager(
            use_supabase, use_gcs, file_manager, "document_algorithms"
        )
        self.executions_manager = self._create_db_manager(
            use_supabase, use_gcs, file_manager, "job_executions"
        )

        # Cloud Tasks
        self.gcp_project = os.environ.get("GCP_PROJECT", DEFAULT_GCP_PROJECT)
        self.gcp_location = os.environ.get("GCP_LOCATION", "us-central1")
        self.tasks_queue = os.environ.get("TASKS_QUEUE", "renombrador-queue")
        self.worker_url = os.environ.get(
            "WORKER_URL",
            f"https://worker-v3-{self.gcp_project}.ue.a.run.app",
        )

        # CORS
        self.allowed_origins = self._load_cors_origins()

    @staticmethod
    def _create_db_manager(use_supabase, use_gcs, file_manager, table_name):
        if use_supabase:
            return DatabaseManager(use_supabase=True, table_name=table_name)
        elif use_gcs:
            return DatabaseManager(use_gcs=True, table_name=table_name)
        else:
            return DatabaseManager(
                file_manager=file_manager,
                db_path=f"data/{table_name}.json",
            )

    def _load_cors_origins(self):
        origins = get_secret("cors-allowed-origins")
        if origins:
            return [o.strip() for o in origins.split(",")]
        return ["http://localhost:4200"]
