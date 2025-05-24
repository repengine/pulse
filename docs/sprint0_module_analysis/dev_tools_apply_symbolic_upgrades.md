# Module Analysis: `dev_tools/apply_symbolic_upgrades.py`

**Last Updated:** 2025-05-15

## 1. Module Intent/Purpose

The module [`dev_tools/apply_symbolic_upgrades.py`](dev_tools/apply_symbolic_upgrades.py:1) is a command-line interface (CLI) tool designed to apply a symbolic upgrade plan to an entire batch of forecasts. It loads a batch of forecasts (JSONL) and a single upgrade plan (JSON), then uses functions from [`symbolic_system.symbolic_executor`](symbolic_system/symbolic_executor.py:1) to rewrite the symbolics of all forecasts according to the plan. The rewritten forecasts are then saved to an output file (JSONL), and each mutation is logged.

## 2. Operational Status/Completeness

-   **Operational:** The module appears to be operational for its core purpose of loading data, applying a blanket symbolic upgrade, logging mutations, and saving the results.
-   **Completeness:**
    -   The primary workflow is complete.
    -   Error handling for file I/O and the rewrite process is present, printing messages to the console.
    -   It successfully utilizes external functions ([`rewrite_forecast_symbolics`](symbolic_system/symbolic_executor.py:3), [`log_symbolic_mutation`](symbolic_system/symbolic_executor.py:3)) for the core logic.
    -   Unlike `apply_symbolic_revisions.py`, this script *does* save the output by default.

## 3. Implementation Gaps / Unfinished Next Steps

-   **Advanced Error Handling:** Similar to `apply_symbolic_revisions.py`, error reporting is basic (console prints). For batch processes, a summary of errors or logging to a dedicated error file would be more robust.
-   **Configuration:** File paths are CLI arguments. No configuration file support for defaults.
-   **Granular Plan Application:** The current design applies one upgrade plan to all forecasts in the batch. There's no mechanism for applying different plans to different forecasts within the same batch run, or for conditional application based on forecast characteristics.
-   **Comparison/Scoring:** This module focuses only on applying upgrades and logging mutations. It does not perform any scoring or comparison between original and upgraded forecasts, which is a key difference from `apply_symbolic_revisions.py`. This might be intentional, with scoring handled as a separate step.

## 4. Connections & Dependencies

-   **Internal Dependencies:**
    -   [`symbolic_system.symbolic_executor`](symbolic_system/symbolic_executor.py:1): Imports [`rewrite_forecast_symbolics()`](symbolic_system/symbolic_executor.py:3) and [`log_symbolic_mutation()`](symbolic_system/symbolic_executor.py:3). This is critical for its functionality.
-   **Standard Library Dependencies:**
    -   `argparse`: For command-line argument parsing.
    -   `json`: For loading JSON and JSONL data, and for dumping JSON to the output file.
    -   `os`: Specifically `os.path.isfile` for checking file existence.
-   **External Data:**
    -   Relies on an input forecast batch file (JSONL format).
    -   Relies on an input upgrade plan file (JSON format, a single plan applied to all).
    -   Produces an output file with rewritten forecasts (JSONL format).

## 5. Function and Class Example Usages

The module is primarily used as a CLI tool.

**CLI Usage Example:**

```bash
python dev_tools/apply_symbolic_upgrades.py --batch path/to/forecast_batch.jsonl --plan path/to/upgrade_plan.json --out path/to/upgraded_forecasts.jsonl
```
If `--out` is not specified, it defaults to `revised_forecasts.jsonl` in the current working directory.

**Function Usage Example (within Python):**

```python
from dev_tools.apply_symbolic_upgrades import apply_symbolic_upgrades

batch_input_file = "inputs/forecast_batch_for_upgrade.jsonl"
upgrade_plan_file = "inputs/global_symbolic_upgrade.json"
output_file = "outputs/upgraded_batch.jsonl"

# Assuming forecast_batch_for_upgrade.jsonl contains:
# {"trace_id": "alpha", "symbolics": "old_expr1", "data": "data_A"}
# {"trace_id": "beta", "symbolics": "old_expr2", "data": "data_B"}

# Assuming global_symbolic_upgrade.json contains a plan like:
# {"upgrade_type": "replace_all", "target_symbol": "X", "replacement_symbol": "Y"}

upgraded_forecasts_list = apply_symbolic_upgrades(
    batch_path=batch_input_file,
    plan_path=upgrade_plan_file,
    out_path=output_file
)

# upgraded_forecasts_list would contain the forecasts with symbolics rewritten.
# The upgraded_batch.jsonl file would be created with these forecasts.
# Mutations would be logged via log_symbolic_mutation.
```

## 6. Hardcoding Issues

