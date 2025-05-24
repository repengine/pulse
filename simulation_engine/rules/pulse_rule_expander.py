"""
Module: pulse_rule_expander.py
Pulse Version: v0.101.0
Location: simulation_engine/rules/

Purpose:
Generate candidate new rules by analyzing regret chains, forecast arc shifts, and symbolic deltas not covered by known rule fingerprints.

Features:
- Suggest rules from common regret arcs
- Detect frequent symbolic shifts not caused by any rule
- Generate candidate rule block (trigger, effect, metadata)
- CLI-supported with export to .json

Author: Pulse AI Engine
"""

import json
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
from simulation_engine.rules.rule_matching_utils import get_all_rule_fingerprints
from simulation_engine.rules.rule_registry import RuleRegistry

REGRET_FILE = "data/regret_chain.jsonl"
FINGERPRINT_FILE = "data/rule_fingerprints.json"
SUGGESTED_FILE = "data/candidate_rules.json"

# Use RuleRegistry for all rule access
_registry = RuleRegistry()
_registry.load_all_rules()


def load_regrets(path: str = REGRET_FILE) -> List[Dict]:
    """
    Load regrets from a JSONL file.
    """
    try:
        with open(path, "r") as f:
            regrets = [json.loads(line.strip()) for line in f]
    except Exception:
        regrets = []
    return regrets


def load_rules(path: Optional[str] = None) -> Dict[str, Dict]:
    """
    Return a dict of all rule fingerprints keyed by rule_id.
    """
    return {
        r.get("rule_id", r.get("id", str(i))): r
        for i, r in enumerate(get_all_rule_fingerprints())
    }


def extract_unmatched_arcs(
    regrets: List[Dict], rules: Dict[str, Dict]
) -> List[Tuple[str, int]]:
    """
    Find arcs in regrets not covered by any rule.
    """
    covered_arcs = {r.get("arc_label") for r in rules.values() if r.get("arc_label")}
    arc_freq = defaultdict(int)
    for r in regrets:
        arc = r.get("arc_label")
        if arc and arc not in covered_arcs:
            arc_freq[arc] += 1
    return sorted(arc_freq.items(), key=lambda x: -x[1])


def generate_candidate_rules(unmatched_arcs: List[Tuple[str, int]]) -> List[Dict]:
    """
    Generate candidate rules from unmatched arcs.
    """
    candidates = []
    for arc, _ in unmatched_arcs:
        candidate = {
            "description": f"Generated rule from frequent regret arc: {arc}",
            "trigger": {"symbolic_trace": f"leading to {arc}"},
            "effect": {"arc_label": arc},
            "metadata": {"generated": True},
        }
        candidates.append(candidate)
    return candidates


def export_candidate_rules(candidates: List[Dict], path: str = SUGGESTED_FILE) -> None:
    """
    Export candidate rules to a JSON file.
    """
    with open(path, "w") as f:
        json.dump(candidates, f, indent=2)


def expand_rules_from_regret() -> Dict:
    regrets = load_regrets()
    rules = load_rules()
    unmatched = extract_unmatched_arcs(regrets, rules)
    candidates = generate_candidate_rules(unmatched)
    export_candidate_rules(candidates)
    return {
        "unmatched_arcs": unmatched,
        "suggested_count": len(candidates),
        "exported_to": SUGGESTED_FILE,
    }


# CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Pulse Rule Expander from Regret/Arc Patterns"
    )
    parser.add_argument("--expand", action="store_true", help="Run expansion")
    args = parser.parse_args()

    if args.expand:
        result = expand_rules_from_regret()
        print(json.dumps(result, indent=2))
    else:
        print("Use --expand to generate new rules from regrets")
