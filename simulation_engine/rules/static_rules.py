""" 
static_rules.py

Defines a basic registry of static causal rules to be used in the Pulse simulation.
Each rule includes a trigger condition, an effect, symbolic tags, and optional flags.

Author: Pulse v0.10
"""

from core.pulse_config import CONFIDENCE_THRESHOLD, DEFAULT_FRAGILITY_THRESHOLD
from core.variable_accessor import get_variable, set_variable, get_overlay
from core.path_registry import PATHS
# from forecast_tags import ... # Uncomment and use if forecast_tags are needed

from pipeline.rule_applier import load_proposed_rule_changes, apply_rule_changes

def build_static_rules(param_overrides=None):
    """
    Build static rules with optional parameter overrides and apply proposed changes.
    param_overrides: dict of {rule_id: {param_name: value}}
    """
    param_overrides = param_overrides or {}
    rules = [
        {
            "id": "R001_EnergySpike",
            "description": "High energy costs lead to rising inflation",
            "threshold": param_overrides.get("R001_EnergySpike", {}).get("threshold", CONFIDENCE_THRESHOLD),
            "effect_size": param_overrides.get("R001_EnergySpike", {}).get("effect_size", 0.01),
            "condition": lambda s, th=None: get_variable(s, "energy_price_index") > (th if th is not None else CONFIDENCE_THRESHOLD),
            "effects": lambda s, eff=None: set_variable(s, "inflation_index", get_variable(s, "inflation_index") + (eff if eff is not None else 0.01)),
            "symbolic_tags": ["fear", "despair"],
            "type": "economic",
            "enabled": True
        },
        {
            "id": "R002_TrustRebound",
            "description": "High public trust reduces AI regulatory pressure",
            "threshold": param_overrides.get("R002_TrustRebound", {}).get("threshold", 0.65),
            "effect_size": param_overrides.get("R002_TrustRebound", {}).get("effect_size", 0.02),
            "condition": lambda s, th=None: get_variable(s, "public_trust_level") > (th if th is not None else 0.65),
            "effects": lambda s, eff=None: set_variable(s, "ai_policy_risk", max(0, get_variable(s, "ai_policy_risk") - (eff if eff is not None else 0.02))),
            "symbolic_tags": ["hope", "stability"],
            "type": "regulatory",
            "enabled": True
        }
    ]

    # Load and apply proposed rule changes
    proposed_changes = load_proposed_rule_changes()
    if proposed_changes:
        rules = apply_rule_changes(proposed_changes, rules)

    return rules