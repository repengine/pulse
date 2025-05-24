# Module Analysis: `dev_tools/module_dependency_map.py`

## 1. Module Intent/Purpose

The primary role of [`dev_tools/module_dependency_map.py`](dev_tools/module_dependency_map.py:) is to analyze and visualize the import dependencies between Python modules within the Pulse project. It recursively scans a specified root directory for `.py` files, parses their import statements, and can output this dependency information in a human-readable format to the console and as a Graphviz DOT file for graphical representation.

## 2. Operational Status/Completeness

The module appears to be functionally complete for its stated purpose. It can:
- Find Python files.
- Parse `import from` statements.
- Exclude common directories like `venv`, `env`, and `__pycache__`.
- Print a summary of dependencies.
- Export the dependency graph to a `.dot` file.

There are no obvious placeholders or TODO comments in the code.

## 3. Implementation Gaps / Unfinished Next Steps

- **Handling of direct `import module` statements:** The current implementation in [`analyze_imports()`](dev_tools/module_dependency_map.py:34) specifically looks for `ast.ImportFrom` nodes (line 50). It does not appear to capture direct imports like `import os` or `import sys`. While these are standard library imports, if the goal is to map *all* dependencies, this could be an omission. For project-internal modules, `from . import X` or `from ..submodule import Y` are common, but direct imports of project modules (`import project_module`) might be missed if they are structured that way.
- **Granularity of Dependencies:** The script currently maps file-to-module dependencies. It doesn't resolve the specific functions or classes imported, nor does it differentiate between project-internal and external library imports in the output graph (though standard libraries are implicitly handled by not being part of the project's file structure).
- **Advanced Graphing Features:** The DOT export is basic. Enhancements could include:
    - Coloring nodes by directory or module type.
    - Sizing nodes by the number of dependents or dependencies.
    - Filtering to show only project-internal dependencies.
- **Error Handling in DOT Export:** The [`export_dot()`](dev_tools/module_dependency_map.py:56) function has a general `except Exception` (line 72) but could benefit from more specific error handling, e.g., for file I/O issues.
- **Configuration for Exclusions:** The `exclude_dirs` set is hardcoded in the [`analyze_imports()`](dev_tools/module_dependency_map.py:34) function's default arguments. Making this configurable via CLI arguments could be useful.

## 4. Connections & Dependencies

- **Direct imports from other project modules:** This module is designed to identify such dependencies but, being a developer tool, it aims to have minimal dependencies on other Pulse project modules itself to ensure it can run independently for analysis.
- **External library dependencies:**
    - `os`: For file system operations (walking directories, joining paths, getting basenames).
    - `ast`: For parsing Python source code into an Abstract Syntax Tree to find import statements.
    - `argparse`: For handling command-line arguments.
    - `typing`: For type hints (`Dict`, `List`, `Set`).
- **Interaction with other modules via shared data:**
    - **Input:** Reads `.py` files from the specified root directory.
    - **Output:**
        - Prints dependency summary to standard output.
        - Writes a `.dot` file (default: [`module_deps.dot`](module_deps.dot)) representing the dependency graph.
- **Input/output files:**
    - **Input:** Python source files (`.py`) within the project.
    - **Output:** A Graphviz DOT file (e.g., [`module_deps.dot`](module_deps.dot)).

## 5. Function and Class Example Usages

The module is primarily script-based. Key functions:

- **[`find_py_files(root: str)`](dev_tools/module_dependency_map.py:19):**
  ```python
  # Example:
  # python_files = find_py_files("/path/to/project")
  # print(f"Found {len(python_files)} Python files.")
  ```
  This function walks a directory tree and returns a list of all `.py` file paths.

- **[`analyze_imports(root: str, exclude_dirs: Set[str])`](dev_tools/module_dependency_map.py:34):**
  ```python
  # Example:
  # dependencies = analyze_imports(root=".", exclude_dirs={"venv", "__pycache__"})
  # for module, imports in dependencies.items():
  #     print(f"{module} imports: {imports}")
  ```
  Parses all Python files found under `root` (excluding specified directories) to extract `from ... import ...` statements. Returns a dictionary mapping file paths to a list of imported module names.

