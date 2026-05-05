"""
Jobs Routes — Job CRUD and execution endpoints.
================================================

:created:   2026-05-05
:filename:  jobs.py
:path:      services/api-server-v3/src/routes/jobs.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

# Injected by main.py
db_manager = None


@router.get("")
async def list_jobs():
    """List all job configurations."""
    try:
        jobs = db_manager.find_all()
        return jobs
    except Exception as e:
        logger.error(f"Failed to fetch jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}")
async def get_job(job_id: str):
    """Get a single job configuration by ID."""
    try:
        jobs = db_manager.find("id", job_id)
        if not jobs:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        return jobs[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """Delete a job configuration."""
    try:
        existing = db_manager.find("id", job_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        db_manager.delete("id", job_id)
        return {"status": "success", "message": f"Job '{job_id}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
