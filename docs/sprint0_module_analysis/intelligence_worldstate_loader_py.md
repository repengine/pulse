# Module Analysis: `intelligence/worldstate_loader.py`

## 1. Module Intent/Purpose

The primary role of the [`intelligence/worldstate_loader.py`](intelligence/worldstate_loader.py:1) module is to provide a "minimal-impact" way to create and initialize a fully-populated `WorldState` object. This involves:
*   Reading baseline data from a CSV or JSON file.
*   Optionally injecting live data fetched via the `VariableIngestion` layer.
*   Allowing for overrides of specific `WorldState` parameters.
*   Validating the resulting `WorldState` against a `VariableRegistry` and reporting any missing variables.
*   Providing functionality to load a `WorldState` from historical snapshots.

## 2. Operational Status/Completeness

The module appears to be largely complete for its "Phase-1 features" as described in its docstring ([`intelligence/worldstate_loader.py:4-10`](intelligence/worldstate_loader.py:4)).
*   It reads baseline files (CSV/JSON) with a fallback mechanism ([`intelligence/worldstate_loader.py:59-68`](intelligence/worldstate_loader.py:59)).
*   It injects live variables if requested ([`intelligence/worldstate_loader.py:78-81`](intelligence/worldstate_loader.py:78)).
*   It validates and reports missing variables ([`intelligence/worldstate_loader.py:120-122`](intelligence/worldstate_loader.py:120)).
*   It supports loading historical snapshots ([`intelligence/worldstate_loader.py:130-244`](intelligence/worldstate_loader.py:130)).

There are no obvious `TODO` comments or major placeholders within the implemented functions. The "Future expansion" section in the docstring ([`intelligence/worldstate_loader.py:11-16`](intelligence/worldstate_loader.py:11)) clearly outlines features not yet implemented.

## 3. Implementation Gaps / Unfinished Next Steps

Based on the module's docstring and current implementation:

*   **Historical Snapshot Support (Retrodiction):** While a function [`load_historical_snapshot()`](intelligence/worldstate_loader.py:130) exists, the broader "retrodiction" capabilities mentioned as future expansion ([`intelligence/worldstate_loader.py:13`](intelligence/worldstate_loader.py:13)) are likely more extensive than just loading a past state. This might involve more complex logic for replaying events or aligning with historical simulation runs.
*   **Multi-source Merge Strategy:** The docstring mentions a "Multi-source merge strategy (baseline file + live API pulls + user overrides)" ([`intelligence/worldstate_loader.py:14-16`](intelligence/worldstate_loader.py:14)). The current implementation handles these sources, but the "strategy" part might imply more sophisticated conflict resolution or prioritization logic in the future beyond the current simple override order (overrides > live vars > baseline).
*   **Error Handling for Live Ingestion:** The [`ingest_live_variables()`](iris/variable_ingestion.py) call within [`load_initial_state()`](intelligence/worldstate_loader.py:80) doesn't have explicit error handling in this module. Failures within `ingest_live_variables` might not be gracefully handled or reported by the loader itself, though the underlying function might have its own error handling.
*   **Schema Validation for Input Files:** While the code reads CSV/JSON, there's no explicit schema validation for these files beyond expecting two columns (name, value) for the baseline and historical snapshots ([`intelligence/worldstate_loader.py:65`](intelligence/worldstate_loader.py:65), [`intelligence/worldstate_loader.py:183`](intelligence/worldstate_loader.py:183)). More robust validation could be an area for improvement.

Development seems to have followed the initial plan for Phase-1. The "Future expansion" items are logical next steps.

## 4. Connections & Dependencies

