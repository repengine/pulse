# Design Document: Duplicate Symbol Scanner (`find_duplicate_symbols.py`)

## 1. Overview
   - **Purpose:** To identify duplicate top-level symbol definitions across `.py` files within a specified Python project. A symbol is considered a duplicate if the same name is defined at the top level of more than one module.
   - **Method:** Static analysis using Python's built-in `ast` (Abstract Syntax Tree) module.
   - **Output:** A JSON file (`dup_symbol_report.json` by default) listing each duplicate symbol and the relative paths of the modules where it is defined.

## 2. Script Structure (`dev_tools/diagnostics/find_duplicate_symbols.py`)

### 2.1. Imports
```python
import ast
import argparse
import json
import os
import logging
from pathlib import Path
from collections import defaultdict
import fnmatch # For pattern matching in exclusions
from typing import Dict, List, Set, Tuple, Optional, Any
```

### 2.2. Core Functions

   - **`is_excluded(path: Path, project_root: Path, exclude_dirs: List[str], exclude_files: List[str]) -> bool`**
     - **Purpose:** Check if a given file path should be excluded from scanning based on directory and file exclusion patterns.
     - **Logic:**
       - Convert `path` to an absolute path for consistent comparison: `abs_path = path.resolve()`.
       - `project_root_abs = project_root.resolve()`.
       - **Directory Exclusion:** Iterate through `exclude_dirs`. For each `pattern`:
         - Check if any parent directory name of `abs_path` (up to `project_root_abs`) matches the `pattern` using `fnmatch.fnmatch(parent_dir_name, pattern)`.
         - Example: If `exclude_dirs = ["tests*"]` and `path` is `project_root/src/tests_feature/file.py`, it should be excluded.
       - **File Exclusion:** Iterate through `exclude_files`. For each `pattern`:
         - Check if `path.name` matches the `pattern` using `fnmatch.fnmatch(path.name, pattern)`.
     - **Returns:** `True` if the path should be excluded, `False` otherwise.

   - **`find_python_files(project_root: Path, exclude_dirs: List[str], exclude_files: List[str]) -> List[Path]`**
     - **Purpose:** Recursively find all `.py` files in the `project_root` directory, respecting exclusions.
     - **Logic:**
       - Use `project_root.rglob('*.py')` to find all Python files.
       - For each found file, call `is_excluded(file_path, project_root, exclude_dirs, exclude_files)` to filter.
     - **Returns:** A list of `Path` objects for Python files to be scanned.

   - **`extract_symbol_name_from_target(target: ast.expr) -> List[str]`**
     - **Purpose:** Extract symbol name(s) from an assignment target (e.g., `x` in `x=1`, or `x, y` in `x,y = 1,2`).
     - **Logic:**
       - If `target` is `ast.Name`, return `[target.id]`.
       - If `target` is `ast.Tuple` or `ast.List` (for unpacking assignment), recursively call `extract_symbol_name_from_target` on each element in `target.elts` and extend the list of names.
       - Otherwise (e.g., `ast.Attribute`, `ast.Subscript`), return an empty list as these are not considered top-level definitions in this context.
     - **Returns:** A list of extracted symbol names.

   - **`extract_top_level_symbols_from_ast(tree: ast.AST, file_path_relative: Path) -> Dict[str, str]`**
     - **Purpose:** Parse an AST to find top-level symbol definitions within a single file.
     - **Logic:**
       - Initialize `symbols: Dict[str, str] = {}`. The value will be the string representation of `file_path_relative`.
       - Iterate through `node` in `tree.body` (direct children of `ast.Module`).
       - **`ast.FunctionDef` / `ast.AsyncFunctionDef`:** `symbols[node.name] = str(file_path_relative)`
       - **`ast.ClassDef`:** `symbols[node.name] = str(file_path_relative)`
       - **`ast.Assign`:**
         - Iterate `target_node` in `node.targets`.
         - Call `names = extract_symbol_name_from_target(target_node)`.
         - For `name` in `names`: `symbols[name] = str(file_path_relative)`.
       - **`ast.AnnAssign`:** (Annotated Assignment)
         - If `node.target` is `ast.Name`: `symbols[node.target.id] = str(file_path_relative)`.
         - (Note: `AnnAssign` does not support tuple unpacking for its target in the same way `Assign` does for simple names at the top level).
       - **`ast.ImportFrom`:** (Handling aliased imports as definitions)
         - Iterate `alias_node` in `node.names` (list of `ast.alias`).
         - If `alias_node.asname` is not `None` (e.g., `from module import name as alias_name`):
           - `symbols[alias_node.asname] = str(file_path_relative)` (The symbol `alias_name` is considered defined in the current module).
         - Non-aliased imports (`from module import name`) are not considered definitions *by* this module for this script's purpose.
     - **Returns:** A dictionary mapping symbol names defined in this file to their relative module path string.

   - **`main()`**
     - **Purpose:** Main execution flow of the script.
     - **Logic:**
       1.  Setup logging.
       2.  Call `argparse_setup()` to parse Command Line Interface (CLI) arguments.
       3.  Initialize `all_symbols: Dict[str, List[str]] = defaultdict(list)`.
       4.  Call `find_python_files(args.project_root, args.exclude_dirs, args.exclude_files)` to get the list of Python files.
       5.  Log the number of Python files found.
       6.  For each `file_path` in the list of files:
           - Calculate `file_path_relative = file_path.relative_to(args.project_root)`.
           - Try to read file content: `source_code = file_path.read_text(encoding='utf-8')`.
             - Handle `IOError` or `UnicodeDecodeError`: log a warning and continue to the next file.
           - Try to parse with `ast.parse(source_code, filename=str(file_path))`.
             - Handle `SyntaxError`: log a warning (e.g., `logging.warning(f"Could not parse {file_path_relative}: {e}")`) and continue.
           - Call `current_file_symbols = extract_top_level_symbols_from_ast(tree, file_path_relative)`.
           - For each `symbol_name, defining_module_str` in `current_file_symbols.items()`:
             - `all_symbols[symbol_name].append(defining_module_str)`
       7.  Filter for duplicates: `duplicates = {sym: paths for sym, paths in all_symbols.items() if len(paths) > 1}`.
       8.  Sort paths for consistent output: `sorted_duplicates = {sym: sorted(list(set(paths))) for sym, paths in duplicates.items()}`.
       9.  Write `sorted_duplicates` to `args.output_file` as JSON with indentation for readability.
       10. Log a summary (e.g., number of files scanned, number of duplicate symbols found, path to report).

