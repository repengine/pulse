# Historical Retrodiction Runner (Compatibility Layer)

## Overview

The module [`engine/historical_retrodiction_runner.py`](../../../engine/historical_retrodiction_runner.py) serves as a compatibility layer. Its original functionality related to running historical retrodiction processes has been deprecated and integrated into [`simulation_engine/simulator_core.py`](../../../simulation_engine/simulator_core.py). This module is retained primarily to ensure backward compatibility for existing tests that might still reference its components.

## Purpose

The main purpose of this module is to provide a consistent interface for older tests or parts of the system that have not yet been updated to use the newer `simulator_core.py` functionalities directly for historical retrodiction tasks. It ensures that these older components can still function without breaking due to the refactoring.

## Key Components

### `get_default_variable_state()` Function

*   **Purpose:** Provides a default set of variables and their states. This is used as a fallback, especially in testing environments where a full historical data file might not be present or necessary.
*   **Functionality:**
    *   Attempts to load historical variables from a JSON file specified by the `PULSE_TRUTH_PATH` environment variable (defaulting to `data/historical_variables.json`).
    *   If the file is found and successfully parsed, it returns the variables dictionary.
    *   If the file is not found or an error occurs during loading, it returns a default dictionary containing `{"energy_cost": 1.0}`.
*   **Usage:** Primarily used by tests or older code to get a baseline state for simulations or retrodiction processes.
    ```python
    from engine.historical_retrodiction_runner import get_default_variable_state
    default_state = get_default_variable_state()
    ```

### `RetrodictionLoader` Class

*   **Purpose:** A compatibility class designed to mimic the behavior of a previous loader for historical snapshots. It allows older tests to load turn-by-turn historical data.
*   **Attributes:**
    *   `path` (str): The path to the JSON file containing historical snapshots.
    *   `snapshots` (Dict[str, Any]): A dictionary where keys are turn numbers (as strings) and values are the corresponding state snapshots.
*   **Methods:**
    *   `__init__(self, path: Optional[str] = None)`: Initializes the loader. It tries to load snapshot data from the specified `path` or the `PULSE_TRUTH_PATH` environment variable.
    *   `get_snapshot_by_turn(self, turn: int) -> Optional[Dict[str, Any]]`: Retrieves a specific snapshot by its turn number. Returns `None` if the snapshot for the given turn is not found.
*   **Usage:**
    ```python
    from engine.historical_retrodiction_runner import RetrodictionLoader

    # Load snapshots (implicitly uses TRUTH_PATH or default)
    loader = RetrodictionLoader()

    # Get snapshot for a specific turn
    snapshot_turn_5 = loader.get_snapshot_by_turn(5)
    if snapshot_turn_5:
        print("Snapshot for turn 5:", snapshot_turn_5)
    ```

## Usage

This module is not intended for new development. Its components are primarily called by older test suites or legacy code that relied on the previous structure of the historical retrodiction system.

*   **For loading default variables:**
    ```python
    from engine.historical_retrodiction_runner import get_default_variable_state
    initial_state = get_default_variable_state()
    ```
*   **For loading historical snapshots (legacy):**
    ```python
    from engine.historical_retrodiction_runner import RetrodictionLoader
    loader = RetrodictionLoader(path="path/to/your/historical_data.json")
    turn_0_data = loader.get_snapshot_by_turn(0)
    ```

For new development requiring historical retrodiction capabilities or simulation state management, please refer to [`simulation_engine/simulator_core.py`](../../../simulation_engine/simulator_core.py) and related modules.

## Relationship to Other Modules

*   **[`simulation_engine/simulator_core.py`](../../../simulation_engine/simulator_core.py):** The core logic previously associated with historical retrodiction running has been migrated to this module. This `historical_retrodiction_runner.py` module now acts as a compatibility shim.
*   **Test Suites:** Various test files (e.g., [`tests/test_historical_retrodiction_runner.py`](../../../tests/test_historical_retrodiction_runner.py)) might still import and use components from this module to ensure backward compatibility of tests.
*   **Data Files:** Relies on `data/historical_variables.json` (or a path specified by `PULSE_TRUTH_PATH`) for loading default variables and snapshots.

## Deprecation Note

This module is effectively deprecated. New code should use the functionalities provided in [`simulation_engine/simulator_core.py`](../../../simulation_engine/simulator_core.py) and other relevant modules for simulation and retrodiction tasks. The components within this module (`RetrodictionLoader`, `get_default_variable_state`) are maintained for backward compatibility with older tests and code.