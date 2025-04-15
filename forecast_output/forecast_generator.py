"""
forecast_generator.py

Creates a structured foresight object by combining symbolic overlays, capital forks,
and alignment tagging. This forms the core output of each shortview simulation cycle.

Author: Pulse v3.5
"""

from simulation_engine.worldstate import WorldState
from capital_engine.shortview_engine import run_shortview_forecast
from capital_engine.portfolio_state import summarize_exposure, portfolio_alignment_tags
from symbolic_system.symbolic_utils import symbolic_fragility_index
from typing import Dict, Any


def generate_forecast(
    state: WorldState,
    assets: list = None,
    horizon_days: int = 2
) -> Dict[str, Any]:
    """
    Generates a full forecast record.

    Parameters:
        state (WorldState): active simulation state
        assets (list): list of assets to simulate forks for
        horizon_days (int): forecast time window (1–7)

    Returns:
        Dict[str, Any]: full structured forecast object
    """
    forecast = run_shortview_forecast(
        state,
        asset_subset=assets,
        duration_days=horizon_days
    )

    output = {
        "horizon_days": horizon_days,
        "forecast": forecast,
        "fragility": forecast["symbolic_fragility"],
        "exposure": summarize_exposure(state),
        "alignment": portfolio_alignment_tags(state),
        "confidence": None,  # placeholder for trust scoring
        "trace_id": f"fcast_turn_{state.turn}",
        "origin_turn": state.turn,
        "status": "pending-eval"
    }

    state.log_event(
        f"[FORECAST] Foresight generated. Turn: {state.turn} | Horizon: {horizon_days}d"
    )

    return output
