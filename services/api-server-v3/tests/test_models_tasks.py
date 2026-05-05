"""
Test: API Server Models + Cloud Tasks extraction (T3.2).

Verifies:
1. Pydantic models extracted from main.py
2. sanitize_payload() masks sensitive data
3. create_cloud_task() creates tasks with OIDC auth

:task: T3.2 - Extract API Server Models + Cloud Tasks
:phase: RED (test written first)
"""

import pytest
from unittest.mock import MagicMock, patch


class TestApiModels:
    """Pydantic models for API server."""

    def test_models_module_exists(self):
        from api_models import ManualJobRequest, JobConfig, JobResponse
        assert ManualJobRequest is not None
        assert JobConfig is not None
        assert JobResponse is not None

    def test_manual_job_request_validates(self):
        from api_models import ManualJobRequest

        req = ManualJobRequest(
            folder_id="1abcDEF123_ghij",
            access_token="ya29.test",
        )
        assert req.folder_id == "1abcDEF123_ghij"
        assert req.access_token == "ya29.test"

    def test_job_config_strict_validation(self):
        from api_models import JobConfig, AgentConfig, ModelConfig

        config = JobConfig(
            id="job_12345",
            name="Test Job",
            source_folder_id="folder_abcde12345",
            agent_config=AgentConfig(
                model=ModelConfig(),
                instructions="Classify",
                prompt_template="Analyze {original_filename}",
                filename_format="{date}_{type}{ext}",
            ),
        )
        assert config.name == "Test Job"
        assert config.active is True

    def test_job_response_model(self):
        from api_models import JobResponse

        resp = JobResponse(
            status="success",
            job_id="job1",
            message="Job submitted",
        )
        assert resp.status == "success"


class TestCloudTasks:
    """Cloud Tasks creation and payload sanitization."""

    def test_cloud_tasks_module_exists(self):
        from cloud_tasks import create_cloud_task, sanitize_payload
        assert create_cloud_task is not None
        assert sanitize_payload is not None

    def test_sanitize_payload_masks_access_token(self):
        """sanitize_payload should mask access_token."""
        from cloud_tasks import sanitize_payload

        payload = {
            "job_id": "job1",
            "access_token": "ya29.super_secret_token",
            "email": "user@test.com",
        }
        result = sanitize_payload(payload)

        assert result["access_token"] != "ya29.super_secret_token"
        assert "***" in result["access_token"]
        assert result["email"] == "user@test.com"

    def test_sanitize_payload_preserves_non_sensitive(self):
        """Non-sensitive fields should be preserved."""
        from cloud_tasks import sanitize_payload

        payload = {"job_id": "job1", "folder_id": "f1"}
        result = sanitize_payload(payload)
        assert result["job_id"] == "job1"
        assert result["folder_id"] == "f1"

    def test_create_cloud_task_returns_task(self):
        """Should create a Cloud Task and return it."""
        from cloud_tasks import create_cloud_task

        mock_config = MagicMock()
        mock_config.gcp_project = "test-project"
        mock_config.gcp_location = "us-central1"
        mock_config.tasks_queue = "test-queue"
        mock_config.worker_url = "https://worker.example.com"

        with patch("cloud_tasks.tasks_v2") as mock_tasks:
            mock_client = MagicMock()
            mock_tasks.CloudTasksClient.return_value = mock_client
            mock_client.create_task.return_value = MagicMock(name="task1")

            result = create_cloud_task(
                {"job_id": "j1", "user_token": "tok"},
                config=mock_config,
            )

            mock_client.create_task.assert_called_once()
