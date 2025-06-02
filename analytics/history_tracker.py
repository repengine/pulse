# pulse/history_tracker.py
"""
Module: history_tracker.py
Purpose: Log the evolution of each variable across simulation steps.
Supports introspection, graphing, and long-term memory of Pulse foresight activity.

Usage:
    from analytics.history_tracker import track_variable_history
    track_variable_history(run_id, state_snapshots)

Each variable's timeline is saved to a structured JSONL per simulation run.
"""

import os
import json
from typing import List, Dict


def track_variable_history(
    run_id: str, state_snapshots: List[Dict], output_dir: str = "history_logs"
) -> None:
    """
    Saves variable histories from a series of simulation states.

    Parameters:
        run_id (str): Unique ID or label for this simulation batch
        state_snapshots (List[Dict]): List of full worldstates (dict) in temporal order
        output_dir (str): Directory to save the log file (default: "history_logs")

    Output:
        File: history_logs/vars_{run_id}.jsonl
    """
    run_id = os.path.basename(run_id)  # Prevent directory traversal
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"vars_{run_id}.jsonl")

    try:
        with open(path, "w") as f:
            for i, snapshot in enumerate(state_snapshots):
                if not isinstance(snapshot, dict):
                    print(f"⚠️ Warning: Step {i} is not a valid dictionary. Skipping.")
                    continue
                variables = snapshot.get("variables")
                if not isinstance(variables, dict):
                    print(
                        f"⚠️ Warning: 'variables' missing or malformed in step {i}. Skipping."
                    )
                    continue
                try:
                    record = {"step": i, "variables": variables}
                    f.write(json.dumps(record) + "\n")
                except TypeError as te:
                    print(f"⚠️ Serialization error at step {i}: {te}")
        print(f"✅ Variable history saved to {path}")
    except Exception as e:
        print(f"❌ Failed to write variable history log: {e}")
