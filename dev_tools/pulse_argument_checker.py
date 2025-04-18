""" 
pulse_argument_checker.py

Scans .py files for function calls where keyword arguments may not match the function definitions.
Highlights possible issues like misspelled or outdated keyword arguments (e.g. decay_rate vs rate).

Author: Pulse v0.20
"""

import ast
import os
import logging

logger = logging.getLogger(__name__)

SEARCH_PATHS = ["simulation_engine", "dev_tools"]

def extract_function_defs(tree):
    defs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defs[node.name] = [arg.arg for arg in node.args.args]
    return defs

def check_keyword_args(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()

    tree = ast.parse(code, filename=filepath)
    function_defs = extract_function_defs(tree)

    issues = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fname = node.func.id
            keywords = [k.arg for k in node.keywords]
            if fname in function_defs:
                valid_args = function_defs[fname]
                for k in keywords:
                    if k not in valid_args:
                        issues.append((fname, k, valid_args))

    return issues

def run_check():
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                path = os.path.join(root, file)
                try:
                    issues = check_keyword_args(path)
                    if issues:
                        logger.warning(f"⚠️  Potential keyword mismatch in: {path}")
                        for fname, bad_kw, valid in issues:
                            logger.warning(f" - {fname}(... {bad_kw}=...) [Valid: {valid}]")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to parse {path}: {e}")

if __name__ == "__main__":
    run_check()