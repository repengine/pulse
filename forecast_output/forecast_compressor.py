"""
PATCHED: forecast_compressor.py
Pulse Version: v0.21.2
Patch: Auto-calls forecast_summary_synthesizer after compressing clusters
"""

import json
from typing import List, Dict, Optional
import numpy as np

from forecast_output.forecast_summary_synthesizer import summarize_forecasts
from utils.log_utils import get_logger
from engine.path_registry import PATHS
from trust_system.trust_engine import compute_symbolic_attention_score


def compress_mc_samples(
    mc_samples: List[Dict[str, np.ndarray]], alpha: float = 0.9
) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Compress Monte Carlo forecast samples into mean and prediction interval.

    Parameters:
        mc_samples: List of forecast dictionaries. Each dict maps field names
                    to 1D numpy arrays of equal length (time steps).
        alpha:       Coverage probability for the prediction interval (0 < alpha < 1).

    Returns:
        A dict mapping each field name to a dict with keys:
            'mean' : np.ndarray of shape (T,), the average across samples.
            'lower': np.ndarray of shape (T,), the lower percentile at (1-alpha)/2*100.
            'upper': np.ndarray of shape (T,), the upper percentile at (1+alpha)/2*100.
    """
    if not mc_samples:
        raise ValueError("mc_samples must be a non-empty list of sample dictionaries.")

    result: Dict[str, Dict[str, np.ndarray]] = {}
    for key in mc_samples[0]:
        data = np.stack([s[key] for s in mc_samples], axis=0)
        mean = np.mean(data, axis=0)
        lower = np.percentile(data, (1 - alpha) / 2 * 100, axis=0)
        upper = np.percentile(data, (1 + alpha) / 2 * 100, axis=0)
        result[key] = {"mean": mean, "lower": lower, "upper": upper}
    return result


assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

COMPRESSED_OUTPUT = PATHS["FORECAST_COMPRESSED"]

logger = get_logger(__name__)


def flag_drift_sensitive_forecasts(
    forecasts: List[Dict], drift_report: Dict, threshold: float = 0.2
) -> List[Dict]:
    """
    Flags forecasts if they belong to unstable arcs or are based on drift-prone rules.

    Args:
        forecasts: List of forecast dictionaries to evaluate
        drift_report: Analysis report containing rule_trigger_delta and overlay_drift data
        threshold: Drift threshold for flagging (default 0.2)

    Returns:
        Modified list of forecasts with drift_flag attribute added
    """
    if not isinstance(forecasts, list):
        logger.error(f"forecasts must be a list, got {type(forecasts)}")
        return []

    if not isinstance(drift_report, dict):
        logger.warning(f"drift_report must be a dict, got {type(drift_report)}")
        return forecasts

    if not isinstance(threshold, (int, float)) or threshold <= 0:
        logger.warning(f"Invalid threshold {threshold}, using default 0.2")
        threshold = 0.2

    # Extract volatile rules and unstable overlays from drift report
    try:
        volatile_rules = {
            r
            for r, delta in drift_report.get("rule_trigger_delta", {}).items()
            if abs(delta) > threshold * 10
        }
        unstable_overlays = {
            k for k, v in drift_report.get("overlay_drift", {}).items() if v > threshold
        }
    except Exception as e:
        logger.error(f"Error extracting volatility data: {e}")
        volatile_rules = set()
        unstable_overlays = set()

    logger.info(
        f"Found {
            len(volatile_rules)} volatile rules and {
            len(unstable_overlays)} unstable overlays")

    for fc in forecasts:
        if not isinstance(fc, dict):
            logger.warning(f"Skipping non-dict forecast: {type(fc)}")
            continue

        arc = fc.get("arc_label", "unknown")
        rules = fc.get("fired_rules", [])
        overlays = fc.get("forecast", {}).get("symbolic_change", {})

        flagged = False

        # Flag forecasts based on rules, overlays or arcs
        try:
            if any(r in volatile_rules for r in rules):
                fc["drift_flag"] = "⚠️ Rule Instability"
                flagged = True
            elif any(k in unstable_overlays for k in overlays):
                fc["drift_flag"] = "⚠️ Overlay Volatility"
                flagged = True
            elif (
                "collapse" in arc.lower()
                and drift_report.get("arc_stability", {}).get("collapse", 0) > threshold
            ):
                fc["drift_flag"] = "⚠️ Arc Volatility"
                flagged = True

            if not flagged:
                fc["drift_flag"] = "✅ Stable"

        except Exception as e:
            logger.error(f"Error flagging forecast: {e}")
            fc["drift_flag"] = "⚠️ Processing Error"

    return forecasts


def compress_forecasts(
    forecasts: List[Dict],
    cluster_key: str = "symbolic_tag",
    top_n: Optional[int] = None,
    summarize: bool = True,
    arc_drift: Optional[Dict[str, int]] = None,
    drift_report: Optional[Dict] = None,
) -> List[Dict]:
    """
    Compresses forecasts by clustering and summarizing.

    Args:
        forecasts: List of forecast dicts.
        cluster_key: Key to cluster by ("symbolic_tag", "narrative_theme", etc).
        top_n: Only keep top N clusters (by count).
        summarize: If True, call forecast_summary_synthesizer.
        arc_drift: Optional dict of arc drift deltas for attention scoring.
        drift_report: Optional simulation drift report for drift flagging.

    Returns:
        List of compressed cluster dicts.
    """
    from collections import defaultdict, Counter

    if not isinstance(forecasts, list):
        logger.warning("Input 'forecasts' is not a list.")
        return []
    # Flag drift-sensitive forecasts if drift_report is provided
    if drift_report:
        forecasts = flag_drift_sensitive_forecasts(forecasts, drift_report)

    # Suppress drift-flagged forecasts before top-K selection
    forecasts = [
        f
        for f in forecasts
        if f.get("drift_flag") not in {"⚠️ Rule Instability", "⚠️ Overlay Volatility"}
    ]

    clusters = defaultdict(list)
    for f in forecasts:
        label = f.get(cluster_key, "unknown")
        clusters[label].append(f)

    if top_n:
        clusters = dict(
            sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)[:top_n]
        )

    compressed = []
    for label, group in clusters.items():
        confs = [f.get("confidence", 0.0) or 0.0 for f in group]
        avg_conf = round(sum(confs) / len(confs), 3) if confs else 0.0
        drivers = []
        for f in group:
            ds = f.get("drivers") or f.get("driver") or []
            if isinstance(ds, str):
                ds = [ds]
            drivers.extend(ds)
        top_drivers = [d for d, _ in Counter(drivers).most_common(3)]
        # Compute attention score for the cluster (use first example's arc_label)
        attention = 0.0
        if arc_drift and group:
            arc_label = group[0].get("arc_label", "unknown")
            try:
                attention = compute_symbolic_attention_score(
                    {"arc_label": arc_label}, arc_drift
                )
            except Exception as e:
                logger.warning(f"Attention score error for arc_label {arc_label}: {e}")
                attention = None
        compressed.append(
            {
                "tag": label,
                "count": len(group),
                "avg_confidence": avg_conf,
                "top_drivers": top_drivers,
                "examples": group[:2],
                "attention_score": attention,
            }
        )

    try:
        with open(COMPRESSED_OUTPUT, "w") as f:
            json.dump(compressed, f, indent=2)
        logger.info(f"Compressed forecasts written to {COMPRESSED_OUTPUT}")
    except Exception as e:
        logger.warning(f"Failed to write compressed output: {e}")

    if summarize:
        try:
            # Always call summarize_forecasts after compression for downstream
            # integration.
            summarize_forecasts(compressed)
        except Exception as e:
            logger.warning(f"Summary synthesizer failed: {e}")

    return compressed


if __name__ == "__main__":
    # Example usage/test
    sample = [
        {
            "symbolic_tag": "hope",
            "confidence": 0.62,
            "drivers": ["NVDA earnings", "AI sentiment"],
        },
        {"symbolic_tag": "hope", "confidence": 0.68, "drivers": ["FED stance"]},
        {"symbolic_tag": "fatigue", "confidence": 0.43, "drivers": ["news overload"]},
    ]
    result = compress_forecasts(sample)
    print(json.dumps(result, indent=2))
