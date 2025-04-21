# trust_system/forecast_licensing_shell.py

"""
Forecast Licensing Shell

Decides whether a forecast is eligible for memory retention, export, or operator trust
based on trust label, alignment score, symbolic drift, and fragility.

Author: Pulse AI Engine
Version: v1.0.0
"""

from typing import Dict

def license_forecast(forecast: Dict, thresholds: Dict = None) -> str:
    """
    Assign a license decision to a forecast.

    Parameters:
        forecast (Dict): A single forecast object with trust metadata
        thresholds (Dict): Optional override values

    Returns:
        str: One of:
            ✅ Approved
            🔴 Blocked - Drift-Prone
            ⚠️ Low Alignment
            🚫 Untrusted
            ❌ No Confidence
    """
    t = thresholds or {
        "confidence_min": 0.6,
        "alignment_min": 70,
    }

    # Defensive: handle missing/invalid fields
    conf = forecast.get("confidence", 0.0)
    try:
        conf = float(conf)
    except Exception:
        conf = 0.0

    align = forecast.get("alignment_score", 0.0)
    try:
        align = float(align)
    except Exception:
        align = 0.0

    trust_label = forecast.get("trust_label", "unknown")
    drift_flag = forecast.get("drift_flag")

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
    tests = [
        {"confidence": 0.8, "alignment_score": 80, "trust_label": "🟢 Trusted"},
        {"confidence": 0.5, "alignment_score": 80, "trust_label": "🟢 Trusted"},
        {"confidence": 0.8, "alignment_score": 60, "trust_label": "🟢 Trusted"},
        {"confidence": 0.8, "alignment_score": 80, "trust_label": "🔴 Fragile"},
        {"confidence": 0.8, "alignment_score": 80, "trust_label": "🟢 Trusted", "drift_flag": "Rule Instability"},
    ]
    for i, fc in enumerate(tests):
        print(f"Test {i+1}: {license_forecast(fc)}")

if __name__ == "__main__":
    _test_license()
