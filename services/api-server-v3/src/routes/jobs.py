"""
Jobs Routes — Job CRUD with dual-table lookup.
===============================================

Handles job create/read/update/delete across both 'jobs'
and 'document_algorithms' tables.

:created:   2026-05-06
:filename:  jobs.py
:path:      services/api-server-v3/src/routes/jobs.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging

from fastapi import APIRouter, HTTPException

from api_models import JobConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

# Injected by main.py
db_manager = None
algorithms_manager = None


def _find_job(job_id: str):
    """Find a job in either jobs or document_algorithms table."""
    jobs = db_manager.find("id", job_id)
    if jobs:
        return jobs[0], db_manager, "jobs"

    algos = algorithms_manager.find("id", job_id)
    if algos:
        return algos[0], algorithms_manager, "document_algorithms"

    return None, None, None


@router.get("")
async def list_jobs(user: dict = None):
    """List all job configurations from both tables."""
    try:
        jobs_from_jobs = db_manager.find_all()
        jobs_from_algorithms = algorithms_manager.find_all()
        all_jobs = jobs_from_jobs + jobs_from_algorithms

        logger.info(f"Found {len(jobs_from_jobs)} jobs, {len(jobs_from_algorithms)} algorithms")

        jobs_summary = []
        for job in all_jobs:
            job_id = job.get("id") or job.get("job_id")
            if not job_id and job.get("source_folder_id"):
                job_id = f"job-folder-{job.get('source_folder_id')[:8]}"
            if not job_id:
                logger.warning(f"Skipping job with missing ID: {job}")
                continue

            jobs_summary.append({
                "id": job_id,
                "name": job.get("name", job_id),
                "description": job.get("description", ""),
                "active": job.get("active", True),
                "trigger_type": job.get("trigger_type", "manual"),
                "schedule": job.get("schedule"),
            })

        return {"status": "success", "jobs": jobs_summary, "total": len(jobs_summary)}
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.get("/{job_id}")
async def get_job(job_id: str, user: dict = None):
    """Get a single job by ID, searching both tables."""
    try:
        jobs = db_manager.find("id", job_id)
        if jobs:
            logger.info(f"Found job {job_id} in 'jobs' table")
            return jobs[0]

        algorithms = algorithms_manager.find("id", job_id)
        if algorithms:
            logger.info(f"Found job {job_id} in 'document_algorithms' table")
            return algorithms[0]

        raise HTTPException(status_code=404, detail="Configuration not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Database retrieval failed")


@router.post("")
async def create_job(job_config: JobConfig, user: dict = None):
    """Create a new job configuration with strict validation."""
    try:
        is_job_config = job_config.trigger_type in ["scheduled", "manual"]
        manager = db_manager if is_job_config else algorithms_manager
        table_name = "jobs" if is_job_config else "document_algorithms"

        existing = manager.find("id", job_config.id)
        if existing:
            raise HTTPException(status_code=409, detail=f"ID '{job_config.id}' already exists in '{table_name}'")

        manager.insert(job_config.dict())
        logger.info(f"Job '{job_config.id}' created in '{table_name}'")
        return {"status": "success", "message": f"Job '{job_config.id}' created in '{table_name}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail="Failed to persist configuration")


@router.put("/{job_id}")
async def update_job(job_id: str, job_config: JobConfig, user: dict = None):
    """Update a job configuration in either table."""
    try:
        _, manager, table_name = _find_job(job_id)
        if not manager:
            raise HTTPException(status_code=404, detail="Configuration not found")
        if job_config.id != job_id:
            raise HTTPException(status_code=400, detail="Path ID and body ID mismatch")

        manager.update("id", job_id, job_config.dict())
        logger.info(f"Job '{job_id}' updated in '{table_name}'")
        return {"status": "success", "message": f"Job '{job_id}' updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Update failed")


@router.delete("/{job_id}")
async def delete_job(job_id: str, user: dict = None):
    """Delete a job configuration from either table."""
    try:
        _, manager, table_name = _find_job(job_id)
        if not manager:
            raise HTTPException(status_code=404, detail="Configuration not found")

        manager.delete("id", job_id)
        logger.info(f"Job '{job_id}' deleted from '{table_name}'")
        return {"status": "success", "message": f"Job '{job_id}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Deletion failed")
