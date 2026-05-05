"""
Health Routes — Health check and config endpoints.
===================================================

:created:   2026-05-05
:filename:  health.py
:path:      services/api-server-v3/src/routes/health.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import os

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "api-server",
        "version": "3.0.0",
    }
