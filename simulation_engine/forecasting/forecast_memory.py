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

import os
import json
from datetime import datetime
from typing import Dict
from memory.forecast_memory import ForecastMemory
from utils.log_utils import get_logger

logger = get_logger(__name__)
forecast_memory = ForecastMemory(persist_dir="forecast_output/forecast_history")


def save_forecast_to_memory(forecast_id: str, metadata: dict, domain: str = None):
    """
    Stores a forecast and its metadata to memory.

    Args:
        forecast_id (str): Identifier for the forecast
        metadata (dict): Associated trust, symbolic, and scoring info
        domain (str): Optional domain tag (e.g., capital, nfl)
    """
    entry = {
        "forecast_id": forecast_id,
        "metadata": metadata,
        "domain": domain
    }
    forecast_memory.store(entry)
    return entry


def load_forecast_history(limit=10, domain_filter=None):
    """
    Loads up to N recent forecast memory entries.

    Args:
        limit (int): Number of entries to load
        domain_filter (str): Optional domain tag to filter entries

    Returns:
        list of dicts
    """
    return forecast_memory.get_recent(limit, domain=domain_filter)