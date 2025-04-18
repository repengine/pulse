import os
import ast

def scan_for_hooks(search_paths):
    hookable_modules = []
    metadata = {}

    for base_path in search_paths:
        for root, _, files in os.walk(base_path):
            for fname in files:
                if fname.endswith(".py") and not fname.startswith("__"):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            node = ast.parse(f.read(), filename=fpath)
                            has_main = any(isinstance(n, ast.FunctionDef) and n.name in ["main", "run"] for n in node.body)
                            has_tag = any(isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "__hook__" for n in node.body)
                            if has_main or has_tag:
                                module_path = os.path.splitext(os.path.relpath(fpath, ".").replace(os.sep, "."))[0]
                                hookable_modules.append({
                                    "module": module_path,
                                    "path": fpath,
                                    "function": "main" if has_main else "run",
                                    "hook_type": "test" if "test" in fname else "batch" if "batch" in fname else "tool"
                                })
                                key = fname.replace(".py", "")
                                metadata[key] = {
                                    "label": f"Auto-hooked CLI tool: {key}",
                                    "category": "suite" if "test" in fname else "batch" if "batch" in fname else "tool"
                                }
                    except Exception as e:
                        print(f"⚠️ Failed to parse {fname}: {e}")
    return hookable_modules, metadata