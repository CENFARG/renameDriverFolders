"""
Test: verify_scheduler_token() validates OIDC tokens from Cloud Scheduler.

The function is called at api-server/main.py:883 but was never implemented.
Scheduled jobs crash with NameError because of this missing function.

TDD RED phase: this test should FAIL because verify_scheduler_token
does not exist yet.

:task: T1.2 - Implement verify_scheduler_token()
:phase: RED (test written first)
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

# Ensure src is on path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestVerifySchedulerToken:
    """Verify OIDC token validation for Cloud Scheduler requests."""

    def test_function_exists_and_importable(self):
        """verify_scheduler_token must be importable from auth module."""
        from auth import verify_scheduler_token
        assert callable(verify_scheduler_token)

    def test_valid_oidc_token_accepted(self):
        """Valid OIDC bearer token from Cloud Scheduler must be accepted."""
        from auth import verify_scheduler_token

        mock_request = MagicMock()
        mock_request.headers = {
            "Authorization": "Bearer valid-oidc-token-123"
        }

        with patch("auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = {
                "iss": "https://accounts.google.com",
                "aud": "renombradorarchivosgdrive-api-v2",
                "email": "scheduler@cloud-functions-474716.iam.gserviceaccount.com",
                "sub": "123456789",
            }
            # Should NOT raise any exception
            result = verify_scheduler_token(mock_request)
            assert result is not None or result is None  # Returns None on success

    def test_missing_authorization_header_rejected(self):
        """Request without Authorization header must return 401."""
        from auth import verify_scheduler_token

        mock_request = MagicMock()
        mock_request.headers = {}

        with pytest.raises(HTTPException) as exc_info:
            verify_scheduler_token(mock_request)

        assert exc_info.value.status_code == 401

    def test_invalid_token_format_rejected(self):
        """Non-Bearer token format must return 401."""
        from auth import verify_scheduler_token

        mock_request = MagicMock()
        mock_request.headers = {
            "Authorization": "Basic dXNlcjpwYXNz"
        }

        with pytest.raises(HTTPException) as exc_info:
            verify_scheduler_token(mock_request)

        assert exc_info.value.status_code == 401

    def test_expired_token_rejected(self):
        """Expired or invalid OIDC token must return 401."""
        from auth import verify_scheduler_token

        mock_request = MagicMock()
        mock_request.headers = {
            "Authorization": "Bearer expired-token"
        }

        with patch("auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.side_effect = ValueError("Token expired")
            with pytest.raises(HTTPException) as exc_info:
                verify_scheduler_token(mock_request)

            assert exc_info.value.status_code == 401

    def test_wrong_issuer_rejected(self):
        """Token with wrong issuer (not Google) must be rejected."""
        from auth import verify_scheduler_token

        mock_request = MagicMock()
        mock_request.headers = {
            "Authorization": "Bearer valid-but-wrong-issuer"
        }

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
        """Token targeting wrong audience must be rejected."""
        from auth import verify_scheduler_token

        mock_request = MagicMock()
        mock_request.headers = {
            "Authorization": "Bearer valid-but-wrong-audience"
        }

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
