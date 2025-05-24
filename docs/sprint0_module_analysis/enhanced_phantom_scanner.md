# SPARC Module Analysis: `enhanced_phantom_scanner.py`

**Module Path**: `enhanced_phantom_scanner.py`

## 1. Module Intent/Purpose
The primary role of `enhanced_phantom_scanner.py` is to serve as a utility for scanning a Python codebase to identify and categorize "phantom functions." Phantom functions are defined as functions or methods that are called within the code but are not explicitly defined within the scanned module or imported from other modules. The script uses Python's built-in `ast` (Abstract Syntax Tree) module to parse the Python source files and analyze their structure.

## 2. Operational Status/Completeness
The module is largely functional for its core purpose of detecting phantom functions based on direct calls.
- It successfully parses Python files and identifies function calls, definitions, and imports.
- The categorization of phantoms is currently a simplified placeholder based on prefix matching (e.g., "df.", "np.", "plt.") and requires significant enhancement for robust classification.
- It includes a basic command-line interface (CLI) for specifying the directory to scan.
- There are `TODO` comments indicating areas for future improvement, particularly around handling different import styles and call types.

## 3. Implementation Gaps / Unfinished Next Steps
- **Robust Phantom Categorization**: The current prefix-based categorization is very basic. A more sophisticated system is needed, potentially involving:
    - Heuristics for common library patterns (e.g., `pandas.DataFrame.method`).
    - Integration with a list of known standard library modules and common third-party packages.
    - User-configurable categorization rules.
- **Handling `from module import *`**: The script notes a `TODO` to better handle star imports, which currently might lead to misidentification of phantoms.
- **Attribute Call Resolution**: The script has a `TODO` for better handling of attribute calls (e.g., `object.method()`). Currently, it might not accurately determine if `method` is a phantom if `object`'s type is not easily inferred.
- **Flexible Output Options**: Currently, results are printed to the console. Adding options for outputting to JSON, CSV, or other structured formats would be beneficial for integration with other tools or for more detailed analysis.
- **Configuration**:
    - Directory exclusion patterns (beyond the hardcoded list) should be configurable.
    - Categorization prefixes/rules should be configurable, perhaps via a configuration file or CLI arguments.
- **Import Resolution Across Project**: For a more accurate scan within a larger project, it might need to understand the project's structure to resolve intra-project imports more effectively, though this module seems designed as a general utility.

## 4. Connections & Dependencies
### Direct Imports from Other Project Modules:
- As per the provided analysis context, this module does **not** appear to import any other custom modules from the Pulse project itself. It functions as a standalone utility.

### External Library Dependencies:
- `os`: For file system operations (walking directories, joining paths).
- `ast`: For parsing Python source code into an abstract syntax tree.
- `sys`: For accessing command-line arguments (`sys.argv`).
- `typing`: For type hints (`List`, `Dict`, `Set`, `Tuple`, `Any`).
- `collections.defaultdict`: For easily creating dictionaries with default values for lists.

### Interaction with Other Modules via Shared Data:
- **Input**: Reads `.py` files from the specified directory and its subdirectories.
- **Output**: Prints the phantom function report to the standard output (console). It does not write to files or databases.

## 5. Function and Class Example Usages
The script is primarily executed from the command line.
```bash
# Example CLI Usage (from the root directory of the project to be scanned):
python enhanced_phantom_scanner.py /path/to/your/python_project
```
If no path is provided, it defaults to the current directory.

Key internal functions:
- `scan_directory(directory_path)`: Orchestrates the scanning process.
- `analyze_file(file_path)`: Parses a single Python file using `ast` and extracts calls, definitions, and imports.
- `categorize_phantom(name, defined_functions, imported_names)`: Attempts to categorize a called name that isn't locally defined or imported.
- `report_phantoms(phantoms, called_from_locations)`: Formats and prints the report.

## 6. Hardcoding Issues
- **Excluded Directories**: `EXCLUDED_DIRS` list (`.git`, `__pycache__`, `venv`, `env`, `node_modules`, `.serverless`, `deploy`, `tests`, `test`) is hardcoded. While `tests` is a common exclusion for such tools, making this configurable would be better.
- **Categorization Prefixes**: `CATEGORIZATION_PREFIXES` (`df.`, `pd.`, `np.`, `plt.`, `go.`, `torch.`, `tf.`, `sklearn.`, `statsmodels.`) are hardcoded. This list is limited and not adaptable without code changes.
- **Report Display Limit**: The number of phantom occurrences displayed in the report (`max_display = 10`) is hardcoded in `report_phantoms`.
- **Input Prompt String**: The string "Please provide the directory path to scan: " is hardcoded for the CLI input.

