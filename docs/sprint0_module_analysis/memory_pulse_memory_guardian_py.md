# Module Analysis: `memory/pulse_memory_guardian.py`

## 1. Module Intent/Purpose

The primary role of the [`memory/pulse_memory_guardian.py`](memory/pulse_memory_guardian.py:1) module is to manage the lifecycle of forecast memory. This includes responsibilities such as pruning older or less relevant forecasts, archiving variable data ("fossils"), managing the status of variables (soft retirement, reconsideration), and ensuring the coherence of forecasts stored in memory.

## 2. Operational Status/Completeness

The module appears partially operational.
- Core pruning functionalities like [`prune_memory()`](memory/pulse_memory_guardian.py:17) (by count) and [`prune_memory_advanced()`](memory/pulse_memory_guardian.py:82) (by count or confidence) seem implemented.
- The function [`prune_incoherent_forecasts()`](memory/pulse_memory_guardian.py:64) is implemented and utilizes the [`TrustEngine`](trust_system/trust_engine.py:1) for coherence checks.
- Functions related to variable lifecycle management such as [`archive_variable_fossil()`](memory/pulse_memory_guardian.py:31), [`soft_retire_variable()`](memory/pulse_memory_guardian.py:43), and [`reconsider_variable()`](memory/pulse_memory_guardian.py:54) are currently stubs. They log intended actions but lack actual persistence or status update logic (commented as "// Stub: Replace with actual ... logic").

## 3. Implementation Gaps / Unfinished Next Steps

-   **Persistence for Archiving:** The [`archive_variable_fossil()`](memory/pulse_memory_guardian.py:31) function explicitly states, "In a real implementation, this would persist to disk or a database." This persistence logic is missing.
-   **Status Update Logic:** Both [`soft_retire_variable()`](memory/pulse_memory_guardian.py:43) and [`reconsider_variable()`](memory/pulse_memory_guardian.py:54) have "Stub: Replace with actual status update logic" or "Stub: Replace with actual reconsideration logic" comments, indicating these are incomplete.
-   **Symbolic Regime Definition:** The [`reconsider_variable()`](memory/pulse_memory_guardian.py:54) function takes a `regime` parameter, but the concept and application of different "symbolic regimes" are not defined or utilized further within this module. This suggests a planned, more extensive feature that is not fully developed.
-   **Detailed Configuration:** While `max_entries` and `min_confidence` are configurable, more sophisticated pruning strategies (e.g., based on forecast utility, error rates, or specific variable importance) could be future enhancements.

## 4. Connections & Dependencies

### Direct Project Module Imports:
-   [`memory.forecast_memory.ForecastMemory`](memory/forecast_memory.py:1): Used as the primary object type for memory manipulation.
-   [`trust_system.trust_engine.TrustEngine`](trust_system/trust_engine.py:1): Used by [`prune_incoherent_forecasts()`](memory/pulse_memory_guardian.py:64) to check forecast coherence.

### External Library Dependencies:
-   `logging`: Standard Python library for logging.
-   `typing.List`, `typing.Dict`, `typing.Any`: Standard Python library for type hinting.

### Interaction with Other Modules via Shared Data:
-   Directly modifies instances of `ForecastMemory` by accessing and altering their `_memory` attribute (a list of forecast dictionaries).
-   The stubbed functions ([`archive_variable_fossil()`](memory/pulse_memory_guardian.py:31), etc.) imply future interaction with a persistent storage system (disk/database) that other modules might also access.

### Input/Output Files:
-   **Input:** None directly from files. Operates on in-memory `ForecastMemory` objects.
-   **Output:**
    -   Logs information using the standard `logging` module.
    -   The [`archive_variable_fossil()`](memory/pulse_memory_guardian.py:31) function is intended to output data to persistent storage, but this is currently a stub.

## 5. Function and Class Example Usages

-   **Pruning memory by entry count:**
    ```python
    from memory.forecast_memory import ForecastMemory
    from memory.pulse_memory_guardian import prune_memory

    fm = ForecastMemory()
    # populate fm with forecasts
    prune_memory(fm, max_entries=500, dry_run=False)
    ```

-   **Pruning memory by confidence:**
    ```python
    from memory.forecast_memory import ForecastMemory
    from memory.pulse_memory_guardian import prune_memory_advanced

    fm = ForecastMemory()
    # populate fm with forecasts that have a "confidence" key
    prune_memory_advanced(fm, min_confidence=0.75, dry_run=False)
    ```

-   **Pruning incoherent forecasts:**
    ```python
    from memory.pulse_memory_guardian import prune_incoherent_forecasts

    # memory_batch is a list of forecast dictionaries
    forecast_batch = [
        {"trace_id": "abc", "value": 10, "confidence": 0.9},
        {"trace_id": "def", "value": 20, "confidence": 0.5},
    ]
    retained_forecasts = prune_incoherent_forecasts(forecast_batch, verbose=True)
    ```
