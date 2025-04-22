# symbolic/symbolic_upgrade_planner.py

"""
Symbolic Upgrade Planner

Analyzes symbolic learning profiles and proposes upgrade plans:
- Replace failing arcs/tags
- Boost successful symbolic strategies
- Adjust overlay defaults or tag heuristics

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
import logging
from typing import Dict, List

logger = logging.getLogger("symbolic_upgrade_planner")
logging.basicConfig(level=logging.INFO)


def detect_underperforming_symbols(performance: Dict[str, Dict], threshold: float = 0.4, min_total: int = 3) -> List[str]:
    """
    Detect symbolic arcs/tags with low success rates.

    Args:
        performance: dict of symbol -> {"rate": float, "total": int}
        threshold: below this rate is considered underperforming
        min_total: minimum number of samples to consider

    Returns:
        List of symbols below threshold
    """
    return [k for k, v in performance.items() if v.get("rate", 0) < threshold and v.get("total", 0) >= min_total]


def detect_high_performers(performance: Dict[str, Dict], threshold: float = 0.85, min_total: int = 3) -> List[str]:
    """
    Detect symbolic arcs/tags with consistent success.

    Args:
        performance: dict of symbol -> {"rate": float, "total": int}
        threshold: above this rate is considered high-performing
        min_total: minimum number of samples to consider

    Returns:
        List of symbols above threshold
    """
    return [k for k, v in performance.items() if v.get("rate", 0) > threshold and v.get("total", 0) >= min_total]


def propose_symbolic_upgrades(profile: Dict) -> Dict:
    """
    Generate symbolic upgrade suggestions based on performance.

    Args:
        profile: learning profile dict

    Returns:
        Dict: structured symbolic revision proposal
    """
    arc_perf = profile.get("arc_performance", {})
    tag_perf = profile.get("tag_performance", {})
    arc_risks = detect_underperforming_symbols(arc_perf)
    tag_risks = detect_underperforming_symbols(tag_perf)
    arc_strengths = detect_high_performers(arc_perf)
    tag_strengths = detect_high_performers(tag_perf)

    return {
        "timestamp": profile.get("last_updated"),
        "underperforming_arcs": arc_risks,
        "underperforming_tags": tag_risks,
        "strong_arcs": arc_strengths,
        "strong_tags": tag_strengths,
        "suggestions": {
            "boost": tag_strengths[:3] + arc_strengths[:3],
            "replace_or_retrain": tag_risks[:3] + arc_risks[:3]
        }
    }


def export_upgrade_plan(plan: Dict, path: str = "plans/symbolic_upgrade_plan.json"):
    """
    Save the symbolic upgrade plan to disk.

    Args:
        plan: upgrade strategy dictionary
        path: output file
    """
    if not isinstance(plan, dict):
        logger.error("❌ Invalid plan: not a dict")
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        logger.info(f"📤 Upgrade plan saved to {path}")
    except Exception as e:
        logger.error(f"❌ Failed to write upgrade plan: {e}")


def _test_symbolic_upgrade_planner():
    """Basic test for symbolic upgrade planner."""
    dummy_profile = {
        "arc_performance": {"Hope Surge": {"rate": 0.9, "total": 10}, "Collapse Risk": {"rate": 0.2, "total": 5}},
        "tag_performance": {"optimism": {"rate": 0.95, "total": 8}, "fear": {"rate": 0.3, "total": 6}},
        "last_updated": "2024-06-01T12:00:00"
    }
    plan = propose_symbolic_upgrades(dummy_profile)
    assert "underperforming_arcs" in plan and "Collapse Risk" in plan["underperforming_arcs"]
    assert "strong_tags" in plan and "optimism" in plan["strong_tags"]
    assert isinstance(plan["underperforming_arcs"], list)
    assert isinstance(plan["strong_tags"], list)
    logger.info("✅ Symbolic upgrade planner test passed.")


if __name__ == "__main__":
    _test_symbolic_upgrade_planner()
