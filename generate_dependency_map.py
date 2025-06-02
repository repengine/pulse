#!/usr/bin/env python3
"""
Generate module dependency map for the Pulse project.
Creates a DOT file showing import relationships between modules.
"""

import ast
from pathlib import Path
from typing import Dict, Set


def extract_imports(file_path: Path) -> Set[str]:
    """Extract import statements from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)

        return imports
    except Exception:
        return set()


def get_pulse_modules(root_path: Path) -> Dict[str, Set[str]]:
    """Get all Pulse modules and their dependencies."""
    modules = {}

    # Define the main module directories
    module_dirs = [
        "engine",
        "rules",
        "ingestion",
        "analytics",
        "adapters",
        "api",
        "cli",
    ]

    for module_dir in module_dirs:
        dir_path = root_path / module_dir
        if dir_path.exists():
            for py_file in dir_path.rglob("*.py"):
                if py_file.name != "__init__.py":
                    relative_path = py_file.relative_to(root_path)
                    module_name = (
                        str(relative_path)
                        .replace("/", ".")
                        .replace("\\", ".")
                        .replace(".py", "")
                    )
                    imports = extract_imports(py_file)

                    # Filter to only Pulse-related imports
                    pulse_imports = {
                        imp
                        for imp in imports
                        if imp.startswith(
                            (
                                "engine",
                                "rules",
                                "ingestion",
                                "analytics",
                                "adapters",
                                "api",
                                "cli",
                            )
                        )
                    }
                    modules[module_name] = pulse_imports

    return modules


def generate_dot_file(modules: Dict[str, Set[str]], output_path: Path):
    """Generate a DOT file for the module dependencies."""
    with open(output_path, "w") as f:
        f.write("digraph PulseDependencies {\n")
        f.write("    rankdir=LR;\n")
        f.write("    node [shape=box, style=rounded];\n\n")

        # Add nodes with colors by domain
        colors = {
            "engine": "lightblue",
            "rules": "lightgreen",
            "ingestion": "lightyellow",
            "analytics": "lightcoral",
            "adapters": "lightgray",
            "api": "lightpink",
            "cli": "lightcyan",
        }

        for module in modules:
            domain = module.split(".")[0]
            color = colors.get(domain, "white")
            f.write(f'    "{module}" [fillcolor={color}, style=filled];\n')

        f.write("\n")

        # Add edges
        for module, imports in modules.items():
            for imp in imports:
                # Only show dependencies between actual modules we found
                if imp in modules:
                    f.write(f'    "{module}" -> "{imp}";\n')

        f.write("}\n")


def main():
    """Main function to generate the dependency map."""
    root_path = Path(".")
    modules = get_pulse_modules(root_path)

    output_path = Path("module_deps.dot")
    generate_dot_file(modules, output_path)

    print(f"Generated dependency map with {len(modules)} modules")
    print(f"Output written to: {output_path}")

    # Also create a simple text summary
    summary_path = Path("module_deps_summary.txt")
    with open(summary_path, "w") as f:
        f.write("Pulse Module Dependency Summary\n")
        f.write("=" * 40 + "\n\n")

        for domain in [
            "engine",
            "rules",
            "ingestion",
            "analytics",
            "adapters",
            "api",
            "cli",
        ]:
            domain_modules = [m for m in modules if m.startswith(domain)]
            if domain_modules:
                f.write(f"{domain.upper()} ({len(domain_modules)} modules):\n")
                for module in sorted(domain_modules):
                    deps = [d for d in modules[module] if d in modules]
                    f.write(f"  {module} -> {len(deps)} dependencies\n")
                f.write("\n")

    print(f"Summary written to: {summary_path}")


if __name__ == "__main__":
    main()
