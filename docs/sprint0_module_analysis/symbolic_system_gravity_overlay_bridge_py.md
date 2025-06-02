# Module Analysis: symbolic_system.gravity.overlay_bridge

**File Path:** [`symbolic_system/gravity/overlay_bridge.py`](symbolic_system/gravity/overlay_bridge.py)

## 1. Module Intent/Purpose

The `overlay_bridge.py` module serves as a compatibility layer between an older "overlay" system and the newer "Symbolic Pillar / Gravity Fabric" architecture. Its primary responsibility is to facilitate a gradual migration from the legacy overlay system to the modern pillar-based approach while ensuring backward compatibility with existing code that relies on overlay functionalities. It provides functions to translate data, calculate metrics using either system, and unify access to symbolic concepts during the transition period.

## 2. Operational Status/Completeness

The module appears to be largely complete and functional for its intended bridging role.
- Functions are well-documented with docstrings, parameter descriptions, and type hints.
- There are no apparent `TODO`, `FIXME` comments, or `pass` statements indicating unfinished core logic.
- The module seems ready to support the transition phase between the two systems.

## 3. Implementation Gaps / Unfinished Next Steps

- **Ultimate Goal:** The existence of this bridge implies the legacy "overlay" system is targeted for eventual deprecation. The main "unfinished next step" from a project perspective is the complete migration to the Symbolic Pillar system, which would render this bridge obsolete.
- **Migration Progress:** The extent of this module's usage throughout the codebase would be an indicator of the migration's progress.
- **Module-Specific Gaps:** Within its defined scope as a bridge, the module does not show obvious signs of unfinished features. Its completeness is tied to the features of the two systems it connects.

## 4. Connections & Dependencies

### 4.1. Direct Project Module Imports

-   [`engine.worldstate`](simulation_engine/worldstate.py:0): Specifically, the `WorldState` class is imported and used as a parameter in several functions to access legacy overlay data.
-   [`symbolic_system.symbolic_utils`](symbolic_system/symbolic_utils.py:0): Imported as `legacy_utils` and used for fallback mechanisms to the old overlay system's functions (e.g., [`legacy_utils.get_overlay_snapshot()`](symbolic_system/symbolic_utils.py:0), [`legacy_utils.symbolic_tension_score()`](symbolic_system/symbolic_utils.py:0)).
-   [`symbolic_system.gravity.symbolic_pillars`](symbolic_system/gravity/symbolic_pillars.py:0): The `SymbolicPillarSystem` class is imported and is central to the new architecture this bridge interacts with.
-   [`symbolic_system.gravity.integration`](symbolic_system/gravity/integration.py:0): Several functions are imported:
    -   [`get_pillar_system()`](symbolic_system/gravity/integration.py:0): To access the current pillar system instance.
    -   [`get_gravity_fabric()`](symbolic_system/gravity/integration.py:0): To access the gravity fabric instance.
    -   [`is_gravity_enabled()`](symbolic_system/gravity/integration.py:0): To determine which system (legacy or pillar) should be active.
    -   [`adapt_overlays_to_pillars()`](symbolic_system/gravity/integration.py:0): To synchronize data from legacy overlays to the pillar system.

### 4.2. External Library Dependencies

-   `logging`: Used for standard logging.
-   `typing`: Used for type hinting (Dict, List, Optional, Tuple, Any).

### 4.3. Interaction via Shared Data

-   Interacts with `WorldState` objects, which presumably contain the state of the legacy "overlays."
-   Reads from and modifies the state of the `SymbolicPillarSystem` and `GravityFabric`, which are obtained via the [`symbolic_system.gravity.integration`](symbolic_system/gravity/integration.py:0) module. These represent the shared state of the new symbolic architecture.

### 4.4. Input/Output Files

-   The module does not perform direct file input/output.
-   It uses the `logging` module, so log messages will be written to configured log files.

## 5. Function and Class Example Usages

Key functions and their intended usage:

-   **[`get_pillar_snapshot(state: Optional[WorldState] = None) -> Dict[str, float]`](symbolic_system/gravity/overlay_bridge.py:27):**
    Retrieves current pillar values. If `state` is provided, it first syncs overlays from `WorldState` to pillars.
    ```python
    # pillar_values = overlay_bridge.get_pillar_snapshot(current_world_state)
    ```

