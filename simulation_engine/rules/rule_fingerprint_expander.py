"""
rule_fingerprint_expander.py

Suggests, validates, and auto-generates new rule fingerprints based on observed deltas.
Validates new rules against test data before integration.

Usage:
    python rule_fingerprint_expander.py --delta key1=val1 key2=val2 --rule-id NEW_RULE
    python rule_fingerprint_expander.py --validate rules/rule_fingerprints.json

Author: Pulse AI Engine
"""

import json
from .reverse_rule_mapper import load_rule_fingerprints, validate_fingerprint_schema

def suggest_fingerprint_from_delta(delta: dict, rule_id: str = None) -> dict:
    """
    Suggest a new fingerprint entry from an observed delta.
    """
    if not isinstance(delta, dict) or not delta:
        raise ValueError("Delta must be a non-empty dict")
    return {
        "rule_id": rule_id or "NEW_RULE",
        "effects": {k: float(v) for k, v in delta.items()}
    }

def validate_fingerprints_file(path: str):
    try:
        fps = load_rule_fingerprints(path)
        errors = validate_fingerprint_schema(fps)
        if errors:
            print("❌ Errors:")
            for e in errors:
                print(" -", e)
        else:
            print("✅ All fingerprints valid.")
    except Exception as e:
        print(f"Validation error: {e}")

def validate_new_rule(rule: dict, test_data: list) -> float:
    """
    Validate a new rule's predictive power against test data.
    Returns accuracy (0.0–1.0).
    """
    if not test_data:
        return 0.0
    correct = 0
    for delta in test_data:
        match = all(abs(delta.get(k, 0) - v) < 1e-3 for k, v in rule["effects"].items())
        if match:
            correct += 1
    return correct / len(test_data)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rule Fingerprint Expander")
    parser.add_argument("--delta", nargs="+", help="Delta: key1=val1 key2=val2 ...")
    parser.add_argument("--rule-id", type=str, default=None)
    parser.add_argument("--validate", type=str, help="Validate fingerprints file")
    parser.add_argument("--test-data", type=str, help="Path to test data (JSON list of deltas)")
    args = parser.parse_args()
    if args.delta:
        try:
            delta = {}
            for kv in args.delta:
                k, v = kv.split("=")
                delta[k] = float(v)
            fp = suggest_fingerprint_from_delta(delta, rule_id=args.rule_id)
            print(json.dumps(fp, indent=2))
            if args.test_data:
                with open(args.test_data, "r") as f:
                    test_data = json.load(f)
                acc = validate_new_rule(fp, test_data)
                print(f"Validation accuracy: {acc:.2f}")
        except Exception as e:
            print(f"Error: {e}")
    elif args.validate:
        validate_fingerprints_file(args.validate)
    else:
        parser.print_help()

# Example usage:
# python rule_fingerprint_expander.py --delta hope=0.1 despair=-0.05 --test-data test_deltas.json
