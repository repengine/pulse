"""
rule_mutation_engine.py

Proposes and applies mutations to causal rule weights, thresholds, or structures
based on retrodiction error, symbolic misalignment, or trust regret.

Author: Pulse v0.36
"""

import random
import json
import logging
import os
from typing import Dict, List, Any

from core.path_registry import PATHS
from simulation_engine.rule_cluster_engine import score_rule_volatility

RULE_REGISTRY_PATH = PATHS.get("RULE_REGISTRY", "configs/rule_registry.json")
RULE_MUTATION_LOG = PATHS.get("RULE_MUTATION_LOG", "logs/rule_mutation_log.jsonl")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def load_rules() -> Dict[str, Dict[str, Any]]:
    """
    Loads the rule registry from disk.
    Returns an empty dict if loading fails.
    """
    try:
        with open(RULE_REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                logging.error("Rule registry is not a dict.")
                return {}
            return data
    except Exception as e:
        logging.error(f"Failed to load rules: {e}")
        return {}

def save_rules(rules: Dict[str, Dict[str, Any]]) -> None:
    """
    Saves the rule registry to disk atomically.
    """
    tmp_path = RULE_REGISTRY_PATH + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(rules, f, indent=2)
        os.replace(tmp_path, RULE_REGISTRY_PATH)
    except Exception as e:
        logging.error(f"Failed to save rules: {e}")

def propose_rule_mutations(rules: Dict[str, Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Proposes mutations to the top-N rules.
    Mutates the 'threshold' field within [0, 1] bounds.
    Favors rules from high-volatility clusters.
    """
    if not rules:
        logging.warning("No rules to mutate.")
        return []
    volatility = score_rule_volatility(rules)
    sorted_rules = sorted(rules.items(), key=lambda x: volatility.get(x[0], 0), reverse=True)
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
    return mutations

def apply_rule_mutations() -> None:
    """
    Loads rules, applies mutations, saves, and logs the changes.
    """
    rules = load_rules()
    if not rules:
        print("[RuleMutation] No rules loaded.")
        return

    mutations = propose_rule_mutations(rules)
    if not mutations:
        print("[RuleMutation] No mutations proposed.")
        return

    save_rules(rules)

    try:
        with open(RULE_MUTATION_LOG, "a", encoding="utf-8") as f:
            for m in mutations:
                f.write(json.dumps({"mutation": m}) + "\n")
        print(f"✅ Applied {len(mutations)} rule mutations.")
    except Exception as e:
        logging.error(f"Failed to log rule mutations: {e}")

def test_rule_mutation_engine():
    """
    Basic test for rule mutation logic.
    """
    # Create dummy rules
    dummy_rules = {
        "rule1": {"threshold": 0.5},
        "rule2": {"threshold": 0.8},
        "rule3": {"threshold": 0.2}
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
