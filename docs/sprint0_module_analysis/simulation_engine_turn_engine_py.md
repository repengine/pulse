# Module Analysis: `simulation_engine/turn_engine.py`

## 1. Module Intent/Purpose

The primary role of [`simulation_engine/turn_engine.py`](simulation_engine/turn_engine.py:1) is to control the simulation loop at the individual turn level. Its responsibilities include:
- Applying symbolic decay to various overlays within the simulation state (e.g., hope, trust).
- Executing narrative and capital effects through [`causal_rules.py`](simulation_engine/causal_rules.py:1).
- Running a structured and auditable causal rule engine via [`rule_engine.py`](simulation_engine/rule_engine.py:1).
- Allowing for the injection of custom rule functions for flexible simulation logic.
- Incrementing the simulation turn counter.
- Returning a detailed audit trail of rule executions for memory, scoring, or analysis purposes.

## 2. Operational Status/Completeness

The module appears largely functional for its defined responsibilities.
- The core logic within the [`run_turn`](simulation_engine/turn_engine.py:50) function seems complete and follows the documented steps.
- There is a commented-out section related to "Post-turn license enforcement" ([`simulation_engine/turn_engine.py:114-119`](simulation_engine/turn_engine.py:114-119)) with a note stating `WorldState has no 'forecasts' attribute`. This suggests a feature that was either deprecated, planned but not fully integrated, or requires `WorldState` to be augmented.
- The [`run_turn`](simulation_engine/turn_engine.py:50) function signature includes `...` on line 58, which is unusual and might be a remnant of initial scaffolding or an unfinished thought, although the function body itself is implemented.

## 3. Implementation Gaps / Unfinished Next Steps

- **License Enforcement:** The most significant gap is the commented-out license enforcement logic ([`simulation_engine/turn_engine.py:114-119`](simulation_engine/turn_engine.py:114-119)). If this feature is still desired, it would require either modifications to `WorldState` or a different approach to accessing forecast data.
- **`run_turn` Signature Ellipsis:** The `...` on line 58 of the [`run_turn`](simulation_engine/turn_engine.py:50) function definition should be reviewed and removed or clarified.
- **Learning Engine Integration:** The `learning_engine` parameter is accepted and used ([`simulation_engine/turn_engine.py:122-123`](simulation_engine/turn_engine.py:122-123)), but its full integration path and the capabilities it's expected to provide are not detailed within this module, implying reliance on external setup and definition.
- **Retrodiction Snapshot Injection:** The module includes logic for injecting a `injection_snapshot` ([`simulation_engine/turn_engine.py:59-61`](simulation_engine/turn_engine.py:59-61)) using [`set_variable`](core/variable_accessor.py:0) and imports [`RetrodictionLoader`](simulation_engine/simulator_core.py:0) ([`simulation_engine/turn_engine.py:31`](simulation_engine/turn_engine.py:31)), but the broader context or workflow for how these snapshots are generated and used for retrodiction isn't fully elaborated within this specific module.

## 4. Connections & Dependencies

### Direct Project Module Imports:
- [`simulation_engine.worldstate`](simulation_engine/worldstate.py): For [`WorldState`](simulation_engine/worldstate.py:0) class.
- [`simulation_engine.state_mutation`](simulation_engine/state_mutation.py): For [`decay_overlay()`](simulation_engine/state_mutation.py:0) function.
- [`simulation_engine.causal_rules`](simulation_engine/causal_rules.py): For [`apply_causal_rules()`](simulation_engine/causal_rules.py:0) function.
- [`simulation_engine.rule_engine`](simulation_engine/rule_engine.py): For [`run_rules()`](simulation_engine/rule_engine.py:0) function.
- [`core.path_registry`](core/path_registry.py): For the [`PATHS`](core/path_registry.py:0) dictionary.
- [`memory.trace_audit_engine`](memory/trace_audit_engine.py): For [`assign_trace_metadata()`](memory/trace_audit_engine.py:0) and [`register_trace_to_memory()`](memory/trace_audit_engine.py:0).
- [`core.pulse_config`](core/pulse_config.py): For the [`ENABLE_TRACE_LOGGING`](core/pulse_config.py:0) constant.
- [`core.variable_accessor`](core/variable_accessor.py): For [`set_variable()`](core/variable_accessor.py:0).
- [`simulation_engine.simulator_core`](simulation_engine/simulator_core.py): For [`simulate_forward()`](simulation_engine/simulator_core.py:0) (aliased as `RetrodictionLoader`).

