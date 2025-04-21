""" 
rule_registry.py

Planned future unification point for all rule types in Pulse:
- Symbolic rules
- Capital rules
- Causal rules
- Strategic triggers

This module will allow rule lookup, grouping, versioning, and validation.

Author: Pulse v0.20 (scaffolded at v0.10)
"""

from core.path_registry import PATHS
assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"
from core.pulse_config import MODULES_ENABLED

print(f"[DEBUG] PATHS type in rule_registry: {type(PATHS)}")  # Add this line for debugging

RULES_LOG_PATH = PATHS.get("RULES_LOG_PATH", PATHS["WORLDSTATE_LOG_DIR"])

# Placeholder schema
class RuleRegistry:
    def __init__(self):
        self.rules = []

    def load_all_rules(self):
        # Future: Load from YAML, DB, DSL, code
        pass

    def get_rules_by_type(self, rule_type: str):
        return [r for r in self.rules if r.get("type") == rule_type]

    def validate(self):
        # Future: Validate rule schema, collisions, tagging integrity
        pass