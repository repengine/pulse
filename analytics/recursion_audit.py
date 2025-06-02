# pulse/recursion_audit.py
"""
Module: recursion_audit.py
Purpose: Compare forecast batches from recursive cycles and summarize Pulse's improvement trajectory.
Analyzes confidence, trust label distributions, retrodiction error, and symbolic arc shifts.

Author: Pulse AI Engine
Version: v0.4.1
"""

from typing import List, Dict, Any
from collections import Counter


def average_confidence(forecasts: List[Dict[str, Any]]) -> float:
    values = [
        f.get("confidence", 0.0)
        for f in forecasts
        if isinstance(f.get("confidence"), (int, float))
    ]
    return round(sum(values) / len(values), 4) if values else 0.0


def average_retrodiction_error(forecasts: List[Dict[str, Any]]) -> float:
    values = [
        f.get("retrodiction_error", 0.0)
        for f in forecasts
        if isinstance(f.get("retrodiction_error"), (int, float))
    ]
    return round(sum(values) / len(values), 4) if values else 0.0


def trust_label_distribution(forecasts: List[Dict[str, Any]]) -> Dict[str, int]:
    labels = [f.get("trust_label", "None") for f in forecasts]
    return dict(Counter(labels))


def symbolic_arc_shift(
    previous: List[Dict[str, Any]], current: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Count how many forecasts changed arc labels between cycles.
    Returns {"same": x, "changed": y, "missing": z}
    """
    changes = {"same": 0, "changed": 0, "missing": 0}
    prev_map = {f.get("trace_id"): f.get("arc_label") for f in previous}
    for f in current:
        tid = f.get("trace_id")
        new_label = f.get("arc_label")
        if tid not in prev_map:
            changes["missing"] += 1
        elif prev_map[tid] == new_label:
            changes["same"] += 1
        else:
            changes["changed"] += 1
    return changes


def generate_recursion_report(
    previous: List[Dict[str, Any]], current: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compare recursive forecast generations and summarize improvement metrics.

    Parameters:
        previous (List[Dict]): Prior forecast batch
        current (List[Dict]): Latest forecast batch

    Returns:
        Dict: Summary statistics and audit metrics
    """
    return {
        "confidence_delta": round(
            average_confidence(current) - average_confidence(previous), 4
        ),
        "retrodiction_error_delta": round(
            average_retrodiction_error(previous) - average_retrodiction_error(current),
            4,
        ),
        "trust_distribution_current": trust_label_distribution(current),
        "arc_shift_summary": symbolic_arc_shift(previous, current),
    }