-   **[`normalize_pillar_vector(pillars: Dict[str, float]) -> Dict[str, float]`](symbolic_system/gravity/overlay_bridge.py:52):**
    Normalizes a dictionary of pillar values to a unit vector.
    ```python
    # normalized_pillars = overlay_bridge.normalize_pillar_vector({"trust": 0.7, "fear": 0.3})
    ```

-   **[`pillar_tension_score(pillars: Optional[Dict[str, float]] = None) -> float`](symbolic_system/gravity/overlay_bridge.py:74):**
    Calculates a tension score from pillar contradictions. Uses the global pillar system if `pillars` argument is `None`.
    ```python
    # tension = overlay_bridge.pillar_tension_score()
    ```

-   **[`pillar_fragility_index(state: Optional[WorldState] = None) -> float`](symbolic_system/gravity/overlay_bridge.py:98):**
    Calculates a fragility index based on pillar tension and gravity system residuals.
    ```python
    # fragility = overlay_bridge.pillar_fragility_index(current_world_state)
    ```

-   **[`compute_pillar_drift_penalty(forecast: dict) -> float`](symbolic_system/gravity/overlay_bridge.py:158):**
    Computes a penalty score (0-1) reflecting pillar instability, using forecast metadata.
    ```python
    # forecast_meta = {"symbolic_fragmented": False, "arc_volatility_score": 0.5}
    # drift_penalty = overlay_bridge.compute_pillar_drift_penalty(forecast_meta)
    ```

-   **[`legacy_to_pillar_system(overlays: Dict[str, float]) -> None`](symbolic_system/gravity/overlay_bridge.py:210):**
    Translates and applies legacy overlay values to the current pillar system.
    ```python
    # old_overlays = {"trust": 0.8, "despair": 0.1}
    # overlay_bridge.legacy_to_pillar_system(old_overlays)
    ```

-   **[`pillar_to_legacy_overlays() -> Dict[str, float]`](symbolic_system/gravity/overlay_bridge.py:231):**
    Converts the current pillar system's state back into a legacy overlay dictionary format.
    ```python
    # legacy_formatted_pillars = overlay_bridge.pillar_to_legacy_overlays()
    ```

-   **[`get_unified_tension_score(state: WorldState) -> float`](symbolic_system/gravity/overlay_bridge.py:244):**
    Returns a tension score, automatically choosing between the pillar system (if gravity is enabled) or the legacy overlay system.
    ```python
    # current_tension = overlay_bridge.get_unified_tension_score(current_world_state)
    ```

-   **[`get_unified_fragility_index(state: WorldState) -> float`](symbolic_system/gravity/overlay_bridge.py:269):**
    Similar to unified tension, but for the fragility index.
    ```python
    # current_fragility = overlay_bridge.get_unified_fragility_index(current_world_state)
    ```

-   **[`update_forecast_with_pillar_data(forecast: dict) -> dict`](symbolic_system/gravity/overlay_bridge.py:292):**
    Enriches a given forecast dictionary with data from the pillar and gravity systems if gravity is enabled.
    ```python
    # my_forecast = {"prediction": 123}
    # enriched_forecast = overlay_bridge.update_forecast_with_pillar_data(my_forecast)
    ```

## 6. Hardcoding Issues

Several magic numbers and string literals are used directly in the logic:

-   In [`pillar_fragility_index()`](symbolic_system/gravity/overlay_bridge.py:98):
    -   Thresholds: `0.3` (for trust), `0.5` (for `rms_weight`), `1.0` (for residual).
    -   Multipliers: `0.5` (for despair), `0.4` (for rage), `0.6` (for `rms_weight` penalty), `0.3` (for residual penalty).
    -   Divisor: `10.0` (for normalizing residual).
    -   Default value: `0.5` (for trust if not present).
    -   Pillar names (strings): `"trust"`, `"despair"`, `"rage"`.
-   In [`compute_pillar_drift_penalty()`](symbolic_system/gravity/overlay_bridge.py:158):
    -   Penalty values: `0.2`, `0.1`, `0.15`.
    -   Thresholds: `0.7` (for `arc_volatility_score`), `0.1` (for pillar growth rate).
    -   Multipliers: `2` (for growth rate penalty), `1.5` (for change in correction magnitude).
    -   Cap: `0.3` (for growth rate penalty).
-   In [`update_forecast_with_pillar_data()`](symbolic_system/gravity/overlay_bridge.py:292):
    -   `n=3` for `get_top_contributors(n=3)`.

