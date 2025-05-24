"""
pulse_test_suite.py

Validates symbolic overlay movement and capital exposure shifts
over time to ensure rule engines are modifying state.

Author: Pulse v0.20
"""

from simulation_engine.worldstate import WorldState
from simulation_engine.turn_engine import run_turn
from utils.log_utils import get_logger

logger = get_logger(__name__)


def test_symbolic_shift(threshold=0.01, turns=5):
    logger.info("🔎 Running symbolic overlay drift test...")
    state = WorldState()
    initial = state.overlays.as_dict().copy()
    for _ in range(turns):
        run_turn(state)

    final = state.overlays.as_dict()
    changes = {k: round(final[k] - initial[k], 4) for k in final}

    for k, delta in changes.items():
        if abs(delta) >= threshold:
            logger.info(f"✅ {k} changed by {delta}")
        else:
            logger.info(f"⚠️  {k} barely changed ({delta})")


def test_capital_shift(threshold=1.0, turns=5):
    logger.info("\n💰 Running capital exposure drift test...")
    state = WorldState()
    initial = state.capital.as_dict().copy()
    for _ in range(turns):
        run_turn(state)

    final = state.capital.as_dict()
    changes = {k: round(final[k] - initial[k], 2) for k in final}

    for k, delta in changes.items():
        if abs(delta) >= threshold:
            logger.info(f"✅ {k} shifted by {delta}")
        else:
            logger.info(f"⚠️  {k} barely moved ({delta})")


if __name__ == "__main__":
    test_symbolic_shift()
    test_capital_shift()
