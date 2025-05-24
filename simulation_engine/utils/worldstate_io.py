"""
worldstate_io.py

Handles saving and loading of WorldState objects to and from disk.
Used for simulation logging, replay, and audit trail generation.

Author: Pulse v3.5
"""

import os
import json
from datetime import datetime
from typing import Optional
from simulation_engine.worldstate import WorldState


def save_worldstate_to_file(
    state: WorldState, directory: str, filename: Optional[str] = None
) -> str:
    """
    Save a WorldState object to a JSON file.

    Args:
        state (WorldState): The simulation state to save.
        directory (str): Path to save the file.
        filename (Optional[str]): Optional filename. If None, auto-generates based on turn and timestamp.

    Returns:
        str: Full path to the saved file.
    """
    os.makedirs(directory, exist_ok=True)

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"turn_{state.turn}_{timestamp}.json"

    full_path = os.path.join(directory, filename)
    try:
        with open(full_path, "w") as f:
            json.dump(state.to_dict(), f, indent=2)
    except Exception as e:
        raise IOError(f"Failed to save WorldState: {e}")

    return full_path


def load_worldstate_from_file(filepath: str) -> WorldState:
    """
    Load a WorldState object from a JSON file.

    Args:
        filepath (str): Full path to JSON file.

    Returns:
        WorldState: The deserialized world state.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"WorldState file not found: {filepath}")

    with open(filepath, "r") as f:
        data = json.load(f)

    try:
        state = WorldState.from_dict(data)
    except Exception as e:
        raise ValueError(f"Failed to parse WorldState from file: {e}")

    return state
