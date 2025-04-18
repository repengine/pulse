"""
Module: forecast_contradiction_detector.py
Pulse Version: v0.019.0
Location: pulse/forecast_output/
Last Updated: 2025-04-17
Author: Pulse AI Engine

Description:
Detects logical contradictions across multiple foresight forecasts.
Flags paradoxes in symbolic state, capital movement, or forecast metadata.

Used by:
- PulseMirror
- Strategos Digest Validator
- PFPA Audit Layer

Log Output:
- logs/forecast_contradiction_log.jsonl
"""

import json
import os
from typing import List, Dict, Tuple
from datetime import datetime

CONTRADICTION_LOG_PATH = "logs/forecast_contradiction_log.jsonl"

def ensure_log_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def detect_forecast_contradictions(forecasts: List[Dict]) -> List[Tuple[str, str, str]]:
    """
    Detects contradictions across a set of forecasts.

    Returns:
        List of (trace_id_1, trace_id_2, reason) tuples
    """
    ensure_log_dir(CONTRADICTION_LOG_PATH)
    contradictions = []

    for i in range(len(forecasts)):
        for j in range(i + 1, len(forecasts)):
            f1 = forecasts[i]
            f2 = forecasts[j]
            id1 = f1.get("trace_id", f"f_{i}")
            id2 = f2.get("trace_id", f"f_{j}")

            # Contradiction condition: same start state, opposite outcome
            if f1.get("origin_turn") == f2.get("origin_turn"):
                end1 = f1.get("forecast", {}).get("end_capital", {})
                end2 = f2.get("forecast", {}).get("end_capital", {})
                for asset in end1:
                    if asset in end2:
                        delta = end1[asset] - end2[asset]
                        if abs(delta) > 1000:  # Highly divergent outcome
                            contradictions.append((id1, id2, f"Conflict on {asset} (${delta:.2f})"))

            # Symbolic contradictions
            sym1 = f1.get("forecast", {}).get("symbolic_change", {})
            sym2 = f2.get("forecast", {}).get("symbolic_change", {})
            if sym1 and sym2:
                hope_gap = abs(sym1.get("hope", 0.5) - sym2.get("hope", 0.5))
                despair_gap = abs(sym1.get("despair", 0.5) - sym2.get("despair", 0.5))
                if hope_gap > 0.6 and despair_gap > 0.6:
                    contradictions.append((id1, id2, "Symbolic paradox: Hope vs Despair divergence"))

    # Log contradictions
    try:
        with open(CONTRADICTION_LOG_PATH, "a") as f:
            for c in contradictions:
                f.write(json.dumps({
                    "trace_id_1": c[0],
                    "trace_id_2": c[1],
                    "reason": c[2],
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {
                        "source": "forecast_contradiction_detector.py",
                        "version": "v0.019.0"
                    }
                }) + "\n")
    except Exception as e:
        print(f"[ContradictionDetector] Log error: {e}")

    return contradictions

# Example test
if __name__ == "__main__":
    # Two forecasts with same origin and diverging symbolic + capital outputs
    f1 = {"trace_id": "F001", "origin_turn": 5, "forecast": {"end_capital": {"nvda": 10000}, "symbolic_change": {"hope": 0.8, "despair": 0.1}}}
    f2 = {"trace_id": "F002", "origin_turn": 5, "forecast": {"end_capital": {"nvda": 8700}, "symbolic_change": {"hope": 0.1, "despair": 0.9}}}
    contradictions = detect_forecast_contradictions([f1, f2])
    for c in contradictions:
        print(f"❗ Contradiction: {c}")
