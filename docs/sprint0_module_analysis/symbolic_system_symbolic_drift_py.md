# Analysis Report for symbolic_system/symbolic_drift.py

## 1. Module Intent/Purpose

The primary role of the [`symbolic_system/symbolic_drift.py`](symbolic_system/symbolic_drift.py:1) module is to detect and log "symbolic drift" within a simulation environment. Symbolic drift is defined as rapid, unexpected, or contradictory changes in symbolic states (overlays) that might indicate issues like narrative collapse, forecast instability, or emotional incoherence in the simulation. It achieves this by comparing symbolic overlay values between consecutive [`WorldState`](simulation_engine/worldstate.py:0) objects.

## 2. Operational Status/Completeness

The module appears to be functionally complete for its defined scope of detecting and logging drift based on predefined thresholds.
- It handles basic type errors during delta computation (lines 25-31).
- A comment on line 31 ([`symbolic_system/symbolic_drift.py:31`](symbolic_system/symbolic_drift.py:31)) suggests "Optional: add logging here for debugging unexpected types," indicating a minor potential enhancement rather than a critical missing piece.
- No other explicit TODOs or major placeholders are visible.

## 3. Implementation Gaps / Unfinished Next Steps

- **Reactive Measures:** The module currently only detects and logs drift. Logical next steps for the broader system could involve implementing reactive measures based on detected drift, such as alerting mechanisms, automated adjustment of simulation parameters, or triggering deeper diagnostic routines. These are outside the current module's scope but represent potential future development.
- **Advanced Drift Characterization:** The current drift detection is based on simple thresholding of deltas and tension scores. Future enhancements could involve more sophisticated drift characterization (e.g., pattern recognition in drift, sustained drift vs. transient spikes).
- **Configurable Logging:** The logging for unexpected types in [`compute_overlay_deltas()`](symbolic_system/symbolic_drift.py:16) is mentioned as optional (line 31). Implementing this with configurable log levels could be a minor improvement.

## 4. Connections & Dependencies

### Direct Project Module Imports:
-   `from engine.worldstate import WorldState` ([`symbolic_system/symbolic_drift.py:11`](symbolic_system/symbolic_drift.py:11)): Imports the [`WorldState`](simulation_engine/worldstate.py:0) class, which is central to its operation as it processes these objects.
-   `from symbolic_system.symbolic_utils import get_overlay_snapshot, symbolic_tension_score` ([`symbolic_system/symbolic_drift.py:12`](symbolic_system/symbolic_drift.py:12)): Imports utility functions for extracting overlay data and calculating tension scores.

### External Library Dependencies:
-   `from typing import Dict` ([`symbolic_system/symbolic_drift.py:13`](symbolic_system/symbolic_drift.py:13)): Standard Python typing library. No other external, non-standard library dependencies are apparent.

### Interaction with Other Modules via Shared Data:
-   It reads symbolic overlay data from `WorldState` objects.
-   It writes log events using the `current_state.log_event()` method ([`symbolic_system/symbolic_drift.py:56`](symbolic_system/symbolic_drift.py:56), [`symbolic_system/symbolic_drift.py:66`](symbolic_system/symbolic_drift.py:66)), implying an interaction with the logging mechanism within the `WorldState` or a connected event management system.

### Input/Output Files:
-   **Input:** Implicitly, the data within `WorldState` objects.
-   **Output:** Log messages generated via `current_state.log_event()`. The actual storage (e.g., console, file, database) of these logs depends on the implementation of the `log_event` method.

## 5. Function and Class Example Usages

### [`compute_overlay_deltas(prev: Dict[str, float], curr: Dict[str, float]) -> Dict[str, float]`](symbolic_system/symbolic_drift.py:16)
-   **Purpose:** Computes the difference in values for each overlay key between two snapshots (dictionaries) of overlay states.
-   **Usage:**
    ```python
    prev_overlay_data = {"emotion_joy": 0.5, "state_alert": 0.2}
    curr_overlay_data = {"emotion_joy": 0.3, "state_alert": 0.25}
    deltas = compute_overlay_deltas(prev_overlay_data, curr_overlay_data)
    # deltas would be {"emotion_joy": -0.2, "state_alert": 0.05}
    ```

### [`detect_symbolic_drift(previous_state: WorldState, current_state: WorldState, tension_threshold: float = 0.2, delta_threshold: float = 0.25) -> Dict[str, float]`](symbolic_system/symbolic_drift.py:35)
-   **Purpose:** Compares symbolic overlays of two consecutive `WorldState` objects to detect and log significant changes (drift) based on provided thresholds.
-   **Usage:**
    ```python
    # Assuming previous_ws and current_ws are WorldState objects
    # with appropriate overlay data and a log_event method.
    drift_deltas = detect_symbolic_drift(previous_ws, current_ws, 
                                         tension_threshold=0.15, 
                                         delta_threshold=0.2)
    # If drift is detected, events will be logged via current_ws.log_event()
    # drift_deltas will contain all computed overlay deltas.
    ```

