"""
forecast_formatter.py

Formats structured forecast objects into human-readable foresight output.
Supports Strategos Tile and Digest formatting for strategic capital-symbolic clarity.

Author: Pulse v3.5
"""

from typing import Dict


def format_forecast_tile(forecast_obj: Dict) -> str:
    """
    Formats a forecast into a Strategos Forecast Tile-style output.

    Parameters:
        forecast_obj (Dict): structured forecast from forecast_generator

    Returns:
        str: formatted foresight string
    """
    f = forecast_obj
    fc = f["forecast"]
    alignment = f.get("alignment", {})
    fragility = f.get("fragility", "N/A")
    confidence = f.get("confidence", "pending")

    formatted = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔮 Strategos Forecast Tile
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Duration      : {f['horizon_days']} days
Turn          : {f['origin_turn']}
Trace ID      : {f['trace_id']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Exposure Delta:
  NVDA  → {fc['end_capital']['nvda'] - fc['start_capital']['nvda']:.2f}
  MSFT  → {fc['end_capital']['msft'] - fc['start_capital']['msft']:.2f}
  IBIT  → {fc['end_capital']['ibit'] - fc['start_capital']['ibit']:.2f}
  SPY   → {fc['end_capital']['spy'] - fc['start_capital']['spy']:.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fragility     : {fragility}
Confidence    : {confidence}
Symbolic Drift: {fc['symbolic_change']}
Alignment     : {alignment.get('bias', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status        : {f.get('status', 'unlabeled')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return formatted.strip()
