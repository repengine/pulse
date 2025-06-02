"""
rule_param_registry.py

Defines tunable parameters for each rule and their valid ranges.
"""

RULE_PARAM_REGISTRY = {
    "R001_EnergySpike": {
        "threshold": {"type": "float", "default": 0.5, "low": 0.1, "high": 2.0},
        "effect_size": {"type": "float", "default": 0.01, "low": 0.001, "high": 0.05},
    },
    "R002_TrustRebound": {
        "threshold": {"type": "float", "default": 0.65, "low": 0.3, "high": 1.0},
        "effect_size": {"type": "float", "default": 0.02, "low": 0.001, "high": 0.05},
    },
}
