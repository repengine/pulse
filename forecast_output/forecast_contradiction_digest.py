"""
forecast_contradiction_digest.py

Displays a digest of recent contradictions found in Pulse forecasts.
Used for trust diagnostics, UI summary panes, and learning loop review.

Author: Pulse v0.37
"""

import os
import json
from collections import defaultdict
from typing import List, Dict
from engine.path_registry import PATHS

CONTRADICTION_LOG_PATH = PATHS.get(
    "CONTRADICTION_LOG_PATH", "logs/forecast_contradiction_log.jsonl"
)


def load_contradiction_log(limit: int = 20) -> List[Dict]:
    if not os.path.exists(CONTRADICTION_LOG_PATH):
        return []
    try:
        with open(CONTRADICTION_LOG_PATH, "r") as f:
            lines = [json.loads(line) for line in f.readlines()]
        return lines[-limit:]
    except Exception as e:
        print(f"[ContradictionDigest] Load error: {e}")
        return []


def group_by_reason(logs: List[Dict]) -> Dict[str, List[Dict]]:
    grouped = defaultdict(list)
    for entry in logs:
        grouped[entry.get("reason", "unknown")].append(entry)
    return dict(grouped)


def render_digest(logs: List[Dict]):
    if not logs:
        print("No contradictions found.")
        return
    print("\n🚨 Forecast Contradiction Digest (latest entries):\n")
    grouped = group_by_reason(logs)
    for reason, items in grouped.items():
        print(f"❗ {reason} ({len(items)} pair(s))")
        for entry in items:
            print(f" - {entry['trace_id_1']} vs {entry['trace_id_2']}")
        print("---")


if __name__ == "__main__":
    logs = load_contradiction_log(limit=25)
    render_digest(logs)