- **[`export_dot(deps: Dict[str, List[str]], dot_path: str)`](dev_tools/module_dependency_map.py:56):**
  ```python
  # Example (assuming 'dependencies' is populated by analyze_imports):
  # export_dot(dependencies, "project_dependencies.dot")
  ```
  Takes the dependency dictionary and writes it to a file in Graphviz DOT format.

- **[`print_summary(deps: Dict[str, List[str]])`](dev_tools/module_dependency_map.py:75):**
  ```python
  # Example (assuming 'dependencies' is populated):
  # print_summary(dependencies)
  ```
  Prints the total number of modules analyzed and the total number of dependency edges found.

**CLI Usage:**
```bash
python dev_tools/module_dependency_map.py --root /path/to/pulse_project --dot output/dependencies.dot
```
This command analyzes the project at `/path/to/pulse_project` and saves the dependency graph to `output/dependencies.dot`.

## 6. Hardcoding Issues

- **Default Root Directory:** In the `if __name__ == "__main__":` block, `args.root` defaults to `"c:/Users/natew/Pulse"` (line 87). While configurable via CLI, this is a user-specific absolute path. A more generic default like `"."` (current directory) might be preferable for wider usability, or it could attempt to detect the project root more dynamically.
- **Default DOT Output File:** `args.dot` defaults to `"module_deps.dot"` (line 88), which is reasonable as it's also configurable.
- **Excluded Directories:** The set `{"venv", "env", "__pycache__"}` is hardcoded as a default parameter in [`analyze_imports()`](dev_tools/module_dependency_map.py:34). This is a common set but making it extendable or configurable via CLI could be an improvement.

## 7. Coupling Points

- The module is largely self-contained. Its primary "coupling" is with the file system (reading `.py` files) and the structure of Python's `import` statements (as interpreted by the `ast` module).
- The output `.dot` file creates an implicit coupling with tools that can process this format, like Graphviz.

## 8. Existing Tests

No specific test files (e.g., `tests/dev_tools/test_module_dependency_map.py`) were found. The module lacks automated tests.

## 9. Module Architecture and Flow

1.  **Initialization:** Parses command-line arguments (`--root`, `--dot`).
2.  **File Discovery ([`find_py_files()`](dev_tools/module_dependency_map.py:19)):** Recursively walks the specified `root` directory to find all `.py` files.
3.  **Import Analysis ([`analyze_imports()`](dev_tools/module_dependency_map.py:34)):**
    *   Iterates through each found `.py` file.
    *   Skips files in excluded directories.
    *   Reads and parses the file content using `ast.parse()`.
    *   Walks the AST to find `ast.ImportFrom` nodes and extracts the `module` attribute (the name of the module being imported from).
    *   Stores dependencies in a dictionary: `{filepath: [imported_module_name, ...]}`.
    *   Includes basic error handling for parsing failures.
4.  **Console Output (main block):** Iterates through the dependency dictionary and prints each module and its unique imports.
5.  **Summary Output ([`print_summary()`](dev_tools/module_dependency_map.py:75)):** Calculates and prints the total number of modules analyzed and total dependencies found.
6.  **DOT Export ([`export_dot()`](dev_tools/module_dependency_map.py:56)):**
    *   Opens the specified DOT output file.
    *   Writes the DOT graph header.
    *   Iterates through the dependency dictionary, writing each dependency as an edge in the DOT format (e.g., `"module_a.py" -> "module_b"`). It uses `os.path.basename(mod)` for the source node name.
    *   Writes the DOT graph footer.
    *   Includes basic error handling for file writing.

## 10. Naming Conventions

- **Functions:** Use `snake_case` (e.g., [`find_py_files()`](dev_tools/module_dependency_map.py:19), [`analyze_imports()`](dev_tools/module_dependency_map.py:34)), which is consistent with PEP 8.
- **Variables:** Generally use `snake_case` (e.g., `py_files`, `dirpath`, `fpath`, `exclude_dirs`, `dot_path`). Some single-letter variables are used in loops (`f`, `n`, `e`), which is acceptable for small scopes.
- **Type Hints:** Uses `typing` module for `Dict`, `List`, `Set`.
- **Clarity:** Names are generally descriptive (e.g., `deps` for dependencies, `tree` for AST).
- **Consistency:** Naming is consistent throughout the module.
- No obvious AI assumption errors or major deviations from PEP 8 were noted. The use of `mod` as a variable for module path and `imp` for imported module name is clear in context.