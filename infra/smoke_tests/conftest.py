"""Conftest for smoke tests — provides v2 and v3 base URLs."""
import os

import pytest


def _env_or_default(key, default):
    return os.environ.get(key, default)


@pytest.fixture
def v2_base():
    """V2 API server base URL."""
    return _env_or_default("V2_API_URL", "https://renombradorarchivosgdrive-api-server-v2-702567224563.us-central1.run.app")


@pytest.fixture
def v3_base():
    """V3 API server base URL."""
    return _env_or_default("V3_API_URL", "https://renombradorarchivosgdrive-api-server-v3-702567224563.us-central1.run.app")


@pytest.fixture
def test_token():
    """Bearer token for authenticated endpoints."""
    return os.environ.get("TEST_AUTH_TOKEN", "")
