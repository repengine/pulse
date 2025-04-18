"""
forecast_generator.py

Creates a structured foresight object by combining symbolic overlays, capital forks,
and alignment tagging. This forms the core output of each shortview simulation cycle.

Author: Pulse v3.5
"""

from forecast_output.forecast_age_tracker import attach_timestamp
from simulation_engine.worldstate import WorldState
from capital_engine.shortview_engine import run_shortview_forecast
from capital_engine.portfolio_state import summarize_exposure, portfolio_alignment_tags
from trust_system.trust_engine import score_forecast
from symbolic_system.symbolic_utils import symbolic_fragility_index
from typing import Dict, Any
from utils.log_utils import get_logger

logger = get_logger(__name__)

def generate_forecast(
    state: WorldState,
    assets: list = None,
    horizon_days: int = 2
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
    try:
        forecast = run_shortview_forecast(state, asset_subset=assets, duration_days=horizon_days)
    except Exception as e:
        logger.error(f"[ERROR] Forecast engine failed: {e}")
        return {}

    output = {
        "horizon_days": horizon_days,
        "forecast": forecast,
        "fragility": forecast["symbolic_fragility"],
        "exposure": summarize_exposure(state),
        "alignment": portfolio_alignment_tags(state),
        "confidence": None,
        "trace_id": f"fcast_turn_{state.turn}",
        "origin_turn": state.turn,
        "status": "experimental"
    }

    # 🔐 Add trust score + status label
    output["confidence"] = score_forecast(output)

    if output["confidence"] >= 0.75:
        output["status"] = "🟢 Trusted"
    elif output["confidence"] >= 0.5:
        output["status"] = "⚠️ Moderate"
    else:
        output["status"] = "🔴 Fragile"

    state.log_event(f"[FORECAST] Foresight generated. Turn: {state.turn} | Horizon: {horizon_days}d")
    output = attach_timestamp(output)
    return output

