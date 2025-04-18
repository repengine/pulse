""" 
static_rules.py

Defines a basic registry of static causal rules to be used in the Pulse simulation.
Each rule includes a trigger condition, an effect, symbolic tags, and optional flags.

Author: Pulse v0.10
"""

def build_static_rules():
    return [
        {
            "id": "R001_EnergySpike",
            "description": "High energy costs lead to rising inflation",
            "condition": lambda s: s.get_variable("energy_price_index") > 0.7,
            "effects": lambda s: s.update_variable("inflation_index", s.get_variable("inflation_index") + 0.01),
            "symbolic_tags": ["fear", "despair"],
            "type": "economic",
            "enabled": True
        },
        {
            "id": "R002_TrustRebound",
            "description": "High public trust reduces AI regulatory pressure",
            "condition": lambda s: s.get_variable("public_trust_level") > 0.65,
            "effects": lambda s: s.update_variable("ai_policy_risk", max(0, s.get_variable("ai_policy_risk") - 0.02)),
            "symbolic_tags": ["hope", "stability"],
            "type": "regulatory",
            "enabled": True
        }
    ]