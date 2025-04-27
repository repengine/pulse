"""
pulse_prompt_logger.py

Logs prompts, config, and overlays used to generate digests or batch forecasts.

Usage:
    log_prompt("Forecast batch run", config, overlays)

Author: Pulse AI Engine
"""

import json
from datetime import datetime
import logging

logger = logging.getLogger("pulse_prompt_logger")

import hashlib

def prompt_hash(prompt: str, config: dict) -> str:
    """
    Generate a consistent 12-character hash for a given prompt and config.
    """
    # Sort keys to ensure deterministic output
    data = prompt + json.dumps(config, sort_keys=True)
    return hashlib.md5(data.encode("utf-8")).hexdigest()[:12]

def log_prompt(prompt: str, config: dict, overlays: dict, path: str = "logs/prompt_log.jsonl"):
    from datetime import timezone
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "config": config,
        "overlays": overlays
    }
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(f"Prompt logged to {path}")
    except Exception as e:
        logger.error(f"Prompt log error: {e}")
