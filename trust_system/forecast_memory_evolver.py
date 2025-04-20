"""
Module: forecast_memory_evolver.py
Pulse Version: v0.100.5
Location: trust_system/

Purpose:
Analyzes past regrets and forecast memory to evolve Pulse's trust system and symbolic weightings.

Features:
- Aggregates repeated regret patterns (symbolic arc, rule ID, variable)
- Adjusts trust weights or flags rule fingerprints for downgrade
- Identifies repeat offending forecast traces or rule tags
- Operator summary of changes made or pending

Author: Pulse AI Engine
"""

import json
import os
from typing import List, Dict, Tuple

REGRET_LOG = "data/regret_chain.jsonl"
FINGERPRINT_FILE = "data/rule_fingerprints.json"

def load_regrets(path: str = REGRET_LOG) -> List[Dict]:
    """Load regret events from JSONL file."""
    regrets = []
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                try:
                    regrets.append(json.loads(line.strip()))
                except:
                    continue
    return regrets

def count_regret_patterns(regrets: List[Dict]) -> Dict:
    """Aggregate common regret patterns."""
    arc_count = {}
    rule_count = {}
    for r in regrets:
        arc = r.get("arc_label", "Unknown")
        rule = r.get("rule_id", "Unknown")
        arc_count[arc] = arc_count.get(arc, 0) + 1
        rule_count[rule] = rule_count.get(rule, 0) + 1
    return {
        "arc_patterns": arc_count,
        "rule_patterns": rule_count
    }

def adjust_rule_trust_weights(rule_stats: Dict, threshold: int = 2) -> Dict:
    """
    Lower trust in rules that appear in regrets more than threshold times.
    Returns: list of rule_ids adjusted or flagged.
    """
    if not os.path.exists(FINGERPRINT_FILE):
        return {}
    with open(FINGERPRINT_FILE, "r") as f:
        rules = json.load(f)

    adjusted = {}
    for rule_id, count in rule_stats.items():
        if rule_id not in rules or rule_id == "Unknown":
            continue
        trust = rules[rule_id].get("trust_weight", 1.0)
        if count >= threshold:
            new_trust = max(0.1, round(trust - 0.1, 2))
            rules[rule_id]["trust_weight"] = new_trust
            adjusted[rule_id] = new_trust

    # Save back
    with open(FINGERPRINT_FILE, "w") as f:
        json.dump(rules, f, indent=2)
    return adjusted

def flag_repeat_forecasts(regrets: List[Dict], min_count: int = 2) -> List[str]:
    """Identify forecast trace_ids that appear repeatedly in regrets."""
    seen = {}
    for r in regrets:
        tid = r.get("trace_id")
        if tid:
            seen[tid] = seen.get(tid, 0) + 1
    return [tid for tid, count in seen.items() if count >= min_count]

def evolve_memory_from_regrets(regret_path: str = REGRET_LOG, rule_file: str = FINGERPRINT_FILE) -> Dict:
    """Full trust evolution pass."""
    regrets = load_regrets(regret_path)
    stats = count_regret_patterns(regrets)
    rule_adjusts = adjust_rule_trust_weights(stats["rule_patterns"])
    repeat_forecasts = flag_repeat_forecasts(regrets)

    return {
        "total_regrets": len(regrets),
        "repeat_forecasts": repeat_forecasts,
        "adjusted_rules": rule_adjusts,
        "symbolic_arc_summary": stats["arc_patterns"]
    }

# CLI entry
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pulse Forecast Memory Evolver")
    parser.add_argument("--summary", action="store_true", help="Print regret pattern summary")
    parser.add_argument("--evolve", action="store_true", help="Run full evolution pass from regrets")

    args = parser.parse_args()
    if args.evolve:
        result = evolve_memory_from_regrets()
        print("✅ Memory evolution complete.")
        print(json.dumps(result, indent=2))
    elif args.summary:
        r = load_regrets()
        s = count_regret_patterns(r)
        print(json.dumps(s, indent=2))
    else:
        print("Use --summary or --evolve")