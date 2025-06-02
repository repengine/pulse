"""
rule_mutation_engine.py

Proposes and applies mutations to causal rule weights, thresholds, or structures
based on retrodiction error, symbolic misalignment, or trust regret.

Author: Pulse v0.36
"""

import random
import json
import logging
from typing import Dict, List, Any

from engine.path_registry import PATHS
from analytics.rule_cluster_engine import score_rule_volatility
from rules.rule_registry import RuleRegistry
from analytics.pulse_learning_log import log_learning_event
from datetime import datetime

RULE_MUTATION_LOG = PATHS.get("RULE_MUTATION_LOG", "logs/rule_mutation_log.jsonl")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

_registry = RuleRegistry()
_registry.load_all_rules()


def get_all_rules() -> dict:
    """Return all rules from the unified registry keyed by rule_id or id."""
    return {
        r.get("rule_id", r.get("id", str(i))): r for i, r in enumerate(_registry.rules)
    }


def propose_rule_mutations(
    rules: Dict[str, Dict[str, Any]], top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Proposes mutations to the top-N rules.
    Mutates the 'threshold' field within [0, 1] bounds.
    Favors rules from high-volatility clusters.
    """
    if not rules:
        logging.warning("No rules to mutate.")
        return []
    volatility = score_rule_volatility(rules)
    sorted_rules = sorted(
        rules.items(), key=lambda x: volatility.get(x[0], 0), reverse=True
    )
    candidates = sorted_rules[:top_n]
    mutations = []
    for rule_id, rule in candidates:
        old = rule.get("threshold", 0.5)
        if not isinstance(old, (int, float)):
            logging.warning(f"Rule {rule_id} has invalid threshold: {old}")
            continue
        # Mutate threshold by up to ±20%, clamp to [0, 1]
        new_threshold = round(max(0.0, min(1.0, old * random.uniform(0.8, 1.2))), 3)
        rule["threshold"] = new_threshold
        mutations.append({"rule": rule_id, "from": old, "to": new_threshold})
        logging.info(f"Mutated rule {rule_id}: threshold {old} -> {new_threshold}")
        log_learning_event(
            "rule_mutation",
            {
                "rule_id": rule_id,
                "from": old,
                "to": new_threshold,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    return mutations


def apply_rule_mutations() -> None:
    """
    Loads rules, applies mutations, saves, and logs the changes.
    """
    rules = get_all_rules()
    if not rules:
        print("[RuleMutation] No rules loaded.")
        return

    mutations = propose_rule_mutations(rules)
    if not mutations:
        print("[RuleMutation] No mutations proposed.")
        return

    try:
        with open(RULE_MUTATION_LOG, "a", encoding="utf-8") as f:
            for m in mutations:
                f.write(json.dumps({"mutation": m}) + "\n")
        print(f"✅ Applied {len(mutations)} rule mutations.")
        log_learning_event(
            "rule_mutation_batch",
            {"count": len(mutations), "timestamp": datetime.utcnow().isoformat()},
        )
    except Exception as e:
        logging.error(f"Failed to log rule mutations: {e}")
        log_learning_event(
            "exception",
            {
                "error": str(e),
                "context": "apply_rule_mutations",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


def test_rule_mutation_engine():
    """
    Basic test for rule mutation logic.
    """
    # Create dummy rules
    dummy_rules = {
        "rule1": {"threshold": 0.5},
        "rule2": {"threshold": 0.8},
        "rule3": {"threshold": 0.2},
    }
    mutations = propose_rule_mutations(dummy_rules, top_n=2)
    assert len(mutations) == 2, "Should mutate top 2 rules"
    for m in mutations:
        assert 0.0 <= m["to"] <= 1.0, "Threshold out of bounds"
    print("Rule mutation engine test passed.")


if __name__ == "__main__":
    # Run main mutation logic or test
    import sys

    if "--test" in sys.argv:
        test_rule_mutation_engine()
    else:
        apply_rule_mutations()
