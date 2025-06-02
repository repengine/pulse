# Module Analysis: `simulation_engine/state_mutation.py`

## 1. Module Intent/Purpose

The primary role of the [`simulation_engine/state_mutation.py`](simulation_engine/state_mutation.py) module is to manage and execute controlled changes to the `WorldState` object within the Pulse simulation engine. It handles the mutation and update logic for `WorldState` variables, symbolic overlays (emotional states), and capital exposure. The module ensures that all updates are validated, bounded, and logged for traceability, supporting inputs from causal rules, decay logic, and external signal ingestion.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope.
- It contains functions for updating numeric variables ([`update_numeric_variable()`](simulation_engine/state_mutation.py:27)), decaying symbolic overlays ([`decay_overlay()`](simulation_engine/state_mutation.py:59)), adjusting symbolic overlays ([`adjust_overlay()`](simulation_engine/state_mutation.py:94)), and adjusting capital ([`adjust_capital()`](simulation_engine/state_mutation.py:151)).
- Each function includes logging for traceability and, where appropriate, logs learning events.
- The logic for handling symbolic system enablement (globally and per mode) within [`adjust_overlay()`](simulation_engine/state_mutation.py:94) is present.
- There are no obvious placeholders (e.g., `pass`, `NotImplementedError`) or "TODO" comments in the provided code.

## 3. Implementation Gaps / Unfinished Next Steps

- **Extensibility for New State Types:** While the module handles numeric variables, symbolic overlays, and capital, if new categories of state (e.g., complex objects, relational data) were to be introduced into `WorldState`, this module would need corresponding mutation functions.
- **Advanced Validation Logic:** The current validation is primarily bounds checking. More complex validation rules (e.g., inter-variable consistency, rate-of-change limits) are not explicitly present and might be a logical next step if required.
- **Configuration of Default Bounds/Rates:** Default values for `min_val`, `max_val` in [`update_numeric_variable()`](simulation_engine/state_mutation.py:27) and `rate` in [`decay_overlay()`](simulation_engine/state_mutation.py:59) are hardcoded. These could potentially be made configurable.
- **Symbolic Processing Mode Granularity:** The [`adjust_overlay()`](simulation_engine/state_mutation.py:94) function checks `CURRENT_SYSTEM_MODE` against `SYMBOLIC_PROCESSING_MODES`. The management and definition of these modes and their specific behaviors (e.g., "minimal_processing" for "retrodiction") might imply a more extensive configuration system for symbolic processing that isn't fully detailed within this module alone.

## 4. Connections & Dependencies

### Direct Imports from Other Project Modules:
- [`engine.worldstate`](simulation_engine/worldstate.py) (specifically the `WorldState` class)
- [`core.pulse_learning_log`](core/pulse_learning_log.py) (specifically the [`log_learning_event()`](core/pulse_learning_log.py) function)
- [`symbolic_system.context`](symbolic_system/context.py) (specifically the [`is_symbolic_enabled()`](symbolic_system/context.py) function, though the comment in [`adjust_overlay()`](simulation_engine/state_mutation.py:113) indicates a direct import of config values is preferred for freshness)
- [`core.pulse_config`](core/pulse_config.py) (imports `ENABLE_SYMBOLIC_SYSTEM`, `CURRENT_SYSTEM_MODE`, `SYMBOLIC_PROCESSING_MODES` directly within [`adjust_overlay()`](simulation_engine/state_mutation.py:114))

### External Library Dependencies:
- `typing` (for `Any`, `Union`, `Optional`)
- `datetime` (for `datetime`, `timezone`)

### Interaction with Other Modules via Shared Data:
- Primarily interacts with the `WorldState` object, which is a central data structure likely shared and accessed by many other modules within `simulation_engine` and potentially other parts of the Pulse system. Changes made here directly affect the state observed and used by other components.
- Logs events using `state.log_event()`, implying the `WorldState` object has a method for logging, which might write to a shared log file or system.
- Uses [`log_learning_event()`](core/pulse_learning_log.py), suggesting interaction with a centralized learning log system.

### Input/Output Files:
- **Input:** Implicitly, the configuration values from [`core.pulse_config`](core/pulse_config.py) (e.g., `ENABLE_SYMBOLIC_SYSTEM`) act as inputs.
- **Output:**
    - Learning logs via [`log_learning_event()`](core/pulse_learning_log.py).
    - General event logs via `state.log_event()`. The destination of these logs is not specified within this module but is a form of output.

## 5. Function and Class Example Usages

The module provides clear examples in the docstrings for each of its public functions:

