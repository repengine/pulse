"""
strategos_tile_formatter.py

Formats a structured forecast object into a Strategos Forecast Tile —
a compact, human-readable foresight unit with symbolic + capital outcomes.

Author: Pulse v3.5
"""

from typing import Dict
from engine.path_registry import PATHS

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

TILE_LOG_PATH = PATHS.get("TILE_LOG_PATH", PATHS["WORLDSTATE_LOG_DIR"])


def format_strategos_tile(forecast_obj: Dict) -> str:
    f = forecast_obj
    fc = f.get("forecast", {})
    fragility = f.get("fragility", "N/A")
    confidence = f.get("confidence", "unscored")
    status = f.get("status", "unlabeled")
    age = forecast_obj.get("age_hours", "N/A")
    age_tag = forecast_obj.get("age_tag", "🕒")

    # Compute trust label
    if isinstance(confidence, float):
        if confidence >= 0.75:
            label = "🟢 Trusted"
        elif confidence >= 0.5:
            label = "⚠️ Moderate"
        else:
            label = "🔴 Fragile"
    else:
        label = "🔘 Unscored"

    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔮 Strategos Forecast Tile
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Trace ID      : {f.get("trace_id")}
Turn          : {f.get("origin_turn")}
Duration      : {f.get("horizon_days")} days
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Exposure Delta:
  NVDA  → {fc.get("end_capital", {}).get("nvda", 0) - fc.get("start_capital", {}).get("nvda", 0):.2f}
  MSFT  → {fc.get("end_capital", {}).get("msft", 0) - fc.get("start_capital", {}).get("msft", 0):.2f}
  IBIT  → {fc.get("end_capital", {}).get("ibit", 0) - fc.get("start_capital", {}).get("ibit", 0):.2f}
  SPY   → {fc.get("end_capital", {}).get("spy", 0) - fc.get("start_capital", {}).get("spy", 0):.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Symbolic Drift:
  {fc.get("symbolic_change")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fragility     : {fragility}
Confidence    : {confidence}
Trust Label   : {label}
Status        : {status}
Age           : {age}h {age_tag}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()
