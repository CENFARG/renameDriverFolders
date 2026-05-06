"""
Job Loader — Job config retrieval from database.
=================================================

Loads job configurations and lists active jobs
from the database manager.

:created:   2026-05-06
:filename:  job_loader.py
:path:      services/worker-v3/src/job_loader.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Injected by main.py
db_manager = None


def load_job_config(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Load job configuration from database.

    Returns None if job not found or inactive.
    """
    try:
        jobs = db_manager.find("id", job_id)
        if jobs:
            job = jobs[0]
            if not job.get("active", True):
                logger.warning(f"Job '{job_id}' is not active")
                return None
            return job
        logger.warning(f"Job '{job_id}' not found in database")
        return None
    except Exception as e:
        logger.error(f"Error loading job config: {e}")
        return None


def get_all_active_jobs() -> list:
    """Get all active jobs from database."""
    try:
        all_jobs = db_manager.find_all()
        active = [job for job in all_jobs if job.get("active", True)]
        logger.info(f"Found {len(active)} active jobs")
        return active
    except Exception as e:
        logger.error(f"Error getting active jobs: {e}")
        return []
