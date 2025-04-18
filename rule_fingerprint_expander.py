"""
rule_fingerprint_expander.py

Suggests, validates, and auto-generates new rule fingerprints based on observed deltas.
Intended for use with audit logs and simulation traces.

Usage:
    python rule_fingerprint_expander.py --delta key1=val1 key2=val2 --rule-id NEW_RULE
    python rule_fingerprint_expander.py --validate rules/rule_fingerprints.json

Related:
    - simulation_engine.rules.reverse_rule_mapper

Author: Pulse AI Engine
"""

import json
from simulation_engine.rules.reverse_rule_mapper import load_rule_fingerprints, validate_fingerprint_schema

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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rule Fingerprint Expander")
    parser.add_argument("--delta", nargs="+", help="Delta: key1=val1 key2=val2 ...")
    parser.add_argument("--rule-id", type=str, default=None)
    parser.add_argument("--validate", type=str, help="Validate fingerprints file")
    args = parser.parse_args()
    if args.delta:
        try:
            delta = {}
            for kv in args.delta:
                k, v = kv.split("=")
                delta[k] = float(v)
            fp = suggest_fingerprint_from_delta(delta, rule_id=args.rule_id)
            print(json.dumps(fp, indent=2))
        except Exception as e:
            print(f"Error: {e}")
    elif args.validate:
        validate_fingerprints_file(args.validate)
    else:
        parser.print_help()