### Direct Imports from Other Project Modules:
*   [`simulation_engine.worldstate.WorldState`](simulation_engine/worldstate.py) ([`intelligence/worldstate_loader.py:25`](intelligence/worldstate_loader.py:25))
*   [`simulation_engine.worldstate.Variables`](simulation_engine/worldstate.py) (local import in functions) ([`intelligence/worldstate_loader.py:84`](intelligence/worldstate_loader.py:84), [`intelligence/worldstate_loader.py:194`](intelligence/worldstate_loader.py:194))
*   [`simulation_engine.worldstate.SymbolicOverlays`](simulation_engine/worldstate.py) (local import in functions) ([`intelligence/worldstate_loader.py:84`](intelligence/worldstate_loader.py:84), [`intelligence/worldstate_loader.py:194`](intelligence/worldstate_loader.py:194))
*   [`simulation_engine.worldstate.CapitalExposure`](simulation_engine/worldstate.py) (local import in functions) ([`intelligence/worldstate_loader.py:84`](intelligence/worldstate_loader.py:84), [`intelligence/worldstate_loader.py:194`](intelligence/worldstate_loader.py:194))
*   [`core.variable_registry.registry`](core/variable_registry.py) ([`intelligence/worldstate_loader.py:26`](intelligence/worldstate_loader.py:26))
*   [`iris.variable_ingestion.ingest_live_variables`](iris/variable_ingestion.py) ([`intelligence/worldstate_loader.py:27`](intelligence/worldstate_loader.py:27))
*   [`intelligence.intelligence_config.WORLDSTATE_DEFAULT_SOURCE`](intelligence/intelligence_config.py) ([`intelligence/worldstate_loader.py:29`](intelligence/worldstate_loader.py:29))
*   [`intelligence.intelligence_config.WORLDSTATE_INJECT_LIVE_DEFAULT`](intelligence/intelligence_config.py) ([`intelligence/worldstate_loader.py:30`](intelligence/worldstate_loader.py:30))

### External Library Dependencies:
*   `pathlib.Path` ([`intelligence/worldstate_loader.py:20`](intelligence/worldstate_loader.py:20))
*   `typing.Any, Dict, Optional` ([`intelligence/worldstate_loader.py:21`](intelligence/worldstate_loader.py:21))
*   `pandas` (as `pd`) ([`intelligence/worldstate_loader.py:23`](intelligence/worldstate_loader.py:23))

### Interaction with Other Modules via Shared Data:
*   **Baseline Files:** Reads CSV/JSON files (e.g., default `data/baselines/default.csv` as per [`WORLDSTATE_DEFAULT_SOURCE`](intelligence/intelligence_config.py:29) or user-specified path).
*   **Historical Snapshot Files:** Reads CSV/JSON files from a specified directory (default `snapshots/`) with names like `worldstate_{date}.csv` or `worldstate_{date}.json` ([`intelligence/worldstate_loader.py:137`](intelligence/worldstate_loader.py:137)).
*   **`VariableRegistry`:** Interacts with the singleton `registry` from [`core.variable_registry`](core/variable_registry.py) to flag missing variables.
*   **`VariableIngestion` Layer:** Calls [`ingest_live_variables()`](iris/variable_ingestion.py) which presumably fetches data from external APIs or other live sources.

### Input/Output Files:
*   **Input:**
    *   Baseline data files (CSV or JSON), e.g., [`data/baselines/default.csv`](data/baselines/default.csv).
    *   Historical snapshot files (CSV or JSON), e.g., `snapshots/worldstate_YYYY-MM-DD.csv`.
*   **Output:**
    *   The module's primary output is a populated `WorldState` object.
    *   It logs events to the `WorldState` object's event log (e.g., missing variables, failure to read baseline).
    *   Prints error messages to `stdout` if baseline/snapshot reading fails (e.g., [`intelligence/worldstate_loader.py:67`](intelligence/worldstate_loader.py:67), [`intelligence/worldstate_loader.py:236`](intelligence/worldstate_loader.py:236)).

## 5. Function and Class Example Usages

### [`load_initial_state(source: str | Path | None = None, *, inject_live: bool = WORLDSTATE_INJECT_LIVE_DEFAULT, **overrides: Dict[str, Any]) -> WorldState`](intelligence/worldstate_loader.py:37)
This function is the primary way to get a new `WorldState` for a simulation.

*   **Basic Usage (defaults):**
    ```python
    from intelligence.worldstate_loader import load_initial_state
    initial_worldstate = load_initial_state()
    # Uses default baseline, injects live variables.
    ```

*   **Using a Specific Baseline File:**
    ```python
    from intelligence.worldstate_loader import load_initial_state
    my_baseline_path = "path/to/my_custom_baseline.csv"
    initial_worldstate = load_initial_state(source=my_baseline_path, inject_live=False)
    # Uses custom baseline, does not inject live variables.
    ```

*   **With Overrides:**
    ```python
    from intelligence.worldstate_loader import load_initial_state
    initial_worldstate = load_initial_state(
        turn=10,
        sim_id="custom_sim_001",
        variables={"var_A": 100.0, "var_B": 200.0},
        metadata={"scenario_name": "High Growth"}
    )
    # Overrides initial turn, sim_id, specific variables, and adds custom metadata.
    ```

### [`load_historical_snapshot(date: str, snapshot_dir: str | Path = "snapshots", **overrides: Dict[str, Any]) -> WorldState`](intelligence/worldstate_loader.py:130)
This function is used to load a `WorldState` as it was at a specific historical date.

