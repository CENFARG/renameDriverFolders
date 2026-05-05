"""
Cloud Tasks — Task creation and payload sanitization.
=====================================================

Creates Google Cloud Tasks with OIDC authentication for
the worker service. Sanitizes payloads before logging.

:created:   2026-05-05
:filename:  cloud_tasks.py
:path:      services/api-server-v3/src/cloud_tasks.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import json
import logging

logger = logging.getLogger(__name__)

tasks_v2 = None  # Lazy import — only needed for create_cloud_task

SENSITIVE_FIELDS = {"access_token", "user_token", "refresh_token"}


def sanitize_payload(payload: dict) -> dict:
    """
    Remove sensitive data from payload for logging.

    Args:
        payload: Original payload dict.

    Returns:
        Copy with sensitive fields masked.
    """
    sanitized = {}
    for key, value in payload.items():
        if key in SENSITIVE_FIELDS and isinstance(value, str):
            sanitized[key] = f"***{value[-4:]}" if len(value) > 4 else "***"
        else:
            sanitized[key] = value
    return sanitized


def create_cloud_task(payload: dict, config=None) -> dict:
    """
    Create a task in Google Cloud Tasks with OIDC authentication.

    Args:
        payload: Task payload dict.
        config: ApiConfig with Cloud Tasks settings.

    Returns:
        Created task object.
    """
    global tasks_v2
    if tasks_v2 is None:
        from google.cloud import tasks_v2 as _tasks_v2
        tasks_v2 = _tasks_v2

    client = tasks_v2.CloudTasksClient()

    parent = client.queue_path(
        config.gcp_project, config.gcp_location, config.tasks_queue
    )

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{config.worker_url}/run-task",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(payload).encode(),
            "oidc_token": {
                "service_account_email": (
                    f"cloud-tasks-sa@{config.gcp_project}.iam.gserviceaccount.com"
                ),
                "audience": config.worker_url,
            },
        }
    }

    logger.info(f"Creating Cloud Task for job: {payload.get('job_id', 'unknown')}")
    logger.debug(f"Sanitized payload: {sanitize_payload(payload)}")

    response = client.create_task(request={"parent": parent, "task": task})
    logger.info(f"Task created: {response.name}")

    return response
