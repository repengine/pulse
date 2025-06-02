"""
pulse_cli_docgen.py

Generates CLI documentation markdown for Pulse hooks based on pulse_hooks_config.json.

Author: Pulse v0.10

Usage:
    python dev_tools/pulse_cli_docgen.py [--outfile <file>] [--type suite|batch|test|tool|all]

- Add --outfile to specify output file (default: PATHS["CLI_DOC"])
- Add --type to filter by mode type (default: all)
- Prints a summary of the number of hooks per category
- Handles missing or malformed config files
"""

import json
import argparse
from typing import Dict, List
from utils.log_utils import get_logger
from engine.path_registry import PATHS

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

CONFIG = "dev_tools/pulse_hooks_config.json"
DEFAULT_OUTFILE = str(PATHS["CLI_DOC"])

logger = get_logger(__name__)

ALL_CATEGORIES = ["suite", "batch", "test", "tool"]


def generate_cli_doc(outfile: str = DEFAULT_OUTFILE, mode_type: str = "all") -> None:
    """
    Generate CLI documentation markdown for Pulse hooks.
    Args:
        outfile (str): Output markdown file path.
        mode_type (str): Filter by mode type (suite, batch, test, tool, all)
    """
    try:
        with open(CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"[DocGen] Failed to load hook config: {e}")
        print("[DocGen] Error: Could not load CLI hook config.")
        return

    lines = [
        "# 🧭 Pulse CLI Reference",
        "",
        "Below are all available auto-hooked CLI tools, grouped by category.",
        "",
    ]

    categories: Dict[str, List] = {cat: [] for cat in ALL_CATEGORIES}
    for hook, enabled in config.get("active_hooks", {}).items():
        if enabled:
            meta = config["metadata"].get(hook, {})
            label = meta.get("label", "No description")
            cat = meta.get("category", "tool")
            categories[cat].append((hook, label))

    selected_cats = ALL_CATEGORIES if mode_type == "all" else [mode_type]
    total_hooks = 0
    for cat in selected_cats:
        if not categories[cat]:
            continue
        lines.append(f"## {cat.title()} Tools")
        for hook, label in categories[cat]:
            lines.append(f"- `--{hook}` — {label}")
            total_hooks += 1
        lines.append("")

    try:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"✅ CLI reference generated: {outfile}")
        print(f"Summary: {total_hooks} hooks documented.")
    except Exception as e:
        logger.error(f"[DocGen] Failed to write CLI doc: {e}")
        print(f"[DocGen] Error: Could not write CLI doc to {outfile}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pulse CLI DocGen")
    parser.add_argument(
        "--outfile", type=str, default=DEFAULT_OUTFILE, help="Output markdown file path"
    )
    parser.add_argument(
        "--type",
        type=str,
        default="all",
        choices=ALL_CATEGORIES + ["all"],
        help="Filter by mode type",
    )
    args = parser.parse_args()
    generate_cli_doc(outfile=args.outfile, mode_type=args.type)
