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

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def is_certified_forecast(forecast: Dict[str, Any]) -> bool:
    """
    Determines if a forecast meets all criteria for certification as fully trustworthy.

    Args:
        forecast: Dictionary containing forecast metadata

    Returns:
        bool: True if the forecast meets all certification criteria, False otherwise
    """
    if not isinstance(forecast, dict):
        logger.warning(
            f"Non-dictionary passed to is_certified_forecast: {type(forecast)}"
        )
        return False

    return (
        forecast.get("trust_label") == "🟢 Trusted"
        and forecast.get("license_status") == "✅ Approved"
        and forecast.get("alignment_score", 0) >= 75
        and forecast.get("confidence", 0) >= 0.6
        and not forecast.get("drift_flag")
        and not forecast.get("symbolic_fragmented")
        and not forecast.get("symbolic_revision_needed", False)
    )


def explain_certification(forecast: Dict[str, Any]) -> str:
    """
    Provides a human-readable explanation for why a forecast was certified or not.

    Args:
        forecast: Dictionary containing forecast metadata

    Returns:
        str: Explanation of certification status
    """
    if not isinstance(forecast, dict):
        return "❌ Invalid forecast format"

    if is_certified_forecast(forecast):
        return "✅ Forecast certified: Meets all trust, license, alignment, and stability criteria"

    reasons = []
    if forecast.get("trust_label") != "🟢 Trusted":
        reasons.append(f"Trust label is {forecast.get('trust_label', 'missing')}")
    if forecast.get("license_status") != "✅ Approved":
        reasons.append(f"License status is {forecast.get('license_status', 'missing')}")
    if forecast.get("alignment_score", 0) < 75:
        reasons.append(
            f"Alignment score is {forecast.get('alignment_score', 0)}, needs 75+"
        )
    if forecast.get("confidence", 0) < 0.6:
        reasons.append(f"Confidence is {forecast.get('confidence', 0)}, needs 0.6+")
    if forecast.get("drift_flag"):
        reasons.append(f"Has drift flag: {forecast.get('drift_flag')}")
    if forecast.get("symbolic_fragmented"):
        reasons.append("Symbolically fragmented")
    if forecast.get("symbolic_revision_needed"):
        reasons.append("Needs symbolic revision")

    return "❌ Forecast not certified:\n- " + "\n- ".join(reasons)


def tag_certified_forecasts(forecasts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Tags each forecast in a list with a 'certified' boolean flag.

    Args:
        forecasts: List of forecast dictionaries

    Returns:
        List of forecasts with 'certified' flag added
    """
    if not isinstance(forecasts, list):
        logger.error(
            f"Expected list for tag_certified_forecasts, got {type(forecasts)}"
        )
        return []

    result = []
    for forecast in forecasts:
        if not isinstance(forecast, dict):
            logger.warning(
                f"Skipping non-dictionary item in forecasts: {type(forecast)}"
            )
            continue

        forecast_copy = forecast.copy()
        forecast_copy["certified"] = is_certified_forecast(forecast)
        result.append(forecast_copy)

    return result


def generate_certified_digest(forecasts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Creates a summary digest of certified forecasts.

    Args:
        forecasts: List of forecasts with 'certified' flag

    Returns:
        Dictionary with certification statistics
    """
    if not isinstance(forecasts, list):
        logger.error(
            f"Expected list for generate_certified_digest, got {type(forecasts)}"
        )
        return {"total": 0, "certified": 0, "ratio": 0.0}

    tagged = tag_certified_forecasts(forecasts)
    total = len(tagged)
    certified = sum(1 for f in tagged if f.get("certified", False))

    return {
        "total": total,
        "certified": certified,
        "ratio": round(certified / total, 2) if total > 0 else 0.0,
        "certified_trace_ids": [
            f.get("trace_id") for f in tagged if f.get("certified", False)
        ],
    }


def _test_forecast_fidelity_certifier():
    """Tests the forecast fidelity certifier functions."""
    dummy = [
        {
            "trust_label": "🟢 Trusted",
            "license_status": "✅ Approved",
            "alignment_score": 80,
            "confidence": 0.7,
            "drift_flag": False,
            "symbolic_fragmented": False,
            "symbolic_revision_needed": False,
        },
        {
            "trust_label": "🟢 Trusted",
            "license_status": "❌ Rejected",
            "alignment_score": 80,
            "confidence": 0.7,
            "drift_flag": False,
            "symbolic_fragmented": False,
            "symbolic_revision_needed": False,
        },
        {
            "trust_label": "🟢 Trusted",
            "license_status": "✅ Approved",
            "alignment_score": 70,
            "confidence": 0.7,
            "drift_flag": False,
            "symbolic_fragmented": False,
            "symbolic_revision_needed": False,
        },
        {
            "trust_label": "🟢 Trusted",
            "license_status": "✅ Approved",
            "alignment_score": 80,
            "confidence": 0.5,
            "drift_flag": False,
            "symbolic_fragmented": False,
            "symbolic_revision_needed": False,
        },
    ]

    # Test individual certification
    assert is_certified_forecast(dummy[0]) is True
    assert is_certified_forecast(dummy[1]) is False
    assert is_certified_forecast(dummy[2]) is False
    assert is_certified_forecast(dummy[3]) is False

    # Test explanation
    assert "✅ Forecast certified" in explain_certification(dummy[0])
    assert "License status" in explain_certification(dummy[1])
    assert "Alignment score" in explain_certification(dummy[2])
    assert "Confidence" in explain_certification(dummy[3])

    # Test batch tagging
    tagged = tag_certified_forecasts(dummy)
    assert tagged[0]["certified"] is True
    assert tagged[1]["certified"] is False

    # Test digest
    digest = generate_certified_digest(tagged)
    assert digest["certified"] == 1
    assert digest["total"] == 4
    assert digest["ratio"] == 0.25

    # Test edge cases
    edge_cases = [
        None,
        {},
        {"trust_label": "🟢 Trusted"},
        {"alignment_score": "invalid"},
    ]
    for case in edge_cases:
        assert is_certified_forecast(case) is False

    print("✅ Forecast fidelity certifier test passed.")


if __name__ == "__main__":
    _test_forecast_fidelity_certifier()
