"""
forecast_regret_engine.py

Runs past simulations through a regret lens, analyzes missed/wrong forecasts, builds learning loop.

Author: Pulse AI Engine
"""

# Moved from project root for better organization
from diagnostics import forecast_regret_engine

from typing import List, Dict

def analyze_regret(forecasts: List[Dict], actuals: Dict) -> List[Dict]:
    """
    Compare forecasts to actuals, flag regret cases.
    """
    regrets = []
    for f in forecasts:
        # Simple regret: if retrodiction_score < 0.5, flag as regret
        score = f.get("retrodiction_score", 1.0)
        if score < 0.5:
            regrets.append({
                "trace_id": f.get("trace_id"),
                "reason": "Low retrodiction score",
                "score": score
            })
    return regrets

def analyze_misses(forecasts: List[Dict], actuals: Dict) -> List[Dict]:
    """
    Analyze causes of missed scenarios.
    """
    misses = []
    for f in forecasts:
        # Placeholder: check for missed asset or overlay
        if "missed_asset" in f:
            misses.append({
                "trace_id": f.get("trace_id"),
                "reason": "Missed asset",
                "asset": f["missed_asset"]
            })
    return misses

def feedback_loop(regrets: List[Dict]):
    """
    Adjust symbolic weights/rules based on regret analysis (stub).
    """
    # Placeholder: print summary
    print(f"Regret feedback: {len(regrets)} cases flagged for review.")