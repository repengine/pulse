"""
forecast_formatter.py

Formats structured forecast objects into human-readable foresight forecast_output.
Supports Strategos Tile and Digest formatting for strategic capital-symbolic clarity.

Author: Pulse v3.5
"""

from typing import Dict
from memory.forecast_memory import ForecastMemory
from core.path_registry import PATHS

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

forecast_memory = ForecastMemory(persist_dir=str(PATHS["FORECAST_HISTORY"]))


def format_forecast_tile(forecast_obj: Dict) -> str:
    """
    Formats a forecast into a Strategos Forecast Tile-style forecast_output.

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
Duration      : {f["horizon_days"]} days
Turn          : {f["origin_turn"]}
Trace ID      : {f["trace_id"]}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Exposure Delta:
  NVDA  → {fc.get("end_capital", {}).get("nvda", 0) - fc.get("start_capital", {}).get("nvda", 0):.2f}
  MSFT  → {fc.get("end_capital", {}).get("msft", 0) - fc.get("start_capital", {}).get("msft", 0):.2f}
  IBIT  → {fc.get("end_capital", {}).get("ibit", 0) - fc.get("start_capital", {}).get("ibit", 0):.2f}
  SPY   → {fc.get("end_capital", {}).get("spy", 0) - fc.get("start_capital", {}).get("spy", 0):.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fragility     : {fragility}
Confidence    : {confidence}
Symbolic Drift: {fc.get("symbolic_change")}
Alignment     : {alignment.get("bias", "N/A")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status        : {f.get("status", "unlabeled")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return formatted.strip()


def save_forecast(forecast_obj: Dict):
    forecast_memory.store(forecast_obj)
