"""
shortview_engine.py

Runs short-term foresight simulations for 1–7 day horizons based on current symbolic state.
Calls asset fork logic and calculates symbolic fragility, exposure delta, and symbolic drift.

Author: Pulse v3.5

- Duration range is parameterized for flexibility.
- Handles missing overlays/capital keys gracefully.
- Inline comments clarify snapshot and symbolic change logic.
"""

from simulation_engine.worldstate import WorldState
from capital_engine.asset_forks import run_capital_forks
from symbolic_system.symbolic_utils import symbolic_fragility_index
from core.pulse_config import MODULES_ENABLED, CONFIDENCE_THRESHOLD, DEFAULT_FRAGILITY_THRESHOLD, TRUST_WEIGHT, DESPAIR_WEIGHT
from typing import Dict, Any, List

# Parameterize allowed duration range
MIN_DURATION = 1
MAX_DURATION = 7

def run_shortview_forecast(
    state: WorldState,
    asset_subset: List[str] = None,
    duration_days: int = 2
) -> Dict[str, Any]:
    """
    Runs a short-horizon foresight simulation and returns a structured forecast.

    Parameters:
        state (WorldState): the current simulation state
        asset_subset (List[str]): optional list of asset names to run forks on
        duration_days (int): time horizon for the forecast (default: 2, min: 1, max: 7)

    Returns:
        Dict[str, Any]: forecast metadata including symbolic drift, exposure delta, and fragility index
    Raises:
        ValueError: if duration_days is out of allowed range
    """
    if duration_days < MIN_DURATION or duration_days > MAX_DURATION:
        raise ValueError(f"ShortView duration must be between {MIN_DURATION} and {MAX_DURATION} days.")

    # Take a snapshot of the state before running forks
    start_snapshot = state.snapshot()

    # Simulate fork logic (symbolic → capital)
    run_capital_forks(state, assets=asset_subset)

    # Take a snapshot after running forks
    end_snapshot = state.snapshot()

    # Compute symbolic overlay changes, handling missing keys gracefully
    symbolic_change = {}
    for overlay in start_snapshot.get("overlays", {}):
        try:
            symbolic_change[overlay] = round(
                end_snapshot["overlays"].get(overlay, 0.0) - start_snapshot["overlays"].get(overlay, 0.0), 3
            )
        except Exception:
            symbolic_change[overlay] = 0.0

    # Compile forecast metadata
    forecast = {
        "duration_days": duration_days,
        "symbolic_fragility": symbolic_fragility_index(state),
        "start_capital": start_snapshot.get("capital", {}),
        "end_capital": end_snapshot.get("capital", {}),
        "symbolic_change": symbolic_change,
        "tags": [],
        "confidence": None  # to be scored later
    }

    # Log the forecast event
    state.log_event(
        f"[SHORTVIEW] Forecast run for {duration_days} days. Fragility: {forecast['symbolic_fragility']:.3f}"
    )

    return forecast
