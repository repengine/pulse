"""
main.py

Pulse v0.2 execution shell. Initializes simulation state, runs a short simulation loop,
generates foresight forecasts, and prints Strategos Digest summaries.

Author: Pulse v0.2
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.log_utils import get_logger
logger = get_logger(__name__)

logger.info("🧠 Starting Pulse...")

from core.module_registry import MODULE_REGISTRY
from core.pulse_config import STARTUP_BANNER

print(STARTUP_BANNER)
print(f"Pulse version: {MODULE_REGISTRY['turn_engine']['version']}")

from foresight_architecture.digest_logger import save_digest_to_file
from operator_interface.strategos_digest import generate_strategos_digest
from memory.forecast_memory import ForecastMemory
from simulation_engine.worldstate import WorldState
from simulation_engine.turn_engine import run_turn
from simulation_engine.causal_rules import apply_causal_rules
from forecast_output.forecast_generator import generate_forecast
from forecast_output.pfpa_logger import log_forecast_to_pfpa
from foresight_architecture.digest_exporter import export_digest, export_digest_json
from forecast_output.strategos_digest_builder import build_digest
from operator_interface.pulse_prompt_logger import log_prompt


def run_pulse_simulation(turns: int = 5):
    logger.info("\n🌐 Initializing Pulse...\n")
    state = WorldState()
    memory = ForecastMemory()

    for _ in range(turns):
        logger.info(f"\n🔄 Running Turn {state.turn + 1}...")
        run_turn(state, rule_fn=apply_causal_rules)
        try:
            forecast = generate_forecast(state)
            memory.store(forecast)
            log_forecast_to_pfpa(forecast)
        except Exception as e:
            logger.error(f"❌ Forecast error: {e}")
            continue

    digest = generate_strategos_digest(memory, n=min(turns, 5))
    logger.info(digest)
    save_digest_to_file(digest)

# Run post-simulation retrodiction test
try:
    from retrodiction_engine import simulate_retrodiction_test
    simulate_retrodiction_test()
except Exception as e:
    logger.warning(f"⚠️ Retrodiction failed: {e}")
# Strategic trust audit
try:
    from trust_audit import audit_forecasts
    audit_forecasts()
except Exception as e:
    logger.warning(f"⚠️ Audit failed: {e}")

if __name__ == "__main__":
    run_pulse_simulation(turns=5)
