"""
Test: API Server Config extraction (T3.1).

Verifies:
1. get_secret() works for API server (same pattern as worker)
2. ApiConfig centralizes initialization
3. verify_auth() handles IAP and OAuth flows
4. get_current_user() is a dependency wrapper

:task: T3.1 - Extract API Server Config + Auth
:phase: RED (test written first)
"""

import pytest
import os
from unittest.mock import MagicMock, patch


class TestApiConfig:
    """ApiConfig centralizes API server initialization."""

    def test_api_config_module_exists(self):
        from api_config import ApiConfig
        assert ApiConfig is not None

    def test_api_config_initializes_db_managers(self):
        """Should create db_manager, algorithms_manager, executions_manager."""
        from api_config import ApiConfig

        with patch.dict(os.environ, {"USE_SUPABASE": "true", "SUPABASE_URL": "http://t", "SUPABASE_KEY": "k"}):
            with patch("api_config.get_secret") as mock_secret:
                mock_secret.side_effect = lambda x: {"supabase-url": "http://t", "supabase-key": "k"}.get(x, "")
                cfg = ApiConfig()
                assert cfg.db_manager is not None
                assert cfg.algorithms_manager is not None
                assert cfg.executions_manager is not None

    def test_api_config_json_mode(self):
        """Should fall back to JSON mode when supabase is off."""
        from api_config import ApiConfig

        with patch.dict(os.environ, {"USE_SUPABASE": "false", "USE_GCS": "false"}):
            cfg = ApiConfig()
            assert cfg.db_manager is not None

    def test_api_config_cloud_tasks_vars(self):
        """Should load Cloud Tasks configuration."""
        from api_config import ApiConfig

        with patch.dict(os.environ, {
            "USE_SUPABASE": "false",
            "GCP_PROJECT": "test-project",
            "GCP_LOCATION": "us-central1",
            "TASKS_QUEUE": "test-queue",
            "WORKER_URL": "https://worker.example.com",
        }):
            cfg = ApiConfig()
            assert cfg.gcp_project == "test-project"
            assert cfg.worker_url == "https://worker.example.com"


class TestApiGetSecret:
    """get_secret() for API server."""

    def test_get_secret_exists(self):
        from api_config import get_secret
        assert callable(get_secret)

    def test_get_secret_from_env(self):
        from api_config import get_secret

        with patch.dict(os.environ, {"SUPABASE_URL": "https://test.supabase.co"}):
            assert get_secret("supabase-url") == "https://test.supabase.co"

    def test_get_secret_empty_on_failure(self):
        from api_config import get_secret

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NONEXISTENT", None)
            with patch("api_config.secretmanager.SecretManagerServiceClient") as mock:
                mock.return_value.access_secret_version.side_effect = Exception("fail")
                assert get_secret("nonexistent") == ""


class TestVerifyAuth:
    """verify_auth() handles IAP + OAuth authentication."""

    def test_verify_auth_exists(self):
        from auth import verify_auth
        assert callable(verify_auth)

    def test_verify_auth_rejects_no_token(self):
        """Should raise HTTPException when no auth header."""
        from auth import verify_auth
        from fastapi import HTTPException

        mock_request = MagicMock()
        mock_request.headers = {}

        with pytest.raises(HTTPException) as exc_info:
            verify_auth(mock_request)
        assert exc_info.value.status_code == 401

    def test_get_current_user_exists(self):
        from auth import get_current_user
        assert callable(get_current_user)
