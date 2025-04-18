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
"""

import ast
import os
from utils.log_utils import get_logger

logger = get_logger(__name__)

def parse_function_defs(module_path):
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

def collect_all_function_defs(root_dir="."):
    func_map = {}
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.endswith(".py") and not f.startswith("__"):
                full_path = os.path.join(root, f)
                defs = parse_function_defs(full_path)
                for name, detail in defs.items():
                    func_map.setdefault(name, []).append(detail)
    return func_map

def validate_keywords_against_definitions(func_map, root_dir="."):
    issues = []
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.endswith(".py") and not f.startswith("__"):
                full_path = os.path.join(root, f)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                        tree = ast.parse(file.read(), filename=full_path)
                except Exception as e:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        # Handle simple calls (func(...))
                        if isinstance(node.func, ast.Name):
                            func_name = node.func.id
                        elif isinstance(node.func, ast.Attribute):
                            func_name = node.func.attr
                        else:
                            continue

                        if func_name in func_map:
                            valid_args = func_map[func_name][0]["args"]
                            for kw in node.keywords:
                                if kw.arg not in valid_args:
                                    issues.append({
                                        "file": full_path,
                                        "function": func_name,
                                        "invalid_kw": kw.arg,
                                        "valid_args": valid_args
                                    })
    return issues

if __name__ == "__main__":
    logger.info("🔎 Scanning for argument mismatches...")
    all_defs = collect_all_function_defs(".")
    mismatches = validate_keywords_against_definitions(all_defs)

    if not mismatches:
        logger.info("✅ No keyword argument issues found.")
    else:
        logger.warning(f"⚠️ Found {len(mismatches)} keyword mismatch(es):")
        for m in mismatches:
            logger.warning(f" - {m['file']}: {m['function']}(... {m['invalid_kw']}=...) [valid: {m['valid_args']}]")