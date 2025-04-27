"""
batch_runner.py

Runs simulation batches from config files or sweep inputs.
Each batch triggers:
- Simulation run (via run_turn or simulate())
- Forecast generation
- Full forecast pipeline processing
- Summary and export of results

Author: Pulse v0.24
"""

import json
import os
import traceback
import tempfile
import shutil
from typing import Dict, List, Optional, Any
from core.path_registry import PATHS
from simulation_engine.turn_engine import run_turn
from simulation_engine.worldstate import WorldState
from forecast_output.forecast_generator import generate_forecast
from learning.forecast_pipeline_runner import run_forecast_pipeline
from utils.log_utils import log_info


DEFAULT_BATCH_OUTPUT = PATHS.get("BATCH_OUTPUT", "logs/batch_output.jsonl")

def load_batch_config(path: str) -> List[Dict[str, Any]]:
    """Load a batch configuration from a JSON file."""
    with open(path, "r") as f:
        return json.load(f)

def run_batch_from_config(
    configs: List[Dict[str, Any]], 
    export_path: Optional[str] = None,
    learning_engine=None  # <-- Add this parameter
) -> List[Dict[str, Any]]:
    """
    Executes a batch of simulation configs.

    Args:
        configs (List[Dict]): Simulation configurations
        export_path (str): Optional output path for saving results
        learning_engine: Optional LearningEngine instance for hooks

    Returns:
        List[Dict]: Pipeline results per config, including error info if failed.
    """
    results = []
    for i, cfg in enumerate(configs):
        try:
            log_info(f"[BATCH] Running batch {i+1}/{len(configs)}")
            # Step 1: Initialize worldstate
            state = WorldState(**cfg.get("state_overrides", {}))
            for _ in range(cfg.get("turns", 1)):
                run_turn(state, learning_engine=learning_engine)
            # Step 2: Generate forecasts
            forecasts = generate_forecast(state.to_dict() if hasattr(state, "to_dict") else vars(state))
            # Step 3: Run forecast pipeline
            if isinstance(forecasts, dict):
                forecasts = [forecasts]
            result = run_forecast_pipeline(forecasts)
            result["config"] = cfg
            result["batch_index"] = i
            results.append(result)
        except Exception as e:
            tb = traceback.format_exc()
            log_info(f"[BATCH] Error on batch {i+1}: {type(e).__name__}: {e}\n{tb}")
            results.append({
                "config": cfg,
                "batch_index": i,
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "traceback": tb
                }
            })

    if export_path:
        try:
            # Write to a temp file and move atomically
            with tempfile.NamedTemporaryFile("w", delete=False, dir=os.path.dirname(export_path), encoding="utf-8") as tf:
                for r in results:
                    tf.write(json.dumps(r) + "\n")
                tempname = tf.name
            shutil.move(tempname, export_path)
            log_info(f"[BATCH] Results saved to {export_path}")
        except Exception as e:
            tb = traceback.format_exc()
            log_info(f"[BATCH] Failed to export batch: {type(e).__name__}: {e}\n{tb}")

    return results


if __name__ == "__main__":
    """
    Example usage: runs two sample configs and exports results.
    TODO: Add CLI/config file support for batch execution.
    """
    sample_config = [
        {"state_overrides": {"hope": 0.6, "despair": 0.2}, "turns": 1},
        {"state_overrides": {"hope": 0.3, "despair": 0.5}, "turns": 1},
    ]
    run_batch_from_config(sample_config, export_path=str(DEFAULT_BATCH_OUTPUT))