## 6. Hardcoding Issues

-   **Default Thresholds:**
    -   In [`detect_symbolic_drift()`](symbolic_system/symbolic_drift.py:35): `tension_threshold: float = 0.2` (line 38) and `delta_threshold: float = 0.25` (line 39). While these are parameters and can be overridden at call time, their default values are hardcoded. These might be better managed via a configuration file or system-wide constants if they need to be tuned frequently or vary across different simulation contexts.
-   **Rounding Precision:**
    -   In [`compute_overlay_deltas()`](symbolic_system/symbolic_drift.py:16): `round(curr_val - prev_val, 3)` (line 28). The precision of 3 decimal places is hardcoded. This might be acceptable but could be a configurable parameter if different precisions are needed.
-   **Log Message Prefixes/Formats:**
    -   Log messages use a hardcoded `"[DRIFT]"` prefix (lines 57, 67). While consistent, more complex logging systems might prefer structured logging or configurable message formats.
    -   The format strings for log messages are also hardcoded, e.g., `f"[DRIFT] Overlay '{overlay}' shifted by {change:.3f} in one turn (THRESH = {delta_threshold})"` ([`symbolic_system/symbolic_drift.py:57`](symbolic_system/symbolic_drift.py:57)).

## 7. Coupling Points

-   **`WorldState` Object:** The module is tightly coupled to the [`engine.worldstate.WorldState`](simulation_engine/worldstate.py:0) class, as it directly takes instances of this class as input and calls its `log_event` method.
-   **`symbolic_utils` Module:** It depends on [`get_overlay_snapshot()`](symbolic_system/symbolic_utils.py:0) and [`symbolic_tension_score()`](symbolic_system/symbolic_utils.py:0) from [`symbolic_system.symbolic_utils`](symbolic_system/symbolic_utils.py:0). Changes to the signature or behavior of these utility functions would directly impact this module.
-   **Overlay Data Structure:** The module assumes overlays are represented as dictionaries of string keys to float values, as processed by [`compute_overlay_deltas()`](symbolic_system/symbolic_drift.py:16) and returned by [`get_overlay_snapshot()`](symbolic_system/symbolic_utils.py:0).

## 8. Existing Tests

A specific test file for this module (e.g., `tests/symbolic_system/test_symbolic_drift.py`) was not found in the `tests/symbolic_system/` directory. Tests for this module might be integrated elsewhere, or test coverage may be missing.

## 9. Module Architecture and Flow

1.  The primary entry point is [`detect_symbolic_drift()`](symbolic_system/symbolic_drift.py:35).
2.  It receives `previous_state` and `current_state` ([`WorldState`](simulation_engine/worldstate.py:0) objects) as input.
3.  It calls [`get_overlay_snapshot()`](symbolic_system/symbolic_utils.py:0) (from `symbolic_utils`) for both states to extract their symbolic overlay data as dictionaries.
4.  These two overlay dictionaries are passed to [`compute_overlay_deltas()`](symbolic_system/symbolic_drift.py:16).
    *   [`compute_overlay_deltas()`](symbolic_system/symbolic_drift.py:16) iterates through keys from the previous overlay.
    *   It safely retrieves values from both current and previous overlays, defaulting to `0.0` and attempting conversion to `float`.
    *   It calculates the difference, rounds it to 3 decimal places, and stores it.
    *   Type errors during conversion result in a delta of `0.0` for that key.
    *   It returns a dictionary of these deltas.
5.  [`detect_symbolic_drift()`](symbolic_system/symbolic_drift.py:35) then iterates through the returned `deltas`:
    *   If the absolute value of any `change` exceeds `delta_threshold`, a drift event is logged via `current_state.log_event()`.
6.  Next, it calculates the symbolic tension:
    *   It calls [`symbolic_tension_score()`](symbolic_system/symbolic_utils.py:0) (from `symbolic_utils`) for both previous and current overlay snapshots.
    *   It computes the difference (`tension_delta`) between current and previous tension scores.
7.  If `tension_delta` exceeds `tension_threshold`, a tension spike drift event is logged via `current_state.log_event()`.
8.  Finally, the `deltas` dictionary is returned by [`detect_symbolic_drift()`](symbolic_system/symbolic_drift.py:35).

## 10. Naming Conventions

-   **Functions:** [`compute_overlay_deltas()`](symbolic_system/symbolic_drift.py:16), [`detect_symbolic_drift()`](symbolic_system/symbolic_drift.py:35) follow PEP 8 (snake_case).
-   **Variables:** `prev_overlay`, `curr_overlay`, `deltas`, `tension_threshold`, `delta_threshold`, `prev_val`, `curr_val` also follow snake_case.
-   **Imported Class:** [`WorldState`](simulation_engine/worldstate.py:0) is PascalCase, which is standard for classes.
-   **Type Hinting:** `Dict` is used from the `typing` module.
-   The naming is generally clear, descriptive, and consistent with Python conventions (PEP 8). No obvious AI assumption errors or significant deviations from standard practices are noted.