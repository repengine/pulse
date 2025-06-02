#!/usr/bin/env python3
"""Ingest signal log to per-turn WorldState snapshots."""

import argparse
import os

from engine.worldstate import WorldState
from engine.variable_accessor import set_variable
from engine.utils.worldstate_io import save_worldstate_to_file

from ingestion.iris_plugins import IrisPluginManager

# Import the historical_ingestion_plugin module directly
from ingestion.iris_plugins_variable_ingestion import (
    historical_ingestion_plugin,
    HISTORY_SNAPSHOT_PREFIX,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate historical WorldState snapshots using the historical ingestion plugin.")
    parser.add_argument(
        "--output-dir",
        default="snapshots",  # Default to snapshots directory
        help="Directory to write historical WorldState snapshots.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = args.output_dir

    os.makedirs(output_dir, exist_ok=True)

    # Instantiate and autoload Iris plugins
    plugin_manager = IrisPluginManager()
    plugin_manager.autoload()

    # Find the historical ingestion plugin function
    historical_plugin_fn = None
    for plugin in plugin_manager.plugins:
        # Check if the plugin is the function from our historical ingestion module
        if plugin == historical_ingestion_plugin:
            historical_plugin_fn = plugin
            break

    if historical_plugin_fn is None:
        print(
            "Error: historical_ingestion_plugin function not found in loaded plugins."
        )
        return

    # Run the historical ingestion plugin to get the timeline of signals
    print("Running historical ingestion plugin...")
    historical_signals_timeline = historical_plugin_fn()
    print(f"Received historical data for {len(historical_signals_timeline)} turns.")

    # Create and save WorldState snapshots for each turn in the timeline
    print(f"Generating historical snapshots in {output_dir}...")
    for turn, signals_for_date in enumerate(historical_signals_timeline, 1):
        state = WorldState()
        for sig in signals_for_date:
            # Ensure signal has 'name' and 'value' keys
            if "name" in sig and "value" in sig:
                set_variable(state, sig["name"], sig["value"])
            else:
                print(f"Warning: Skipping invalid signal: {sig}")

        # Save each snapshot with a unique filename per turn
        # Access HISTORY_SNAPSHOT_PREFIX from the imported module
        filename = f"{HISTORY_SNAPSHOT_PREFIX}{turn:04d}.json"
        save_worldstate_to_file(state, output_dir, filename=filename)
        if turn % 100 == 0:
            print(f"Generated {turn} snapshots...")

    print("Historical snapshot generation complete.")


if __name__ == "__main__":
    main()
