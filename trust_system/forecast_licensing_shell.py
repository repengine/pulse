# trust_system/forecast_licensing_shell.py

"""
Forecast Licensing Shell

Decides whether a forecast is eligible for memory retention, export, or operator trust
based on trust label, alignment score, symbolic drift, and fragility.

Author: Pulse AI Engine
Version: v1.0.0
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

def license_forecast(forecast: Optional[Dict], thresholds: Optional[Dict] = None) -> str:
    """
    Determines the licensing status of a forecast based on confidence, trust, alignment, and drift.
    
    Args:
        forecast (Dict): The forecast to evaluate, containing trust_label, confidence, 
                         alignment_score, and drift_flag keys.
        thresholds (Dict, optional): Custom thresholds for confidence and alignment.
                                     Defaults to {"confidence_min": 0.60, "alignment_min": 0.75}.
    
    Returns:
        str: License status (one of: "✅ Approved", "❌ No Confidence", "🚫 Untrusted", 
             "🔴 Blocked - {drift_flag}", "⚠️ Low Alignment")
    
    Raises:
        ValueError: If the forecast is None or not a dictionary
    """
    if forecast is None or not isinstance(forecast, dict):
        logger.error("Invalid forecast provided to license_forecast")
        raise ValueError("Forecast must be a dictionary")

    # Default thresholds
    t = thresholds or {"confidence_min": 0.60, "alignment_min": 0.75}
    
    # Extract and validate confidence
    try:
        conf = forecast.get("confidence", 0.0)
        if not isinstance(conf, (int, float)):
            logger.warning(f"Invalid confidence value: {conf}, defaulting to 0.0")
            conf = 0.0
    except Exception as e:
        logger.error(f"Error extracting confidence: {e}")
        conf = 0.0
    
    # Extract and validate alignment score
    try:
        align = forecast.get("alignment_score", 0.0)
        if not isinstance(align, (int, float)) and align is not None:
            logger.warning(f"Invalid alignment value: {align}, defaulting to 0.0")
            align = 0.0
        align = float(align) if align is not None else 0.0
    except Exception as e:
        logger.error(f"Error extracting alignment score: {e}")
        align = 0.0

    trust_label = forecast.get("trust_label", "unknown")
    drift_flag = forecast.get("drift_flag")

    # Decision logic
    if conf < t["confidence_min"]:
        return "❌ No Confidence"
    if trust_label not in {"🟢 Trusted", "⚠️ Moderate"}:
        return "🚫 Untrusted"
    if drift_flag and drift_flag != "✅ Stable":
        return f"🔴 Blocked - {drift_flag}"
    if align < t["alignment_min"]:
        return "⚠️ Low Alignment"

    return "✅ Approved"

# --- Simple test function for manual validation ---
def _test_license():
    """Basic test for forecast licensing shell."""
    test_forecasts = [
        {"confidence": 0.8, "trust_label": "🟢 Trusted", "alignment_score": 0.9, "drift_flag": "✅ Stable"},
        {"confidence": 0.4, "trust_label": "🟢 Trusted", "alignment_score": 0.9, "drift_flag": "✅ Stable"},
        {"confidence": 0.8, "trust_label": "🔴 Rejected", "alignment_score": 0.9, "drift_flag": "✅ Stable"},
        {"confidence": 0.8, "trust_label": "🟢 Trusted", "alignment_score": 0.5, "drift_flag": "✅ Stable"},
        {"confidence": 0.8, "trust_label": "🟢 Trusted", "alignment_score": 0.9, "drift_flag": "⚠️ Overlay Volatility"},
    ]
    
    for i, fc in enumerate(test_forecasts):
        status = license_forecast(fc)
        print(f"Test {i+1}: {status}")
    
    # Edge case testing
    try:
        print(f"Edge case 1: {license_forecast(None)}")
    except ValueError as e:
        print(f"Edge case 1 correctly failed: {e}")
    
    try:
        print(f"Edge case 2: {license_forecast({'confidence': 'invalid'})}")
        print(f"Edge case 3: {license_forecast({'alignment_score': 'invalid'})}")
    except Exception as e:
        print(f"Unexpected failure: {e}")

if __name__ == "__main__":
    _test_license()
