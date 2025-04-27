"""
rule_coherence_checker.py

Scans all rule fingerprints for logical, structural, and schema errors.

Responsibilities:
- Central source for schema, uniqueness, and logical validation
- Detects conflicting triggers, opposite effects, and duplicate rules
- Used by all rule modules for validation

All validation logic should be added here for consistency.
"""

import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from simulation_engine.rules.rule_matching_utils import get_all_rule_fingerprints

# Use centralized get_all_rule_fingerprints for all rule access

def get_all_rule_fingerprints_dict() -> dict:
    """Retrieve all rule fingerprints as a dict keyed by rule_id."""
    return {r.get("rule_id", r.get("id", str(i))): r for i, r in enumerate(get_all_rule_fingerprints())}

def validate_rule_schema(rules: Dict[str, Dict]) -> List[str]:
    """Validate schema and uniqueness for all rules."""
    errors = []
    seen_ids = set()
    for i, (rid, rule) in enumerate(rules.items()):
        rule_id = rule.get("rule_id") or rule.get("id")
        if not rule_id:
            errors.append(f"Rule {i} missing id/rule_id: {rule}")
        elif rule_id in seen_ids:
            errors.append(f"Duplicate rule id: {rule_id}")
        else:
            seen_ids.add(rule_id)
        if not rule.get("effects") and not rule.get("effect"):
            errors.append(f"Rule {rule_id} missing effects/effect field")
    return errors

def detect_conflicting_triggers(rules: Dict[str, Dict]) -> List[Tuple[str, str, str]]:
    """Detect rules with conflicting symbolic triggers on the same input."""
    conflicts = []
    trigger_map = {}
    for rid, rule in rules.items():
        trig = str(rule.get("trigger"))
        if trig not in trigger_map:
            trigger_map[trig] = [rid]
        else:
            conflicts.extend(
                (existing, rid, "Same trigger, different effects")
                for existing in trigger_map[trig]
                if rule.get("effect") != rules[existing].get("effect")
            )
            trigger_map[trig].append(rid)
    return conflicts

def detect_opposite_effects(rules: Dict[str, Dict]) -> List[Tuple[str, str, str]]:
    """Detect rules that produce opposite effects on same variable."""
    conflicts = []
    for id1, r1 in rules.items():
        for id2, r2 in rules.items():
            if id1 >= id2: continue
            eff1 = r1.get("effect", {})
            eff2 = r2.get("effect", {})
            for k in eff1:
                if (
                    k in eff2
                    and eff1[k] != eff2[k]
                    and (eff1[k].startswith("+-") or eff2[k].startswith("-+"))
                ):
                    conflicts.append((id1, id2, f"Opposite effect on {k}"))
    return conflicts

def detect_duplicate_rules(rules: Dict[str, Dict]) -> List[Tuple[str, str]]:
    """Detect rules that are structurally identical."""
    seen = {}
    dups = []
    for rid, rule in rules.items():
        sig = json.dumps({"trigger": rule.get("trigger"), "effect": rule.get("effect")}, sort_keys=True)
        if sig in seen:
            dups.extend([(seen[sig], rid)])
        else:
            seen[sig] = rid
    return dups

def scan_rule_coherence() -> Dict:
    rules = get_all_rule_fingerprints_dict()
    result = {
        "schema_errors": validate_rule_schema(rules),
        "conflicting_triggers": detect_conflicting_triggers(rules),
        "opposite_effects": detect_opposite_effects(rules),
        "duplicate_rules": detect_duplicate_rules(rules),
        "total_rules": len(rules)
    }
    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pulse Rule Coherence Checker")
    args = parser.parse_args()
    result = scan_rule_coherence()
    print(json.dumps(result, indent=2))