-   **Default Output Filename:** The default output path is hardcoded to `"revised_forecasts.jsonl"` ([`apply_symbolic_upgrades()`](dev_tools/apply_symbolic_upgrades.py:7) function signature and [`main()`](dev_tools/apply_symbolic_upgrades.py:60) argparse default). While overridable, a more descriptive default like `upgraded_forecasts.jsonl` might be better aligned with the module's purpose.
-   Error messages and log messages are hardcoded strings (e.g., "❌ Batch file not found:"). This is generally acceptable for CLI tool console output.
-   No critical hardcoding of secrets or API keys was observed.

## 7. Coupling Points

-   **High Coupling:** Tightly coupled to the API and expected behavior of [`rewrite_forecast_symbolics()`](symbolic_system/symbolic_executor.py:3) and [`log_symbolic_mutation()`](symbolic_system/symbolic_executor.py:3) from [`symbolic_system.symbolic_executor`](symbolic_system/symbolic_executor.py:1).
-   **Data Format Coupling:** Tightly coupled to the expected JSON/JSONL structure of the input forecast batch and the JSON structure of the upgrade plan.

## 8. Existing Tests

-   No dedicated unit tests or integration tests were found within the project structure for this specific module.
-   The module itself does not contain inline tests.

## 9. Module Architecture and Flow

-   **Architecture:** Simple script-based architecture.
    -   A main processing function [`apply_symbolic_upgrades()`](dev_tools/apply_symbolic_upgrades.py:7) that handles file loading, calls the rewrite function, logs mutations, and writes the output.
    -   A [`main()`](dev_tools/apply_symbolic_upgrades.py:56) function for CLI argument parsing and invoking the processing function.
-   **Flow:**
    1.  Parse CLI arguments (`--batch`, `--plan`, `--out`).
    2.  Call [`apply_symbolic_upgrades()`](dev_tools/apply_symbolic_upgrades.py:7).
        a.  Validate that `batch_path` and `plan_path` are provided.
        b.  Check if `batch_path` and `plan_path` files exist. Print error and return if not.
        c.  Load forecasts from `batch_path` (JSONL). Handle load errors.
        d.  Load the single upgrade plan from `plan_path` (JSON). Handle load errors.
        e.  Attempt to call [`rewrite_forecast_symbolics()`](symbolic_system/symbolic_executor.py:3) with all loaded forecasts and the single upgrade plan. Handle errors during rewrite.
        f.  Attempt to open `out_path` for writing:
            i.  Iterate through each rewritten forecast.
            ii. Write the forecast to the output file as a JSONL entry.
            iii. Attempt to call [`log_symbolic_mutation()`](symbolic_system/symbolic_executor.py:3) for the forecast. Handle logging errors.
        g.  Print success message with the output path.
        h.  Handle errors during file writing.
        i.  Return the list of rewritten forecasts.

## 10. Naming Conventions

-   Python naming conventions (snake_case for functions and variables) are generally followed (e.g., [`apply_symbolic_upgrades`](dev_tools/apply_symbolic_upgrades.py:7), `batch_path`, `plan_path`).
-   The argument `--plan` in `argparse` corresponds to `plan_path` in the function, which is clear.
-   The default output filename `revised_forecasts.jsonl` could be more specific (e.g., `upgraded_forecasts.jsonl`) to better reflect the module's "upgrade" terminology.

## 11. SPARC Analysis

-   **Specification:** The module's purpose as a CLI tool for applying a single upgrade plan to a batch of forecasts is clear.
-   **Project Context & Understanding:** Fits into a system that manages forecasts and their symbolic representations, allowing for bulk updates based on defined plans.
-   **Architecture Adherence:** Utility script architecture, delegating complex symbolic logic.
-   **Modularity:**
    -   Good: Core symbolic rewriting and mutation logging are delegated to [`symbolic_system.symbolic_executor`](symbolic_system/symbolic_executor.py:1).
    -   The file loading logic for JSONL is simple and self-contained.
-   **Maintainability:**
    -   The code is concise and relatively easy to follow.
    -   Lack of tests is a significant drawback for maintainability, making it harder to refactor or verify changes.
-   **Testability:**
    -   Poor: No dedicated tests.
    -   The main function [`apply_symbolic_upgrades()`](dev_tools/apply_symbolic_upgrades.py:7) could be unit-tested by mocking file system operations and the imported `symbolic_executor` functions.
-   **Security:** No direct handling of sensitive information. Assumes input files are trusted.
-   **Hardcoding:** The default output filename is hardcoded but overridable. Console messages are hardcoded. No critical hardcoding.
-   **Clarity & Readability:** Good. The script is short and its logic is straightforward.
-   **Error Handling:** Basic error handling for file operations and the rewrite process is present, with messages printed to `stdout`. Could be improved for batch processing with error summaries or dedicated log files.

## Summary Note for Main Report

The [`dev_tools/apply_symbolic_upgrades.py`](dev_tools/apply_symbolic_upgrades.py:1) module is a CLI tool that applies a single symbolic upgrade plan to an entire batch of forecasts, saving the rewritten forecasts and logging mutations. It depends on [`symbolic_system.symbolic_executor`](symbolic_system/symbolic_executor.py:1) for core operations and lacks dedicated tests.