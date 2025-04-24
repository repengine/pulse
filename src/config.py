"""
Consolidated configuration module.
"""

import os
import yaml
from core.path_registry import PATHS

# Default path to simulation config YAML
CONFIG_PATH = os.environ.get(
    "SIMULATION_CONFIG_PATH",
    os.path.normpath(os.path.join(os.path.dirname(__file__), "../config/simulation_config.yaml"))
)

def load_simulation_config(path: str = CONFIG_PATH) -> dict:
    """
    Load simulation configuration overrides from YAML file.
    """
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}

# Load at import
SIMULATION_CONFIG = load_simulation_config()

__all__ = [
    "PATHS",
    "CONFIG_PATH",
    "load_simulation_config",
    "SIMULATION_CONFIG",
]