#!/usr/bin/env python3
"""Ingest signal log to per-turn WorldState snapshots."""
import argparse
import json
import os

from simulation_engine.worldstate import WorldState
from core.variable_accessor import set_variable
from simulation_engine.utils.worldstate_io import save_worldstate_to_file

def parse_args():
    parser = argparse.ArgumentParser(
        description="Ingest signal log to per-turn WorldState snapshots."
    )
    parser.add_argument(
        "--signal-log",
        required=True,
        help="Path to the JSONL file produced by IngestionService.export_signal_log()."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write per-turn WorldState snapshots."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    signal_log = args.signal_log
    output_dir = args.output_dir

    os.makedirs(output_dir, exist_ok=True)

    with open(signal_log, "r") as f:
        for turn, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            signals = json.loads(line)
            # Support both a list of signals or a single signal dict per line
            if isinstance(signals, dict):
                signals = [signals]
            state = WorldState()
            for sig in signals:
                set_variable(state, sig["name"], sig["value"])
            # Save each snapshot with a unique filename per turn
            filename = f"turn_{turn:04d}.json"
            save_worldstate_to_file(state, output_dir, filename=filename)

if __name__ == "__main__":
    main()