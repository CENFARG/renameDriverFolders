"""Final verification: all decomposed modules under 250 lines, no debug code."""
import os
import re
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MAX_LINES = 250


def _py_files(directory, exclude_tests=True):
    """Yield Python file paths in directory."""
    for root, dirs, files in os.walk(os.path.join(ROOT, directory)):
        if exclude_tests and "tests" in root:
            continue
        for f in files:
            if f.endswith(".py") and f not in ("__init__.py", "conftest.py", "main.py"):
                yield os.path.join(root, f)


class TestFileSizeCompliance:
    """Verify all decomposed modules are under 250 lines."""

    @pytest.mark.parametrize("filepath", list(_py_files("packages/core-renombrador/src")))
    def test_core_module_under_250(self, filepath):
        with open(filepath) as f:
            lines = len(f.readlines())
        assert lines <= MAX_LINES, f"{os.path.relpath(filepath, ROOT)}: {lines} lines (max {MAX_LINES})"

    @pytest.mark.parametrize("filepath", list(_py_files("services/api-server-v3/src")))
    def test_api_v3_module_under_250(self, filepath):
        with open(filepath) as f:
            lines = len(f.readlines())
        assert lines <= MAX_LINES, f"{os.path.relpath(filepath, ROOT)}: {lines} lines (max {MAX_LINES})"

    @pytest.mark.parametrize("filepath", list(_py_files("services/worker-v3/src")))
    def test_worker_v3_module_under_250(self, filepath):
        with open(filepath) as f:
            lines = len(f.readlines())
        assert lines <= MAX_LINES, f"{os.path.relpath(filepath, ROOT)}: {lines} lines (max {MAX_LINES})"


class TestNoPrintStatements:
    """Verify no print() calls in production code (excluding main.py)."""

    @pytest.mark.parametrize("filepath", list(_py_files("services/worker-v3/src")))
    def test_worker_no_prints(self, filepath):
        with open(filepath) as f:
            content = f.read()
        assert "print(" not in content, f"{os.path.relpath(filepath, ROOT)} contains print()"

    @pytest.mark.parametrize("filepath", list(_py_files("services/api-server-v3/src")))
    def test_api_no_prints(self, filepath):
        with open(filepath) as f:
            content = f.read()
        assert "print(" not in content, f"{os.path.relpath(filepath, ROOT)} contains print()"


class TestLoggingSetup:
    """Verify all modules use logging, not print."""

    @pytest.mark.parametrize("filepath", list(_py_files("services/worker-v3/src")))
    def test_worker_has_logger(self, filepath):
        with open(filepath) as f:
            content = f.read()
        assert "logging.getLogger" in content or "logger" in content, \
            f"{os.path.relpath(filepath, ROOT)} missing logger setup"
