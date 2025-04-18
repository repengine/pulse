""" 
pulse_cli_docgen.py

Generates CLI documentation markdown for Pulse hooks based on pulse_hooks_config.json.

Author: Pulse v0.10
"""

import json
from utils.log_utils import get_logger

CONFIG = "dev_tools/pulse_hooks_config.json"
OUTFILE = "pulse_cli_reference.md"

logger = get_logger(__name__)

def generate_cli_doc():
    with open(CONFIG, 'r', encoding='utf-8') as f:
        config = json.load(f)

    lines = [
        "# 🧭 Pulse CLI Reference",
        "",
        "Below are all available auto-hooked CLI tools, grouped by category.",
        ""
    ]

    categories = {"suite": [], "batch": [], "test": [], "tool": []}
    for hook, enabled in config["active_hooks"].items():
        if enabled:
            meta = config["metadata"].get(hook, {})
            label = meta.get("label", "No description")
            cat = meta.get("category", "tool")
            categories[cat].append((hook, label))

    for cat, entries in categories.items():
        lines.append(f"## {cat.title()} Tools")
        for hook, label in entries:
            lines.append(f"- `--{hook}` — {label}")
        lines.append("")

    with open(OUTFILE, "w", encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"✅ CLI reference generated: {OUTFILE}")


if __name__ == "__main__":
    generate_cli_doc()