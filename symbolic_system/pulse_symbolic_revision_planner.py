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

from typing import Dict

def plan_symbolic_revision(forecast: Dict) -> Dict[str, str]:
    """
    Generate a symbolic revision suggestion for a forecast.

    Returns:
        Dict[str, str]: suggested updates (overlay, arc, tag)
    """
    plan = {}
    arc = forecast.get("arc_label", "").lower()
    tag = forecast.get("symbolic_tag", "").lower()
    overlays = forecast.get("forecast", {}).get("symbolic_change", {}) or forecast.get("overlays", {})

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


def revision_ready(forecast: Dict) -> bool:
    """
    Determine whether this forecast has enough data to be revised.

    Returns:
        bool: True if symbolic plan can be generated
    """
    return forecast.get("symbolic_revision_needed", False)


def generate_revision_report(forecasts: list) -> list:
    """
    Generate symbolic revision plans for a list of unstable forecasts.

    Returns:
        list: Each item contains trace_id and plan
    """
    report = []
    for fc in forecasts:
        if revision_ready(fc):
            plan = plan_symbolic_revision(fc)
            if plan:
                report.append({
                    "trace_id": fc.get("trace_id", "unknown"),
                    "plan": plan
                })
    return report