*   **Basic Usage:**
    ```python
    from intelligence.worldstate_loader import load_historical_snapshot
    historical_date = "2023-01-15"
    historical_worldstate = load_historical_snapshot(date=historical_date)
    # Loads from 'snapshots/worldstate_2023-01-15.csv' or '.json'.
    ```

*   **Using a Custom Snapshot Directory:**
    ```python
    from intelligence.worldstate_loader import load_historical_snapshot
    historical_date = "2023-01-15"
    custom_dir = "data/archive/snapshots"
    historical_worldstate = load_historical_snapshot(date=historical_date, snapshot_dir=custom_dir)
    ```
*   **With Overrides:**
    ```python
    from intelligence.worldstate_loader import load_historical_snapshot
    historical_worldstate = load_historical_snapshot(
        date="2023-01-15",
        variables={"var_C": 300.0}, # Override a variable from the snapshot
        metadata={"source_system": "ArchivalSystemX"}
    )
    ```

## 6. Hardcoding Issues

*   **Default Baseline Path:** While configurable via [`WORLDSTATE_DEFAULT_SOURCE`](intelligence/intelligence_config.py:29), if this config itself is considered a form of hardcoding, then the ultimate default path (e.g., `data/baselines/default.csv`) is hardcoded at that configuration level. The loader itself correctly uses this config.
*   **Default Snapshot Directory:** The default `snapshot_dir` in [`load_historical_snapshot()`](intelligence/worldstate_loader.py:132) is `"snapshots"`. This is a direct string literal.
*   **Snapshot Filename Convention:** The convention `worldstate_{date}.(csv|json)` ([`intelligence/worldstate_loader.py:137`](intelligence/worldstate_loader.py:137)) is hardcoded into the [`load_historical_snapshot()`](intelligence/worldstate_loader.py:130) function.
*   **`WorldState` Constructor Argument Keys:** The list `valid_constructor_keys = {"turn", "sim_id", "overlays", "capital", "event_log"}` ([`intelligence/worldstate_loader.py:73`](intelligence/worldstate_loader.py:73), [`intelligence/worldstate_loader.py:189`](intelligence/worldstate_loader.py:189)) is hardcoded. If the `WorldState` constructor changes, this list would need manual updating.
*   **Metadata Keys:** Keys like `"baseline_file"`, `"live_ingested"`, `"historical_date"`, `"load_type"` ([`intelligence/worldstate_loader.py:113-115`](intelligence/worldstate_loader.py:113), [`intelligence/worldstate_loader.py:223-225`](intelligence/worldstate_loader.py:223)) used for populating `WorldState.metadata` are hardcoded strings.
*   **Log Message Prefixes:** Prefixes like `"[WS-LOADER]"` ([`intelligence/worldstate_loader.py:67`](intelligence/worldstate_loader.py:67), [`intelligence/worldstate_loader.py:121`](intelligence/worldstate_loader.py:121)) and `"[WS-LOADER-HISTORICAL]"` ([`intelligence/worldstate_loader.py:233`](intelligence/worldstate_loader.py:233), [`intelligence/worldstate_loader.py:236`](intelligence/worldstate_loader.py:236)) are hardcoded.

## 7. Coupling Points

*   **`WorldState` Object:** Tightly coupled to the structure and constructor of the [`WorldState`](simulation_engine/worldstate.py) class, including its internal components like `Variables`, `SymbolicOverlays`, and `CapitalExposure`. Changes to `WorldState`'s initialization or structure would likely require changes here.
*   **`intelligence_config`:** Relies on constants like [`WORLDSTATE_DEFAULT_SOURCE`](intelligence/intelligence_config.py:29) and [`WORLDSTATE_INJECT_LIVE_DEFAULT`](intelligence/intelligence_config.py:30).
*   **`core.variable_registry`:** Depends on the `registry` singleton and its [`flag_missing_variables()`](core/variable_registry.py) method.
*   **`iris.variable_ingestion`:** Depends on the [`ingest_live_variables()`](iris/variable_ingestion.py) function and its behavior/return type.
*   **Pandas DataFrame Structure:** Assumes a specific structure for input CSV/JSON files (first column names/keys, second column values) when creating `baseline_vars` ([`intelligence/worldstate_loader.py:65`](intelligence/worldstate_loader.py:65), [`intelligence/worldstate_loader.py:183`](intelligence/worldstate_loader.py:183)).
*   **File System:** Directly interacts with the file system to read baseline and snapshot files. The existence and format of these files are crucial.

