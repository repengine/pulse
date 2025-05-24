"""
Standardized error handling for Pulse modules.
Adds custom exception classes and stack trace logging utilities.
"""

import logging
import traceback
from typing import Optional


class PulseError(Exception):
    """Base exception for Pulse errors."""

    pass


class DataValidationError(PulseError):
    """Raised when data validation fails."""

    pass


class ConfigurationError(PulseError):
    """Raised for configuration-related errors."""

    pass


class ExternalServiceError(PulseError):
    """Raised when an external service call fails."""

    pass


def log_exception(
    logger: logging.Logger, exc: Exception, message: Optional[str] = None
) -> None:
    """
    Logs an exception with stack trace for debugging.
    Args:
        logger (logging.Logger): Logger to use.
        exc (Exception): The exception instance.
        message (str, optional): Additional message to log.
    """
    if message:
        logger.error(f"{message}: {exc}")
    else:
        logger.error(f"Exception: {exc}")
    logger.error(traceback.format_exc())
