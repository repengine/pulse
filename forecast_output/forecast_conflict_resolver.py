"""
forecast_conflict_resolver.py

Resolves conflicting forecasts by confidence or other heuristics.

Usage:
    resolved = resolve_conflicts(forecast_list)
"""

from typing import List, Dict

def resolve_conflicts(forecasts: List[Dict]) -> List[Dict]:
    """
    Returns a list of non-conflicting forecasts, preferring higher confidence.
    """
    seen = {}
    for f in forecasts:
        key = f.get("symbolic_tag", "") + str(f.get("drivers", ""))
        if key not in seen or f.get("confidence", 0) > seen[key].get("confidence", 0):
            seen[key] = f
    return list(seen.values())
