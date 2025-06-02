"""
Forecast Generator Module

This module generates final forecasts by optionally incorporating AI forecaster adjustments
into simulation-based forecasts.
"""

import logging
from typing import Dict, Optional

import engine.pulse_config as pulse_config
from forecast_engine import ai_forecaster, forecast_ensemble
from causal_model.structural_causal_model import StructuralCausalModel

logger = logging.getLogger(__name__)


def generate_simulation_forecast() -> Dict:
    """
    Dummy function to simulate simulation-based forecast.
    Returns:
        A dictionary with forecast value.
    """
    # For demonstration purposes, we simulate a static forecast value.
    return {"value": 100.0}


def generate_forecast(
    input_features: Dict, causal_model: Optional[StructuralCausalModel] = None
) -> Dict:
    """
    Generate the final forecast by combining simulation-based forecast with AI forecaster adjustments.
    Optionally attaches a causal explanation if a causal model is provided.
    Args:
        input_features: Dictionary containing relevant input features for forecasting.
        causal_model: Optional StructuralCausalModel for generating causal explanations.
    Returns:
        Combined forecast dictionary, possibly with a causal_explanation field.
    """
    # Input validation
    if not isinstance(input_features, dict):
        logger.error(
            f"Invalid input_features type: {
                type(input_features)}. Expected dict. Using empty dict.")
        input_features = {}

    logger.info(
        "[Forecast Pipeline] Entering generate_forecast: type(input_features)=%s, keys=%s, sample=%s",
        type(input_features),
        list(input_features.keys())[:5] if input_features else [],
        (
            {k: input_features[k] for k in list(input_features.keys())[:3]}
            if input_features
            else {}
        ),
    )

    # Generate base simulation forecast
    try:
        simulation_forecast = generate_simulation_forecast()
        # Validate simulation forecast structure
        if not isinstance(simulation_forecast, dict):
            logger.error(
                f"Invalid simulation_forecast type: {
                    type(simulation_forecast)}. Expected dict. Using default.")
            simulation_forecast = {"value": 0.0}
        if "value" not in simulation_forecast:
            logger.warning(
                "simulation_forecast missing 'value' key. Adding default value: 0.0"
            )
            simulation_forecast["value"] = 0.0
        # Ensure value is numeric
        try:
            simulation_forecast["value"] = float(simulation_forecast["value"])
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid simulation_forecast value: {
                    simulation_forecast.get('value')}. Using default: 0.0")
            simulation_forecast["value"] = 0.0
    except Exception as e:
        logger.exception(f"Error generating simulation forecast: {e}")
        simulation_forecast = {"value": 0.0}

    if getattr(pulse_config, "AI_FORECAST_ENABLED", True):
        try:
            # Filter input_features to only include numeric values (flatten nested
            # dicts)
            numeric_features = {}
            for key, value in input_features.items():
                try:
                    if isinstance(value, (int, float)):
                        numeric_features[key] = float(value)
                    elif isinstance(value, dict):
                        for nested_key, nested_value in value.items():
                            if isinstance(nested_value, (int, float)):
                                numeric_features[f"{key}_{nested_key}"] = float(
                                    nested_value
                                )
                            elif nested_value is not None:
                                try:
                                    numeric_value = float(nested_value)
                                    numeric_features[f"{key}_{nested_key}"] = (
                                        numeric_value
                                    )
                                    logger.info(
                                        f"Converted non-numeric value for {key}_{nested_key}: {nested_value} to {numeric_value}")
                                except (ValueError, TypeError):
                                    logger.warning(
                                        f"Skipping non-numeric value for {key}_{nested_key}: {nested_value}")
                    elif value is not None:
                        # Attempt to convert string or other values to float if possible
                        try:
                            numeric_value = float(value)
                            numeric_features[key] = numeric_value
                            logger.info(
                                f"Converted non-numeric value for {key}: {value} to {numeric_value}")
                        except (ValueError, TypeError):
                            logger.warning(
                                f"Skipping non-numeric value for {key}: {value}"
                            )
                except Exception as e:
                    logger.warning(f"Error processing feature {key}: {e}")

            logger.info(
                f"Filtered numeric features: {
                    len(numeric_features)} of {
                    len(input_features)} total features")

            # Generate AI forecast
            ai_forecast = ai_forecaster.predict(numeric_features)

            # Validate AI forecast
            if not isinstance(ai_forecast, dict):
                logger.error(
                    f"Invalid ai_forecast type: {
                        type(ai_forecast)}. Expected dict. Using default.")
                ai_forecast = {"adjustment": 0.0}
            if "adjustment" not in ai_forecast:
                logger.warning(
                    "ai_forecast missing 'adjustment' key. Adding default adjustment: 0.0"
                )
                ai_forecast["adjustment"] = 0.0

            # Ensure adjustment is numeric
            try:
                ai_forecast["adjustment"] = float(ai_forecast["adjustment"])
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid ai_forecast adjustment: {
                        ai_forecast.get('adjustment')}. Using default: 0.0")
                ai_forecast["adjustment"] = 0.0

            logger.info(
                "[Forecast Pipeline] After ai_forecaster.predict(): type(ai_forecast)=%s, keys=%s, sample=%s",
                type(ai_forecast),
                (
                    list(ai_forecast.keys())[:5]
                    if hasattr(ai_forecast, "keys")
                    else str(ai_forecast)[:50]
                ),
                (
                    {k: ai_forecast[k] for k in list(ai_forecast.keys())[:3]}
                    if hasattr(ai_forecast, "keys")
                    else str(ai_forecast)[:100]
                ),
            )

            # Ensemble forecasts
            final_forecast_value = forecast_ensemble.ensemble_forecast(
                simulation_forecast, ai_forecast
            ).get("value", 0.0)

            forecast = {
                "value": final_forecast_value,
                "breakdown": {
                    "simulation_based": simulation_forecast.get("value", 0.0),
                    "ai_adjustment": ai_forecast.get("adjustment", 0.0),
                },
                # Placeholders for more detailed information
                "confidence_interval": None,  # Requires updates to underlying models
                "probability_distribution": None,  # Requires updates to underlying models
                "contributing_factors": {},  # Placeholder for detailed influence analysis
            }

        except Exception as e:
            logger.exception(f"Error in AI forecasting pipeline: {e}")
            # Construct the forecast dictionary with error information
            forecast = {
                "value": simulation_forecast.get(
                    "value", 0.0
                ),  # Use simulation value as fallback
                "breakdown": {
                    "simulation_based": simulation_forecast.get("value", 0.0),
                    "ai_adjustment": 0.0,  # Assume no AI adjustment on error
                },
                "error": f"AI forecasting failed: {str(e)}",
                "confidence_interval": None,  # Requires updates to underlying models
                "probability_distribution": None,  # Requires updates to underlying models
                "contributing_factors": {},  # Placeholder for detailed influence analysis
            }

    else:
        # AI forecasting is disabled, use simulation forecast and structure the output
        forecast = {
            "value": simulation_forecast.get("value", 0.0),
            "breakdown": {
                "simulation_based": simulation_forecast.get("value", 0.0),
                "ai_adjustment": 0.0,
            },
            "confidence_interval": None,
            "probability_distribution": None,
            "contributing_factors": {},
        }

    # Attach causal explanation if a model is provided
    if causal_model is not None:
        try:
            # Example: get parents of a key variable as explanation
            key_var = next(iter(input_features.keys()), None)
            if key_var:
                parents = causal_model.parents(key_var)
                forecast["causal_explanation"] = {
                    "variable": key_var,
                    "parents": parents,
                    # Placeholder for more detailed influence analysis
                    "influence_breakdown": {},  # Requires updates to causal model/engine
                }
        except Exception as e:
            logger.warning(f"Failed to attach causal explanation: {e}")
            forecast["causal_explanation"] = {"error": str(e)}

    # Final validation to ensure the forecast has essential fields (confidence and fragility)
    # These might be added by the ensemble step or need defaults
    for field in ["confidence", "fragility"]:
        if field not in forecast or not isinstance(forecast[field], (int, float)):
            # Check if the field exists and is numeric, otherwise add/default
            forecast[field] = 0.5  # Default midpoint value
            logger.info(
                f"Added/Corrected missing or non-numeric field '{field}' with default value 0.5")

    return forecast


# For demonstration purposes, run a sample forecast generation if executed as main.
if __name__ == "__main__":
    features = {"example_feature": 1}
    forecast = generate_forecast(features)
    logger.info("Generated Forecast: %s", forecast)
    print("Forecast:", forecast)
