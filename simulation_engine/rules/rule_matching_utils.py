"""
rule_matching_utils.py

Centralized utilities for rule matching and validation in Pulse.

Responsibilities:
- Provide all delta-to-rule matching (exact, partial, fuzzy)
- Provide a single interface for rule fingerprint access
- Provide a wrapper for schema/uniqueness validation (delegates to rule_coherence_checker)

All rule-related modules should import matching and validation logic from here.
"""

from typing import Dict, List, Optional, Tuple
from simulation_engine.rules.rule_registry import RuleRegistry
from simulation_engine.rules.rule_coherence_checker import validate_rule_schema, get_all_rule_fingerprints_dict

_registry = RuleRegistry()
_registry.load_all_rules()

def get_all_rule_fingerprints() -> List[Dict]:
    """Return all rule fingerprints from the unified registry."""
    return [r for r in _registry.rules if r.get("effects") or r.get("effect")]

def validate_fingerprint_schema(fingerprints: list) -> list:
    """Wrapper for backward compatibility. Uses centralized validate_rule_schema."""
    rules_dict = {r.get("rule_id", r.get("id", str(i))): r for i, r in enumerate(fingerprints)}
    return validate_rule_schema(rules_dict)

def match_rule_by_delta(
    delta: Dict[str, float],
    fingerprints: Optional[List[Dict]] = None,
    min_match: float = 0.5
) -> List[Tuple[str, float]]:
    """
    Given a delta (dict of overlay/variable changes), return ranked candidate rule IDs.
    Supports partial/approximate matching.
    """
    if fingerprints is None:
        fingerprints = get_all_rule_fingerprints()
    results = []
    for rule in fingerprints:
        effects = rule.get("effects", {})
        match_keys = set(delta) & set(effects)
        if not match_keys:
            continue
        score = sum(abs(effects[k] - delta[k]) < 1e-3 for k in match_keys) / max(len(effects), 1)
        if score >= min_match:
            results.append((rule.get("rule_id") or rule.get("id"), score))
    return sorted(results, key=lambda x: -x[1])

def fuzzy_match_rule_by_delta(
    delta: Dict[str, float],
    fingerprints: Optional[List[Dict]] = None,
    tol: float = 0.05,
    min_conf: float = 0.0,
    confidence_threshold: float = 0.0
) -> List[Tuple[str, float]]:
    """
    Fuzzy match: allow numeric differences up to tol (absolute).
    Returns list of (rule_id, confidence_score) above min_conf and confidence_threshold.
    """
    if fingerprints is None:
        fingerprints = get_all_rule_fingerprints()
    matches = []
    for rule in fingerprints:
        diffs = [abs(delta.get(k, 0) - rule.get("effects", {}).get(k, 0)) for k in delta]
        max_diff = max(diffs) if diffs else 0
        if all(d <= tol for d in diffs):
            confidence = 1 - max_diff
            if confidence >= min_conf and confidence >= confidence_threshold:
                matches.append((rule.get("rule_id", "unknown"), confidence))
    return sorted(matches, key=lambda x: -x[1])
