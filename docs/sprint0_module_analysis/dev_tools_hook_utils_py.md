# Analysis of `dev_tools/hook_utils.py`

## Module Intent/Purpose
`hook_utils.py` provides `scan_for_hooks` to discover Python modules suitable for CLI integration. It statically analyzes ASTs for `main`/`run` functions or a `__hook__ = "type_string"` variable assignment, returning structured data (import path, file path, function, hook type) for discovered hooks.

## Operational Status/Completeness
Largely functional. Traverses directories, filters Python files (excluding `__init__.py` from direct candidacy), uses `ast.parse`, identifies `main`/`run` functions, and extracts `__hook__` string values. Handles empty files and parsing errors with warnings. Determines `hook_type` via tag, then filename conventions ("test", "batch"), defaulting to "tool".

## Implementation Gaps / Unfinished Next Steps
- **`module_import_path` Robustness:** Relies on CWD being project root for correct relative path generation. Could be improved by requiring an explicit project root argument.
- **Exclusion of `__init__.py`:** `__init__.py` files are not considered directly hookable. This might be intentional.
- **Configuration of Hook Signatures:** `main`, `run`, and `__hook__` are hardcoded; could be configurable.

## Connections & Dependencies
- **Direct Project Module Imports:** None.
- **External Library Dependencies:** `os`, `ast`, `typing` (standard Python).
- **Interaction:** Reads Python files in `search_paths`. Output consumed by a CLI framework.
- **Input/Output Files:**
    - **Inputs:** Python files in `search_paths`.
    - **Outputs:** Returns a list of hook dictionaries and a metadata dictionary. Prints warnings.

## Function and Class Example Usages
```python
from dev_tools.hook_utils import scan_for_hooks
modules, metadata = scan_for_hooks(["dev_tools", "simulation_engine/forecasting"])
```

## Hardcoding Issues
- Hook function names ("main", "run").
- Hook tag name (`__hook__`).
- Filename-based type detection strings ("test", "batch").
- Default hook type ("tool").

## Coupling Points
- Python AST structure.
- Project's convention for CLI entry points (`main`, `run`, `__hook__`).

## Existing Tests
- No dedicated test file listed. Testing would need mock files with various hook patterns and error conditions.

## Module Architecture and Flow
1.  `scan_for_hooks(search_paths)`:
    - Initializes `hookable_modules`, `metadata`.
    - For each `base_path` in `search_paths`:
        - `os.walk` to find `.py` files (excluding those starting with `__`).
        - For each file: read, parse with `ast` (skip if empty, handle errors).
        - Detect hooks: `main`/`run` functions, `__hook__ = "value"` assignments.
        - If hook found: determine `module_import_path` (relative to CWD), `hook_type` (tag > filename > default), `func_name`.
        - Append to `hookable_modules`, populate `metadata`.
    - Returns `hookable_modules`, `metadata`.

## Naming Conventions
- Follows PEP 8. `snake_case` for functions/variables. Type hints used. Descriptive names.