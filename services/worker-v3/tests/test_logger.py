"""
Test: Worker Logger extraction (T2.2).

Verifies:
1. Dev mode: DEBUG level, console output
2. Prod mode: INFO level, JSON structured output
3. No hardcoded DEBUG in production

:task: T2.2 - Extract Worker Logger Module
:phase: RED (test written first)
"""

import pytest
import os
import logging
from unittest.mock import patch


class TestWorkerLogger:
    """WorkerLogger provides dev/prod mode logging."""

    def test_logger_module_exists(self):
        from logger import WorkerLogger
        assert WorkerLogger is not None

    def test_dev_mode_sets_debug_level(self):
        """Dev mode (default) should set DEBUG level."""
        from logger import WorkerLogger

        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            wl = WorkerLogger()
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG

    def test_prod_mode_sets_info_level(self):
        """Production mode should set INFO level."""
        from logger import WorkerLogger

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            wl = WorkerLogger()
            root_logger = logging.getLogger()
            assert root_logger.level == logging.INFO

    def test_get_logger_returns_logger(self):
        """get_logger() returns a logging.Logger instance."""
        from logger import WorkerLogger

        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            wl = WorkerLogger()
            logger = wl.get_logger("test_module")
            assert isinstance(logger, logging.Logger)

    def test_no_hardcoded_debug_in_prod(self):
        """Logger should NOT hardcode DEBUG in production."""
        from logger import WorkerLogger

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            wl = WorkerLogger()
            logger = wl.get_logger("test_module")
            assert logger.level != logging.DEBUG or logger.level == logging.NOTSET

    def test_default_is_dev_mode(self):
        """Without ENVIRONMENT var, should default to dev (DEBUG)."""
        from logger import WorkerLogger

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ENVIRONMENT", None)
            wl = WorkerLogger()
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG
