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
import argparse # Added argparse
from typing import Dict, List, Optional, Any

# Ensure log_utils is imported before its potential first use
from utils.log_utils import log_info

from core.path_registry import PATHS
from core.pulse_config import SHADOW_MONITOR_CONFIG

try:
    from diagnostics.shadow_model_monitor import ShadowModelMonitor
except ImportError:
    ShadowModelMonitor = None
    # Now log_info is guaranteed to be defined here
    log_info("Warning: ShadowModelMonitor could not be imported for batch_runner.")

from simulation_engine.simulator_core import simulate_forward
from simulation_engine.worldstate import WorldState, SymbolicOverlays # Ensure SymbolicOverlays is imported
from forecast_output.forecast_generator import generate_forecast
from learning.forecast_pipeline_runner import run_forecast_pipeline


DEFAULT_BATCH_OUTPUT = PATHS.get("BATCH_OUTPUT", "logs/batch_output.jsonl")

def load_batch_config(path: str) -> List[Dict[str, Any]]:
    """Load a batch configuration from a JSON file."""
    with open(path, "r") as f:
        return json.load(f)

def run_batch_from_config(
    configs: List[Dict[str, Any]],
    export_path: Optional[str] = None,
    learning_engine=None,
    gravity_enabled: bool = True # Added gravity_enabled parameter
) -> List[Dict[str, Any]]:
    """
    Executes a batch of simulation configs.

    Args:
        configs (List[Dict]): Simulation configurations
        export_path (str): Optional output path for saving results
        learning_engine: Optional LearningEngine instance for hooks
        gravity_enabled (bool): Whether gravity correction is enabled (default: True)

    Returns:
        List[Dict]: Pipeline results per config, including error info if failed.
    """
    results = []

    shadow_monitor = None # Removed type hint to fix Pylance error
    if ShadowModelMonitor and SHADOW_MONITOR_CONFIG and SHADOW_MONITOR_CONFIG.get("enabled", False):
        try:
            shadow_monitor = ShadowModelMonitor(
                threshold=SHADOW_MONITOR_CONFIG["threshold_variance_explained"],
                window_steps=SHADOW_MONITOR_CONFIG["window_steps"],
                critical_variables=SHADOW_MONITOR_CONFIG["critical_variables"]
            )
            log_info("[BATCH] ShadowModelMonitor enabled and initialized.")
        except KeyError as e:
            log_info(f"[BATCH] Error initializing ShadowModelMonitor from config: Missing key {e}. Monitor disabled.")
            shadow_monitor = None
        except Exception as e:
            log_info(f"[BATCH] Error initializing ShadowModelMonitor: {e}. Monitor disabled.")
            shadow_monitor = None
    else:
        log_info("[BATCH] ShadowModelMonitor is disabled or not configured.")

    for i, cfg in enumerate(configs):
        try:
            log_info(f"[BATCH] Running batch {i+1}/{len(configs)}")
            state = WorldState() # Initialize WorldState

            # Initialize or update overlays
            state_overrides = cfg.get("state_overrides", {})
            if state_overrides:
                if not hasattr(state, 'overlays') or not isinstance(state.overlays, SymbolicOverlays):
                    state.overlays = SymbolicOverlays.from_dict(state_overrides)
                else: # It is a SymbolicOverlays instance, update it
                    current_overlays_dict = state.overlays.as_dict() if hasattr(state.overlays, 'as_dict') else {}
                    current_overlays_dict.update(state_overrides)
                    state.overlays = SymbolicOverlays.from_dict(current_overlays_dict)
            elif not hasattr(state, 'overlays') or state.overlays is None :
                 state.overlays = SymbolicOverlays.from_dict({})


            num_turns = cfg.get("turns", 1)
            simulation_results = simulate_forward(
                state=state,
                turns=num_turns,
                use_symbolism=cfg.get("use_symbolism", True),
                return_mode="full", # Shadow monitor needs detailed state
                logger=log_info,
                learning_engine=learning_engine,
                shadow_monitor_instance=shadow_monitor,
                gravity_enabled=gravity_enabled # Pass the gravity_enabled parameter
            )

            final_state_snapshot = {}
            if simulation_results:
                final_state_data = simulation_results[-1].get("full_state")
                if final_state_data and isinstance(final_state_data, dict):
                    final_state_snapshot = final_state_data
                else:
                    log_info("[BATCH] Warning: 'full_state' not found or not a dict in last sim step. Using current WorldState.")
                    final_state_snapshot = state.to_dict() if hasattr(state, "to_dict") else vars(state)
            else:
                log_info("[BATCH] Warning: Simulation produced no results. Using initial state for forecast.")
                final_state_snapshot = state.to_dict() if hasattr(state, "to_dict") else vars(state)

            forecasts = generate_forecast(final_state_snapshot)

            if isinstance(forecasts, dict): # Ensure forecasts is a list for pipeline
                forecasts = [forecasts]
            pipeline_result_data = run_forecast_pipeline(forecasts)
            pipeline_result_data["config"] = cfg
            pipeline_result_data["batch_index"] = i
            results.append(pipeline_result_data)

        except Exception as e:
            tb = traceback.format_exc()
            log_info(f"[BATCH] Error on batch {i+1}: {type(e).__name__}: {e}\n{tb}")
            results.append({
                "config": cfg,
                "batch_index": i,
                "error": {"type": type(e).__name__, "message": str(e), "traceback": tb}
            })

    if export_path:
        try:
            # Write to a temp file and move atomically
            temp_dir = os.path.dirname(export_path)
            if not temp_dir: # Handle case where export_path is just a filename
                temp_dir = "."
            os.makedirs(temp_dir, exist_ok=True) # Ensure directory exists

            with tempfile.NamedTemporaryFile("w", delete=False, dir=temp_dir, encoding="utf-8") as tf:
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
    parser = argparse.ArgumentParser(description="Run simulation batches.")
    parser.add_argument(
        "--gravity-off",
        action="store_true", # This makes it a boolean flag
        help="Disable gravity correction during simulation."
    )
    # TODO: Add CLI/config file support for batch execution.
    # For now, using sample configs
    args = parser.parse_args()

    sample_configs_main = [
        {"state_overrides": {"hope": 0.6, "despair": 0.2}, "turns": 1},
        {"state_overrides": {"hope": 0.3, "despair": 0.5}, "turns": 1},
    ]

    # Pass the gravity_enabled flag to the runner function
    run_batch_from_config(
        sample_configs_main,
        export_path=str(DEFAULT_BATCH_OUTPUT),
        gravity_enabled=not args.gravity_off # Pass the inverse of the flag
    )
