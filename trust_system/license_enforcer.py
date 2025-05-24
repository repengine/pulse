# trust_system/license_enforcer.py

"""
Forecast License Enforcer

Enforces final trust filtering for forecast export, memory retention,
operator briefing, and Strategos digest generation.

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
from typing import List, Dict, Optional

from trust_system.license_explainer import explain_forecast_license
from trust_system.forecast_licensing_shell import license_forecast
from trust_system.forecast_audit_trail import generate_forecast_audit


def annotate_forecasts(forecasts: List[Dict]) -> List[Dict]:
    """
    Add license status and rationale to each forecast.

    Returns:
        List[Dict]: Updated forecasts
    """
    for fc in forecasts:
        fc["license_status"] = license_forecast(fc)
        fc["license_explanation"] = explain_forecast_license(fc)
    return forecasts


def filter_licensed(forecasts: List[Dict], only_approved=True) -> List[Dict]:
    """
    Filter forecasts based on license status.

    Args:
        only_approved (bool): If True, return only '✅ Approved'

    Returns:
        List[Dict]: Filtered forecasts
    """
    return [
        fc
        for fc in forecasts
        if not only_approved or fc.get("license_status") == "✅ Approved"
    ]


def summarize_license_distribution(forecasts: List[Dict]) -> Dict[str, int]:
    """
    Count how many forecasts fall into each license category.

    Returns:
        Dict[str, int]: Count per license_status
    """
    counts = {}
    for fc in forecasts:
        status = fc.get("license_status", "❓ Unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def export_rejected_forecasts(forecasts: List[Dict], path: str) -> None:
    """
    Save forecasts that failed licensing for audit trail / future learning.

    Args:
        forecasts: full list of forecasts
        path: where to save
    """
    rejected = [f for f in forecasts if f.get("license_status") != "✅ Approved"]
    try:
        with open(path, "w") as f:
            for r in rejected:
                f.write(json.dumps(r) + "\n")
        print(f"📤 Rejected forecasts saved to {path}")
    except Exception as e:
        print(f"❌ Failed to save rejected forecasts: {e}")




def full_trust_license_audit_pipeline(
    forecasts: List[Dict],
    current_state: Optional[Dict] = None,
    memory: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    Run trust processing, licensing, and audit trail generation on a batch of forecasts.
    Each forecast is updated in-place with trust, license, and audit metadata.
    Returns the updated forecasts.
    """
    from trust_system.trust_engine import (
        TrustEngine,
    )  # moved import here to avoid circular import

    for fc in forecasts:
        TrustEngine.apply_all([fc])  # TrustEngine.apply_all mutates in-place
        annotate_forecasts([fc])
        fc["pulse_audit_trail"] = generate_forecast_audit(
            fc, current_state=current_state, memory=memory
        )
    return forecasts