- **[`update_numeric_variable(state: WorldState, name: str, delta: float, min_val: float = 0.0, max_val: float = 1.0) -> float`](simulation_engine/state_mutation.py:27):**
  ```python
  # Assuming 'state' is an initialized WorldState object
  new_value = update_numeric_variable(state, "inflation_index", +0.03, min_val=0.0, max_val=2.0)
  print(f"Inflation index is now {new_value}")
  ```
  This function is used to safely increment or decrement a numeric variable within the `state.variables` attribute, ensuring it stays within `min_val` and `max_val`.

- **[`decay_overlay(state: WorldState, overlay: str, rate: float = 0.01) -> Optional[float]`](simulation_engine/state_mutation.py:59):**
  ```python
  # Assuming 'state' is an initialized WorldState object
  new_value = decay_overlay(state, "hope", rate=0.02)
  if new_value is not None:
      print(f"Hope decayed to {new_value}")
  ```
  This function applies a gradual reduction to a symbolic overlay (e.g., "hope", "trust") stored in `state.overlays`, representing a natural return to a baseline.

- **[`adjust_overlay(state: WorldState, overlay: str, delta: float) -> Optional[float]`](simulation_engine/state_mutation.py:94):**
  ```python
  # Assuming 'state' is an initialized WorldState object
  new_value = adjust_overlay(state, "trust", +0.1)
  if new_value is not None:
      print(f"Trust increased to {new_value}")
  ```
  This function modifies a symbolic overlay in `state.overlays` based on a `delta`, bounded between 0.0 and 1.0. It respects global and mode-specific symbolic system enablement flags.

- **[`adjust_capital(state: WorldState, asset: str, delta: float) -> Optional[float]`](simulation_engine/state_mutation.py:151):**
  ```python
  # Assuming 'state' is an initialized WorldState object
  new_value = adjust_capital(state, "nvda", +500.0)
  if new_value is not None:
      print(f"NVDA position increased to ${new_value:.2f}")
  ```
  This function updates capital exposure for a given asset in `state.capital`. These values are not bounded like overlays and can be negative.

## 6. Hardcoding Issues

- **Default Values for Numeric Variables:** In [`update_numeric_variable()`](simulation_engine/state_mutation.py:27), if a variable doesn't exist, it's initialized to `0.0` (line 52: `current = getattr(state.variables, name, 0.0)`). The default `min_val` is `0.0` and `max_val` is `1.0`. These might be too restrictive or not suitable for all numeric variables.
- **Default Decay Rate:** In [`decay_overlay()`](simulation_engine/state_mutation.py:59), the default `rate` is `0.01`.
- **Overlay Bounds:** Symbolic overlays in [`adjust_overlay()`](simulation_engine/state_mutation.py:94) are hardcoded to be bounded between `0.0` and `1.0` (line 127: `new_value = max(0.0, min(1.0, current_value + delta))`).
- **String Literals for Logging/Events:** Event types like `"overlay_shift"` (line 82, 138) and `"capital_shift"` (line 174) are hardcoded strings. Overlay names (`"hope"`, `"trust"`, `"despair"`) and asset names (`"nvda"`, `"msft"`, `"cash"`) are provided as examples in docstrings but would be passed as arguments during runtime.
- **Symbolic Processing Mode String:** The string `"retrodiction"` is used to check for minimal processing mode in [`adjust_overlay()`](simulation_engine/state_mutation.py:133).

## 7. Coupling Points

- **`WorldState` Object:** The module is tightly coupled to the structure of the [`WorldState`](simulation_engine/worldstate.py) object, specifically its `variables`, `overlays`, and `capital` attributes, and its `log_event` method. Changes to `WorldState`'s structure would likely require changes in this module.
- **[`core.pulse_config`](core/pulse_config.py):** The [`adjust_overlay()`](simulation_engine/state_mutation.py:94) function directly imports and uses `ENABLE_SYMBOLIC_SYSTEM`, `CURRENT_SYSTEM_MODE`, and `SYMBOLIC_PROCESSING_MODES` from [`core.pulse_config`](core/pulse_config.py). This creates a strong coupling to these specific configuration variables and their interpretation.
- **[`core.pulse_learning_log`](core/pulse_learning_log.py):** All primary functions use [`log_learning_event()`](core/pulse_learning_log.py), creating a dependency on this logging mechanism and its expected event structure.
- **Symbolic System Context:** The module's behavior, particularly for overlays, is dependent on the broader symbolic system's enabled status, managed externally but checked within [`adjust_overlay()`](simulation_engine/state_mutation.py:94).

## 8. Existing Tests

