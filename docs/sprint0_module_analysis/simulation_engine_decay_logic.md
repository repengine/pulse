# SPARC Analysis: engine.decay_logic

**Date of Analysis:** 2025-05-14
**Analyzer:** Roo

## 1. Module Intent/Purpose (Specification)

The [`simulation_engine/decay_logic.py`](simulation_engine/decay_logic.py:1) module is responsible for defining and applying decay patterns to symbolic overlays and numeric variables within the simulation's `WorldState`. Its primary role is to simulate the gradual reduction or erosion of these values over time, reflecting a more realistic and dynamic simulation environment. It currently implements linear decay and notes future support for exponential and conditional symbolic erosion.

## 2. Operational Status/Completeness

The module appears to be operational for its current scope (linear decay).
- **Placeholders/TODOs:**
    - Line 5-6: Mentions "future support for conditional symbolic erosion" and "exponential-style decay", indicating planned enhancements.
- **Completeness:** The core linear decay functionality for both symbolic overlays and general variables is implemented.

## 3. Implementation Gaps / Unfinished Next Steps

- **Exponential Decay:** Not yet implemented, as mentioned in the module docstring.
- **Conditional Symbolic Erosion:** Not yet implemented, as mentioned in the module docstring. This would likely involve more complex logic based on other state variables or events.
- **More Sophisticated Decay Models:** The module could be extended with other decay types (e.g., logarithmic, or custom curves).

## 4. Connections & Dependencies

### Direct Imports:
- **Project Modules:**
    - `from engine.worldstate import WorldState` ([`simulation_engine/decay_logic.py:11`](simulation_engine/decay_logic.py:11)) - Core dependency for accessing and modifying simulation state.
    - `from core.pulse_config import config_loader` ([`simulation_engine/decay_logic.py:22`](simulation_engine/decay_logic.py:22), [`simulation_engine/decay_logic.py:35`](simulation_engine/decay_logic.py:35), [`simulation_engine/decay_logic.py:56`](simulation_engine/decay_logic.py:56)) - Used to fetch configuration values, specifically `default_decay_rate` from `core_config.yaml`.
- **External Libraries:**
    - `typing.Optional` ([`simulation_engine/decay_logic.py:15`](simulation_engine/decay_logic.py:15)) - For type hinting.

### Touched Project Files (for dependency mapping):
To understand the dependencies and intent, the following project files were read:
- [`simulation_engine/decay_logic.py`](simulation_engine/decay_logic.py:1) (The module being analyzed)
- [`simulation_engine/worldstate.py`](simulation_engine/worldstate.py:1) (Defines `WorldState` and its components like `SymbolicOverlays` and `Variables`)
- [`core/pulse_config.py`](core/pulse_config.py:1) (Defines `config_loader` and how configurations are accessed, including `default_decay_rate`)
- [`config/core_config.yaml`](config/core_config.yaml:1) (Contains the actual value for `default_decay_rate`)
- [`core/path_registry.py`](core/path_registry.py:1) (Imported by [`core/pulse_config.py`](core/pulse_config.py:1) for path management, though not directly used by `decay_logic.py` for its primary operations beyond how `pulse_config` might resolve paths).

### Interactions:
- **Shared Data:**
    - Modifies `state.overlays` (specifically attributes like `hope`, `despair`, etc.) within the `WorldState` object.
    - Modifies `state.variables` (a dictionary of numeric variables) within the `WorldState` object.
    - Reads `default_decay_rate` from [`config/core_config.yaml`](config/core_config.yaml:1) via the `config_loader`.
- **Files:**
    - Indirectly depends on [`config/core_config.yaml`](config/core_config.yaml:1) for the `default_decay_rate`.
- **Databases/Queues:** No direct interaction.

### Input/Output Files:
- **Input:** Reads [`config/core_config.yaml`](config/core_config.yaml:1) for `default_decay_rate`.
- **Output:** No direct file output. Changes are made to the `WorldState` object in memory. Events are logged to `state.event_log`.

## 5. Function and Class Example Usages

**`linear_decay(value: float, rate: Optional[float] = None) -> float`**
```python
from engine.decay_logic import linear_decay

initial_value = 0.8
decay_rate = 0.05
decayed_value = linear_decay(initial_value, rate=decay_rate)
# decayed_value will be 0.75

# Using default rate from config
another_value = 0.6
decayed_again = linear_decay(another_value)
# decayed_again will be 0.6 - (default_decay_rate from core_config.yaml, e.g., 0.1) = 0.5
```

