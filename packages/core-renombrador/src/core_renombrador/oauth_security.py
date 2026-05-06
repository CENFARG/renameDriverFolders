"""
OAuth Security Manager con Domain Whitelisting
==============================================

Manages OAuth 2.0 authentication with Google and domain-based authorization.
Maneja autenticación OAuth 2.0 con Google y autorización basada en dominios.

Framework-agnostic: works with FastAPI, Flask, or any Python web framework.
Accepts headers as a plain dict — no framework-specific request object needed.

Features:
- OAuth 2.0 with Google Sign-In
- Domain whitelisting (@miempresa.com, @clientedomain.com)
- Individual email whitelisting
- Token verification
- Rate limiting per user

:created:   2025-12-05
:filename:  oauth_security.py
:author:    amBotHs + CENF
:version:   2.0.0
:status:    Development
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

logger = logging.getLogger(__name__)


class OAuthSecurityManager:
    """
    Manages OAuth authentication and domain-based authorization.
    Maneja autenticación OAuth y autorización basada en dominios.

    Framework-agnostic: uses plain dicts for headers, no Flask/FastAPI dependency.
    """

    def __init__(
        self,
        client_id: str,
        allowed_domains: Optional[List[str]] = None,
        allowed_emails: Optional[List[str]] = None,
        require_domain_match: bool = True
    ):
        """
        Initialize OAuth Security Manager.

        Args:
            client_id: Google OAuth Client ID.
            allowed_domains: List of allowed email domains (e.g., ["miempresa.com"]).
            allowed_emails: List of specific allowed emails.
            require_domain_match: If True, requires email to match allowed domains.
        """
        self.client_id = client_id
        self.allowed_domains = allowed_domains or []
        self.allowed_emails = allowed_emails or []
        self.require_domain_match = require_domain_match

        # Rate limiting storage (in-memory, consider Redis for production)
        self._rate_limit_store: Dict[str, List[datetime]] = {}

        logger.info(f"OAuthSecurityManager initialized with {len(self.allowed_domains)} domains")

    def verify_token(self, token: str) -> Optional[Dict[str, str]]:
        """
        Verifies a Google OAuth ID token.

        Args:
            token: The ID token from Google Sign-In.

        Returns:
            User info dict if valid, None if invalid.
        """
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                self.client_id
            )

            email = idinfo.get("email")
            email_verified = idinfo.get("email_verified", False)

            if not email or not email_verified:
                logger.warning("Token verification failed: email not verified")
                return None

            domain = email.split("@")[1] if "@" in email else None

            user_info = {
                "email": email,
                "name": idinfo.get("name"),
                "picture": idinfo.get("picture"),
                "email_verified": email_verified,
                "domain": domain,
                "sub": idinfo.get("sub"),
            }

            logger.info(f"Token verified for user: {email}")
            return user_info

        except ValueError as e:
            logger.error(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    def is_authorized(self, user_info: Dict[str, str]) -> bool:
        """
        Checks if user is authorized based on domain/email whitelist.

        Args:
            user_info: User info from verify_token().

        Returns:
            True if authorized, False otherwise.
        """
        email = user_info.get("email")
        domain = user_info.get("domain")

        if email in self.allowed_emails:
            logger.info(f"User {email} authorized via email whitelist")
            return True

        if self.require_domain_match:
            if domain in self.allowed_domains:
                logger.info(f"User {email} authorized via domain whitelist ({domain})")
                return True
            else:
                logger.warning(f"User {email} denied: domain {domain} not in whitelist")
                return False

        logger.info(f"User {email} authorized (domain matching disabled)")
        return True

    def check_rate_limit(
        self,
        user_email: str,
        max_requests: int = 10,
        window_minutes: int = 1
    ) -> bool:
        """
        Checks if user has exceeded rate limit.

        Args:
            user_email: User's email.
            max_requests: Maximum requests allowed in time window.
            window_minutes: Time window in minutes.

        Returns:
            True if within limit, False if exceeded.
        """
        now = datetime.now()
        cutoff = now - timedelta(minutes=window_minutes)

        if user_email not in self._rate_limit_store:
            self._rate_limit_store[user_email] = []

        self._rate_limit_store[user_email] = [
            req_time for req_time in self._rate_limit_store[user_email]
            if req_time > cutoff
        ]

        request_count = len(self._rate_limit_store[user_email])

        if request_count >= max_requests:
            logger.warning(
                f"Rate limit exceeded for {user_email}: "
                f"{request_count}/{max_requests} in {window_minutes}min"
            )
            return False

        self._rate_limit_store[user_email].append(now)
        return True

    def get_user_from_headers(self, headers: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Extracts and verifies user from request headers.

        Framework-agnostic: accepts a plain headers dict instead of
        Flask's request object. Works with any Python web framework.

        Looks for Authorization header: "Bearer <token>"

        Args:
            headers: Dict of HTTP headers (e.g., {"Authorization": "Bearer <token>"}).

        Returns:
            User info dict if authenticated, None otherwise.
        """
        auth_header = headers.get("Authorization")

        if not auth_header:
            logger.warning("No Authorization header in request")
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning("Invalid Authorization header format")
            return None

        token = parts[1]
        return self.verify_token(token)


def create_oauth_manager_from_config(config_manager) -> OAuthSecurityManager:
    """
    Creates OAuthSecurityManager from ConfigManager.

    Expected config structure:
    {
        "oauth": {
            "client_id": "...",
            "allowed_domains": ["miempresa.com", "cenf.com.ar"],
            "allowed_emails": ["admin@example.com"]
        }
    }
    """
    client_id = config_manager.get_setting("oauth.client_id")
    allowed_domains = config_manager.get_setting("oauth.allowed_domains", [])
    allowed_emails = config_manager.get_setting("oauth.allowed_emails", [])

    if not client_id:
        raise ValueError("OAuth client_id not configured")

    return OAuthSecurityManager(
        client_id=client_id,
        allowed_domains=allowed_domains,
        allowed_emails=allowed_emails,
        require_domain_match=True
    )
