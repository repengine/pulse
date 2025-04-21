# symbolic/symbolic_convergence_detector.py

"""
Symbolic Convergence Detector

Scores convergence across forecast arcs/tags:
- Score of 1.0 = total narrative agreement
- Detects symbolic factioning or instability

Author: Pulse AI Engine
Version: v1.0.0
"""

from typing import List, Dict
from collections import Counter
import matplotlib.pyplot as plt


def compute_convergence_score(forecasts: List[Dict], key: str = "arc_label") -> float:
    """
    Measure symbolic convergence: how dominant is the top tag/arc.

    Args:
        forecasts: list of forecast dicts
        key: symbolic field to evaluate ("arc_label" or "symbolic_tag")

    Returns:
        float: convergence score (0–1)
    """
    labels = [f.get(key, "unknown") for f in forecasts]
    if not labels:
        return 0.0

    counts = Counter(labels)
    top = max(counts.values())
    total = len(labels)
    return round(top / total, 3)


def identify_dominant_arcs(forecasts: List[Dict], key: str = "arc_label") -> Dict[str, int]:
    """
    Return sorted label frequency.

    Returns:
        dict: {label → count}
    """
    counts = Counter(f.get(key, "unknown") for f in forecasts)
    return dict(counts.most_common())


def detect_fragmentation(forecasts: List[Dict], key: str = "arc_label") -> bool:
    """
    Detect symbolic narrative fragmentation (no dominant arc).

    Returns:
        bool: True if top arc < 40% of total
    """
    score = compute_convergence_score(forecasts, key)
    return score < 0.4


def plot_convergence_bars(forecasts: List[Dict], key: str = "arc_label", title: str = "Symbolic Convergence"):
    """
    Display a bar chart of arc/tag frequency.

    Args:
        forecasts: forecast set
        key: arc_label or symbolic_tag
    """
    counts = Counter(f.get(key, "unknown") for f in forecasts)
    labels, values = zip(*counts.most_common())

    plt.figure(figsize=(10, 4))
    plt.bar(labels, values, color="steelblue", edgecolor="black")
    plt.title(title)
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()
