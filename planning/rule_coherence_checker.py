"""
Module: rule_coherence_checker.py
Pulse Version: v0.100.3
Location: planning/

Purpose:
Scans rule_fingerprints.json to detect logical inconsistencies, loops, or contradictory effects.
Also surfaces duplicate and redundant rules for review.

Features:
- Detect conflicting triggers (e.g., same input causes opposite symbolic changes)
- Detect contradictory effects across similar rules
- Detect cycles in causal rule chains (TBD)
- Report redundant or duplicate rules

Author: Pulse AI Engine
"""

import json
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger("rule_coherence_checker")

def load_rule_fingerprints(path: str = "data/rule_fingerprints.json") -> Dict:
    """Load rule fingerprints from a JSON file."""
    with open(path, "r") as f:
        return json.load(f)

def detect_conflicting_triggers(rules: Dict[str, Dict]) -> List[Tuple[str, str, str]]:
    """
    Detect rules with conflicting symbolic triggers on the same input.
    Returns a list of (rule_id1, rule_id2, description).
    """
    conflicts = []
    trigger_map = {}
    for rid, rule in rules.items():
        trig = str(rule.get("trigger"))
        if trig not in trigger_map:
            trigger_map[trig] = [rid]
        else:
            for existing in trigger_map[trig]:
                if rule.get("effect") != rules[existing].get("effect"):
                    conflicts.append((existing, rid, "Same trigger, different effects"))
            trigger_map[trig].append(rid)
    return conflicts

def detect_opposite_effects(rules: Dict[str, Dict]) -> List[Tuple[str, str, str]]:
    """
    Detect rules that produce opposite effects on same variable.
    Returns a list of (rule_id1, rule_id2, description).
    """
    conflicts = []
    for id1, r1 in rules.items():
        for id2, r2 in rules.items():
            if id1 >= id2: continue
            eff1 = r1.get("effect", {})
            eff2 = r2.get("effect", {})
            for k in eff1:
                if k in eff2 and eff1[k] != eff2[k] and eff1[k].startswith("+-") or eff2[k].startswith("-+"):
                    conflicts.append((id1, id2, f"Opposite effect on {k}"))
    return conflicts

def detect_duplicate_rules(rules: Dict[str, Dict]) -> List[Tuple[str, str]]:
    """
    Detect rules that are structurally identical.
    Returns a list of (rule_id1, rule_id2).
    """
    seen = {}
    dups = []
    for rid, rule in rules.items():
        sig = json.dumps({"trigger": rule.get("trigger"), "effect": rule.get("effect")}, sort_keys=True)
        if sig in seen:
            dups.append((seen[sig], rid))
        else:
            seen[sig] = rid
    return dups

def scan_rule_coherence(fpath: str = "data/rule_fingerprints.json") -> Dict:
    """
    Scan rule fingerprints for coherence issues.
    Returns a dict with lists of conflicts and duplicates.
    """
    try:
        rules = load_rule_fingerprints(fpath)
    except Exception as e:
        logger.error(f"Failed to load rule fingerprints: {e}")
        return {}
    result = {
        "conflicting_triggers": detect_conflicting_triggers(rules),
        "opposite_effects": detect_opposite_effects(rules),
        "duplicate_rules": detect_duplicate_rules(rules),
        "total_rules": len(rules)
    }
    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pulse Rule Coherence Checker")
    parser.add_argument("--file", default="data/rule_fingerprints.json", help="Path to rule fingerprint file")
    args = parser.parse_args()

    result = scan_rule_coherence(args.file)
    print(json.dumps(result, indent=2))
