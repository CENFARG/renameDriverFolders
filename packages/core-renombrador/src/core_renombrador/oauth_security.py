"""
OAuth Security Manager con Domain Whitelisting
==============================================

Manages OAuth 2.0 authentication with Google and domain-based authorization.
Maneja autenticación OAuth 2.0 con Google y autorización basada en dominios.

Features:
- OAuth 2.0 with Google Sign-In
- Domain whitelisting (@miempresa.com, @clientedomain.com)
- Individual email whitelisting
- Token verification
- Rate limiting per user

:created:   2025-12-05
:filename:  oauth_security.py
:author:    amBotHs + CENF
:version:   1.0.0
:status:    Development
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask import request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

logger = logging.getLogger(__name__)


class OAuthSecurityManager:
    """
    Manages OAuth authentication and domain-based authorization.
    Maneja autenticación OAuth y autorización basada en dominios.
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
                      ID de Cliente OAuth de Google.
            allowed_domains: List of allowed email domains (e.g., ["miempresa.com"]).
                            Lista de dominios permitidos.
            allowed_emails: List of specific allowed emails.
                           Lista de emails específicos permitidos.
            require_domain_match: If True, requires email to match allowed domains.
                                 Si True, requiere que el email coincida con dominios permitidos.
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
        Verifica un token de ID OAuth de Google.

        Args:
            token: The ID token from Google Sign-In.
                  El token de ID desde Google Sign-In.

        Returns:
            User info dict if valid, None if invalid.
            Dict de info de usuario si es válido, None si es inválido.
            
            Example return:
            {
                "email": "user@miempresa.com",
                "name": "John Doe",
                "picture": "https://...",
                "email_verified": True,
                "domain": "miempresa.com"
            }
        """
        try:
            # Verify token signature and expiration
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                self.client_id
            )
            
            # Extract user info
            email = idinfo.get("email")
            email_verified = idinfo.get("email_verified", False)
            
            if not email or not email_verified:
                logger.warning("Token verification failed: email not verified")
                return None
            
            # Extract domain from email
            domain = email.split("@")[1] if "@" in email else None
            
            user_info = {
                "email": email,
                "name": idinfo.get("name"),
                "picture": idinfo.get("picture"),
                "email_verified": email_verified,
                "domain": domain,
                "sub": idinfo.get("sub"),  # Google user ID
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
        Verifica si el usuario está autorizado basado en whitelist de dominio/email.

        Args:
            user_info: User info from verify_token().
                      Info de usuario desde verify_token().

        Returns:
            True if authorized, False otherwise.
            True si está autorizado, False de lo contrario.
        """
        email = user_info.get("email")
        domain = user_info.get("domain")
        
        # Check if email is specifically whitelisted
        if email in self.allowed_emails:
            logger.info(f"User {email} authorized via email whitelist")
            return True
        
        # Check domain whitelist
        if self.require_domain_match:
            if domain in self.allowed_domains:
                logger.info(f"User {email} authorized via domain whitelist ({domain})")
                return True
            else:
                logger.warning(f"User {email} denied: domain {domain} not in whitelist")
                return False
        
        # If domain match not required, allow any verified email
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
        Verifica si el usuario ha excedido el límite de tasa.

        Args:
            user_email: User's email.
                       Email del usuario.
            max_requests: Maximum requests allowed in time window.
                         Máximo de requests permitidos en ventana de tiempo.
            window_minutes: Time window in minutes.
                           Ventana de tiempo en minutos.

        Returns:
            True if within limit, False if exceeded.
            True si está dentro del límite, False si lo excedió.
        """
        now = datetime.now()
        cutoff = now - timedelta(minutes=window_minutes)
        
        # Get or create request history for this user
        if user_email not in self._rate_limit_store:
            self._rate_limit_store[user_email] = []
        
        # Remove old requests outside window
        self._rate_limit_store[user_email] = [
            req_time for req_time in self._rate_limit_store[user_email]
            if req_time > cutoff
        ]
        
        # Check if limit exceeded
        request_count = len(self._rate_limit_store[user_email])
        
        if request_count >= max_requests:
            logger.warning(
                f"Rate limit exceeded for {user_email}: "
                f"{request_count}/{max_requests} in {window_minutes}min"
            )
            return False
        
        # Add current request
        self._rate_limit_store[user_email].append(now)
        return True

    def get_user_from_request(self) -> Optional[Dict[str, str]]:
        """
        Extracts and verifies user from Flask request.
        Extrae y verifica usuario desde request de Flask.

        Looks for Authorization header: "Bearer <token>"

        Returns:
            User info dict if authenticated, None otherwise.
            Dict de info de usuario si autenticado, None de lo contrario.
        """
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            logger.warning("No Authorization header in request")
            return None
        
        # Extract token from "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning("Invalid Authorization header format")
            return None
        
        token = parts[1]
        return self.verify_token(token)


# Flask decorator for protected endpoints
def require_auth(
    oauth_manager: OAuthSecurityManager,
    rate_limit_requests: int = 10,
    rate_limit_minutes: int = 1
):
    """
    Decorator to protect Flask endpoints with OAuth authentication.
    Decorador para proteger endpoints de Flask con autenticación OAuth.

    Usage:
        @app.route("/api/protected")
        @require_auth(oauth_manager)
        def protected_endpoint():
            user = g.current_user  # User info is stored in Flask g
            return f"Hello {user['email']}"

    Args:
        oauth_manager: OAuthSecurityManager instance.
        rate_limit_requests: Max requests per window.
        rate_limit_minutes: Time window in minutes.
    """
    from functools import wraps
    from flask import g, jsonify

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verify token
            user_info = oauth_manager.get_user_from_request()
            if not user_info:
                return jsonify({"error": "Invalid or missing token"}), 401
            
            # Check authorization
            if not oauth_manager.is_authorized(user_info):
                return jsonify({
                    "error": "Unauthorized domain",
                    "message": f"Domain {user_info.get('domain')} is not authorized"
                }), 403
            
            # Check rate limit
            if not oauth_manager.check_rate_limit(
                user_info["email"],
                max_requests=rate_limit_requests,
                window_minutes=rate_limit_minutes
            ):
                return jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Max {rate_limit_requests} requests per {rate_limit_minutes} minute(s)"
                }), 429
            
            # Store user info in Flask g for use in endpoint
            g.current_user = user_info
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# Helper function to load config from database/file
def create_oauth_manager_from_config(config_manager) -> OAuthSecurityManager:
    """
    Creates OAuthSecurityManager from ConfigManager.
    Crea OAuthSecurityManager desde ConfigManager.

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
