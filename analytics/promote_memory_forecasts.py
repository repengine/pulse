"""
Pulse Forecast Memory Promoter (CLI)

Usage:
    python tools/promote_memory_forecasts.py --batch forecasts.jsonl
"""

import argparse
import json
from analytics.forecast_memory_promoter import (
    select_promotable_forecasts,
    export_promoted,
)


def load_jsonl(path):
    with open(path, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]


parser = argparse.ArgumentParser()
parser.add_argument("--batch", required=True)
parser.add_argument("--export", default="memory/core_forecast_memory.jsonl")
args = parser.parse_args()

batch = load_jsonl(args.batch)
selected = select_promotable_forecasts(batch)
export_promoted(selected, args.export)
