# Module Analysis: dev_tools/analysis/enhanced_phantom_scanner.py

## 1. Module Intent/Purpose

The [`dev_tools/analysis/enhanced_phantom_scanner.py`](../../../../dev_tools/analysis/enhanced_phantom_scanner.py:1) module provides an `EnhancedPhantomScanner` class designed to statically analyze a Python codebase to detect "phantom functions." These are functions that are called within the code but are not defined locally or explicitly imported. The scanner aims to categorize these phantom functions to help identify missing internal implementations, unimported standard library functions, or missing third-party library dependencies.

## 2. Key Functionalities

*   **Codebase Scanning:** Recursively walks a given root directory to find and process all Python (`.py`) files using the [`scan()`](../../../../dev_tools/analysis/enhanced_phantom_scanner.py:22) method.
*   **AST Parsing:** Uses the `ast` module to parse Python files into Abstract Syntax Trees for analysis within the [`_process_file()`](../../../../dev_tools/analysis/enhanced_phantom_scanner.py:36) method.
*   **Function Definition Tracking:** Identifies and stores all function definitions found within the codebase (in `self.defined_functions`).
*   **Function Call Tracking:** Identifies all function calls and records the name of the called function and the file/line number where the call occurs (in `self.called_functions` and `self.function_contexts`).
*   **Import Tracking:**
    *   Tracks `import module` statements (in `self.module_imports` and `self.module_aliases` for aliased imports).
    *   Tracks `from module import name` statements (in `self.imported_names` and `self.module_imports`). It explicitly skips wildcard imports (`from module import *`) as they cannot be statically tracked effectively.
*   **Phantom Function Identification:** The [`find_true_phantoms()`](../../../../dev_tools/analysis/enhanced_phantom_scanner.py:92) method identifies functions that are present in `self.called_functions` but not in `self.defined_functions` or `self.imported_names`.
*   **Phantom Function Categorization:** The [`categorize_phantom_functions()`](../../../../dev_tools/analysis/enhanced_phantom_scanner.py:112) method attempts to classify true phantom functions into 'standard_lib', 'ml_libraries', 'project_specific', or 'unknown' based on predefined prefixes. This categorization is a heuristic and might require tuning.
*   **Reporting:** The [`report()`](../../../../dev_tools/analysis/enhanced_phantom_scanner.py:175) method prints a summary of defined, called, and phantom functions, a breakdown by category, and detailed call contexts for project-specific and unknown phantoms. It also provides generic recommended actions.
*   **CLI Interface:** A `main()` function allows the scanner to be run from the command line, taking the project root directory as an argument or prompting for it.

## 3. Role within `dev_tools/analysis/`

This module serves as a static code analysis tool within the `dev_tools/analysis/` subdirectory. Its role is to help maintain code health by identifying potentially missing or incorrectly referenced functions. This can be particularly useful in large codebases to catch errors that might lead to `NameError` exceptions at runtime.

## 4. Dependencies

### External Libraries:
*   `os`: Used for file system operations like walking directories and joining paths.
*   `ast`: The core library used for parsing Python source code into an Abstract Syntax Tree.
*   `sys`: Used for accessing command-line arguments and for a simplified check against standard library modules (though this check is very basic in the current implementation).
*   `typing`: Used for type hints (`Dict`, `Set`, `List`, `Tuple`, `Optional`).
*   `collections.defaultdict`: Used for conveniently storing collections of items.

### Internal Pulse Modules:
*   None directly imported. This module is self-contained in its analysis logic but operates on the Pulse codebase (or any Python codebase).

## 5. SPARC Principles Adherence

*   **Module Intent/Purpose:**
    *   Clear and well-defined: The module aims to find and categorize phantom functions. The class and method names are descriptive.
*   **Operational Status/Completeness:**
    *   The module appears largely complete for its core static analysis task. It scans, processes, categorizes, and reports.
    *   The categorization logic is heuristic and explicitly noted as a simplification (lines 119-120). A more robust implementation would involve checking against actual installed modules or a comprehensive list of standard/third-party libraries.
