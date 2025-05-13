# Root Directory Cleanup Plan

This document outlines the proposed plan to reorganize files currently located in the root directory of the Pulse project into more appropriate subdirectories. This effort aims to improve project structure, maintainability, and clarity.

## Methodology

1.  **Identification:** Files in the root directory were analyzed to identify modules, scripts, configuration files, documentation, and data/output files that would be better placed in subdirectories.
2.  **Destination:** For each identified file, a target subdirectory (either existing or newly proposed) was determined based on its function and the existing project structure.
3.  **Import Patching (Post-Move):** For every Python (`.py`) file moved, all files importing it will need their import statements updated. This will be done using `search_files` to locate dependencies and `apply_diff` to patch them. This step will be performed after the file moves are approved and executed.

## Proposed File Moves

Below is a list of files to be moved, their proposed new locations, and the reasoning for each move.

### Category 1: Scripts & Utilities

| Current Path                        | Proposed New Path                                       | Reasoning                                                                 |
| :---------------------------------- | :------------------------------------------------------ | :------------------------------------------------------------------------ |
| `analyze_historical_data_quality.py`| `scripts/analysis/analyze_historical_data_quality.py`   | Script for data quality analysis.                                         |
| `api_key_report.py`                 | `scripts/reporting/api_key_report.py`                   | Script for reporting on API keys.                                         |
| `api_key_test_updated.py`           | `dev_tools/testing/api_key_test_updated.py`             | Test script for API keys.                                                 |
| `api_key_test.py`                   | `dev_tools/testing/api_key_test.py`                     | Test script for API keys.                                                 |
| `benchmark_retrodiction.py`         | `scripts/benchmarking/benchmark_retrodiction.py`        | Script for running retrodiction benchmarks.                               |
| `check_benchmark_deps.py`           | `scripts/benchmarking/check_benchmark_deps.py`          | Script to check benchmark dependencies.                                   |
| `delete_pycache.py`                 | `dev_tools/utils/delete_pycache.py`                     | Utility script for cleaning `__pycache__`.                                |
| `enhanced_phantom_scanner.py`       | `dev_tools/analysis/enhanced_phantom_scanner.py`        | Code analysis/scanning tool.                                              |
| `phantom_function_scanner.py`       | `dev_tools/analysis/phantom_function_scanner.py`        | Code analysis/scanning tool.                                              |
| `git_cleanup.py`                    | `dev_tools/utils/git_cleanup.py`                        | Utility script for Git operations.                                        |
| `improve_historical_data.py`        | `scripts/data_management/improve_historical_data.py`    | Script for improving historical data.                                     |
| `mlflow_tracking_example.py`        | `examples/mlflow_tracking_example.py`                   | Example script demonstrating MLflow usage.                                |
| `patch_imports.py`                  | `dev_tools/utils/patch_imports.py`                      | Utility script for patching import statements.                            |
| `runversionone.py`                  | `scripts/legacy/runversionone.py`                       | Likely an old or legacy run script.                                       |
| `pulse_ui_start.bat`                | `scripts/launchers/pulse_ui_start.bat`                  | Batch script to start the Pulse UI.                                       |
| `start_pulse_gui.bat`               | `scripts/launchers/start_pulse_gui.bat`                 | Batch script to start the Pulse GUI.                                      |

### Category 2: Core Application Logic / API / Main Entry Points

| Current Path                        | Proposed New Path                                       | Reasoning                                                                 |
| :---------------------------------- | :------------------------------------------------------ | :------------------------------------------------------------------------ |
| `api.py`                            | `api/core_api.py`                                       | Core API definitions. Moved to a new top-level `api/` directory.          |
| `event_bus.py`                      | `core/event_bus.py`                                     | Core event bus component, fits well within the existing `core/` module.   |
| `main.py`                           | `cli/main.py`                                           | Main CLI entry point for the application. Moved to a new `cli/` directory.|
| `pulse_api_server.py`               | `api/server.py`                                         | API server implementation. Moved to `api/` directory.                     |
| `pulse_gui_launcher.py`             | `cli/gui_launcher.py`                                   | GUI launcher script. Moved to `cli/` directory.                           |
| `pulse_interactive_shell.py`        | `cli/interactive_shell.py`                              | Interactive shell for Pulse. Moved to `cli/` directory.                   |
| `pulse_tkinter_ui.py`               | `pulse_desktop/tkinter_ui.py`                           | Tkinter UI code, belongs with other desktop UI components.                |
| `pulse_ui_operator.py`              | `pulse_desktop/ui_operator.py`                          | UI operator component, belongs with other desktop UI components.          |
| `pulse_ui_shell.py`                 | `pulse_desktop/ui_shell.py`                             | UI shell component, belongs with other desktop UI components.             |
| `service_registry.py`               | `core/service_registry.py`                              | Core service registry, fits well within the existing `core/` module.      |

