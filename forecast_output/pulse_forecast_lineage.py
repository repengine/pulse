"""
pulse_forecast_lineage.py

Tracks ancestry and influence of forecasts, detects drift, generates forecast trees, flags divergence.

Author: Pulse AI Engine
"""

from typing import List, Dict, Any
import logging
import argparse
import json

logger = logging.getLogger("pulse_forecast_lineage")

def build_forecast_lineage(forecasts: List[Dict]) -> Dict[str, List[str]]:
    """
    Build a mapping from forecast_id to its children (descendants).
    Args:
        forecasts: List of forecast dicts (should include 'trace_id' and 'parent_id').
    Returns:
        Dict mapping parent_id to list of child trace_ids.
    """
    lineage = {}
    for f in forecasts:
        parent = f.get("parent_id")
        if parent:
            lineage.setdefault(parent, []).append(f.get("trace_id"))
    logger.info(f"Lineage built for {len(lineage)} parents.")
    return lineage

def detect_drift(forecasts: List[Dict], drift_key: str = "symbolic_tag") -> List[str]:
    """
    Detects drift in a specified key (default: symbolic_tag) over time.
    Args:
        forecasts: List of forecast dicts (chronologically ordered).
        drift_key: Key to check for drift (default: 'symbolic_tag').
    Returns:
        List of drift event strings.
    """
    drifts = []
    for i in range(1, len(forecasts)):
        prev = forecasts[i-1]
        curr = forecasts[i]
        if prev.get(drift_key) != curr.get(drift_key):
            drifts.append(f"Drift: {prev.get('trace_id')} → {curr.get('trace_id')} [{drift_key}: {prev.get(drift_key)} → {curr.get(drift_key)}]")
    logger.info(f"Drift detection: {len(drifts)} drift events found for key '{drift_key}'.")
    return drifts

def flag_divergence(forecasts: List[Dict]) -> List[str]:
    """
    Flags divergence forks for operator review.
    Args:
        forecasts: List of forecast dicts (should include 'trace_id' and 'parent_id').
    Returns:
        List of divergence event strings.
    """
    forks = []
    seen = set()
    for f in forecasts:
        parent = f.get("parent_id")
        if parent and parent in seen:
            forks.append(f"Divergence: {f.get('trace_id')} from parent {parent}")
        seen.add(f.get("trace_id"))
    logger.info(f"Divergence flagging: {len(forks)} forks found.")
    return forks

def main():
    parser = argparse.ArgumentParser(description="Pulse Forecast Lineage CLI")
    parser.add_argument("--forecasts", type=str, required=True, help="Path to forecasts JSON file")
    parser.add_argument("--drift-key", type=str, default="symbolic_tag", help="Key to check for drift")
    parser.add_argument("--lineage", action="store_true", help="Show forecast lineage")
    parser.add_argument("--drift", action="store_true", help="Detect drift events")
    parser.add_argument("--divergence", action="store_true", help="Flag divergence forks")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    with open(args.forecasts, "r", encoding="utf-8") as f:
        forecasts = json.load(f)
    if args.lineage:
        lineage = build_forecast_lineage(forecasts)
        print(json.dumps(lineage, indent=2))
    if args.drift:
        drifts = detect_drift(forecasts, drift_key=args.drift_key)
        print(json.dumps(drifts, indent=2))
    if args.divergence:
        forks = flag_divergence(forecasts)
        print(json.dumps(forks, indent=2))

if __name__ == "__main__":
    main()
