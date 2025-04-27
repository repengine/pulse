#!/usr/bin/env python3
"""
Generate a plain edge-list of internal module dependencies for the Pulse project.
Scans all .py files excluding tests/ and outputs MODULE_DEPENDENCY_MAP.md at project root.
"""

import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
IGNORE_DIRS = {'tests'}
MODULE_MAP = {}  # module_name -> file_path

# Discover modules
for dirpath, dirnames, filenames in os.walk(ROOT):
    # adjust dirnames in-place to skip tests
    dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith('.')]
    for fname in filenames:
        if not fname.endswith('.py'):
            continue
        full = os.path.join(dirpath, fname)
        rel = os.path.relpath(full, ROOT)
        parts = rel.replace(os.path.sep, '/').split('/')
        # ignore __init__.py? But treat.
        if parts[-1] == '__init__.py':
            mod = '.'.join(parts[:-1])
        else:
            mod = '.'.join(parts)[:-3]  # remove .py
        if not mod:
            mod = '__init__'
        MODULE_MAP[mod] = rel

# Sort module names by length desc to match longest first
sorted_mods = sorted(MODULE_MAP.keys(), key=lambda x: -len(x))

edges = []

# Parse imports
for mod, rel in MODULE_MAP.items():
    path = os.path.join(ROOT, rel)
    with open(path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=rel)
        except SyntaxError:
            continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                # find internal
                for m in sorted_mods:
                    if name == m or name.startswith(m + '.'):
                        edges.append((rel, MODULE_MAP[m]))
                        break
        elif isinstance(node, ast.ImportFrom):
            if not node.module:
                continue
            name = node.module
            # handle relative imports
            if node.level:
                # compute mod name relative
                parent = mod.split('.')[:-node.level]
                name = '.'.join(parent + [name]) if name else '.'.join(parent)
            for m in sorted_mods:
                if name == m or name.startswith(m + '.'):
                    edges.append((rel, MODULE_MAP[m]))
                    break

# Deduplicate edges
edges = sorted(set(edges))

# Write to MODULE_DEPENDENCY_MAP.md
out_path = os.path.join(ROOT, 'MODULE_DEPENDENCY_MAP.md')
with open(out_path, 'w', encoding='utf-8') as outf:
    outf.write('# Module Dependency Edge List\n\n')
    for src, dst in edges:
        outf.write(f'{src} -> {dst}\n')
print(f'Wrote {len(edges)} edges to {out_path}')