### Category 3: Test Files

| Current Path                        | Proposed New Path                                       | Reasoning                                                                 |
| :---------------------------------- | :------------------------------------------------------ | :------------------------------------------------------------------------ |
| `test_incremental_ingestion.py`     | `tests/ingestion/test_incremental_ingestion.py`         | Test for incremental ingestion, moved to a new `tests/ingestion/` subdir. |
| `test_ingestion_changes.py`         | `tests/ingestion/test_ingestion_changes.py`         | Test for ingestion changes, moved to `tests/ingestion/` subdir.       |
| `test_nasdaq_plugin.py`             | `tests/plugins/test_nasdaq_plugin.py`                   | Test for NASDAQ plugin, moved to a new `tests/plugins/` subdir.         |
| `test_retriever.py`                 | `tests/retrieval/test_retriever.py`                     | Test for data retriever, moved to a new `tests/retrieval/` subdir.      |

### Category 4: Documentation & Reports

| Current Path                                      | Proposed New Path                                                           | Reasoning                                                                 |
| :------------------------------------------------ | :-------------------------------------------------------------------------- | :------------------------------------------------------------------------ |
| `historical_retrodiction_plan.md`                 | `docs/planning/historical_retrodiction_plan.md`                             | Planning document for historical retrodiction.                            |
| `pulse_ui_design_rev1.md`                         | `docs/ui/pulse_ui_design_rev1.md`                                           | UI design document.                                                       |
| `retrodiction_benchmark_report.md`                | `reports/benchmarking/retrodiction_benchmark_report.md`                     | Benchmark report, moved to a new top-level `reports/` directory.        |
| `retrodiction_optimization_benchmark_report.md`   | `reports/benchmarking/retrodiction_optimization_benchmark_report.md`        | Benchmark report, moved to `reports/benchmarking/`.                       |

### Category 5: Data / Output Files

| Current Path                              | Proposed New Path                                                 | Reasoning                                                                 |
| :---------------------------------------- | :---------------------------------------------------------------- | :------------------------------------------------------------------------ |
| `benchmark_results.json`                  | `data/benchmarks/benchmark_results.json`                          | Benchmark results data.                                                   |
| `new_optimized_benchmark_results.json`    | `data/benchmarks/new_optimized_benchmark_results.json`            | Benchmark results data.                                                   |
| `optimized_benchmark_results.json`        | `data/benchmarks/optimized_benchmark_results.json`                | Benchmark results data.                                                   |
| `historical_timeline.json`                | `data/historical/historical_timeline.json`                        | Historical timeline data.                                                 |
| `retrodiction_latest.json`                | `forecast_output/retrodiction/retrodiction_latest.json`           | Latest retrodiction output.                                               |
| `symbol_index.json`                       | `data/indices/symbol_index.json`                                  | Index of symbols.                                                         |

### Category 6: Other Configuration/Definition Files

| Current Path                        | Proposed New Path                                       | Reasoning                                                                 |
| :---------------------------------- | :------------------------------------------------------ | :------------------------------------------------------------------------ |
| `dependency_graph.dot`              | `diagnostics/dependency_graph.dot`                      | Graphviz dependency graph, suitable for `diagnostics/`.                   |

## Summary of New Proposed Directories

The following new directories will be created to house the moved files:

*   `api/`
*   `cli/`
*   `data/benchmarks/`
*   `data/historical/`
*   `data/indices/`
*   `dev_tools/analysis/`
*   `dev_tools/testing/`
*   `dev_tools/utils/`
*   `docs/planning/`
*   `docs/ui/`
*   `forecast_output/retrodiction/`
*   `reports/`
*   `reports/benchmarking/`
*   `scripts/analysis/`
*   `scripts/benchmarking/`
*   `scripts/data_management/`
*   `scripts/launchers/`
*   `scripts/legacy/`
*   `scripts/reporting/`
*   `tests/ingestion/`
*   `tests/plugins/`
*   `tests/retrieval/`

## Next Steps

1.  **Review and Approval:** Please review this plan.
2.  **Execution (If Approved):**
    *   Create the new directories.
    *   Move the files to their new locations. This will likely be done by requesting a switch to "Code" mode for efficient file operations.
    *   For each Python file moved:
        *   Use `search_files` to identify all files that import it.
        *   Use `read_file` to get the exact content of import lines in dependent files.
        *   Use `apply_diff` to update the import paths in those dependent files.
3.  **Verification:** After changes, run tests and linters to ensure the project remains functional.

This reorganization is a significant step towards a cleaner and more maintainable codebase.