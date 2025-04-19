"""
pulse_forecast_lineage.py

Tracks ancestry and influence of forecasts, detects drift, generates forecast trees, flags divergence.

Author: Pulse AI Engine
"""

from typing import List, Dict

def build_forecast_lineage(forecasts: List[Dict]) -> Dict[str, List[str]]:
    """
    Build a mapping from forecast_id to its children (descendants).
    """
    lineage = {}
    for f in forecasts:
        parent = f.get("parent_id")
        if parent:
            lineage.setdefault(parent, []).append(f.get("trace_id"))
    return lineage

def detect_drift(forecasts: List[Dict]) -> List[str]:
    """
    Detects drift in symbolic arc or trust label over time.
    """
    drifts = []
    for i in range(1, len(forecasts)):
        prev = forecasts[i-1]
        curr = forecasts[i]
        if prev.get("symbolic_tag") != curr.get("symbolic_tag"):
            drifts.append(f"Drift: {prev.get('trace_id')} → {curr.get('trace_id')}")
    return drifts

def flag_divergence(forecasts: List[Dict]) -> List[str]:
    """
    Flags divergence forks for operator review.
    """
    forks = []
    seen = set()
    for f in forecasts:
        parent = f.get("parent_id")
        if parent and parent in seen:
            forks.append(f"Divergence: {f.get('trace_id')} from parent {parent}")
        seen.add(f.get("trace_id"))
    return forks
