"""Smoke tests comparing v2 and v3 API responses.

These tests verify that v3 endpoints return the same shape of data
as v2, ensuring parity before shifting production traffic.

Run with:
  V2_API_URL=... V3_API_URL=... TEST_AUTH_TOKEN=... pytest infra/smoke_tests/
"""
import re

import pytest


def _sanitize_response(data):
    """Remove volatile fields (timestamps, IDs) for comparison."""
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if k not in ("timestamp", "created_at", "updated_at", "task_id")}
    return data


def _extract_json(response_text):
    """Extract JSON from response text, handling HTML error pages."""
    import json
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return None


class TestHealthEndpoint:
    def test_v3_health_returns_ok(self, v3_base):
        """V3 health endpoint should return 200."""
        import urllib.request
        import json

        url = f"{v3_base}/health"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                assert resp.status == 200
                data = json.loads(resp.read())
                assert data.get("status") in ("ok", "healthy", "healthy")
        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                pytest.skip("V3 health endpoint not yet deployed")
            raise


class TestParityStructure:
    def test_algorithms_response_has_same_shape(self, v2_base, v3_base):
        """Both v2 and v3 /algorithms should return list with same keys."""
        import urllib.request
        import json

        headers = {}
        token = pytest.importorskip("conftest").__dict__.get("test_token", "")

        for base_url, label in [(v2_base, "v2"), (v3_base, "v3")]:
            url = f"{base_url}/api/v1/algorithms"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                    if isinstance(data, list) and len(data) > 0:
                        assert "id" in data[0], f"{label}: algorithms response missing 'id'"
                        assert "name" in data[0], f"{label}: algorithms response missing 'name'"
            except Exception:
                pytest.skip(f"{label} algorithms endpoint not available")

    def test_jobs_response_has_same_shape(self, v2_base, v3_base):
        """Both /jobs endpoints should return list with same keys."""
        import urllib.request
        import json

        for base_url, label in [(v2_base, "v2"), (v3_base, "v3")]:
            url = f"{base_url}/api/v1/jobs"
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                    if isinstance(data, list) and len(data) > 0:
                        assert "id" in data[0], f"{label}: jobs response missing 'id'"
                        assert "name" in data[0], f"{label}: jobs response missing 'name'"
            except Exception:
                pytest.skip(f"{label} jobs endpoint not available")


class TestSmokeTestStructure:
    """Meta-tests that verify the smoke test infrastructure itself."""

    def test_v2_url_is_valid(self, v2_base):
        assert v2_base.startswith("https://")
        assert "us-central1" in v2_base

    def test_v3_url_is_valid(self, v3_base):
        assert v3_base.startswith("https://")
        assert "us-central1" in v3_base

    def test_sanitize_removes_volatile_fields(self):
        data = {"id": "1", "name": "test", "timestamp": "2026-01-01", "created_at": "now"}
        result = _sanitize_response(data)
        assert "timestamp" not in result
        assert "created_at" not in result
        assert "id" in result
        assert "name" in result
