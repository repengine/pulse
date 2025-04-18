"""
diagnose_pulse.py

Prints a diagnostic summary of symbolic overlays, fragility score, and capital exposure state.
Useful for validating Pulse readiness and simulation stability.

Author: Pulse v3.5
"""

from simulation_engine.worldstate import WorldState
from symbolic_system.symbolic_utils import get_overlay_snapshot, symbolic_fragility_index
from capital_engine.portfolio_state import summarize_exposure, exposure_percentages
from typing import Dict
from utils.log_utils import get_logger

logger = get_logger(__name__)


def run_diagnostics() -> Dict[str, any]:
    """
    Performs basic symbolic and capital diagnostic checks.

    Returns:
        Dict[str, any]: summary of key simulation state
    """
    report = {}
    state = WorldState()

    report["turn"] = state.turn
    report["symbolic_overlays"] = get_overlay_snapshot(state)
    report["symbolic_fragility"] = symbolic_fragility_index(state)
    report["capital_exposure"] = summarize_exposure(state)
    report["capital_percentages"] = exposure_percentages(state)

    logger.info("\n📋 PULSE SYSTEM DIAGNOSTICS\n")
    logger.info(f"Turn: {report['turn']}")

    logger.info("\nSymbolic Overlays:")
    for k, v in report["symbolic_overlays"].items():
        logger.info(f"  {k.capitalize():<8}: {v:.3f}")

    logger.info(f"\nSymbolic Fragility Index: {report['symbolic_fragility']:.3f}")

    logger.info("\nCapital Exposure:")
    for asset, val in report["capital_exposure"].items():
        logger.info(f"  {asset.upper():<5} : ${val:,.2f}")

    logger.info("\nExposure % Breakdown:")
    for asset, pct in report["capital_percentages"].items():
        logger.info(f"  {asset.upper():<5} : {pct*100:.2f}%")

    return report


if __name__ == "__main__":
    result = run_diagnostics()
    logger.info(result)
