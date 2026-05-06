"""
Error Handlers — HTTP exception handlers.
==========================================

Registers custom error handlers for 401, 403, 429, and
global unhandled exceptions.

:created:   2026-05-06
:filename:  error_handlers.py
:path:      services/api-server-v3/src/error_handlers.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI):
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(401)
    async def unauthorized_handler(request: Request, exc):
        return JSONResponse(
            status_code=401,
            content={
                "error": "Unauthorized",
                "message": "Valid authentication token required",
                "detail": exc.detail,
            },
        )

    @app.exception_handler(403)
    async def forbidden_handler(request: Request, exc):
        return JSONResponse(
            status_code=403,
            content={
                "error": "Forbidden",
                "message": "Your domain is not authorized to access this resource",
                "detail": exc.detail,
            },
        )

    @app.exception_handler(429)
    async def rate_limit_handler(request: Request, exc):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too Many Requests",
                "message": "Rate limit exceeded",
                "detail": exc.detail,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"UNHANDLED EXCEPTION: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An unexpected error occurred. Please contact the administrator.",
            },
        )
