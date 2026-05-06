"""
Worker Models — Pydantic request/response models.
=================================================

Request models for Cloud Tasks, manual job triggers,
and user credentials.

:created:   2026-05-05
:filename:  models.py
:path:      services/worker-v3/src/models.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class UserCredentials(BaseModel):
    """User OAuth credentials for Google Drive API access."""
    access_token: str
    email: str
    name: Optional[str] = None
    scope: str = "https://www.googleapis.com/auth/drive"

    class Config:
        extra = "ignore"


class TaskPayload(BaseModel):
    """Payload for Cloud Tasks."""
    job_id: Optional[str] = None
    folder_id: Optional[str] = None
    user_token: Optional[str] = None
    user_credentials: Optional[UserCredentials] = None
    trigger_type: str = "scheduled"
    execution_id: Optional[str] = None


class JobRunRequest(BaseModel):
    """Request to run a specific job."""
    job_id: str
    folder_id: Optional[str] = None
