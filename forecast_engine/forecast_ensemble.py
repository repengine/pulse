"""
Forecast Ensemble Module

This module aggregates simulation-based forecasts with predictions from the AI model.
It computes a combined forecast using a weighted average, with ensemble weights configurable
via core configuration settings in core/pulse_config.py.
"""

import logging
from typing import Dict
import core.pulse_config as pulse_config

logger = logging.getLogger(__name__)


def ensemble_forecast(simulation_forecast: Dict, ai_forecast: Dict) -> Dict:
    """
    Combine simulation-based forecast and AI forecast predictions based on ensemble weights.

    Args:
        simulation_forecast: A dictionary containing simulation-based forecast output.
                             Expected to have a key 'value'.
        ai_forecast: A dictionary containing AI forecast adjustments.
                     Expected to have a key 'adjustment'.

    Returns:
        A dictionary with the combined ensemble forecast.
    """
    logger.info(
        "[Forecast Pipeline] Entering ensemble_forecast: type(simulation_forecast)=%s, sample=%s; type(ai_forecast)=%s, sample=%s",
        type(simulation_forecast),
        {k: simulation_forecast[k] for k in list(simulation_forecast.keys())[:3]}
        if hasattr(simulation_forecast, "keys")
        else str(simulation_forecast)[:100],
        type(ai_forecast),
        {k: ai_forecast[k] for k in list(ai_forecast.keys())[:3]}
        if hasattr(ai_forecast, "keys")
        else str(ai_forecast)[:100],
    )
    # Check if AI forecasting is enabled in configuration. Default to True if not specified.
    enable_ai = getattr(pulse_config, "AI_FORECAST_ENABLED", True)
    if not enable_ai:
        logger.info("AI forecasting is disabled. Returning simulation forecast only.")
        return simulation_forecast

    # Retrieve ensemble weights from configuration with default values.
    ensemble_weights = getattr(
        pulse_config, "ENSEMBLE_WEIGHTS", {"simulation": 0.7, "ai": 0.3}
    )
    sim_weight = ensemble_weights.get("simulation", 0.7)
    ai_weight = ensemble_weights.get("ai", 0.3)

    # Extract values and ensure they are float type to prevent "must be real number, not str" errors
    sim_val_raw = simulation_forecast.get("value", 0.0)
    import re

    uuid_like = isinstance(sim_val_raw, str) and re.match(
        r"^[0-9a-fA-F-]{32,36}$", sim_val_raw
    )
    try:
        if uuid_like:
            logger.error(
                f"Simulation forecast 'value' is a UUID string (forecast_id?): {sim_val_raw}. This is a bug upstream. Using default 0.0"
            )
            sim_value = 0.0
        else:
            sim_value = float(sim_val_raw)
    except (ValueError, TypeError):
        logger.warning(
            f"Invalid simulation forecast value: {sim_val_raw} (type={type(sim_val_raw)}). Using default 0.0"
        )
        sim_value = 0.0

    ai_adj_raw = ai_forecast.get("adjustment", 0.0)
    # Also check AI adjustment for UUID-like strings
    uuid_like_ai = isinstance(ai_adj_raw, str) and re.match(
        r"^[0-9a-fA-F-]{32,36}$", ai_adj_raw
    )
    try:
        if uuid_like_ai:
            logger.error(
                f"AI forecast 'adjustment' is a UUID string (forecast_id?): {ai_adj_raw}. This is a bug upstream. Using default 0.0"
            )
            ai_adjustment = 0.0
        else:
            ai_adjustment = float(ai_adj_raw)
    except (ValueError, TypeError):
        logger.warning(
            f"Invalid AI adjustment value: {ai_adj_raw} (type={type(ai_adj_raw)}). Using default 0.0"
        )
        ai_adjustment = 0.0

    # Compute the combined forecast value with validated float values
    combined_value = sim_weight * sim_value + ai_weight * (sim_value + ai_adjustment)
    logger.info(
        "Simulation forecast: %f, AI adjustment: %f, Combined ensemble forecast: %f",
        sim_value,
        ai_adjustment,
        combined_value,
    )
    combined_forecast = {"ensemble_forecast": combined_value, "value": combined_value}
    logger.info(
        "[Forecast Pipeline] Returning from ensemble_forecast: type=%s, value=%s",
        type(combined_forecast),
        {k: combined_forecast[k] for k in list(combined_forecast.keys())},
    )
    return combined_forecast
