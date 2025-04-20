"""
path_registry.py

Centralized file path management for Pulse I/O.

Each key in PATHS describes a logical file or directory used by the system.
Add new paths here to keep all file locations consistent and portable.
"""
import os
from typing import Dict

# Base directories
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "pulse", "logs")  # All log files
FORECAST_HISTORY_DIR = os.path.join(BASE_DIR, "forecast_output", "forecast_history")  # Forecast history
DIAGNOSTICS_DIR = os.path.join(BASE_DIR, "diagnostics")  # Diagnostics output
BATCH_DIR = os.path.join(BASE_DIR, "batch")  # Batch forecast output

PATHS: Dict[str, str] = {
    # Directory for worldstate logs
    "WORLDSTATE_LOG_DIR": LOGS_DIR,

    # Directory for forecast history files
    "FORECAST_HISTORY": FORECAST_HISTORY_DIR,
    # File for batch forecast summary
    "BATCH_FORECAST_SUMMARY": os.path.join(BATCH_DIR, "batch_forecast_summary.txt"),

    # File for diagnostics logs
    "DIAGNOSTICS_LOG": os.path.join(DIAGNOSTICS_DIR, "diagnostics.log"),

    # File for CLI documentation output
    "CLI_DOC": os.path.join(BASE_DIR, "docs", "cli_reference.md"),

    # File for compressed forecast output
    "FORECAST_COMPRESSED": os.path.join(FORECAST_HISTORY_DIR, "compressed_forecasts.json"),

    # Main log file
    "LOG_FILE": os.path.join(LOGS_DIR, "pulse.log"),

    # Add other centralized paths as needed
}

def get_path(key: str) -> str:
    """
    Retrieve a path from the PATHS registry.
    Args:
        key (str): The path key.
    Returns:
        str: The file or directory path.
    Raises:
        KeyError: If the key is not found in PATHS.
    """
    if key not in PATHS:
        raise KeyError(f"Path key '{key}' not found in PATHS registry.")
    return PATHS[key]
