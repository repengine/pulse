"""
plia_stub.py

PLIA = Pulse Logic Integrity Audit (Stub Mode)
This lightweight diagnostic checks symbolic tension and capital deployment for coherence.

Author: Pulse v3.5
"""

from simulation_engine.worldstate import WorldState
from symbolic_system.symbolic_utils import get_overlay_snapshot, symbolic_tension_score
from capital_engine.capital_layer import total_exposure
from typing import Dict, Any
from utils.log_utils import get_logger

logger = get_logger(__name__)

# Diagnostics enabled flag (can be toggled at runtime)
DIAGNOSTICS_ENABLED = True


def set_diagnostics_enabled(enabled: bool):
    """
    Enable or disable PLIA diagnostics dynamically.
    """
    global DIAGNOSTICS_ENABLED
    DIAGNOSTICS_ENABLED = enabled


def run_plia_stub(state: WorldState) -> Dict[str, Any]:
    """
    Basic integrity snapshot for symbolic overlays and capital totals.

    Parameters:
        state (WorldState): active WorldState instance

    Returns:
        Dict[str, any]: audit results
    """
    if not DIAGNOSTICS_ENABLED:
        logger.info("PLIA diagnostics are currently disabled.")
        return {"status": "disabled"}
    symbolic_state = get_overlay_snapshot(state)
    symbolic_tension = symbolic_tension_score(symbolic_state)
    capital_total = total_exposure(state)

    results = {
        "symbolic_tension": symbolic_tension,
        "capital_deployed": capital_total,
        "symbolic_overlays": symbolic_state,
        "status": "pass (stub mode)",
    }

    logger.info("\n🧠 [PLIA STUB] Logic Integrity Check:")
    logger.info(f"Symbolic Tension Score : {symbolic_tension:.3f}")
    logger.info(f"Total Capital Deployed: ${capital_total:,.2f}")
    logger.info(f"Overlay Snapshot       : {symbolic_state}")

    return results


def test_plia_stub():
    """
    Test function for PLIA stub diagnostics.
    """
    from simulation_engine.worldstate import WorldState

    set_diagnostics_enabled(True)
    result = run_plia_stub(WorldState())
    assert result["status"].startswith("pass")
    set_diagnostics_enabled(False)
    result = run_plia_stub(WorldState())
    assert result["status"] == "disabled"
    logger.info("test_plia_stub passed.")


if __name__ == "__main__":
    test_plia_stub()
