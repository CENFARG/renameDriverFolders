"""
API Models — Pydantic request/response models.
===============================================

Request models for job management, manual job submission,
and agent configuration.

:created:   2026-05-05
:filename:  api_models.py
:path:      services/api-server-v3/src/api_models.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import re
from typing import Optional

from pydantic import BaseModel, validator


class ManualJobRequest(BaseModel):
    """Request for manual job submission with input validation."""
    folder_id: str
    job_type: Optional[str] = "generic"
    access_token: Optional[str] = None

    @validator("folder_id")
    def validate_folder_id(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Invalid folder_id format")
        return v


class ModelConfig(BaseModel):
    name: str = "gemini-2.5-flash"
    temperature: float = 0.1
    max_tokens: int = 4096


class AgentConfig(BaseModel):
    model: ModelConfig
    instructions: str
    prompt_template: str
    filename_format: str
    output_schema: Optional[dict] = None


class JobConfig(BaseModel):
    """Strict model for job configuration to prevent mass assignment."""
    id: str
    name: str
    description: Optional[str] = ""
    active: bool = True
    trigger_type: str = "manual"
    schedule: Optional[str] = None
    source_folder_id: str
    target_folder_names: list[str] = ["Procesados"]
    agent_config: AgentConfig

    @validator("id", "source_folder_id")
    def validate_ids(cls, v):
        if v != "DYNAMIC" and not re.match(r"^[a-zA-Z0-9_-]{5,50}$", v):
            raise ValueError(f"Invalid ID format: {v}")
        return v

    @validator("trigger_type")
    def validate_trigger(cls, v):
        if v not in ["manual", "scheduled"]:
            raise ValueError("trigger_type must be manual or scheduled")
        return v


class JobResponse(BaseModel):
    """Response for job submission."""
    status: str
    message: str
    job_id: Optional[str] = None
    task_id: Optional[str] = None
