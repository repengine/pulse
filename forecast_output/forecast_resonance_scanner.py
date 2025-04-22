# forecasting/forecast_resonance_scanner.py

"""
Forecast Resonance Scanner

Detects symbolic alignment clusters within a forecast batch.
Useful for identifying convergence zones and stable narrative sets.

Author: Pulse AI Engine
Version: v1.0.0
"""

from typing import List, Dict
from collections import defaultdict, Counter


def cluster_resonant_forecasts(forecasts: List[Dict], key: str = "arc_label") -> Dict[str, List[Dict]]:
    """
    Group forecasts that share the same arc/tag label.

    Args:
        forecasts: List of forecast dicts
        key: symbolic field to group by

    Returns:
        Dict[str, List[Dict]]: symbolic groupings
    """
    clusters = defaultdict(list)
    for fc in forecasts:
        if not isinstance(fc, dict):
            continue
        label = fc.get(key, "unknown")
        clusters[label].append(fc)
    return dict(clusters)


def score_resonance(forecasts: List[Dict], key: str = "arc_label") -> float:
    """
    Score symbolic resonance from 0–1.0 (higher = more convergence)

    Args:
        forecasts: List of forecast dicts
        key: symbolic field to score

    Returns:
        float: fraction of forecasts in top arc/tag
    """
    labels = [f.get(key, "unknown") for f in forecasts if isinstance(f, dict)]
    if not labels:
        return 0.0
    top = Counter(labels).most_common(1)[0][1]
    return round(top / len(labels), 3)


def detect_consensus_themes(forecasts: List[Dict], key: str = "arc_label") -> List[str]:
    """
    Return top 3 most common symbolic labels.

    Args:
        forecasts: List of forecast dicts
        key: symbolic field to analyze

    Returns:
        List[str]
    """
    counts = Counter(f.get(key, "unknown") for f in forecasts if isinstance(f, dict))
    return [k for k, _ in counts.most_common(3)]


def generate_resonance_summary(forecasts: List[Dict], key: str = "arc_label") -> Dict:
    """
    Return symbolic alignment summary across batch.

    Args:
        forecasts: List of forecast dicts
        key: symbolic field to analyze

    Returns:
        {
            resonance_score: float,
            top_themes: List[str],
            cluster_sizes: Dict[str, int],
            dominant_arc: str
        }
    """
    if not isinstance(forecasts, list):
        raise ValueError("Input forecasts must be a list of dicts")
    score = score_resonance(forecasts, key=key)
    clusters = cluster_resonant_forecasts(forecasts, key=key)
    top_themes = detect_consensus_themes(forecasts, key=key)
    return {
        "resonance_score": score,
        "top_themes": top_themes,
        "cluster_sizes": {k: len(v) for k, v in clusters.items()},
        "dominant_arc": top_themes[0] if top_themes else "unknown"
    }


# --- Simple test for robustness ---
if __name__ == "__main__":
    # Minimal test: 3 forecasts, 2 with same arc_label
    test_forecasts = [
        {"arc_label": "Hope Surge", "confidence": 0.8},
        {"arc_label": "Hope Surge", "confidence": 0.7},
        {"arc_label": "Collapse Risk", "confidence": 0.4},
        {},  # malformed
        "notadict",  # malformed
    ]
    summary = generate_resonance_summary(test_forecasts, key="arc_label")
    print("Resonance summary:", summary)
