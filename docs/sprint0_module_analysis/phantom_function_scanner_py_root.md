# Analysis of `phantom_function_scanner.py` (Root Level)

## Module Path

[`phantom_function_scanner.py`](phantom_function_scanner.py:1)

## Purpose & Functionality

The `phantom_function_scanner.py` module is a utility script designed to perform a static analysis of Python files within a specified project directory. Its primary purpose is to identify "phantom functions" – functions that are called within the codebase but do not have a corresponding definition found within the scanned files.

Key functionalities include:
- Recursively scanning a directory for `.py` files.
- Parsing Python files using the `ast` (Abstract Syntax Tree) module.
- Identifying all function definitions and function calls.
- Reporting a list of function names that are called but not defined locally.

It serves as a basic tool to help developers find potentially broken code, such as typos in function names or calls to functions that were removed or never implemented.

## Key Components / Classes / Functions

- **Class: `FullPhantomScanner`**
    - **`__init__(self, root_dir)`**: Initializes the scanner with the root directory of the project to be analyzed. It sets up two sets: `defined_functions` and `called_functions`.
    - **`scan(self)`**: The main method that orchestrates the scanning process. It uses [`os.walk()`](phantom_function_scanner.py:11) to traverse the directory tree, ignoring hidden directories. For each Python file found, it calls `_process_file()`. Finally, it calls `_report()` to display the findings.
    - **`_process_file(self, filepath)`**: Reads the content of a given Python file, parses it into an AST using [`ast.parse()`](phantom_function_scanner.py:22). It then walks the AST:
        - If an [`ast.FunctionDef`](phantom_function_scanner.py:24) node is found, its name is added to `self.defined_functions`.
        - If an [`ast.Call`](phantom_function_scanner.py:26) node is found, the function's name is extracted using `_extract_name()` and added to `self.called_functions`.
        - Includes basic error handling for file parsing issues.
    - **`_extract_name(self, func)`**: A helper method to retrieve the name of a function being called. It handles direct name calls (e.g., `my_func()`) via [`ast.Name`](phantom_function_scanner.py:34) and attribute calls (e.g., `my_obj.method()`) via [`ast.Attribute`](phantom_function_scanner.py:36), returning the attribute part (e.g., `method`).
    - **`_report(self)`**: Calculates the set difference between `called_functions` and `defined_functions` to identify potential phantoms. It then prints a summary, including the total number of defined and called functions, and lists any phantom functions found.

- **Script Execution (`if __name__ == "__main__":`)**:
    - Prompts the user to input the path to the Pulse project root directory.
    - Instantiates `FullPhantomScanner` with the provided path.
    - Calls the `scan()` method to initiate the analysis.

## Dependencies

- **External Libraries:**
    - [`os`](phantom_function_scanner.py:1): Used for directory traversal ([`os.walk()`](phantom_function_scanner.py:11)) and path joining ([`os.path.join()`](phantom_function_scanner.py:16)).
    - [`ast`](phantom_function_scanner.py:2): The Abstract Syntax Tree module, fundamental for parsing Python source code and inspecting its structure (e.g., [`ast.parse()`](phantom_function_scanner.py:22), [`ast.walk()`](phantom_function_scanner.py:23), [`ast.FunctionDef`](phantom_function_scanner.py:24), [`ast.Call`](phantom_function_scanner.py:26)).
- **Internal Pulse Modules:**
    - None. The script is self-contained and operates on the file system based on the provided root directory.

## SPARC Analysis

-   **Specification:**
    *   **Clarity of Purpose:** The module's purpose is reasonably clear from its name and output: to find functions that are called but not defined within the scanned project files.
    *   **Well-Defined Requirements:** The core requirement is met. However, its definition of "phantom" is limited to locally defined functions. It does not resolve imports, so functions from standard libraries, third-party packages, or even other project modules (if not directly in the scan path and defined there) will be flagged. The report message "no local definition or import seen" is slightly misleading as it doesn't actively check imports.

-   **Architecture & Modularity:**
    *   **Structure:** The module is well-structured, with logic encapsulated within the `FullPhantomScanner` class.
    *   **Responsibilities:** Methods within the class have clear, distinct responsibilities (initialization, scanning, file processing, name extraction, reporting).

