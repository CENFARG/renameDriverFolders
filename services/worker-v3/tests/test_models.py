"""
Test: Worker Models extraction (T2.8).

Verifies models extracted from main.py:
1. UserCredentials: OAuth credentials from user
2. TaskPayload: Cloud Tasks payload
3. JobRunRequest: Manual job trigger request

:task: T2.8 - Extract Worker Models
:phase: RED (test written first)
"""

import pytest


class TestUserCredentials:
    """UserCredentials model for OAuth credentials."""

    def test_models_module_exists(self):
        from models import UserCredentials
        assert UserCredentials is not None

    def test_user_credentials_required_fields(self):
        from models import UserCredentials

        creds = UserCredentials(access_token="ya29.test", email="user@test.com")
        assert creds.access_token == "ya29.test"
        assert creds.email == "user@test.com"

    def test_user_credentials_defaults(self):
        from models import UserCredentials

        creds = UserCredentials(access_token="tok", email="e@e.com")
        assert creds.scope == "https://www.googleapis.com/auth/drive"
        assert creds.name is None

    def test_user_credentials_ignores_extra_fields(self):
        from models import UserCredentials

        creds = UserCredentials(
            access_token="tok", email="e@e.com",
            extra_field="should be ignored"
        )
        assert creds.access_token == "tok"


class TestTaskPayload:
    """TaskPayload model for Cloud Tasks."""

    def test_task_payload_exists(self):
        from models import TaskPayload
        assert TaskPayload is not None

    def test_task_payload_defaults(self):
        from models import TaskPayload

        payload = TaskPayload()
        assert payload.job_id is None
        assert payload.trigger_type == "scheduled"
        assert payload.user_token is None
        assert payload.user_credentials is None

    def test_task_payload_with_values(self):
        from models import TaskPayload
        from models import UserCredentials

        creds = UserCredentials(access_token="tok", email="u@test.com")
        payload = TaskPayload(
            job_id="job123",
            trigger_type="manual",
            user_credentials=creds,
        )
        assert payload.job_id == "job123"
        assert payload.trigger_type == "manual"
        assert payload.user_credentials.access_token == "tok"


class TestJobRunRequest:
    """JobRunRequest model for manual job triggers."""

    def test_job_run_request_exists(self):
        from models import JobRunRequest
        assert JobRunRequest is not None

    def test_job_run_request_required_job_id(self):
        from models import JobRunRequest

        req = JobRunRequest(job_id="job456")
        assert req.job_id == "job456"

    def test_job_run_request_optional_folder_id(self):
        from models import JobRunRequest

        req = JobRunRequest(job_id="job1", folder_id="folder1")
        assert req.folder_id == "folder1"

        req2 = JobRunRequest(job_id="job2")
        assert req2.folder_id is None
