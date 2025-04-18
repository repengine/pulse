""" 
pulse_cli_dashboard.py

Displays all available Pulse CLI shell modes and their descriptions.
Groups modes by type and color codes them.

Author: Pulse v0.10
"""

import json
from utils.log_utils import get_logger

HOOK_CONFIG = "dev_tools/pulse_hooks_config.json"
logger = get_logger(__name__)

def show_cli_dashboard():
    print("🔧 Pulse CLI Dashboard — Available Modes\n")

    with open(HOOK_CONFIG, 'r') as f:
        config = json.load(f)

    grouped = {"suite": [], "batch": [], "test": [], "tool": []}

    for mode, enabled in config["active_hooks"].items():
        if enabled:
            meta = config["metadata"].get(mode, {})
            grouped[meta.get("category", "tool")].append((mode, meta.get("label", "No description")))

    for cat in grouped:
        color = {"suite": "\033[94m", "batch": "\033[92m", "test": "\033[93m", "tool": "\033[90m"}[cat]
        print(f"{color}>> {cat.upper()} MODES:\033[0m")
        for mode, label in grouped[cat]:
            print(f"  --mode {mode:<28} {label}")
        print("")

if __name__ == "__main__":
    show_cli_dashboard()