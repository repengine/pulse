# Module Analysis: `symbolic_system/overlays.py`

## Table of Contents

- [Module Intent/Purpose](#module-intentpurpose)
- [Operational Status/Completeness](#operational-statuscompleteness)
- [Implementation Gaps / Unfinished Next Steps](#implementation-gaps--unfinished-next-steps)
- [Connections & Dependencies](#connections--dependencies)
- [Function and Class Example Usages](#function-and-class-example-usages)
- [Hardcoding Issues](#hardcoding-issues)
- [Coupling Points](#coupling-points)
- [Existing Tests](#existing-tests)
- [Module Architecture and Flow](#module-architecture-and-flow)
- [Naming Conventions](#naming-conventions)

## Module Intent/Purpose

The primary role of the [`symbolic_system/overlays.py`](symbolic_system/overlays.py:) module is to define and manage the symbolic overlay system within the Pulse simulation. These overlays represent latent emotional-sentiment variables such as "Hope," "Despair," "Rage," "Fatigue," and "Trust." The module provides centralized functions to access, normalize, and modulate these overlay values and their interactions, aiming to enable coherent symbolic behavior across different parts of the simulation.

## Operational Status/Completeness

The module appears to be operationally complete for its defined scope. The functions cover getting overlay values, checking for dominance, boosting/suppressing overlays, and applying basic interactions between them. There are no explicit "TODO" comments or obvious placeholders suggesting unfinished core functionality. The [`apply_overlay_interactions()`](symbolic_system/overlays.py:90) function includes different behaviors based on an `operation_level`, indicating a degree of maturity.

## Implementation Gaps / Unfinished Next Steps

-   **Advanced Interactions:** The current overlay interactions in [`apply_overlay_interactions()`](symbolic_system/overlays.py:90) are relatively simple (e.g., "Hope boosts Trust"). More complex, nuanced, or conditional interactions could be developed. The system could be extended to allow dynamic registration of interaction rules or more sophisticated logic based on combinations of overlays or external simulation events.
-   **Minimal Mode Sophistication:** The "minimal" operation level in [`apply_overlay_interactions()`](symbolic_system/overlays.py:108) is a simplified version. A more granular or adaptive approach to scaling interaction complexity for different modes (like training or retrodiction) could be beneficial.
-   **External Triggers:** While overlays influence each other, the module doesn't explicitly define mechanisms for external simulation events or agent actions to directly trigger more complex overlay shifts beyond simple `boost` or `suppress`.
-   **Configuration of Interactions:** The interaction logic (e.g., which overlay affects which, and by how much) is hardcoded within [`apply_overlay_interactions()`](symbolic_system/overlays.py:90). This could be made more configurable, perhaps by loading rules from an external configuration file.

## Connections & Dependencies

### Direct Project Module Imports:
-   [`simulation_engine.worldstate.WorldState`](simulation_engine/worldstate.py:) (imported as `WorldState` from [`simulation_engine.worldstate`](simulation_engine/worldstate.py:14))
-   [`simulation_engine.state_mutation.adjust_overlay`](simulation_engine/state_mutation.py:) (imported as `adjust_overlay` from [`simulation_engine.state_mutation`](simulation_engine/state_mutation.py:15))
-   [`core.pulse_config.MODULES_ENABLED`](core/pulse_config.py:) (referenced in [`OVERLAY_NAMES`](symbolic_system/overlays.py:27) retrieval, though `MODULES_ENABLED` itself is not directly used in the provided snippet for `OVERLAY_NAMES`)
-   [`core.pulse_config.OVERLAY_NAMES`](core/pulse_config.py:) (retrieved via `getattr(__import__('core.pulse_config'), 'OVERLAY_NAMES', ...)` at line [`symbolic_system/overlays.py:27`](symbolic_system/overlays.py:27))
-   [`core.pulse_config.ENABLE_SYMBOLIC_SYSTEM`](core/pulse_config.py:) (imported locally within [`boost_overlay()`](symbolic_system/overlays.py:47) and [`suppress_overlay()`](symbolic_system/overlays.py:63))
-   [`symbolic_system.optimization`](symbolic_system/optimization.py:) (imports [`lazy_symbolic()`](symbolic_system/optimization.py:), [`cached_symbolic()`](symbolic_system/optimization.py:), [`training_optimized()`](symbolic_system/optimization.py:), [`get_operation_level()`](symbolic_system/optimization.py:) at lines [`symbolic_system/overlays.py:20-25`](symbolic_system/overlays.py:20-25))

### External Library Dependencies:
-   `typing` (standard Python library for type hints: `List`, `Dict`, `Optional` imported at line [`symbolic_system/overlays.py:16`](symbolic_system/overlays.py:16))

### Interaction with Other Modules via Shared Data:
-   Primarily interacts by modifying the `overlays` attribute of the [`WorldState`](simulation_engine/worldstate.py:) object passed to its functions.
-   Logs events using `state.log_event()` (e.g., in [`reinforce_synergy()`](symbolic_system/overlays.py:79)).

### Input/Output Files:
-   The module does not directly read from or write to files.
-   It relies on the [`WorldState`](simulation_engine/worldstate.py:) object which might be part of a larger persistence mechanism elsewhere in the system.
-   Event logging via `state.log_event()` implies output to a logging system.

## Function and Class Example Usages

(Assuming `state` is an instance of `WorldState`)

-   **`get_overlay_value(state: WorldState, name: str) -> float`**
    ```python
    hope_value = get_overlay_value(state, "hope")
    print(f"Current hope: {hope_value}")
    ```
-   **`is_overlay_dominant(state: WorldState, name: str, threshold: float = 0.65) -> bool`**
    ```python
    if is_overlay_dominant(state, "rage"):
        print("Rage is dominant.")
    if is_overlay_dominant(state, "trust", threshold=0.75):
        print("Trust is highly dominant.")
    ```
-   **`boost_overlay(state: WorldState, name: str, amount: float = 0.02)`**
    ```python
    boost_overlay(state, "hope", amount=0.05) # Increase hope by 0.05
    ```
-   **`suppress_overlay(state: WorldState, name: str, amount: float = 0.02)`**
    ```python
    suppress_overlay(state, "despair") # Decrease despair by 0.02
    ```
-   **`reinforce_synergy(state: WorldState, trigger: str, affected: str, factor: float = 0.01)`**
    ```python
    # If 'hope' is dominant, 'trust' will be boosted by 'factor'
    reinforce_synergy(state, "hope", "trust", factor=0.015)
    ```
-   **`apply_overlay_interactions(state: WorldState)`**
    ```python
    # Called once per turn to apply standard overlay interactions
    apply_overlay_interactions(state)
    ```
-   **`get_overlay_summary(state: WorldState) -> Dict[str, Dict[str, float]]`**
    ```python
    summary = get_overlay_summary(state)
    print(f"Dominant overlays: {summary['dominant']}")
    print(f"Moderate overlays: {summary['moderate']}")
    ```

## Hardcoding Issues

-   **Default Overlay Names:** The fallback list `["hope", "despair", "rage", "fatigue", "trust"]` for [`OVERLAY_NAMES`](symbolic_system/overlays.py:27) is hardcoded. While it attempts to load from `core.pulse_config`, this default exists.
-   **Thresholds:**
    -   [`is_overlay_dominant()`](symbolic_system/overlays.py:39): `threshold` defaults to `0.65`.
    -   [`apply_overlay_interactions()`](symbolic_system/overlays.py:90) (minimal mode): checks for `>= 0.7` for "hope" and "despair".
    -   [`get_overlay_summary()`](symbolic_system/overlays.py:131): uses `0.65` to categorize "dominant" and `0.35` for "moderate".
-   **Adjustment Amounts/Factors:**
    -   [`boost_overlay()`](symbolic_system/overlays.py:47) / [`suppress_overlay()`](symbolic_system/overlays.py:63): `amount` defaults to `0.02`.
    -   [`reinforce_synergy()`](symbolic_system/overlays.py:79): `factor` defaults to `0.01`.
    -   [`apply_overlay_interactions()`](symbolic_system/overlays.py:90) (full mode): uses specific factors/amounts like `0.01`, `0.015`, `0.02`.
    -   [`apply_overlay_interactions()`](symbolic_system/overlays.py:90) (minimal mode): uses `0.01`.
-   **Cache TTL:** [`get_overlay_summary()`](symbolic_system/overlays.py:131) uses a hardcoded `ttl_seconds=300` for its cache.
-   **Operation Level Strings:** The strings `"none"` and `"minimal"` are used in [`apply_overlay_interactions()`](symbolic_system/overlays.py:104) to determine behavior. The "full" mode is implied. These could be enum or constant definitions.
-   **Default Overlay Value:** [`get_overlay_value()`](symbolic_system/overlays.py:31) returns `0.0` if an overlay is not found.

## Coupling Points

-   **`WorldState` Object:** The module is tightly coupled to the [`simulation_engine.worldstate.WorldState`](simulation_engine/worldstate.py:) object, as it's a required parameter for nearly all functions and its `overlays` attribute is directly manipulated.
-   **`adjust_overlay` Function:** Relies on [`simulation_engine.state_mutation.adjust_overlay()`](simulation_engine/state_mutation.py:) for the actual modification of overlay values.
-   **`core.pulse_config`:** Depends on [`core.pulse_config`](core/pulse_config.py:) for the list of [`OVERLAY_NAMES`](symbolic_system/overlays.py:27) and the [`ENABLE_SYMBOLIC_SYSTEM`](symbolic_system/overlays.py:53) flag. Changes in `core.pulse_config` regarding these could directly impact the module's behavior.
-   **`symbolic_system.optimization` Decorators:** The use of decorators ([`lazy_symbolic()`](symbolic_system/optimization.py:), [`cached_symbolic()`](symbolic_system/optimization.py:), [`training_optimized()`](symbolic_system/optimization.py:)) creates a dependency on the [`symbolic_system.optimization`](symbolic_system/optimization.py:) module.
-   **`turn_engine.py` (Implied):** The docstring for [`apply_overlay_interactions()`](symbolic_system/overlays.py:90) mentions it's "Called once per turn in `turn_engine.py` or via rule engine," implying a coupling point for its primary execution.

## Existing Tests

Based on the provided file listing, a dedicated test file such as `tests/symbolic_system/test_overlays.py` does not appear to exist in the immediate `tests/symbolic_system/` directory. The existing files are `tests/symbolic_system/__init__.py` and `tests/symbolic_system/gravity/test_residual_gravity_engine.py`.
Therefore, it's likely that:
-   Tests for this module are integrated into broader integration tests.
-   Tests might exist in a different location not immediately obvious from the partial file list.
-   Dedicated unit tests for this specific module may be missing.
Further investigation by searching the `tests/` directory would be needed to confirm the full extent of test coverage.

## Module Architecture and Flow

The module provides a set of utility functions to interact with symbolic emotional overlays stored within the `WorldState`.
-   **Data Model:** Overlays are attributes (e.g., `hope`, `despair`) on a `state.overlays` object, presumably numerical values (floats).
-   **Core Logic:**
    -   Functions like [`get_overlay_value()`](symbolic_system/overlays.py:31), [`is_overlay_dominant()`](symbolic_system/overlays.py:39), [`boost_overlay()`](symbolic_system/overlays.py:47), and [`suppress_overlay()`](symbolic_system/overlays.py:63) provide basic CRUD-like (Create-Read-Update-Delete) operations and checks on individual overlays.
    -   [`reinforce_synergy()`](symbolic_system/overlays.py:79) implements a simple rule for one overlay to boost another if the trigger overlay is dominant.
    -   The main interaction logic is encapsulated in [`apply_overlay_interactions()`](symbolic_system/overlays.py:90). This function is designed to be called periodically (e.g., per simulation turn). It applies a set of predefined rules for how overlays affect each other.
-   **Optimization:** The module leverages decorators from [`symbolic_system.optimization`](symbolic_system/optimization.py:) ([`lazy_symbolic()`](symbolic_system/optimization.py:), [`cached_symbolic()`](symbolic_system/optimization.py:), [`training_optimized()`](symbolic_system/optimization.py:)) to potentially improve performance, especially for frequently called or expensive operations.
-   **Conditional Execution:** Overlay modifications via [`boost_overlay()`](symbolic_system/overlays.py:47) and [`suppress_overlay()`](symbolic_system/overlays.py:63) are conditional on the [`ENABLE_SYMBOLIC_SYSTEM`](symbolic_system/overlays.py:53) flag from [`core.pulse_config`](core/pulse_config.py:). The [`apply_overlay_interactions()`](symbolic_system/overlays.py:90) function also has different execution paths based on an `operation_level` (full, minimal, none).
-   **Summarization:** [`get_overlay_summary()`](symbolic_system/overlays.py:131) provides a categorized view of the overlay states, which is cached for performance.

## Naming Conventions

-   **Functions:** Adhere to `snake_case` (e.g., [`get_overlay_value()`](symbolic_system/overlays.py:31), [`apply_overlay_interactions()`](symbolic_system/overlays.py:90)), which is standard Python practice (PEP 8). Names are generally descriptive and clearly indicate their purpose.
-   **Variables:** Local variables use `snake_case` (e.g., `operation_level`, `value`). The module-level constant [`OVERLAY_NAMES`](symbolic_system/overlays.py:27) uses `UPPER_SNAKE_CASE`, which is also PEP 8 compliant.
-   **Parameters:** Function parameters also use `snake_case` (e.g., `state`, `name`, `threshold`).
-   **Clarity:** The naming is clear and does not show obvious signs of AI-generated names that might be awkward or non-idiomatic for Python.
-   **Consistency:** Naming is consistent throughout the module.

Overall, the naming conventions are good and follow Python community standards.