# Module Analysis: `dev_tools/pulse_ui_bridge.py`

## 1. Module Intent/Purpose

The [`dev_tools/pulse_ui_bridge.py`](dev_tools/pulse_ui_bridge.py:1) module acts as an intermediary layer to connect command-line interface (CLI) functionalities with a graphical user interface (GUI), likely for the Pulse Operator Interface. Its main purpose is to expose core analysis and reporting tools, such as recursion audits, trust brief generation, and variable graphing, in a way that can be easily integrated into and triggered by a UI.

## 2. Key Functionalities

*   **`run_trust_audit_cli(prev_path: str, curr_path: str) -> dict`**:
    *   Takes paths to two forecast cycle files (previous and current, expected in JSONL format).
    *   Reads and parses these files.
    *   Calls [`generate_recursion_report()`](learning/recursion_audit.py:0) from the `learning.recursion_audit` module to compare the two cycles.
    *   Returns a dictionary containing the audit summary or an error message.
*   **`generate_markdown_brief(report_path: str, out_path: str = "pulse_brief.md") -> str`**:
    *   Takes the path to a JSON audit report file.
    *   Reads the report and validates the presence of required keys (`confidence_delta`, `retrodiction_error_delta`, `trust_distribution_current`, `arc_shift_summary`).
    *   Generates a Markdown formatted "Pulse Operator Brief" summarizing the audit.
    *   Writes the brief to the specified `out_path`.
    *   Returns the output path or an error message.
*   **`run_variable_graph(path: str, variables: list, export_path: Optional[str] = None) -> str`**:
    *   Takes the path to a variable history trace file and a list of variable names.
    *   Loads the trace data for the specified variables using [`load_variable_trace()`](dev_tools/pulse_ui_plot.py:0) from [`dev_tools.pulse_ui_plot`](dev_tools/pulse_ui_plot.py:1).
    *   If data is found, it plots the variables using [`plot_variables()`](dev_tools/pulse_ui_plot.py:0) from the same module, optionally exporting the plot to `export_path`.
    *   Returns a success or error/warning message.
*   **UI Helper Functions (Optional, for Tkinter integration):**
    *   **`prompt_and_run_audit(log)`**: Uses `tkinter.filedialog` to prompt the user for previous and current forecast files, then runs [`run_trust_audit_cli()`](dev_tools/pulse_ui_bridge.py:17) and logs the results.
    *   **`prompt_and_generate_brief(log)`**: Uses `tkinter.filedialog` to prompt for an audit report file and a save location for the Markdown brief, then runs [`generate_markdown_brief()`](dev_tools/pulse_ui_bridge.py:29) and logs the output path.
    *   **`prompt_and_plot_variables(log)`**: Uses `tkinter.filedialog` and `tkinter.simpledialog` to prompt for a trace file, variable names, and an optional export path, then runs [`run_variable_graph()`](dev_tools/pulse_ui_bridge.py:54) and logs the result.

## 3. Role Within `dev_tools/` Directory

This module serves as a crucial link between backend/CLI developer tools and a potential GUI front-end. Its role is to:

*   **Abstract Complexity:** Hide the direct implementation details of audit generation and plotting from the UI.
*   **Provide Stable Interfaces:** Offer clear functions that a UI can call to perform specific actions.
*   **Facilitate User Interaction:** Include helper functions that directly use `tkinter` for file dialogs, making it easier to integrate these tools into a Tkinter-based GUI.

## 4. Dependencies

### Internal Pulse Modules:

*   [`learning.recursion_audit.generate_recursion_report`](learning/recursion_audit.py:0): For comparing forecast cycles.
*   [`dev_tools.pulse_ui_plot.load_variable_trace`](dev_tools/pulse_ui_plot.py:0): For loading variable data from trace files.
*   [`dev_tools.pulse_ui_plot.plot_variables`](dev_tools/pulse_ui_plot.py:0): For generating plots of variable data.

### External Libraries:

*   `json`: For reading and parsing JSON/JSONL files.
*   `os`: For path existence checks (`os.path.exists`).
*   `typing.Optional`: For type hinting.
*   `tkinter.filedialog`, `tkinter.simpledialog`: For creating GUI dialogs to select files and input data (used in the optional UI helper functions).

## 5. Adherence to SPARC Principles

*   **Module Intent/Purpose:**
    *   Clearly stated: "Bridge module to unify CLI and GUI tools for the Pulse Operator Interface." This aligns with providing clear, maintainable solutions.
*   **Operational Status/Completeness:**
    *   The core functions ([`run_trust_audit_cli()`](dev_tools/pulse_ui_bridge.py:17), [`generate_markdown_brief()`](dev_tools/pulse_ui_bridge.py:29), [`run_variable_graph()`](dev_tools/pulse_ui_bridge.py:54)) appear operational for their defined tasks, assuming their dependencies work correctly.
    *   The Tkinter helper functions provide a basic level of UI integration completeness.
