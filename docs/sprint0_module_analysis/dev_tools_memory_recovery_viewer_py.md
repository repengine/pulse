# Module Analysis: `dev_tools/memory_recovery_viewer.py`

## 1. Module Intent/Purpose

The primary role of the [`dev_tools/memory_recovery_viewer.py`](../../dev_tools/memory_recovery_viewer.py:1) module is to serve as a command-line utility. It is designed to help users explore, summarize, and export forecasts that have been discarded or "blocked" and logged, typically due to failing license enforcement gates (e.g., issues like drift or low alignment with expected patterns).

## 2. Operational Status/Completeness

The module appears to be functionally complete for its stated objectives:
- It successfully loads data from a specified log file.
- It can generate a summary of blocked forecasts based on their `license_status`.
- It allows users to export a subset of these forecasts filtered by a specific reason.
- Basic error handling for file operations (loading and exporting) is implemented (e.g., in [`load_blocked_forecasts()`](../../dev_tools/memory_recovery_viewer.py:18) and [`export_subset()`](../../dev_tools/memory_recovery_viewer.py:40)).
- No `TODO`, `FIXME`, or other explicit placeholder comments indicating unfinished work were found.

## 3. Implementation Gaps / Unfinished Next Steps

-   **Intended Extensiveness:** The module is well-focused and fulfills its immediate goals. There are no strong indications that it was originally intended to be significantly more extensive within its current defined scope.
-   **Logical Next Steps/Follow-up Features (Potential Enhancements):**
    *   **Advanced Filtering:** Implement more sophisticated filtering capabilities beyond a single `license_status` (e.g., date ranges, specific forecast attributes).
    *   **Interactive Mode:** An interactive command-line interface (CLI) mode could allow for more dynamic exploration of the blocked forecasts.
    *   **Integration with Recovery Pipelines:** The exported forecasts could be fed into a "memory repair" or "re-evaluation" pipeline. The tool could offer an option to trigger such a pipeline.
    *   **Detailed Statistics:** The summary could be enhanced to include more detailed statistics, such as timestamps of when forecasts were blocked, or distributions of other relevant forecast attributes.
-   **Deviations/Stoppages:** There are no clear signs of development paths that were started but then abandoned or significantly altered.

## 4. Connections & Dependencies

-   **Direct Project Module Imports:** None. This module operates as a standalone tool.
-   **External Library Dependencies:**
    *   [`argparse`](../../dev_tools/memory_recovery_viewer.py:13): Used for parsing command-line arguments.
    *   [`json`](../../dev_tools/memory_recovery_viewer.py:14): Used for reading and writing data in JSON and JSON Lines (JSONL) format.
    *   [`typing`](../../dev_tools/memory_recovery_viewer.py:15) (`List`, `Dict`): Used for type hinting to improve code clarity and maintainability.
-   **Interaction via Shared Data:**
    *   The module primarily interacts by reading from a log file. The default path is [`logs/blocked_memory_log.jsonl`](../../dev_tools/memory_recovery_viewer.py:54), as specified in the [`main()`](../../dev_tools/memory_recovery_viewer.py:52) function's argument parser. This file is the main data input.
    *   It can write to a user-specified output file if the export functionality is used.
-   **Input/Output Files:**
    *   **Input:** A JSON Lines (`.jsonl`) file. The default is [`logs/blocked_memory_log.jsonl`](../../dev_tools/memory_recovery_viewer.py:54), but this can be overridden using the `--log` command-line argument. Each line in this file is expected to be a JSON object representing a single blocked forecast.
    *   **Output:** A user-specified file path for exporting filtered subsets of forecasts, provided via the `--export` command-line argument. The output is also in JSON Lines format.

## 5. Function and Class Example Usages

The module consists of functions and a `main` execution block:

-   **[`load_blocked_forecasts(path: str) -> List[Dict]`](../../dev_tools/memory_recovery_viewer.py:18):**
    *   **Description:** Reads a JSON Lines file from the given `path`. Each line is parsed as a JSON object (dictionary). It returns a list of these forecast dictionaries.
    *   **Example Usage (Conceptual):**
        ```python
        forecast_data = load_blocked_forecasts("path/to/your/blocked_memory_log.jsonl")
        ```

-   **[`summarize_blocked_memory(forecasts: List[Dict]) -> None`](../../dev_tools/memory_recovery_viewer.py:28):**
    *   **Description:** Takes a list of forecast dictionaries, counts them based on the value of their `"license_status"` key, and prints a summary to the console.
    *   **Example Usage (Conceptual):**
        ```python
        forecast_data = load_blocked_forecasts("log.jsonl")
        if forecast_data:
            summarize_blocked_memory(forecast_data)
        ```

-   **[`export_subset(forecasts: List[Dict], reason_filter: str, out_path: str) -> None`](../../dev_tools/memory_recovery_viewer.py:40):**
    *   **Description:** Filters the input `forecasts` list, selecting only those dictionaries where the `"license_status"` key matches the `reason_filter`. The selected forecasts are then written to `out_path` in JSON Lines format.
    *   **Example Usage (Conceptual):**
        ```python
        forecast_data = load_blocked_forecasts("log.jsonl")
        if forecast_data:
            export_subset(forecast_data, "LOW_ALIGNMENT_SCORE", "exports/low_alignment_forecasts.jsonl")
        ```

