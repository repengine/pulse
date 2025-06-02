#!/usr/bin/env python3
import os
import re


def module_exists(mod, project_root):
    # Check if a module exists as a single file or as a package with an __init__.py
    path1 = os.path.join(project_root, mod.replace(".", "/") + ".py")
    if os.path.exists(path1):
        return True
    path2 = os.path.join(project_root, mod.replace(".", "/"), "__init__.py")
    if os.path.exists(path2):
        return True
    return False


def search_module(module_basename, project_root):
    # Search for a file named module_basename.py anywhere in the project,
    # ignoring directories that start with a dot.
    matches = []
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        if module_basename + ".py" in files:
            full_path = os.path.join(root, module_basename + ".py")
            rel_path = os.path.relpath(full_path, project_root)
            # Convert file path to dotted module path (strip .py extension)
            mod_path = rel_path[:-3].replace(os.sep, ".")
            matches.append(mod_path)
    return matches


def patch_imports_in_file(file_path, project_root):
    changed = False
    new_lines = []
    # Regular expressions for "from X import ..." and "import X" statements
    pattern_from = re.compile(r"^(from\s+([\w\.]+)\s+import\s+.*)$")
    pattern_import = re.compile(r"^(import\s+([\w\.]+)(\s+as\s+\w+)?)(.*)$")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()
        # Try to match "from ... import ..." statements
        m = pattern_from.match(stripped)
        if m:
            module_name = m.group(2)
            if not module_exists(module_name, project_root):
                # Use the last component as a heuristic to search for the module file
                base_module = module_name.split(".")[-1]
                candidates = search_module(base_module, project_root)
                if len(candidates) == 1:
                    new_module = candidates[0]
                    new_line = line.replace(module_name, new_module)
                    print(
                        f"File {file_path}: Replacing '{module_name}' with '{new_module}'")
                    line = new_line
                    changed = True
        else:
            # Try to match "import ..." statements
            m = pattern_import.match(stripped)
            if m:
                module_name = m.group(2)
                if not module_exists(module_name, project_root):
                    base_module = module_name.split(".")[-1]
                    candidates = search_module(base_module, project_root)
                    if len(candidates) == 1:
                        new_module = candidates[0]
                        new_line = line.replace(module_name, new_module)
                        print(
                            f"File {file_path}: Replacing '{module_name}' with '{new_module}'")
                        line = new_line
                        changed = True
        new_lines.append(line)

    if changed:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    return changed


def patch_all_imports(project_root):
    changes_made = 0
    for root, dirs, files in os.walk(project_root):
        # Ignore all directories starting with a dot
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for file in files:
            # Ignore files that start with a dot
            if file.startswith("."):
                continue
            if file.endswith(".py") and file != "patch_imports.py":
                file_path = os.path.join(root, file)
                if patch_imports_in_file(file_path, project_root):
                    changes_made += 1
    print(f"Patched imports in {changes_made} files.")


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.dirname(__file__))
    patch_all_imports(project_root)
