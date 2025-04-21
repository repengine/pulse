"""
forecast_licenser.py

Filters or labels forecasts based on confidence, fragility, and licensing thresholds.
Prevents low-trust forecasts from flooding the Strategos Digest.

Author: Pulse v0.2
"""

from typing import List, Dict
from utils.log_utils import get_logger
from core.pulse_config import CONFIDENCE_THRESHOLD, DEFAULT_FRAGILITY_THRESHOLD

logger = get_logger(__name__)


def license_forecast(
    forecast: Dict,
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
    fragility_threshold: float = DEFAULT_FRAGILITY_THRESHOLD
) -> Dict:
    """
    Assigns a license tag to a forecast based on trustworthiness.
    Does NOT delete forecast — just labels it.

    Args:
        forecast (Dict): The forecast dictionary to license.
        confidence_threshold (float): Minimum confidence for licensing.
        fragility_threshold (float): Maximum fragility for licensing.
    Returns:
        Dict: The forecast dict with .license_status field
    """
    conf = forecast.get("confidence", 0.0)
    frag = forecast.get("fragility", 0.0)

    if conf >= confidence_threshold and frag < fragility_threshold:
        forecast["license_status"] = "✅ Licensed"
        logger.info(f"Forecast {forecast.get('trace_id', '-')}: Licensed (conf={conf}, frag={frag})")
    elif conf >= 0.4:
        forecast["license_status"] = "⚠️ Unlicensed (low trust)"
        logger.warning(f"Forecast {forecast.get('trace_id', '-')}: Unlicensed (low trust) (conf={conf}, frag={frag})")
    else:
        forecast["license_status"] = "❌ Suppressed (very low trust)"
        logger.error(f"Forecast {forecast.get('trace_id', '-')}: Suppressed (very low trust) (conf={conf}, frag={frag})")

    return forecast


def filter_licensed_forecasts(
    forecasts: List[Dict],
    strict: bool = False
) -> List[Dict]:
    """
    Filters forecasts using license_forecast().

    Args:
        forecasts (List[Dict]): Batch of forecast dicts.
        strict (bool): If True, returns only ✅ Licensed forecasts.
    Returns:
        List[Dict]: Filtered or labeled forecasts.
    """
    # Flatten any nested lists and filter out non-dict items
    flat = []
    for f in forecasts:
        if isinstance(f, dict):
            flat.append(f)
        elif isinstance(f, list):
            flat.extend([x for x in f if isinstance(x, dict)])
        # else: ignore non-dict, non-list items

    labeled = [license_forecast(f) for f in flat]
    if strict:
        return [f for f in labeled if f.get("license_status") == "✅ Licensed"]
    return labeled


def test_license_generation():
    """
    Unit test for license_forecast and filter_licensed_forecasts.
    """
    test_batch = [
        {"trace_id": "A", "confidence": 0.97, "fragility": 0.2},
        {"trace_id": "B", "confidence": 0.5, "fragility": 0.8},
        {"trace_id": "C", "confidence": 0.2, "fragility": 0.1},
    ]
    results = filter_licensed_forecasts(test_batch)
    assert results[0]["license_status"] == "✅ Licensed"
    assert results[1]["license_status"].startswith("⚠️")
    assert results[2]["license_status"].startswith("❌")
    logger.info("test_license_generation passed.")

if __name__ == "__main__":
    test_license_generation()
