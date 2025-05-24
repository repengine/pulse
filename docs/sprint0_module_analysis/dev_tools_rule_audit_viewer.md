# Module Analysis: `dev_tools/rule_audit_viewer.py`

**Last Updated:** 2025-05-15
**Module Version:** As of `dev_tools/review_forecast_batch.py` (Author: Pulse v0.20 in docstring)
**Analyst:** Roo Docs

## 1. Module Intent/Purpose

The module [`dev_tools/rule_audit_viewer.py`](dev_tools/rule_audit_viewer.py:1) is a command-line utility designed to display symbolic and variable deltas caused by the application of rules during a forecast. It reads a saved forecast JSON file, parses the rule audit trail embedded within its metadata, and prints a human-readable summary of changes made by each rule. Its primary purpose is to aid developers and analysts in understanding the impact and behavior of individual rules within the forecasting process.

## 2. Operational Status/Completeness

The module appears to be **operational** for its defined scope. It successfully parses command-line arguments for a forecast file path, reads the JSON data, and iterates through the `rule_audit` section to print relevant information.

**Key Functionalities:**
-   Parses a forecast JSON file.
-   Displays basic forecast metadata (ID, confidence, fragility).
-   Lists each rule applied, including its ID and symbolic tags.
-   Details changes to variables (value `from` -> `to`).
-   Details changes to overlays (value `from` -> `to`).

## 3. Implementation Gaps / Unfinished Next Steps

-   **Error Handling:** Basic error handling for file I/O (e.g., file not found) or JSON parsing errors (e.g., malformed JSON) is not explicitly implemented; it relies on Python's default exception handling. More user-friendly error messages could be beneficial.
-   **Unused Import:** The module imports `PATHS` from [`core.path_registry`](core/path_registry.py:1) and asserts its type, but `PATHS` is not subsequently used in the script's logic. This might be a remnant of previous development or an incomplete integration.
-   **Output Flexibility:** The output is currently limited to `print` statements to the console. Enhancements could include options for more structured output (e.g., CSV, detailed JSON) or logging to a file.
-   **Schema Rigidity:** The script assumes a specific structure for the input forecast JSON, particularly the `metadata.rule_audit` section. While necessary for parsing, it means changes to this schema would require updates to the viewer.

## 4. Connections & Dependencies

### Internal Pulse Modules:
-   [`utils.log_utils.get_logger`](utils/log_utils.py:1): Used for obtaining a logger instance.
-   [`core.path_registry.PATHS`](core/path_registry.py:1): Imported and type-checked, but not actively used in the core logic.

### External Libraries:
-   `json`: Standard Python library for parsing JSON data.
-   `argparse`: Standard Python library for parsing command-line arguments.

## 5. Function and Class Example Usages

The module is designed to be run as a command-line script.

**Example Usage (from command line):**
```bash
python dev_tools/rule_audit_viewer.py path/to/your/forecast_file.json
```

**Code Snippet (Illustrative of core logic):**
```python
# From show_audit_from_forecast(forecast_path)
# ... (file loading and initial print statements) ...
# audit_log = metadata.get("rule_audit", [])
#
# print("\n🔍 Rule Audit Trail:")
# for entry in audit_log:
#     print(f"• {entry['rule_id']} (tags: {entry['symbolic_tags']})")
#     for var, delta in entry.get("variables_changed", {}).items():
#         print(f"   Δ {var}: {delta['from']} → {delta['to']}")
#     for ov, delta in entry.get("overlays_changed", {}).items():
#         print(f"   Δ [overlay] {ov}: {delta['from']} → {delta['to']}")
#     print("")
```

## 6. Hardcoding Issues

-   **Forecast JSON Schema:** The script implicitly relies on specific keys and structures within the input forecast JSON file (e.g., `forecast_id`, `metadata`, `rule_audit`, `variables_changed`, `overlays_changed`, `from`, `to`). This is inherent to its function as a data viewer but makes it sensitive to schema changes.
-   No hardcoded file paths for input data; the path is provided via a command-line argument.
-   No hardcoded secrets or sensitive credentials.

## 7. Coupling Points

-   **High Coupling:** Tightly coupled to the schema of the forecast JSON files it processes, especially the structure of the `metadata.rule_audit` array and its elements.
-   **Low Coupling:** Loosely coupled to the internal [`utils.log_utils`](utils/log_utils.py:1) and [`core.path_registry`](core/path_registry.py:1) modules.

