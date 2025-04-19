""" 
pulse_shell_autohook.py

Scans Pulse modules for CLI hook candidates.
Looks for files with:
- `main()` or `run()` methods
- `__hook__ = True` tag
- Located in dev_tools/, forecasting/, or similar

Generates:
- Suggested `--mode` entries for pulse_ui_shell.py
- Optional JSON hook registry

Author: Pulse v0.10
"""

import os
import json
from utils.log_utils import get_logger
from hook_utils import scan_for_hooks
from core.path_registry import PATHS
from operator_interface.pulse_prompt_logger import log_prompt

logger = get_logger(__name__)

SEARCH_PATHS = ["dev_tools", "simulation_engine/forecasting"]
HOOKS_JSON = PATHS.get("HOOKS_JSON", "dev_tools/pulse_hooks_config.json")
SHELL_TEMPLATE_DIR = PATHS.get("SHELL_TEMPLATE_DIR", "dev_tools/shell_templates")

def write_hook_summary(modules):
    with open(HOOKS_JSON, 'w') as f:
        json.dump(modules, f, indent=2)
    logger.info(f"✅ Hook summary written to {HOOKS_JSON}")

def print_shell_templates(modules):
    print("\n📎 Suggested CLI shell modes:")
    for mod in modules:
        name = mod["module"].split(".")[-1]
        flag = mod["hook_type"]
        print(f"elif args.mode == '{name}':")
        print(f"    from {mod['module']} import {mod['function']}")
        print(f"    {mod['function']}()\n")

def main():
    try:
        found, _ = scan_for_hooks(SEARCH_PATHS)
        write_hook_summary(found)
        print_shell_templates(found)
    except Exception as e:
        logger.error(f"Shell autohook failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()