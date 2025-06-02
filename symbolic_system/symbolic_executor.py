# symbolic/symbolic_executor.py

"""
Symbolic Executor

Applies symbolic upgrade plans to active forecasts:
- Replaces arcs/tags based on upgrade maps
- Rewrites symbolic overlays in memory
- Tracks symbolic transformation lineage

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
import logging
from typing import Dict, List

logger = logging.getLogger("symbolic_executor")
logging.basicConfig(level=logging.INFO)


def apply_symbolic_upgrade(forecast: Dict, upgrade_map: Dict) -> Dict:
    """
    Apply symbolic upgrade plan to a forecast's symbolic fields.

    Args:
        forecast: the original forecast
        upgrade_map: dict with 'replace_or_retrain' and 'boost' lists

    Returns:
        Mutated forecast (copy) with symbolic override
    """
    revised = json.loads(json.dumps(forecast))  # deep copy

    tag = forecast.get("symbolic_tag", "")
    arc = forecast.get("arc_label", "")

    if tag in upgrade_map.get("replace_or_retrain", []):
        revised["symbolic_tag"] = "Stabilization"
        revised.setdefault("symbolic_mutation", {})["tag"] = f"{tag} → Stabilization"

    if arc in upgrade_map.get("replace_or_retrain", []):
        revised["arc_label"] = "Narrative Convergence"
        revised.setdefault("symbolic_mutation", {})[
            "arc"
        ] = f"{arc} → Narrative Convergence"

    revised["mutation_type"] = "symbolic_upgrade"
    return revised


def rewrite_forecast_symbolics(forecasts: List[Dict], upgrade_plan: Dict) -> List[Dict]:
    """
    Apply symbolic rewrites across a forecast batch.

    Args:
        forecasts: input forecasts
        upgrade_plan: upgrade plan from upgrade_planner

    Returns:
        List of revised forecasts
    """
    revised = []
    for fc in forecasts:
        revised.append(apply_symbolic_upgrade(fc, upgrade_plan.get("suggestions", {})))
    return revised


def generate_upgrade_trace(original: Dict, mutated: Dict) -> Dict:
    """
    Return a comparison record of symbolic field rewrites.

    Returns:
        Dict summary of before/after
    """
    return {
        "trace_id": original.get("trace_id", "unknown"),
        "arc_before": original.get("arc_label"),
        "arc_after": mutated.get("arc_label"),
        "tag_before": original.get("symbolic_tag"),
        "tag_after": mutated.get("symbolic_tag"),
        "mutation_details": mutated.get("symbolic_mutation", {}),
    }


def log_symbolic_mutation(trace: Dict, path: str = "logs/symbolic_mutation_log.jsonl"):
    """
    Append symbolic rewrite trace to log.

    Args:
        trace: mutation record
        path: output file
    """
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace, ensure_ascii=False) + "\n")
        logger.info(
            f"🧬 Symbolic mutation logged for {trace.get('trace_id', 'unknown')}"
        )
    except Exception as e:
        logger.error(f"❌ Failed to log symbolic mutation: {e}")


def _test_symbolic_executor():
    dummy = {"trace_id": "t1", "arc_label": "Collapse Risk", "symbolic_tag": "fear"}
    upgrade = {"replace_or_retrain": ["Collapse Risk", "fear"], "boost": []}
    mutated = apply_symbolic_upgrade(dummy, upgrade)
    _trace = generate_upgrade_trace(dummy, mutated)
    assert mutated["arc_label"] == "Narrative Convergence"
    assert mutated["symbolic_tag"] == "Stabilization"
    assert mutated["mutation_type"] == "symbolic_upgrade"
    logger.info("✅ Symbolic executor test passed.")


if __name__ == "__main__":
    _test_symbolic_executor()
