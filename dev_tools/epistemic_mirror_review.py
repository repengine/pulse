"""
Epistemic Mirror Review Utility

Summarizes foreign causal fingerprints and divergence logs for operator review and curriculum learning.

Usage:
  python dev_tools/epistemic_mirror_review.py --summarize-foreign-fingerprints
  python dev_tools/epistemic_mirror_review.py --summarize-divergence-log
  python dev_tools/epistemic_mirror_review.py --export-md <output.md>
"""
import argparse
import json
from collections import Counter, defaultdict

FOREIGN_ARCHIVE = "GPT/foreign_causal_archive.jsonl"
DIVERGENCE_LOG = "GPT/gpt_forecast_divergence_log.jsonl"

def summarize_foreign_fingerprints(path=FOREIGN_ARCHIVE):
    counts = Counter()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                fp = json.loads(line)
                key = fp.get("variable", "unknown") + ": " + fp.get("consequence", "unknown")
                counts[key] += 1
    except FileNotFoundError:
        print(f"No foreign archive found at {path}")
        return
    print("\nForeign Causal Fingerprints (unmatched):")
    for k, v in counts.most_common():
        print(f"- {k}: {v}")

def summarize_divergence_log(path=DIVERGENCE_LOG):
    counts = Counter()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                tag = entry.get("divergence_type", "unknown")
                counts[tag] += 1
    except FileNotFoundError:
        print(f"No divergence log found at {path}")
        return
    print("\nDivergence Log Summary:")
    for k, v in counts.most_common():
        print(f"- {k}: {v}")

def export_md_summary(output_md):
    lines = ["# Epistemic Mirror Review\n"]
    # Foreign fingerprints
    lines.append("## Foreign Causal Fingerprints\n")
    try:
        with open(FOREIGN_ARCHIVE, "r", encoding="utf-8") as f:
            fps = [json.loads(line) for line in f]
        by_var = defaultdict(list)
        for fp in fps:
            key = fp.get("variable", "unknown")
            by_var[key].append(fp.get("consequence", "unknown"))
        for var, cons in by_var.items():
            lines.append(f"- **{var}**: {', '.join(set(cons))}")
    except FileNotFoundError:
        lines.append("_No foreign archive found._\n")
    # Divergence log
    lines.append("\n## Divergence Log Summary\n")
    try:
        with open(DIVERGENCE_LOG, "r", encoding="utf-8") as f:
            entries = [json.loads(line) for line in f]
        tags = Counter(e.get("divergence_type", "unknown") for e in entries)
        for tag, count in tags.most_common():
            lines.append(f"- {tag}: {count}")
    except FileNotFoundError:
        lines.append("_No divergence log found._\n")
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ Exported epistemic mirror summary to {output_md}")

def main():
    parser = argparse.ArgumentParser(description="Epistemic Mirror Review Utility")
    parser.add_argument("--summarize-foreign-fingerprints", action="store_true")
    parser.add_argument("--summarize-divergence-log", action="store_true")
    parser.add_argument("--export-md", type=str, help="Export summary as markdown")
    args = parser.parse_args()
    if args.summarize_foreign_fingerprints:
        summarize_foreign_fingerprints()
    if args.summarize_divergence_log:
        summarize_divergence_log()
    if args.export_md:
        export_md_summary(args.export_md)

if __name__ == "__main__":
    main()
