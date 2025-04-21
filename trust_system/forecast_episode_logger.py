# trust_system/forecast_episode_logger.py
"""
Forecast Episode Logger

Logs symbolic episode metadata per forecast, including:
- Arc label
- Symbolic tag
- Overlay state
- Confidence
- Timestamp

Author: Pulse AI Engine
Version: v1.0.1
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
from collections import Counter

EPISODE_LOG_PATH = "logs/forecast_episodes.jsonl"


def log_episode(forecast: Dict, path: str = EPISODE_LOG_PATH) -> None:
    """
    Log a single symbolic episode to disk.

    Args:
        forecast (Dict): Forecast object
        path (str): JSONL output path
    """
    overlays = forecast.get("forecast", {}).get("symbolic_change") or forecast.get("overlays") or {}
    if not isinstance(overlays, dict):
        overlays = {}

    entry = {
        "forecast_id": forecast.get("trace_id", "unknown"),
        "arc_label": forecast.get("arc_label", "unknown"),
        "symbolic_tag": forecast.get("symbolic_tag", "unknown"),
        "confidence": forecast.get("confidence", None),
        "timestamp": datetime.utcnow().isoformat(),
        "overlays": overlays
    }

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"🧠 Episode logged: {entry['forecast_id']}")
    except Exception as e:
        print(f"❌ Failed to log episode: {e}")


def log_batch_episodes(forecasts: List[Dict], path: str = EPISODE_LOG_PATH) -> None:
    """
    Log a batch of forecasts to the symbolic memory log.

    Args:
        forecasts (List[Dict]): List of forecast entries
        path (str): Path to episode log
    """
    for fc in forecasts:
        log_episode(fc, path=path)


def summarize_episodes(path: str = EPISODE_LOG_PATH) -> Dict[str, int]:
    """
    Summarize symbolic tags and arcs from the log.

    Args:
        path (str): Path to episode log

    Returns:
        Dict[str, int]: Count summary by tag and arc
    """
    if not os.path.exists(path):
        print(f"⚠️ Episode log not found at {path}")
        return {}

    arcs = Counter()
    tags = Counter()
    skipped = 0

    with open(path, "r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                arcs[entry.get("arc_label", "unknown")] += 1
                tags[entry.get("symbolic_tag", "unknown")] += 1
            except Exception:
                skipped += 1
                continue

    summary = {
        "total_episodes": sum(arcs.values()),
        "unique_arcs": len(arcs),
        "unique_tags": len(tags),
        "skipped_entries": skipped,
        **{f"arc_{k}": v for k, v in arcs.items()},
        **{f"tag_{k}": v for k, v in tags.items()}
    }
    return summary


def plot_episode_arcs(path: str = EPISODE_LOG_PATH):
    """
    Show bar chart of arc distribution.

    Args:
        path (str): JSONL episode log
    """
    summary = summarize_episodes(path)
    arcs = {k.replace("arc_", ""): v for k, v in summary.items() if k.startswith("arc_")}
    if not arcs:
        print("❌ No arc data to plot.")
        return

    labels = list(arcs.keys())
    values = list(arcs.values())

    plt.figure(figsize=(10, 4))
    plt.bar(labels, values, color="slateblue", edgecolor="black")
    plt.title("Symbolic Arc Frequency (Episode Memory)")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()
