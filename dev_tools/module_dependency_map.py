"""
module_dependency_map.py

Analyzes and prints import dependencies between Pulse modules.
Optionally exports to Graphviz DOT format.

Usage:
    python module_dependency_map.py [--root <dir>] [--dot <output.dot>]

- Prints a summary of modules and dependencies found.
- Skips common virtual environment and cache directories.
- Add --root and --dot CLI arguments for flexibility.
"""
import os
import ast
import argparse
from typing import Dict, List, Set

def find_py_files(root: str) -> List[str]:
    """
    Recursively find all .py files under the given root directory.
    Args:
        root (str): Root directory to search.
    Returns:
        List[str]: List of Python file paths.
    """
    py_files = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(dirpath, f))
    return py_files

def analyze_imports(root: str = ".", exclude_dirs: Set[str] = {"venv", "env", "__pycache__"}) -> Dict[str, List[str]]:
    """
    Analyze import dependencies for all .py files under root, skipping excluded directories.
    Args:
        root (str): Root directory to search.
        exclude_dirs (Set[str]): Directory names to exclude from analysis.
    Returns:
        Dict[str, List[str]]: Mapping from file path to list of imported modules.
    """
    deps = {}
    for fpath in find_py_files(root):
        if any(ex in fpath for ex in exclude_dirs):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=fpath)
                imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
                deps[fpath] = imports
        except Exception as e:
            print(f"[DepMap] Failed to parse {fpath}: {e}")
    return deps

def export_dot(deps: Dict[str, List[str]], dot_path: str = "module_deps.dot") -> None:
    """
    Export dependencies to a Graphviz DOT file.
    Args:
        deps (Dict[str, List[str]]): Dependency mapping.
        dot_path (str): Output DOT file path.
    """
    try:
        with open(dot_path, "w", encoding="utf-8") as f:
            f.write("digraph G {\n")
            for mod, imports in deps.items():
                mod_name = os.path.basename(mod)
                for imp in imports:
                    f.write(f'    "{mod_name}" -> "{imp}";\n')
            f.write("}\n")
        print(f"Dependency graph exported to {dot_path}")
    except Exception as e:
        print(f"[DepMap] Error: {e}")

def print_summary(deps: Dict[str, List[str]]) -> None:
    """
    Print a summary of modules and dependencies found.
    Args:
        deps (Dict[str, List[str]]): Dependency mapping.
    """
    print(f"\nSummary: {len(deps)} modules analyzed.")
    total_edges = sum(len(imps) for imps in deps.values())
    print(f"Total dependencies: {total_edges}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pulse Module Dependency Map")
    parser.add_argument("--root", type=str, default="c:/Users/natew/Pulse", help="Root directory to analyze")
    parser.add_argument("--dot", type=str, default="module_deps.dot", help="Output DOT file path")
    args = parser.parse_args()

    deps = analyze_imports(args.root)
    for mod, imports in deps.items():
        print(f"{mod}: {set(imports)}")
    print_summary(deps)
    export_dot(deps, args.dot)