## 7. Coupling Points
- **AST Structure**: The script is tightly coupled to the structure of Python's AST as provided by the `ast` module. Changes in Python's AST structure (though rare and typically backward-compatible for visitors) could potentially affect it.
- **File System**: Relies on `os.walk` for directory traversal.

## 8. Existing Tests
- No dedicated test file (e.g., `tests/test_enhanced_phantom_scanner.py` or similar) was found in the general project structure provided previously.
- The absence of unit tests for a utility like this, which involves parsing and complex logic, is a significant gap. Tests should cover:
    - Correct parsing of various Python constructs.
    - Accurate identification of function calls, definitions, and different import styles.
    - Correct identification of phantoms and non-phantoms.
    - Edge cases in categorization.
    - Handling of file I/O errors (e.g., unreadable files).

## 9. Module Architecture and Flow
1.  **Initialization**:
    *   Global sets for `defined_functions_global`, `imported_names_global`, `all_called_names_global`.
    *   `defaultdict` for `phantoms_global` (to store locations of phantom calls) and `called_from_locations_global`.
2.  **CLI Argument Parsing**:
    *   If a command-line argument (directory path) is provided, it's used. Otherwise, it prompts the user for a path.
3.  **Directory Scanning (`scan_directory`)**:
    *   Uses `os.walk` to traverse the specified directory.
    *   For each `.py` file found (and not in `EXCLUDED_DIRS`):
        *   Calls `analyze_file(file_path)`.
4.  **File Analysis (`analyze_file`)**:
    *   Reads the file content.
    *   Parses the content into an AST using `ast.parse()`.
    *   Iterates through the AST nodes:
        *   Identifies function and class definitions, adding them to local `defined_functions` and `defined_functions_global`.
        *   Identifies imports (`ast.Import`, `ast.ImportFrom`), adding them to local `imported_names` and `imported_names_global`.
        *   Identifies function calls (`ast.Call`):
            *   Extracts the called function/method name.
            *   Adds to `all_called_names_global`.
            *   If the name is not in local `defined_functions` or `imported_names`, it's considered a potential phantom.
            *   Calls `categorize_phantom` for these potential phantoms.
            *   Stores call locations.
5.  **Phantom Categorization (`categorize_phantom`)**:
    *   Takes a called name, local definitions, and local imports.
    *   If the name starts with a known prefix (e.g., "df."), it's categorized (e.g., "DataFrame Method").
    *   Otherwise, it's categorized as "Unknown Phantom" or "Likely Standard Library / Third-Party".
    *   Updates `phantoms_global` with the categorized phantom and its call location.
6.  **Reporting (`report_phantoms`)**:
    *   Prints a summary of total files scanned, functions defined, names imported, and unique names called.
    *   Iterates through `phantoms_global`, printing each phantom, its category, count, and up to `max_display` locations where it was called.

## 10. Naming Conventions
- **Functions and Variables**: Generally follow `snake_case` (e.g., `scan_directory`, `file_path`, `phantoms_global`).
- **Constants**: `EXCLUDED_DIRS`, `CATEGORIZATION_PREFIXES` use `UPPER_SNAKE_CASE`.
- Naming is clear and adheres well to PEP 8 standards. No significant AI assumption errors in naming were noted.

## 11. SPARC Compliance Summary
- **Specification**: The module has a clear, specific purpose: to identify phantom functions in a Python codebase.
- **Pseudocode**: The internal logic is relatively straightforward for a utility of this nature.
- **Architecture**: Modular in the sense that it's a self-contained script. File analysis and reporting are distinct logical blocks.
- **Refinement (Testability)**: Low. Lacks dedicated unit tests, which is crucial for a code analysis tool to ensure accuracy across various Python code structures and edge cases.
- **Refinement (Maintainability)**: Fair. The hardcoded exclusion lists and categorization prefixes reduce maintainability and adaptability. The core AST parsing logic is standard.
- **Refinement (No Hardcoding)**: Violations exist with `EXCLUDED_DIRS`, `CATEGORIZATION_PREFIXES`, and report display limits. These should ideally be configurable. No hardcoded secrets or environment variables critical to security were found.
- **Refinement (Security)**: Not directly applicable in terms of typical application security, as it's a developer tool. It reads source code files, so file system access is involved.
- **Completion (Composability)**: Designed as a standalone script. Outputting structured data (e.g., JSON) would improve its composability with other tools.
- **Completion (Documentation)**: Contains some inline comments and `TODO` notes. More comprehensive docstrings for functions, explaining parameters, return values, and behavior, would be beneficial.
- **Completion (Error Handling)**: Basic error handling for file reading (`try-except FileNotFoundError, UnicodeDecodeError`). Could be more robust (e.g., handling `ast.parse` errors for malformed Python files).