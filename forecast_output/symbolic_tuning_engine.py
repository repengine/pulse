# symbolic/symbolic_tuning_engine.py

"""
Symbolic Tuning Engine

Takes forecasts flagged for revision and simulates revised versions based on:
- Overlay suggestions
- Arc/tag replacements
- Alignment optimization

Outputs scored revised forecasts with change summary.

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
import logging
from typing import Dict, Any
from trust_system.alignment_index import compute_alignment_index
from trust_system.license_enforcer import license_forecast


def apply_revision_plan(
    forecast: Dict[str, Any], plan: Dict[str, str]
) -> Dict[str, Any]:
    """
    Apply symbolic tuning suggestions to forecast.

    Args:
        forecast: original forecast
        plan: suggested field updates

    Returns:
        Dict: revised forecast (copy)
    """
    revised = json.loads(json.dumps(forecast))  # deep copy

    if "arc_label" in plan:
        revised["arc_label"] = plan["arc_label"]

    if "symbolic_tag" in plan:
        revised["symbolic_tag"] = plan["symbolic_tag"]

    for k, v in plan.items():
        if k.startswith("overlay_"):
            overlay_key = k.replace("overlay_", "")
            try:
                revised.setdefault("overlays", {})[overlay_key] = float(
                    str(v).split()[0]
                )
            except Exception as e:
                logging.error(
                    f"Failed to parse overlay value for {overlay_key}: {v} ({e})"
                )

    revised["revision_applied"] = True
    return revised


def simulate_revised_forecast(
    forecast: Dict[str, Any], plan: Dict[str, str]
) -> Dict[str, Any]:
    """
    Apply revision and rescore alignment + trust.

    Args:
        forecast (Dict): Original forecast.
        plan (Dict): Revision plan.

    Returns:
        Dict: updated revised forecast with license + alignment
    """
    revised = apply_revision_plan(forecast, plan)
    alignment = compute_alignment_index(revised)
    revised["alignment_score"] = alignment["alignment_score"]
    revised["alignment_components"] = alignment["components"]
    revised["license_status"] = license_forecast(revised)
    return revised


def compare_scores(original: Dict[str, Any], revised: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare trust metrics between original and revised forecasts.

    Args:
        original (Dict): Original forecast.
        revised (Dict): Revised forecast.

    Returns:
        Dict: field deltas
    """
    fields = ["alignment_score", "confidence"]
    deltas = {}

    for f in fields:
        a = revised.get(f, 0)
        b = original.get(f, 0)
        deltas[f] = round(a - b, 4)

    deltas["license_status_change"] = (
        f"{original.get('license_status')} → {revised.get('license_status')}"
    )
    return deltas


def log_tuning_result(
    original: Dict[str, Any],
    revised: Dict[str, Any],
    path: str = "logs/tuning_results.jsonl",
):
    """
    Log original + revised pair to audit trail.

    Args:
        original: original forecast
        revised: revised forecast
        path: log output
    """
    record = {
        "original_trace_id": original.get("trace_id", "unknown"),
        "revised_trace_id": revised.get("trace_id", "unknown") + "_rev",
        "original_license": original.get("license_status"),
        "revised_license": revised.get("license_status"),
        "alignment_delta": round(
            revised.get("alignment_score", 0) - original.get("alignment_score", 0), 4
        ),
        "symbolic_revision_plan": revised.get("revision_plan", {}),
    }
    try:
        with open(path, "a") as f:
            f.write(json.dumps(record) + "\n")
        print(f"🧠 Tuning result logged for {record['original_trace_id']}")
    except Exception as e:
        print(f"❌ Failed to log tuning result: {e}")


def _test_symbolic_tuning_engine():
    """Basic test for symbolic tuning engine."""
    dummy = {
        "arc_label": "Collapse Risk",
        "symbolic_tag": "rage rise",
        "overlays": {"rage": 0.7, "hope": 0.1},
        "license_status": "❌ Rejected",
        "alignment_score": 0.2,
        "trace_id": "fc_test",
    }
    plan = {
        "arc_label": "Stabilization Phase",
        "symbolic_tag": "Neutralization",
        "overlay_rage": "0.3",
        "overlay_hope": "0.4",
    }
    revised = apply_revision_plan(dummy, plan)
    assert revised["arc_label"] == "Stabilization Phase"
    assert revised["symbolic_tag"] == "Neutralization"
    assert revised["overlays"]["rage"] == 0.3
    assert revised["overlays"]["hope"] == 0.4
    print("✅ Symbolic tuning engine test passed.")


if __name__ == "__main__":
    _test_symbolic_tuning_engine()
