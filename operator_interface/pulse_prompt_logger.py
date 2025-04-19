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
from core.path_registry import PATHS

logger = logging.getLogger("pulse_prompt_logger")

def log_prompt(prompt: str, config: dict, overlays: dict, path: str = None):
    if path is None:
        path = PATHS.get("PROMPT_LOG", "logs/prompt_log.jsonl")
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
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

def get_prompt_hash(trace_id: str) -> Optional[str]:
    """
    Retrieve prompt hash for a given trace_id.
    Stub: Replace with actual lookup from prompt log if available.
    """
    return f"hash_{trace_id}"
