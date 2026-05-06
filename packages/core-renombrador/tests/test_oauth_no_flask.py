"""
Test: OAuth Security works without Flask dependency.

Verifies that oauth_security.py does NOT import Flask
and that get_user_from_request works with a plain headers dict.

TDD RED phase: this test should FAIL initially because
oauth_security.py currently imports Flask at line 28.

:task: T1.1 - Fix Flask import in oauth_security.py
:phase: RED (test written first)
"""

import importlib
import sys
import pytest


class TestNoFlaskDependency:
    """Verify oauth_security.py has zero Flask dependencies."""

    def test_no_flask_import_in_oauth_security(self):
        """oauth_security.py MUST NOT import flask anywhere."""
        with open(
            "src/core_renombrador/oauth_security.py", "r", encoding="utf-8"
        ) as f:
            content = f.read()

        assert "from flask" not in content, (
            "oauth_security.py still imports Flask — remove all Flask dependencies"
        )
        assert "import flask" not in content, (
            "oauth_security.py still imports Flask — remove all Flask dependencies"
        )
        assert "flask" not in content.lower().replace("flask", "").replace("flask", ""), (
            "References to flask remain in oauth_security.py"
        )

    def test_oauth_security_importable_without_flask(self):
        """Module must be importable even if Flask is not installed."""
        # Ensure Flask is NOT in sys.modules (simulating clean env)
        flask_modules = [m for m in sys.modules if m.startswith("flask")]
        saved = {}
        for m in flask_modules:
            saved[m] = sys.modules.pop(m, None)

        try:
            # Force re-import
            if "core_renombrador.oauth_security" in sys.modules:
                del sys.modules["core_renombrador.oauth_security"]

            import core_renombrador.oauth_security
            importlib.reload(core_renombrador.oauth_security)
        finally:
            # Restore Flask modules if they were loaded
            for m, mod in saved.items():
                if mod is not None:
                    sys.modules[m] = mod

    def test_get_user_from_headers_dict(self):
        """get_user_from_request must accept a headers dict instead of Flask request."""
        from unittest.mock import patch, MagicMock
        from core_renombrador.oauth_security import OAuthSecurityManager

        manager = OAuthSecurityManager(
            client_id="test-client-id",
            allowed_domains=["example.com"],
            allowed_emails=["admin@example.com"],
        )

        # Mock the token verification
        mock_user = {
            "email": "user@example.com",
            "name": "Test User",
            "domain": "example.com",
            "email_verified": True,
            "sub": "12345",
        }

        with patch.object(manager, "verify_token", return_value=mock_user):
            headers = {"Authorization": "Bearer fake-token-123"}
            result = manager.get_user_from_headers(headers)

        assert result is not None
        assert result["email"] == "user@example.com"
        assert result["domain"] == "example.com"

    def test_get_user_from_headers_missing_auth(self):
        """Must return None when no Authorization header."""
        from core_renombrador.oauth_security import OAuthSecurityManager

        manager = OAuthSecurityManager(client_id="test-client-id")
        result = manager.get_user_from_headers({})
        assert result is None

    def test_get_user_from_headers_invalid_format(self):
        """Must return None for malformed Authorization header."""
        from core_renombrador.oauth_security import OAuthSecurityManager

        manager = OAuthSecurityManager(client_id="test-client-id")
        result = manager.get_user_from_headers({"Authorization": "NotBearer token"})
        assert result is None

    def test_get_user_from_headers_basic_auth(self):
        """Must return None for Basic auth (only Bearer supported)."""
        from core_renombrador.oauth_security import OAuthSecurityManager

        manager = OAuthSecurityManager(client_id="test-client-id")
        result = manager.get_user_from_headers({"Authorization": "Basic dXNlcjpwYXNz"})
        assert result is None

    def test_no_flask_decorator_function(self):
        """require_auth decorator must NOT exist (Flask-specific, not needed)."""
        with open(
            "src/core_renombrador/oauth_security.py", "r", encoding="utf-8"
        ) as f:
            content = f.read()

        assert "def require_auth" not in content, (
            "require_auth is a Flask-specific decorator and should be removed"
        )
