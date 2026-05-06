"""Tests for CI pipeline configuration."""
import os
import yaml
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_yaml(path):
    with open(os.path.join(ROOT, path)) as f:
        return yaml.safe_load(f)


class TestCIPipeline:
    def test_ci_file_exists(self):
        assert os.path.exists(os.path.join(ROOT, ".github", "workflows", "ci.yml"))

    def test_triggers_on_develop_and_main(self):
        config = _load_yaml(".github/workflows/ci.yml")
        on_key = True  # PyYAML parses `on:` as boolean True
        branches = config[on_key]["push"]["branches"]
        assert "develop" in branches
        assert "main" in branches

    def test_has_lint_job(self):
        config = _load_yaml(".github/workflows/ci.yml")
        assert "lint" in config["jobs"]

    def test_has_test_jobs(self):
        config = _load_yaml(".github/workflows/ci.yml")
        assert "test-core" in config["jobs"]
        assert "test-api-v3" in config["jobs"]
        assert "test-worker-v3" in config["jobs"]

    def test_has_file_size_check(self):
        config = _load_yaml(".github/workflows/ci.yml")
        assert "file-size-check" in config["jobs"]

    def test_test_jobs_depend_on_lint(self):
        config = _load_yaml(".github/workflows/ci.yml")
        for job in ["test-core", "test-api-v3", "test-worker-v3"]:
            assert "lint" in config["jobs"][job]["needs"]

    def test_size_check_depends_on_tests(self):
        config = _load_yaml(".github/workflows/ci.yml")
        needs = config["jobs"]["file-size-check"]["needs"]
        assert "test-core" in needs
        assert "test-api-v3" in needs
        assert "test-worker-v3" in needs

    def test_lint_uses_ruff(self):
        config = _load_yaml(".github/workflows/ci.yml")
        lint_steps = config["jobs"]["lint"]["steps"]
        ruff_step = next((s for s in lint_steps if "ruff" in str(s.get("run", ""))), None)
        assert ruff_step is not None

    def test_max_lines_is_250(self):
        config = _load_yaml(".github/workflows/ci.yml")
        size_steps = config["jobs"]["file-size-check"]["steps"]
        check_step = next((s for s in size_steps if "250" in str(s.get("run", ""))), None)
        assert check_step is not None
