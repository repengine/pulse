"""
rule_fingerprint_expander.py

Expands and suggests new rules based on symbolic overlays and trust weighting.
Supports approval workflow for new rules (stub).

Usage:
    python rule_fingerprint_expander.py --delta key1=val1 key2=val2 --rule-id NEW_RULE
    python rule_fingerprint_expander.py --validate rules/rule_fingerprints.json
    python rule_fingerprint_expander.py --input forecasts.json --min-conf 0.7
    submit_rule_for_approval(rule)  # New: submit rule for approval

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

def suggest_fingerprints(forecasts: list, min_conf: float = 0.7) -> list:
    """
    Suggest new rule fingerprints, weighted by forecast trust/confidence.

    Args:
        forecasts: List of forecast dicts.
        min_conf: Minimum confidence to consider.

    Returns:
        List of suggestions sorted by weight.
    """
    suggestions = []
    for f in forecasts:
        conf = f.get("confidence", 0)
        if conf >= min_conf:
            suggestions.append({"trace_id": f["trace_id"], "weight": conf, "effects": f.get("effects", {})})
    # Sort by weight
    return sorted(suggestions, key=lambda x: -x["weight"])

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

import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def submit_rule_for_approval(rule, approver: str = None):
    """Stub: Submit a new rule for approval. In production, this would route to a review queue or require multi-party signoff."""
    logger.info(f"Rule submitted for approval: {rule} (approver: {approver})")
    # Placeholder for approval workflow logic
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rule Fingerprint Suggestion Review CLI")
    parser.add_argument("--delta", nargs="+", help="Delta: key1=val1 key2=val2 ...")
    parser.add_argument("--rule-id", type=str, default=None)
    parser.add_argument("--validate", type=str, help="Validate fingerprints file")
    parser.add_argument("--test-data", type=str, help="Path to test data (JSON list of deltas)")
    parser.add_argument("--input", type=str, required=True, help="Forecasts JSON file")
    parser.add_argument("--min-conf", type=float, default=0.7, help="Minimum confidence")
    parser.add_argument("--approve", action="store_true", help="Interactive approval workflow")
    parser.add_argument("--output", type=str, default=None, help="Output file for approved suggestions")
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
        with open(args.input, "r", encoding="utf-8") as f:
            forecasts = json.load(f)
        suggestions = suggest_fingerprints(forecasts, min_conf=args.min_conf)
        approved = []
        if args.approve:
            for s in suggestions:
                print(json.dumps(s, indent=2))
                resp = input("Approve this suggestion? [y/N]: ").strip().lower()
                if resp == "y":
                    s["approved"] = True
                    approved.append(s)
                else:
                    s["approved"] = False
            print(f"Approved {len([s for s in approved if s['approved']])} of {len(suggestions)} suggestions.")
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump([s for s in approved if s["approved"]], f, indent=2)
                print(f"Approved suggestions written to {args.output}")
        else:
            for s in suggestions:
                print(json.dumps(s, indent=2))
            print(f"Total suggestions: {len(suggestions)}")

# Example usage:
# python rule_fingerprint_expander.py --delta hope=0.1 despair=-0.05 --test-data test_deltas.json
# python rule_fingerprint_expander.py --input forecasts.json --min-conf 0.7 --approve --output approved_suggestions.json
