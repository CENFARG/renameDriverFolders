"""Tests for v3 parallel deployment configuration."""
import os
import yaml
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_yaml(path):
    with open(os.path.join(ROOT, path)) as f:
        return yaml.safe_load(f)


def _read_file(path):
    with open(os.path.join(ROOT, path)) as f:
        return f.read()


class TestApiServerCloudbuild:
    def test_uses_v3_image_name(self):
        config = _load_yaml("services/api-server-v3/cloudbuild.yaml")
        images = config.get("images", [])
        assert any("api-server-v3" in img for img in images)

    def test_builds_from_v3_dockerfile(self):
        config = _load_yaml("services/api-server-v3/cloudbuild.yaml")
        build_step = config["steps"][0]
        assert "services/api-server-v3/Dockerfile.build" in build_step["args"]

    def test_deploys_v3_service_name(self):
        config = _load_yaml("services/api-server-v3/cloudbuild.yaml")
        deploy_step = config["steps"][2]
        assert "api-server-v3" in " ".join(deploy_step["args"])

    def test_uses_commit_sha_tag(self):
        config = _load_yaml("services/api-server-v3/cloudbuild.yaml")
        images = config.get("images", [])
        assert any("$COMMIT_SHA" in img for img in images)


class TestWorkerCloudbuild:
    def test_uses_v3_image_name(self):
        config = _load_yaml("services/worker-v3/cloudbuild.yaml")
        images = config.get("images", [])
        assert any("worker-v3" in img for img in images)

    def test_builds_from_v3_dockerfile(self):
        config = _load_yaml("services/worker-v3/cloudbuild.yaml")
        build_step = config["steps"][0]
        assert "services/worker-v3/Dockerfile.build" in build_step["args"]

    def test_worker_is_not_public(self):
        config = _load_yaml("services/worker-v3/cloudbuild.yaml")
        deploy_step = config["steps"][2]
        assert "--no-allow-unauthenticated" in deploy_step["args"]


class TestApiDockerfileBuild:
    def test_copies_v3_paths(self):
        content = _read_file("services/api-server-v3/Dockerfile.build")
        assert "services/api-server-v3/requirements.txt" in content
        assert "services/api-server-v3/src" in content

    def test_no_v2_references(self):
        content = _read_file("services/api-server-v3/Dockerfile.build")
        assert "services/api-server/" not in content
        assert "services/api-server/src" not in content


class TestWorkerDockerfileBuild:
    def test_copies_v3_paths(self):
        content = _read_file("services/worker-v3/Dockerfile.build")
        assert "services/worker-v3/requirements.txt" in content
        assert "services/worker-v3/src" in content

    def test_no_v2_references(self):
        content = _read_file("services/worker-v3/Dockerfile.build")
        assert "services/worker-renombrador/" not in content


class TestDeployScript:
    def test_deploy_script_exists(self):
        path = os.path.join(ROOT, "infra", "deploy-v3.sh")
        assert os.path.exists(path)

    def test_deploy_script_references_v3(self):
        content = _read_file("infra/deploy-v3.sh")
        assert "api-server-v3" in content
        assert "worker-v3" in content
        assert "traffic" in content
