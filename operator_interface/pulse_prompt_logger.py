"""
pulse_prompt_logger.py

Logs prompts, config, and overlays used to generate digests or batch forecasts.

Usage:
    log_prompt("Forecast batch run", config, overlays)

Author: Pulse AI Engine
"""

import json
import hashlib
from datetime import datetime
import logging
from core.path_registry import PATHS
from typing import Optional

logger = logging.getLogger("pulse_prompt_logger")

def prompt_hash(prompt: str, config: dict) -> str:
    """
    Generate a hash for a prompt/config pair.
    """
    s = prompt + json.dumps(config, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

def log_prompt(prompt: str, config: dict, overlays: dict, path: str = None):
    """
    Log a prompt with metadata and hash.
    """
    if path is None:
        path = PATHS.get("PROMPT_LOG", "logs/prompt_log.jsonl")
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "prompt": prompt,
        "config": config,
        "overlays": overlays,
        "prompt_hash": prompt_hash(prompt, config)
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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Prompt Log Viewer CLI")
    parser.add_argument("--recent", type=int, default=10, help="Show N most recent prompts")
    parser.add_argument("--search", type=str, default=None, help="Search for prompt substring")
    parser.add_argument("--logfile", type=str, default="logs/prompt_log.jsonl", help="Prompt log file")
    parser.add_argument("--hash", type=str, default=None, help="Show prompt by hash")
    args = parser.parse_args()
    try:
        with open(args.logfile, "r", encoding="utf-8") as f:
            lines = f.readlines()
        entries = []
        for line in lines:
            try:
                entries.append(json.loads(line))
            except Exception:
                continue
        if args.hash:
            found = [e for e in entries if e.get("prompt_hash") == args.hash]
            for e in found:
                print(json.dumps(e, indent=2))
            if not found:
                print("No prompt found with that hash.")
        else:
            if args.search:
                entries = [e for e in entries if args.search.lower() in e.get("prompt", "").lower()]
            for e in entries[-args.recent:]:
                print(f"[{e['timestamp']}] {e['prompt_hash']} | {e['prompt']}")
    except Exception as e:
        print(f"Prompt log error: {e}")
