"""
pulse_cli_dashboard.py

Displays all available Pulse CLI shell modes and their descriptions.
Groups modes by type and color codes them.

Author: Pulse v0.10

Usage:
    python dev_tools/pulse_cli_dashboard.py [--type suite|batch|test|tool|all] [--no-color]

- Add --type to filter by mode type (default: all)
- Add --no-color to disable ANSI color output
- Prints a summary of the number of modes per category
- Handles missing or malformed hook config files
"""
import json
import argparse
from utils.log_utils import get_logger
from core.path_registry import PATHS
assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"
from typing import Dict, List

DASHBOARD_CONFIG = PATHS.get("DASHBOARD_CONFIG", "dev_tools/dashboard_config.json")
HOOK_CONFIG = PATHS.get("HOOK_CONFIG", "dev_tools/pulse_hooks_config.json")
logger = get_logger(__name__)

CATEGORY_COLORS = {
    "suite": "\033[94m",
    "batch": "\033[92m",
    "test": "\033[93m",
    "tool": "\033[90m"
}

ALL_CATEGORIES = ["suite", "batch", "test", "tool"]

def show_cli_dashboard(mode_type: str = "all", use_color: bool = True) -> None:
    """
    Display all available Pulse CLI shell modes, grouped and color-coded by type.
    Args:
        mode_type (str): Filter by mode type (suite, batch, test, tool, all)
        use_color (bool): Whether to use ANSI color codes
    """
    print("🔧 Pulse CLI Dashboard — Available Modes\n")
    try:
        with open(HOOK_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"[Dashboard] Failed to load hook config: {e}")
        print("[Dashboard] Error: Could not load CLI hook config.")
        return

    grouped: Dict[str, List] = {cat: [] for cat in ALL_CATEGORIES}
    for mode, enabled in config.get("active_hooks", {}).items():
        if enabled:
            meta = config["metadata"].get(mode, {})
            cat = meta.get("category", "tool")
            grouped[cat].append((mode, meta.get("label", "No description")))

    categories = ALL_CATEGORIES if mode_type == "all" else [mode_type]
    total_modes = 0
    for cat in categories:
        if not grouped[cat]:
            continue
        color = CATEGORY_COLORS[cat] if use_color else ""
        reset = "\033[0m" if use_color else ""
        print(f"{color}>> {cat.upper()} MODES:{reset}")
        for mode, label in grouped[cat]:
            print(f"  --mode {mode:<28} {label}")
            total_modes += 1
        print("")
    print(f"Summary: {total_modes} modes displayed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pulse CLI Dashboard")
    parser.add_argument("--type", type=str, default="all", choices=["suite", "batch", "test", "tool", "all"], help="Filter by mode type")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color output")
    args = parser.parse_args()
    show_cli_dashboard(mode_type=args.type, use_color=not args.no_color)