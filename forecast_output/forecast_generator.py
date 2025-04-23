"""
forecast_generator.py

Creates a structured foresight object by combining symbolic overlays, capital forks,
and alignment tagging. This forms the core output of each shortview simulation cycle.

Author: Pulse v3.5
"""

from forecast_output.forecast_age_tracker import attach_timestamp
from simulation_engine.worldstate import WorldState
from capital_engine.capital_layer import run_shortview_forecast
from capital_engine.capital_layer import summarize_exposure, portfolio_alignment_tags
from trust_system.trust_engine import score_forecast
from symbolic_system.symbolic_utils import symbolic_fragility_index
from symbolic_system.symbolic_state_tagger import tag_symbolic_state
from symbolic_system.pulse_symbolic_arc_tracker import compute_arc_label
from typing import Dict, Any
from utils.log_utils import get_logger
from core.pulse_config import CONFIDENCE_THRESHOLD, DEFAULT_FRAGILITY_THRESHOLD, TRUST_WEIGHT, DESPAIR_WEIGHT, USE_SYMBOLIC_OVERLAYS

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

    Note:
        Symbolic overlays (symbolic_tag, arc_label) are only included if USE_SYMBOLIC_OVERLAYS is True.
    """
    try:
        forecast = run_shortview_forecast(state, asset_subset=assets, duration_days=horizon_days)
    except Exception as e:
        logger.error(f"[ERROR] Forecast engine failed: {e}")
        return {}

    # Defensive: check for symbolic_fragility
    fragility = forecast.get("symbolic_fragility", 1.0)

    output = {
        "horizon_days": horizon_days,
        "forecast": forecast,
        "fragility": fragility,
        "exposure": summarize_exposure(state),
        "alignment": portfolio_alignment_tags(state),
        "confidence": None,
        "trace_id": f"fcast_turn_{state.turn}",
        "origin_turn": state.turn,
        "status": "experimental"
    }

    # 🔐 Add trust score + status label
    output["confidence"] = score_forecast(output)

    # Use config thresholds for status
    if output["confidence"] >= CONFIDENCE_THRESHOLD:
        output["status"] = "🟢 Trusted"
    elif output["confidence"] >= DEFAULT_FRAGILITY_THRESHOLD:
        output["status"] = "⚠️ Moderate"
    else:
        output["status"] = "🔴 Fragile"

    # Add symbolic overlays if enabled
    if USE_SYMBOLIC_OVERLAYS:
        try:
            # Use tag_symbolic_state and compute_arc_label instead of classify_symbolic_state and compute_arc
            forecast.update(tag_symbolic_state(forecast))
            forecast["arc_label"] = compute_arc_label(forecast)
            # ...other symbolic overlay logic...
        except Exception as e:
            logger.warning(f"Symbolic overlay logic failed: {e}")

    state.log_event(f"[FORECAST] Foresight generated. Turn: {state.turn} | Horizon: {horizon_days}d")
    output = attach_timestamp(output)
    return output

