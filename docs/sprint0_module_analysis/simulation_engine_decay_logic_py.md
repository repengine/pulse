# Module Analysis: `simulation_engine/decay_logic.py`

## 1. Module Intent/Purpose

The primary role of the [`simulation_engine/decay_logic.py`](../../simulation_engine/decay_logic.py) module is to define and apply various decay patterns to symbolic overlays and numeric variables within the simulation's [`WorldState`](../../simulation_engine/worldstate.py:11). This includes mechanisms for linear decay and outlines future support for more complex decay models like exponential decay and conditional symbolic erosion.

## 2. Operational Status/Completeness

The module appears operational for its current scope, primarily implementing linear decay.
- The docstring explicitly mentions "future support for conditional symbolic erosion" ([`simulation_engine/decay_logic.py:6`](../../simulation_engine/decay_logic.py:6)) and "exponential-style decay" ([`simulation_engine/decay_logic.py:5`](../../simulation_engine/decay_logic.py:5)), indicating planned features that are not yet implemented.
- No other obvious placeholders (e.g., `TODO` comments) are present in the implemented code.

## 3. Implementation Gaps / Unfinished Next Steps

- **Conditional Symbolic Erosion:** As mentioned in the module docstring ([`simulation_engine/decay_logic.py:6`](../../simulation_engine/decay_logic.py:6)), this feature is planned but not implemented.
- **Exponential-Style Decay:** Also mentioned in the docstring ([`simulation_engine/decay_logic.py:5`](../../simulation_engine/decay_logic.py:5)), this decay pattern is not yet implemented.
- **Advanced Decay Models:** The current implementation focuses on simple linear decay. Logical next steps could involve introducing more sophisticated decay models based on various factors or curves.
- **Dynamic Overlay List:** The `apply_overlay_decay` function uses a hardcoded list of overlay names. This could be made more dynamic or configurable.

## 4. Connections & Dependencies

### Direct Project Module Imports
- [`engine.worldstate.WorldState`](../../simulation_engine/worldstate.py:11): Used for accessing and modifying simulation state, including overlays and variables.
- [`core.pulse_config.config_loader`](../../core/pulse_config.py): Used by all decay functions ([`linear_decay`](../../simulation_engine/decay_logic.py:17), [`apply_overlay_decay`](../../simulation_engine/decay_logic.py:29), [`decay_variable`](../../simulation_engine/decay_logic.py:45)) to fetch the `default_decay_rate` from [`core_config.yaml`](../../core/pulse_config.py) if no rate is explicitly provided.

### External Library Dependencies
- `typing.Optional`: Used for type hinting optional parameters.

### Interaction with Other Modules via Shared Data
- **[`WorldState`](../../simulation_engine/worldstate.py:11) Object:** The module directly reads and modifies attributes of the `WorldState` object passed to its functions (e.g., `state.overlays`, `state.variables`).
- **Configuration File (`core_config.yaml`):** Reads the `default_decay_rate` via the [`config_loader`](../../core/pulse_config.py).

### Input/Output Files
- **Input:** Reads configuration from [`core_config.yaml`](../../core/pulse_config.py) (indirectly via [`config_loader`](../../core/pulse_config.py)).
- **Output:** Logs decay events using the `state.log_event()` method of the [`WorldState`](../../simulation_engine/worldstate.py:11) object (e.g., [`simulation_engine/decay_logic.py:42`](../../simulation_engine/decay_logic.py:42), [`simulation_engine/decay_logic.py:62`](../../simulation_engine/decay_logic.py:62)).

## 5. Hardcoding Issues

- **Overlay Names:** The list of overlay names (`["hope", "despair", "rage", "fatigue", "trust"]`) in [`apply_overlay_decay`](../../simulation_engine/decay_logic.py:37) is hardcoded. This limits flexibility if new overlays are added or if the set of decayable overlays needs to change without code modification.
- **Default Decay Rate Fallback:** If the [`config_loader`](../../core/pulse_config.py) fails to retrieve `"default_decay_rate"` from [`"core_config.yaml"`](simulation_engine/decay_logic.py:23), a fallback value of `0.1` is used within the functions ([`linear_decay`](../../simulation_engine/decay_logic.py:23), [`apply_overlay_decay`](../../simulation_engine/decay_logic.py:36), [`decay_variable`](../../simulation_engine/decay_logic.py:57)). While this provides a default, it might obscure configuration issues.
- **Default Floor Value:** The [`decay_variable`](../../simulation_engine/decay_logic.py:45) function has a default `floor` parameter set to `0.0`.

## 6. Coupling Points

- **[`WorldState`](../../simulation_engine/worldstate.py:11):** The module is tightly coupled to the `WorldState` class structure, directly accessing and modifying its `overlays` and `variables` attributes, and using its `log_event` and `update_variable` methods.
- **[`core.pulse_config.config_loader`](../../core/pulse_config.py):** All primary functions rely on this for fetching the default decay rate, creating a dependency on the configuration loading mechanism and the presence/structure of [`core_config.yaml`](../../core/pulse_config.py).

## 7. Existing Tests

- No dedicated test file (e.g., `tests/test_decay_logic.py`) was found in the `tests/` directory during the analysis. This indicates a potential gap in unit testing for this module's functionality.

## 8. Module Architecture and Flow

- The module consists of three public functions: [`linear_decay`](../../simulation_engine/decay_logic.py:17), [`apply_overlay_decay`](../../simulation_engine/decay_logic.py:29), and [`decay_variable`](../../simulation_engine/decay_logic.py:45).
- [`linear_decay`](../../simulation_engine/decay_logic.py:17) serves as a core utility, performing the basic decay calculation. It fetches a default decay rate from config if one isn't provided.
- [`apply_overlay_decay`](../../simulation_engine/decay_logic.py:29) iterates through a hardcoded list of symbolic overlay names. For each, it retrieves the current value from the `WorldState`, applies [`linear_decay`](../../simulation_engine/decay_logic.py:17), updates the `WorldState`, and logs the event. It also fetches a default decay rate.
- [`decay_variable`](../../simulation_engine/decay_logic.py:45) targets a specific named variable in `WorldState.variables`. It retrieves the current value, applies decay (subtracting the rate and respecting a floor), updates the variable in `WorldState`, and logs the event. It also fetches a default decay rate.
- Control flow is straightforward within each function, involving value retrieval, calculation, state update, and logging.

## 9. Naming Conventions

- **Functions:** Use `snake_case` (e.g., [`linear_decay`](../../simulation_engine/decay_logic.py:17), [`apply_overlay_decay`](../../simulation_engine/decay_logic.py:29)), adhering to PEP 8.
- **Variables:** Use `snake_case` (e.g., `decay_rate`, `current_value`), adhering to PEP 8.
- **Class Names:** `WorldState` (imported) uses `PascalCase`, which is standard for Python classes.
- **Constants/Configuration Keys:** String literals like `"default_decay_rate"` are used for configuration keys.
- The naming is generally clear and descriptive. No significant deviations from common Python conventions or potential AI assumption errors in naming were observed.