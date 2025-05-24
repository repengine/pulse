# Module Analysis: `simulation_engine/utils/simulation_replayer.py`

## 1. Module Intent/Purpose

The primary role of this module, [`simulation_replayer.py`](simulation_engine/utils/simulation_replayer.py:1), is to replay previously saved [`WorldState`](simulation_engine/worldstate.py:1) snapshots. This functionality is designed for various purposes including:
*   **Audit:** Inspecting variable states at each turn of a simulation.
*   **Diagnostics:** Showing differences in variables and overlays between simulation turns.
*   **Retrodiction:** Re-running simulation logic on historical state data and comparing the outcomes against the original run.

It allows for detailed examination of simulation runs, facilitating debugging, validation, and understanding of simulation dynamics.

## 2. Operational Status/Completeness

*   The module appears largely functional for its core defined modes: 'audit', 'diagnostic', and 'retrodiction'.
*   Core functionalities like loading [`WorldState`](simulation_engine/worldstate.py:1) snapshots from JSON files, iterating through them, and performing mode-specific actions are implemented.
*   Attribute access for `WorldState.variables` and `WorldState.overlays` within the `_diff_states` method has been corrected to use `state.variables.as_dict()` and `state.overlays.as_dict()` respectively.
*   Type hinting has been improved using `typing.TYPE_CHECKING` for conditional imports of `WorldState` and related classes, and dummy classes have been enhanced for better fallback behavior.
*   The [`show_lineage()`](simulation_engine/utils/simulation_replayer.py:243) method is explicitly marked as a "stub" with a placeholder comment, indicating this feature for visualizing forecast ancestry is incomplete.
*   No explicit "TODO" comments are present, but the stub function is a clear indicator of unfinished work.

## 3. Implementation Gaps / Unfinished Next Steps

*   **`show_lineage()` Function:** The [`show_lineage()`](simulation_engine/utils/simulation_replayer.py:243) method needs full implementation to provide the intended visualization of forecast ancestry.
*   **Retrodiction Outcome Comparison:** While the 'retrodiction' mode has a placeholder for re-running logic ([`simulation_engine/utils/simulation_replayer.py:209-220`](simulation_engine/utils/simulation_replayer.py:209-220)), the detailed comparison and reporting of differences between the original run and the retrodicted run are not explicitly implemented within the [`replay_simulation()`](simulation_engine/utils/simulation_replayer.py:154) method. This comparison logic might be assumed to be handled externally or is a gap.
*   **Symbolic Diff Depth:** The nature and depth of "symbolic diffs" for overlays, conditional on `self.config.show_symbolic` ([`simulation_engine/utils/simulation_replayer.py:119-127`](simulation_engine/utils/simulation_replayer.py:119-127)), could potentially be expanded for more detailed insights.
*   **Error Handling:** Robustness could be improved with more comprehensive error handling for file operations (e.g., corrupted JSON files, missing individual snapshot files beyond the initial directory listing).
*   **Configuration for Replay Output:** The audit mode currently logs/prints a sample of 5 variable keys and 3 overlay keys ([`simulation_engine/utils/simulation_replayer.py:190-194`](simulation_engine/utils/simulation_replayer.py:190-194)); this could be made configurable.

## 4. Connections & Dependencies

### Project-Internal Dependencies:
*   [`simulation_engine.worldstate.WorldState`](simulation_engine/worldstate.py:1): For loading and representing simulation states.
*   [`simulation_engine.turn_engine.run_turn`](simulation_engine/turn_engine.py:1): Potentially used in 'retrodiction' mode (currently placeholder logic).
*   [`logging`](simulation_engine/utils/simulation_replayer.py:19): Standard Python logging.
*   [`core.path_registry.PATHS`](core/path_registry.py:1): Used to get the default path for replay logs.
*   [`core.pulse_learning_log.log_learning_event`](core/pulse_learning_log.py:1): For logging replay events.

### External Library Dependencies:
*   `os`: For file system operations (listing files, creating directories).
*   `json`: For loading and saving data (WorldState snapshots, replay logs).
*   `copy` (specifically `deepcopy`): For creating isolated copies of [`WorldState`](simulation_engine/worldstate.py:1) objects for retrodiction.
*   `typing` (`List`, `Optional`, `Dict`, `Any`, `Tuple`, `TYPE_CHECKING`): For type hinting.
*   `dataclasses` (`dataclass`, `field`): For creating the [`ReplayerConfig`](simulation_engine/utils/simulation_replayer.py:54) class.
*   `datetime` (from `datetime`): For timestamping replay log files.
*   `time`: For generating timestamps in example usage and dummy class fallbacks.

