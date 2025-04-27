"""
forecast_regret_engine.py

Runs past simulations through a regret lens, analyzes missed/wrong forecasts, builds learning loop.

Author: Pulse AI Engine
"""

from typing import List, Dict, Any
import logging
import argparse
import json

logger = logging.getLogger("forecast_regret_engine")

DEFAULT_REGRET_THRESHOLD = 0.5

def analyze_regret(forecasts: List[Dict], actuals: Dict, regret_threshold: float = DEFAULT_REGRET_THRESHOLD) -> List[Dict]:
    """
    Compare forecasts to actuals, flag regret cases.
    Args:
        forecasts: List of forecast dicts (should include 'retrodiction_score').
        actuals: Dict of actual outcomes (not used in default logic).
        regret_threshold: Threshold below which a forecast is flagged as regret.
    Returns:
        List of regret dicts.
    """
    regrets = []
    for f in forecasts:
        score = f.get("retrodiction_score", 1.0)
        if score < regret_threshold:
            regrets.append({
                "trace_id": f.get("trace_id"),
                "reason": "Low retrodiction score",
                "score": score
            })
    logger.info(f"Regret analysis: {len(regrets)} regrets found (threshold={regret_threshold})")
    return regrets

def analyze_misses(forecasts: List[Dict], actuals: Dict) -> List[Dict]:
    """
    Analyze causes of missed scenarios, including missed assets, overlays, and symbolic_tag drift.
    Args:
        forecasts: List of forecast dicts.
        actuals: Dict of actual outcomes (should include overlays, assets, etc.).
    Returns:
        List of miss dicts.
    """
    misses = []
    for f in forecasts:
        # Missed asset
        if "missed_asset" in f:
            misses.append({
                "trace_id": f.get("trace_id"),
                "reason": "Missed asset",
                "asset": f["missed_asset"]
            })
        # Missed overlay
        if "missed_overlay" in f:
            misses.append({
                "trace_id": f.get("trace_id"),
                "reason": "Missed overlay",
                "overlay": f["missed_overlay"]
            })
        # Symbolic tag drift
        if actuals and "symbolic_tag" in f and "symbolic_tag" in actuals:
            if f["symbolic_tag"] != actuals["symbolic_tag"]:
                misses.append({
                    "trace_id": f.get("trace_id"),
                    "reason": "Symbolic tag drift",
                    "forecast_tag": f["symbolic_tag"],
                    "actual_tag": actuals["symbolic_tag"]
                })
    logger.info(f"Miss analysis: {len(misses)} misses found.")
    return misses

from typing import Optional

def feedback_loop(regrets: List[Dict], log_path: Optional[str] = None):
    """
    Adjust symbolic weights/rules based on regret analysis (stub).
    Optionally logs regrets to a file.
    """
    logger.info(f"Regret feedback: {len(regrets)} cases flagged for review.")
    if log_path:
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(regrets, f, indent=2)
            logger.info(f"Regret feedback written to {log_path}")
        except Exception as e:
            logger.error(f"Failed to write regret feedback: {e}")
    # TODO: Integrate with model update logic

def main():
    parser = argparse.ArgumentParser(description="Forecast Regret Engine CLI")
    parser.add_argument("--forecasts", type=str, required=True, help="Path to forecasts JSON file")
    parser.add_argument("--actuals", type=str, required=False, help="Path to actuals JSON file")
    parser.add_argument("--regret-threshold", type=float, default=DEFAULT_REGRET_THRESHOLD, help="Regret threshold")
    parser.add_argument("--log", type=str, default=None, help="Log regrets to file")
    parser.add_argument("--misses", action="store_true", help="Analyze misses as well as regrets")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    with open(args.forecasts, "r", encoding="utf-8") as f:
        forecasts = json.load(f)
    actuals = {}
    if args.actuals:
        with open(args.actuals, "r", encoding="utf-8") as f:
            actuals = json.load(f)
    regrets = analyze_regret(forecasts, actuals, regret_threshold=args.regret_threshold)
    feedback_loop(regrets, log_path=args.log)
    if args.misses:
        misses = analyze_misses(forecasts, actuals)
        print(json.dumps(misses, indent=2))
    print(json.dumps(regrets, indent=2))

if __name__ == "__main__":
    main()