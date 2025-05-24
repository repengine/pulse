"""
variable_cluster_digest_formatter.py

Renders markdown summaries of variable clusters by volatility and symbolic class.
Used for strategos digest, trust audits, and overlay-pressure mutation summaries.

Author: Pulse v0.39
"""

import os
from memory.variable_cluster_engine import summarize_clusters


def highlight_volatility(score: float) -> str:
    if score > 0.7:
        return "🔴"
    elif score > 0.4:
        return "🟡"
    return "🟢"


def format_variable_cluster_digest_md(limit: int = 10) -> str:
    clusters = summarize_clusters()
    lines = ["### 🧠 Variable Cluster Digest", ""]
    for c in clusters[:limit]:
        emoji = highlight_volatility(c["volatility_score"])
        lines.append(f"#### {emoji} `{c['cluster']}`  (size: {c['size']})")
        lines.append(f"- Volatility Score: **{c['volatility_score']:.3f}**")
        lines.append("- Variables:")
        for v in c["variables"]:
            lines.append(f"  - `{v}`")
        lines.append("")
    return "\n".join(lines)


def export_variable_cluster_digest_md(path: str = "logs/variable_cluster_digest.md"):
    md = format_variable_cluster_digest_md()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"✅ Markdown digest saved to {path}")
    except Exception as e:
        print(f"❌ Failed to save digest: {e}")


if __name__ == "__main__":
    print(format_variable_cluster_digest_md())
