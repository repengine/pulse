"""
Logging utilities for Pulse modules.
Standardizes logging format and provides log rotation support.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from core.path_registry import PATHS

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

LOG_FILE_PATH = str(PATHS.get("LOG_FILE", "logs/pulse.log"))

DEFAULT_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"


def get_logger(
    name,
    level=logging.INFO,
    log_to_file: bool = True,
    max_bytes: int = 5_000_000,
    backup_count: int = 3,
):
    """
    Returns a configured logger with standardized format and optional log rotation.
    Args:
        name (str): Logger name.
        level: Logging level (default: logging.INFO)
        log_to_file (bool): If True, logs to file as well as stdout.
        max_bytes (int): Max log file size before rotation (default 5MB).
        backup_count (int): Number of rotated log files to keep.
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        if log_to_file:
            os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
            file_handler = RotatingFileHandler(
                LOG_FILE_PATH,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    logger.setLevel(level)
    return logger


def log_info(msg: str):
    """
    Simple info-level logger for convenience.
    """
    logger = get_logger("pulse")
    logger.info(msg)
