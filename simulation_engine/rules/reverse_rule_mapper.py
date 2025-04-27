"""
reverse_rule_mapper.py

Maps observed state changes (deltas) to candidate rules using partial or approximate matching.

Responsibilities:
- Provide CLI and API for delta-to-rule mapping
- Use centralized matching/validation from rule_matching_utils

All rule matching logic should be imported from rule_matching_utils.
"""

import json
from typing import Dict, List, Tuple, Optional
from simulation_engine.rules.rule_matching_utils import (
    get_all_rule_fingerprints,
    match_rule_by_delta,
    validate_fingerprint_schema
)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rule Fingerprint Validator")
    parser.add_argument("--validate", action="store_true", help="Validate fingerprint schema")
    parser.add_argument("--match", nargs="+", help="Match delta: key1=val1 key2=val2 ...")
    args = parser.parse_args()
    if args.validate:
        fps = get_all_rule_fingerprints()
        if errs := validate_fingerprint_schema(fps):
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
