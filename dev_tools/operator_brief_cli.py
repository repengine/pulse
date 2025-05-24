# tools/operator_brief_cli.py

"""
Pulse Operator Brief CLI

Usage:
    python tools/operator_brief_cli.py \
      --alignment data/alignment_output.jsonl \
      --episodes logs/forecast_episodes.jsonl \
      --export operator_brief.md
"""

import argparse
from operator_interface.operator_brief_generator import generate_operator_brief
from trust_system.license_explainer import explain_forecast_license


def main():
    parser = argparse.ArgumentParser(description="Pulse Operator Brief Generator CLI")
    parser.add_argument(
        "--alignment",
        type=str,
        required=True,
        help="Alignment-scored forecast file (.jsonl)",
    )
    parser.add_argument(
        "--episodes", type=str, required=True, help="Symbolic episode log (.jsonl)"
    )
    parser.add_argument(
        "--export", type=str, default="operator_brief.md", help="Output markdown path"
    )
    parser.add_argument(
        "--topk", type=int, default=5, help="Top-N forecasts to include"
    )
    parser.add_argument(
        "--previous-episodes",
        type=str,
        help="Optional: prior episode log for drift comparison",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Print rationale for each license decision",
    )

    args = parser.parse_args()

    if args.explain:
        import json

        print("🔍 License Rationales:")
        with open(args.alignment, "r", encoding="utf-8") as f:
            forecasts = [json.loads(line) for line in f]
        for fc in forecasts:
            explanation = explain_forecast_license(fc)
            print(f"→ {fc.get('trace_id', 'unknown')} — {explanation}")

    generate_operator_brief(
        alignment_file=args.alignment,
        episode_log_file=args.episodes,
        output_md_path=args.export,
        top_k=args.topk,
        previous_episode_log=args.previous_episodes,
    )


if __name__ == "__main__":
    main()
