"""
forecast_generator.py

Generates a structured forecast object by simulating short-term changes in symbolic and capital state.
Acts as the core foresight engine at the interface of symbolic overlays and capital forks.

Author: Pulse v3.5
"""

from worldstate import WorldState
from shortview_engine import run_shortview_forecast
from portfolio_state import summarize_exposure, portfolio_alignment_tags
from symbolic_utils import symbolic_fragility_index
from typing import Dict, Any


def generate_forecast(
    state: WorldState,
    assets: list = None,
    horizon_days: int = 2,
) -> Dict[str, Any]:
    """
    Produces a single foresight forecast object.

    Parameters:
        state (WorldState): the current simulation state
        assets (list): assets to include in fork logic
        horizon_days (int): number of days to simulate (1–7 typical)

    Returns:
        Dict: structured foresight forecast
    """
    forecast = run_shortview_forecast(state, asset_subset=assets, duration_days=horizon_days)

    output = {
        "horizon_days": horizon_days,
        "forecast": forecast,
        "fragility": forecast["symbolic_fragility"],
        "exposure": summarize_exposure(state),
        "alignment": portfolio_alignment_tags(state),
        "confidence": None,  # Placeholder for PFPA or signal-informed scoring
        "trace_id": f"fcast_turn_{state.turn}",
        "origin_turn": state.turn,
        "status": "pending-eval"
    }

    state.log_event(f"[FORECAST] Foresight generated. Turn: {state.turn} | Horizon: {horizon_days}d")

    return output
