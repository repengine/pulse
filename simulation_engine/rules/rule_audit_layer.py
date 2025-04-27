"""
rule_audit_layer.py

Logs detailed audit traces for each rule executed during a simulation turn.

Responsibilities:
- Capture rule execution metadata (ID, tags, deltas, overlays)
- Enable forecast scoring, drift monitoring, and justification
- Should be used by simulation/forecast engines for traceability

This module does not perform rule matching or validation.
"""

from simulation_engine.worldstate import WorldState
from typing import Dict, Any


def audit_rule(
    rule_id: str,
    state_before: WorldState,
    state_after: WorldState,
    symbolic_tags: list[str],
    turn: int
) -> Dict[str, Any]:
    """
    Audits a single rule execution and returns structured trace.
    """
    var_deltas = {}
    for key, before_val in state_before.variables.as_dict().items():
        after_val = state_after.variables.as_dict().get(key)
        if after_val != before_val:
            if before_val is not None and after_val is not None:
                var_deltas[key] = {"from": round(before_val, 4), "to": round(after_val, 4)}
            else:
                var_deltas[key] = {"from": before_val, "to": after_val}

    overlay_deltas = {}
    for key, before_val in state_before.overlays.as_dict().items():
        after_val = state_after.overlays.as_dict().get(key)
        if after_val != before_val:
            if before_val is not None and after_val is not None:
                overlay_deltas[key] = {"from": round(before_val, 4), "to": round(after_val, 4)}
            else:
                overlay_deltas[key] = {"from": before_val, "to": after_val}

    return {
        "rule_id": rule_id,
        "timestamp": turn,
        "symbolic_tags": symbolic_tags,
        "variables_changed": var_deltas,
        "overlays_changed": overlay_deltas
    }