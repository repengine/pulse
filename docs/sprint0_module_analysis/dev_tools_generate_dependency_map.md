# Module Analysis: `dev_tools/generate_dependency_map.py`

## 1. Module Intent/Purpose

The [`dev_tools/generate_dependency_map.py`](dev_tools/generate_dependency_map.py:1) script is a utility designed to analyze the Pulse project's codebase and generate a map of internal module dependencies. It scans Python files, identifies import statements, and outputs a plain edge-list representing these dependencies to a Markdown file. This helps developers visualize and understand the relationships between different modules in the project.

## 2. Key Functionalities

*   **Project Root Detection:**
    *   Determines the project's root directory ([`ROOT`](dev_tools/generate_dependency_map.py:10)) based on the script's location.
*   **Module Discovery:**
    *   Walks through the project directory using [`os.walk()`](dev_tools/generate_dependency_map.py:15).
    *   Ignores specified directories ([`IGNORE_DIRS`](dev_tools/generate_dependency_map.py:11), currently `{'tests'}`) and hidden directories (starting with '.').
    *   Identifies all `.py` files.
    *   Constructs a module name from the file path (e.g., `folder/subfolder/file.py` becomes `folder.subfolder.file`).
    *   Handles `__init__.py` files by assigning the module name of their parent directory.
    *   Stores a mapping ([`MODULE_MAP`](dev_tools/generate_dependency_map.py:12)) from module name to its relative file path.
*   **Import Parsing:**
    *   Iterates through each discovered module.
    *   Reads the content of each Python file.
    *   Parses the file content into an Abstract Syntax Tree (AST) using [`ast.parse()`](dev_tools/generate_dependency_map.py:43).
    *   Skips files with `SyntaxError`.
    *   Walks through the AST to find `ast.Import` and `ast.ImportFrom` nodes.
*   **Dependency Identification:**
    *   For `ast.Import` nodes (e.g., `import module.submodule`):
        *   Extracts the imported name.
        *   Checks if the imported name (or its prefix) matches any discovered internal module names (sorted by length to match longest first, ensuring correct matching for submodules).
        *   If a match is found, an edge (source_file_path, destination_file_path) is recorded.
    *   For `ast.ImportFrom` nodes (e.g., `from . import sibling` or `from package import item`):
        *   Extracts the module name.
        *   Handles relative imports (e.g., `from .foo import bar`, `from ..foo import bar`) by resolving the absolute module name based on the current module's path and the import level.
        *   Checks if the resolved imported module name matches any discovered internal module names.
        *   If a match is found, an edge is recorded.
*   **Output Generation:**
    *   Deduplicates and sorts the collected dependency edges.
    *   Writes the edges to a file named [`MODULE_DEPENDENCY_MAP.md`](MODULE_DEPENDENCY_MAP.md) in the project root.
    *   The format is `source_file_path -> destination_file_path` per line.
    *   Prints a confirmation message with the number of edges written.

## 3. Role within `dev_tools/`

This script is a developer tool for static code analysis. It provides a simple way to generate a textual representation of the project's internal dependency structure, which can be useful for:
*   Understanding module coupling.
*   Identifying potential circular dependencies (though this script only lists edges, further processing would be needed).
*   Visualizing project architecture (the output can be used as input for graph visualization tools).
*   Refactoring efforts.

## 4. Dependencies

### Internal Pulse Modules:
*   None. This script analyzes other Pulse modules but does not import or run them.

### External Libraries:
*   `ast`: For parsing Python source code into an Abstract Syntax Tree (standard Python library).
*   `os`: For file system navigation and path manipulation (standard Python library).

## 5. SPARC Principles Adherence

*   **Module Intent/Purpose:**
    *   Clearly stated in the docstring: "Generate a plain edge-list of internal module dependencies".
*   **Operational Status/Completeness:**
    *   Appears fully operational for its defined scope. It discovers modules, parses imports (including relative ones), and generates the specified output file.
*   **Implementation Gaps / Unfinished Next Steps:**
    *   The script currently ignores `__init__.py` files in a way that might be slightly ambiguous (comment: `# ignore __init__.py? But treat.`). The logic assigns the parent directory's module name. This is a common approach but could be clarified.
    *   It doesn't explicitly differentiate between direct and transitive dependencies in its output, only direct import relationships.
    *   The output format is a simple edge list; more advanced formats (e.g., DOT language for Graphviz) could be an extension.
*   **Connections & Dependencies:**
    *   The script's primary "dependency" is the structure of the Python codebase it analyzes.
*   **Function and Class Example Usages:**
    *   The script is executed directly: `python dev_tools/generate_dependency_map.py`
*   **Hardcoding Issues:**
    *   [`IGNORE_DIRS`](dev_tools/generate_dependency_map.py:11) is hardcoded to `{'tests'}`. This is reasonable for its purpose but could be made configurable if needed.
    *   The output filename [`MODULE_DEPENDENCY_MAP.md`](MODULE_DEPENDENCY_MAP.md) is hardcoded.
*   **Coupling Points:**
    *   Coupled to the Python language's import syntax (as interpreted by the `ast` module).
*   **Existing Tests:**
    *   Test coverage is not determinable from this file. Tests would involve running the script on a small, controlled set of Python files with known import structures and verifying the content of the output map.
*   **Module Architecture and Flow:**
    *   Sequential script:
        1.  Define constants and initial data structures.
        2.  Discover all Python modules in the project.
        3.  Parse each module to find imports and build an edge list.
        4.  Deduplicate and sort edges.
        5.  Write the edge list to the output file.
    *   The architecture is straightforward and suitable for this type of analysis tool.
*   **Naming Conventions:**
    *   Follows standard Python naming conventions (snake_case for variables, UPPER_CASE for constants).

## 6. Overall Assessment

*   **Completeness:** The module is complete for its primary goal of generating a basic dependency edge list.
*   **Quality:** The code is well-structured and uses appropriate Python features (like `ast` for parsing and `os.walk` for file discovery). The logic for handling module naming and relative imports is reasonably robust. It's a good quality utility script.

## 7. Summary Note for Main Report

The [`dev_tools/generate_dependency_map.py`](dev_tools/generate_dependency_map.py:1) script analyzes the project's Python files to produce an internal module dependency map ([`MODULE_DEPENDENCY_MAP.md`](MODULE_DEPENDENCY_MAP.md)), aiding in understanding code structure.