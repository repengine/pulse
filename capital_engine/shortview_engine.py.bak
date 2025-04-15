"""
shortview_engine.py

Runs short-term capital forecast simulations (1–7 day horizon) using symbolic overlays
to drive exposure logic via asset_forks. Intended to produce structured outputs for
confidence scoring and tile formatting.

Author: Pulse v3.5
"""

from worldstate import WorldState
from asset_forks import run_capital_forks
from symbolic_utils import symbolic_fragility_index
from typing import Dict, Any


def run_shortview_forecast(
    state: WorldState,
    asset_subset: list = None,
    duration_days: int = 2
) -> Dict[str, Any]:
    """
    Runs a short-horizon (1–7 day) forecast simulation.

    Parameters:
        state (WorldState): current simulation state
        asset_subset (list): which assets to forecast (default = all)
        duration_days (int): time horizon (1–7 days)

    Returns:
        Dict: forecast summary including asset exposure changes, symbolic fragility, and tags
    """
    if duration_days < 1 or duration_days > 7:
        raise ValueError("ShortView duration must be between 1 and 7 days.")

    start_snapshot = state.snapshot()
    run_capital_forks(state, assets=asset_subset)
    end_snapshot = state.snapshot()

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
        "confidence": None  # PFPA scoring will plug in here later
    }

    state.log_event(f"[SHORTVIEW] Forecast run for {duration_days} days. Fragility: {forecast['symbolic_fragility']:.3f}")

    return forecast