*   **Implementation Gaps / Unfinished Next Steps:**
    *   **Star Imports:** Wildcard imports (`from module import *`) are not fully handled (line 63), which is a known limitation of static analysis for such constructs.
    *   **Dynamic Calls:** Cannot detect functions called dynamically (e.g., via `getattr()` or `eval()`). This is an inherent limitation of static analysis.
    *   **Method Calls on Objects:** The `_extract_name()` function (line 89) returns only the attribute name for method calls (e.g., `obj.method()` yields `method`). This means it doesn't distinguish between `obj1.method` and `obj2.method` if they are different methods with the same name. It also won't identify the module/class of `obj`.
    *   **Context for Imported Functions:** While it tracks imported names, the link between a called imported function and its original module for categorization purposes could be stronger.
    *   **Categorization Robustness:** The prefix-based categorization is basic and prone to false positives/negatives.
*   **Connections & Dependencies:**
    *   Relies on standard Python libraries. No internal Pulse module dependencies for its operation.
*   **Function and Class Example Usages:**
    *   The `EnhancedPhantomScanner` class is instantiated with a `root_dir`.
    *   Methods like `scan()` and `report()` are called on the instance.
    *   CLI usage: `python dev_tools/analysis/enhanced_phantom_scanner.py <path_to_project_root>`
*   **Hardcoding Issues:**
    *   The directory exclusion list (line 27-28) is hardcoded but reasonable for typical Python projects.
    *   The categorization prefixes (lines 121-135) are hardcoded and project-specific ones would need manual updates. This is acknowledged in comments.
    *   The `max_contexts` in `report()` defaults to 3, and the number of unknown functions to display is capped at 20. These could be configurable.
*   **Coupling Points:**
    *   Primarily coupled to the structure of Python code (as interpreted by the `ast` module).
*   **Existing Tests:**
    *   Test status is not determinable from the module's code.
*   **Module Architecture and Flow:**
    1.  Initialize `EnhancedPhantomScanner` with the root directory.
    2.  `scan()`: Walks the directory tree.
    3.  `_process_file()`: For each Python file:
        *   Reads and parses the file using `ast`.
        *   First pass (ast.walk): Collects all function definitions and import statements (populating `defined_functions`, `imported_names`, `module_imports`, `module_aliases`).
        *   Second pass (ast.walk): Collects all function calls using `_extract_name()` and their contexts (populating `called_functions`, `function_contexts`).
    4.  `find_true_phantoms()`: Compares called functions against defined and imported names to find phantoms.
    5.  `categorize_phantom_functions()`: Applies prefix-based rules to categorize phantoms.
    6.  `report()`: Prints a formatted summary of the findings.
    *   The flow is logical for a static analyzer. The two-pass approach in `_process_file` (first definitions/imports, then calls) is sensible.
*   **Naming Conventions:**
    *   Generally follows Python naming conventions (PEP 8). Class name `EnhancedPhantomScanner` is clear. Method names like `_process_file`, `find_true_phantoms` are descriptive. Variable names are also clear.

## 6. Overall Assessment

The [`dev_tools/analysis/enhanced_phantom_scanner.py`](../../../../dev_tools/analysis/enhanced_phantom_scanner.py:1) module is a useful and reasonably well-implemented static analysis tool for identifying undefined function calls. It provides good context (file and line numbers) for called functions. While its categorization is heuristic and has limitations (especially with dynamic code features and complex import scenarios), it serves as a good starting point for codebase cleanup and identifying potential `NameError` issues. The code is well-commented and structured.

Key areas for potential improvement include more robust categorization of phantom functions and potentially deeper analysis of attribute calls to better identify methods.

---

**Note for Main Report:**
The [`dev_tools/analysis/enhanced_phantom_scanner.py`](../../../../dev_tools/analysis/enhanced_phantom_scanner.py:1) module provides a static analyzer, `EnhancedPhantomScanner`, to detect and categorize functions called but not defined or imported within a Python codebase, using AST parsing and offering contextual reports.