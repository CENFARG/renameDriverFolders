"""
Auth Routes — Authentication endpoints.
========================================

:created:   2026-05-05
:filename:  auth_routes.py
:path:      services/api-server-v3/src/routes/auth_routes.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging

from fastapi import APIRouter, HTTPException, Request

from auth import verify_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/whoami")
async def whoami(request: Request):
    """Returns the current authenticated user info."""
    try:
        user = verify_auth(request)
        return {"status": "success", "user": user}
    except HTTPException:
        return {"status": "success", "authenticated": False, "user": None}
