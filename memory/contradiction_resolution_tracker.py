"""
contradiction_resolution_tracker.py

Tracks whether detected forecast contradictions were later resolved, reversed, or persisted.
Used for symbolic conflict auditing, memory-based rule validation, and trust score adjustments.

Author: Pulse v0.41
"""

import os
import json
from typing import Dict, Optional
from core.path_registry import PATHS
from memory.forecast_memory import ForecastMemory

RESOLUTION_LOG = PATHS.get(
    "CONTRADICTION_RESOLUTION_LOG", "logs/contradiction_resolution_log.jsonl"
)


def compare_symbolic_outcomes(fc1: Dict, fc2: Dict) -> str:
    arc1 = fc1.get("arc_label", "unknown")
    arc2 = fc2.get("arc_label", "unknown")
    tag1 = fc1.get("symbolic_tag", "none")
    tag2 = fc2.get("symbolic_tag", "none")
    if arc1 == arc2 and tag1 == tag2:
        return "✅ Resolved"
    elif arc1 != arc2 and tag1 != tag2:
        return "↔️ Still Contradictory"
    else:
        return "🌀 Partial Alignment"


def track_resolution(
    trace_id_1: str, trace_id_2: str, memory: Optional[ForecastMemory] = None
) -> Optional[str]:
    memory = memory or ForecastMemory()
    f1 = memory.find_by_trace_id(trace_id_1)
    f2 = memory.find_by_trace_id(trace_id_2)
    if not f1 or not f2:
        return None
    outcome = compare_symbolic_outcomes(f1, f2)
    log_resolution_outcome(trace_id_1, trace_id_2, outcome)
    return outcome


def log_resolution_outcome(tid1: str, tid2: str, status: str):
    os.makedirs(os.path.dirname(RESOLUTION_LOG), exist_ok=True)
    with open(RESOLUTION_LOG, "a", encoding="utf-8") as f:
        f.write(
            json.dumps({"trace_id_1": tid1, "trace_id_2": tid2, "status": status})
            + "\n"
        )


def summarize_resolution_outcomes(path: str = str(RESOLUTION_LOG)) -> Dict[str, int]:
    if not os.path.exists(path):
        return {}
    counts = {"✅ Resolved": 0, "↔️ Still Contradictory": 0, "🌀 Partial Alignment": 0}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                counts[entry.get("status")] += 1
            except Exception:
                continue
    return counts


if __name__ == "__main__":
    mem = ForecastMemory()
    res = track_resolution("T1", "T2", memory=mem)
    print(f"Resolution Status: {res}")
    print("Summary:", summarize_resolution_outcomes())
