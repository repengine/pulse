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

    Returns:
        forecast dict with .license_status field
    """
    conf = forecast.get("confidence", 0.0)
    frag = forecast.get("fragility", 0.0)

    if conf >= confidence_threshold and frag < fragility_threshold:
        forecast["license_status"] = "✅ Licensed"
    elif conf >= 0.4:
        forecast["license_status"] = "⚠️ Unlicensed (low trust)"
    else:
        forecast["license_status"] = "❌ Suppressed (very low trust)"

    return forecast


def filter_licensed_forecasts(
    forecasts: List[Dict],
    strict: bool = False
) -> List[Dict]:
    """
    Filters forecasts using license_forecast()

    Parameters:
        forecasts (List): batch of foresight dicts
        strict (bool): if True, returns only ✅ Licensed

    Returns:
        List: filtered or labeled forecasts
    """
    labeled = [license_forecast(f) for f in forecasts]
    if strict:
        return [f for f in labeled if f.get("license_status") == "✅ Licensed"]
    return labeled


# === Local test ===
def simulate_license_test():
    from forecast_output.pfpa_logger import PFPA_ARCHIVE
    batch = PFPA_ARCHIVE[-5:]
    filtered = filter_licensed_forecasts(batch)
    for f in filtered:
        logger.info(f"{f['trace_id']} → {f['confidence']} | {f.get('license_status')}")


if __name__ == "__main__":
    simulate_license_test()
