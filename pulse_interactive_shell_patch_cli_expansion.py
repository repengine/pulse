"""
PATCHED: pulse_interactive_shell.py
Pulse Version: v0.22.5
Adds:
- score-trace [file]        → Runs symbolic trace scorer
- audit-forecast [file]     → Runs confidence + contradiction audit
- digest-tile [file]        → Renders Strategos Forecast Tiles
"""

import sys, os, json
from typing import List
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "pulse")))

from symbolic_system.symbolic_trace_scorer import score_symbolic_trace
from forecast_output.forecast_confidence_gate import filter_by_confidence
from forecast_output.forecast_contradiction_detector import detect_forecast_contradictions
from forecast_output.strategos_tile_formatter import format_strategos_tile

def log_interaction(command: str, result: str):
    print(f"[LOG] {command} → {result}")

def cmd_score_trace(args: List[str]):
    """Score symbolic memory log using trace scorer"""
    if not args:
        print("Usage: score-trace [file]")
        return
    try:
        with open(args[0], "r") as f:
            trace = [json.loads(line) for line in f.readlines() if line.strip()]
        result = score_symbolic_trace(trace)
        print(f"🧠 Arc: {result['arc_label']} | Score: {result['symbolic_score']} | Certainty: {result['arc_certainty']}")
        log_interaction("score-trace", result["arc_label"])
    except Exception as e:
        print("Error:", e)

def cmd_audit_forecast(args: List[str]):
    """Run confidence gate + contradiction detector on forecast set"""
    if not args:
        print("Usage: audit-forecast [file]")
        return
    try:
        with open(args[0], "r") as f:
            forecasts = [json.loads(line) for line in f.readlines() if line.strip()]
        filtered = filter_by_confidence(forecasts)
        contradictions = detect_forecast_contradictions(filtered)
        print(f"✅ Filtered: {len(filtered)} forecasts")
        for c in contradictions:
            print(f"❗ Contradiction: {c}")
        log_interaction("audit-forecast", f"{len(filtered)} ok, {len(contradictions)} flagged")
    except Exception as e:
        print("Error:", e)

def cmd_digest_tile(args: List[str]):
    """Render Strategos Forecast Tile(s)"""
    if not args:
        print("Usage: digest-tile [file]")
        return
    try:
        with open(args[0], "r") as f:
            forecasts = [json.loads(line) for line in f.readlines() if line.strip()]
        for fc in forecasts:
            print(format_strategos_tile(fc))
        log_interaction("digest-tile", f"{len(forecasts)} rendered")
    except Exception as e:
        print("Error:", e)

# To register:
# "score-trace": cmd_score_trace,
# "audit-forecast": cmd_audit_forecast,
# "digest-tile": cmd_digest_tile
