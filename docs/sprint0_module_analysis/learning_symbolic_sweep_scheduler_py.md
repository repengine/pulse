# Module Analysis: `learning/symbolic_sweep_scheduler.py`

## 1. Module Intent/Purpose

The primary role of the [`learning/symbolic_sweep_scheduler.py`](learning/symbolic_sweep_scheduler.py) module is to periodically re-process forecasts that were previously blocked, attempting to recover them based on updated logic or criteria. Its key responsibilities include:
- Loading forecasts marked as "blocked."
- Retrying the licensing process for these forecasts.
- Scoring the newly recovered forecasts.
- Flagging any recovered forecasts that are still unstable.
- Exporting recovered and flagged forecasts to designated log files.
- Maintaining a log of sweep operations and their outcomes.

## 2. Operational Status/Completeness

The module appears to be functionally complete for its defined scope. It provides two main functions: one to execute the sweep process ([`run_sweep_now()`](learning/symbolic_sweep_scheduler.py:36)) and another to summarize past sweep logs ([`summarize_sweep_log()`](learning/symbolic_sweep_scheduler.py:69)). There are no explicit `TODO` comments or obvious placeholders in the code, suggesting that the implemented features are considered complete.

## 3. Implementation Gaps / Unfinished Next Steps

- **Automation:** The module's name includes "scheduler," implying automated execution. However, the current implementation only provides a function ([`run_sweep_now()`](learning/symbolic_sweep_scheduler.py:36)) for manual triggering. Integration with an actual scheduling mechanism (e.g., cron, Airflow) is a potential next step.
- **Configuration Management:** Log file paths are hardcoded as constants (e.g., [`SWEEP_LOG_PATH`](learning/symbolic_sweep_scheduler.py:31), [`BLOCKED_LOG_PATH`](learning/symbolic_sweep_scheduler.py:32)). Moving these to a configuration file or environment variables would improve flexibility.
- **Error Handling:** Error handling is basic, primarily relying on `print` statements for exceptions (e.g., [`learning/symbolic_sweep_scheduler.py:64`](learning/symbolic_sweep_scheduler.py:64), [`learning/symbolic_sweep_scheduler.py:78`](learning/symbolic_sweep_scheduler.py:78)). For a production environment, more robust error logging, notification, or retry mechanisms might be necessary.
- **Extensibility of Summary:** The [`summarize_sweep_log()`](learning/symbolic_sweep_scheduler.py:69) function currently shows only the last 5 entries ([`learning/symbolic_sweep_scheduler.py:75`](learning/symbolic_sweep_scheduler.py:75)). This could be made configurable.

## 4. Connections & Dependencies

### Direct Project Module Imports:
- [`memory.memory_repair_queue`](memory/memory_repair_queue.py):
    - [`load_blocked_memory()`](memory/memory_repair_queue.py)
    - [`retry_licensing()`](memory/memory_repair_queue.py)
    - [`export_recovered()`](memory/memory_repair_queue.py)
- [`trust_system.recovered_forecast_scorer`](trust_system/recovered_forecast_scorer.py):
    - [`score_recovered_forecasts()`](trust_system/recovered_forecast_scorer.py)
    - [`flag_unstable_forecasts()`](trust_system/recovered_forecast_scorer.py)
    - [`summarize_repair_quality()`](trust_system/recovered_forecast_scorer.py)
    - [`export_flagged_for_revision()`](trust_system/recovered_forecast_scorer.py)

### External Library Dependencies:
- `json`
- `os`
- `datetime`
- `typing` (List, Dict)

### Interaction via Shared Data (Files):
The module interacts with other parts of the system through JSONL log files:
- **Input:**
    - Reads blocked forecasts from [`logs/blocked_memory_log.jsonl`](logs/blocked_memory_log.jsonl) (defined by [`BLOCKED_LOG_PATH`](learning/symbolic_sweep_scheduler.py:32)).
- **Output:**
    - Writes recovered forecasts to [`logs/sweep_recovered_forecasts.jsonl`](logs/sweep_recovered_forecasts.jsonl) (defined by [`RECOVERED_OUTPUT_PATH`](learning/symbolic_sweep_scheduler.py:33)).
    - Writes a summary of each sweep operation to [`logs/symbolic_sweep_log.jsonl`](logs/symbolic_sweep_log.jsonl) (defined by [`SWEEP_LOG_PATH`](learning/symbolic_sweep_scheduler.py:31)).
    - Writes forecasts flagged for revision to [`logs/unresolved_forecasts.jsonl`](logs/unresolved_forecasts.jsonl) (hardcoded path in [`run_sweep_now()`](learning/symbolic_sweep_scheduler.py:49)).

## 5. Function and Class Example Usages

### [`run_sweep_now(export: str = RECOVERED_OUTPUT_PATH) -> Dict`](learning/symbolic_sweep_scheduler.py:36)
This function executes the symbolic sweep process. It loads blocked forecasts, attempts to recover them by retrying the licensing process, scores them, flags unstable ones, summarizes the repair quality, and exports various results to log files.
```python
# Example Usage:
# from learning.symbolic_sweep_scheduler import run_sweep_now

# Run sweep with default output path
results = run_sweep_now()
print(f"Sweep completed. Recovered: {results.get('recovered_count', 0)}")

# Run sweep with custom output path for recovered forecasts
custom_path = "custom_logs/my_recovered_forecasts.jsonl"
results_custom = run_sweep_now(export=custom_path)
print(f"Sweep completed. Output at: {results_custom.get('output_path')}")
```

