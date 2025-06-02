# Module Analysis: `scripts/discover_available_variables.py`

**Version:** 1.0
**Date:** 2025-05-18

## 1. Module Intent/Purpose

The primary role of the [`discover_available_variables.py`](../../../scripts/discover_available_variables.py) script is to automatically discover and compile a comprehensive list of variables that can be ingested into the Pulse system. It achieves this by scanning the plugins located within the [`iris/iris_plugins_variable_ingestion/`](../../../iris/iris_plugins_variable_ingestion/) directory, querying each plugin for the variables it provides, and then generating a Markdown report ([`data/historical_timeline/available_variables.md`](../../../data/historical_timeline/available_variables.md)) detailing these findings.

## 2. Operational Status/Completeness

The module appears to be largely functional and complete for its intended purpose. It includes:
*   Dynamic plugin loading.
*   Multiple methods for variable discovery within plugins (explicit definitions, class inspection, regex-based source code analysis).
*   Integration with a pre-existing [`variable_catalog.json`](../../../data/historical_timeline/variable_catalog.json).
*   Generation of a structured Markdown report.
*   Basic logging and error handling for file/directory operations.

A minor structural issue exists where the `datetime` module is imported locally within the `if __name__ == "__main__":` block (line 290) instead of at the top of the file. This does not affect its functionality when run as a script.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Heuristic Variable Discovery:** The methods for discovering variables, particularly "Method 3: Analyze the plugin source code directly" (lines 148-170) using regex, are acknowledged as heuristic (comment on line 155: `This is a heuristic approach and may need refinement`). This could lead to false positives or missed variables.
*   **Dynamic Variable Limitation:** The script intentionally avoids calling plugin methods like `fetch_signals` (line 133) to prevent actual API calls. This is a safe approach but might miss variables that plugins generate or define dynamically based on external responses.
*   **Silent Error Handling:** A `pass` statement within a `try-except` block when attempting to call a plugin's `get_available_variables` method (lines 143-144) could silently ignore errors, potentially missing variables if this specific method fails.
*   **Plugin Class Naming Convention:** The script assumes plugin classes end with the suffix 'Plugin' (line 119). If plugins deviate from this, they might not be fully processed for class-based variable discovery.
*   **Refinement of Regex Patterns:** The regex patterns (lines 156-162) for source code analysis could be expanded or refined for better accuracy.

## 4. Connections & Dependencies

### 4.1. Project Module Imports
*   The script dynamically imports modules from the [`ingestion.iris_plugins_variable_ingestion`](../../../iris/iris_plugins_variable_ingestion/) package using `importlib.import_module()` (line 99).

### 4.2. External Library Dependencies
*   `os`
*   `sys`
*   `importlib`
*   `inspect`
*   `logging`
*   `pathlib`
*   `json`
*   `re`
*   `markdown` (Note: `markdown` library is imported but not used in the provided script content)
*   `datetime` (imported locally in `if __name__ == "__main__":`)

### 4.3. Interaction via Shared Data
*   Reads Python plugin files from the [`iris/iris_plugins_variable_ingestion/`](../../../iris/iris_plugins_variable_ingestion/) directory.
*   Reads variable metadata from [`data/historical_timeline/variable_catalog.json`](../../../data/historical_timeline/variable_catalog.json).

### 4.4. Input/Output Files
*   **Input:**
    *   Plugin files: `*.py` within [`iris/iris_plugins_variable_ingestion/`](../../../iris/iris_plugins_variable_ingestion/)
    *   Variable catalog: [`data/historical_timeline/variable_catalog.json`](../../../data/historical_timeline/variable_catalog.json)
*   **Output:**
    *   Markdown report: [`data/historical_timeline/available_variables.md`](../../../data/historical_timeline/available_variables.md)
    *   Log messages to standard output.

## 5. Function and Class Example Usages

*   **[`get_plugins_list()`](../../../scripts/discover_available_variables.py:37):**
    *   Scans the `IRIS_PLUGINS_DIR` and returns a list of plugin module names (e.g., `['alpha_vantage_plugin', 'fred_plugin']`).
*   **[`get_variable_catalog()`](../../../scripts/discover_available_variables.py:59):**
    *   Loads and returns the content of [`data/historical_timeline/variable_catalog.json`](../../../data/historical_timeline/variable_catalog.json) as a Python dictionary.
*   **[`discover_plugin_variables(plugin_name)`](../../../scripts/discover_available_variables.py:79):**
    *   `plugin_name` (string): The name of the plugin module (e.g., `"alpha_vantage_plugin"`).
    *   Attempts to import the plugin and uses introspection, checks for predefined variable lists/dictionaries, and regex on source code to find variable names. Returns a list of discovered variable strings.
*   **[`discover_all_plugins_variables()`](../../../scripts/discover_available_variables.py:181):**
    *   Orchestrates the discovery process by calling [`get_plugins_list()`](../../../scripts/discover_available_variables.py:37), [`get_variable_catalog()`](../../../scripts/discover_available_variables.py:59), and iterating through plugins with [`discover_plugin_variables()`](../../../scripts/discover_available_variables.py:79).
    *   Returns a dictionary mapping plugin names to a list of their discovered variables.
