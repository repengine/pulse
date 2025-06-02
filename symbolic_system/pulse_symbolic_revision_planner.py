# symbolic/pulse_symbolic_revision_planner.py

"""
Pulse Symbolic Revision Planner

Suggests symbolic tuning recommendations for unstable or drift-flagged forecasts:
- Overlay profile adjustments
- Arc label reclassification
- Symbolic tag realignment

Author: Pulse AI Engine
Version: v1.0.0
"""

from typing import Dict, List, Any
from collections import Counter


def plan_symbolic_revision(forecast: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate a symbolic revision suggestion for a forecast.

    Args:
        forecast (Dict): Forecast dictionary.

    Returns:
        Dict[str, str]: suggested updates (overlay, arc, tag)
    """
    plan = {}
    arc = str(forecast.get("arc_label", "")).lower()
    tag = str(forecast.get("symbolic_tag", "")).lower()
    overlays = forecast.get("forecast", {}).get("symbolic_change", {}) or forecast.get(
        "overlays", {}
    )

    # Suggest arc relabels
    if arc in {"collapse risk", "despair drop", "fatigue loop"}:
        plan["arc_label"] = "Stabilization Phase"

    # Suggest tag adjustments
    if tag in {"rage rise", "despair"}:
        plan["symbolic_tag"] = "Neutralization"

    # Suggest overlay damping
    if "rage" in overlays and overlays["rage"] > 0.6:
        plan["overlay_rage"] = "reduce to < 0.5"

    if "hope" in overlays and overlays["hope"] < 0.2:
        plan["overlay_hope"] = "increase to > 0.3"

    return plan


def revision_ready(forecast: Dict[str, Any]) -> bool:
    """
    Determine whether this forecast has enough data to be revised.

    Args:
        forecast (Dict): Forecast dictionary.

    Returns:
        bool: True if symbolic plan can be generated
    """
    return bool(forecast.get("symbolic_revision_needed", False))


def generate_revision_report(forecasts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate symbolic revision plans for a list of unstable forecasts.

    Args:
        forecasts (list): List of forecast dicts.

    Returns:
        list: Each item contains trace_id and plan
    """
    report = []
    for fc in forecasts:
        if revision_ready(fc):
            plan = plan_symbolic_revision(fc)
            if plan:
                report.append({"trace_id": fc.get("trace_id", "unknown"), "plan": plan})
    return report


def plan_revisions_for_fragmented_arcs(
    forecasts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Suggest symbolic revisions for dominant arcs in fragmented forecasts.

    Args:
        forecasts (List[Dict]): List of forecast dicts.

    Returns:
        List of {arc, tag suggestions, overlay hints}
    """
    fragmented = [f for f in forecasts if f.get("symbolic_fragmented")]
    arc_counts = Counter(f.get("arc_label", "unknown") for f in fragmented)

    plans = []
    for arc, count in arc_counts.items():
        plan = {"arc": arc, "tag_suggestion": None, "overlay_hint": {}}
        if arc in {"Collapse Risk", "Fatigue Loop"}:
            plan["tag_suggestion"] = "Stabilization"
            plan["overlay_hint"] = {"hope": "increase", "rage": "reduce"}
        elif arc == "Despair Drop":
            plan["tag_suggestion"] = "Reconstruction"
        plans.append(plan)

    return plans


def _test_revision_planner() -> None:
    """Basic test for symbolic revision planner."""
    dummy = [
        {"arc_label": "Collapse Risk", "symbolic_fragmented": True},
        {"arc_label": "Fatigue Loop", "symbolic_fragmented": True},
        {"arc_label": "Despair Drop", "symbolic_fragmented": True},
        {"arc_label": "Other", "symbolic_fragmented": False},
    ]
    plans = plan_revisions_for_fragmented_arcs(dummy)
    assert any(p["arc"] == "Collapse Risk" for p in plans)
    print("✅ Symbolic revision planner test passed.")


if __name__ == "__main__":
    _test_revision_planner()
