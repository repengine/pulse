"""
path_registry.py

Centralized file path management for Pulse I/O.

Each key in PATHS describes a logical file or directory used by the system.
Add new paths here to keep all file locations consistent and portable.
Uses pathlib for robust, platform-independent path management.
"""

from pathlib import Path
from typing import Dict

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "pulse" / "logs"  # All log files
FORECAST_HISTORY_DIR = (
    BASE_DIR / "forecast_output" / "forecast_history"
)  # Forecast history
DIAGNOSTICS_DIR = BASE_DIR / "diagnostics"  # Diagnostics output
BATCH_DIR = BASE_DIR / "batch"  # Batch forecast output

PATHS: Dict[str, Path] = {
    # Directory for worldstate logs
    "WORLDSTATE_LOG_DIR": LOGS_DIR,
    # Directory for forecast history files
    "FORECAST_HISTORY": FORECAST_HISTORY_DIR,
    # File for batch forecast summary
    "BATCH_FORECAST_SUMMARY": BATCH_DIR / "batch_forecast_summary.txt",
    # File for diagnostics logs
    "DIAGNOSTICS_LOG": DIAGNOSTICS_DIR / "diagnostics.log",
    # File for CLI documentation output
    "CLI_DOC": BASE_DIR / "docs" / "cli_reference.md",
    # File for compressed forecast output
    "FORECAST_COMPRESSED": FORECAST_HISTORY_DIR / "compressed_forecasts.json",
    # Main log file
    "LOG_FILE": LOGS_DIR / "pulse.log",
    # Rules log file
    "RULES_LOG_PATH": LOGS_DIR / "rules.log",
    # Add other centralized paths as needed
    "MODEL_REGISTRY": BASE_DIR / "models" / "model_registry.json",
}


def get_path(key: str) -> Path:
    """
    Retrieve a path from the PATHS registry.
    Args:
        key (str): The path key.
    Returns:
        Path: The file or directory path.
    Raises:
        KeyError: If the key is not found in PATHS.
    """
    if key not in PATHS:
        raise KeyError(f"Path key '{key}' not found in PATHS registry.")
    return PATHS[key]
