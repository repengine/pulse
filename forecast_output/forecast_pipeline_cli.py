"""
forecast_pipeline_cli.py

CLI wrapper for forecast_pipeline_runner.
Usage:
    python -m forecast_output.forecast_pipeline_cli --input forecasts.jsonl [--digest] [--memory]

Options:
    --input   Path to input forecasts (.jsonl)
    --digest  Enable digest generation
    --memory  Enable memory storage

Author: Pulse AI Engine
"""

import argparse
import json
import sys
from output.forecast_pipeline_runner import run_forecast_pipeline

def load_jsonl(path):
    with open(path, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

def main():
    parser = argparse.ArgumentParser(description="Pulse Forecast Pipeline CLI")
    parser.add_argument("--input", type=str, required=True, help="Forecast batch (.jsonl)")
    parser.add_argument("--digest", action="store_true", help="Enable digest generation")
    parser.add_argument("--memory", action="store_true", help="Enable memory storage")
    args = parser.parse_args()

    try:
        forecasts = load_jsonl(args.input)
    except Exception as e:
        print(f"❌ Failed to load input: {e}")
        sys.exit(1)

    result = run_forecast_pipeline(
        forecasts,
        enable_digest=args.digest,
        save_to_memory=args.memory
    )
    print("\n📦 Pipeline Result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
