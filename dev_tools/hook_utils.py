"""
hook_utils.py

Scans directories for Python modules with CLI hook candidates (main/run functions or __hook__ tag).
Returns a list of hookable modules and associated metadata for CLI integration.

Usage:
    from dev_tools.hook_utils import scan_for_hooks
    modules, metadata = scan_for_hooks(["dev_tools", "simulation_engine/forecasting"])

Returned hookable_modules: List[Dict[str, Any]] with keys:
    - module: module import path (str)
    - path: file path (str)
    - function: 'main' or 'run' (str)
    - hook_type: 'test', 'batch', or 'tool' (str)

Returned metadata: Dict[str, Dict[str, str]] with keys:
    - label: human-readable label
    - category: 'suite', 'batch', or 'tool'
"""

import os
import ast
from typing import List, Dict, Any, Tuple


def scan_for_hooks(
    search_paths: List[str],
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, str]]]:
    """
    Scan directories for Python modules with CLI hook candidates.
    Args:
        search_paths (List[str]): List of directories to search.
    Returns:
        Tuple[List[Dict[str, Any]], Dict[str, Dict[str, str]]]: (hookable_modules, metadata)
    """
    hookable_modules = []
    metadata = {}

    for base_path in search_paths:
        for root, _, files in os.walk(base_path):
            for fname in files:
                if fname.endswith(".py") and not fname.startswith("__"):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            node = ast.parse(f.read(), filename=fpath)
                        # Detect main/run function or __hook__ tag
                        has_main = any(
                            isinstance(n, ast.FunctionDef) and n.name in ["main", "run"]
                            for n in node.body
                        )
                        has_tag = any(
                            isinstance(n, ast.Assign)
                            and getattr(n.targets[0], "id", "") == "__hook__"
                            for n in node.body
                        )
                        if has_main or has_tag:
                            module_path = os.path.splitext(
                                os.path.relpath(fpath, ".").replace(os.sep, ".")
                            )[0]
                            hook_type = (
                                "test"
                                if "test" in fname
                                else "batch"
                                if "batch" in fname
                                else "tool"
                            )
                            hookable_modules.append(
                                {
                                    "module": module_path,
                                    "path": fpath,
                                    "function": "main" if has_main else "run",
                                    "hook_type": hook_type,
                                }
                            )
                            key = fname.replace(".py", "")
                            metadata[key] = {
                                "label": f"Auto-hooked CLI tool: {key}",
                                "category": "suite"
                                if "test" in fname
                                else "batch"
                                if "batch" in fname
                                else "tool",
                            }
                    except Exception as e:
                        print(f"⚠️ Failed to parse {fname}: {e}")
    return hookable_modules, metadata
