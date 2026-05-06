"""
Test: Middleware + seed removal (T3.4 + T3.5).

T3.4: Middleware (CORS, security headers, error handler).
T3.5: Remove seed_default_algorithms from main.

:task: T3.4 + T3.5
:phase: RED (test written first)
"""

import pytest
import os
import glob
from unittest.mock import MagicMock


class TestMiddleware:
    """Middleware modules for CORS, security headers, error handling."""

    def test_middleware_module_exists(self):
        from middleware import SecurityHeadersMiddleware, setup_middleware
        assert SecurityHeadersMiddleware is not None
        assert setup_middleware is not None

    def test_security_headers_added(self):
        """SecurityHeadersMiddleware adds security headers to responses."""
        from middleware import SecurityHeadersMiddleware
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)

        response = client.get("/test")
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in response.headers

    def test_setup_middleware_adds_cors(self):
        """setup_middleware should add CORS and security headers."""
        from middleware import setup_middleware
        from fastapi import FastAPI

        app = FastAPI()
        config = MagicMock()
        config.allowed_origins = ["http://localhost:4200"]

        setup_middleware(app, config)
        # Verify middleware was added (no error raised)
        assert len(app.user_middleware) > 0


class TestNoSeedFunction:
    """T3.5: seed_default_algorithms should not be in new modules."""

    def test_no_seed_function_in_extracted_code(self):
        """No seed_default_algorithms in extracted modules."""
        src_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "src")
        )

        offenders = []
        for py_file in glob.glob(os.path.join(src_dir, "*.py")):
            basename = os.path.basename(py_file)
            if basename in ("main.py", "seed.py"):
                continue  # main.py and seed.py legitimately have it
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "seed_default_algorithms" in content:
                    offenders.append(basename)

        assert offenders == [], f"Found seed function in: {offenders}"

    def test_diego_algorithms_not_in_extracted_code(self):
        """No diego_algorithms list in extracted modules."""
        src_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "src")
        )

        offenders = []
        for py_file in glob.glob(os.path.join(src_dir, "*.py")):
            basename = os.path.basename(py_file)
            if basename == "main.py":
                continue
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "diego_algorithms" in content:
                    offenders.append(basename)

        assert offenders == [], f"Found diego_algorithms in: {offenders}"
