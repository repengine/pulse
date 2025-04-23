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

import importlib
import json
from pathlib import Path

STATIC_RULES_MODULE = "simulation_engine.rules.static_rules"
FINGERPRINTS_PATH = Path(PATHS.get("RULE_FINGERPRINTS", "simulation_engine/rules/rule_fingerprints.json"))
CANDIDATE_RULES_PATH = Path(PATHS.get("CANDIDATE_RULES", "data/candidate_rules.json"))

class RuleRegistry:
    def __init__(self):
        self.rules = []
        self.static_rules = []
        self.fingerprint_rules = []
        self.candidate_rules = []

    def load_static_rules(self):
        try:
            static_mod = importlib.import_module(STATIC_RULES_MODULE)
            self.static_rules = static_mod.build_static_rules()
        except Exception as e:
            print(f"[RuleRegistry] Error loading static rules: {e}")
            self.static_rules = []

    def load_fingerprint_rules(self):
        try:
            with open(FINGERPRINTS_PATH, "r", encoding="utf-8") as f:
                self.fingerprint_rules = json.load(f)
        except Exception as e:
            print(f"[RuleRegistry] Error loading fingerprint rules: {e}")
            self.fingerprint_rules = []

    def load_candidate_rules(self):
        if not CANDIDATE_RULES_PATH.exists():
            self.candidate_rules = []
            return
        try:
            with open(CANDIDATE_RULES_PATH, "r", encoding="utf-8") as f:
                self.candidate_rules = json.load(f)
        except Exception as e:
            print(f"[RuleRegistry] Error loading candidate rules: {e}")
            self.candidate_rules = []

    def load_all_rules(self):
        self.load_static_rules()
        self.load_fingerprint_rules()
        self.load_candidate_rules()
        self.rules = self.static_rules + self.fingerprint_rules + self.candidate_rules

    def get_rules_by_type(self, rule_type: str):
        return [r for r in self.rules if r.get("type") == rule_type]

    def validate(self):
        errors = []
        seen_ids = set()
        for i, rule in enumerate(self.rules):
            rid = rule.get("id") or rule.get("rule_id")
            if not rid:
                errors.append(f"Rule {i} missing id/rule_id: {rule}")
            elif rid in seen_ids:
                errors.append(f"Duplicate rule id: {rid}")
            else:
                seen_ids.add(rid)
            if not rule.get("effects") and not rule.get("effect"):
                errors.append(f"Rule {rid} missing effects/effect field")
        return errors

    def export_rules(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.rules, f, indent=2)
        print(f"Exported {len(self.rules)} rules to {path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Unified Rule Registry CLI")
    parser.add_argument("--list", action="store_true", help="List all rules")
    parser.add_argument("--validate", action="store_true", help="Validate all rules")
    parser.add_argument("--export", type=str, help="Export all rules to file")
    args = parser.parse_args()
    reg = RuleRegistry()
    reg.load_all_rules()
    if args.list:
        for rule in reg.rules:
            print(json.dumps(rule, indent=2))
    if args.validate:
        errs = reg.validate()
        if errs:
            print("❌ Validation errors:")
            for e in errs:
                print(" -", e)
        else:
            print("✅ All rules valid.")
    if args.export:
        reg.export_rules(args.export)