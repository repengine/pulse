"""
pulse_scan_hooks.py

Re-scans all hookable modules and rewrites pulse_hooks_config.json automatically.
Should be run after new modules are added to ensure Pulse CLI dashboard stays current.

Author: Pulse v0.10
"""

import json
import os
import ast
from utils.log_utils import get_logger
from engine.path_registry import PATHS

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

logger = get_logger(__name__)

HOOKS_DIR = PATHS.get("HOOKS_DIR", "hooks")
SEARCH_PATHS = ["dev_tools", "simulation_engine/forecasting", HOOKS_DIR]
HOOKS_JSON = "dev_tools/pulse_hooks_config.json"


def scan_for_hooks():
    """
    Scans SEARCH_PATHS for Python modules with CLI hook candidates.
    Updates HOOKS_JSON with discovered hooks and metadata.
    """
    hookable_modules = {}
    metadata = {}

    for base_path in SEARCH_PATHS:
        for root, _, files in os.walk(base_path):
            for fname in files:
                if fname.endswith(".py") and not fname.startswith("__"):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r") as f:
                            node = ast.parse(f.read(), filename=fpath)
                            has_main = any(
                                isinstance(n, ast.FunctionDef)
                                and n.name in ["main", "run"]
                                for n in node.body
                            )
                            has_tag = any(
                                isinstance(n, ast.Assign)
                                and getattr(n.targets[0], "id", "") == "__hook__"
                                for n in node.body
                            )
                            if has_main or has_tag:
                                key = fname.replace(".py", "")
                                hookable_modules[key] = True
                                category = (
                                    "suite"
                                    if "test" in fname
                                    else "batch" if "batch" in fname else "tool"
                                )
                                metadata[key] = {
                                    "label": f"Auto-hooked CLI tool: {key}",
                                    "category": category,
                                }
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to parse {fname}: {e}")

    logger.info(f"✅ Found {len(hookable_modules)} hookable modules.")
    full_data = {"active_hooks": hookable_modules, "metadata": metadata}

    os.makedirs(os.path.dirname(HOOKS_JSON), exist_ok=True)
    with open(HOOKS_JSON, "w") as f:
        json.dump(full_data, f, indent=2)

    logger.info(f"🔁 Updated hook config written to {HOOKS_JSON}")


if __name__ == "__main__":
    scan_for_hooks()
