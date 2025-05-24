# tools/certify_forecast_batch.py

"""
Certify Forecast Batch CLI

Marks which forecasts pass Pulse certification standards.
Exports certified set and optional summary report.

Author: Pulse AI Engine
"""

import argparse
import json
from forecast_output.forecast_fidelity_certifier import (
    tag_certified_forecasts,
    generate_certified_digest,
)


def load_jsonl(path):
    with open(path, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]


def save_jsonl(batch, path):
    with open(path, "w") as f:
        for fc in batch:
            f.write(json.dumps(fc) + "\n")


parser = argparse.ArgumentParser()
parser.add_argument("--batch", required=True)
parser.add_argument("--export", default="certified_forecasts.jsonl")
parser.add_argument("--summary", action="store_true")
args = parser.parse_args()

forecasts = load_jsonl(args.batch)
tagged = tag_certified_forecasts(forecasts)
save_jsonl(tagged, args.export)

if args.summary:
    report = generate_certified_digest(tagged)
    print(f"\n📜 Certification Summary:\n{json.dumps(report, indent=2)}")
