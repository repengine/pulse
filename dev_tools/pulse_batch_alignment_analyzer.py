# dev_tools/pulse_batch_alignment_analyzer.py

"""
Pulse Batch Alignment Analyzer

Scores a forecast batch using alignment index (FAI) and outputs:
- Top-N forecasts
- Ranked alignment scores
- Optional CSV and plot exports

Author: Pulse AI Engine
Version: v1.0.0
"""

import argparse
import json
import csv
import matplotlib.pyplot as plt
from trust_system.alignment_index import compute_alignment_index


def load_forecasts(path):
    with open(path, "r") as f:
        return [json.loads(line) for line in f if line.strip()]


def save_as_jsonl(forecasts, path):
    with open(path, "w") as f:
        for fc in forecasts:
            f.write(json.dumps(fc) + "\n")


def save_as_csv(forecasts, path):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["trace_id", "alignment_score"])
        for fc in forecasts:
            writer.writerow([fc.get("trace_id", "unknown"), fc.get("alignment_score", 0)])


def plot_alignment_scores(forecasts, path):
    ids = [fc.get("trace_id", f"fc{i}") for i, fc in enumerate(forecasts)]
    scores = [fc.get("alignment_score", 0) for fc in forecasts]
    plt.figure(figsize=(10, 4))
    plt.bar(ids, scores, color="mediumseagreen", edgecolor="black")
    plt.title("Forecast Alignment Index (FAI)")
    plt.ylabel("Score (0–100)")
    plt.xlabel("Forecast ID")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(path)
    print(f"📊 Alignment plot saved to {path}")


def main():
    parser = argparse.ArgumentParser(description="Pulse Batch Alignment Analyzer")
    parser.add_argument("--batch", type=str, required=True, help="Forecast batch (.jsonl)")
    parser.add_argument("--output", type=str, help="Save output JSONL with alignment scores")
    parser.add_argument("--topk", type=int, default=10, help="Print top-K by alignment")
    parser.add_argument("--export-csv", type=str, help="Optional: export scores to CSV")
    parser.add_argument("--plot", type=str, help="Optional: path to save bar chart of scores")
    args = parser.parse_args()

    batch = load_forecasts(args.batch)
    scored = []

    for fc in batch:
        alignment = compute_alignment_index(fc)
        fc["alignment_score"] = alignment["alignment_score"]
        fc["alignment_components"] = alignment["components"]
        scored.append(fc)

    ranked = sorted(scored, key=lambda x: x["alignment_score"], reverse=True)

    if args.output:
        save_as_jsonl(ranked, args.output)
        print(f"✅ Output saved to {args.output}")

    if args.export_csv:
        save_as_csv(ranked, args.export_csv)
        print(f"📤 CSV exported to {args.export_csv}")

    if args.plot:
        plot_alignment_scores(ranked, args.plot)

    print(f"\n🏆 Top {args.topk} forecasts by alignment:")
    for fc in ranked[:args.topk]:
        print(f"{fc.get('trace_id', 'unknown')}: {fc['alignment_score']}")

if __name__ == "__main__":
    main()
