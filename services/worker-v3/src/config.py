"""
Worker Config — Configuration, secrets, and credentials.
========================================================

Centralizes all worker initialization: Secret Manager access,
Google Cloud credentials, feature flags, and database manager setup.

:created:   2026-05-05
:filename:  config.py
:path:      services/worker-v3/src/config.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
import os

import google.auth
from google.cloud import secretmanager
from google.oauth2.credentials import Credentials as OAuthCredentials

logger = logging.getLogger(__name__)

DEFAULT_GCP_PROJECT = "cloud-functions-474716"


def get_secret(secret_id: str) -> str:
    """
    Retrieve a secret from environment variables (local) or
    Google Secret Manager (production).

    Priority:
        1. Environment variable (e.g. SUPABASE_URL for secret_id "supabase-url")
        2. Google Secret Manager (latest version)

    Args:
        secret_id: Secret identifier, e.g. "supabase-url".

    Returns:
        Secret value as string, or empty string on failure.
    """
    env_var = secret_id.upper().replace("-", "_")
    local_value = os.environ.get(env_var)

    if local_value:
        logger.info(f"Using local config for {secret_id}")
        return local_value.strip()

    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get("GCP_PROJECT_ID", DEFAULT_GCP_PROJECT)
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        logger.info(f"Using Secret Manager for {secret_id}")
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        logger.warning(f"Failed to get secret {secret_id}: {e}")
        return ""


def get_credentials():
    """
    Obtain Google Cloud credentials via Application Default Credentials.

    Returns:
        Google auth credentials with Drive and Cloud Platform scopes.

    Raises:
        Exception: If ADC is not available.
    """
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/cloud-platform",
    ]
    try:
        credentials, project_id = google.auth.default(scopes=scopes)
        logger.info("Using Application Default Credentials")
        return credentials
    except Exception as e:
        logger.error(f"Failed to get credentials: {e}")
        raise


def create_credentials_from_token(access_token: str):
    """
    Build OAuth credentials from a user access token.

    Args:
        access_token: OAuth access token from user's Google session.

    Returns:
        OAuthCredentials scoped for Drive access.
    """
    credentials = OAuthCredentials(
        token=access_token,
        scopes=["https://www.googleapis.com/auth/drive"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id="",
        client_secret="",
    )
    logger.info(f"Created OAuth credentials from access token: {access_token[:20]}...")
    return credentials


class WorkerConfig:
    """
    Centralized worker configuration.

    Reads feature flags from environment and initializes the
    appropriate database mode (Supabase, GCS, or local JSON).

    Attributes:
        use_supabase: Whether Supabase mode is active.
        use_gcs: Whether GCS mode is active.
        enable_ocr: Whether OCR extraction is enabled.
    """

    def __init__(self):
        self.use_supabase = os.environ.get("USE_SUPABASE", "false").lower() == "true"
        self.use_gcs = (
            os.environ.get("USE_GCS", "false").lower() == "true"
            or "GCS_BUCKET_NAME" in os.environ
        )
        self.enable_ocr = os.environ.get("ENABLE_OCR", "true").lower() == "true"

        if self.use_supabase:
            self._load_supabase_credentials()

    def _load_supabase_credentials(self):
        """Load Supabase URL and key from Secret Manager or env."""
        supabase_url = get_secret("supabase-url")
        supabase_key = get_secret("supabase-key")

        if supabase_url and supabase_key:
            os.environ["SUPABASE_URL"] = supabase_url
            os.environ["SUPABASE_KEY"] = supabase_key
            logger.info("Supabase credentials loaded from Secret Manager")
        else:
            logger.warning(
                "Supabase credentials not found in Secret Manager, "
                "falling back to JSON mode"
            )
            self.use_supabase = False
