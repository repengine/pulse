# trust_system/forecast_audit_trail.py
"""
Forecast Audit Trail Generator

Creates a record of each forecast's performance and metadata including:
- Confidence
- Retrodiction error
- Alignment score
- Arc label + symbolic tag
- Rule triggers and trust label

Appends each entry to `logs/forecast_audit_trail.jsonl`.

Author: Pulse AI Engine
Version: v1.0.2
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from trust.alignment_index import compute_alignment_index
from trust.forecast_retrospector import compute_retrodiction_error

AUDIT_LOG_PATH = "logs/forecast_audit_trail.jsonl"


def generate_forecast_audit(
    forecast: Dict,
    current_state: Optional[Dict] = None,
    memory: Optional[List[Dict]] = None,
    arc_volatility: Optional[float] = None,
    tag_match: Optional[float] = None
) -> Dict:
    """
    Generate an audit trail record for a forecast.

    Parameters:
        forecast (Dict): The forecast object to audit
        current_state (Optional[Dict]): For retrodiction comparison
        memory (Optional[List[Dict]]): Optional prior forecast memory
        arc_volatility (Optional[float]): Arc shift score (if known)
        tag_match (Optional[float]): Symbolic tag match score (0–1)

    Returns:
        Dict: Full audit record for this forecast
    """
    alignment = compute_alignment_index(
        forecast,
        current_state=current_state,
        memory=memory,
        arc_volatility=arc_volatility,
        tag_match=tag_match
    )

    ret_error = None
    if current_state:
        try:
            ret_error = compute_retrodiction_error(forecast, current_state)
        except Exception as e:
            ret_error = None

    return {
        "forecast_id": forecast.get("trace_id", "unknown"),
        "timestamp": datetime.utcnow().isoformat(),
        "alignment_score": alignment["alignment_score"],
        "confidence": forecast.get("confidence", None),
        "retrodiction_error": ret_error,
        "arc_label": forecast.get("arc_label", "unknown"),
        "symbolic_tag": forecast.get("symbolic_tag", "unknown"),
        "trust_label": forecast.get("trust_label", None),
        "rule_ids": forecast.get("fired_rules", []),
        "components": alignment["components"]
    }


def log_forecast_audit(audit: Dict, path: str = AUDIT_LOG_PATH) -> None:
    """
    Save audit trail to persistent JSONL file.

    Parameters:
        audit (Dict): Audit record dictionary
        path (str): Path to JSONL file
    """
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(audit) + "\n")
        print(f"✅ Forecast audit logged: {audit['forecast_id']}")
    except Exception as e:
        print(f"❌ Failed to write forecast audit: {e}")
