"""
PATCHED: strategos_tile_formatter.py
Pulse Version: v0.022.2
Enhancement: Adds symbolic arc and score to Strategos Forecast Tile
Includes: sys.path fix for standalone or non-package runs
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "pulse", "main", "symbolic_system")))

from typing import Dict

def format_strategos_tile(forecast_obj: Dict) -> str:
    f = forecast_obj
    fc = f.get("forecast", {})
    alignment = f.get("alignment", {})
    fragility = f.get("fragility", "N/A")
    confidence = f.get("confidence", "unscored")
    status = f.get("status", "unlabeled")
    arc = f.get("arc_label", "Neutral")
    symbolic_score = f.get("symbolic_score", "N/A")
    age = forecast_obj.get("age_hours", "N/A")
    age_tag = forecast_obj.get("age_tag", "🕒")

    if isinstance(confidence, float):
        if confidence >= 0.75:
            trust_label = "🟢 Trusted"
        elif confidence >= 0.5:
            trust_label = "⚠️ Moderate"
        else:
            trust_label = "🔴 Fragile"
    else:
        trust_label = "🔘 Unscored"

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
Symbolic Drift : {fc.get("symbolic_change")}
Narrative Arc  : {arc}
Symbolic Score : {symbolic_score}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fragility     : {fragility}
Confidence    : {confidence}
Trust Label   : {trust_label}
Status        : {status}
Age           : {age}h {age_tag}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()
