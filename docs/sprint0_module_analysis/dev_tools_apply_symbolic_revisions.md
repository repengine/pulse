# Module Analysis: `dev_tools/apply_symbolic_revisions.py`

**Last Updated:** 2025-05-15

## 1. Module Intent/Purpose

The module [`dev_tools/apply_symbolic_revisions.py`](dev_tools/apply_symbolic_revisions.py:1) is a command-line interface (CLI) tool designed to apply symbolic revisions to a batch of forecasts. It takes a set of input forecasts (in JSONL format) and a corresponding set of revision plans (in JSON format), simulates the revised forecasts, compares their scores against the originals, and logs the results of this tuning process.

## 2. Operational Status/Completeness

-   **Operational:** The module appears to be operational for its core purpose. It can load forecast and plan files, iterate through them, apply revisions using imported functions, compare scores, and log results.
-   **Completeness:**
    -   The core workflow of loading data, processing revisions, and logging seems complete.
    -   Error handling is present for file loading and individual forecast processing, printing messages to the console.
    -   It relies on external functions ([`simulate_revised_forecast`](forecast_output/symbolic_tuning_engine.py:1), [`compare_scores`](forecast_output/symbolic_tuning_engine.py:1), [`log_tuning_result`](forecast_output/symbolic_tuning_engine.py:1)) from [`forecast_output.symbolic_tuning_engine`](forecast_output/symbolic_tuning_engine.py:1) for the actual revision, scoring, and detailed logging logic.

## 3. Implementation Gaps / Unfinished Next Steps

-   **Advanced Error Handling:** While basic error messages are printed, more sophisticated error handling or reporting (e.g., writing to an error log file, summarizing errors at the end) could be beneficial, especially for large batches.
-   **Configuration:** File paths are passed as CLI arguments. There's no apparent support for configuration files for default paths or other operational parameters.
-   **Output of Revised Forecasts:** The function [`apply_symbolic_revisions()`](dev_tools/apply_symbolic_revisions.py:33) returns a list of revised forecasts, but the [`main()`](dev_tools/apply_symbolic_revisions.py:79) function (CLI entry point) does not do anything with this returned list (e.g., save to a new file). This seems like a significant gap if the user intends to persist the revised forecasts.
-   **Selective Processing:** No mechanism to process only a subset of forecasts based on criteria other than the presence of a plan.

## 4. Connections & Dependencies

-   **Internal Dependencies:**
    -   [`forecast_output.symbolic_tuning_engine`](forecast_output/symbolic_tuning_engine.py:1): Imports [`simulate_revised_forecast()`](forecast_output/symbolic_tuning_engine.py:1), [`compare_scores()`](forecast_output/symbolic_tuning_engine.py:1), and [`log_tuning_result()`](forecast_output/symbolic_tuning_engine.py:1). This is a critical dependency for its core functionality.
-   **Standard Library Dependencies:**
    -   `argparse`: For command-line argument parsing.
    -   `json`: For loading JSON and JSONL data.
    -   `os`: Specifically `os.path.isfile` for checking file existence.
    -   `typing`: For type hints (`List`, `Dict`, `Any`).
-   **External Data:**
    -   Relies on input forecast files (JSONL format).
    -   Relies on input revision plan files (JSON format).

## 5. Function and Class Example Usages

The module is primarily used as a CLI tool.

**CLI Usage Example:**

```bash
python dev_tools/apply_symbolic_revisions.py --batch path/to/forecast_batch.jsonl --plans path/to/revision_plans.json
```

**Function Usage Example (within Python):**

```python
from dev_tools.apply_symbolic_revisions import apply_symbolic_revisions

batch_file = "inputs/forecast_candidates.jsonl"
plans_file = "inputs/symbolic_revision_plans.json"

# Assuming forecast_candidates.jsonl contains:
# {"trace_id": "trace1", "score": 0.5, "data": "original_data1"}
# {"trace_id": "trace2", "score": 0.7, "data": "original_data2"}

# Assuming symbolic_revision_plans.json contains:
# [
#   {"trace_id": "trace1", "plan": {"action": "modify", "param": "value1"}},
#   {"trace_id": "trace3", "plan": {"action": "modify", "param": "value3"}}
# ]

revised_forecasts_list = apply_symbolic_revisions(batch_path=batch_file, plans_path=plans_file)

# revised_forecasts_list would contain the revised forecast for "trace1"
# A warning would be printed for "trace2" (no plan)
# An error/warning might be printed if "trace3" is not in the batch.
# The function would print progress and score deltas to stdout.
# The actual revised forecasts are returned but not saved by default by the CLI.
```

## 6. Hardcoding Issues

-   No critical hardcoding of secrets or API keys was observed.
-   File paths for forecasts and plans are provided via CLI arguments, which is appropriate for a tool of this nature.
-   Error messages and log messages are hardcoded strings (e.g., "❌ File not found:", "🔁 {trace} → {delta}"). This is generally acceptable for CLI tool console output.

## 7. Coupling Points

-   **High Coupling:** Tightly coupled to the functions and expected data structures of [`forecast_output.symbolic_tuning_engine`](forecast_output/symbolic_tuning_engine.py:1). Changes in that module's API or behavior would directly impact this script.
-   **Data Format Coupling:** Tightly coupled to the expected JSON/JSONL structure of the input forecast batch and revision plan files. Specifically, it expects `trace_id` fields for matching forecasts to plans.

