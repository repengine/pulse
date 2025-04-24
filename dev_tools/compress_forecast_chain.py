# dev_tools/compress_forecast_chain.py

"""
Compress Forecast Mutation Chain CLI

Given a forecast archive + root trace ID, this compresses the mutation chain
into a canonical forecast using alignment, trust, and arc stability.

Author: Pulse AI Engine
"""

import argparse
import json
from forecast_output.mutation_compression_engine import (
    compress_episode_chain, export_compressed_episode
)
from memory.forecast_episode_tracer import build_episode_chain

def load_jsonl(path):
    with open(path, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

def main():
    parser = argparse.ArgumentParser(description="Forecast Mutation Chain Compressor")
    parser.add_argument("--batch", required=True, help="Forecast archive (.jsonl)")
    parser.add_argument("--root", required=True, help="Trace ID to begin compression from")
    parser.add_argument("--export", type=str, required=True, help="Path to save compressed forecast")
    args = parser.parse_args()

    forecasts = load_jsonl(args.batch)
    chain = build_episode_chain(forecasts, args.root)
    compressed = compress_episode_chain(chain)
    export_compressed_episode(compressed, args.export)

if __name__ == "__main__":
    main()
