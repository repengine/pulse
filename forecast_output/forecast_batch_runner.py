"""
Module: forecast_batch_runner.py
Pulse Version: v0.012.0
Location: pulse/forecast_output/
Last Updated: 2025-04-17
Author: Pulse AI Engine

Description:
Generates multiple foresight forecasts in batch from a WorldState.
Links directly into forecast_generator, compressor, and summary modules.

Used by:
- Pulse CLI
- Strategos Digest Builder
- PFPA Batch Logger

Log Output:
- logs/forecast_batch_output.jsonl
"""

import json
import os
from datetime import datetime
from typing import List, Dict

from forecast_output.forecast_generator import generate_forecast
from forecast_output.forecast_compressor import compress_forecasts
from forecast_output.forecast_summary_synthesizer import summarize_forecasts
from simulation_engine.worldstate import WorldState
from core.path_registry import PATHS
assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

BATCH_LOG_PATH = PATHS.get("BATCH_LOG_PATH", "logs/forecast_batch_output.jsonl")

def ensure_log_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def run_forecast_batch(
    state: WorldState,
    batch_size: int = 5,
    assets: List[str] = None,
    horizon_days: int = 2
) -> List[Dict]:
    """
    Generates a batch of forecasts and routes them through compressor + summary
    """
    ensure_log_dir(BATCH_LOG_PATH)

    results = []
    for i in range(batch_size):
        forecast = generate_forecast(state, assets=assets, horizon_days=horizon_days)
        if forecast:
            results.append(forecast)

    if results:
        try:
            with open(BATCH_LOG_PATH, "a") as f:
                for r in results:
                    f.write(json.dumps(r) + "\n")
        except Exception as e:
            print(f"[BatchRunner] Logging error: {e}")

        compress_forecasts(results)
        summarize_forecasts(results)

    return results

# Example usage
if __name__ == "__main__":
    from simulation_engine.worldstate import WorldState
    dummy = WorldState()
    batch = run_forecast_batch(dummy, batch_size=3, horizon_days=2)
    print(f"✅ Batch complete. {len(batch)} forecasts generated.")
