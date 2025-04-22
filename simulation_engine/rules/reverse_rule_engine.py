"""
reverse_rule_engine.py

Builds a reverse causal graph from rule fingerprints.
Given observed deltas, traces possible rule chains that could have produced them.
Supports fuzzy matching for approximate rule identification.
Ranks rules by trust/frequency and suggests new rules if no match is found.

Usage:
    python reverse_rule_engine.py --delta key1=val1 key2=val2 --max-depth 3 --fuzzy
    python reverse_rule_engine.py --delta key1=val1 key2=val2 --fingerprints path/to/fingerprints.json --tol 0.05

Related:
    - simulation_engine.rules.reverse_rule_mapper
    - simulation_engine.rules.rule_fingerprint_expander

Author: Pulse AI Engine
"""

from simulation_engine.rules.reverse_rule_mapper import load_rule_fingerprints, match_rule_by_delta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("reverse_rule_engine")

def levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein distance between two strings."""
    if a == b: return 0
    if not a: return len(b)
    if not b: return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            insert = curr[-1] + 1
            delete = prev[j] + 1
            replace = prev[j-1] + (ca != cb)
            curr.append(min(insert, delete, replace))
        prev = curr
    return prev[-1]

def fuzzy_match_rule_by_delta(
    delta: dict, fingerprints: list, tol: float = 0.05, min_conf: float = 0.0, confidence_threshold: float = 0.0
) -> list:
    """
    Fuzzy match: allow numeric differences up to tol (absolute).
    Returns list of (rule_id, confidence_score) above min_conf and confidence_threshold.

    Example:
        matches = fuzzy_match_rule_by_delta({"hope": 0.1}, fingerprints, tol=0.1, min_conf=0.7, confidence_threshold=0.5)
    """
    matches = []
    for rule in fingerprints:
        diffs = [abs(delta.get(k, 0) - rule.get("effects", {}).get(k, 0)) for k in delta]
        max_diff = max(diffs) if diffs else 0
        if all(d <= tol for d in diffs):
            confidence = 1 - max_diff
            if confidence >= min_conf and confidence >= confidence_threshold:
                matches.append((rule.get("rule_id", "unknown"), confidence))
    return sorted(matches, key=lambda x: -x[1])

def rank_rules_by_trust(matches: List[tuple], fingerprints: List[Dict]) -> List[tuple]:
    """
    Rank matched rules by trust/frequency if available.
    """
    def get_trust(rule_id):
        for fp in fingerprints:
            if fp.get("rule_id") == rule_id:
                return fp.get("trust", 0) + fp.get("frequency", 0)
        return 0
    return sorted(matches, key=lambda x: get_trust(x[0]), reverse=True)

def suggest_new_rule_if_no_match(delta: Dict[str, float], fingerprints: List[Dict]) -> Dict:
    """
    Suggest a new rule fingerprint if no match is found.
    """
    if not fingerprints or not delta:
        return {}
    from simulation_engine.rules.rule_fingerprint_expander import suggest_fingerprint_from_delta
    return suggest_fingerprint_from_delta(delta)

def trace_causal_paths(
    delta: Dict[str, float],
    fingerprints: Optional[List[Dict]] = None,
    max_depth: int = 3,
    min_match: float = 0.5,
    path: Optional[List[str]] = None,
    fuzzy: bool = False,
    confidence_threshold: float = 0.0
) -> List[List[str]]:
    """
    Given a delta, return possible rule chains (as lists of rule_ids) that could explain it.
    Recursively subtracts effects and searches for multi-step chains.
    Supports fuzzy matching if enabled.
    Ranks by trust/frequency if available. Suggests new rule if no match.

    Args:
        delta: Observed overlay/variable changes.
        fingerprints: List of rule fingerprints.
        max_depth: Max depth for recursive search.
        min_match: Minimum match ratio for candidate rules.
        path: Internal use for recursion.
        fuzzy: Use fuzzy key matching.
        confidence_threshold: Minimum confidence score for rule matches.

    Returns:
        List of rule_id chains (each a list of rule_ids).
    """
    if fingerprints is None:
        fingerprints = load_rule_fingerprints()
    if path is None:
        path = []
    if max_depth <= 0 or not delta:
        return []
    if fuzzy:
        matches = fuzzy_match_rule_by_delta(delta, fingerprints, confidence_threshold=confidence_threshold)
    else:
        matches = match_rule_by_delta(delta, fingerprints, min_match=min_match)
    matches = rank_rules_by_trust(matches, fingerprints)
    chains = []
    for rule_id, *_ in matches:
        rule = next((r for r in fingerprints if r["rule_id"] == rule_id), None)
        if not rule:
            continue
        new_delta = {k: delta[k] - rule["effects"].get(k, 0.0) for k in delta}
        new_delta = {k: v for k, v in new_delta.items() if abs(v) > 1e-3}
        if not new_delta:
            chains.append(path + [rule_id])
        else:
            subchains = trace_causal_paths(new_delta, fingerprints, max_depth-1, min_match, path + [rule_id], fuzzy=fuzzy, confidence_threshold=confidence_threshold)
            chains.extend(subchains)
    if not chains and delta:
        # No match found, suggest new rule
        suggestion = suggest_new_rule_if_no_match(delta, fingerprints)
        if suggestion:
            chains.append(["SUGGEST_NEW_RULE", suggestion])
    return chains

def compute_match_score(input_data: dict, rule: dict) -> float:
    """
    Compute a simple match score between input_data and rule's effects.
    Score is 1.0 if all keys match exactly, otherwise decreases with difference.
    """
    effects = rule.get("effects", {})
    if not input_data or not effects:
        return 0.0
    keys = set(input_data.keys()) | set(effects.keys())
    if not keys:
        return 0.0
    total_diff = 0.0
    for k in keys:
        v1 = input_data.get(k, 0.0)
        v2 = effects.get(k, 0.0)
        total_diff += abs(v1 - v2)
    # Normalize: higher score for smaller difference
    score = max(0.0, 1.0 - total_diff / (len(keys) or 1))
    return score

def match_rules(input_data, rules, confidence_threshold: float = 0.0):
    """Match input data to rules, returning only those above the confidence threshold."""
    matches = []
    for rule in rules:
        score = compute_match_score(input_data, rule)
        if score >= confidence_threshold:
            matches.append((rule, score))
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches

if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser(description="Reverse Rule Engine")
    parser.add_argument("--delta", nargs="+", help="Delta: key1=val1 key2=val2 ...")
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--min-match", type=float, default=0.5)
    parser.add_argument("--fuzzy", action="store_true", help="Enable fuzzy key matching")
    parser.add_argument("--log", action="store_true", help="Enable debug logging")
    parser.add_argument("--fingerprints", type=str, help="Path to fingerprints JSON")
    parser.add_argument("--tol", type=float, default=0.05, help="Tolerance for fuzzy match")
    parser.add_argument("--min-conf", type=float, default=0.0, help="Minimum confidence score")
    parser.add_argument("--confidence-threshold", type=float, default=0.0, help="Confidence threshold for rule matches")
    args = parser.parse_args()
    if args.log:
        logging.basicConfig(level=logging.DEBUG)
    if args.delta:
        try:
            delta = {}
            for kv in args.delta:
                k, v = kv.split("=")
                delta[k] = float(v)
            if args.fingerprints:
                with open(args.fingerprints, "r", encoding="utf-8") as f:
                    fingerprints = json.load(f)
                matches = fuzzy_match_rule_by_delta(delta, fingerprints, tol=args.tol, min_conf=args.min_conf, confidence_threshold=args.confidence_threshold)
                for rule_id, conf in matches:
                    print(f"{rule_id}: confidence={conf:.3f}")
                if not matches:
                    print("No matches found.")
            else:
                chains = trace_causal_paths(delta, max_depth=args.max_depth, min_match=args.min_match, fuzzy=args.fuzzy, confidence_threshold=args.confidence_threshold)
                print("Possible rule chains:", json.dumps(chains, indent=2))
        except Exception as e:
            logger.error(f"Error: {e}")
    else:
        parser.print_help()

# Example usage:
# python reverse_rule_engine.py --delta hope=0.1 despair=-0.05 --fuzzy
# python reverse_rule_engine.py --delta hope=0.1 despair=-0.05 --fingerprints path/to/fingerprints.json --tol 0.05 --min-conf 0.7 --confidence-threshold 0.5