## 8. Existing Tests

-   No dedicated unit test file (e.g., `tests/dev_tools/test_rule_audit_viewer.py`) was identified in the provided project structure.
-   The module contains an `assert isinstance(PATHS, dict)` on line 13, which is a basic type check for an imported variable.
-   The main functionality within [`show_audit_from_forecast()`](dev_tools/rule_audit_viewer.py:17) is not covered by automated tests within the module itself.

## 9. Module Architecture and Flow

-   **Architecture:** Simple script-based architecture.
    -   It defines a single primary function: [`show_audit_from_forecast(forecast_path)`](dev_tools/rule_audit_viewer.py:17).
    -   It uses the `argparse` module to handle command-line argument parsing in the `if __name__ == "__main__":` block.
-   **Control Flow:**
    1.  Script execution begins; logger is initialized.
    2.  If run as the main script, `argparse` parses the command-line arguments to get the `forecast_file` path.
    3.  The [`show_audit_from_forecast()`](dev_tools/rule_audit_viewer.py:17) function is called with the file path.
    4.  Inside the function:
        a.  The specified JSON file is opened and its content is loaded.
        b.  Basic forecast information (ID, confidence, fragility) is printed.
        c.  The `rule_audit` list is extracted from the metadata.
        d.  The script iterates through each entry in `rule_audit`.
        e.  For each entry, it prints the rule ID, tags, and details of variable and overlay changes.

## 10. Naming Conventions

-   Variable names (e.g., `forecast_path`, `audit_log`, `entry`) and function names (`show_audit_from_forecast`, `get_logger`) generally follow Python's snake_case convention (PEP 8).
-   The logger instance is named `logger`.
-   Imported `PATHS` is uppercase, typical for constants.

## 11. SPARC Principles Adherence Assessment

-   **Specification (Clarity of Purpose):** Good. The module's purpose is clearly stated in its docstring and reflected in its functionality.
-   **Modularity:** Good. The core logic is encapsulated in the [`show_audit_from_forecast()`](dev_tools/rule_audit_viewer.py:17) function. It has minimal, well-defined dependencies.
-   **Testability:** Fair. The core function could be tested by mocking file reads and JSON content. However, the lack of existing dedicated tests is a drawback.
-   **Maintainability:** Good for its current size and complexity. The code is straightforward and readable. Adding more robust error handling and tests would improve it further.
-   **No Hardcoding (Critical):** Good. No hardcoded file paths for input or sensitive credentials. Relies on the structure of the input JSON, which is acceptable for a viewer.
-   **Security (Secrets):** Excellent. No secrets are handled or stored.
-   **Composability/Reusability:** Fair. The main function could potentially be imported and used by other tools if its output mechanism were more flexible (e.g., returning data instead of just printing).
-   **Configurability:** Fair. Takes the input file path as a command-line argument. No other configuration options are present.
-   **Error Handling:** Needs Improvement. Relies on default Python exceptions.
-   **Logging:** Basic. Uses `get_logger` but only prints to console within the main function. The logger instance itself is not heavily used for varied log levels or detailed tracing within this script.

## 12. Overall Assessment & Quality

[`dev_tools/rule_audit_viewer.py`](dev_tools/rule_audit_viewer.py:1) is a useful and functional command-line utility for inspecting the effects of rules on forecasts. It is concise, readable, and serves its specific purpose well.

**Strengths:**
-   Clear purpose and straightforward implementation.
-   Correctly uses `argparse` for command-line interaction.
-   Provides a human-readable output of complex audit data.

**Areas for Improvement:**
-   **Testing:** Implement dedicated unit tests to ensure reliability and facilitate future modifications.
-   **Error Handling:** Add more specific error handling for file operations and JSON parsing to provide better user feedback.
-   **Unused Import:** Resolve the status of the `PATHS` import from [`core.path_registry`](core/path_registry.py:1) (either use it or remove it).
-   **Output Flexibility (Optional):** Consider options for more structured output if the tool's usage evolves.

**Overall Quality:** Good for a developer utility. It fulfills its intended role effectively with a simple design.

## 13. Summary Note for Main Report

The [`dev_tools/rule_audit_viewer.py`](dev_tools/rule_audit_viewer.py:1) module is a CLI tool that effectively displays rule-induced changes from forecast JSON files, aiding in debugging and analysis. It is functional but could benefit from dedicated unit tests and more robust error handling.