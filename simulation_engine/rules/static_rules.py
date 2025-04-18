""" 
static_rules.py

Defines a basic registry of static causal rules to be used in the Pulse simulation.
Each rule includes a trigger condition, an effect, symbolic tags, and optional flags.

Author: Pulse v0.10
"""

from core.pulse_config import CONFIDENCE_THRESHOLD
from core.variable_accessor import get_variable, set_variable

def build_static_rules():
    return [
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
            "condition": lambda s: get_variable(s, "public_trust_level") > 0.65,
            "effects": lambda s: set_variable(s, "ai_policy_risk", max(0, get_variable(s, "ai_policy_risk") - 0.02)),
            "symbolic_tags": ["hope", "stability"],
            "type": "regulatory",
            "enabled": True
        }
    ]