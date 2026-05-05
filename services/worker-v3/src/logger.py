"""
Worker Logger — Dev/prod mode logging for worker-v3.
====================================================

Provides environment-aware logging configuration.
Dev mode: DEBUG level. Production: INFO level.

:created:   2026-05-05
:filename:  logger.py
:path:      services/worker-v3/src/logger.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
import os


class WorkerLogger:
    """
    Environment-aware logger for the worker service.

    Dev mode (default): DEBUG level, human-readable output.
    Production: INFO level, structured output.
    """

    def __init__(self, config_manager=None):
        self._is_production = os.environ.get("ENVIRONMENT", "development") == "production"
        self._level = logging.INFO if self._is_production else logging.DEBUG
        logging.basicConfig(level=self._level)
        logging.getLogger().setLevel(self._level)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger for the given module name."""
        logger = logging.getLogger(name)
        return logger
