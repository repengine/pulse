"""
pulse_prompt_logger.py

Logs prompts, config, and overlays used to generate digests or batch forecasts.
Supports log rotation for archival.

Usage:
    log_prompt("Forecast batch run", config, overlays)

Author: Pulse AI Engine
"""

import json
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("pulse_prompt_logger")
if not logger.handlers:
    handler = RotatingFileHandler("logs/prompt_log.jsonl", maxBytes=1024*1024, backupCount=5)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def log_prompt(prompt: str, config: dict, overlays: dict, path: str = "logs/prompt_log.jsonl"):
    """
    Log a prompt and associated metadata to a rotating log file.

    Args:
        prompt: Description or prompt string.
        config: Configuration dict.
        overlays: Overlay values dict.
        path: Log file path.
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "prompt": prompt,
        "config": config,
        "overlays": overlays
    }
    try:
        logger.info(json.dumps(entry))
    except Exception as e:
        logger.error(f"Prompt log error: {e}")

# Example usage:
# log_prompt("Batch run", {"param": 1}, {"hope": 0.5})