## 8. Existing Tests

*   No specific test file (e.g., `test_worldstate_loader.py`) was found in the `tests/intelligence/` directory.
*   No specific test file for this module was found in the main `tests/` directory.
*   **Assessment:** There is an apparent lack of dedicated unit tests for this module. This is a significant gap, as the module handles file I/O, data parsing, and integration with several other components, all ofwhich are common sources of errors. Without tests, it's hard to ensure its robustness, especially concerning different file formats, missing files, corrupted data, or changes in dependencies.

## 9. Module Architecture and Flow

The module defines two main public functions:

1.  **[`load_initial_state()`](intelligence/worldstate_loader.py:37):**
    *   Determines the source path for baseline data (uses default from config if `source` is `None`).
    *   Attempts to read and parse the baseline file (CSV or JSON) into `baseline_vars`. Handles file reading errors by printing a message.
    *   Merges `variables` from `**overrides` into `baseline_vars`.
    *   Separates `WorldState` constructor-specific arguments (`turn`, `sim_id`, etc.) from other `**overrides`.
    *   Optionally calls [`ingest_live_variables()`](iris/variable_ingestion.py) and updates `baseline_vars` with this live data (live data can overwrite baseline).
    *   Constructs the `WorldState` object, passing `baseline_vars` and filtered constructor arguments.
    *   Populates `WorldState.metadata` with information about the loading process (baseline file, live ingested keys) and merges any `metadata` from `**overrides`.
    *   Calls [`registry.flag_missing_variables()`](core/variable_registry.py) and logs any missing variables to the `WorldState`'s event log.
    *   Returns the populated `WorldState` object.

2.  **[`load_historical_snapshot()`](intelligence/worldstate_loader.py:130):**
    *   Constructs potential paths for snapshot files (CSV and JSON) based on `date` and `snapshot_dir`.
    *   Raises `FileNotFoundError` if neither CSV nor JSON snapshot file exists.
    *   Attempts to read and parse the snapshot file into `baseline_vars`.
    *   Merges `variables` from `**overrides` into `baseline_vars`.
    *   Separates `WorldState` constructor-specific arguments.
    *   Constructs the `WorldState` object.
    *   Populates `WorldState.metadata` (snapshot file, historical date, load type) and merges `metadata` from `**overrides`.
    *   Calls [`registry.flag_missing_variables()`](core/variable_registry.py) and logs missing variables.
    *   Handles exceptions during processing by printing a message and re-raising the exception.
    *   Returns the populated `WorldState` object.

Both functions perform local imports of `Variables`, `SymbolicOverlays`, and `CapitalExposure` from `simulation_engine.worldstate` to aid type checking and construction.

## 10. Naming Conventions

*   **Functions:** `load_initial_state`, `load_historical_snapshot` - follow PEP 8 (snake_case).
*   **Variables:** Generally follow PEP 8 (snake_case), e.g., `baseline_vars`, `source_path`, `constructor_args`.
*   **Parameters:** Generally follow PEP 8, e.g., `inject_live`, `snapshot_dir`.
*   **Constants (Imported):** `WORLDSTATE_DEFAULT_SOURCE`, `WORLDSTATE_INJECT_LIVE_DEFAULT` - follow PEP 8 for constants (UPPER_SNAKE_CASE).
*   **Classes (Imported):** `WorldState`, `Path`, `Variables`, `SymbolicOverlays`, `CapitalExposure` - follow PEP 8 (CapWords).
*   **Type Hinting:** Uses modern type hints (`str | Path | None`).
*   **Clarity:** Names are generally descriptive and understandable.
*   **Potential AI Assumption Errors/Deviations:**
    *   The use of `df.iloc[:, 0]` and `df.iloc[:, 1]` ([`intelligence/worldstate_loader.py:65`](intelligence/worldstate_loader.py:65), [`intelligence/worldstate_loader.py:183`](intelligence/worldstate_loader.py:183)) assumes the CSV/JSON structure rigidly (first column is name, second is value). While common, it's an implicit assumption not enforced by a schema. An AI might struggle if the input format deviates slightly without more explicit parsing instructions or column name references.
    *   The broad exception catching `except Exception as exc: # noqa: BLE001` ([`intelligence/worldstate_loader.py:66`](intelligence/worldstate_loader.py:66), [`intelligence/worldstate_loader.py:235`](intelligence/worldstate_loader.py:235)) is generally discouraged. While it has a `noqa` for `BLE001` (blind except), more specific exceptions could be caught.

Overall, naming conventions are good and largely adhere to PEP 8.