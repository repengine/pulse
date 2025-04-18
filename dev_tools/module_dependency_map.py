"""
module_dependency_map.py

Analyzes and prints import dependencies between Pulse modules.
Optionally exports to Graphviz DOT format.

Usage:
    python module_dependency_map.py
"""

import os
import ast

def find_py_files(root):
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(dirpath, f)

def analyze_imports(root=".", exclude_dirs=("venv", "env", "__pycache__")):
    deps = {}
    for fpath in find_py_files(root):
        if any(ex in fpath for ex in exclude_dirs):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=fpath)
                imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
                deps[fpath] = imports
        except Exception:
            continue
    return deps

def export_dot(deps, dot_path="module_deps.dot"):
    try:
        with open(dot_path, "w") as f:
            f.write("digraph G {\n")
            for mod, imports in deps.items():
                mod_name = os.path.basename(mod)
                for imp in imports:
                    f.write(f'    "{mod_name}" -> "{imp}";\n')
            f.write("}\n")
        print(f"Dependency graph exported to {dot_path}")
    except Exception as e:
        print(f"[DepMap] Error: {e}")

if __name__ == "__main__":
    deps = analyze_imports("c:/Users/natew/Pulse")
    for mod, imports in deps.items():
        print(f"{mod}: {set(imports)}")
    export_dot(deps)
