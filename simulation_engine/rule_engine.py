"""
rule_engine.py

Executes static causal rules to mutate WorldState based on conditions.
Returns a list of triggered rule audits for downstream scoring and memory.

Author: Pulse v0.20
"""

from simulation_engine.worldstate import WorldState
from simulation_engine.rules.static_rules import build_static_rules
from simulation_engine.rules.rule_audit_layer import audit_rule
import copy
from symbolic_system.symbolic_bias_tracker import SymbolicBiasTracker

bias_tracker = SymbolicBiasTracker()


def run_rules(state: WorldState, verbose: bool = True) -> list[dict]:
    """
    Executes all active causal rules on the current worldstate.

    Returns:
        list of rule audit entries with structure:
        {
            "rule_id": ...,
            "timestamp": ...,
            "symbolic_tags": [...],
            "variables_changed": {...},
            "overlays_changed": {...}
        }
    """
    rules = build_static_rules()
    execution_log = []

    for rule in rules:
        if not rule.get("enabled", True):
            continue
        try:
            if rule["condition"](state):
                state_before = copy.deepcopy(state)
                rule["effects"](state)
                audit = audit_rule(
                    rule_id=rule["id"],
                    state_before=state_before,
                    state_after=state,
                    symbolic_tags=rule.get("symbolic_tags", []),
                    turn=state.turn,
                )
                execution_log.append(audit)
                for tag in rule.get("symbolic_tags", []):
                    bias_tracker.record(tag)
                state.log_event(
                    f"Rule triggered: {rule['id']} → tags={rule.get('symbolic_tags')}"
                )
            elif verbose:
                state.log_event(f"Rule checked but not triggered: {rule['id']}")
        except Exception as e:
            state.log_event(f"[RULE ERROR] {rule['id']}: {e}")

    return execution_log
