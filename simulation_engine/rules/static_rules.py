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

def build_static_rules():
    # Use config constants and module gating
    rules = [
        {
            "id": "R001_EnergySpike",
            "description": "High energy costs lead to rising inflation",
            "condition": lambda s: get_variable(s, "energy_price_index") > CONFIDENCE_THRESHOLD,
            "effects": lambda s: set_variable(s, "inflation_index", get_variable(s, "inflation_index") + 0.01),
            "symbolic_tags": ["fear", "despair"],
            "type": "economic",
            "enabled": True
        },
        {
            "id": "R002_TrustRebound",
            "description": "High public trust reduces AI regulatory pressure",
            "condition": lambda s: get_variable(s, "public_trust_level") > 0.65,  # Could add to config if reused
            "effects": lambda s: set_variable(s, "ai_policy_risk", max(0, get_variable(s, "ai_policy_risk") - 0.02)),
            "symbolic_tags": ["hope", "stability"],
            "type": "regulatory",
            "enabled": True
        }
    ]
    return rules

# Register static rules with the central registry if imported as main module
try:
    from simulation_engine.rules.rule_registry import RuleRegistry
    _static_rules = build_static_rules()
    registry = RuleRegistry()
    registry.static_rules = _static_rules
    registry.rules.extend(_static_rules)
except Exception as e:
    print(f"[static_rules] Could not register static rules: {e}")