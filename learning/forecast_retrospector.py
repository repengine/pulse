"""
forecast_retrospector.py

Reconstructs and analyzes past worldstates from forecast logs/history.

Usage:
    worldstates = reconstruct_worldstates("logs/forecast_batch_output.jsonl")
"""

import json
from typing import List, Dict, Callable, Optional
import os
from trust_system.forecast_retrospector import *

def compute_retrodiction_error(forecast: Dict, current_state: Dict, keys: Optional[List[str]] = None) -> float:
    """
    Compute symbolic/variable delta between forecast's initial assumption
    and what the current_state actually contains now.

    Args:
        forecast (Dict): The forecast being evaluated
        current_state (Dict): Ground truth snapshot
        keys (Optional[List[str]]): Specific overlays or variables to score (default: all)

    Returns:
        float: Normalized mean squared error (0–1+)
    """
    # Robustness: handle missing nested keys and type errors
    f_init = forecast.get("forecast", {}).get("start_state", {}).get("overlays", {})
    c_now = current_state.get("overlays", {})
    if not isinstance(f_init, dict) or not isinstance(c_now, dict):
        return 0.0
    keys = keys or list(set(f_init.keys()) & set(c_now.keys()))
    if not keys:
        return 0.0

    deltas = []
    for k in keys:
        try:
            a = float(f_init.get(k, 0))
            b = float(c_now.get(k, 0))
            deltas.append((a - b) ** 2)
        except Exception as e:
            # Error handling: log if verbose/debug needed
            continue

    if not deltas:
        return 0.0

    return round(sum(deltas) / len(deltas), 4)


def reconstruct_worldstates(
    forecast_log_path: str,
    filter_fn: Optional[Callable[[Dict], bool]] = None,
    limit: Optional[int] = None,
    verbose: bool = False
) -> List[Dict]:
    """
    Loads forecast logs and reconstructs worldstates.
    Optionally filters entries with filter_fn.

    Args:
        forecast_log_path (str): Path to forecast log (.jsonl)
        filter_fn (Callable[[Dict], bool], optional): Function to filter entries.
        limit (int, optional): Max number of worldstates to return.
        verbose (bool, optional): Print progress and errors.

    Returns:
        List[Dict]: List of reconstructed worldstate snapshots.
    """
    worldstates = []
    if not os.path.exists(forecast_log_path):
        if verbose:
            print(f"[Retrospector] File not found: {forecast_log_path}")
        return worldstates
    try:
        with open(forecast_log_path, "r") as f:
            for i, line in enumerate(f):
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    if verbose:
                        print(f"[Retrospector] Skipping malformed line {i+1}")
                    continue
                if filter_fn and not filter_fn(entry):
                    continue
                ws = entry.get("worldstate_snapshot")
                if ws:
                    worldstates.append(ws)
                    if limit and len(worldstates) >= limit:
                        break
    except Exception as e:
        print(f"[Retrospector] Error: {e}")
    return worldstates

# --- Simple test ---
if __name__ == "__main__":
    # Example: print number of worldstates in a file
    path = "logs/forecast_batch_output.jsonl"
    ws_list = reconstruct_worldstates(path, verbose=True)
    print(f"Loaded {len(ws_list)} worldstates from {path}")

    # Test: compute_retrodiction_error with dummy data
    dummy_forecast = {
        "forecast": {
            "start_state": {
                "overlays": {"hope": 0.7, "despair": 0.2}
            }
        }
    }
    dummy_state = {"overlays": {"hope": 0.6, "despair": 0.3}}
    err = compute_retrodiction_error(dummy_forecast, dummy_state)
    print(f"Retrodiction error (dummy): {err}")
