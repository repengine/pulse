# cli_retrodict_forecasts.py
"""
Command-line tool to apply retrodiction scoring to forecast files.
Usage:
    python cli_retrodict_forecasts.py --forecasts input.jsonl --state state.json --output forecast_output.jsonl
"""

import argparse
import json
from learning.learning import retrospective_analysis_batch

parser = argparse.ArgumentParser(description="Retrodiction audit for forecast batches.")
parser.add_argument("--forecasts", type=str, required=True, help="Path to forecasts (.jsonl)")
parser.add_argument("--state", type=str, required=True, help="Path to current_state JSON")
parser.add_argument("--output", type=str, default="retrodicted_forecasts.jsonl", help="Output file")
parser.add_argument("--threshold", type=float, default=1.5, help="Retrodiction flag threshold")
args = parser.parse_args()

# Load input forecasts
forecasts = []
with open(args.forecasts, "r") as f:
    for line in f:
        try:
            forecasts.append(json.loads(line.strip()))
        except Exception:
            continue

# Load current state
with open(args.state, "r") as f:
    current_state = json.load(f)

# Apply retrodiction
scored = retrospective_analysis_batch(forecasts, current_state, threshold=args.threshold)

# Write to output
with open(args.output, "w") as f:
    for entry in scored:
        f.write(json.dumps(entry) + "\n")

print(f"✅ Retrodiction complete. Output written to {args.output}")
