"""
forecast_age_tracker.py

Adds time-awareness and trust decay to Pulse forecasts. Supports:
- Timestamping forecasts
- Confidence + priority_score decay
- Age-based tagging (e.g., "📉 Decayed", "❌ Expired")
- Memory pruning or diagnostics

Author: Pulse v0.2
"""

import datetime
from typing import List, Dict
from utils.log_utils import get_logger

logger = get_logger(__name__)


def attach_timestamp(forecast: Dict) -> Dict:
    """
    Adds a UTC timestamp to a forecast if not already present.
    """
    if "timestamp" not in forecast:
        forecast["timestamp"] = datetime.datetime.utcnow().isoformat()
    return forecast


def get_forecast_age(forecast: Dict) -> float:
    """
    Returns age in hours since forecast creation.
    """
    ts = forecast.get("timestamp")
    if not ts:
        return 0.0
    try:
        then = datetime.datetime.fromisoformat(ts)
        now = datetime.datetime.utcnow()
        delta = now - then
        return round(delta.total_seconds() / 3600.0, 2)
    except:
        return 0.0


def decay_confidence_and_priority(
    forecast: Dict,
    decay_per_hour: float = 0.01,
    min_confidence: float = 0.1,
    min_priority: float = 0.05
) -> Dict:
    """
    Applies linear decay to confidence and priority score.
    """
    age = get_forecast_age(forecast)
    forecast["confidence"] = round(max(min_confidence, forecast.get("confidence", 1.0) - decay_per_hour * age), 3)
    forecast["priority_score"] = round(max(min_priority, forecast.get("priority_score", 0.5) - decay_per_hour * age), 3)
    forecast["age_hours"] = age

    if age > 12:
        forecast["age_tag"] = "📉 Decayed"
    elif age > 24:
        forecast["age_tag"] = "❌ Expired"
    else:
        forecast["age_tag"] = "🕒 Fresh"

    return forecast


def prune_stale_forecasts(forecasts: List[Dict], max_age_hours: float = 24.0) -> List[Dict]:
    """
    Filters out forecasts older than max_age_hours.
    """
    return [f for f in forecasts if get_forecast_age(f) <= max_age_hours]


def simulate_age_decay_test():
    from forecast_output.pfpa_logger import PFPA_ARCHIVE
    logger.info("\n[DECAY TEST] Age-based trust decay preview:")
    for f in PFPA_ARCHIVE[-5:]:
        decay_confidence_and_priority(f)
        logger.info(f"→ {f.get('trace_id')} | Age: {f['age_hours']}h | Conf: {f['confidence']} | Priority: {f.get('priority_score')} | {f.get('age_tag')}")


if __name__ == "__main__":
    simulate_age_decay_test()
