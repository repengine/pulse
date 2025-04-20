"""
reverse_rule_engine.py

Builds a reverse causal graph from rule fingerprints.
Given observed deltas, traces possible rule chains that could have produced them.

Usage:
    python reverse_rule_engine.py --delta key1=val1 key2=val2 --max-depth 3

Related:
    - simulation_engine.rules.reverse_rule_mapper
    - simulation_engine.rules.rule_fingerprint_expander

Author: Pulse AI Engine
"""

from simulation_engine.rules.reverse_rule_mapper import load_rule_fingerprints, match_rule_by_delta
from simulation_engine.rules.rule_fingerprint_expander import expand_rule_fingerprints
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("reverse_rule_engine")

def trace_causal_paths(
    delta: Dict[str, float],
    fingerprints: Optional[List[Dict]] = None,
    max_depth: int = 3,
    min_match: float = 0.5,
    path: Optional[List[str]] = None
) -> List[List[str]]:
    """
    Given a delta, return possible rule chains (as lists of rule_ids) that could explain it.
    Recursively subtracts effects and searches for multi-step chains.

    Args:
        delta: Observed overlay/variable changes.
        fingerprints: List of rule fingerprints.
        max_depth: Max depth for recursive search.
        min_match: Minimum match ratio for candidate rules.
        path: Internal use for recursion.

    Returns:
        List of rule_id chains (each a list of rule_ids).

    The function works as follows:
    1. If fingerprints are not provided, it loads them using `load_rule_fingerprints`.
    2. If the recursion depth (`max_depth`) is zero or the delta is empty, it terminates.
    3. Matches rules against the delta using `match_rule_by_delta`.
    4. For each matched rule, subtracts its effects from the delta.
    5. Filters out near-zero deltas to avoid unnecessary recursion.
    6. If the new delta is empty, appends the current path to the chains.
    7. Otherwise, recursively calls itself to trace deeper causal paths.
    """
    if fingerprints is None:
        fingerprints = load_rule_fingerprints()
    if path is None:
        path = []
    if max_depth <= 0 or not delta:
        return []
    matches = match_rule_by_delta(delta, fingerprints, min_match=min_match)
    chains = []
    for rule_id, _ in matches:
        rule = next((r for r in fingerprints if r["rule_id"] == rule_id), None)
        if not rule:
            continue
        # Subtract effects from delta
        new_delta = {k: delta[k] - rule["effects"].get(k, 0.0) for k in delta}
        # Remove near-zero deltas
        new_delta = {k: v for k, v in new_delta.items() if abs(v) > 1e-3}
        if not new_delta:
            chains.append(path + [rule_id])
        else:
            subchains = trace_causal_paths(new_delta, fingerprints, max_depth-1, min_match, path + [rule_id])
            chains.extend(subchains)
    return chains

if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser(description="Reverse Rule Engine")
    parser.add_argument("--delta", nargs="+", help="Delta: key1=val1 key2=val2 ...")
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--min-match", type=float, default=0.5)
    parser.add_argument("--log", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    if args.log:
        logging.basicConfig(level=logging.DEBUG)
    if args.delta:
        try:
            delta = {}
            for kv in args.delta:
                k, v = kv.split("=")
                delta[k] = float(v)
            chains = trace_causal_paths(delta, max_depth=args.max_depth, min_match=args.min_match)
            print("Possible rule chains:", json.dumps(chains, indent=2))
        except Exception as e:
            logger.error(f"Error: {e}")
    else:
        parser.print_help()