-   **[`main()`](../../dev_tools/memory_recovery_viewer.py:52):**
    *   **Description:** This is the main entry point when the script is executed. It uses `argparse` to handle command-line arguments for specifying the log file path, requesting a summary, and defining export parameters (output path and filter reason).
    *   **CLI Example Usages:**
        ```bash
        # Show summary from the default log file
        python dev_tools/memory_recovery_viewer.py --summary

        # Show summary from a custom log file
        python dev_tools/memory_recovery_viewer.py --log custom_logs/blocked.jsonl --summary

        # Export forecasts with a specific reason to a specified file
        python dev_tools/memory_recovery_viewer.py --log logs/blocked_memory_log.jsonl --export exported_data/drift_detected.jsonl --reason "DRIFT_DETECTED"
        ```

## 6. Hardcoding Issues

-   **Default Log Path:** The default path for the input log file is hardcoded as [`"logs/blocked_memory_log.jsonl"`](../../dev_tools/memory_recovery_viewer.py:54) within the `argparse` setup. While this provides a convenient default, it assumes a specific project directory structure. Users can override this with the `--log` argument.
-   **Default Label for Missing Status:** If a forecast entry in the log file is missing the `"license_status"` key, it's categorized as [`"❓ Unlabeled"`](../../dev_tools/memory_recovery_viewer.py:32) in the summary. This is a reasonable default for handling potentially malformed data.
-   **Console Output Prefixes:** Status messages printed to the console use hardcoded emoji prefixes (e.g., [`"❌ Failed..."`](../../dev_tools/memory_recovery_viewer.py:24), [`"✅ Exported..."`](../../dev_tools/memory_recovery_viewer.py:47)). These are minor and primarily affect user interface rather than core logic.

## 7. Coupling Points

-   **Log File Format:** The module is tightly coupled to the expected format of the `blocked_memory_log.jsonl` file. It assumes:
    *   The file is in JSON Lines format (one JSON object per line).
    *   Each JSON object (forecast) contains a key named `"license_status"` which is used for summarization and filtering.
    Any deviation from this format in the log file would likely cause errors or incorrect behavior in the tool.
-   **License Status Semantics:** The tool is implicitly coupled to the system that generates the `blocked_memory_log.jsonl`. The meaning and set of possible values for `"license_status"` are defined externally by that system.

## 8. Existing Tests

-   Based on the provided project file structure, there is no apparent dedicated test file for this module (e.g., a `tests/dev_tools/test_memory_recovery_viewer.py` or similar).
-   **Assessment:** It appears that no formal unit tests exist for this module. Testing would likely involve:
    *   Creating sample `blocked_memory_log.jsonl` files with various scenarios (empty file, malformed JSON, different `license_status` values, missing `license_status` key).
    *   Verifying the console output of the summary function.
    *   Verifying the content of exported files.

## 9. Module Architecture and Flow

The module follows a straightforward command-line tool architecture:

1.  **Initialization & Argument Parsing ([`main()`](../../dev_tools/memory_recovery_viewer.py:52)):**
    *   The script starts by parsing command-line arguments using `argparse`. This determines the input log file, whether to show a summary, and if/what to export.
2.  **Data Loading ([`load_blocked_forecasts()`](../../dev_tools/memory_recovery_viewer.py:18)):**
    *   The specified log file (defaulting to [`logs/blocked_memory_log.jsonl`](../../dev_tools/memory_recovery_viewer.py:54)) is read.
    *   Each line is parsed as a JSON object, and these are collected into a list of dictionaries.
    *   Basic error handling is in place for file reading issues.
3.  **Conditional Processing (based on parsed arguments):**
    *   **Summary Generation ([`summarize_blocked_memory()`](../../dev_tools/memory_recovery_viewer.py:28)):** If the `--summary` flag is present, this function is called. It iterates through the loaded forecasts, counts them by their `license_status`, and prints a formatted summary to the console.
    *   **Data Export ([`export_subset()`](../../dev_tools/memory_recovery_viewer.py:40)):** If both `--export` (output path) and `--reason` (filter criterion) arguments are provided, this function is called. It filters the forecasts based on the `license_status` matching the given reason and writes the selected forecasts to the specified output file. Error handling for file writing is included.
4.  **Execution Trigger:**
    *   The script uses the common Python idiom `if __name__ == "__main__":` to call the [`main()`](../../dev_tools/memory_recovery_viewer.py:69) function, making it directly executable.

## 10. Naming Conventions

-   **Functions:** Names like [`load_blocked_forecasts`](../../dev_tools/memory_recovery_viewer.py:18), [`summarize_blocked_memory`](../../dev_tools/memory_recovery_viewer.py:28), and [`export_subset`](../../dev_tools/memory_recovery_viewer.py:40) use `snake_case`, adhering to PEP 8 guidelines.
-   **Variables:** Variable names such as `forecasts`, `by_reason`, `reason_filter`, `out_path`, and `args` are generally clear, descriptive, and also use `snake_case`. The use of `fc` as a loop variable for 'forecast' is a common and acceptable abbreviation.
-   **Module Name:** `memory_recovery_viewer.py` is descriptive of the module's purpose.
-   **Constants/Defaults:** String literals like [`"❓ Unlabeled"`](../../dev_tools/memory_recovery_viewer.py:32) are used for default values where appropriate.
-   **Overall Consistency:** Naming conventions are applied consistently throughout the module and align well with standard Python practices (PEP 8). There are no apparent AI assumption errors or significant deviations from these standards.