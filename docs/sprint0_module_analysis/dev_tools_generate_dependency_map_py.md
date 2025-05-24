# Analysis of `dev_tools/generate_dependency_map.py`

## Module Intent/Purpose
This script generates a map of internal module dependencies by scanning project Python files, parsing import statements using `ast`, and resolving them. The output is an edge-list in `MODULE_DEPENDENCY_MAP.md` for understanding project structure.

## Operational Status/Completeness
Largely functional. Traverses directories, identifies Python files, and uses `ast` for import parsing. Attempts to handle absolute and relative imports.

## Implementation Gaps / Unfinished Next Steps
- **Relative Import Resolution:** Complex and noted as needing refinement, especially for `from . import module_name` (currently skipped).
- **`__init__.py` Handling:** Interaction with relative import resolution is complex.
- **External Dependencies:** Does not report external library usage.
- **Output Format:** Simple edge list; DOT file for Graphviz could be more useful.
- **Error Reporting:** Basic `SyntaxError` handling; could be more comprehensive for resolution issues.

## Connections & Dependencies
- **Direct Project Module Imports:** None.
- **External Library Dependencies:** `ast`, `os` (standard Python).
- **Interaction:** Reads all `.py` files (excluding `IGNORE_DIRS`).
- **Input/Output Files:**
    - **Inputs:** Project Python files.
    - **Output:** `MODULE_DEPENDENCY_MAP.md` at project root.

## Function and Class Example Usages
- CLI: `python dev_tools/generate_dependency_map.py`

## Hardcoding Issues
- `IGNORE_DIRS` (e.g., `{'tests'}`).
- Output filename `MODULE_DEPENDENCY_MAP.md`.
- Project root determination assumes script location.

## Coupling Points
- Python's import system rules and syntax.
- `ast` module structure.
- File system structure.

## Existing Tests
- No specific test file listed. Testing would need a fixture project with diverse import patterns.

## Module Architecture and Flow
1.  Initialize `ROOT`, `IGNORE_DIRS`, `MODULE_MAP`.
2.  **Module Discovery:** `os.walk` to find Python files, construct module names, populate `MODULE_MAP`.
3.  Sort `MODULE_MAP` keys by length (descending) for correct import matching.
4.  **Import Parsing:** Iterate `MODULE_MAP`, parse files with `ast`.
    - For `ast.Import` and `ast.ImportFrom`, resolve module names (handling relative imports with noted complexity) against `sorted_mods`.
    - Add `(source_path, dest_path)` to `edges` for internal dependencies.
5.  Finalize `edges` (remove duplicates, sort).
6.  Write edges to `MODULE_DEPENDENCY_MAP.md`.

## Naming Conventions
- Adheres to Python conventions. Names are descriptive.