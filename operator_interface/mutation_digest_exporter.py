"""
mutation_digest_exporter.py

Exports a unified markdown digest of:
- Rule cluster volatility
- Variable cluster instability
- Learning/mutation events

Used for Strategos Digest, weekly foresight reports, and trust evolution audits.

Author: Pulse v0.39
"""

import os
from datetime import datetime, timezone
from operator_interface.rule_cluster_digest_formatter import format_cluster_digest_md
from operator_interface.variable_cluster_digest_formatter import (
    format_variable_cluster_digest_md,
)
from operator_interface.mutation_log_viewer import load_log
from engine.path_registry import PATHS

LEARNING_LOG = PATHS.get("LEARNING_LOG", "logs/pulse_learning_log.jsonl")
DIGEST_OUT = "logs/full_mutation_digest.md"


def render_learning_summary_md(limit: int = 15) -> str:
    entries = load_log(str(LEARNING_LOG))[-limit:]
    lines = ["### 🔧 Recent Learning Events\n"]
    for e in entries:
        lines.append(f"- `{e.get('timestamp', '?')}` **{e.get('event_type')}**")
        for k, v in e.get("data", {}).items():
            lines.append(f"    - {k}: {v}")
        lines.append("")
    return "\n".join(lines)


def export_full_digest():
    digest = [
        "# 🧠 Pulse Mutation Digest",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()} UTC\n",
        format_cluster_digest_md(limit=5),
        format_variable_cluster_digest_md(limit=5),
        render_learning_summary_md(limit=15),
        "---",
        "Pulse v0.39 | Strategos Audit Layer",
    ]
    try:
        os.makedirs(os.path.dirname(DIGEST_OUT), exist_ok=True)
        with open(DIGEST_OUT, "w", encoding="utf-8") as f:
            f.write("\n\n".join(digest))
        print(f"✅ Digest saved to {DIGEST_OUT}")
    except Exception as e:
        print(f"❌ Failed to export digest: {e}")


if __name__ == "__main__":
    export_full_digest()
