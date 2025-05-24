# Module Analysis: `pulse_desktop/ui_operator.py`

## 1. Module Intent/Purpose

The primary role of the [`pulse_desktop/ui_operator.py`](pulse_desktop/ui_operator.py) module is to serve as a Command Line Interface (CLI) and a basic unified console for operators to inspect, evaluate, and interact with Pulse's recursive intelligence. It provides functionalities for:
- Comparing recursion cycles (trust + retrodiction deltas).
- Plotting the evolution of variables over time.
- Generating trust audit reports.
- Creating operator briefs in Markdown format.
- Viewing various system digests and logs.
- Running the forecast pipeline with basic UI assistance for file selection.

## 2. Operational Status/Completeness

The module appears largely functional for the features explicitly described and implemented.
- CLI argument parsing via `argparse` is implemented for core tasks.
- An interactive text-based menu provides access to additional functionalities.
- Functions for comparison, plotting, brief generation, and log/digest viewing are present.
- There are no obvious "TODO" comments or major incomplete placeholders for the implemented features.
- The [`display_forecast_visualization()`](pulse_desktop/ui_operator.py:184) function, though not called by the main CLI flow, seems complete for its purpose.

## 3. Implementation Gaps / Unfinished Next Steps

- **GUI Sophistication:** Despite being in a `pulse_desktop` directory and named `ui_operator.py`, the UI is predominantly CLI-based. The use of `tkinter` is minimal (only for file dialogs in [`run_forecast_pipeline_ui()`](pulse_desktop/ui_operator.py:72)). This suggests that a more comprehensive graphical user interface might have been an intended but not fully developed feature.
- **`last_batch` Global:** The function [`run_forecast_pipeline_ui()`](pulse_desktop/ui_operator.py:72) attempts to access `globals().get("last_batch", None)` ([`pulse_desktop/ui_operator.py:147`](pulse_desktop/ui_operator.py:147)). This implies an expectation that this variable might be populated by a broader desktop application context, which is not evident within this standalone module. This could be an incomplete integration point.
- **Error Handling and User Feedback:** While some `try-except` blocks exist, error handling could be more robust, and user feedback in the CLI could be more detailed for certain operations.

## 4. Connections & Dependencies

### Direct Project Module Imports:
- [`learning.recursion_audit`](learning/recursion_audit.py): For [`generate_recursion_report()`](learning/recursion_audit.py:18).
- [`dev_tools.pulse_ui_plot`](dev_tools/pulse_ui_plot.py): For [`load_variable_trace()`](dev_tools/pulse_ui_plot.py:19) and [`plot_variables()`](dev_tools/pulse_ui_plot.py:19).
- [`core.pulse_config`](core/pulse_config.py): For accessing and modifying global configurations like `USE_SYMBOLIC_OVERLAYS`.
- [`operator_interface.learning_log_viewer`](operator_interface/learning_log_viewer.py): For [`load_learning_events()`](operator_interface/learning_log_viewer.py:21), [`summarize_learning_events()`](operator_interface/learning_log_viewer.py:21), [`render_event_digest()`](operator_interface/learning_log_viewer.py:21).
- [`memory.variable_cluster_engine`](memory/variable_cluster_engine.py): For [`summarize_clusters()`](memory/variable_cluster_engine.py:22).
- [`operator_interface.variable_cluster_digest_formatter`](operator_interface/variable_cluster_digest_formatter.py): For [`format_variable_cluster_digest_md()`](operator_interface/variable_cluster_digest_formatter.py:23).
- [`operator_interface.mutation_digest_exporter`](operator_interface/mutation_digest_exporter.py): For [`export_full_digest()`](operator_interface/mutation_digest_exporter.py:24).
- [`operator_interface.symbolic_contradiction_digest`](operator_interface/symbolic_contradiction_digest.py): For [`format_contradiction_cluster_md()`](operator_interface/symbolic_contradiction_digest.py:25) and [`load_symbolic_conflict_events()`](operator_interface/symbolic_contradiction_digest.py:176).
- [`learning.forecast_pipeline_runner`](learning/forecast_pipeline_runner.py): For [`run_forecast_pipeline()`](learning/forecast_pipeline_runner.py:76).

