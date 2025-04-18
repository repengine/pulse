"""
path_registry.py

Centralized file path management for Pulse I/O.
"""

import os

# Base directories
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "pulse", "logs")
FORECAST_HISTORY_DIR = os.path.join(BASE_DIR, "forecast_output", "forecast_history")
DIAGNOSTICS_DIR = os.path.join(BASE_DIR, "diagnostics")
BATCH_DIR = os.path.join(BASE_DIR, "batch")

PATHS = {
    # Worldstate logs
    "WORLDSTATE_LOG_DIR": LOGS_DIR,

    # Forecast history and summaries
    "FORECAST_HISTORY": FORECAST_HISTORY_DIR,
    "BATCH_FORECAST_SUMMARY": os.path.join(BATCH_DIR, "batch_forecast_summary.txt"),

    # Diagnostics logs
    "DIAGNOSTICS_LOG": os.path.join(DIAGNOSTICS_DIR, "diagnostics.log"),

    # CLI doc output
    "CLI_DOC": os.path.join(BASE_DIR, "docs", "cli_reference.md"),

    # Compressed forecast output
    "FORECAST_COMPRESSED": os.path.join(FORECAST_HISTORY_DIR, "compressed_forecasts.json"),

    # Log file
    "LOG_FILE": os.path.join(LOGS_DIR, "pulse.log"),

    # Add other centralized paths as needed
}
