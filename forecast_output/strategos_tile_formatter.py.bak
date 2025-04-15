"""
strategos_tile_formatter.py

Formats a forecast object into a Strategos Forecast Tile:
a compact, readable foresight unit that combines symbolic drift, capital movement,
confidence, fragility, and alignment into a clear scenario snapshot.

Author: Pulse v3.5
"""

from typing import Dict


def format_strategos_tile(forecast_obj: Dict) -> str:
    """
    Formats a forecast into a Strategos Forecast Tile.

    Parameters:
        forecast_obj (Dict): structured forecast from forecast_generator.py

    Returns:
        str: formatted tile string
    """
    f = forecast_obj
    fc = f.get("forecast", {})
    alignment = f.get("alignment", {})
    fragility = f.get("fragility", "N/A")
    confidence = f.get("confidence", "pending")

    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔮 Strategos Forecast Tile
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Trace ID      : {f.get("trace_id")}
Turn          : {f.get("origin_turn")}
Duration      : {f.get("horizon_days")} days
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Exposure Delta:
  NVDA  → {fc['end_capital']['nvda'] - fc['start_capital']['nvda']:.2f}
  MSFT  → {fc['end_capital']['msft'] - fc['start_capital']['msft']:.2f}
  IBIT  → {fc['end_capital']['ibit'] - fc['start_capital']['ibit']:.2f}
  SPY   → {fc['end_capital']['spy'] - fc['start_capital']['spy']:.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Symbolic Drift:
  {fc.get('symbolic_change')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fragility     : {fragility}
Confidence    : {confidence}
Alignment     : {alignment.get('bias', 'N/A')}
Status        : {f.get('status', 'unlabeled')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()
