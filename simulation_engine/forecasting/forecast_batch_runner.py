""" 
forecast_batch_runner.py

Batch processor for Pulse forecasts.
Each forecast is:
- Simulated
- Scored and validated
- Saved if trusted
- Archived to memory
- Logged with reasons if rejected

Includes CLI usage and JSON export of run results.

Author: Pulse v0.10
"""

import os
import json
import argparse
from datetime import datetime
from simulation_engine.worldstate import WorldState
from simulation_engine.turn_engine import run_turn
from simulation_engine.forecasting.forecast_tracker import ForecastTracker
from simulation_engine.forecasting.forecast_scoring import score_forecast
from simulation_engine.forecasting.forecast_integrity_engine import validate_forecast
from simulation_engine.forecasting.forecast_memory import save_forecast_to_memory
from utils.log_utils import get_logger
from core.path_registry import PATHS
from core.pulse_config import CONFIDENCE_THRESHOLD
from core.module_registry import MODULE_REGISTRY

logger = get_logger(__name__)

SUMMARY_PATH = PATHS["BATCH_FORECAST_SUMMARY"]


def run_batch_forecasts(count=5, domain="capital", min_conf=None, symbolic_block=None, verbose=True, export_summary=True):
    """
    Runs batch of forecast simulations and outputs results.

    Args:
        count (int): Number of forecasts to simulate
        domain (str): Domain tag
        min_conf (float): Minimum confidence to accept forecast
        symbolic_block (list): Symbolic drivers to auto-reject
        verbose (bool): Print status
        export_summary (bool): Write summary to disk
    """
    min_conf = min_conf if min_conf is not None else CONFIDENCE_THRESHOLD
    if not MODULE_REGISTRY.get("forecast_batch_runner", {}).get("enabled", True):
        logger.warning("Forecast batch runner is disabled in module registry.")
        return

    tracker = ForecastTracker()
    accepted = 0
    rejected = 0
    logs = []

    for i in range(count):
        state = WorldState()
        rule_log = run_turn(state)
        metadata = score_forecast(state, rule_log)
        forecast_id = f"{domain}_forecast_{i+1}"

        valid = validate_forecast(
            metadata,
            min_conf=min_conf,
            blocked_tags=symbolic_block,
            required_keys=["confidence", "symbolic_driver"]
        )

        if valid:
            tracker.record_forecast(forecast_id, state, rule_log, domain=domain)
            accepted += 1
            logs.append({"forecast_id": forecast_id, "status": "accepted", "metadata": metadata})
        else:
            rejected += 1
            reason = "low_confidence" if metadata.get("confidence", 0) < min_conf else "blocked_symbolic"
            logs.append({"forecast_id": forecast_id, "status": "rejected", "reason": reason, "metadata": metadata})
            if verbose:
                print(f"⛔ Rejected [{forecast_id}] ({reason}) | Metadata: {metadata}")

    if export_summary:
        os.makedirs(os.path.dirname(SUMMARY_PATH), exist_ok=True)
        with open(SUMMARY_PATH, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "domain": domain,
                "requested": count,
                "accepted": accepted,
                "rejected": rejected,
                "logs": logs
            }, f, indent=2)

        print(f"📝 Batch summary written to {SUMMARY_PATH}")

    print(f"✅ Batch complete: {accepted} accepted / {count} total")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pulse Batch Forecast Runner")
    parser.add_argument("--count", type=int, default=5, help="Number of forecasts to run")
    parser.add_argument("--domain", type=str, default="capital", help="Forecast domain tag")
    parser.add_argument("--min_conf", type=float, default=0.5, help="Minimum required confidence")
    parser.add_argument("--block", nargs='*', default=None, help="Symbolic drivers to block (e.g. despair)")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    args = parser.parse_args()

    run_batch_forecasts(
        count=args.count,
        domain=args.domain,
        min_conf=args.min_conf,
        symbolic_block=args.block,
        verbose=not args.quiet
    )