"""
diagnose_pulse.py

Runs basic diagnostic checks on core Pulse components to ensure system health,
symbolic consistency, and capital exposure validity before simulation export.

Author: Pulse v3.5
"""

from worldstate import WorldState
from portfolio_state import summarize_exposure, exposure_percentages
from symbolic_utils import get_overlay_snapshot, symbolic_fragility_index
from typing import Dict


def run_diagnostics() -> Dict[str, any]:
    """
    Runs core system diagnostics and returns a summary report.

    Returns:
        Dict: diagnostic report containing key symbolic and capital values
    """
    report = {}
    state = WorldState()

    report["turn"] = state.turn
    report["symbolic_overlays"] = get_overlay_snapshot(state)
    report["symbolic_fragility"] = symbolic_fragility_index(state)
    report["capital_exposure"] = summarize_exposure(state)
    report["capital_percentages"] = exposure_percentages(state)

    print("\n📋 PULSE SYSTEM DIAGNOSTICS\n")
    print(f"Turn: {report['turn']}")
    print("\nSymbolic Overlays:")
    for k, v in report["symbolic_overlays"].items():
        print(f"  {k.capitalize():<8}: {v:.3f}")

    print(f"\nSymbolic Fragility Index: {report['symbolic_fragility']:.3f}")

    print("\nCapital Exposure:")
    for asset, val in report["capital_exposure"].items():
        print(f"  {asset.upper():<5} : ${val:,.2f}")

    print("\nExposure % Breakdown:")
    for asset, pct in report["capital_percentages"].items():
        print(f"  {asset.upper():<5} : {pct*100:.2f}%")

    return report


if __name__ == "__main__":
    run_diagnostics()
