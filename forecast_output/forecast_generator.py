"""
Forecast Generator Module

This module generates final forecasts by optionally incorporating AI forecaster adjustments
into simulation-based forecasts.
"""

import logging
from typing import Dict, Optional

import core.pulse_config as pulse_config
from forecast_engine import ai_forecaster, forecast_ensemble
from causal_model.structural_causal_model import StructuralCausalModel
from causal_model.discovery import CausalDiscovery
from causal_model.counterfactual_engine import CounterfactualEngine

logger = logging.getLogger(__name__)

def generate_simulation_forecast() -> Dict:
    """
    Dummy function to simulate simulation-based forecast.
    Returns:
        A dictionary with forecast value.
    """
    # For demonstration purposes, we simulate a static forecast value.
    return {"value": 100.0}

def generate_forecast(input_features: Dict, causal_model: Optional[StructuralCausalModel] = None) -> Dict:
    """
    Generate the final forecast by combining simulation-based forecast with AI forecaster adjustments.
    Optionally attaches a causal explanation if a causal model is provided.
    Args:
        input_features: Dictionary containing relevant input features for forecasting.
        causal_model: Optional StructuralCausalModel for generating causal explanations.
    Returns:
        Combined forecast dictionary, possibly with a causal_explanation field.
    """
    logger.info(
        "[Forecast Pipeline] Entering generate_forecast: type(input_features)=%s, keys=%s, sample=%s",
        type(input_features),
        list(input_features.keys())[:5],
        {k: input_features[k] for k in list(input_features.keys())[:3]}
    )
    simulation_forecast = generate_simulation_forecast()
    if getattr(pulse_config, "AI_FORECAST_ENABLED", True):
        # Filter input_features to only include numeric values (flatten nested dicts)
        numeric_features = {}
        for key, value in input_features.items():
            if isinstance(value, (int, float)):
                numeric_features[key] = value
            elif isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, (int, float)):
                        numeric_features[f"{key}_{nested_key}"] = nested_value

        ai_forecast = ai_forecaster.predict(numeric_features)
        logger.info(
            "[Forecast Pipeline] After ai_forecaster.predict(): type(ai_forecast)=%s, keys=%s, sample=%s",
            type(ai_forecast),
            list(ai_forecast.keys())[:5] if hasattr(ai_forecast, "keys") else str(ai_forecast)[:50],
            {k: ai_forecast[k] for k in list(ai_forecast.keys())[:3]} if hasattr(ai_forecast, "keys") else str(ai_forecast)[:100]
        )
        forecast = forecast_ensemble.ensemble_forecast(simulation_forecast, ai_forecast)
    else:
        forecast = simulation_forecast

    # Attach causal explanation if a model is provided
    if causal_model is not None:
        # Example: get parents of a key variable as explanation
        key_var = next(iter(input_features.keys()), None)
        if key_var:
            parents = causal_model.parents(key_var)
            forecast["causal_explanation"] = {
                "variable": key_var,
                "parents": parents
            }
    return forecast

# For demonstration purposes, run a sample forecast generation if executed as main.
if __name__ == "__main__":
    features = {"example_feature": 1}
    forecast = generate_forecast(features)
    logger.info("Generated Forecast: %s", forecast)
    print("Forecast:", forecast)
