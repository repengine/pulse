"""
symbolic_alignment_engine.py

Compares symbolic tags with simulation variables for alignment analysis.

Usage:
    score = compute_alignment("Hope Rising", {"capital_delta": 100})
    report = alignment_report("Hope Rising", {"capital_delta": 100})
    batch = batch_alignment_report([("Hope Rising", {"capital_delta": 100}), ...])
"""

from typing import Dict, Any, List, Tuple


def compute_alignment(symbolic_tag: str, variables: Dict[str, Any]) -> float:
    """
    Returns an alignment score (0.0–1.0) between symbolic tag and variable state.
    """
    try:
        if (
            symbolic_tag.lower().startswith("hope")
            and variables.get("capital_delta", 0) > 0
        ):
            return 1.0
        if (
            symbolic_tag.lower().startswith("despair")
            and variables.get("capital_delta", 0) < 0
        ):
            return 1.0
        # Add more rules as needed
        return 0.5  # Neutral/unknown
    except Exception:
        return 0.0


def alignment_report(tag: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    score = compute_alignment(tag, variables)
    return {"symbolic_tag": tag, "alignment_score": score, "variables": variables}


def batch_alignment_report(
    pairs: List[Tuple[str, Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    return [alignment_report(tag, vars) for tag, vars in pairs]
