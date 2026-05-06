"""
Test: API Server Routes extraction (T3.3).

Verifies all router modules exist and expose correct endpoints.

:task: T3.3 - Extract API Routes
:phase: RED (test written first)
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestRouteModulesExist:
    """All router modules should be importable."""

    def test_health_router_exists(self):
        from routes.health import router as health_router
        assert health_router is not None

    def test_auth_router_exists(self):
        from routes.auth_routes import router as auth_router
        assert auth_router is not None

    def test_jobs_router_exists(self):
        from routes.jobs import router as jobs_router
        assert jobs_router is not None

    def test_algorithms_router_exists(self):
        from routes.algorithms import router as algo_router
        assert algo_router is not None


class TestHealthRoutes:
    """Health and config endpoints."""

    def test_health_endpoint(self):
        from routes.health import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAuthRoutes:
    """Auth endpoints."""

    def test_whoami_with_auth(self):
        from routes.auth_routes import router

        app = FastAPI()
        app.include_router(router)

        with patch("routes.auth_routes.verify_auth") as mock_auth:
            mock_auth.return_value = {"email": "user@test.com", "name": "Test User"}
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/auth/whoami",
                headers={"Authorization": "Bearer test_token"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["email"] == "user@test.com"


class TestAlgorithmsRoutes:
    """Algorithms endpoints."""

    def test_list_algorithms(self):
        from routes.algorithms import router

        app = FastAPI()
        app.include_router(router)

        with patch("routes.algorithms.algorithms_manager") as mock_mgr:
            mock_mgr.find_all.return_value = [
                {"id": "algo1", "name": "Test Algorithm", "active": True}
            ]
            client = TestClient(app)
            response = client.get("/api/v1/algorithms")
            assert response.status_code == 200


class TestJobsRoutes:
    """Jobs CRUD endpoints."""

    def test_list_jobs(self):
        from routes.jobs import router

        app = FastAPI()
        app.include_router(router)

        with patch("routes.jobs.db_manager") as mock_db, \
             patch("routes.jobs.algorithms_manager") as mock_algo:
            mock_db.find_all.return_value = []
            mock_algo.find_all.return_value = []
            client = TestClient(app)
            response = client.get("/api/v1/jobs")
            assert response.status_code == 200

    def test_get_single_job(self):
        from routes.jobs import router

        app = FastAPI()
        app.include_router(router)

        with patch("routes.jobs.db_manager") as mock_db:
            mock_db.find.return_value = [{"id": "j1", "name": "Job 1"}]
            client = TestClient(app)
            response = client.get("/api/v1/jobs/j1")
            assert response.status_code == 200

    def test_delete_job(self):
        from routes.jobs import router

        app = FastAPI()
        app.include_router(router)

        with patch("routes.jobs.db_manager") as mock_db:
            mock_db.find.return_value = [{"id": "j1"}]
            mock_db.delete.return_value = True
            client = TestClient(app)
            response = client.delete("/api/v1/jobs/j1")
            assert response.status_code == 200