## 8. Existing Tests

-   No dedicated unit tests or integration tests were found within the project structure for this specific module (e.g., in a `tests/dev_tools/` directory or `tests/test_apply_symbolic_revisions.py`).
-   The module itself does not contain inline tests.

## 9. Module Architecture and Flow

-   **Architecture:** Simple script-based architecture.
    -   A [`load_jsonl()`](dev_tools/apply_symbolic_revisions.py:22) helper function for reading JSONL files.
    -   A main processing function [`apply_symbolic_revisions()`](dev_tools/apply_symbolic_revisions.py:33) that orchestrates loading, iteration, revision application, scoring, and logging.
    -   A [`main()`](dev_tools/apply_symbolic_revisions.py:79) function that handles CLI argument parsing and calls the processing function.
-   **Flow:**
    1.  Parse CLI arguments (`--batch`, `--plans`).
    2.  Call [`apply_symbolic_revisions()`](dev_tools/apply_symbolic_revisions.py:33).
        a.  Validate that `batch_path` and `plans_path` are provided.
        b.  Load forecasts from `batch_path` using [`load_jsonl()`](dev_tools/apply_symbolic_revisions.py:22). Handle file not found or load errors.
        c.  Load revision plans from `plans_path` (JSON). Handle file not found or load errors.
        d.  Iterate through each forecast in the loaded batch:
            i.  Get the `trace_id` from the forecast.
            ii. Find the corresponding revision plan based on `trace_id`.
            iii. If no plan is found, print a warning and skip.
            iv. Attempt to:
                1.  Call [`simulate_revised_forecast()`](forecast_output/symbolic_tuning_engine.py:1) with the original forecast and plan.
                2.  Call [`compare_scores()`](forecast_output/symbolic_tuning_engine.py:1) between original and revised forecast.
                3.  Print the trace ID and score delta.
                4.  Add the `revision_plan` to the revised forecast dictionary.
                5.  Call [`log_tuning_result()`](forecast_output/symbolic_tuning_engine.py:1) with original and revised forecast. Handle logging errors.
                6.  Append the revised forecast to `revised_forecasts` list.
            v.  Catch any exceptions during this processing block, print an error, and continue to the next forecast.
        e.  Print a summary of how many forecasts were revised.
        f.  Return the `revised_forecasts` list.
    3.  The CLI's [`main()`](dev_tools/apply_symbolic_revisions.py:79) function does not currently utilize the returned list.

## 10. Naming Conventions

-   Python naming conventions (snake_case for functions and variables) are generally followed (e.g., [`apply_symbolic_revisions`](dev_tools/apply_symbolic_revisions.py:33), `batch_path`, `revised_forecasts`).
-   Constants are not explicitly defined, but local variables serve their purpose.

## 11. SPARC Analysis

-   **Specification:** The module's intent as a CLI tool for applying revisions is clear from its docstrings and argument parser.
-   **Project Context & Understanding:** It fits within a larger system involving forecasts, symbolic tuning, and scoring, as evidenced by its imports.
-   **Architecture Adherence:** Appears to be a utility script, likely adhering to a tools-based architecture.
-   **Modularity:**
    -   Good: Delegates core revision, scoring, and detailed logging logic to [`forecast_output.symbolic_tuning_engine`](forecast_output/symbolic_tuning_engine.py:1).
    -   Could be improved: The file loading logic ([`load_jsonl()`](dev_tools/apply_symbolic_revisions.py:22)) is specific to this module but could potentially be a shared utility if similar JSONL loading is needed elsewhere.
-   **Maintainability:**
    -   The code is relatively straightforward and readable.
    -   Lack of tests reduces confidence in making changes.
    -   The fact that the CLI doesn't save the output of revised forecasts might be a maintenance oversight or an indication of incomplete specification.
-   **Testability:**
    -   Poor: No dedicated tests.
    -   The main function [`apply_symbolic_revisions()`](dev_tools/apply_symbolic_revisions.py:33) could be unit-tested by mocking file system operations and the imported `symbolic_tuning_engine` functions.
-   **Security:** No direct handling of sensitive information or external network calls observed beyond file I/O. Assumes input files are trusted.
-   **Hardcoding:** Minimal and mostly related to console messages. No critical hardcoding.
-   **Clarity & Readability:** Good. Code is well-commented with docstrings and inline comments where appropriate. Print statements provide good feedback on progress and errors.
-   **Error Handling:** Basic error handling is present (file not found, JSON parsing errors, errors during revision processing). Errors are printed to `stdout`. More robust error aggregation or logging to a file could be an improvement for batch operations.

## Summary Note for Main Report

The [`dev_tools/apply_symbolic_revisions.py`](dev_tools/apply_symbolic_revisions.py:1) module is a CLI tool for applying symbolic revision plans to forecast batches, simulating changes, and logging score comparisons. It relies on [`forecast_output.symbolic_tuning_engine`](forecast_output/symbolic_tuning_engine.py:1) for core logic but lacks dedicated tests and currently does not persist the generated revised forecasts.