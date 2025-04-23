"""
pfpa_logger.py

Pulse Forecast Performance Archive (PFPA) logger.
Stores forecast metadata, symbolic conditions, and scoring hooks for long-term memory and trust analysis.

Author: Pulse v3.5
"""

from output.forecast_age_tracker import decay_confidence_and_priority
from trust_system.retrodiction_engine import retrodict_forecast
from memory.forecast_memory import ForecastMemory
from typing import Dict, List
import datetime
from utils.log_utils import get_logger
from core.pulse_config import CONFIDENCE_THRESHOLD
from core.path_registry import PATHS
from trust_system.trust_engine import TrustEngine

logger = get_logger(__name__)

# Persistent archive layer
pfpa_memory = ForecastMemory(persist_dir=PATHS["FORECAST_HISTORY"])

PFPA_ARCHIVE = []  # or your actual archive object


def log_forecast_to_pfpa(forecast_obj: dict, outcome: dict = None, status: str = "open") -> None:
    """
    Logs a forecast to the PFPA archive, tagging if below confidence threshold.
    Args:
        forecast_obj (dict): The forecast object to log.
        outcome (dict, optional): Outcome data for the forecast.
        status (str): Status tag for the forecast.
    Returns:
        None
    """
    # Wrap in a list for coherence check
    status_flag, issues = TrustEngine.check_forecast_coherence([forecast_obj])
    if status_flag == "fail":
        logger.error(f"[PFPA] ❌ Forecast rejected due to coherence issues:")
        for i in issues:
            logger.error("  - %s", i)
        return None

    if forecast_obj.get("confidence", 0) < CONFIDENCE_THRESHOLD:
        forecast_obj["trust_label"] = "🔴 Below threshold"
        logger.warning(f"Forecast {forecast_obj.get('trace_id', '-')} below confidence threshold.")

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
    # --- PATCH: Ensure overlays are serializable before storing ---
    def overlay_to_dict(overlay):
        if hasattr(overlay, "as_dict"):
            return overlay.as_dict()
        return dict(overlay)
    if "overlays" in entry:
        entry["overlays"] = overlay_to_dict(entry["overlays"])
    if "forks" in entry:
        for fork in entry["forks"]:
            if "overlays" in fork:
                fork["overlays"] = overlay_to_dict(fork["overlays"])
    # --- END PATCH ---
    pfpa_memory.store(entry)
    logger.info(f"Logged forecast {entry['trace_id']} to PFPA archive.")


def get_latest_forecasts(n: int = 5) -> List[Dict]:
    """
    Returns the N most recent forecasts from the archive.
    Args:
        n (int): Number of recent forecasts to retrieve.
    Returns:
        List[Dict]: List of recent forecast entries.
    """
    return pfpa_memory.get_recent(n)
