# forecast_output/strategic_fork_resolver.py

"""
Strategic Fork Resolver

Selects one side of a symbolic narrative fork (Scenario A vs B)
based on alignment, confidence, arc priority, and symbolic trust.

Author: Pulse AI Engine
Version: v1.0.0
"""

from typing import Dict, List
from forecast_output.forecast_prioritization_engine import score_forecast
from forecast_output.forecast_cluster_classifier import classify_forecast_cluster


def score_fork_options(a: Dict, b: Dict) -> Dict[str, float]:
    """
    Score each forecast based on alignment + confidence + arc weight.

    Returns:
        Dict: {'A': score, 'B': score}
    """
    sa = score_forecast(a)
    sb = score_forecast(b)
    return {"A": round(sa, 3), "B": round(sb, 3)}


def resolve_fork(pair: Dict) -> Dict:
    """
    Choose best forecast between scenario A and B.

    Returns:
        Dict with decision and rationale
    """
    a = pair.get("scenario_a", {}).get("forecast")
    b = pair.get("scenario_b", {}).get("forecast")

    if not a or not b:
        return {"decision": "undecided", "reason": "missing data", "score": {}}

    scores = score_fork_options(a, b)
    decision = "A" if scores["A"] > scores["B"] else "B"

    return {
        "decision": decision,
        "selected_trace_id": a["trace_id"] if decision == "A" else b["trace_id"],
        "reason": f"Score A={scores['A']} vs B={scores['B']}",
        "cluster": classify_forecast_cluster(a if decision == "A" else b),
        "score": scores,
    }


def resolve_all_forks(dual_scenarios: List[Dict]) -> List[Dict]:
    """
    Run resolver on all scenario pairs.

    Returns:
        List of decision summaries
    """
    return [resolve_fork(pair) for pair in dual_scenarios]


def export_fork_decision_summary(results: List[Dict], path: str):
    """Save decision summary to disk."""
    import json

    try:
        with open(path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"✅ Fork decisions saved to {path}")
    except Exception as e:
        print(f"❌ Export failed: {e}")
