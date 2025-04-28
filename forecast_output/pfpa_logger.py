"""
pfpa_logger.py

Pulse Forecast Performance Archive (PFPA) logger.
Stores forecast metadata, symbolic conditions, and scoring hooks for long-term memory and trust analysis.

Author: Pulse v3.5
"""

from forecast_output.forecast_age_tracker import decay_confidence_and_priority
from memory.forecast_memory import ForecastMemory
from typing import Dict, List, Optional
import datetime
from utils.log_utils import get_logger
from core.pulse_config import CONFIDENCE_THRESHOLD
from core.path_registry import PATHS
from trust_system.trust_engine import TrustEngine
import json
from pathlib import Path

PFPA_ARCHIVE = Path('forecasts') / 'pfpa_archive.jsonl'

logger = get_logger(__name__)

# Persistent archive layer
pfpa_memory = ForecastMemory(persist_dir=str(PATHS["FORECAST_HISTORY"]))



def log_forecast_to_pfpa(forecast_obj: dict, retrodiction_results: Optional[dict] = None, outcome: Optional[dict] = None, status: str = "open") -> None:
    """
    Logs a forecast to the PFPA archive, tagging if below confidence threshold.
    Integrates retrodiction results from the unified simulate_forward function.

    Args:
        forecast_obj (dict): The forecast object to log.
        retrodiction_results (dict, optional): Retrodiction results from simulate_forward.
        outcome (dict, optional): Outcome data for the forecast.
        status (str): Status tag for the forecast.

    Returns:
        None

    Usage:
        log_forecast_to_pfpa(forecast_obj, retrodiction_results=retrodiction_data)
    """
    # Wrap in a list for coherence check
    status_flag, issues = TrustEngine.check_forecast_coherence([forecast_obj])
    if status_flag == "fail":
        logger.error("[PFPA] ❌ Forecast rejected due to coherence issues:")
        for i in issues:
            logger.error("  - %s", i)
        return None

    if forecast_obj.get("confidence", 0) < CONFIDENCE_THRESHOLD:
        forecast_obj["trust_label"] = "🔴 Below threshold"
        logger.warning(f"Forecast {forecast_obj.get('trace_id', '-')} below confidence threshold.")

    # Use retrodiction results from simulate_forward if provided
    if retrodiction_results is None:
        retrodiction_results = {
            "retrodiction_score": None,
            "symbolic_score": None,
            "asset_hits": [],
            "symbolic_hits": []
        }

    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "trace_id": forecast_obj.get("trace_id"),
        "origin_turn": forecast_obj.get("origin_turn"),
        "horizon_days": forecast_obj.get("horizon_days"),
        "fragility": forecast_obj.get("fragility"),
        "confidence": forecast_obj.get("confidence"),
        "status": forecast_obj.get("status"),  # Original forecast status
        "trust_label": forecast_obj.get("trust_label", "🟡 Unlabeled"),
        "alignment": forecast_obj.get("alignment", {}),
        "symbolic_snapshot": forecast_obj.get("forecast", {}).get("symbolic_change"),
        "exposure_start": forecast_obj.get("forecast", {}).get("start_capital"),
        "exposure_end": forecast_obj.get("forecast", {}).get("end_capital"),
        "retrodiction_score": retrodiction_results.get("retrodiction_score"),
        "symbolic_score": retrodiction_results.get("symbolic_score"),
        "retrodiction_hits": retrodiction_results.get("asset_hits"),
        "symbolic_hits": retrodiction_results.get("symbolic_hits"),
        "outcome": outcome or {},
        "status_tag": status  # Status tag passed as function parameter
    }
    forecast_obj = decay_confidence_and_priority(forecast_obj)
    pfpa_memory.store(entry)
    # Append entry to PFPA archive file
    PFPA_ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    with PFPA_ARCHIVE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
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