### Data Interactions:
*   **Input:** Reads `.json` files representing serialized [`WorldState`](simulation_engine/worldstate.py:1) objects from a user-specified `log_dir`.
*   **Output:**
    *   Writes a JSON replay log file (e.g., `replay_log_YYYYMMDD_HHMMSS.json`) to the directory specified by `config.log_path` (defaulting to `replay_logs` via [`PATHS`](core/path_registry.py:1)) if `config.log_to_file` is `True`.
    *   Outputs information to the console via the `logger` and `print()` statements.
    *   Logs learning events using [`log_learning_event()`](core/pulse_learning_log.py:1).

## 5. Function and Class Example Usages

*   **`ReplayerConfig` Dataclass ([`simulation_engine/utils/simulation_replayer.py:31`](simulation_engine/utils/simulation_replayer.py:31)):**
    ```python
    from simulation_engine.utils.simulation_replayer import ReplayerConfig

    # Configure for diagnostic mode, limiting to 10 steps, with verbose output
    config = ReplayerConfig(mode="diagnostic", step_limit=10, verbose=True, show_symbolic=True) # type: ignore
    ```
    This dataclass is used to define the settings for a replay session.

*   **`SimulationReplayer` Class ([`simulation_engine/utils/simulation_replayer.py:75`](simulation_engine/utils/simulation_replayer.py:75)):**
    ```python
    from simulation_engine.utils.simulation_replayer import SimulationReplayer, ReplayerConfig # type: ignore

    # Define the directory containing WorldState snapshot .json files
    snapshot_directory = "path/to/your/simulation_snapshots"

    # Create a configuration
    replay_config = ReplayerConfig(mode="audit", log_to_file=True, verbose=False) # type: ignore

    # Initialize the replayer
    replayer = SimulationReplayer(snapshot_directory=snapshot_directory, config=replay_config) # type: ignore

    # Run the replay
    replayer.replay_simulation(replay_session_id="audit_session_001") # type: ignore

    # Example of replaying only the last run (Note: replay_last_run is not in the new code)
    # # replayer.replay_last_run()
    ```
    The [`SimulationReplayer`](simulation_engine/utils/simulation_replayer.py:75) class is the main interface. Its [`replay_simulation()`](simulation_engine/utils/simulation_replayer.py:154) method processes the snapshots based on the provided configuration.

## 6. Hardcoding Issues

*   **Default Log Path Fallback:** The log path `str(PATHS.get("REPLAY_LOG_PATH", "replay_logs/"))` ([`simulation_engine/utils/simulation_replayer.py:58`](simulation_engine/utils/simulation_replayer.py:58)) uses a hardcoded string `"replay_logs/"` as a fallback.
*   **Snapshot File Extension and Prefix:** The module specifically looks for files ending with `".json"` and starting with `"worldstate_snapshot_turn_"` ([`simulation_engine/utils/simulation_replayer.py:155`](simulation_engine/utils/simulation_replayer.py:155)). These are hardcoded.
*   **Default Decay Rate:** The [`ReplayerConfig`](simulation_engine/utils/simulation_replayer.py:54) no longer has a `decay_rate` attribute by default in the provided new code. If used by `run_turn`, it would need to be passed or configured.
*   **Audit Mode Variable Display Limit:** In 'audit' mode, a sample of 5 variable keys and 3 overlay keys are shown ([`simulation_engine/utils/simulation_replayer.py:190-191`](simulation_engine/utils/simulation_replayer.py:190-191)). These limits are hardcoded.
*   **Log Learning Event Details:** The event name `"simulation_replay_session_completed"` and its payload structure in [`log_learning_event()`](simulation_engine/utils/simulation_replayer.py:230) are hardcoded.

## 7. Coupling Points

*   **[`WorldState`](simulation_engine/worldstate.py:1) Object Structure:** The module is tightly coupled to the [`WorldState`](simulation_engine/worldstate.py:1) class, particularly its `from_dict` method for deserialization and the structure of its `variables` and `overlays` attributes (now accessed via `as_dict()` methods). Changes to [`WorldState`](simulation_engine/worldstate.py:1) would likely require updates here.
*   **[`turn_engine.run_turn()`](simulation_engine/turn_engine.py:1) Interface:** The 'retrodiction' mode (currently placeholder) would depend on the `run_turn()` signature and behavior.
*   **[`core.path_registry.PATHS`](core/path_registry.py:1):** Dependency for resolving the default replay log path.
*   **[`core.pulse_learning_log.log_learning_event`](core/pulse_learning_log.py:1):** Dependency for the logging mechanism of replay events.
*   **File System Structure:** Relies on a specific file system structure where snapshots are individual JSON files (with a specific naming pattern) within a given directory.

## 8. Existing Tests

*   A review of the provided file list does not show a dedicated test file for `simulation_replayer.py` (e.g., `tests/simulation_engine/utils/test_simulation_replayer.py`).
*   The module includes an `if __name__ == "__main__":` block ([`simulation_engine/utils/simulation_replayer.py:255`](simulation_engine/utils/simulation_replayer.py:255)) with example usage that creates dummy snapshots and tests audit and diagnostic modes. This serves as a form of integration/smoke test but not as formal unit tests.
*   **Conclusion:** There appears to be a lack of dedicated unit tests for this module. This is a significant gap, as tests are crucial for verifying the correctness of the different replay modes, diffing logic, and file handling, especially given the module's role in diagnostics and auditing.