### External Library Dependencies:
- `argparse`: For CLI argument parsing.
- `json`: For reading and writing JSON data (forecast batches, reports).
- `os`: Standard library (implicitly used for path operations, though not extensively).
- `tkinter`: Conditionally imported for file dialogs in the UI.
- `typing.Optional`: For type hinting.

### Interaction via Shared Data:
- Reads `.jsonl` files for forecast batches and variable traces.
- Reads `.json` files for audit reports.
- Modifies the global configuration `core.pulse_config.USE_SYMBOLIC_OVERLAYS`.

### Input/Output Files:
- **Input:**
    - Previous and current forecast batches (`.jsonl` files) for comparison.
    - Variable trace files (`.jsonl`) for plotting.
    - JSON audit reports for brief generation.
- **Output:**
    - JSON audit reports (e.g., `audit.json`).
    - PNG image files for plots (e.g., `graph.png`).
    - Markdown operator briefs (e.g., `pulse_brief.md`).

## 5. Function and Class Example Usages

- **`run_cycle_comparison(prev_path: str, curr_path: str, output: Optional[str] = None)` ([`pulse_desktop/ui_operator.py:28`](pulse_desktop/ui_operator.py:28))**
  - Compares two forecast batches from JSONL files and outputs a JSON report.
  - CLI Usage: `python pulse_desktop/ui_operator.py --compare prev_batch.jsonl curr_batch.jsonl --export comparison_report.json`

- **`run_variable_plot(trace_path: str, variables: list, export: Optional[str] = None)` ([`pulse_desktop/ui_operator.py:43`](pulse_desktop/ui_operator.py:43))**
  - Loads variable history from a trace file and plots specified variables, optionally exporting to an image.
  - CLI Usage: `python pulse_desktop/ui_operator.py --plot-variable var_A var_B --history variable_traces.jsonl --export plot_output.png`

- **`generate_operator_brief(report_path: str, output_md: str)` ([`pulse_desktop/ui_operator.py:51`](pulse_desktop/ui_operator.py:51))**
  - Generates a Markdown summary from a JSON audit report.
  - CLI Usage: `python pulse_desktop/ui_operator.py --brief audit_report.json --export operator_summary.md`

- **`main()` ([`pulse_desktop/ui_operator.py:105`](pulse_desktop/ui_operator.py:105))**
  - Parses CLI arguments for direct actions or presents an interactive menu for various operations like viewing logs, digests, or toggling symbolic overlays.

- **`display_forecast_visualization(...)` ([`pulse_desktop/ui_operator.py:184`](pulse_desktop/ui_operator.py:184))**
  - Prints a text-based visualization of simulation, AI, and ensemble forecasts along with performance metrics. This function is not directly invoked by the main CLI argument flow.

## 6. Hardcoding Issues

- **Default Filenames:** The default output filename for the operator brief is hardcoded as `"pulse_brief.md"` ([`pulse_desktop/ui_operator.py:125`](pulse_desktop/ui_operator.py:125)) if an export path isn't provided.
- **Menu Choices:** Interactive menu options are hardcoded strings (e.g., `"8"`, `"9"`, `"L"`, `"V"`, `"B"`, `"D"`, `"Y"`) within the [`main()`](pulse_desktop/ui_operator.py:105) function ([`pulse_desktop/ui_operator.py:139-178`](pulse_desktop/ui_operator.py:139)).
- **UI Text & Titles:** Various print statements for UI prompts, titles, and section headers in generated reports are hardcoded strings (e.g., "🔁 Comparing recursive forecast batches..." ([`pulse_desktop/ui_operator.py:29`](pulse_desktop/ui_operator.py:29)), Markdown headers in [`generate_operator_brief()`](pulse_desktop/ui_operator.py:51) ([`pulse_desktop/ui_operator.py:57-66`](pulse_desktop/ui_operator.py:57))).
- **Log Limits:** The number of events loaded by [`load_learning_events()`](operator_interface/learning_log_viewer.py:21) is hardcoded to `limit=20` ([`pulse_desktop/ui_operator.py:154`](pulse_desktop/ui_operator.py:154)).
- **Format Strings:** Output formatting in [`display_forecast_visualization()`](pulse_desktop/ui_operator.py:184) uses hardcoded format specifiers (e.g., `"{:.2f}"`).

