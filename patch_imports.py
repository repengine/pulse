#!/usr/bin/env python3
import os
import re
from typing import List, Optional, Match


def module_exists(mod: str, project_root: str) -> bool:
    # Check if a module exists as a single file or as a package with an __init__.py
    path1: str = os.path.join(project_root, mod.replace(".", "/") + ".py")
    if os.path.exists(path1):
        return True
    path2: str = os.path.join(project_root, mod.replace(".", "/"), "__init__.py")
    if os.path.exists(path2):
        return True
    return False


def search_module(module_basename: str, project_root: str) -> List[str]:
    # Search for a file named module_basename.py anywhere in the project,
    # ignoring directories that start with a dot.
    matches: List[str] = []
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        if module_basename + ".py" in files:
            full_path: str = os.path.join(root, module_basename + ".py")
            rel_path: str = os.path.relpath(full_path, project_root)
            # Convert file path to dotted module path (strip .py extension)
            mod_path: str = rel_path[:-3].replace(os.sep, ".")
            matches.append(mod_path)
    return matches


def patch_imports_in_file(file_path: str, project_root: str) -> bool:
    changed: bool = False
    new_lines: List[str] = []
    # Regular expressions for "from X import ..." and "import X" statements
    pattern_from: re.Pattern[str] = re.compile(r"^(from\s+([\w\.]+)\s+import\s+.*)$")
    pattern_import: re.Pattern[str] = re.compile(
        r"^(import\s+([\w\.]+)(\s+as\s+\w+)?)(.*)$"
    )

    with open(file_path, "r", encoding="utf-8") as f:
        lines: List[str] = f.readlines()

    for line_content in lines:  # Renamed line to line_content to avoid conflict
        stripped: str = line_content.strip()
        # Try to match "from ... import ..." statements
        m_from: Optional[Match[str]] = pattern_from.match(stripped)
        if m_from:
            module_name: str = m_from.group(2)
            if not module_exists(module_name, project_root):
                # Use the last component as a heuristic to search for the module file
                base_module: str = module_name.split(".")[-1]
                candidates: List[str] = search_module(base_module, project_root)
                if len(candidates) == 1:
                    new_module: str = candidates[0]
                    new_line_content: str = line_content.replace(
                        module_name, new_module
                    )
                    print(
                        f"File {file_path}: Replacing '{module_name}' with '{new_module}'"
                    )
                    line_content = new_line_content
                    changed = True
        else:
            # Try to match "import ..." statements
            m_import: Optional[Match[str]] = pattern_import.match(stripped)
            if m_import:
                module_name = m_import.group(2)
                if not module_exists(module_name, project_root):
                    base_module = module_name.split(".")[-1]
                    candidates = search_module(base_module, project_root)
                    if len(candidates) == 1:
                        new_module = candidates[0]
                        new_line_content = line_content.replace(module_name, new_module)
                        print(
                            f"File {file_path}: Replacing '{module_name}' with '{new_module}'"
                        )
                        line_content = new_line_content
                        changed = True
        new_lines.append(line_content)

    if changed:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    return changed


def patch_all_imports(project_root: str) -> None:
    changes_made: int = 0
    for root, dirs, files in os.walk(project_root):
        # Ignore all directories starting with a dot
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for file_name in files:  # Renamed file to file_name
            # Ignore files that start with a dot
            if file_name.startswith("."):
                continue
            if file_name.endswith(".py") and file_name != "patch_imports.py":
                file_path_to_patch: str = os.path.join(root, file_name)  # Renamed
                if patch_imports_in_file(file_path_to_patch, project_root):
                    changes_made += 1
    print(f"Patched imports in {changes_made} files.")


if __name__ == "__main__":
    current_project_root: str = os.path.abspath(os.path.dirname(__file__))
    patch_all_imports(current_project_root)
