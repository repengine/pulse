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
import argparse  # Added argparse
from typing import Dict, List, Optional, Any

# Ensure log_utils is imported before its potential first use
# First, add the parent directory to the path if running as script
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now try to import, with a fallback if module still not found
try:
    from utils.log_utils import log_info
except ImportError:
    # Fallback implementation if log_utils cannot be imported
    import logging

    logging.basicConfig(
        level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
    )
    logger = logging.getLogger("pulse")

    def log_info(msg):
        """Simple fallback info-level logger."""
        logger.info(msg)

    print("Warning: utils.log_utils module not found, using fallback logger.")

from engine.path_registry import PATHS
from engine.pulse_config import SHADOW_MONITOR_CONFIG
import config.gravity_config as grav_cfg
from symbolic_system.gravity.engines.residual_gravity_engine import GravityEngineConfig

try:
    from diagnostics.shadow_model_monitor import ShadowModelMonitor
except ImportError:
    ShadowModelMonitor = None
    # Now log_info is guaranteed to be defined here
    log_info("Warning: ShadowModelMonitor could not be imported for batch_runner.")

from engine.simulator_core import simulate_forward
from engine.worldstate import (
    WorldState,
    SymbolicOverlays,
)  # Ensure SymbolicOverlays is imported
from forecast_output.forecast_generator import generate_forecast
from analytics.forecast_pipeline_runner import run_forecast_pipeline


DEFAULT_BATCH_OUTPUT = PATHS.get("BATCH_OUTPUT", "logs/batch_output.jsonl")


