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

    This is a compatibility function for tests that provides a fallback
    variable state when historical data files are not available.

    Returns:
        Dict[str, float]: Dictionary containing historical variables if file exists,
            otherwise returns a default dict with 'energy_cost': 1.0.

    Example:
        Basic usage:
        >>> state = get_default_variable_state()
        >>> isinstance(state, dict)
        True
        >>> "energy_cost" in state or len(state) > 0
        True

        Verify default fallback:
        >>> state = get_default_variable_state()
        >>> len(state) >= 1  # At least energy_cost should be present
        True
        >>> all(isinstance(v, (int, float)) for v in state.values())
        True
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

    Provides the interface that was previously available for loading historical
    snapshots used in retrodiction simulations. This class maintains backward
    compatibility with existing tests while the main functionality has been
    merged into simulation_engine/simulator_core.py.

    Attributes:
        path (str): Path to the historical variables JSON file.
        snapshots (Dict[str, Any]): Dictionary of loaded snapshots keyed by turn.

    Example:
        Basic initialization:
        >>> loader = RetrodictionLoader()
        >>> isinstance(loader.path, str)
        True
        >>> isinstance(loader.snapshots, dict)
        True

        Custom path initialization:
        >>> custom_loader = RetrodictionLoader("custom/path.json")
        >>> custom_loader.path == "custom/path.json"
        True

        Snapshot retrieval:
        >>> loader = RetrodictionLoader()
        >>> snapshot = loader.get_snapshot_by_turn(0)
        >>> snapshot is None or isinstance(snapshot, dict)
        True
    """

    def __init__(self, path: Optional[str] = None) -> None:
        """
        Initialize the RetrodictionLoader.

        Args:
            path: Optional path to historical variables JSON file. If not provided,
                uses the PULSE_TRUTH_PATH environment variable or default path.

        Example:
            Default path initialization:
            >>> loader = RetrodictionLoader()
            >>> loader.path is not None
            True
            >>> isinstance(loader.snapshots, dict)
            True

            Custom path initialization:
            >>> loader = RetrodictionLoader("custom/path.json")
            >>> loader.path == "custom/path.json"
            True
            >>> isinstance(loader.snapshots, dict)
            True

            Environment variable path:
            >>> import os
            >>> original_path = os.environ.get("PULSE_TRUTH_PATH")
            >>> os.environ["PULSE_TRUTH_PATH"] = "test/path.json"
            >>> loader = RetrodictionLoader()
            >>> loader.path == "test/path.json"
            True
            >>> if original_path:
            ...     os.environ["PULSE_TRUTH_PATH"] = original_path
            ... else:
            ...     _ = os.environ.pop("PULSE_TRUTH_PATH", None)
        """
        self.path = path or os.environ.get(
            "PULSE_TRUTH_PATH", "data/historical_variables.json"
        )
        self.snapshots = {}
        try:
            if Path(self.path).exists():
                with open(self.path, "r") as f:
                    data = json.load(f)
                    self.snapshots = data.get("snapshots", {})
        except Exception:
            pass

    def get_snapshot_by_turn(self, turn: int) -> Optional[Dict[str, Any]]:
        """
        Get a snapshot for a specific turn if available.

        Args:
            turn: The turn number to retrieve snapshot for.

        Returns:
            Optional[Dict[str, Any]]: Snapshot data for the specified turn,
                or None if no snapshot exists for that turn.

        Example:
            Basic snapshot retrieval:
            >>> loader = RetrodictionLoader()
            >>> snapshot = loader.get_snapshot_by_turn(1)
            >>> snapshot is None or isinstance(snapshot, dict)
            True

            Multiple turn queries:
            >>> loader = RetrodictionLoader()
            >>> for turn in [0, 1, 5, 10]:
            ...     snapshot = loader.get_snapshot_by_turn(turn)
            ...     assert snapshot is None or isinstance(snapshot, dict)

            Non-existent turn handling:
            >>> loader = RetrodictionLoader()
            >>> snapshot = loader.get_snapshot_by_turn(999)
            >>> snapshot is None
            True
        """
        return self.snapshots.get(str(turn))
