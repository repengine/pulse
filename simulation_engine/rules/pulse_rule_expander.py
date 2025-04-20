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
import os
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

REGRET_FILE = "data/regret_chain.jsonl"
FINGERPRINT_FILE = "data/rule_fingerprints.json"
SUGGESTED_FILE = "data/candidate_rules.json"

def load_regrets(path: str = REGRET_FILE) -> List[Dict]:
    regrets = []
    try:
        with open(path, "r") as f:
            for line in f:
                regrets.append(json.loads(line.strip()))
    except:
        pass
    return regrets

def load_rules(path: str = FINGERPRINT_FILE) -> Dict[str, Dict]:
    with open(path, "r") as f:
        return json.load(f)

def extract_unmatched_arcs(regrets: List[Dict], rules: Dict[str, Dict]) -> List[str]:
    covered_arcs = {r.get("arc_label") for r in rules.values() if r.get("arc_label")}
    arc_freq = defaultdict(int)
    for r in regrets:
        arc = r.get("arc_label")
        if arc and arc not in covered_arcs:
            arc_freq[arc] += 1
    return sorted(arc_freq.items(), key=lambda x: -x[1])

def generate_candidate_rules(unmatched_arcs: List[Tuple[str, int]]) -> List[Dict]:
    candidates = []
    for arc, freq in unmatched_arcs:
        candidate = {
            "description": f"Generated rule from frequent regret arc: {arc}",
            "trigger": {"symbolic_trace": f"leading to {arc}"},
            "effect": {"arc_label": arc},
            "trust_weight": 0.5,
            "source": "pulse_rule_expander.py"
        }
        candidates.append(candidate)
    return candidates

def export_candidate_rules(candidates: List[Dict], path: str = SUGGESTED_FILE):
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
        "exported_to": SUGGESTED_FILE
    }

# CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pulse Rule Expander from Regret/Arc Patterns")
    parser.add_argument("--expand", action="store_true", help="Run expansion")
    args = parser.parse_args()

    if args.expand:
        result = expand_rules_from_regret()
        print(json.dumps(result, indent=2))
    else:
        print("Use --expand to generate new rules from regrets")