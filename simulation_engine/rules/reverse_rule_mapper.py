"""
reverse_rule_mapper.py

Provides mapping between observed state changes (deltas) and candidate rules.
Supports partial/approximate matching, schema validation, and CLI.

Author: Pulse AI Engine
"""

import json
from typing import Dict, List, Tuple, Optional
from simulation_engine.rules.rule_registry import RuleRegistry

_registry = RuleRegistry()
_registry.load_all_rules()

def get_all_rule_fingerprints() -> List[Dict]:
    """
    Return all rule fingerprints from the unified registry.
    """
    return [r for r in _registry.rules if r.get("effects") or r.get("effect")]

def match_rule_by_delta(
    delta: Dict[str, float],
    fingerprints: Optional[List[Dict]] = None,
    min_match: float = 0.5
) -> List[Tuple[str, float]]:
    """
    Given a delta (dict of overlay/variable changes), return ranked candidate rule IDs.
    Supports partial/approximate matching.

    Args:
        delta: Dict of observed changes.
        fingerprints: List of rule fingerprints (dicts).
        min_match: Minimum match ratio (0-1) to include.

    Returns:
        List of (rule_id, match_score) tuples, sorted by score descending.
    """
    if fingerprints is None:
        fingerprints = get_all_rule_fingerprints()
    results = []
    for rule in fingerprints:
        effects = rule.get("effects", {})
        match_keys = set(delta) & set(effects)
        if not match_keys:
            continue
        score = sum(1 for k in match_keys if abs(effects[k] - delta[k]) < 1e-3) / max(len(effects), 1)
        if score >= min_match:
            results.append((rule.get("rule_id") or rule.get("id"), score))
    return sorted(results, key=lambda x: -x[1])

def validate_fingerprint_schema(fingerprints: List[Dict]) -> List[str]:
    """
    Validates that each fingerprint has required fields.
    Returns a list of errors.
    """
    errors = []
    for i, rule in enumerate(fingerprints):
        if "rule_id" not in rule and "id" not in rule or "effects" not in rule:
            errors.append(f"Entry {i} missing required fields: {rule}")
    return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rule Fingerprint Validator")
    parser.add_argument("--validate", action="store_true", help="Validate fingerprint schema")
    parser.add_argument("--match", nargs="+", help="Match delta: key1=val1 key2=val2 ...")
    args = parser.parse_args()
    if args.validate:
        fps = get_all_rule_fingerprints()
        errs = validate_fingerprint_schema(fps)
        if errs:
            print("❌ Schema errors:")
            for e in errs:
                print(" -", e)
        else:
            print("✅ All fingerprints valid.")
    elif args.match:
        delta = {}
        for kv in args.match:
            k, v = kv.split("=")
            delta[k] = float(v)
        matches = match_rule_by_delta(delta, get_all_rule_fingerprints())
        print("Matches:", matches)
    else:
        parser.print_help()