## 9. Module Architecture and Flow

The module is structured around the [`ReplayerConfig`](simulation_engine/utils/simulation_replayer.py:54) dataclass and the [`SimulationReplayer`](simulation_engine/utils/simulation_replayer.py:75) class.

1.  **Configuration (`ReplayerConfig`):**
    *   Stores settings like `mode` ('audit', 'diagnostic', 'retrodiction'), `step_limit`, logging preferences, `verbose` flag, and `show_symbolic` flag.
    *   Includes a `__post_init__` to create the log path directory.

2.  **Core Logic (`SimulationReplayer`):**
    *   **Initialization (`__init__`)**:
        *   Takes `snapshot_directory` and an optional [`ReplayerConfig`](simulation_engine/utils/simulation_replayer.py:54) instance.
        *   Validates the existence of `snapshot_directory`.
        *   Initializes an empty list `self.replay_log_entries` to store replay data.
    *   **State Loading (`_load_snapshot`)**:
        *   Reads a JSON file from the given path.
        *   Deserializes the JSON data into a [`WorldState`](simulation_engine/worldstate.py:1) object using [`WorldState.from_dict()`](simulation_engine/worldstate.py:1).
    *   **Main Replay Loop (`replay_simulation`)**:
        *   Lists `.json` files matching a specific pattern (e.g., "worldstate_snapshot_turn_...") in `self.snapshot_directory` and sorts them.
        *   Applies `step_limit` if configured.
        *   Iterates through each snapshot file:
            *   Loads the [`WorldState`](simulation_engine/worldstate.py:1) for the current turn using `_load_snapshot`.
            *   Logs verbose output if enabled, including turn number, filename, and WorldState timestamp.
            *   **Mode-Specific Actions**:
                *   **'audit'**: Logs/prints a sample of variables and overlays.
                *   **'diagnostic'**: If a `previous_state` exists, calls [`_diff_states()`](simulation_engine/utils/simulation_replayer.py:108) to find differences in variables and overlays. Prints/logs these diffs.
                *   **'retrodiction'**: (Placeholder) Intended to re-run logic and compare.
            *   Appends a dictionary of results for the current turn to `self.replay_log_entries`.
            *   Sets `previous_state = current_state` for the next iteration's diffing.
        *   After the loop, if `self.config.log_to_file` is true, calls `_save_replay_log` to dump `self.replay_log_entries` to a timestamped JSON file.
        *   If a `replay_session_id` is provided, logs a "simulation_replay_session_completed" event via [`log_learning_event()`](core/pulse_learning_log.py:1).
    *   **Helper Methods**:
        *   [`_diff_states()`](simulation_engine/utils/simulation_replayer.py:108): Compares variables (from `state.variables.as_dict()`) and overlays (from `state.overlays.as_dict()`) of two [`WorldState`](simulation_engine/worldstate.py:1) objects.
        *   [`_print_diffs()`](simulation_engine/utils/simulation_replayer.py:139): Logs the diffs found by [`_diff_states()`](simulation_engine/utils/simulation_replayer.py:108).
        *   [`_save_replay_log()`](simulation_engine/utils/simulation_replayer.py:236): Saves the replay log to a file.
        *   (Removed methods: `replay_last_run`, `compare_base_vs_counterfactual`, `show_lineage` from the class level, with `show_lineage` being a known stub if it were present).

## 10. Naming Conventions

*   **Classes:** `ReplayerConfig`, `SimulationReplayer` use PascalCase, adhering to PEP 8.
*   **Methods and Functions:** `_load_snapshot`, `replay_simulation`, `_diff_states`, `_print_diffs`, `_save_replay_log` use snake_case, adhering to PEP 8. Internal helper methods are correctly prefixed with an underscore.
*   **Variables:** `snapshot_directory`, `config`, `previous_state`, `variable_diffs`, `overlay_diffs` generally use snake_case.
*   **Constants/Globals:** `PATHS` (imported) is uppercase. `logger` is lowercase, which is standard for loggers.
*   **Docstrings:** The module has a comprehensive docstring explaining its purpose and modes. Most public methods and the class also have docstrings. The module docstring includes "Author: Pulse AI (Architect Mode)" and a plan reference ([`simulation_engine/utils/simulation_replayer.py:10-11`](simulation_engine/utils/simulation_replayer.py:10-11)).
*   **Consistency:** Naming is generally consistent and follows Python community standards (PEP 8).
*   **Potential AI Assumption Errors:** The "Author" line now clearly indicates AI involvement as per the plan. No other obvious AI-related naming errors are apparent.