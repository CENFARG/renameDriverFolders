"""
Test: Remove print() statements from worker-v3 source (T2.9).

Verifies that no production code uses print() — only logger.

:task: T2.9 - Remove All print() Statements
:phase: RED (test written first)
"""

import os
import glob


class TestNoPrintStatements:
    """Source files should use logger, not print()."""

    def test_no_print_in_source_files(self):
        """No print() calls in src/ directory."""
        src_dir = os.path.join(os.path.dirname(__file__), "..", "src")
        src_dir = os.path.normpath(src_dir)

        offenders = []
        for py_file in glob.glob(os.path.join(src_dir, "*.py")):
            with open(py_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    # Skip comments and docstrings
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if "print(" in line:
                        offenders.append(f"{os.path.basename(py_file)}:{line_num}: {stripped}")

        assert offenders == [], (
            f"Found {len(offenders)} print() calls in source:\n"
            + "\n".join(offenders)
        )

    def test_logger_used_in_all_modules(self):
        """All source modules should have a logger."""
        src_dir = os.path.join(os.path.dirname(__file__), "..", "src")
        src_dir = os.path.normpath(src_dir)

        modules_without_logger = []
        for py_file in glob.glob(os.path.join(src_dir, "*.py")):
            basename = os.path.basename(py_file)
            # Skip __init__.py and main.py (uses LoggerManager)
            if basename in ("__init__.py",):
                continue

            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            if "logger = logging.getLogger" not in content and "get_logger" not in content:
                modules_without_logger.append(basename)

        assert modules_without_logger == [], (
            f"Modules without logger: {modules_without_logger}"
        )
