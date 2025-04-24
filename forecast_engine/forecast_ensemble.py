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
    # Check if AI forecasting is enabled in configuration. Default to True if not specified.
    enable_ai = getattr(pulse_config, "AI_FORECAST_ENABLED", True)
    if not enable_ai:
        logger.info("AI forecasting is disabled. Returning simulation forecast only.")
        return simulation_forecast

    # Retrieve ensemble weights from configuration with default values.
    ensemble_weights = getattr(pulse_config, "ENSEMBLE_WEIGHTS", {"simulation": 0.7, "ai": 0.3})
    sim_weight = ensemble_weights.get("simulation", 0.7)
    ai_weight = ensemble_weights.get("ai", 0.3)

    sim_value = simulation_forecast.get("value", 0.0)
    ai_adjustment = ai_forecast.get("adjustment", 0.0)
    
    # Compute the combined forecast value.
    combined_value = sim_weight * sim_value + ai_weight * (sim_value + ai_adjustment)
    logger.info("Simulation forecast: %f, AI adjustment: %f, Combined ensemble forecast: %f", sim_value, ai_adjustment, combined_value)
    
    return {"ensemble_forecast": combined_value}