-   **Refinement - Testability:**
    *   **Existing Tests:** No tests are included within this module.
    *   **Design for Testability:** The class-based structure lends itself to testability. One could instantiate it with a controlled directory structure for testing. However, its direct use of `print()` for output and `input()` for path configuration in the `__main__` block makes automated testing less straightforward without patching/mocking. Core logic in `_process_file` could be tested by feeding it AST snippets.

-   **Refinement - Maintainability:**
    *   **Clarity & Readability:** The code is generally clear, readable, and follows common Python conventions. Variable and method names are descriptive.
    *   **Documentation:** Lacks docstrings for the class and its methods. Inline comments are minimal but explain key decisions (e.g., ignoring hidden directories).

-   **Refinement - Security:**
    *   **Input Handling:** The script takes a file path via `input()`. While intended for developer use, un-sanitized path input can be a risk in broader contexts, though low here.
    *   **File Operations:** It reads files from the disk. Maliciously crafted (though valid Python) files are unlikely to cause issues with `ast.parse`, but it's a theoretical consideration for any file parser.
    *   **Overall:** No significant, obvious security vulnerabilities for its intended use case as a local development tool.

-   **Refinement - No Hardcoding:**
    *   **Paths:** The root directory for scanning is configurable via `__init__` or user input, not hardcoded in the core logic.
    *   **Parameters:** The `.py` file extension and the logic to ignore dot-prefixed directories are hardcoded, which is generally acceptable for this type of utility.
    *   **Exclusion Lists:** No explicit, configurable exclusion lists for files, directories, or known functions.

## Identified Gaps & Areas for Improvement

1.  **Import Resolution:** The most significant gap. The scanner does not attempt to resolve imports. This means functions imported from other modules (standard library, third-party, or other project files not directly defining them) will be incorrectly flagged as "phantoms."
2.  **Built-in and Standard Library Functions:** Calls to Python's built-in functions (e.g., `print()`, `len()`) or functions from the standard library will be reported as phantoms, generating significant noise.
3.  **Contextual Awareness:** The scanner has a flat view of functions; it doesn't differentiate between top-level functions, methods within classes, or nested functions if names collide.
4.  **Documentation:** Missing docstrings for the `FullPhantomScanner` class and its methods, reducing maintainability and understandability.
5.  **Configuration:** Lack of options to:
    *   Exclude specific directories or files.
    *   Provide a list of known external/built-in functions to ignore.
6.  **Output Mechanism:** Directing output to `print()` makes it harder to integrate the scanner into automated workflows or to process its results programmatically. Returning a data structure or using a logger would be more flexible.
7.  **Error Handling in `_report`:** If `self.defined_functions` or `self.called_functions` are not populated (e.g., empty directory), the report might be less informative but won't crash.
8.  **Granularity of `_extract_name`:** While it correctly extracts method names from attributes, it doesn't capture the object/class part, which might be useful for more advanced analysis (though perhaps beyond its current scope).

## Overall Assessment & Next Steps

**Overall Assessment:**
[`phantom_function_scanner.py`](phantom_function_scanner.py:1) is a simple, functional utility for identifying function calls that lack local definitions within a Python project. Its use of `ast` for parsing is appropriate. However, its utility is limited by its inability to resolve imports or recognize built-in/standard library functions, leading to potentially numerous false positives in a typical project. The code is readable but lacks formal documentation (docstrings).

**Recommended Next Steps:**
1.  **Address Import Blindness:** Implement a basic mechanism to recognize imported names or, at minimum, significantly clarify this limitation in its output and documentation.
2.  **Filter Known Functions:** Introduce a configurable or default list of Python built-in functions and common standard library functions to exclude from the "phantom" report.
3.  **Add Docstrings:** Thoroughly document the class and its methods to improve maintainability.
4.  **Improve Output:** Consider returning the list of phantoms as a data structure rather than just printing, to allow for easier programmatic use.
5.  **Enhance Configuration:** Allow users to specify directories/files to ignore or a custom list of known external functions.
6.  **Develop Tests:** Create a suite of unit tests to ensure reliability, especially if enhancements are made.