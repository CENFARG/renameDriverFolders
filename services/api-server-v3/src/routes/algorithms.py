"""
Algorithms Routes — Document classification algorithms.
=======================================================

:created:   2026-05-05
:filename:  algorithms.py
:path:      services/api-server-v3/src/routes/algorithms.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["algorithms"])

# Injected by main.py
algorithms_manager = None


@router.get("/algorithms")
async def list_algorithms():
    """List all available document classification algorithms."""
    try:
        algorithms = algorithms_manager.find_all()
        active = [a for a in algorithms if a.get("is_active", True)]
        return active
    except Exception as e:
        logger.error(f"Failed to fetch algorithms: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch algorithms: {str(e)}")