**`apply_overlay_decay(state: WorldState, decay_rate: Optional[float] = None)`**
```python
from engine.worldstate import WorldState, SymbolicOverlays
from engine.decay_logic import apply_overlay_decay

# Assume 'current_state' is an instance of WorldState
current_state = WorldState()
current_state.overlays.hope = 0.9
current_state.overlays.trust = 0.7

print(f"Before decay: Hope={current_state.overlays.hope}, Trust={current_state.overlays.trust}")
# Example: Before decay: Hope=0.9, Trust=0.7

apply_overlay_decay(current_state, decay_rate=0.02)

print(f"After decay: Hope={current_state.overlays.hope}, Trust={current_state.overlays.trust}")
# Example: After decay: Hope=0.88, Trust=0.68
# Event log will contain entries like:
# "[DECAY] hope: 0.900 → 0.880"
# "[DECAY] trust: 0.700 → 0.680"
```

**`decay_variable(state: WorldState, name: str, rate: Optional[float] = None, floor: float = 0.0)`**
```python
from engine.worldstate import WorldState, Variables
from engine.decay_logic import decay_variable

# Assume 'current_state' is an instance of WorldState
current_state = WorldState()
current_state.variables.data['resource_level'] = 100.0
current_state.variables.data['morale'] = 0.75

print(f"Before decay: Resource={current_state.variables.get('resource_level')}, Morale={current_state.variables.get('morale')}")
# Example: Before decay: Resource=100.0, Morale=0.75

decay_variable(current_state, 'resource_level', rate=5.0, floor=10.0)
decay_variable(current_state, 'morale', rate=0.05) # Uses default floor of 0.0

print(f"After decay: Resource={current_state.variables.get('resource_level')}, Morale={current_state.variables.get('morale')}")
# Example: After decay: Resource=95.0, Morale=0.7
# Event log will contain entries like:
# "[DECAY] Variable 'resource_level': 100.000 → 95.000"
# "[DECAY] Variable 'morale': 0.750 → 0.700"
```

## 6. Hardcoding Issues (SPARC Critical)

- **Overlay Names in `apply_overlay_decay`:**
  The list of symbolic overlays to decay is hardcoded: `["hope", "despair", "rage", "fatigue", "trust"]` ([`simulation_engine/decay_logic.py:37`](simulation_engine/decay_logic.py:37)).
  This is problematic because `SymbolicOverlays` in [`simulation_engine/worldstate.py`](simulation_engine/worldstate.py:1) supports dynamic overlays. The `apply_overlay_decay` function will not affect any dynamically added overlays.
  **Recommendation:** Modify `apply_overlay_decay` to iterate over `state.overlays.as_dict().keys()` or a similar method that retrieves all available overlays, rather than a fixed list. This aligns better with the dynamic nature of `SymbolicOverlays`.

- **Default Fallback for `default_decay_rate`:**
  In all three functions, if `config_loader.get_config_value("core_config.yaml", "default_decay_rate", 0.1)` is called, the `0.1` acts as a hardcoded fallback default if the key is not found in the YAML or the YAML itself is missing/malformed.
  While having a fallback is good, this value is repeated.
  **Recommendation:** Consider defining this ultimate fallback default in [`core/pulse_config.py`](core/pulse_config.py:1) (e.g., `DEFAULT_DECAY_RATE_FALLBACK = 0.1`) and referencing that constant if the YAML load fails or the key is absent. This centralizes the fallback. The current implementation in [`core/pulse_config.py`](core/pulse_config.py:1) already defines `DEFAULT_DECAY_RATE = 0.1` ([`core/pulse_config.py:25`](core/pulse_config.py:25)), which the `config_loader`'s `get_config_value` default parameter uses. This seems mostly fine, but the `decay_logic.py` functions *also* specify `0.1` as the default in their calls to `get_config_value`. This is redundant. The default should ideally only be specified in one place (either in `pulse_config.py` as a constant that `get_config_value` uses, or as the default parameter to `get_config_value` itself, but not both places and also in the calling function). The current setup is slightly confusing due to this repetition. The most robust way is for `get_config_value` to have its own fallback if the key is missing, and `decay_logic.py` functions just call it without providing a default.

## 7. Coupling Points

- **High Coupling with `WorldState`:** The module is tightly coupled to the `WorldState` class structure, particularly `state.overlays` and `state.variables`. This is expected for a module that modifies the world state.
- **Coupling with `core.pulse_config.config_loader`:** Relies on this specific mechanism for fetching the `default_decay_rate`. Changes to the config loading mechanism or file structure (`core_config.yaml`) could break this module.
- **Implicit Coupling on Overlay Names:** The `apply_overlay_decay` function is implicitly coupled to the specific names of core symbolic overlays if it doesn't adapt to iterate all existing overlays.

## 8. Existing Tests (SPARC Refinement)

