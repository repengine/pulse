"""
pfpa_logger.py

Pulse Forecast Performance Archive (PFPA) logger.
Stores forecast metadata, symbolic conditions, and scoring hooks for long-term memory and trust analysis.

Author: Pulse v3.5
"""

from typing import Dict, List
import datetime


# In-memory archive placeholder (replace with persistent layer post-export)
PFPA_ARCHIVE: List[Dict] = []


def log_forecast_to_pfpa(forecast_obj: Dict, outcome: Dict = None, status: str = "open"):
    """
    Logs a forecast object into the PFPA archive.

    Parameters:
        forecast_obj (Dict): forecast dictionary from forecast_generator
        outcome (Dict): optional outcome summary for later scoring
        status (str): current evaluation status ('open', 'hit', 'miss', 'inconclusive')
    """
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "trace_id": forecast_obj.get("trace_id"),
        "origin_turn": forecast_obj.get("origin_turn"),
        "horizon_days": forecast_obj.get("horizon_days"),
        "fragility": forecast_obj.get("fragility"),
        "confidence": forecast_obj.get("confidence"),
        "alignment": forecast_obj.get("alignment", {}),
        "symbolic_snapshot": forecast_obj["forecast"]["symbolic_change"],
        "exposure_start": forecast_obj["forecast"]["start_capital"],
        "exposure_end": forecast_obj["forecast"]["end_capital"],
        "status": status,
        "outcome": outcome or {},
    }

    PFPA_ARCHIVE.append(entry)


def get_latest_forecasts(n: int = 5) -> List[Dict]:
    """
    Returns the N most recent forecasts from the archive.
    """
    return PFPA_ARCHIVE[-n:]
