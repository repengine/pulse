"""
strategos_digest.py

Generates a strategic digest summary composed of recent Strategos Forecast Tiles.
Intended for daily/weekly foresight reporting and operator review.

Author: Pulse v3.5
"""

from forecast_output.strategos_tile_formatter import format_strategos_tile
from memory.forecast_memory import ForecastMemory
from typing import Optional


def generate_strategos_digest(
    memory: ForecastMemory,
    n: int = 3,
    title: Optional[str] = None
) -> str:
    """
    Returns a human-readable foresight digest composed of recent forecast tiles.

    Parameters:
        memory (ForecastMemory): forecast memory instance
        n (int): number of forecasts to include
        title (str): optional digest title/header

    Returns:
        str: formatted digest string
    """
    recent_forecasts = memory.get_recent(n)
    header = title or "Strategos Forecast Digest"
    tiles = [format_strategos_tile(f) for f in recent_forecasts]

    return f"""
========================================
📘 {header}
========================================
{"\n\n".join(tiles)}
========================================
Total Forecasts: {len(tiles)}
========================================
""".strip()
