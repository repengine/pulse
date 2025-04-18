"""
pfpa_logger.py

Pulse Forecast Performance Archive (PFPA) logger.
Stores forecast metadata, symbolic conditions, and scoring hooks for long-term memory and trust analysis.

Author: Pulse v3.5
"""

from forecast_output.forecast_age_tracker import decay_confidence_and_priority
from trust_system.retrodiction_engine import retrodict_forecast
from memory.forecast_memory import ForecastMemory
from typing import Dict, List
import datetime
from utils.log_utils import get_logger

logger = get_logger(__name__)

# Persistent archive layer
pfpa_memory = ForecastMemory(persist_dir="forecast_output/forecast_history")


def log_forecast_to_pfpa(forecast_obj: Dict, outcome: Dict = None, status: str = "open"):
    """
    Logs forecast to PFPA with optional actual outcome scoring
    """
    # Optional: simulate actual exposure for retrodiction
    simulated_actual = {
        "nvda": 10100,
        "msft": 9800,
        "ibit": 5300,
        "spy": 9600
    }

    retrodicted = retrodict_forecast(forecast_obj, simulated_actual)

    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "trace_id": forecast_obj.get("trace_id"),
        "origin_turn": forecast_obj.get("origin_turn"),
        "horizon_days": forecast_obj.get("horizon_days"),
        "fragility": forecast_obj.get("fragility"),
        "confidence": forecast_obj.get("confidence"),
        "status": forecast_obj.get("status"),
        "trust_label": forecast_obj.get("trust_label", "🟡 Unlabeled"),
        "alignment": forecast_obj.get("alignment", {}),
        "symbolic_snapshot": forecast_obj["forecast"]["symbolic_change"],
        "exposure_start": forecast_obj["forecast"]["start_capital"],
        "exposure_end": forecast_obj["forecast"]["end_capital"],
        "retrodiction_score": retrodicted["retrodiction_score"],
        "symbolic_score": retrodicted["symbolic_score"],
        "retrodiction_hits": retrodicted["asset_hits"],
        "symbolic_hits": retrodicted["symbolic_hits"],
        "outcome": outcome or {},
        "status_tag": status
    }
    forecast_obj = decay_confidence_and_priority(forecast_obj)
    pfpa_memory.store(entry)
    logger.info(f"Logged forecast {entry['trace_id']} to PFPA archive.")


def get_latest_forecasts(n: int = 5) -> List[Dict]:
    """
    Returns the N most recent forecasts from the archive.
    """
    return pfpa_memory.get_recent(n)
