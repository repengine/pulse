"""
forecast_retrospector.py

Reconstructs and analyzes past worldstates from forecast logs/history.

Usage:
    worldstates = reconstruct_worldstates("logs/forecast_batch_output.jsonl")
"""

import json
from typing import List, Dict, Callable

def reconstruct_worldstates(forecast_log_path: str, filter_fn: Callable[[Dict], bool] = None) -> List[Dict]:
    """
    Loads forecast logs and reconstructs worldstates.
    Optionally filters entries with filter_fn.
    """
    worldstates = []
    try:
        with open(forecast_log_path, "r") as f:
            for line in f:
                entry = json.loads(line)
                if filter_fn and not filter_fn(entry):
                    continue
                ws = entry.get("worldstate_snapshot")
                if ws:
                    worldstates.append(ws)
    except Exception as e:
        print(f"[Retrospector] Error: {e}")
    return worldstates
