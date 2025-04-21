# trust_system/recovered_forecast_scorer.py

"""
Recovered Forecast Scorer

Re-evaluates forecasts recovered via symbolic sweep. Flags any that remain unstable:
- Low alignment
- Drift-prone trust labels
- Fragility or symbolic volatility

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
from typing import List, Dict
from trust_system.license_enforcer import annotate_forecasts, filter_licensed


def score_recovered_forecasts(forecasts: List[Dict]) -> List[Dict]:
    """
    Re-scores alignment and license for recovered forecasts.

    Returns:
        List[Dict]: Annotated forecasts with trust metadata
    """
    return annotate_forecasts(forecasts)


def flag_unstable_forecasts(forecasts: List[Dict], align_threshold=70, trust_required="🟢 Trusted") -> List[Dict]:
    """
    Apply instability warnings to re-licensed forecasts.

    Returns:
        List[Dict]: Updated forecasts with 'symbolic_revision_needed'
    """
    for fc in forecasts:
        if fc.get("license_status") != "✅ Approved":
            continue
        needs_revision = False
        if fc.get("alignment_score", 100) < align_threshold:
            needs_revision = True
        if fc.get("trust_label") != trust_required:
            needs_revision = True
        if fc.get("drift_flag"):
            needs_revision = True

        fc["symbolic_revision_needed"] = needs_revision
    return forecasts


def summarize_repair_quality(forecasts: List[Dict]) -> Dict[str, int]:
    """
    Count how many repaired forecasts remain unstable.
    """
    total = len(forecasts)
    unstable = sum(1 for fc in forecasts if fc.get("symbolic_revision_needed"))
    stable = total - unstable
    return {
        "total_repaired": total,
        "still_unstable": unstable,
        "stable_now": stable
    }


def export_flagged_for_revision(forecasts: List[Dict], path: str) -> None:
    """
    Save forecasts marked for symbolic revision to disk.
    """
    flagged = [fc for fc in forecasts if fc.get("symbolic_revision_needed")]
    try:
        with open(path, "w") as f:
            for fc in flagged:
                f.write(json.dumps(fc) + "\n")
        print(f"📤 Exported {len(flagged)} unstable forecasts to {path}")
    except Exception as e:
        print(f"❌ Export failed: {e}")