### External Library Dependencies:
- `typing`: For `Callable`, `Optional`, `Dict`.

### Shared Data Interactions:
- Utilizes the [`PATHS`](core/path_registry.py:0) dictionary from [`core.path_registry`](core/path_registry.py) to determine `TURN_LOG_PATH`.
- Interacts with the `learning_engine` object (if provided) by calling its `on_simulation_turn_end` method.
- Logs events directly to the passed `WorldState` object.
- Registers trace information to a memory system via functions from [`memory.trace_audit_engine`](memory/trace_audit_engine.py).

### Input/Output Files:
- Potentially logs information to `TURN_LOG_PATH`, which defaults to `PATHS["WORLDSTATE_LOG_DIR"]` if `PATHS.get("TURN_LOG_PATH")` is not found ([`simulation_engine/turn_engine.py:34`](simulation_engine/turn_engine.py:34)). The exact nature and content of these logs are not detailed in this module but are managed by the `WorldState` object's `log_event` method.

## 5. Function and Class Example Usages

- **[`initialize_worldstate(start_year: Optional[int] = None, **kwargs) -> WorldState`](simulation_engine/turn_engine.py:40):**
  A factory function to create and initialize a `WorldState` object. This allows other parts of the system (like `IntelligenceCore`) to bootstrap a simulation without directly importing the `WorldState` class.
  ```python
  from simulation_engine.turn_engine import initialize_worldstate
  # Basic initialization
  world = initialize_worldstate()
  # Initialization with a specific start year
  world_2023 = initialize_worldstate(start_year=2023)
  # Initialization with other WorldState parameters
  world_custom = initialize_worldstate(initial_variables={"population": 1000})
  ```

- **[`run_turn(state: WorldState, rule_fn: Optional[Callable[[WorldState], None]] = None, decay_rate: float = 0.01, verbose: bool = True, learning_engine=None, injection_snapshot: Optional[Dict[str, float]] = None) -> list[dict]`](simulation_engine/turn_engine.py:50):**
  The core function that executes a single turn of the simulation.
  ```python
  from simulation_engine.turn_engine import run_turn, initialize_worldstate
  current_worldstate = initialize_worldstate()
  # Run a basic turn
  audit_log = run_turn(current_worldstate)
  # Run a turn with a custom rule function and different decay rate
  def custom_logic(state):
      if state.variables.get("population", 0) > 1500:
          print("Population high!")
  audit_log_custom = run_turn(current_worldstate, rule_fn=custom_logic, decay_rate=0.05)
  # Run a turn with an injection snapshot
  snapshot_data = {"economy_index": 1.2, "public_unrest": 0.1}
  audit_log_injected = run_turn(current_worldstate, injection_snapshot=snapshot_data)
  ```

## 6. Hardcoding Issues

- **`AUTO_ENFORCE = False` ([`simulation_engine/turn_engine.py:36`](simulation_engine/turn_engine.py:36)):** A boolean constant that globally enables or disables post-turn license enforcement. If this needs to be configurable per simulation run, it should be a parameter or loaded from a configuration file.
- **Default `decay_rate: float = 0.01`** in [`run_turn()`](simulation_engine/turn_engine.py:53): While a parameter, its default value is hardcoded.
- **Default `verbose: bool = True`** in [`run_turn()`](simulation_engine/turn_engine.py:54): Similar to `decay_rate`, the default is hardcoded.
- **Event Log Strings:** Strings used for logging events (e.g., `"Symbolic decay applied to overlays."` on [`simulation_engine/turn_engine.py:81`](simulation_engine/turn_engine.py:81), error messages) are hardcoded. For internationalization or more structured logging, these could be managed differently.

## 7. Coupling Points

