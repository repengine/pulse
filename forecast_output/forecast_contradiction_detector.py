"""
Module: forecast_contradiction_detector.py
Pulse Version: v0.019.0
Location: pulse/forecast_output/
Last Updated: 2025-04-17
Author: Pulse AI Engine

Description:
Detects logical contradictions across multiple foresight forecasts.
Flags paradoxes in symbolic state, capital movement, or forecast metadata.
Flags divergence forks for operator review.

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
from collections import defaultdict
from core.path_registry import PATHS
from core.pulse_learning_log import log_learning_event  # 🧠 Enhancement 2

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

CONTRADICTION_LOG_PATH = PATHS.get(
    "CONTRADICTION_LOG_PATH", "logs/forecast_contradiction_log.jsonl"
)


def ensure_log_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def detect_forecast_contradictions(forecasts: List[Dict]) -> List[Tuple[str, str, str]]:
    """
    Detects contradictions across a set of forecasts.
    Flags divergence forks for operator review.

    Returns:
        List of (trace_id_1, trace_id_2, reason) tuples
    """
    ensure_log_dir(str(CONTRADICTION_LOG_PATH))
    contradictions = []

    # Track which forecasts are involved in contradictions for status escalation
    contradiction_pairs = []

    # Group forecasts by origin_turn
    grouped = defaultdict(list)
    for f in forecasts:
        grouped[f.get("origin_turn", -1)].append(f)

    for turn, group in grouped.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                f1 = group[i]
                f2 = group[j]
                id1 = f1.get("trace_id", f"f_{i}")
                id2 = f2.get("trace_id", f"f_{j}")

                # Contradiction condition: same start state, opposite outcome
                end1 = f1.get("forecast", {}).get("end_capital", {})
                end2 = f2.get("forecast", {}).get("end_capital", {})
                for asset in end1:
                    if asset in end2:
                        delta = end1[asset] - end2[asset]
                        if abs(delta) > 1000:  # Highly divergent outcome
                            contradictions.append(
                                (id1, id2, f"Conflict on {asset} (${delta:.2f})")
                            )
                            contradiction_pairs.append(
                                (
                                    forecasts.index(f1),
                                    forecasts.index(f2),
                                    f"Conflict on {asset} (${delta:.2f})",
                                )
                            )

                # Symbolic contradictions
                sym1 = f1.get("forecast", {}).get("symbolic_change", {})
                sym2 = f2.get("forecast", {}).get("symbolic_change", {})
                if sym1 and sym2:
                    hope_gap = abs(sym1.get("hope", 0.5) - sym2.get("hope", 0.5))
                    despair_gap = abs(
                        sym1.get("despair", 0.5) - sym2.get("despair", 0.5)
                    )
                    if hope_gap > 0.6 and despair_gap > 0.6:
                        contradictions.append(
                            (id1, id2, "Symbolic paradox: Hope vs Despair divergence")
                        )
                        contradiction_pairs.append(
                            (
                                forecasts.index(f1),
                                forecasts.index(f2),
                                "Symbolic paradox: Hope vs Despair divergence",
                            )
                        )

                # Divergence fork flag
                if f1.get("parent_id") == f2.get("parent_id") and id1 != id2:
                    contradictions.append(
                        (id1, id2, "Divergence fork from same parent")
                    )
                    contradiction_pairs.append(
                        (
                            forecasts.index(f1),
                            forecasts.index(f2),
                            "Divergence fork from same parent",
                        )
                    )

    # 🧠 Escalate to Trust Engine: Mark involved forecasts as contradictory
    for i, j, reason in contradiction_pairs:
        for idx in (i, j):
            if 0 <= idx < len(forecasts):
                forecasts[idx]["confidence_status"] = "❌ Contradictory"
        # 🧠 Log to pulse_learning_log.py
        try:
            log_learning_event(
                "forecast_contradiction_detected",
                {
                    "trace_id_1": forecasts[i].get("trace_id", f"f_{i}"),
                    "trace_id_2": forecasts[j].get("trace_id", f"f_{j}"),
                    "reason": reason,
                },
            )
        except Exception as e:
            print(f"[ContradictionDetector] Learning log error: {e}")

    # Log contradictions
    try:
        with open(CONTRADICTION_LOG_PATH, "a") as f:
            for c in contradictions:
                f.write(
                    json.dumps(
                        {
                            "trace_id_1": c[0],
                            "trace_id_2": c[1],
                            "reason": c[2],
                            "timestamp": datetime.utcnow().isoformat(),
                            "metadata": {
                                "source": "forecast_contradiction_detector.py",
                                "version": "v0.019.0",
                            },
                        }
                    )
                    + "\n"
                )
    except Exception as e:
        print(f"[ContradictionDetector] Log error: {e}")

    return contradictions


# Example test
if __name__ == "__main__":
    # Two forecasts with same origin and diverging symbolic + capital outputs
    f1 = {
        "trace_id": "F001",
        "origin_turn": 5,
        "forecast": {
            "end_capital": {"nvda": 10000},
            "symbolic_change": {"hope": 0.8, "despair": 0.1},
        },
    }
    f2 = {
        "trace_id": "F002",
        "origin_turn": 5,
        "forecast": {
            "end_capital": {"nvda": 8700},
            "symbolic_change": {"hope": 0.1, "despair": 0.9},
        },
    }
    contradictions = detect_forecast_contradictions([f1, f2])
    for c in contradictions:
        print(f"❗ Contradiction: {c}")