### 2.3. CLI Argument Parsing

   - Function: **`argparse_setup() -> argparse.Namespace`**
   - **Arguments:**
     - `--project-root` (Type: `str`, Default: `.`, Help: "Root directory of the project to scan. Paths in the report will be relative to this root.")
     - `--output-file` (Type: `str`, Default: `dup_symbol_report.json`, Help: "Path to save the JSON report.")
     - `--exclude-dirs` (Type: `str`, Nargs: `*`, Default: `['.venv', '.git', '__pycache__', 'tests', 'test', 'docs', 'build*', 'dist*']`, Help: "Directory names/patterns to exclude. Applied to any part of the path. E.g., 'tests' or 'build*'.")
     - `--exclude-files` (Type: `str`, Nargs: `*`, Default: `['setup.py', '*_pb2.py', '__init__.py']`, Help: "File names/patterns to exclude. E.g., 'conf.py' or '*_generated.py'.")
     - `--log-level` (Type: `str`, Default: `INFO`, Choices: `['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']`, Help: "Set the logging level.")
   - **Logic:**
     - Create `argparse.ArgumentParser`.
     - Add arguments as defined above.
     - Parse arguments: `args = parser.parse_args()`.
     - Convert `args.project_root` to `Path(args.project_root).resolve()`.
     - Convert `args.output_file` to `Path(args.output_file)`. Ensure its parent directory exists.
   - **Returns:** Parsed arguments namespace.

## 3. AST Node Handling Details (Recap)

### 3.1. `ast.FunctionDef` / `ast.AsyncFunctionDef`
   - Symbol name: `node.name`

### 3.2. `ast.ClassDef`
   - Symbol name: `node.name`

### 3.3. `ast.Assign`
   - Targets: `node.targets`. Use `extract_symbol_name_from_target` to handle `ast.Name`, `ast.Tuple`, `ast.List`.

### 3.4. `ast.AnnAssign`
   - Target: `node.target`. If `ast.Name`, symbol is `node.target.id`.