- **Test Coverage:** The prompt does not provide information about existing tests for this module. A dedicated test file (e.g., `tests/simulation_engine/test_decay_logic.py`) would be necessary.
- **Test Quality Gaps (Assumed, if tests exist):**
    - Tests should cover cases where `rate` is provided and when it's `None` (falling back to config).
    - Tests for `linear_decay` should check boundary conditions (value at or below zero, value close to zero).
    - Tests for `apply_overlay_decay` should verify:
        - All hardcoded overlays are decayed correctly.
        - Dynamically added overlays are *not* decayed (current limitation) or *are* decayed (if fixed).
        - Values are correctly clamped between 0.0 and 1.0.
        - Event logging occurs as expected.
    - Tests for `decay_variable` should verify:
        - Decay with and without a provided rate.
        - Correct application of the `floor` value.
        - Behavior when the variable doesn't exist (should default to 0.0 before decay).
        - Event logging and `state.update_variable` calls.
    - Test for `ValueError` when decay rate cannot be resolved ([`simulation_engine/decay_logic.py:25`](simulation_engine/decay_logic.py:25)).

## 9. Module Architecture and Flow (SPARC Architecture)

- **Structure:** The module consists of three public functions:
    - [`linear_decay()`](simulation_engine/decay_logic.py:17): A utility function performing the core decay calculation.
    - [`apply_overlay_decay()`](simulation_engine/decay_logic.py:29): Applies decay to a predefined set of symbolic overlays in `WorldState`.
    - [`decay_variable()`](simulation_engine/decay_logic.py:45): Applies decay to a specified numeric variable in `WorldState.variables`.
- **Flow:**
    1. Functions are called with a `WorldState` object and optional decay parameters.
    2. If `rate` is not provided, it's fetched from [`config/core_config.yaml`](config/core_config.yaml:1) via `config_loader`. A `ValueError` is raised if the rate cannot be determined.
    3. For `apply_overlay_decay`, it iterates through a hardcoded list of overlay names, gets their current values from `state.overlays`, applies `linear_decay`, updates the overlay, and logs the event.
    4. For `decay_variable`, it gets the variable's current value from `state.variables`, applies decay (respecting a `floor`), updates the variable in `state.variables` and via `state.update_variable()`, and logs the event.
- **Modularity:**
    - The `linear_decay` function is well-encapsulated.
    - The functions for overlays and variables are distinct.
    - The module has a clear, focused responsibility (decay logic).
- **Potential Improvements:**
    - Decouple `apply_overlay_decay` from the hardcoded list of overlay names to support dynamic overlays fully.
    - Centralize the ultimate fallback for `default_decay_rate` if the configuration system doesn't robustly provide one.

## 10. Naming Conventions (SPARC Maintainability)

- **Functions:** `linear_decay`, `apply_overlay_decay`, `decay_variable` are clear and follow Python's `snake_case` convention.
- **Parameters:** `value`, `rate`, `state`, `name`, `floor` are descriptive.
- **Variables:** `current_value`, `decayed`, `current`, `overlay_name` are clear.
- **Docstrings:** Present for the module and all functions, explaining their purpose, and for `decay_variable`, its parameters. The docstring for `linear_decay` could explicitly mention the 0-1 clamping if that's an implicit assumption for overlays, though the function itself only clamps at 0. The clamping to 1.0 for overlays happens in `SymbolicOverlays.__setattr__`.
- **Clarity:** The code is generally clear and easy to understand.
- **Comments:** A comment at line 12 explains the removal of a hardcoded import, which is good practice.

## 11. SPARC Compliance Summary

- **Specification:**
    - **Met:** The module's purpose is clearly defined in its docstring.
- **Modularity/Architecture:**
    - **Mostly Met:** The module is focused on decay logic. The hardcoding of overlay names in `apply_overlay_decay` slightly reduces its ideal modularity with respect to the dynamic capabilities of `SymbolicOverlays`.
- **Refinement Focus:**
    - **Testability:**
        - **Needs Improvement (Assumed):** No tests provided, but clear areas for testing identified. The functions are generally testable.
    - **Security (Hardcoding):**
        - **Partially Met:** No secrets or sensitive paths are hardcoded. However, the list of overlay names in `apply_overlay_decay` is a form of data hardcoding that limits flexibility. The default fallback `0.1` for decay rate is repeated, though ultimately sourced from config or a constant in `pulse_config`.
    - **Maintainability:**
        - **Good:** Naming conventions are good, code is clear, and docstrings are present. The hardcoded overlay list is a minor maintainability concern if new core overlays are added or if dynamic overlays are intended to be decayed by this function.
- **No Hardcoding (Critical):**
    - **Needs Improvement:** As noted, the overlay names in `apply_overlay_decay` are hardcoded.

**Overall SPARC Alignment:** The module is reasonably well-aligned with SPARC principles but could be improved by addressing the hardcoded overlay names to enhance flexibility and maintainability, and by ensuring comprehensive test coverage. The dependency on configuration for `default_decay_rate` is good.