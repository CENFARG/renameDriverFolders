"""
Test: API Server decomposition (main.py split).
================================================

Verifies new extracted modules work correctly:
- seed.py: default algorithm seeding
- error_handlers.py: HTTP error handlers
- routes/jobs_manual.py: manual job submission
- routes/jobs_scheduled.py: scheduled job processing
- routes/audit.py: audit logs and execution export

:created:   2026-05-06
:task:      Decompose API main.py
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestSeedModule:
    """Seed module for default algorithms."""

    def test_seed_module_importable(self):
        from seed import seed_default_algorithms, DEFAULT_ALGORITHMS
        assert seed_default_algorithms is not None
        assert len(DEFAULT_ALGORITHMS) == 4

    def test_seed_inserts_missing_algorithms(self):
        from seed import seed_default_algorithms

        mock_db = MagicMock()
        mock_db.find.return_value = None  # Not found
        mock_db.insert.return_value = True

        seed_default_algorithms(mock_db)

        assert mock_db.insert.call_count == 4

    def test_seed_skips_existing_algorithms(self):
        from seed import seed_default_algorithms

        mock_db = MagicMock()
        mock_db.find.return_value = [{"id": "existing"}]  # Found
        mock_db.insert.return_value = True

        seed_default_algorithms(mock_db)

        mock_db.insert.assert_not_called()


class TestErrorHandlers:
    """Custom HTTP error handlers."""

    def test_error_handlers_module_importable(self):
        from error_handlers import register_error_handlers
        assert register_error_handlers is not None

    def test_401_handler_returns_json(self):
        from error_handlers import register_error_handlers

        app = FastAPI()
        register_error_handlers(app)
        client = TestClient(app, raise_server_exceptions=False)

        @app.get("/test-401")
        async def trigger_401():
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Unauthorized test")

        response = client.get("/test-401")
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "Unauthorized"

    def test_403_handler_returns_json(self):
        from error_handlers import register_error_handlers

        app = FastAPI()
        register_error_handlers(app)
        client = TestClient(app, raise_server_exceptions=False)

        @app.get("/test-403")
        async def trigger_403():
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Forbidden test")

        response = client.get("/test-403")
        assert response.status_code == 403
        data = response.json()
        assert data["error"] == "Forbidden"

    def test_global_exception_returns_500(self):
        from error_handlers import register_error_handlers

        app = FastAPI()
        register_error_handlers(app)
        client = TestClient(app, raise_server_exceptions=False)

        @app.get("/test-crash")
        async def trigger_crash():
            raise RuntimeError("Unexpected crash")

        response = client.get("/test-crash")
        assert response.status_code == 500


class TestJobsManualModule:
    """Manual job submission route module."""

    def test_jobs_manual_module_importable(self):
        from routes.jobs_manual import router, submit_manual_job
        assert router is not None
        assert submit_manual_job is not None

    def test_resolve_access_token_from_body(self):
        from routes.jobs_manual import _resolve_access_token

        mock_request = MagicMock()
        job_request = MagicMock()
        job_request.access_token = "ya29.test_token"

        token = _resolve_access_token(job_request, mock_request)
        assert token == "ya29.test_token"

    def test_resolve_access_token_from_header(self):
        from routes.jobs_manual import _resolve_access_token
        from fastapi import HTTPException

        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer ya29.header_token"
        job_request = MagicMock()
        job_request.access_token = None

        token = _resolve_access_token(job_request, mock_request)
        assert token == "ya29.header_token"

    def test_resolve_access_token_raises_without_both(self):
        from routes.jobs_manual import _resolve_access_token
        from fastapi import HTTPException

        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        job_request = MagicMock()
        job_request.access_token = None

        with pytest.raises(HTTPException) as exc_info:
            _resolve_access_token(job_request, mock_request)
        assert exc_info.value.status_code == 401

    def test_find_or_seed_creates_from_algorithm(self):
        from routes import jobs_manual
        from routes.jobs_manual import _find_or_seed_job_config

        original_db = jobs_manual.db_manager
        original_algo = jobs_manual.algorithms_manager

        try:
            mock_db = MagicMock()
            mock_db.find.return_value = None
            mock_algo_mgr = MagicMock()
            mock_algo_mgr.find.return_value = [{"id": "algo1", "name": "Test", "description": "Desc", "extraction_prompt": "p", "filename_format": "f", "output_schema": {}, "classification_criteria": "c"}]

            jobs_manual.db_manager = mock_db
            jobs_manual.algorithms_manager = mock_algo_mgr

            _find_or_seed_job_config("job-manual-algo1", "algo1")
            mock_db.insert.assert_called_once()
        finally:
            jobs_manual.db_manager = original_db
            jobs_manual.algorithms_manager = original_algo

    def test_find_or_seed_creates_default(self):
        from routes import jobs_manual
        from routes.jobs_manual import _find_or_seed_job_config

        original_db = jobs_manual.db_manager
        original_algo = jobs_manual.algorithms_manager

        try:
            mock_db = MagicMock()
            mock_db.find.return_value = None
            mock_algo_mgr = MagicMock()
            mock_algo_mgr.find.return_value = None

            jobs_manual.db_manager = mock_db
            jobs_manual.algorithms_manager = mock_algo_mgr

            _find_or_seed_job_config("job-manual-unknown", "unknown")
            mock_db.insert.assert_called_once()
        finally:
            jobs_manual.db_manager = original_db
            jobs_manual.algorithms_manager = original_algo

    def test_create_execution_log_structure(self):
        from routes.jobs_manual import _create_execution_log

        user = {"email": "test@example.com", "name": "Test"}
        job_request = MagicMock()
        job_request.folder_id = "folder123"
        job_request.job_type = "generic"

        log = _create_execution_log(user, job_request, "job-manual-generic")
        assert log["user_email"] == "test@example.com"
        assert log["status"] == "submitted"
        assert log["task_id"] is None


class TestJobsScheduledModule:
    """Scheduled job processing route module."""

    def test_jobs_scheduled_module_importable(self):
        from routes.jobs_scheduled import router, process_scheduled_jobs
        assert router is not None

    def test_scheduled_endpoint_exists(self):
        from routes.jobs_scheduled import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/jobs/scheduled")
        assert response.status_code in (401, 500)  # Auth or config required


class TestAuditModule:
    """Audit log route module."""

    def test_audit_module_importable(self):
        from routes.audit import router, get_audit_logs, export_execution_logs
        assert router is not None

    def test_audit_logs_endpoint_with_mock(self):
        from routes.audit import router

        app = FastAPI()
        app.include_router(router)

        with patch("routes.audit.executions_manager") as mock_mgr:
            mock_mgr.find_all.return_value = []
            client = TestClient(app)
            response = client.get("/api/v1/audit-logs")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["total"] == 0

    def test_build_log_content(self):
        from routes.audit import _build_log_content

        execution = {
            "id": "exec-123",
            "timestamp": "2026-05-06T10:00:00Z",
            "user_email": "user@test.com",
            "folder_id": "folder-abc",
            "status": "completed",
            "details": "Test details",
            "stats": {"files_processed": 10, "files_renamed": 8, "errors": 1},
        }

        content = _build_log_content(execution)
        assert "exec-123" in content
        assert "user@test.com" in content
        assert "FIN DEL LOG" in content
        assert "10" in content


class TestJobsRouteDualTable:
    """Jobs CRUD with dual-table (jobs + algorithms) lookup."""

    def test_create_job_in_jobs_table(self):
        from routes.jobs import router

        app = FastAPI()
        app.include_router(router)

        with patch("routes.jobs.db_manager") as mock_db, \
             patch("routes.jobs.algorithms_manager") as mock_algo:
            mock_db.find.return_value = None
            mock_db.insert.return_value = True

            client = TestClient(app)
            response = client.post("/api/v1/jobs", json={
                "job_config": {
                    "id": "test_job_12345",
                    "name": "Test Job",
                    "source_folder_id": "folder_abcde12345",
                    "trigger_type": "manual",
                    "agent_config": {
                        "model": {"name": "gemini-2.5-flash", "temperature": 0.1, "max_tokens": 4096},
                        "instructions": "Test",
                        "prompt_template": "Test {x}",
                        "filename_format": "{x}",
                    },
                },
            })
            assert response.status_code == 200

    def test_update_job_found_in_algorithms_table(self):
        from routes.jobs import router

        app = FastAPI()
        app.include_router(router)

        with patch("routes.jobs.db_manager") as mock_db, \
             patch("routes.jobs.algorithms_manager") as mock_algo:
            mock_db.find.return_value = None
            mock_algo.find.return_value = [{"id": "algo_test_12345"}]
            mock_algo.update.return_value = True

            client = TestClient(app)
            response = client.put("/api/v1/jobs/algo_test_12345", json={
                "job_config": {
                    "id": "algo_test_12345",
                    "name": "Updated Algo",
                    "source_folder_id": "DYNAMIC",
                    "trigger_type": "manual",
                    "agent_config": {
                        "model": {"name": "gemini-2.5-flash", "temperature": 0.1, "max_tokens": 4096},
                        "instructions": "Updated",
                        "prompt_template": "Updated {x}",
                        "filename_format": "{x}",
                    },
                },
            })
            assert response.status_code == 200