*   **[`create_markdown_file(variables_by_plugin)`](../../../scripts/discover_available_variables.py:224):**
    *   `variables_by_plugin` (dict): The dictionary returned by [`discover_all_plugins_variables()`](../../../scripts/discover_available_variables.py:181).
    *   Generates a Markdown formatted string summarizing the variables and writes it to `OUTPUT_FILE`.
*   **[`main()`](../../../scripts/discover_available_variables.py:274):**
    *   The main entry point of the script. Calls [`discover_all_plugins_variables()`](../../../scripts/discover_available_variables.py:181) and then [`create_markdown_file()`](../../../scripts/discover_available_variables.py:224) to produce the final report.

## 6. Hardcoding Issues

The script contains several hardcoded paths, names, and patterns:
*   **Directory Paths:**
    *   `IRIS_PLUGINS_DIR = "iris/iris_plugins_variable_ingestion"` (line 33)
*   **File Paths:**
    *   `OUTPUT_FILE = "data/historical_timeline/available_variables.md"` (line 34)
    *   `catalog_path = Path("data/historical_timeline/variable_catalog.json")` (line 66)
*   **Variable/Dictionary Names:**
    *   `potential_var_dicts` list (lines 104-107): `["STOCK_SYMBOLS", "CRYPTO_SYMBOLS", ...]`
*   **Regex Patterns:**
    *   `var_patterns` list (lines 156-162) used for source code analysis.
*   **Naming Conventions:**
    *   Assumption that plugin classes end with `'Plugin'` (line 119).

These hardcodings make the script less flexible if directory structures or naming conventions change.

## 7. Coupling Points

*   **Directory Structure:** Tightly coupled to the existence and structure of the [`iris/iris_plugins_variable_ingestion/`](../../../iris/iris_plugins_variable_ingestion/) directory.
*   **Variable Catalog:** Dependent on the presence and JSON format of [`data/historical_timeline/variable_catalog.json`](../../../data/historical_timeline/variable_catalog.json).
*   **Plugin Implementation Details:** Relies on plugins adhering to certain (heuristic) patterns for defining variables, such as specific dictionary names, class naming conventions (ending with `Plugin`), or having a `get_available_variables` method.
*   **Output Path:** The output file path [`data/historical_timeline/available_variables.md`](../../../data/historical_timeline/available_variables.md) is fixed.

## 8. Existing Tests

No dedicated test file (e.g., `tests/scripts/test_discover_available_variables.py`) is immediately apparent from the project's file listing. As a utility script, it might not have comprehensive unit tests. Testing would likely involve:
*   Creating mock plugin files with various variable definition patterns.
*   A mock `variable_catalog.json`.
*   Verifying the content of the generated Markdown file.

## 9. Module Architecture and Flow

The script follows a sequential execution flow:
1.  **Setup:** Initializes logging, defines constants, and appends the project root to `sys.path`.
2.  **Plugin Identification:** The [`get_plugins_list()`](../../../scripts/discover_available_variables.py:37) function scans `IRIS_PLUGINS_DIR` to find all potential plugin files.
3.  **Catalog Loading:** The [`get_variable_catalog()`](../../../scripts/discover_available_variables.py:59) function loads known variables from a JSON file.
4.  **Variable Discovery Loop (in [`discover_all_plugins_variables()`](../../../scripts/discover_available_variables.py:181)):**
    *   Iterates through each identified plugin.
    *   For each plugin, [`discover_plugin_variables()`](../../../scripts/discover_available_variables.py:79) is called. This function:
        *   Attempts to import the plugin module.
        *   Looks for explicitly defined variable dictionaries/lists (e.g., `STOCK_SYMBOLS`).
        *   Inspects plugin classes (especially those ending in `Plugin`) for attributes or specific methods like `get_available_variables`.
        *   Performs a regex-based scan of the plugin's source code for patterns indicating variable names.
    *   Combines discovered variables with those listed for the plugin in the loaded catalog.
    *   Stores results in a dictionary mapping plugin names to their variables.
5.  **Report Generation:** The [`create_markdown_file()`](../../../scripts/discover_available_variables.py:224) function takes the aggregated variable data and generates a Markdown report. This report includes a summary table and detailed lists of variables per plugin.
6.  **Main Execution:** The [`main()`](../../../scripts/discover_available_variables.py:274) function orchestrates these steps and logs the completion.

## 10. Naming Conventions

*   **Functions and Variables:** Generally adhere to `snake_case` (e.g., [`get_plugins_list`](../../../scripts/discover_available_variables.py:37), `variables_by_plugin`). This aligns with PEP 8.
*   **Constants:** Use `UPPER_CASE` (e.g., `IRIS_PLUGINS_DIR`, `OUTPUT_FILE`). This aligns with PEP 8.
*   **Module Name:** `discover_available_variables.py` is descriptive.
*   **Logging:** A `logger` instance named `logger` is used consistently.
*   **Clarity:** Most names are clear and indicate their purpose.
*   **Minor Inconsistency:** The `datetime` import is done locally within the `if __name__ == "__main__":` block (line 290) rather than at the top with other imports. While functional for a script, it's unconventional.