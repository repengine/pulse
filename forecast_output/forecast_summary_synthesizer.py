"""
Module: forecast_summary_synthesizer.py
Pulse Version: v0.015.0
Location: pulse/forecast_output/
Last Updated: 2025-04-17
Author: Pulse AI Engine

Description:
Synthesizes strategic summaries from forecast clusters or raw forecast sets.
Extracts symbolic drivers, ranks by confidence, and compresses into human-readable summary outputs.

Inputs:
- List[Dict]: Each dict is a forecast (must include 'confidence', 'symbolic_tag', optional 'drivers')

Outputs:
- Summarized JSONL per forecast
- Optional printout or interactive use

Used by:
- forecast_compressor.py
- Pulse CLI
- Strategos Digest
- PFPA Loggers

Log Output:
- logs/forecast_summary_log.jsonl
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from engine.path_registry import PATHS
from engine.pulse_config import USE_SYMBOLIC_OVERLAYS
from symbolic_system.pulse_symbolic_arc_tracker import (
    compare_arc_drift,
    compute_arc_stability,
)
from trust_system.alignment_index import compute_alignment_index
from trust_system.forecast_episode_logger import summarize_episodes

# Import symbolic fragmentation detector
from symbolic_system.symbolic_convergence_detector import detect_fragmentation

from utils.log_utils import get_logger

logger = get_logger(__name__)

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

VALID_TAGS = {"hope", "despair", "rage", "fatigue", "trust"}


def is_valid_tag(tag: str) -> bool:
    return tag.lower() in VALID_TAGS


SUMMARY_LOG_PATH = PATHS.get("SUMMARY_LOG_PATH", "logs/forecast_summary_log.jsonl")


def ensure_log_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


# Add symbolic fragmentation tagging
def tag_fragmented_forecasts(
    forecasts: List[Dict], key: str = "arc_label"
) -> List[Dict]:
    """
    Tag forecasts as fragmented if symbolic fragmentation is detected.
    Used by forecast_compressor, digest, and pipeline modules.
    """
    if detect_fragmentation(forecasts, key=key):
        for f in forecasts:
            f["symbolic_fragmented"] = True
    else:
        for f in forecasts:
            f["symbolic_fragmented"] = False
    return forecasts


def summarize_forecasts(
    forecasts: List[Dict],
    method: str = "default",
    log_path: Optional[str] = None,
    previous_forecasts: Optional[List[Dict]] = None,
    alignment: bool = False,
    previous_episode_log: Optional[str] = None,
) -> List[Dict]:
    """
    Generate a human-readable summary of each forecast.
    Returns a list of summary dicts and writes them to log.
    """
    if not forecasts:
        return []

    path = log_path or SUMMARY_LOG_PATH
    ensure_log_dir(path)

    summaries = []
    arc_drift = {}
    arc_volatility = None

    if previous_episode_log and os.path.exists(previous_episode_log):
        prev = summarize_episodes(previous_episode_log)
        curr = summarize_episodes(
            PATHS.get("EPISODE_LOG_PATH", "logs/forecast_episode_log.jsonl")
        )
        arcs_prev = {
            k.replace("arc_", ""): v for k, v in prev.items() if k.startswith("arc_")
        }
        arcs_curr = {
            k.replace("arc_", ""): v for k, v in curr.items() if k.startswith("arc_")
        }
        all_keys = set(arcs_prev) | set(arcs_curr)
        arc_drift = {k: arcs_curr.get(k, 0) - arcs_prev.get(k, 0) for k in all_keys}
    elif previous_forecasts:
        arc_drift = compare_arc_drift(previous_forecasts, forecasts)
        arc_volatility = compute_arc_stability(arc_drift)

    # Tag fragmentation before summarizing
    if USE_SYMBOLIC_OVERLAYS:
        forecasts = tag_fragmented_forecasts(forecasts, key="arc_label")

    # Tag revision candidates after fragmentation detection
    if USE_SYMBOLIC_OVERLAYS:
        for fc in forecasts:
            if fc.get("symbolic_fragmented"):
                fc["revision_candidate"] = True

    for i, f in enumerate(forecasts):
        conf = f.get("confidence", 0.5)
        tag = f.get("symbolic_tag", "unlabeled")
        if not is_valid_tag(tag):
            tag = "unlabeled"
        drivers = f.get("drivers", ["unknown"])
        scenario = {
            "summary": f"Scenario {i + 1}: {tag} scenario driven by {', '.join(drivers)}.",
            "confidence": round(conf, 4),
            "symbolic_tag": tag,
            "drivers": drivers,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "version": "v0.015.0",
                "source": "pulse/forecast_output/forecast_summary_synthesizer.py",
            },
            "arc_drift_summary": arc_drift,
            "arc_volatility_score": arc_volatility if USE_SYMBOLIC_OVERLAYS else None,
            "symbolic_fragmented": f.get("symbolic_fragmented", False)
            if USE_SYMBOLIC_OVERLAYS
            else None,
        }
        if arc_drift and USE_SYMBOLIC_OVERLAYS:
            scenario["symbolic_arc_drift"] = arc_drift
        if alignment:
            alignment_info = compute_alignment_index(f, current_state=None)
            scenario["alignment_score"] = alignment_info["alignment_score"]
            scenario["alignment_components"] = alignment_info["components"]
        summaries.append(scenario)

        try:
            with open(path, "a") as f:
                f.write(json.dumps(scenario) + "\n")
        except Exception as e:
            logger.error(f"[SummarySynthesizer] Logging error: {e}")

    return summaries


# Example usage
if __name__ == "__main__":
    sample_forecasts = [
        {
            "confidence": 0.78,
            "symbolic_tag": "Hope Rising",
            "drivers": ["AI policy", "VIX drop"],
        },
        {
            "confidence": 0.52,
            "symbolic_tag": "Fatigue Plateau",
            "drivers": ["media overload", "macro stability"],
        },
    ]
    summaries = summarize_forecasts(sample_forecasts)
    for s in summaries:
        print(s["summary"], "| Confidence:", s["confidence"])