def load_batch_config(path: str) -> List[Dict[str, Any]]:
    """Load a batch configuration from a JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def run_batch_from_config(
    configs: List[Dict[str, Any]],
    export_path: Optional[str] = None,
    learning_engine=None,
    gravity_enabled: bool = True,  # Added gravity_enabled parameter
    gravity_config: Optional[
        GravityEngineConfig
    ] = None,  # Added gravity_config parameter
) -> List[Dict[str, Any]]:
    """
    Executes a batch of simulation configs.

    Args:
        configs (List[Dict]): Simulation configurations
        export_path (str): Optional output path for saving results
        learning_engine: Optional LearningEngine instance for hooks
        gravity_enabled (bool): Whether gravity correction is enabled (default: True)
        gravity_config (GravityEngineConfig, optional): Configuration for the gravity engine

    Returns:
        List[Dict]: Pipeline results per config, including error info if failed.
    """
    results = []

    shadow_monitor = None  # Removed type hint to fix Pylance error
    if (
        ShadowModelMonitor
        and SHADOW_MONITOR_CONFIG
        and SHADOW_MONITOR_CONFIG.get("enabled", False)
    ):
        try:
            shadow_monitor = ShadowModelMonitor(
                threshold=SHADOW_MONITOR_CONFIG["threshold_variance_explained"],
                window_steps=SHADOW_MONITOR_CONFIG["window_steps"],
                critical_variables=SHADOW_MONITOR_CONFIG["critical_variables"],
            )
            log_info("[BATCH] ShadowModelMonitor enabled and initialized.")
        except KeyError as e:
            log_info(
                f"[BATCH] Error initializing ShadowModelMonitor from config: Missing key {e}. Monitor disabled."
            )
            shadow_monitor = None
        except Exception as e:
            log_info(
                f"[BATCH] Error initializing ShadowModelMonitor: {e}. Monitor disabled."
            )
            shadow_monitor = None
    else:
        log_info("[BATCH] ShadowModelMonitor is disabled or not configured.")

    for i, cfg in enumerate(configs):
        try:
            log_info(f"[BATCH] Running batch {i + 1}/{len(configs)}")
            state = WorldState()  # Initialize WorldState

            # Initialize or update overlays
            state_overrides = cfg.get("state_overrides", {})
            if state_overrides:
                if not hasattr(state, "overlays") or not isinstance(
                    state.overlays, SymbolicOverlays
                ):
                    state.overlays = SymbolicOverlays.from_dict(state_overrides)
                else:  # It is a SymbolicOverlays instance, update it
                    current_overlays_dict = (
                        state.overlays.as_dict()
                        if hasattr(state.overlays, "as_dict")
                        else {}
                    )
                    current_overlays_dict.update(state_overrides)
                    state.overlays = SymbolicOverlays.from_dict(current_overlays_dict)
            elif not hasattr(state, "overlays") or state.overlays is None:
                state.overlays = SymbolicOverlays.from_dict({})

            num_turns = cfg.get("turns", 1)
            simulation_results = simulate_forward(
                state=state,
                turns=num_turns,
                use_symbolism=cfg.get("use_symbolism", True),
                return_mode="full",  # Shadow monitor needs detailed state
                logger=log_info,
                learning_engine=learning_engine,
                shadow_monitor_instance=shadow_monitor,
                gravity_enabled=gravity_enabled,  # Pass the gravity_enabled parameter
                gravity_config=gravity_config,  # Pass the gravity_config parameter
            )

            final_state_snapshot = {}
            if simulation_results:
                final_state_data = simulation_results[-1].get("full_state")
                if final_state_data and isinstance(final_state_data, dict):
                    final_state_snapshot = final_state_data
                else:
                    log_info(
                        "[BATCH] Warning: 'full_state' not found or not a dict in last sim step. Using current WorldState."
                    )
                    final_state_snapshot = (
                        state.to_dict() if hasattr(state, "to_dict") else vars(state)
                    )
            else:
                log_info(
                    "[BATCH] Warning: Simulation produced no results. Using initial state for forecast."
                )
                final_state_snapshot = (
                    state.to_dict() if hasattr(state, "to_dict") else vars(state)
                )

            forecasts = generate_forecast(final_state_snapshot)

            if isinstance(forecasts, dict):  # Ensure forecasts is a list for pipeline
                forecasts = [forecasts]
            pipeline_result_data = run_forecast_pipeline(forecasts)
            pipeline_result_data["config"] = cfg
            pipeline_result_data["batch_index"] = i
            results.append(pipeline_result_data)

        except Exception as e:
            tb = traceback.format_exc()
            log_info(f"[BATCH] Error on batch {i + 1}: {type(e).__name__}: {e}\n{tb}")
            results.append(
                {
                    "config": cfg,
                    "batch_index": i,
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e),
                        "traceback": tb,
                    },
                }
            )

    if export_path:
        try:
            # Write to a temp file and move atomically
            temp_dir = os.path.dirname(export_path)
            if not temp_dir:  # Handle case where export_path is just a filename
                temp_dir = "."
            os.makedirs(temp_dir, exist_ok=True)  # Ensure directory exists

            with tempfile.NamedTemporaryFile(
                "w", delete=False, dir=temp_dir, encoding="utf-8"
            ) as tf:
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
    # Existing gravity flag
    parser.add_argument(
        "--gravity-off",
        action="store_true",
        help="Disable gravity correction during simulation (equivalent to --enable-residual-gravity=False).",
    )

    # New ResidualGravityEngine CLI flags
    parser.add_argument(
        "--enable-residual-gravity",
        action="store_true",
        help="Enable the residual gravity overlay system (overrides --gravity-off).",
    )
    parser.add_argument(
        "--gravity-disable-adaptive-lambda",
        action="store_false",
        dest="gravity_enable_adaptive_lambda",
        default=None,
        help=f"Disable adaptive lambda adjustment in the gravity engine (default: {grav_cfg.DEFAULT_ENABLE_ADAPTIVE_LAMBDA}).",
    )
    parser.add_argument(
        "--gravity-disable-weight-pruning",
        action="store_false",
        dest="gravity_enable_weight_pruning",
        default=None,
        help=f"Disable weight pruning in the gravity engine (default: {grav_cfg.DEFAULT_ENABLE_WEIGHT_PRUNING}).",
    )
    parser.add_argument(
        "--gravity-disable-shadow-model-trigger",
        action="store_false",
        dest="gravity_enable_shadow_model_trigger",
        default=None,
        help=f"Disable shadow model trigger in the gravity engine (default: {grav_cfg.DEFAULT_ENABLE_SHADOW_MODEL_TRIGGER}).",
    )
    parser.add_argument(
        "--gravity-lambda",
        type=float,
        default=None,
        help=f"Set initial lambda value for gravity strength (default: {grav_cfg.DEFAULT_LAMBDA}).",
    )
    parser.add_argument(
        "--gravity-learning-rate",
        type=float,
        default=None,
        help=f"Set learning rate for gravity engine (default: {grav_cfg.DEFAULT_LEARNING_RATE}).",
    )
    parser.add_argument(
        "--gravity-ewma-span",
        type=float,
        default=None,
        help=f"Set EWMA span for gravity engine (default: {grav_cfg.DEFAULT_EWMA_SPAN}).",
    )
    parser.add_argument(
        "--gravity-adaptive-lambda-min",
        type=float,
        default=None,
        help=f"Set minimum lambda for adaptive adjustment (default: {grav_cfg.DEFAULT_ADAPTIVE_LAMBDA_MIN}).",
    )
    parser.add_argument(
        "--gravity-adaptive-lambda-max",
        type=float,
        default=None,
        help=f"Set maximum lambda for adaptive adjustment (default: {grav_cfg.DEFAULT_ADAPTIVE_LAMBDA_MAX}).",
    )
    parser.add_argument(
        "--gravity-shadow-variance-threshold",
        type=float,
        default=None,
        help=f"Set variance threshold for shadow model trigger (default: {grav_cfg.DEFAULT_SHADOW_MODEL_VARIANCE_THRESHOLD}).",
    )

    # TODO: Add CLI/config file support for batch execution.
    # For now, using sample configs
    args = parser.parse_args()

    sample_configs_main = [
        {"state_overrides": {"hope": 0.6, "despair": 0.2}, "turns": 1},
        {"state_overrides": {"hope": 0.3, "despair": 0.5}, "turns": 1},
    ]

    # Determine whether gravity is enabled based on flags
    # --enable-residual-gravity overrides --gravity-off
    gravity_enabled = True
    if args.gravity_off and not args.enable_residual_gravity:
        gravity_enabled = False

    # Create a configuration object for the gravity engine if any gravity parameters are specified
    gravity_config = None
    if any(
        getattr(args, param) is not None
        for param in [
            "gravity_enable_adaptive_lambda",
            "gravity_enable_weight_pruning",
            "gravity_enable_shadow_model_trigger",
            "gravity_lambda",
            "gravity_learning_rate",
            "gravity_ewma_span",
            "gravity_adaptive_lambda_min",
            "gravity_adaptive_lambda_max",
            "gravity_shadow_variance_threshold",
        ]
    ):
        # Create config with CLI arguments
        gravity_config = GravityEngineConfig(
            lambda_=args.gravity_lambda,
            learning_rate=args.gravity_learning_rate,
            ewma_span=args.gravity_ewma_span,
            enable_adaptive_lambda=args.gravity_enable_adaptive_lambda,
            enable_weight_pruning=args.gravity_enable_weight_pruning,
            adaptive_lambda_min=args.gravity_adaptive_lambda_min,
            adaptive_lambda_max=args.gravity_adaptive_lambda_max,
        )

        # Set shadow model trigger parameters
        if args.gravity_enable_shadow_model_trigger is not None:
            gravity_config.enable_shadow_model_trigger = (
                args.gravity_enable_shadow_model_trigger
            )
        if args.gravity_shadow_variance_threshold is not None:
            gravity_config.shadow_model_variance_threshold = (
                args.gravity_shadow_variance_threshold
            )

    # Pass the gravity_enabled flag and gravity_config to the runner function
    run_batch_from_config(
        sample_configs_main,
        export_path=str(DEFAULT_BATCH_OUTPUT),
        gravity_enabled=gravity_enabled,
        gravity_config=gravity_config,
    )