These hardcoded values could potentially be refactored into named constants or configuration parameters for better readability, maintainability, and tunability.

## 7. Coupling Points

-   **High Coupling with [`symbolic_system.gravity.integration`](symbolic_system/gravity/integration.py:0):** Relies heavily on this module for accessing `SymbolicPillarSystem`, `GravityFabric`, and system status (e.g., `is_gravity_enabled()`).
-   **High Coupling with `WorldState`:** Several functions require `WorldState` objects to interact with legacy overlay data.
-   **High Coupling with [`symbolic_system.symbolic_utils`](symbolic_system/symbolic_utils.py:0):** Uses this for fallback to legacy system calculations.
-   **Transitional Coupling:** Functions like [`get_unified_tension_score()`](symbolic_system/gravity/overlay_bridge.py:244) and [`get_unified_fragility_index()`](symbolic_system/gravity/overlay_bridge.py:269) exhibit tight coupling to both old and new systems, as their logic explicitly branches based on whether the new gravity system is enabled.
-   **Data Structure Coupling:** [`update_forecast_with_pillar_data()`](symbolic_system/gravity/overlay_bridge.py:292) is coupled to the expected structure of the input `forecast` dictionary and the internal data structures of `GravityFabric` and `SymbolicPillarSystem`.

## 8. Existing Tests

-   A specific test file such as `tests/symbolic_system/gravity/test_overlay_bridge.py` is not present in the provided file listing.
-   The directory [`tests/symbolic_system/gravity/`](tests/symbolic_system/gravity/) exists and contains `test_residual_gravity_engine.py`, but no direct tests for `overlay_bridge.py` are apparent.
-   This suggests a potential gap in dedicated unit tests for this module. Its functionality might be covered indirectly through integration tests of the broader gravity system or modules that utilize these bridge functions.

## 9. Module Architecture and Flow

-   The module consists of a collection of utility functions rather than classes.
-   **General Control Flow:**
    1.  Functions often start by obtaining instances of `SymbolicPillarSystem` and `GravityFabric` via the `integration` module.
    2.  Some functions accept a `WorldState` object to synchronize legacy overlay data with the pillar system using [`adapt_overlays_to_pillars()`](symbolic_system/gravity/integration.py:0).
    3.  Calculations and data transformations are performed based on the state of these systems.
    4.  "Unified" functions ([`get_unified_tension_score()`](symbolic_system/gravity/overlay_bridge.py:244), [`get_unified_fragility_index()`](symbolic_system/gravity/overlay_bridge.py:269)) use [`is_gravity_enabled()`](symbolic_system/gravity/integration.py:0) to decide whether to use new pillar-based logic or fall back to legacy overlay-based logic (via `legacy_utils`).
    5.  Direct conversion functions ([`legacy_to_pillar_system()`](symbolic_system/gravity/overlay_bridge.py:210), [`pillar_to_legacy_overlays()`](symbolic_system/gravity/overlay_bridge.py:231)) are provided for explicit data translation.
-   The module acts as an important abstraction layer, allowing other parts of the system to work with symbolic concepts (like tension and fragility) consistently, regardless of whether the underlying system is the old overlays or the new pillars/gravity fabric.

## 10. Naming Conventions

-   **PEP 8 Adherence:** Function and variable names generally follow Python's PEP 8 style guide (snake_case), e.g., [`get_pillar_snapshot`](symbolic_system/gravity/overlay_bridge.py:27), [`pillar_system`](symbolic_system/gravity/overlay_bridge.py:43).
-   **Clarity:** Names are largely descriptive and clearly indicate the purpose of functions and variables, especially highlighting the "bridge" nature (e.g., `legacy_to_pillar_system`, `pillar_to_legacy_overlays`, `get_unified_tension_score`).
-   **Consistency with Legacy:** Functions replacing or analogous to legacy utilities often adapt legacy names, substituting "pillar" for "overlay" or "symbolic" (e.g., [`get_pillar_snapshot`](symbolic_system/gravity/overlay_bridge.py:27) mirrors a presumed `get_overlay_snapshot()`).
-   **Type Hinting:** The module makes good use of type hints, improving code clarity and maintainability.
-   **Constants:** As noted in "Hardcoding Issues," many numeric literals are used directly. Defining these as named constants would improve adherence to best practices for maintainability.
-   No obvious AI-induced naming errors; names seem human-generated and contextually appropriate.