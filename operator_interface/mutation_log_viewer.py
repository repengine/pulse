"""
mutation_log_viewer.py

Displays a readable summary of recent variable, overlay, and rule mutations.
Used for CLI diagnostics, strategos digest rendering, and trust evolution audit.

Author: Pulse v0.36
"""

import os
import json
from typing import List, Dict
from engine.path_registry import PATHS

LEARNING_LOG = PATHS.get("LEARNING_LOG", "logs/pulse_learning_log.jsonl")
RULE_LOG = PATHS.get("RULE_MUTATION_LOG", "logs/rule_mutation_log.jsonl")


def load_log(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]
    except Exception as e:
        print(f"[LogViewer] Failed to load {path}: {e}")
        return []


def render_learning_summary(events: List[Dict]):
    print("\n📜 Pulse Learning Event Summary:")
    for e in events[-30:]:
        t = e.get("timestamp", "?")
        typ = e.get("event_type", "?")
        dat = e.get("data", {})
        print(f"[{t}] {typ}")

        if typ == "volatile_cluster_mutation":
            print(
                f" 🔁 Cluster: {dat.get('cluster')} | Volatility: {dat.get('volatility_score')}"
            )
            for v in dat.get("mutated_variables", []):
                print(f"   - {v['name']} → trust_weight: {v['new_weight']}")
        else:
            for k, v in dat.items():
                print(f"   - {k}: {v}")
        print("---")


def render_rule_mutation_summary(log: List[Dict]):
    print("\n🔧 Rule Mutation Summary:")
    for entry in log[-10:]:
        mut = entry.get("mutation")
        if not mut:
            continue
        print(f" - Rule `{mut['rule']}`: {mut['from']} → {mut['to']}")


if __name__ == "__main__":
    learning_events = load_log(str(LEARNING_LOG))
    render_learning_summary(learning_events)

    rule_mutations = load_log(str(RULE_LOG))
    render_rule_mutation_summary(rule_mutations)
