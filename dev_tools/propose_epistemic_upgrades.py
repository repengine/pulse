"""
Propose Epistemic Upgrades from Foreign Causal Archive and Divergence Logs

Reads the foreign causal archive and divergence logs, then proposes symbolic upgrades (new rules/arcs/tags) for curriculum learning and operator review.

Usage:
  python dev_tools/propose_epistemic_upgrades.py --output plans/epistemic_upgrade_plan.json
"""

import argparse
import json
from collections import Counter
import os

FOREIGN_ARCHIVE = "GPT/foreign_causal_archive.jsonl"
DIVERGENCE_LOG = "GPT/gpt_forecast_divergence_log.jsonl"


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def propose_upgrades():
    # Aggregate foreign fingerprints
    fingerprints = load_jsonl(FOREIGN_ARCHIVE)
    var_counts = Counter(fp.get("variable", "unknown") for fp in fingerprints)
    cons_counts = Counter(fp.get("consequence", "unknown") for fp in fingerprints)
    # Aggregate divergence types
    divergences = load_jsonl(DIVERGENCE_LOG)
    div_counts = Counter(d.get("divergence_type", "unknown") for d in divergences)
    # Propose upgrades: most frequent foreign variables/consequences, and most
    # common divergence types
    upgrades = {
        "proposed_variables": [
            v for v, c in var_counts.most_common(10) if v != "unknown"
        ],
        "proposed_consequences": [
            c for c, n in cons_counts.most_common(10) if c != "unknown"
        ],
        "divergence_types": dict(div_counts.most_common()),
        "notes": "Review these for possible rule mutation, symbolic overlay, or curriculum learning.",
    }
    return upgrades


def main():
    parser = argparse.ArgumentParser(description="Propose Epistemic Upgrades from logs")
    parser.add_argument(
        "--output", type=str, required=True, help="Path to save upgrade plan JSON"
    )
    args = parser.parse_args()
    upgrades = propose_upgrades()
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(upgrades, f, indent=2)
    print(f"✅ Epistemic upgrade plan written to {args.output}")


if __name__ == "__main__":
    main()
