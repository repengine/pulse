# pulse/symbolic_analysis/pulse_symbolic_arc_tracker.py
"""
Module: pulse_symbolic_arc_tracker.py
Tracks symbolic arc distribution and change over time across forecast batches.

Features:
- Arc frequency counting
- Arc drift comparison between batches
- Arc stability scoring
- Exportable summary
- Optional matplotlib plot

Author: Pulse AI Engine
Version: v0.1.0
"""

import json
from typing import List, Dict, Optional
from collections import Counter
import matplotlib.pyplot as plt
import os

def track_symbolic_arcs(forecasts: List[Dict]) -> Dict[str, int]:
    """
    Count the number of times each symbolic arc label appears in a forecast batch.

    Args:
        forecasts (List[Dict]): List of forecast dicts.

    Returns:
        Dict[str, int]: Dictionary mapping arc labels to counts.
    """
    arc_counts = Counter()
    for f in forecasts:
        arc = f.get("arc_label", "Unknown")
        arc_counts[arc] += 1
    return dict(arc_counts)


def compare_arc_drift(prev: List[Dict], curr: List[Dict]) -> Dict[str, float]:
    """
    Compare two forecast batches for arc label change over time.

    Args:
        prev (List[Dict]): Previous batch of forecasts.
        curr (List[Dict]): Current batch of forecasts.

    Returns:
        Dict[str, float]: Percent change per arc label.
    """
    prev_counts = track_symbolic_arcs(prev)
    curr_counts = track_symbolic_arcs(curr)

    all_arcs = set(prev_counts.keys()).union(curr_counts.keys())
    drift = {}
    for arc in all_arcs:
        p = prev_counts.get(arc, 0)
        c = curr_counts.get(arc, 0)
        if p == 0:
            drift[arc] = 100.0 if c > 0 else 0.0
        else:
            drift[arc] = round(((c - p) / p) * 100, 2)
    return drift


def compute_arc_stability(drift: Dict[str, float]) -> float:
    """
    Quantify overall arc stability (lower = more stable).

    Args:
        drift (Dict[str, float]): Output from compare_arc_drift.

    Returns:
        float: Average absolute drift percentage.
    """
    if not drift:
        return 0.0
    return round(sum(abs(v) for v in drift.values()) / len(drift), 2)


def export_arc_summary(arc_counts: Dict[str, int], path: str) -> None:
    """
    Save arc count dictionary to JSON.

    Args:
        arc_counts (Dict[str, int]): Arc label count dictionary.
        path (str): Path to save JSON forecast_output.
    """
    try:
        with open(path, "w") as f:
            json.dump(arc_counts, f, indent=2)
        print(f"✅ Arc summary exported to {path}")
    except Exception as e:
        print(f"❌ Failed to save arc summary: {e}")


def plot_arc_distribution(arc_counts: Dict[str, int], title: Optional[str] = "Symbolic Arc Distribution", export_path: Optional[str] = None) -> None:
    """
    Plot arc label distribution as a bar chart.

    Args:
        arc_counts (Dict[str, int]): Arc label count dictionary.
        title (str): Plot title.
        export_path (Optional[str]): If given, save plot to this path.
    """
    try:
        labels = list(arc_counts.keys())
        values = list(arc_counts.values())
        plt.figure(figsize=(8, 4))
        plt.bar(labels, values, color="skyblue", edgecolor="black")
        safe_title = title if title is not None else "Symbolic Arc Distribution"
        plt.title(safe_title)
        plt.xlabel("Arc Label")
        plt.ylabel("Count")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        if export_path:
            plt.savefig(export_path)
            print(f"📊 Arc plot saved to {export_path}")
        else:
            plt.show()
    except Exception as e:
        print(f"❌ Failed to plot arc distribution: {e}")

def compute_arc_label(forecast: Dict) -> str:
    """
    Assign a symbolic arc label to a forecast based on its symbolic_tag or drivers.

    Args:
        forecast (Dict): Forecast object.

    Returns:
        str: Arc label string.
    """
    tag = forecast.get("symbolic_tag", "").lower()
    if "hope" in tag:
        return "arc_hope_recovery"
    if "despair" in tag:
        return "arc_despair_decline"
    if "rage" in tag:
        return "arc_instability"
    if "fatigue" in tag:
        return "arc_exhaustion"
    if "trust" in tag:
        return "arc_stability"
    return "arc_unknown"
