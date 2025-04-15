"""
strategos_digest.py

Generates a foresight digest containing recent Strategos Forecast Tiles.
Used to summarize recent simulations for operator review or export.

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
    Formats a multi-tile digest of recent forecasts.

    Parameters:
        memory (ForecastMemory): forecast storage object
        n (int): number of tiles to include
        title (str): optional header for the digest

    Returns:
        str: formatted digest output
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
