"""
rule_cluster_digest_formatter.py

Renders markdown summaries of rule clusters by volatility.
Used in Strategos Digest, operator learning logs, and trust audits.

Author: Pulse v0.39
"""

import os
from analytics.rule_cluster_engine import summarize_rule_clusters


def highlight_volatility(score: float) -> str:
    if score > 0.7:
        return "🔴"
    elif score > 0.4:
        return "🟡"
    else:
        return "🟢"


def format_cluster_digest_md(limit: int = 10) -> str:
    clusters = summarize_rule_clusters()
    lines = ["### 🧠 Rule Cluster Digest", ""]
    for c in clusters[:limit]:
        tag = highlight_volatility(c["volatility_score"])
        lines.append(f"#### {tag} `{c['cluster']}`  (size: {c['size']})")
        lines.append(f"- Volatility Score: **{c['volatility_score']:.3f}**")
        lines.append("- Rules:")
        for rule_id in c["rules"]:
            lines.append(f"  - `{rule_id}`")
        lines.append("")
    return "\n".join(lines)


def export_cluster_digest_md(path: str = "logs/rule_cluster_digest.md"):
    md = format_cluster_digest_md()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"✅ Markdown digest saved to {path}")
    except Exception as e:
        print(f"❌ Failed to save digest: {e}")


if __name__ == "__main__":
    print(format_cluster_digest_md())
