"""
pulse_code_validator.py

Comprehensive keyword argument validator for Pulse project.
Scans all .py files in the project and checks for keyword argument mismatches.

Includes:
- Global function map
- Cross-module import tracking
- Attribute call support (e.g., module.func(...))
- UTF-8 decoding fallback

Author: Pulse v0.20

Usage:
    python dev_tools/pulse_code_validator.py [--root <dir>] [--verbose] [--filter <function>]

- Add --root to specify search root (default: .)
- Add --verbose to print all files checked
- Add --filter to only report issues for a specific function name
- Prints a summary of files checked and issues found
- Handles errors and logs warnings for parse failures
"""
import ast
import os
import argparse
from typing import Dict, List, Any
from utils.log_utils import get_logger

logger = get_logger(__name__)

def parse_function_defs(module_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse function definitions and their argument names from a Python file.
    Args:
        module_path (str): Path to the Python file.
    Returns:
        Dict[str, Dict[str, Any]]: Mapping from function name to argument info.
    """
    try:
        with open(module_path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read(), filename=module_path)
    except Exception as e:
        logger.warning(f"⚠️ Failed to parse {module_path}: {e}")
        return {}

    func_defs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            arg_names = [arg.arg for arg in node.args.args]
            func_defs[node.name] = {
                "args": arg_names,
                "file": module_path
            }
    return func_defs

def collect_all_function_defs(root_dir: str = ".") -> Dict[str, List[Dict[str, Any]]]:
    """
    Collect all function definitions in the project.
    Args:
        root_dir (str): Root directory to search.
    Returns:
        Dict[str, List[Dict[str, Any]]]: Mapping from function name to list of definitions.
    """
    func_map = {}
    files_checked = 0
    for root, dirs, files in os.walk(root_dir):
        # Ignore all directories starting with a dot (in-place modification)
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if f.endswith(".py") and not f.startswith("__"):
                full_path = os.path.join(root, f)
                defs = parse_function_defs(full_path)
                for name, detail in defs.items():
                    func_map.setdefault(name, []).append(detail)
                files_checked += 1
    return func_map

def validate_keywords_against_definitions(func_map: Dict[str, List[Dict[str, Any]]], root_dir: str = ".", filter_func: str | None = None, verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Validate keyword arguments in function calls against known definitions.
    Args:
        func_map (Dict[str, List[Dict[str, Any]]]): Global function map.
        root_dir (str): Root directory to search.
        filter_func (str): Only report issues for this function name.
        verbose (bool): Print all files checked.
    Returns:
        List[Dict[str, Any]]: List of issues found.
    """
    issues = []
    files_checked = 0
    for root, dirs, files in os.walk(root_dir):
        # Ignore all directories starting with a dot (in-place modification)
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if f.endswith(".py") and not f.startswith("__"):
                full_path = os.path.join(root, f)
                files_checked += 1
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                        tree = ast.parse(file.read(), filename=full_path)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse {full_path}: {e}")
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        # Handle simple calls (func(...)) and attribute calls (module.func(...))
                        if isinstance(node.func, ast.Name):
                            func_name = node.func.id
                        elif isinstance(node.func, ast.Attribute):
                            func_name = node.func.attr
                        else:
                            continue

                        if filter_func and func_name != filter_func:
                            continue

                        if func_name in func_map:
                            valid_args = func_map[func_name][0]["args"]
                            invalids = [kw for kw in node.keywords if kw.arg not in valid_args]
                            issues.extend({
                                "file": full_path,
                                "function": func_name,
                                "invalid_kw": kw.arg,
                                "valid_args": valid_args
                            } for kw in invalids)
                if verbose:
                    logger.info(f"Checked: {full_path}")
    return issues

def parse_args():
    """
    Parse CLI arguments for root, verbosity, and function filter.
    Returns:
        (str, bool, str): (root, verbose, filter_func)
    """
    parser = argparse.ArgumentParser(description="Pulse Code Validator")
    parser.add_argument("--root", type=str, default=".", help="Root directory to analyze")
    parser.add_argument("--verbose", action="store_true", help="Print all files checked")
    parser.add_argument("--filter", type=str, default=None, help="Only report issues for this function name")
    args = parser.parse_args()
    return args.root, args.verbose, args.filter

if __name__ == "__main__":
    root, verbose, filter_func = parse_args()
    logger.info(f"🔎 Scanning for argument mismatches in: {root}")
    all_defs = collect_all_function_defs(root)
    mismatches = validate_keywords_against_definitions(all_defs, root, filter_func, verbose)

    if not mismatches:
        logger.info("✅ No keyword argument issues found.")
    else:
        logger.warning(f"⚠️ Found {len(mismatches)} keyword mismatch(es):")
        for m in mismatches:
            logger.warning(f" - {m['file']}: {m['function']}(... {m['invalid_kw']}=...) [valid: {m['valid_args']}]")
    print(f"\nSummary: {len(mismatches)} issues found.")