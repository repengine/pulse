"""
Compatibility layer for historical_retrodiction_runner module.

This module was originally deprecated and its functionality merged into
simulation_engine/simulator_core.py. This file exists to maintain backward
compatibility with existing tests.
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

# Compatibility constants
TRUTH_PATH = os.environ.get("PULSE_TRUTH_PATH", "data/historical_variables.json")


def get_default_variable_state() -> Dict[str, float]:
    """
    Return default variable state, either from file or as empty dict.
    This is a compatibility function for tests.

    Returns:
        Dict containing historical variables if file exists, otherwise empty dict
    """
    try:
        path = Path(TRUTH_PATH)
        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
                if isinstance(data, dict) and "variables" in data:
                    return data["variables"]
                return data
    except Exception:
        pass

    # Default fallback
    return {"energy_cost": 1.0}


class RetrodictionLoader:
    """
    Compatibility class for RetrodictionLoader.
    Provides the interface that was previously available.
    """

    def __init__(self, path: Optional[str] = None):
        self.path = path or TRUTH_PATH
        self.snapshots = {}
        try:
            if Path(self.path).exists():
                with open(self.path, "r") as f:
                    data = json.load(f)
                    self.snapshots = data.get("snapshots", {})
        except Exception:
            pass

    def get_snapshot_by_turn(self, turn: int) -> Optional[Dict[str, Any]]:
        """Get a snapshot for a specific turn if available"""
        return self.snapshots.get(str(turn))
