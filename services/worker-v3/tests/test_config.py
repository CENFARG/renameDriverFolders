"""
Test: Worker Config + Secret Manager extraction (T2.1).

Verifies:
1. get_secret() reads from env vars (local) and Secret Manager (prod)
2. get_credentials() obtains Google Cloud ADC
3. create_credentials_from_token() builds OAuth credentials
4. WorkerConfig centralizes all initialization

:task: T2.1 - Extract Worker Config + Secret Manager
:phase: RED (test written first)
"""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestGetSecret:
    """get_secret() retrieves secrets from env vars or Google Secret Manager."""

    def test_config_module_exists(self):
        from config import get_secret
        assert get_secret is not None

    def test_get_secret_from_env_var(self):
        """Local dev: returns value from environment variable."""
        from config import get_secret

        with patch.dict(os.environ, {"SUPABASE_URL": "https://test.supabase.co"}):
            result = get_secret("supabase-url")
            assert result == "https://test.supabase.co"

    def test_get_secret_env_var_stripped(self):
        """Leading/trailing whitespace is stripped."""
        from config import get_secret

        with patch.dict(os.environ, {"MY_SECRET": "  value123  "}):
            result = get_secret("my-secret")
            assert result == "value123"

    def test_get_secret_from_secret_manager(self):
        """Production: falls back to Google Secret Manager."""
        from config import get_secret

        mock_response = MagicMock()
        mock_response.payload.data.decode.return_value = "prod-secret-value"

        with patch.dict(os.environ, {}, clear=False):
            # Remove any matching env var
            os.environ.pop("MY_SECRET", None)
            with patch("config.secretmanager.SecretManagerServiceClient") as mock_client:
                mock_instance = mock_client.return_value
                mock_instance.access_secret_version.return_value = mock_response

                result = get_secret("my-secret")
                assert result == "prod-secret-value"

    def test_get_secret_returns_empty_on_failure(self):
        """Returns empty string when neither env nor Secret Manager has the secret."""
        from config import get_secret

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NONEXISTENT_SECRET", None)
            with patch("config.secretmanager.SecretManagerServiceClient") as mock_client:
                mock_client.return_value.access_secret_version.side_effect = Exception("not found")

                result = get_secret("nonexistent-secret")
                assert result == ""


class TestGetCredentials:
    """get_credentials() obtains Google Cloud Application Default Credentials."""

    def test_get_credentials_function_exists(self):
        from config import get_credentials
        assert callable(get_credentials)

    def test_get_credentials_uses_adc(self):
        """Should call google.auth.default() with correct scopes."""
        from config import get_credentials

        mock_creds = MagicMock()
        with patch("config.google.auth.default") as mock_default:
            mock_default.return_value = (mock_creds, "test-project")
            creds = get_credentials()
            assert creds == mock_creds
            mock_default.assert_called_once()
            args, kwargs = mock_default.call_args
            assert "scopes" in kwargs or len(args) > 0

    def test_get_credentials_raises_on_failure(self):
        """Should raise when ADC fails."""
        from config import get_credentials

        with patch("config.google.auth.default") as mock_default:
            mock_default.side_effect = Exception("No ADC")
            with pytest.raises(Exception, match="No ADC"):
                get_credentials()


class TestCreateCredentialsFromToken:
    """create_credentials_from_token() builds OAuth credentials."""

    def test_create_credentials_function_exists(self):
        from config import create_credentials_from_token
        assert callable(create_credentials_from_token)

    def test_creates_credentials_with_token(self):
        """Should create OAuthCredentials with the provided token."""
        from config import create_credentials_from_token

        mock_creds = MagicMock()
        with patch("config.OAuthCredentials", return_value=mock_creds):
            creds = create_credentials_from_token("ya29.test-token-12345")
            assert creds == mock_creds


class TestWorkerConfig:
    """WorkerConfig centralizes configuration initialization."""

    def test_worker_config_class_exists(self):
        from config import WorkerConfig
        assert WorkerConfig is not None

    def test_worker_config_defaults(self):
        """Default config uses JSON mode (no supabase, no gcs)."""
        from config import WorkerConfig

        with patch.dict(os.environ, {
            "USE_SUPABASE": "false",
            "USE_GCS": "false",
            "ENABLE_OCR": "true",
        }):
            cfg = WorkerConfig()
            assert cfg.use_supabase is False
            assert cfg.use_gcs is False
            assert cfg.enable_ocr is True

    def test_worker_config_supabase_mode(self):
        """When USE_SUPABASE=true, loads Supabase credentials."""
        from config import WorkerConfig

        with patch.dict(os.environ, {
            "USE_SUPABASE": "true",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key-123",
            "ENABLE_OCR": "false",
        }):
            cfg = WorkerConfig()
            assert cfg.use_supabase is True

    def test_worker_config_supabase_fallback_when_no_creds(self):
        """Falls back to JSON mode when Supabase creds are missing."""
        from config import WorkerConfig

        with patch.dict(os.environ, {
            "USE_SUPABASE": "true",
            "ENABLE_OCR": "true",
        }):
            # get_secret returns empty for both
            with patch("config.get_secret", return_value=""):
                cfg = WorkerConfig()
                assert cfg.use_supabase is False

    def test_worker_config_gcs_mode(self):
        """When USE_GCS=true or GCS_BUCKET_NAME is set, enables GCS mode."""
        from config import WorkerConfig

        with patch.dict(os.environ, {
            "USE_SUPABASE": "false",
            "USE_GCS": "true",
            "GCS_BUCKET_NAME": "test-bucket",
            "ENABLE_OCR": "true",
        }):
            cfg = WorkerConfig()
            assert cfg.use_gcs is True
