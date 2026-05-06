"""
Error Handler — Global exception handling.
============================================

Sets up unhandled exception logging for the application.

:created:   2025-12-05
:filename:  error_handler.py
:path:      packages/core-renombrador/src/core_renombrador/error_handler.py
:author:    amBotHs + CENF
:version:   2.0.0
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import sys
import logging
from typing import Type

logger = logging.getLogger(__name__)

class ErrorHandler:
    @classmethod
    def setup_global_exception_handling(cls):
        sys.excepthook = cls._handle_exception
        logger.info("Manejo global de excepciones configurado.")

    @classmethod
    def _handle_exception(cls, exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: any):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Excepción no capturada:", exc_info=(exc_type, exc_value, exc_traceback))
