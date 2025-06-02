# forecast_output/forecast_divergence_detector.py

"""
Forecast Divergence Detector

Detects symbolic contradictions or splits within a forecast batch.
Highlights arc/tag polarity, forks, or unstable divergence patterns.

Author: Pulse AI Engine
Version: v1.0.0
"""

from typing import List, Dict, Tuple, Any
from collections import Counter


# Optional: symbolic opposition map
OPPOSING_ARCS = {
    "Hope Surge": "Collapse Risk",
    "Collapse Risk": "Hope Surge",
    "Stabilization": "Despair Drop",
    "Despair Drop": "Stabilization",
    "Reconstruction": "Fatigue Loop",
}


def detect_symbolic_opposition(
    forecasts: List[Dict[str, Any]], key: str = "arc_label"
) -> List[Tuple[str, str]]:
    if not isinstance(forecasts, list):
        raise ValueError("Input forecasts must be a list")
    """
    Identify active symbolic oppositions in the batch.

    Returns:
        List of (a, b) arc/tag opposition pairs both present
    """
    labels = {f.get(key, "unknown") for f in forecasts}
    return [(a, b) for a, b in OPPOSING_ARCS.items() if a in labels and b in labels]


def score_batch_divergence(
    forecasts: List[Dict[str, Any]], key: str = "arc_label"
) -> float:
    if not isinstance(forecasts, list):
        raise ValueError("Input forecasts must be a list")
    """
    Score polarization: 1.0 = max narrative opposition.

    Returns:
        float
    """
    labels = [f.get(key, "unknown") for f in forecasts]
    if not labels:
        return 0.0
    counts = Counter(labels)
    total = len(labels)
    top_two = counts.most_common(2)
    if len(top_two) < 2:
        return 0.0
    a, b = top_two[0][1], top_two[1][1]
    return round((a / total) * (b / total), 3)


def group_conflicting_forecasts(
    forecasts: List[Dict[str, Any]], key: str = "arc_label"
) -> Dict[str, List[Dict[str, Any]]]:
    if not isinstance(forecasts, list):
        raise ValueError("Input forecasts must be a list")
    """
    Return {symbolic_label: [forecasts]} for oppositional arcs/tags.
    """
    active_conflicts = detect_symbolic_opposition(forecasts, key=key)
    group: Dict[str, List[Dict[str, Any]]] = {
        label: [] for pair in active_conflicts for label in pair
    }
    for f in forecasts:
        label = f.get(key, "unknown")
        if label in group:
            group[label].append(f)
    return group


def generate_divergence_report(
    forecasts: List[Dict[str, Any]], key: str = "arc_label"
) -> Dict[str, Any]:
    """
    Return symbolic divergence summary.

    Returns:
        Dict: {conflicts, divergence_score, cluster_sizes}
    """
    conflicts = detect_symbolic_opposition(forecasts, key)
    score = score_batch_divergence(forecasts, key)
    conflict_groups = group_conflicting_forecasts(forecasts, key)

    return {
        "divergence_score": score,
        "symbolic_conflicts": conflicts,
        "cluster_sizes": {k: len(v) for k, v in conflict_groups.items()},
    }


def _test_forecast_divergence_detector() -> None:
    dummy = [
        {"arc_label": "Hope Surge"},
        {"arc_label": "Collapse Risk"},
        {"arc_label": "Hope Surge"},
    ]
    report = generate_divergence_report(dummy)
    assert "divergence_score" in report
    assert isinstance(report["symbolic_conflicts"], list)
    print("✅ Forecast divergence detector test passed.")


if __name__ == "__main__":
    _test_forecast_divergence_detector()
