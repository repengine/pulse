"""
rule_registry.py

Central registry for all rule types in Pulse (static, fingerprint, candidate).

Responsibilities:
- Load, store, and export all rules
- Provide lookup and grouping by type or tag
- Delegate all validation to rule_coherence_checker

All rule access should go through this registry for consistency.
"""

from engine.path_registry import PATHS
import importlib
import json
from pathlib import Path
from rules.rule_coherence_checker import validate_rule_schema

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

print(
    f"[DEBUG] PATHS type in rule_registry: {type(PATHS)}"
)  # Add this line for debugging

RULES_LOG_PATH = PATHS.get("RULES_LOG_PATH", PATHS["WORLDSTATE_LOG_DIR"])


STATIC_RULES_MODULE = "engine.rules.static_rules"
FINGERPRINTS_PATH = Path(
    PATHS.get("RULE_FINGERPRINTS", "simulation_engine/rules/rule_fingerprints.json")
)
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
        # Use centralized schema/uniqueness validation
        rules_dict = {
            r.get("rule_id", r.get("id", str(i))): r for i, r in enumerate(self.rules)
        }
        return validate_rule_schema(rules_dict)

    def export_rules(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.rules, f, indent=2)
        print(f"Exported {len(self.rules)} rules to {path}")

    def add_rule(self, rule: dict):
        """Add a new rule to the registry, enforcing schema."""
        required_fields = ["symbolic_tags", "source", "trust_weight", "enabled", "type"]
        for field in required_fields:
            if field not in rule:
                raise ValueError(f"Rule missing required field: {field}")
        self.rules.append(rule)
        print(f"[RuleRegistry] Rule added: {rule.get('id') or rule.get('rule_id')}")

    def promote_candidate(self, rule_id: str):
        """Promote a candidate rule to active registry and set enabled=True."""
        for rule in self.candidate_rules:
            if rule.get("rule_id") == rule_id or rule.get("id") == rule_id:
                rule["enabled"] = True
                self.rules.append(rule)
                self.candidate_rules.remove(rule)
                print(f"[RuleRegistry] Candidate promoted: {rule_id}")
                return
        print(f"[RuleRegistry] Candidate rule not found: {rule_id}")

    def update_trust_score(self, rule_id, delta):
        """Update trust_weight for a rule by delta."""
        for rule in self.rules:
            if rule.get("rule_id") == rule_id or rule.get("id") == rule_id:
                old = rule.get("trust_weight", 1.0)
                rule["trust_weight"] = round(old + delta, 3)
                print(
                    f"[RuleRegistry] Trust updated for {rule_id}: {old} -> {rule['trust_weight']}"
                )
                return
        print(f"[RuleRegistry] Rule not found: {rule_id}")

    def get_rules_by_symbolic_tag(self, tag):
        """Return all rules with a given symbolic tag."""
        return [r for r in self.rules if tag in r.get("symbolic_tags", [])]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Unified Rule Registry CLI")
    parser.add_argument("--list", action="store_true", help="List all rules")
    parser.add_argument("--validate", action="store_true", help="Validate all rules")
    parser.add_argument("--export", type=str, help="Export all rules to file")
    parser.add_argument("--promote", type=str, help="Promote candidate rule by rule_id")
    parser.add_argument("--disable", type=str, help="Disable rule by rule_id")
    parser.add_argument("--trust", nargs=2, help="Update trust score: rule_id delta")
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
    if args.promote:
        reg.promote_candidate(args.promote)
    if args.disable:
        for rule in reg.rules:
            if rule.get("rule_id") == args.disable or rule.get("id") == args.disable:
                rule["enabled"] = False
                print(f"[RuleRegistry] Rule disabled: {args.disable}")
                break
        else:
            print(f"[RuleRegistry] Rule not found: {args.disable}")
    if args.trust:
        rule_id, delta = args.trust
        try:
            reg.update_trust_score(rule_id, float(delta))
        except Exception as e:
            print(f"[RuleRegistry] Trust update error: {e}")