### [`summarize_sweep_log(path: str = SWEEP_LOG_PATH)`](learning/symbolic_sweep_scheduler.py:69)
This function reads the sweep log file and prints a summary of the last few sweep operations, showing timestamps and recovery counts.
```python
# Example Usage:
# from learning.symbolic_sweep_scheduler import summarize_sweep_log

# Summarize the default sweep log
summarize_sweep_log()

# Summarize a custom sweep log file
# summarize_sweep_log(path="custom_logs/custom_sweep_log.jsonl")
```

## 6. Hardcoding Issues

- **Log File Paths:**
    - [`SWEEP_LOG_PATH = "logs/symbolic_sweep_log.jsonl"`](learning/symbolic_sweep_scheduler.py:31)
    - [`BLOCKED_LOG_PATH = "logs/blocked_memory_log.jsonl"`](learning/symbolic_sweep_scheduler.py:32)
    - [`RECOVERED_OUTPUT_PATH = "logs/sweep_recovered_forecasts.jsonl"`](learning/symbolic_sweep_scheduler.py:33)
    - The output path for unresolved forecasts, `"logs/unresolved_forecasts.jsonl"`, is hardcoded directly in the call to [`export_flagged_for_revision()`](learning/symbolic_sweep_scheduler.py:49).
- **Magic Strings/Values:**
    - The string `"symbolic_sweep"` is assigned to `fc["repair_source"]` ([`learning/symbolic_sweep_scheduler.py:42`](learning/symbolic_sweep_scheduler.py:42)) to tag the origin of the repair.
    - The number of log entries to summarize in [`summarize_sweep_log()`](learning/symbolic_sweep_scheduler.py:69) is hardcoded to `5` ([`learning/symbolic_sweep_scheduler.py:75`](learning/symbolic_sweep_scheduler.py:75)).

## 7. Coupling Points

- **High Coupling with `memory.memory_repair_queue`:** The module heavily relies on functions from [`memory.memory_repair_queue`](memory/memory_repair_queue.py) for core operations like loading blocked memory, retrying licensing, and exporting results. Changes to the API or data structures in `memory_repair_queue` would directly necessitate changes in this scheduler.
- **High Coupling with `trust_system.recovered_forecast_scorer`:** Similarly, the module is tightly coupled with [`trust_system.recovered_forecast_scorer`](trust_system/recovered_forecast_scorer.py) for scoring, flagging, and summarizing the quality of recovered forecasts.
- **File-Based Data Exchange:** The reliance on specific JSONL file paths and formats for input and output creates coupling with any other processes that produce or consume these files.

## 8. Existing Tests

No dedicated test file (e.g., `tests/learning/test_symbolic_sweep_scheduler.py`) was found in the `tests/learning/` directory. This indicates a lack of unit tests for this module, which is a significant gap for ensuring its reliability and maintainability.

## 9. Module Architecture and Flow

The module is procedural and consists of two main functions:

- **[`run_sweep_now()`](learning/symbolic_sweep_scheduler.py:36):**
    1. Loads blocked forecasts using [`load_blocked_memory()`](memory/memory_repair_queue.py).
    2. Attempts to recover forecasts via [`retry_licensing()`](memory/memory_repair_queue.py).
    3. Tags each recovered forecast with `repair_source = "symbolic_sweep"`.
    4. Exports these forecasts using [`export_recovered()`](memory/memory_repair_queue.py).
    5. Scores the recovered forecasts using [`score_recovered_forecasts()`](trust_system/recovered_forecast_scorer.py).
    6. Flags unstable forecasts using [`flag_unstable_forecasts()`](trust_system/recovered_forecast_scorer.py).
    7. Generates a quality summary using [`summarize_repair_quality()`](trust_system/recovered_forecast_scorer.py) (and prints it).
    8. Exports flagged forecasts using [`export_flagged_for_revision()`](trust_system/recovered_forecast_scorer.py).
    9. Constructs a result dictionary containing sweep statistics.
    10. Appends this result to the [`SWEEP_LOG_PATH`](learning/symbolic_sweep_scheduler.py:31).
    11. Returns the result dictionary.

- **[`summarize_sweep_log()`](learning/symbolic_sweep_scheduler.py:69):**
    1. Reads and parses entries from the [`SWEEP_LOG_PATH`](learning/symbolic_sweep_scheduler.py:31).
    2. Prints a summary of the last five sweep operations, including timestamps and recovery statistics.

## 10. Naming Conventions

- **Variables:** Generally follow Python's `snake_case` convention (e.g., `blocked_memory`, `recovered_forecasts`).
- **Functions:** Use `snake_case` (e.g., [`run_sweep_now`](learning/symbolic_sweep_scheduler.py:36), [`summarize_sweep_log`](learning/symbolic_sweep_scheduler.py:69)).
- **Constants:** Use `UPPER_SNAKE_CASE` (e.g., [`SWEEP_LOG_PATH`](learning/symbolic_sweep_scheduler.py:31)).
- The naming is generally clear and consistent with PEP 8 guidelines. The module name itself, [`symbolic_sweep_scheduler.py`](learning/symbolic_sweep_scheduler.py), is descriptive.
- The initial comment `# scheduler/symbolic_sweep_scheduler.py` ([`learning/symbolic_sweep_scheduler.py:1`](learning/symbolic_sweep_scheduler.py:1)) might indicate a previous or intended file location, but the current location is `learning/`.