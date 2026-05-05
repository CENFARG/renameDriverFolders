"""
Agent Config — Model resolution and job config loading.
========================================================

Handles loading job configurations from database and resolving
the correct AI model (Vertex AI vs standard Gemini).

:created:   2026-05-05
:filename:  agent_config.py
:path:      packages/core-renombrador/src/core_renombrador/agent_config.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
import os
from typing import Any, Dict, Optional

from agno.models.google import Gemini

logger = logging.getLogger(__name__)


class AgentConfig:
    """Loads job configurations and resolves AI model instances."""

    def __init__(
        self,
        database_manager: Optional[Any] = None,
        config_manager: Optional[Any] = None,
    ):
        self.database_manager = database_manager
        self.config_manager = config_manager

    def load_job_config(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Load a job configuration from database."""
        if not self.database_manager:
            logger.warning("No DatabaseManager configured")
            return None
        try:
            jobs = self.database_manager.find("id", job_id)
            if jobs:
                return jobs[0]
            logger.warning(f"Job '{job_id}' not found in database")
            return None
        except Exception as e:
            logger.error(f"Error loading job config: {e}")
            return None

    def resolve_model(self, model_id: str) -> Gemini:
        """
        Resolve a Gemini model instance.

        Uses Vertex AI when GCP_PROJECT is set, otherwise standard mode.
        """
        project_id = os.environ.get("GCP_PROJECT")
        location = os.environ.get("GCP_LOCATION", "us-central1")

        if project_id:
            logger.info(f"Vertex AI Gemini: project={project_id}, location={location}")
            return Gemini(
                id=model_id,
                project_id=project_id,
                location=location,
                vertexai=True,
            )

        logger.warning("GCP_PROJECT not set. Gemini in standard mode (API Key required).")
        return Gemini(id=model_id)

    def extract_model_id(self, job_config: Dict[str, Any]) -> str:
        """Extract model ID from job config."""
        agent_config = job_config.get("agent_config", {})
        model_config = agent_config.get("model", {})
        return model_config.get("name", "gemini-2.5-flash")