*   **Implementation Gaps / Unfinished Next Steps:**
    *   **Error Handling:** While `try-except` blocks are used, error messages returned as strings (e.g., `f"❌ File not found: {path}"`) might be less ideal for programmatic UI handling than raising specific exceptions or returning structured error objects.
    *   **Tkinter UI Robustness:** The Tkinter helpers are basic. A full-fledged UI would require more sophisticated state management, error display, and user feedback.
    *   **Configuration:** No external configuration is apparent; paths and parameters are passed directly.
    *   **Testing:** No explicit tests for this bridge module itself are visible within the file.
*   **Connections & Dependencies:**
    *   Dependencies are clearly imported. The module connects data processing logic (recursion audit, plotting) with UI interaction elements (Tkinter).
*   **Function and Class Example Usages:**
    *   The Tkinter helper functions ([`prompt_and_run_audit()`](dev_tools/pulse_ui_bridge.py:70), [`prompt_and_generate_brief()`](dev_tools/pulse_ui_bridge.py:81), [`prompt_and_plot_variables()`](dev_tools/pulse_ui_bridge.py:92)) serve as examples of how the core functions can be invoked, particularly in a GUI context.
    *   Example usage of core functions:
        ```python
        # For run_trust_audit_cli
        # audit_summary = run_trust_audit_cli("path/to/prev_forecast.jsonl", "path/to/curr_forecast.jsonl")
        
        # For generate_markdown_brief
        # brief_path = generate_markdown_brief("path/to/audit_report.json", "output_brief.md")

        # For run_variable_graph
        # result_message = run_variable_graph("path/to/history_trace.jsonl", ["var1", "var2"], "output_plot.png")
        ```
*   **Hardcoding Issues:**
    *   Default output filename `pulse_brief.md` in [`generate_markdown_brief()`](dev_tools/pulse_ui_bridge.py:29).
    *   The structure of the Markdown brief is hardcoded within [`generate_markdown_brief()`](dev_tools/pulse_ui_bridge.py:29).
*   **Coupling Points:**
    *   Tightly coupled to the specific output format of [`generate_recursion_report()`](learning/recursion_audit.py:0) (expects keys like `confidence_delta`).
    *   Coupled to the interfaces of [`load_variable_trace()`](dev_tools/pulse_ui_plot.py:0) and [`plot_variables()`](dev_tools/pulse_ui_plot.py:0).
    *   The UI helper functions are directly coupled to `tkinter`. If a different UI framework were used, these helpers would need to be rewritten.
*   **Existing Tests:**
    *   No tests for this module are present within the file itself.
*   **Module Architecture and Flow:**
    1.  Imports.
    2.  Core bridge functions:
        *   [`run_trust_audit_cli()`](dev_tools/pulse_ui_bridge.py:17): File I/O, call to `generate_recursion_report`, error handling.
        *   [`generate_markdown_brief()`](dev_tools/pulse_ui_bridge.py:29): File I/O, data validation, Markdown string formatting, error handling.
        *   [`run_variable_graph()`](dev_tools/pulse_ui_bridge.py:54): File check, call to `load_variable_trace` and `plot_variables`, error handling.
    3.  Optional Tkinter UI helper functions: Each prompts for inputs using dialogs, calls a core function, and logs the output.
    The architecture is functional, separating core logic from UI interaction helpers.
*   **Naming Conventions:**
    *   Module name (`pulse_ui_bridge.py`) is descriptive.
    *   Function names are clear and follow snake_case.
    *   Variable names are generally clear.

## 6. Overall Assessment

*   **Completeness:**
    *   The module is reasonably complete for its role as a bridge, providing the necessary functions to expose backend tools to a UI.
    *   The Tkinter helpers offer a basic but functional starting point for UI integration.
*   **Quality:**
    *   **Strengths:**
        *   Clear separation of concerns between core logic functions and UI helper functions.
        *   Provides a necessary abstraction layer for UI development.
        *   Basic error handling is present in each core function.
    *   **Areas for Improvement:**
        *   **Error Reporting:** Returning error strings can be less effective for UI logic than raising custom exceptions or returning structured error objects/codes.
        *   **Flexibility of Markdown Generation:** The Markdown brief format is hardcoded. Templates or a more configurable approach could be beneficial.
        *   **Testability:** The functions, especially those with file I/O and external calls, could be structured for easier unit testing (e.g., by injecting dependencies like file readers/writers).
        *   **UI Agnostic Core:** While Tkinter helpers are useful, ensuring the core functions remain entirely UI-agnostic is important for future flexibility if the UI framework changes.

## 7. Note for Main Report

The `dev_tools/pulse_ui_bridge.py` module effectively connects CLI tools for recursion audits, brief generation, and variable plotting to a UI, featuring Tkinter-based helpers for user interaction, though its error handling could be more robust for UI integration.