"""
shortview_engine.py

Runs short-term foresight simulations for 1–7 day horizons based on current symbolic state.
Calls asset fork logic and calculates symbolic fragility, exposure delta, and symbolic drift.

Author: Pulse v3.5
"""

from simulation_engine.worldstate import WorldState
from capital_engine.asset_forks import run_capital_forks
from symbolic_system.symbolic_utils import symbolic_fragility_index
from typing import Dict, Any, List


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
        duration_days (int): time horizon for the forecast (1–7 days typical)

    Returns:
        Dict[str, Any]: forecast metadata including symbolic drift, exposure delta, and fragility index
    """
    if duration_days < 1 or duration_days > 7:
        raise ValueError("ShortView duration must be between 1 and 7 days.")

    start_snapshot = state.snapshot()

    # Simulate fork logic (symbolic → capital)
    run_capital_forks(state, assets=asset_subset)

    end_snapshot = state.snapshot()

    # Compile forecast metadata
    forecast = {
        "duration_days": duration_days,
        "symbolic_fragility": symbolic_fragility_index(state),
        "start_capital": start_snapshot["capital"],
        "end_capital": end_snapshot["capital"],
        "symbolic_change": {
            overlay: round(end_snapshot["overlays"][overlay] - start_snapshot["overlays"][overlay], 3)
            for overlay in start_snapshot["overlays"]
        },
        "tags": [],
        "confidence": None  # to be scored later
    }

    state.log_event(
        f"[SHORTVIEW] Forecast run for {duration_days} days. Fragility: {forecast['symbolic_fragility']:.3f}"
    )

    return forecast
