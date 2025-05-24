# Module Analysis: `dev_tools/analysis/phantom_function_scanner.py`

## 1. Overview

The [`phantom_function_scanner.py`](../../dev_tools/analysis/phantom_function_scanner.py:1) module is a utility designed to scan a Python project directory and identify "phantom functions." These are functions that are called within the codebase but do not have a corresponding definition within the scanned files. This tool helps in maintaining code health by flagging potential issues such as typos in function calls, missing imports, or references to deprecated/removed functions.

## 2. Key Functionalities

*   **Directory Traversal:** Recursively walks through the specified project directory to find all Python (`.py`) files. It ignores hidden directories (those starting with a dot).
*   **AST Parsing:** Uses Python's built-in `ast` (Abstract Syntax Tree) module to parse each Python file. This allows for a structured analysis of the code's syntax.
*   **Function Definition Collection:** Identifies and collects the names of all functions defined (using `def`) within the scanned files.
*   **Function Call Collection:** Identifies and collects the names of all functions called throughout the codebase. It attempts to extract the function name from simple name calls (e.g., `my_func()`) and attribute calls (e.g., `obj.method()`).
*   **Phantom Function Identification:** Compares the set of called functions against the set of defined functions. Any function name present in the "called" set but not in the "defined" set is flagged as a potential phantom function.
*   **Reporting:** Prints a summary report to the console, including:
    *   Total number of functions defined.
    *   Total number of functions called.
    *   A list of potential phantom functions, if any are found.
    *   A confirmation message if no phantom calls are detected locally.
*   **Error Handling:** Includes basic error handling to print a warning and skip files that fail to parse, preventing the entire scan from halting.

## 3. Module Structure

The module consists of a single class, [`FullPhantomScanner`](../../dev_tools/analysis/phantom_function_scanner.py:4), and a main execution block to run the scanner.

*   **`FullPhantomScanner(root_dir)` Class:**
    *   [`__init__(self, root_dir)`](../../dev_tools/analysis/phantom_function_scanner.py:5): Initializes the scanner with the root directory of the project to be scanned. It also initializes sets to store defined and called function names.
    *   [`scan(self)`](../../dev_tools/analysis/phantom_function_scanner.py:10): The main method that orchestrates the scanning process. It iterates through files and calls `_process_file()` for each Python file, then calls `_report()` to display the results.
    *   [`_process_file(self, filepath)`](../../dev_tools/analysis/phantom_function_scanner.py:19): Reads and parses a single Python file. It walks through the AST to find `ast.FunctionDef` nodes (for defined functions) and `ast.Call` nodes (for called functions).
    *   [`_extract_name(self, func)`](../../dev_tools/analysis/phantom_function_scanner.py:33): A helper method to extract the name of a called function from an AST node. It handles `ast.Name` (e.g., `foo()`) and `ast.Attribute` (e.g., `bar.foo()`, returning `foo`).
    *   [`_report(self)`](../../dev_tools/analysis/phantom_function_scanner.py:40): Compiles the findings and prints the report to the console.

*   **Main Execution Block (`if __name__ == "__main__":`)**
    *   Prompts the user to enter the path to the Pulse project root.
    *   Instantiates [`FullPhantomScanner`](../../dev_tools/analysis/phantom_function_scanner.py:4).
    *   Calls the [`scan()`](../../dev_tools/analysis/phantom_function_scanner.py:10) method to start the analysis.

## 4. Dependencies

*   **External Libraries:**
    *   [`os`](https://docs.python.org/3/library/os.html): Standard Python library for interacting with the operating system, used here for directory traversal ([`os.walk`](dev_tools/analysis/phantom_function_scanner.py:11)) and path manipulation ([`os.path.join`](dev_tools/analysis/phantom_function_scanner.py:16)).
    *   [`ast`](https://docs.python.org/3/library/ast.html): Standard Python library for working with Abstract Syntax Trees, used for parsing Python source code ([`ast.parse`](dev_tools/analysis/phantom_function_scanner.py:22), [`ast.walk`](dev_tools/analysis/phantom_function_scanner.py:23), [`ast.FunctionDef`](dev_tools/analysis/phantom_function_scanner.py:24), [`ast.Call`](dev_tools/analysis/phantom_function_scanner.py:26), [`ast.Name`](dev_tools/analysis/phantom_function_scanner.py:34), [`ast.Attribute`](dev_tools/analysis/phantom_function_scanner.py:36)).
*   **Internal Pulse Modules:**
    *   No direct dependencies on other Pulse-specific modules are apparent within this file. It operates as a standalone script.

## 5. Role in `dev_tools/analysis/`

Within the `dev_tools/analysis/` directory, the [`phantom_function_scanner.py`](../../dev_tools/analysis/phantom_function_scanner.py:1) serves as a static code analysis tool. Its primary role is to help developers identify and resolve issues related to undefined function calls, contributing to:
*   **Code Correctness:** Ensuring that all function calls refer to existing, defined functions.
*   **Code Maintenance:** Making it easier to refactor or remove code by highlighting potentially broken references.
*   **Reducing Runtime Errors:** Proactively catching `NameError` exceptions that might occur due to calls to non-existent functions.

## 6. Adherence to SPARC Principles

*   **Simplicity:** The module is relatively simple in its design and implementation. It uses standard Python libraries and follows a clear logic for scanning and reporting.
*   **Iterate:** While not directly an iterative development tool itself, it processes files and AST nodes iteratively.
*   **Focus:** The tool is highly focused on a single task: identifying phantom functions based on local definitions.
*   **Quality:** It contributes to overall code quality by providing a mechanism to detect potential defects. The code includes basic error handling for parsing.
*   **Collaboration:** Not directly applicable in its current form, but its output can be used by developers to collaborate on fixing identified issues.

## 7. Assessment

*   **Completeness:**
    *   The module effectively performs its core function of identifying called functions that are not defined *within the scanned files*.
    *   It currently does not account for imported functions or methods from external libraries or other modules within the project unless those modules are also scanned and define those functions. This means it might report false positives for correctly imported functions, as noted by its output "Potential Phantoms (no local definition or import seen)".
    *   It does not differentiate between standalone functions and class methods in its "defined functions" set, though [`_extract_name`](../../dev_tools/analysis/phantom_function_scanner.py:33) can get method names from calls.
*   **Quality:**
    *   The code is well-structured and readable.
    *   The use of `ast` for parsing is appropriate and robust for analyzing Python code structure.
    *   Error handling for file parsing is present, which is good practice.
    *   The reporting is clear and provides actionable information.
*   **Potential Enhancements:**
    *   **Import Resolution:** Extend the scanner to understand import statements (`import`, `from ... import`) to reduce false positives by recognizing functions/methods imported from other modules or standard/third-party libraries.
    *   **Scope Awareness:** More sophisticated scope analysis could improve accuracy.
    *   **Configuration:** Allow configuration for ignored directories or files.
    *   **Output Format:** Offer different output formats (e.g., JSON, CSV) for easier integration with other tools.

## 8. Usage

To use the scanner:
1.  Run the script from the command line:
    ```bash
    python dev_tools/analysis/phantom_function_scanner.py
    ```
2.  When prompted, enter the full path to the root directory of the Pulse project you wish to scan.

The script will then output its findings to the console.