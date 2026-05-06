"""
Test: verify_scheduler_token() validates OIDC tokens from Cloud Scheduler.

:task: T1.2 - Implement verify_scheduler_token()
:path: services/api-server-v3/tests/
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestVerifySchedulerToken:

    def test_function_exists_and_importable(self):
        from auth import verify_scheduler_token
        assert callable(verify_scheduler_token)

    def test_valid_oidc_token_accepted(self):
        from auth import verify_scheduler_token
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer valid-oidc-token-123"}

        with patch("auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = {
                "iss": "https://accounts.google.com",
                "aud": "renombradorarchivosgdrive-api-v2",
                "email": "scheduler@cloud-functions-474716.iam.gserviceaccount.com",
                "sub": "123456789",
            }
            result = verify_scheduler_token(mock_request)
            assert result is not None

    def test_missing_authorization_header_rejected(self):
        from auth import verify_scheduler_token
        mock_request = MagicMock()
        mock_request.headers = {}
        with pytest.raises(HTTPException) as exc_info:
            verify_scheduler_token(mock_request)
        assert exc_info.value.status_code == 401

    def test_invalid_token_format_rejected(self):
        from auth import verify_scheduler_token
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        with pytest.raises(HTTPException) as exc_info:
            verify_scheduler_token(mock_request)
        assert exc_info.value.status_code == 401

    def test_expired_token_rejected(self):
        from auth import verify_scheduler_token
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer expired-token"}
        with patch("auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.side_effect = ValueError("Token expired")
            with pytest.raises(HTTPException) as exc_info:
                verify_scheduler_token(mock_request)
            assert exc_info.value.status_code == 401

    def test_wrong_issuer_rejected(self):
        from auth import verify_scheduler_token
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer valid-but-wrong-issuer"}
        with patch("auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = {
                "iss": "https://evil.com",
                "aud": "renombradorarchivosgdrive-api-v2",
                "email": "evil@evil.com",
                "sub": "999",
            }
            with pytest.raises(HTTPException) as exc_info:
                verify_scheduler_token(mock_request)
            assert exc_info.value.status_code == 401

    def test_wrong_audience_rejected(self):
        from auth import verify_scheduler_token
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer valid-but-wrong-audience"}
        with patch("auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = {
                "iss": "https://accounts.google.com",
                "aud": "wrong-service",
                "email": "scheduler@project.iam.gserviceaccount.com",
                "sub": "123",
            }
            with pytest.raises(HTTPException) as exc_info:
                verify_scheduler_token(mock_request)
            assert exc_info.value.status_code == 401