- **High Coupling with `WorldState`:** The module is tightly coupled with the [`WorldState`](simulation_engine/worldstate.py:0) object, as it directly manipulates its attributes and calls its methods (e.g., `log_event`, `advance_turn`, accessing `overlays`, `variables`).
- **Core Simulation Logic:** Tightly coupled with [`simulation_engine.state_mutation`](simulation_engine/state_mutation.py), [`simulation_engine.causal_rules`](simulation_engine/causal_rules.py), and [`simulation_engine.rule_engine`](simulation_engine/rule_engine.py) for the fundamental steps of a simulation turn.
- **Configuration/Path Management:** Depends on [`core.path_registry`](core/path_registry.py) for `TURN_LOG_PATH` and [`core.pulse_config`](core/pulse_config.py) for `ENABLE_TRACE_LOGGING`. Changes in these central configurations directly affect the module's behavior.
- **Optional Systems:**
    - `learning_engine`: If provided, the module calls its `on_simulation_turn_end` method.
    - `trace_audit_engine`: If `ENABLE_TRACE_LOGGING` is true, the module interacts with this system.
    - `RetrodictionLoader` ([`simulation_engine.simulator_core.simulate_forward`](simulation_engine/simulator_core.py:0)): Used if `injection_snapshot` is provided.

## 8. Existing Tests

- A search in the `tests/simulation_engine/` directory revealed no specific test files for `turn_engine.py` (e.g., `test_turn_engine.py`).
- This indicates a **significant gap in test coverage** for this core simulation module. Without dedicated tests, verifying its correctness, robustness (especially error handling within try-except blocks), and the impact of future changes becomes difficult and risky.

## 9. Module Architecture and Flow

The module defines two primary functions:

1.  **[`initialize_worldstate()`](simulation_engine/turn_engine.py:40):**
    *   Acts as a lightweight factory to create an instance of `WorldState`.
    *   Optionally sets a `start_year` in the `WorldState` metadata.

2.  **[`run_turn()`](simulation_engine/turn_engine.py:50):** This is the main operational function and follows these steps:
    *   **Snapshot Injection (Optional):** If `injection_snapshot` is provided, iterate through its items and update the `WorldState` using [`set_variable()`](core/variable_accessor.py:0).
    *   **Symbolic Decay:** Iterates through overlays in `WorldState` and applies decay using [`decay_overlay()`](simulation_engine/state_mutation.py:0). Logs success or failure.
    *   **Causal Rules (Non-audited):** Applies symbolic and capital shifts using [`apply_causal_rules()`](simulation_engine/causal_rules.py:0). Logs success or failure.
    *   **Structured Rule Engine:** Executes the structured rule engine via [`run_rules()`](simulation_engine/rule_engine.py:0) and captures the `rule_execution_log`. Logs success or failure.
    *   **Custom Logic (Optional):** If a `rule_fn` (custom rule function) is provided, it is executed. Logs success or failure.
    *   **Advance Turn:** Calls `state.advance_turn()` to increment the simulation turn. Logs this event.
    *   **License Enforcement (Commented Out):** Contains commented-out logic for license enforcement.
    *   **Learning Hook (Optional):** If a `learning_engine` is provided, its `on_simulation_turn_end` method is called with a snapshot of the current state.
    *   **Trace Logging (Optional):** If `ENABLE_TRACE_LOGGING` is true, it prepares simulation input/output data, assigns trace metadata using [`assign_trace_metadata()`](memory/trace_audit_engine.py:0), and registers the trace using [`register_trace_to_memory()`](memory/trace_audit_engine.py:0).
    *   **Return Value:** Returns the `rule_execution_log` (a list of dictionaries).

## 10. Naming Conventions

- **General Adherence to PEP 8:** Functions (`run_turn`, `initialize_worldstate`, `decay_overlay`) and local variables (`decay_rate`, `rule_execution_log`) generally use `snake_case`.
- **Class Names:** [`WorldState`](simulation_engine/worldstate.py:0) is `PascalCase`, which is standard for Python classes.
- **Constants:** [`PATHS`](core/path_registry.py:0), `ENABLE_TRACE_LOGGING`, `TURN_LOG_PATH`, and `AUTO_ENFORCE` are `UPPER_CASE_SNAKE_CASE` or `UPPER_CASE`, appropriate for constants.
- **Alias:** [`simulate_forward`](simulation_engine/simulator_core.py:0) is aliased as `RetrodictionLoader` ([`simulation_engine/turn_engine.py:31`](simulation_engine/turn_engine.py:31)). Using `PascalCase` for a function alias is unconventional but might be intended to signify its role as a major component or loader.
- **Unconventional Ellipsis:** The `...` in the [`run_turn`](simulation_engine/turn_engine.py:50) function signature ([`simulation_engine/turn_engine.py:58`](simulation_engine/turn_engine.py:58)) is not standard Python syntax for a completed function and should be addressed. It's typically used as a placeholder in stubs or for `NotImplemented`.