"""
Jobs Scheduled — Scheduled job processing endpoint.
====================================================

Processes all active scheduled jobs triggered by Cloud Scheduler
with OIDC authentication.

:created:   2026-05-06
:filename:  jobs_scheduled.py
:path:      services/api-server-v3/src/routes/jobs_scheduled.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["jobs"])

# Injected by main.py
db_manager = None
create_cloud_task = None


@router.post("/jobs/scheduled")
async def process_scheduled_jobs(request: Request):
    """
    Process all scheduled jobs.

    Triggered by Cloud Scheduler with OIDC authentication.
    No OAuth required (service-to-service).
    """
    from auth import verify_scheduler_token
    verify_scheduler_token(request)

    logger.info("Scheduled jobs trigger received")

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
                "jobs_processed": 0,
            }

        results = []
        for job in scheduled_jobs:
            job_id = job.get("id")
            payload = {"job_id": job_id, "trigger_type": "scheduled"}

            try:
                task_id = create_cloud_task(payload)
                results.append({"job_id": job_id, "status": "task_created", "task_id": task_id})
                logger.info(f"Task created for scheduled job: {job_id}")
            except Exception as e:
                logger.error(f"Error creating task for job {job_id}: {e}")
                results.append({"job_id": job_id, "status": "error", "error": str(e)})

        success_count = sum(1 for r in results if r["status"] == "task_created")

        return {
            "status": "success",
            "message": f"Processed {len(scheduled_jobs)} scheduled jobs",
            "jobs_processed": len(scheduled_jobs),
            "tasks_created": success_count,
            "results": results,
        }
    except Exception as e:
        logger.error(f"Error processing scheduled jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process scheduled jobs: {str(e)}")
