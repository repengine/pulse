# trust_system/license_explainer.py

"""
Forecast License Explainer

Explains the licensing decision of a forecast based on:
- Confidence
- Alignment
- Trust label
- Drift status

Author: Pulse AI Engine
Version: v1.0.0
"""

from typing import Dict


def explain_forecast_license(forecast: Dict) -> str:
    """
    Return a plain-language explanation for the license status of a forecast.

    Args:
        forecast (Dict): A forecast object with trust metadata

    Returns:
        str: Human-readable rationale
    """
    label = forecast.get("license_status", "")
    conf = forecast.get("confidence", 0.0)
    align = forecast.get("alignment_score", 0.0)
    trust = forecast.get("trust_label", "")
    drift = forecast.get("drift_flag", "")
    reasons = []

    if label == "✅ Approved":
        return "This forecast met all trust criteria and is fully licensed for strategic use."

    if conf < 0.6:
        reasons.append(f"Confidence was too low ({conf:.2f}).")
    if trust != "🟢 Trusted":
        reasons.append(f"Forecast trust label is '{trust}', not fully trusted.")
    if drift:
        reasons.append(f"Symbolic drift detected: {drift}.")
    if align < 70:
        reasons.append(f"Alignment score below threshold ({align:.2f}).")

    if not reasons:
        return "Forecast failed licensing but no specific cause identified."

    return "License blocked for the following reason(s):\n- " + "\n- ".join(reasons)
