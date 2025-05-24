"""
Module: symbolic_trace_scorer.py
Pulse Version: v0.022.1
Location: pulse/main/symbolic_system/
Last Updated: 2025-04-17
Author: Pulse AI Engine

Description:
Scores symbolic trace histories for narrative coherence, symbolic instability, and emotional arc structure.
Used by PFPA, Strategos Tile Formatter, Forecast Summary Synthesis, and Symbolic Diagnostics.

Inputs:
- List[Dict[str, float]] — symbolic overlays per turn

Outputs:
- symbolic_score: float (0–1)
- arc_label: str (e.g. "Hope Arc", "Fatigue Collapse", "Whiplash")
- volatility_score: float
- arc_certainty: float

Log Output:
- logs/symbolic_trace_scores.jsonl
"""

import json
import os
from typing import List, Dict
from datetime import datetime

SCORE_LOG_PATH = "logs/symbolic_trace_scores.jsonl"


def ensure_log_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def score_symbolic_trace(trace: List[Dict[str, float]]) -> Dict:
    """
    Scores a symbolic trace across turns for emotional coherence, volatility, and arc shape.
    """
    ensure_log_dir(SCORE_LOG_PATH)
    if not trace:
        return {
            "symbolic_score": 0.0,
            "arc_label": "Empty",
            "volatility_score": 0.0,
            "arc_certainty": 0.0,
            "turns": 0,
        }

    hope_vals = [t.get("hope", 0.5) for t in trace]
    fatigue_vals = [t.get("fatigue", 0.5) for t in trace]
    rage_vals = [t.get("rage", 0.5) for t in trace]
    despair_vals = [t.get("despair", 0.5) for t in trace]

    def delta_avg(values: List[float]) -> float:
        return sum(abs(values[i + 1] - values[i]) for i in range(len(values) - 1)) / (
            len(values) - 1
        )

    def trend_direction(values: List[float]) -> str:
        return "up" if values[-1] > values[0] else "down"

    volatility = (
        delta_avg(hope_vals)
        + delta_avg(fatigue_vals)
        + delta_avg(rage_vals)
        + delta_avg(despair_vals)
    ) / 4.0

    arc = "Neutral"
    if trend_direction(hope_vals) == "up" and max(hope_vals) > 0.7:
        arc = "Hope Arc"
    elif trend_direction(fatigue_vals) == "up" and max(fatigue_vals) > 0.7:
        arc = "Fatigue Collapse"
    elif volatility > 0.25:
        arc = "Symbolic Whiplash"
    elif (
        trend_direction(despair_vals) == "down"
        and despair_vals[0] > 0.6
        and despair_vals[-1] < 0.4
    ):
        arc = "Recovery Arc"

    symbolic_score = round(1.0 - min(volatility * 1.2, 1.0), 4)
    arc_certainty = round(1.0 - min(volatility * 2.0, 1.0), 4)

    result = {
        "symbolic_score": symbolic_score,
        "arc_certainty": arc_certainty,
        "arc_label": arc,
        "volatility_score": round(volatility, 4),
        "turns": len(trace),
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {"version": "v0.022.1", "source": "symbolic_trace_scorer.py"},
    }

    try:
        with open(SCORE_LOG_PATH, "a") as f:
            f.write(json.dumps(result) + "\n")
    except Exception as e:
        print(f"[TraceScorer] Log error: {e}")

    return result


# === Example usage
if __name__ == "__main__":
    example_trace = [
        {"hope": 0.5, "fatigue": 0.4, "rage": 0.3, "despair": 0.6},
        {"hope": 0.55, "fatigue": 0.42, "rage": 0.32, "despair": 0.52},
        {"hope": 0.68, "fatigue": 0.38, "rage": 0.34, "despair": 0.42},
        {"hope": 0.78, "fatigue": 0.35, "rage": 0.33, "despair": 0.28},
    ]
    score = score_symbolic_trace(example_trace)
    print("Arc:", score["arc_label"], "| Symbolic Score:", score["symbolic_score"])
