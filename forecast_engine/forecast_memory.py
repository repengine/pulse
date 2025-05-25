"""
forecast_memory.py

Archives forecast metadata snapshots for long-term memory and validation.
Supports:
- Saving scored forecast entries
- Retrieving forecast history
- Lightweight tagging and optional domain filtering

Future extensions:
- Clustering
- Divergence tracking
- Rule echo memory

Author: Pulse v0.10
"""

from typing import Dict, Any, Optional, List
from core.pulse_config import MODULES_ENABLED
from core.path_registry import PATHS
from memory.forecast_memory import ForecastMemory
from utils.log_utils import get_logger

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

if not MODULES_ENABLED.get("memory_guardian", True):
    raise RuntimeError("Forecast memory module is disabled in config.")

forecast_memory = ForecastMemory(persist_dir=str(PATHS["FORECAST_HISTORY"]))
logger = get_logger(__name__)


def save_forecast_to_memory(
    forecast_id: str, metadata: Dict[str, Any], domain: Optional[str] = None
) -> Dict[str, Any]:
    """
    Stores a forecast and its metadata to memory.

    Args:
        forecast_id (str): Identifier for the forecast
        metadata (dict): Associated trust, symbolic, and scoring info
        domain (str): Optional domain tag (e.g., capital, nfl)
    Returns:
        dict: The stored entry
    """
    entry = {"forecast_id": forecast_id, "metadata": metadata, "domain": domain}
    forecast_memory.store(entry)
    return entry


def load_forecast_history(
    limit: int = 10, domain_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Loads up to N recent forecast memory entries.

    Args:
        limit (int): Number of entries to load
        domain_filter (str): Optional domain tag to filter entries

    Returns:
        list of dicts
    """
    return forecast_memory.get_recent(limit, domain=domain_filter)
