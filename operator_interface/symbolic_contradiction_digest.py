"""
symbolic_contradiction_digest.py

Renders markdown summaries of symbolic contradiction clusters.
Used in Strategos Digest, foresight trust audits, and symbolic drift visualization.

Author: Pulse v0.40
"""

import os
import json
from typing import List, Dict
from engine.path_registry import PATHS

LEARNING_LOG = PATHS.get("LEARNING_LOG", "logs/pulse_learning_log.jsonl")
DIGEST_OUT = "logs/symbolic_contradiction_digest.md"


def load_symbolic_conflict_events() -> List[Dict]:
    if not os.path.exists(LEARNING_LOG):
        return []
    try:
        with open(LEARNING_LOG, "r", encoding="utf-8") as f:
            return [
                json.loads(line)
                for line in f
                if "symbolic_contradiction_cluster" in line
            ]
    except Exception as e:
        print(f"[SymbolicDigest] Failed to load log: {e}")
        return []


def format_contradiction_cluster_md(clusters: List[Dict]) -> str:
    lines = ["### ♻️ Symbolic Contradiction Digest\n"]
    for c in clusters:
        turn = c.get("data", {}).get("origin_turn", "?")
        lines.append(f"#### 🌀 Origin Turn: {turn}")
        conflicts = c.get("data", {}).get("conflicts", [])
        for a, b, reason in conflicts:
            lines.append(f"- `{a}` vs `{b}` → **{reason}**")
        lines.append("")
    return "\n".join(lines)


def export_contradiction_digest_md(path: str = DIGEST_OUT):
    clusters = load_symbolic_conflict_events()
    md = format_contradiction_cluster_md(clusters)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"✅ Symbolic contradiction digest saved to {path}")
    except Exception as e:
        print(f"❌ Failed to save contradiction digest: {e}")


if __name__ == "__main__":
    export_contradiction_digest_md()
