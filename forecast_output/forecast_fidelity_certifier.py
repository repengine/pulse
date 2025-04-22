# forecast_output/forecast_fidelity_certifier.py

"""
Forecast Fidelity Certifier

Certifies forecasts as fully trustworthy if they meet:
- Trust label: 🟢 Trusted
- License: ✅ Approved
- Alignment score ≥ 75
- Confidence ≥ 0.6
- Not drift-prone or symbolically unstable

Author: Pulse AI Engine
Version: v1.0.0
"""

from typing import List, Dict


def is_certified_forecast(forecast: Dict) -> bool:
    if not isinstance(forecast, dict):
        return False
    return (
        forecast.get("trust_label") == "🟢 Trusted" and
        forecast.get("license_status") == "✅ Approved" and
        forecast.get("alignment_score", 0) >= 75 and
        forecast.get("confidence", 0) >= 0.6 and
        not forecast.get("drift_flag") and
        not forecast.get("symbolic_fragmented") and
        not forecast.get("symbolic_revision_needed", False)
    )


def explain_certification(forecast: Dict) -> str:
    """
    Return textual explanation of certification status.

    Returns:
        str
    """
    if is_certified_forecast(forecast):
        return "✅ Forecast certified for strategic use."

    reasons = []
    if forecast.get("trust_label") != "🟢 Trusted":
        reasons.append("Trust label not green.")
    if forecast.get("license_status") != "✅ Approved":
        reasons.append("License not approved.")
    if forecast.get("alignment_score", 0) < 75:
        reasons.append("Low alignment score.")
    if forecast.get("confidence", 0) < 0.6:
        reasons.append("Low confidence.")
    if forecast.get("drift_flag"):
        reasons.append("Drift-flagged forecast.")
    if forecast.get("symbolic_fragmented"):
        reasons.append("Part of symbolic fragmentation cluster.")
    if forecast.get("symbolic_revision_needed"):
        reasons.append("Still marked for symbolic revision.")

    return "❌ Forecast not certified:\n- " + "\n- ".join(reasons)


def tag_certified_forecasts(forecasts: List[Dict]) -> List[Dict]:
    if not isinstance(forecasts, list):
        raise ValueError("Input must be a list of dicts")
    for fc in forecasts:
        fc["certified"] = is_certified_forecast(fc)
    return forecasts


def generate_certified_digest(forecasts: List[Dict]) -> Dict:
    """
    Return count summary of certified vs uncertified forecasts.

    Returns:
        Dict: {'certified': x, 'uncertified': y}
    """
    c = sum(1 for fc in forecasts if is_certified_forecast(fc))
    return {
        "certified": c,
        "uncertified": len(forecasts) - c,
        "certified_ratio": round(c / max(len(forecasts), 1), 3)
    }


def _test_forecast_fidelity_certifier():
    dummy = [
        {"trust_label": "🟢 Trusted", "license_status": "✅ Approved", "alignment_score": 80, "confidence": 0.7, "drift_flag": False, "symbolic_fragmented": False, "symbolic_revision_needed": False},
        {"trust_label": "🟢 Trusted", "license_status": "❌ Rejected", "alignment_score": 80, "confidence": 0.7, "drift_flag": False, "symbolic_fragmented": False, "symbolic_revision_needed": False},
    ]
    tagged = tag_certified_forecasts(dummy)
    assert tagged[0]["certified"] is True
    assert tagged[1]["certified"] is False
    digest = generate_certified_digest(tagged)
    assert digest["certified"] == 1
    print("✅ Forecast fidelity certifier test passed.")


if __name__ == "__main__":
    _test_forecast_fidelity_certifier()
