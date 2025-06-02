"""
Module: forecast_drift_monitor.py
Pulse Version: v0.22.1
Last Updated: 2025-04-16
Author: Pulse AI Engine

Description:
Compares symbolic-tagged forecast cluster summaries from two runs.
Detects narrative drift or symbolic trust volatility.

Inputs:
- before_run: List[Dict] of clusters from first forecast run
- after_run: List[Dict] of clusters from second forecast run

Outputs:
- Drift score
- Symbolic flip warnings (e.g., Hope -> Despair)
- Per-tag delta for interpretability

Log Output:
- logs/forecast_drift_log.jsonl

Enhancements:
- Symbolic delta per tag
- Input validation
- Robust handling of partial/missing clusters
- Metadata tagging
- Human-readable summary for UI piping

Status: ✅ Enhanced + Ready
"""

import json
import os
from typing import List, Dict, Optional
from utils.log_utils import get_logger
from engine.path_registry import PATHS

logger = get_logger(__name__)

DRIFT_LOG_PATH = PATHS.get(
    "DRIFT_LOG_PATH",
    os.path.join(PATHS["WORLDSTATE_LOG_DIR"], "forecast_drift_log.jsonl"),
)


def ensure_log_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def normalize_forecast_clusters(clusters: List[Dict]) -> Dict[str, Dict]:
    norm = {}
    for entry in clusters:
        tag = entry.get("tag")
        conf = entry.get("avg_confidence", 0.5)
        if tag and isinstance(conf, (int, float)):
            norm[tag] = {
                "avg_confidence": round(conf, 4),
                "count": entry.get("count", None),
            }
    return norm


def score_drift(before: Dict[str, Dict], after: Dict[str, Dict]) -> Dict:
    drift_total = 0.0
    tag_deltas = {}
    all_tags = set(before) | set(after)

    for tag in all_tags:
        b = before.get(tag, {"avg_confidence": 0.5})["avg_confidence"]
        a = after.get(tag, {"avg_confidence": 0.5})["avg_confidence"]
        delta = round(a - b, 4)
        drift_total += abs(delta)
        tag_deltas[tag] = delta

    drift_score = round(drift_total / len(all_tags), 4)
    return {"drift_score": drift_score, "tag_deltas": tag_deltas}


def compare_forecast_clusters(
    before_run: List[Dict],
    after_run: List[Dict],
    run_id: str = "default",
    log_path: Optional[str] = None,
) -> Dict:
    path = str(log_path or DRIFT_LOG_PATH)
    ensure_log_dir(path)

    before = normalize_forecast_clusters(before_run)
    after = normalize_forecast_clusters(after_run)
    drift_metrics = score_drift(before, after)

    symbolic_flips = [
        tag
        for tag in drift_metrics["tag_deltas"]
        if (
            tag in before
            and tag in after
            and before.get(tag, {}).get("avg_confidence", 0.5) > 0.6
            and after.get(tag, {}).get("avg_confidence", 0.5) < 0.4
        )
    ]

    result = {
        "run_id": run_id,
        "drift_score": drift_metrics["drift_score"],
        "tag_deltas": drift_metrics["tag_deltas"],
        "symbolic_flips": symbolic_flips,
        "metadata": {"version": "v0.22.1", "source": "forecast_drift_monitor.py"},
    }

    try:
        with open(path, "a") as f:
            f.write(json.dumps(result) + "\n")
    except Exception as e:
        logger.error(f"[DriftMonitor] Logging error: {e}")

    return result


# --- Drift Detectors: ADWIN and KSWIN (river) ---
try:
    from river.drift import ADWIN, KSWIN
except ImportError:
    ADWIN = None
    KSWIN = None


def detect_adwin_drift(series, delta=0.002):
    """
    Run ADWIN drift detection on a numeric series.
    Returns indices where drift is detected.
    """
    if ADWIN is None:
        raise ImportError("river[drift] is required for ADWIN drift detection.")
    adwin = ADWIN(delta=delta)
    drift_points = []
    for i, val in enumerate(series):
        _ = adwin.update(
            val
        )  # in_drift is not used, only the side effect of update() is needed
        if adwin.drift_detected:
            drift_points.append(i)
    return drift_points


def detect_kswin_drift(series, window_size=20, stat_size=5, alpha=0.005):
    """
    Run KSWIN drift detection on a numeric series.
    Returns indices where drift is detected.
    """
    if KSWIN is None:
        raise ImportError("river[drift] is required for KSWIN drift detection.")
    kswin = KSWIN(window_size=window_size, stat_size=stat_size, alpha=alpha)
    drift_points = []
    for i, val in enumerate(series):
        kswin.update(val)
        if kswin.change_detected:
            drift_points.append(i)
    return drift_points


# Example usage
if __name__ == "__main__":
    before = [
        {"tag": "hope", "avg_confidence": 0.68},
        {"tag": "fatigue", "avg_confidence": 0.45},
        {"tag": "despair", "avg_confidence": 0.33},
    ]
    after = [
        {"tag": "hope", "avg_confidence": 0.41},
        {"tag": "fatigue", "avg_confidence": 0.55},
        {"tag": "despair", "avg_confidence": 0.48},
    ]
    summary = compare_forecast_clusters(before, after, run_id="0425_shift")
    logger.info("Forecast Drift Summary:")
    for tag, delta in summary["tag_deltas"].items():
        logger.info(f"  {tag}: Δ {delta:+.3f}")
    logger.info(f"Symbolic Flips: {summary['symbolic_flips']}")
    logger.info(f"Drift Score: {summary['drift_score']}")
