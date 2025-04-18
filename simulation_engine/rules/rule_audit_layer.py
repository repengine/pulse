""" 
rule_audit_layer.py

Logs detailed audit traces for each rule executed during a simulation turn.
Captures:
- Rule ID and timestamp
- Symbolic tags
- Variable deltas (pre/post)
- Symbolic overlay deltas (pre/post)

This enables:
- Forecast scoring
- Drift monitoring
- Forecast memory justification

Author: Pulse v0.20
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
        after_val = state_after.variables.get(key)
        if after_val != before_val:
            var_deltas[key] = {"from": round(before_val, 4), "to": round(after_val, 4)}

    overlay_deltas = {}
    for key, before_val in state_before.overlays.as_dict().items():
        after_val = state_after.overlays.as_dict().get(key)
        if after_val != before_val:
            overlay_deltas[key] = {"from": round(before_val, 4), "to": round(after_val, 4)}

    return {
        "rule_id": rule_id,
        "timestamp": turn,
        "symbolic_tags": symbolic_tags,
        "variables_changed": var_deltas,
        "overlays_changed": overlay_deltas
    }