"""
pulse_argument_checker.py

Scans .py files for function calls where keyword arguments may not match the function definitions.
Highlights possible issues like misspelled or outdated keyword arguments (e.g. decay_rate vs rate).

Author: Pulse v0.20

Usage:
    python dev_tools/pulse_argument_checker.py [--paths path1 path2 ...] [--verbose]

- Specify search paths with --paths (default: simulation_engine dev_tools)
- Use --verbose for more detailed output
- Prints a summary of files checked and issues found
"""
import ast
import os
import logging
import argparse
from typing import List, Tuple, Dict

logger = logging.getLogger("pulse_argument_checker")

DEFAULT_SEARCH_PATHS = ["simulation_engine", "dev_tools"]

def extract_function_defs(tree: ast.AST) -> Dict[str, List[str]]:
    """
    Extract function definitions and their argument names from an AST tree.
    Args:
        tree (ast.AST): Parsed AST tree.
    Returns:
        Dict[str, List[str]]: Mapping from function name to list of argument names.
    """
    defs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defs[node.name] = [arg.arg for arg in node.args.args]
    return defs

def check_keyword_args(filepath: str) -> List[Tuple[str, str, List[str]]]:
    """
    Check for keyword argument mismatches in a Python file.
    Args:
        filepath (str): Path to the Python file.
    Returns:
        List[Tuple[str, str, List[str]]]: List of (function, bad_kw, valid_args) tuples.
    """
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

def run_check(search_paths: List[str], verbose: bool = False) -> None:
    """
    Run the keyword argument checker on all .py files in the given search paths.
    Args:
        search_paths (List[str]): List of directories to search.
        verbose (bool): If True, print all files checked.
    """
    files_checked = 0
    total_issues = 0
    for root_dir in search_paths:
        for root, dirs, files in os.walk(root_dir):
            # Ignore all directories starting with a dot
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    path = os.path.join(root, file)
                    files_checked += 1
                    try:
                        issues = check_keyword_args(path)
                        if issues:
                            total_issues += len(issues)
                            logger.warning(f"⚠️  Potential keyword mismatch in: {path}")
                            for fname, bad_kw, valid in issues:
                                logger.warning(f" - {fname}(... {bad_kw}=...) [Valid: {valid}]")
                        elif verbose:
                            logger.info(f"Checked: {path}")
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to parse {path}: {e}")
    print(f"\nSummary: {files_checked} files checked, {total_issues} issues found.")

def parse_args():
    """
    Parse CLI arguments for search paths and verbosity.
    Returns:
        (List[str], bool): (search_paths, verbose)
    """
    parser = argparse.ArgumentParser(description="Pulse Argument Checker")
    parser.add_argument("--paths", nargs="*", default=DEFAULT_SEARCH_PATHS, help="Directories to search")
    parser.add_argument("--verbose", action="store_true", help="Print all files checked")
    args = parser.parse_args()
    return args.paths, args.verbose

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    search_paths, verbose = parse_args()
    run_check(search_paths, verbose)