- The problem description does not provide information about existing tests (e.g., by checking for a corresponding `tests/simulation_engine/test_state_mutation.py`).
- To assess existing tests, one would typically look for a test file like `tests/simulation_engine/test_state_mutation.py` or `tests/test_state_mutation.py`.
- **Assumed Gaps (if no tests exist):**
    - Tests for `update_numeric_variable` covering cases like: creation of new variable, updates within bounds, updates hitting min/max bounds, updates attempting to go out of bounds.
    - Tests for `decay_overlay` covering: decay of existing overlay, decay hitting zero, attempt to decay non-existent overlay.
    - Tests for `adjust_overlay` covering: adjustment of existing overlay within bounds, adjustments hitting 0 or 1, attempts to go out of bounds, behavior when symbolic system is disabled globally, behavior when symbolic system is disabled for the current mode, behavior in "retrodiction" minimal processing mode.
    - Tests for `adjust_capital` covering: adjustment of existing asset (positive and negative deltas), creation of new asset (if applicable, though current code updates existing), adjustments resulting in negative capital.
    - Verification of correct logging (both `state.log_event` and `log_learning_event`) for all operations.

## 9. Module Architecture and Flow

- **Architecture:** The module consists of a set of stateless utility functions that operate on a passed-in `WorldState` object. Each function is responsible for a specific type of state mutation (numeric, overlay decay, overlay adjustment, capital adjustment).
- **Control Flow:**
    - External callers (e.g., rule engine, simulation loop) invoke one of the public functions with the current `WorldState` and mutation parameters.
    - **`update_numeric_variable`**: Reads the current value (or defaults to 0.0), calculates the new value applying delta and bounds, updates the `WorldState`, logs, and returns the new value.
    - **`decay_overlay`**: Reads the current overlay value. If it exists, calculates decay, updates `WorldState`, logs (general and learning), and returns the new value. Returns `None` if overlay doesn't exist.
    - **`adjust_overlay`**:
        - Checks global symbolic system enablement (`ENABLE_SYMBOLIC_SYSTEM` from [`core.pulse_config`](core/pulse_config.py)). If disabled, returns current value (no-op).
        - Checks mode-specific symbolic processing enablement (`CURRENT_SYSTEM_MODE` and `SYMBOLIC_PROCESSING_MODES` from [`core.pulse_config`](core/pulse_config.py)). If disabled for mode, returns current value (no-op).
        - If enabled, reads current overlay value. If it exists, calculates new value applying delta and bounds (0.0 to 1.0).
        - Updates `WorldState`.
        - Checks for "minimal_processing" mode (e.g., "retrodiction"). If not minimal, logs events (general and learning).
        - Returns the new value. Returns `None` if overlay doesn't exist initially.
    - **`adjust_capital`**: Checks if asset exists in `state.capital`. If yes, reads current value, calculates new value with delta (unbounded), updates `WorldState`, logs (general and learning), and returns new value. Returns `None` if asset doesn't exist.
- **Data Flow:** Data (variable names, deltas, asset names) flows into the functions. The functions read from and write to the `WorldState` object. New values are returned. Logging information is sent to external logging systems.

## 10. Naming Conventions

- **Module Name (`state_mutation.py`):** Clear and descriptive.
- **Function Names (`update_numeric_variable`, `decay_overlay`, `adjust_overlay`, `adjust_capital`):** Verb-noun style, clearly indicating their action. Consistent.
- **Variable Names (`state`, `name`, `delta`, `min_val`, `max_val`, `overlay`, `rate`, `asset`, `current_value`, `updated`, `new_value`):** Generally clear and follow PEP 8 (snake_case for variables and functions).
- **Constants/Config Imports (`ENABLE_SYMBOLIC_SYSTEM`, `CURRENT_SYSTEM_MODE`, `SYMBOLIC_PROCESSING_MODES`):** Uppercase with underscores, typical for constants, imported from [`core.pulse_config`](core/pulse_config.py).
- **Docstrings and Comments:** Well-documented with clear explanations and examples.
- **Potential AI Assumption Errors/Deviations:**
    - The author tag "Pulse v3.5" (line 17) seems like an AI-generated placeholder or a project-internal versioning tag.
    - The comment in [`adjust_overlay()`](simulation_engine/state_mutation.py:112-113) `"# Import directly inside function to get the freshest values # Do not use is_symbolic_enabled() to ensure we get the actual current value"` suggests a deliberate choice to bypass a potentially cached or less direct way of checking symbolic system status, which is a nuanced decision likely based on deeper system knowledge. This is good practice if config can change dynamically.
- No significant deviations from PEP 8 are apparent in the naming conventions. Consistency is good.