-   **Archiving a variable (conceptual):**
    ```python
    from memory.pulse_memory_guardian import archive_variable_fossil

    variable_data = {"last_value": 123, "update_time": "2023-01-01T10:00:00Z"}
    archive_variable_fossil("my_variable", variable_data, dry_run=True)
## 6. Hardcoding Issues

-   **Default `max_entries`:** The [`prune_memory()`](memory/pulse_memory_guardian.py:17) and [`prune_memory_advanced()`](memory/pulse_memory_guardian.py:82) functions use a default `max_entries` value of `1000`. While configurable, this default might not be optimal for all use cases.
-   **Default `regime`:** The [`reconsider_variable()`](memory/pulse_memory_guardian.py:54) function has a hardcoded default `regime="alternate"`. The meaning and implications of this regime are not defined in the module.
-   **Logging Prefixes:** String literals like `"[MemoryGuardian]"` and `"[Guardian]"` are used in logging messages. These are not configurable.
-   **Confidence Key:** The [`prune_memory_advanced()`](memory/pulse_memory_guardian.py:82) function hardcodes the lookup of forecast confidence using `f.get("confidence", 0)`. If the confidence field has a different name, this will fail or use the default.

## 7. Coupling Points

-   **`ForecastMemory` Internals:** The pruning functions ([`prune_memory()`](memory/pulse_memory_guardian.py:17), [`prune_memory_advanced()`](memory/pulse_memory_guardian.py:82)) are tightly coupled to the internal implementation of [`ForecastMemory`](memory/forecast_memory.py:1), specifically by directly accessing and slicing its `_memory` attribute (`memory._memory = memory._memory[-max_entries:]`). Changes to `ForecastMemory`'s internal storage could break this module.
-   **`TrustEngine` Dependency:** [`prune_incoherent_forecasts()`](memory/pulse_memory_guardian.py:64) directly calls [`TrustEngine.check_forecast_coherence()`](trust_system/trust_engine.py:1). Any changes to the API or behavior of this static method in `TrustEngine` could impact the guardian.
-   **Forecast Dictionary Structure:** Functions like [`prune_incoherent_forecasts()`](memory/pulse_memory_guardian.py:64) (accessing `forecast.get('trace_id')`) and [`prune_memory_advanced()`](memory/pulse_memory_guardian.py:82) (accessing `f.get("confidence", 0)`) assume a certain dictionary structure for forecast objects.

## 8. Existing Tests

-   A specific test file named `test_pulse_memory_guardian.py` was **not found** in the `tests/` directory.
-   The file [`tests/test_forecast_memory.py`](tests/test_forecast_memory.py:1) exists, which might indirectly test some aspects of memory pruning if `ForecastMemory` itself uses these guardian functions, or if its tests involve scenarios where memory limits are reached.
-   However, dedicated unit tests for the specific logic within `pulse_memory_guardian.py` are likely missing. This includes:
    -   Testing `dry_run=True` vs. `dry_run=False` behavior for all relevant functions.
    -   Testing pruning by `min_confidence` in [`prune_memory_advanced()`](memory/pulse_memory_guardian.py:82).
    -   Testing the behavior of [`prune_incoherent_forecasts()`](memory/pulse_memory_guardian.py:64) with various coherence statuses.
    -   Testing the logging output of the stubbed functions ([`archive_variable_fossil()`](memory/pulse_memory_guardian.py:31), [`soft_retire_variable()`](memory/pulse_memory_guardian.py:43), [`reconsider_variable()`](memory/pulse_memory_guardian.py:54)).

## 9. Module Architecture and Flow

-   The module is structured as a collection of utility functions rather than classes.
-   **Memory Pruning Flow:**
    -   [`prune_memory()`](memory/pulse_memory_guardian.py:17): Calculates excess entries in a `ForecastMemory` object and, if not a dry run, truncates the internal `_memory` list to the `max_entries`.
    -   [`prune_memory_advanced()`](memory/pulse_memory_guardian.py:82): If `min_confidence` is provided, it filters the `_memory` list to keep forecasts meeting the confidence threshold. Otherwise, it defers to [`prune_memory()`](memory/pulse_memory_guardian.py:17).
-   **Variable Lifecycle Management Flow (Conceptual/Stubs):**
    -   [`archive_variable_fossil()`](memory/pulse_memory_guardian.py:31), [`soft_retire_variable()`](memory/pulse_memory_guardian.py:43), [`reconsider_variable()`](memory/pulse_memory_guardian.py:54): These functions currently only log their intent. In a full implementation, they would interact with a persistence layer or status tracking system.
-   **Coherence Pruning Flow:**
    -   [`prune_incoherent_forecasts()`](memory/pulse_memory_guardian.py:64): Iterates through a batch of forecast dictionaries, calls [`TrustEngine.check_forecast_coherence()`](trust_system/trust_engine.py:1) for each, and appends forecasts that pass the check to a `retained` list. Logs issues for pruned forecasts if `verbose` is true.

## 10. Naming Conventions

-   **Module Name:** [`pulse_memory_guardian.py`](memory/pulse_memory_guardian.py:1) is descriptive.
-   **Function Names:** Generally follow PEP 8 (snake_case) and are descriptive of their actions (e.g., [`prune_memory()`](memory/pulse_memory_guardian.py:17), [`archive_variable_fossil()`](memory/pulse_memory_guardian.py:31)).
-   **Variable Names:** Mostly clear and follow PEP 8 (e.g., `max_entries`, `dry_run`, `min_confidence`).
-   **Logging Prefixes:** Consistent use of `"[MemoryGuardian]"` or `"[Guardian]"` in log messages helps identify the source of the log entry.
-   No obvious AI assumption errors or significant deviations from PEP 8 were noted.