### 3.5. `ast.ImportFrom`
   - Aliases: `node.names`. If `alias.asname` is not `None`, symbol is `alias.asname`.

### 3.6. Top-Level Scope
   - Only direct children of `ast.Module` (nodes in `tree.body`) are processed.

## 4. Configuration and Exclusions (Recap)

### 4.1. CLI Arguments
   - As defined in section 2.3.

### 4.2. Default Exclusions
   - Directories: `.venv`, `.git`, `__pycache__`, `tests`, `test`, `docs`, `build*`, `dist*`.
   - Files: `setup.py`, `*_pb2.py`, `__init__.py` (often empty or used for namespace, less likely for conflicting primary definitions).
   - These are defaults and can be overridden via CLI.

### 4.3. Exclusion Logic (`is_excluded` function)
   - Uses `fnmatch.fnmatch()` for pattern matching against directory names and file names.
   - Directory exclusion checks each component of a file's path against `exclude_dirs` patterns.

## 5. Error Handling (Recap)

### 5.1. File Read Errors
   - `try-except (IOError, UnicodeDecodeError)` around `file_path.read_text()`. Log warning, skip file.

### 5.2. AST Parsing Errors
   - `try-except SyntaxError` around `ast.parse()`. Log warning (with filename and error), skip file.

## 6. Data Structures (Recap)

### 6.1. Intermediate (per file): `Dict[str, str]`
   - `{symbol_name: relative_file_path_str}`

### 6.2. Aggregated (all files): `defaultdict(list)` -> `Dict[str, List[str]]`
   - `{symbol_name: [relative_path1_str, relative_path2_str, ...]}`

### 6.3. Final JSON Output: `Dict[str, List[str]]`
   - Filtered for symbols with `len(paths) > 1`. Paths sorted.

## 7. Output Format (`dup_symbol_report.json`)
   - JSON object. Keys are duplicate symbol names. Values are sorted lists of unique relative file paths.
   - Example:
     ```json
     {
       "common_util": [
         "lib/commonutils.py",
         "utils/helpers.py"
       ],
       "DataObject": [
         "models/data.py",
         "schemas/data_objects.py"
       ]
     }
     ```

## 8. Logging
   - Use the `logging` module, configured by `--log-level`.
   - `INFO`: Script start/end, number of files scanned, number of duplicates, report path.
   - `WARNING`: Files skipped (read/parse errors), non-critical issues.
   - `DEBUG`: Detailed processing steps, symbol extraction details (if needed).

## 9. Performance Considerations
   - Target: Script execution ≤ 15s for typical projects.
   - `ast.parse` is generally efficient. File I/O and directory traversal (`rglob`) are primary factors.
   - `pathlib` and `fnmatch` are standard and performant enough for this task.

## 10. Testing Strategy (Guidance for Code Mode)
   - **Unit Tests:**
     - `is_excluded()`: Test with various paths, project roots, and exclusion patterns (dirs and files, exact matches, glob patterns).
     - `extract_symbol_name_from_target()`: Test with `ast.Name`, `ast.Tuple` (nested and simple), `ast.List`, and other `ast.expr` types.
     - `extract_top_level_symbols_from_ast()`:
       - Provide diverse AST snippets as input.
       - Test `FunctionDef`, `AsyncFunctionDef`, `ClassDef`.
       - Test `Assign` with single targets, tuple/list unpacking.
       - Test `AnnAssign` with `ast.Name` targets.
       - Test `ImportFrom` with and without `asname`.
       - Test that only top-level definitions are extracted.
   - **Integration Tests:**
     - `find_python_files()`: Use a mock directory structure with various `.py` files and subdirectories. Test with different exclusion settings.
   - **End-to-End Tests (for `main()`):**
     - Create a small mock Python project (a few files in a temporary directory).
       - Include intentional duplicate symbols across files.
       - Include files/directories that should be excluded.
       - Include a file with syntax errors.
     - Run the `find_duplicate_symbols.py` script against this mock project.
     - Verify the content of the generated JSON report against expected duplicates and paths.
     - Test different CLI arguments: `--project-root`, `--output-file`, `--exclude-dirs`, `--exclude-files`, `--log-level`.
     - Verify that warnings are logged for unparseable files.
     - Check script exit codes (0 for success).