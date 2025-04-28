"""
main.py

Pulse v0.2 execution shell. Initializes simulation state, runs a short simulation loop,
generates foresight forecasts, and prints Strategos Digest summaries.

Author: Pulse v0.2

Usage:
    python main.py [--turns N] [--output FILE]

Options:
    --turns N   Number of simulation turns to run (default: 5)
    --output FILE   Optional output file for digest
"""
import sys
import os
import argparse
from datetime import datetime, timezone
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.log_utils import get_logger
logger = get_logger(__name__)

logger.info("🧠 Starting Pulse...")

from core.pulse_config import STARTUP_BANNER

print(STARTUP_BANNER)

from forecast_output.digest_logger import save_digest_to_file
from operator_interface.strategos_digest import generate_strategos_digest
from memory.forecast_memory import ForecastMemory
from simulation_engine.worldstate import WorldState
from simulation_engine.turn_engine import run_turn
from simulation_engine.causal_rules import apply_causal_rules
from forecast_output.forecast_generator import generate_forecast
from forecast_output.pfpa_logger import log_forecast_to_pfpa
from forecast_output.digest_exporter import export_digest, export_digest_json
from forecast_output.strategos_digest_builder import build_digest
from operator_interface.pulse_prompt_logger import log_prompt
from forecast_engine.forecast_regret_engine import analyze_regret, analyze_misses, feedback_loop
from core.pulse_learning_log import log_learning_event

def run_pulse_simulation(turns: int = 5):
    """
    Run the main Pulse simulation loop.

    Args:
        turns (int): Number of simulation turns to execute.
    """
    logger.info("\n🌐 Initializing Pulse...\n")
    state = WorldState()
    memory = ForecastMemory()

    for _ in range(turns):
        logger.info(f"\n🔄 Running Turn {state.turn + 1}...")
        # Use a lambda that returns None to satisfy the type
        run_turn(state, rule_fn=lambda s: (apply_causal_rules(s), None)[1])
        try:
            # Always pass a dict to generate_forecast
            forecast = generate_forecast(state.to_dict())
            memory.store(forecast)
            log_forecast_to_pfpa(forecast)
        except Exception as e:
            logger.error(f"❌ Forecast error: {e}")
            log_learning_event("exception", {"error": str(e), "context": "forecast_generation", "timestamp": datetime.now(timezone.utc).isoformat()})
            continue

    digest = generate_strategos_digest(memory, n=min(turns, 5))
    logger.info(digest)
    save_digest_to_file(digest)

# Run post-simulation retrodiction test
try:
    from trust_system.retrodiction_engine import simulate_retrodiction_test
    simulate_retrodiction_test()
    log_learning_event("forecast_scored", {"forecast_id": "retrodiction_test", "score": "success", "timestamp": datetime.now(timezone.utc).isoformat()})
except Exception as e:
    logger.warning(f"⚠️ Retrodiction failed: {e}")
    log_learning_event("exception", {"error": str(e), "context": "retrodiction_test", "timestamp": datetime.now(timezone.utc).isoformat()})
# Strategic trust audit
try:
    from learning.trust_audit import audit_forecasts
    audit_forecasts()
    log_learning_event("symbolic_contradiction", {"details": "audit_success", "timestamp": datetime.now(timezone.utc).isoformat()})
except Exception as e:
    logger.warning(f"⚠️ Audit failed: {e}")
    log_learning_event("exception", {"error": str(e), "context": "trust_audit", "timestamp": datetime.now(timezone.utc).isoformat()})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pulse Simulation Engine")
    parser.add_argument("--turns", type=int, default=5, help="Number of simulation turns to run")
    parser.add_argument("--output", type=str, default=None, help="Optional output file for digest")
    parser.add_argument("--auto-upgrade", action="store_true", help="Automatically generate epistemic upgrade plan after run")
    args = parser.parse_args()
    run_pulse_simulation(turns=args.turns)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("# Strategos Digest\n\n")
                f.write(str(generate_strategos_digest(ForecastMemory(), n=min(args.turns, 5))))
            logger.info(f"Digest exported to {args.output}")
        except Exception as e:
            logger.error(f"Failed to export digest: {e}")
            log_learning_event("exception", {"error": str(e), "context": "digest_export", "timestamp": datetime.now(timezone.utc).isoformat()})
    # --- Epistemic Mirror Curriculum Learning ---
    if getattr(args, "auto_upgrade", False):
        try:
            import subprocess
            upgrade_path = "plans/epistemic_upgrade_plan.json"
            batch_path = "logs/strategic_batch_output.jsonl"
            revised_path = "logs/revised_forecasts.jsonl"
            # Step 1: Generate upgrade plan
            subprocess.run([
                sys.executable, "dev_tools/propose_epistemic_upgrades.py", "--output", upgrade_path
            ], check=True)
            logger.info(f"Epistemic upgrade plan generated at {upgrade_path}")
            # Step 2: Apply upgrade plan to latest batch
            if os.path.exists(batch_path) and os.path.exists(upgrade_path):
                subprocess.run([
                    sys.executable, "dev_tools/apply_symbolic_upgrades.py",
                    "--batch", batch_path, "--plan", upgrade_path, "--out", revised_path
                ], check=True)
                logger.info(f"Applied epistemic upgrade plan to {batch_path}, output: {revised_path}")
            else:
                logger.warning(f"Batch or upgrade plan not found for application: {batch_path}, {upgrade_path}")
        except Exception as e:
            logger.error(f"Failed to generate/apply epistemic upgrade plan: {e}")