## 7. Coupling Points

- **Data Formats:** Tightly coupled to the specific JSON and JSONL structures of input forecast batches, variable traces, and audit reports. Changes to these external data formats would likely break the module.
- **Imported Module Interfaces:** Relies on the specific function signatures, parameter expectations, and return value structures of functions imported from other project modules (e.g., [`generate_recursion_report()`](learning/recursion_audit.py:18), [`plot_variables()`](dev_tools/pulse_ui_plot.py:19), [`run_forecast_pipeline()`](learning/forecast_pipeline_runner.py:76)).
- **Global Configuration:** Directly accesses and modifies the global state variable `core.pulse_config.USE_SYMBOLIC_OVERLAYS` ([`pulse_desktop/ui_operator.py:132`](pulse_desktop/ui_operator.py:132), [`pulse_desktop/ui_operator.py:141-142`](pulse_desktop/ui_operator.py:141)), creating a strong coupling point with the project's global configuration.
- **Execution Environment for `last_batch`:** The use of `globals().get("last_batch", None)` ([`pulse_desktop/ui_operator.py:147`](pulse_desktop/ui_operator.py:147)) creates a dependency on the execution environment or a calling module to potentially set this global variable.

## 8. Existing Tests

- Based on the provided file list, there is no apparent dedicated test file for `pulse_desktop/ui_operator.py` (e.g., `tests/pulse_desktop/test_ui_operator.py`).
- Testing this module would likely require:
    - Mocking file system operations for reading/writing reports and data files.
    - Mocking the `tkinter` library for UI interactions.
    - Mocking the imported functions from other project modules to isolate testing to this module's logic.
    - Integration tests to verify CLI argument parsing and interactive menu flows.
- The absence of a specific test file suggests that unit/integration test coverage for this module might be limited or handled within broader, less granular test suites.

## 9. Module Architecture and Flow

- **Entry Point:** The [`main()`](pulse_desktop/ui_operator.py:105) function serves as the primary entry point.
- **Dispatch Logic:**
    - It uses `argparse` to handle specific command-line arguments (`--compare`, `--plot-variable`, `--brief`). If these are provided, the corresponding function is executed, and the script typically exits.
    - If no specific task-oriented arguments are given, it falls back to an interactive text-based menu. User input then drives the execution of different functionalities (toggling configurations, viewing logs, running pipelines, etc.).
- **Functional Decomposition:** The module is broken down into several functions, each responsible for a distinct task (e.g., [`run_cycle_comparison()`](pulse_desktop/ui_operator.py:28), [`generate_operator_brief()`](pulse_desktop/ui_operator.py:51), [`run_variable_plot()`](pulse_desktop/ui_operator.py:43)).
- **UI Interaction:**
    - Primarily CLI-based.
    - Minimal GUI interaction via `tkinter.filedialog` within the [`run_forecast_pipeline_ui()`](pulse_desktop/ui_operator.py:72) function for file selection.
- **Standalone Utility:** The [`display_forecast_visualization()`](pulse_desktop/ui_operator.py:184) function is present but not integrated into the main CLI/interactive flow, suggesting it might be a utility function called from elsewhere or intended for a different context.

## 10. Naming Conventions

- **Functions:** Generally follow `snake_case` (e.g., [`run_cycle_comparison()`](pulse_desktop/ui_operator.py:28), [`generate_operator_brief()`](pulse_desktop/ui_operator.py:51)), which is consistent with PEP 8.
- **Variables:** Mostly use `snake_case` (e.g., `prev_path`, `output_md`, `trace_path`).
- **Module Name:** `ui_operator.py` is descriptive of its purpose.
- **Constants:** Imported global configurations like `USE_SYMBOLIC_OVERLAYS` follow `UPPER_CASE_SNAKE_CASE`.
- **Clarity:** Names are generally clear and indicative of their purpose. No significant deviations from common Python naming standards or potential AI-induced naming errors were observed. String literals for UI prompts are functional.