# Module Analysis: `simulation_engine/simulator_core.py`

## 1. Module Intent/Purpose

The `simulation_engine/simulator_core.py` module serves as the central simulation engine for the Pulse project. Its primary role is to execute turn-by-turn forward simulations based on a `WorldState` object. Key responsibilities include:

*   Managing the simulation loop and advancing the `WorldState` through discrete turns.
*   Applying decay to overlays within the `WorldState`.
*   Executing rules defined in the `rule_engine` to modify the state.
*   Optionally integrating symbolic logic for state tagging and trace scoring.
*   Tracking changes (deltas) in overlays per turn.
*   Providing different levels of detail in simulation output ("summary" or "full").
*   Supporting counterfactual simulations by running a base and a forked simulation with modified initial variables and comparing their traces.
*   Offering functionality to validate historical variable traces.
*   Initial integration points for a "Symbolic Gravity" system to apply corrections to variables, a `ShadowModelMonitor` for observing critical variable changes, a `LearningEngine` for in-loop processing, and a `TrustSystem` for enriching outputs.
*   A placeholder for backward simulation capabilities.

## 2. Operational Status/Completeness

The module appears largely functional for its core responsibility of forward simulation. However, it contains several explicit `TODO` items and placeholders indicating planned extensions and areas for completion:

*   **TODOs (as per docstring lines 31-39):**
    *   Checkpointing (save/load state mid-run).
    *   Schema validation for overlays/variables.
    *   Simulation hooks (pre/post turn, pre/post simulation).
    *   Batch/parallel simulation support.
    *   Enhancements to the CLI entry point.
    *   Comprehensive unit tests and validation utilities.
    *   Simulation seeding/reproducibility.
    *   Overlay/variable schema documentation and enforcement.
*   **Placeholders/NotImplemented:**
    *   The [`simulate_backward()`](simulation_engine/simulator_core.py:839) function is explicitly a placeholder for more complex reverse simulation logic.
    *   Parallel execution in [`simulate_forward()`](simulation_engine/simulator_core.py:581) raises a `NotImplementedError` (line 625).
*   **Partial Integrations:**
    *   The Symbolic Gravity system is integrated but might require further development for robustness or advanced features.
    *   The `ShadowModelMonitor` integration is present, but its full impact depends on the completeness of the monitor itself.

## 3. Implementation Gaps / Unfinished Next Steps

*   **More Extensive Intent:** The listed TODOs clearly indicate that the module was envisioned to be more robust, with features like batch processing, advanced checkpointing, and rigorous schema validation being significant planned extensions.
*   **Logical Next Steps & Missing Features:**
    *   **Full `simulate_backward` Implementation:** The current placeholder needs to be replaced with a functional reverse simulation capability for true causal analysis or state reconstruction.
    *   **Learning Engine Maturation:** The integration with the `LearningEngine` is basic; developing more sophisticated learning hooks and processing within the simulation loop is a likely next step.
    *   **Trust System Enhancement:** Further development of the `TrustSystem` integration to provide more meaningful trust assessments.
    *   **Shadow Model Monitor:** Ensuring the `ShadowModelMonitor` is fully implemented and its triggers are well-calibrated.
    *   **Symbolic Gravity Refinement:** Continued development and refinement of the symbolic gravity mechanism.
    *   **Parallel Simulation:** Implementing the planned parallel execution for `simulate_forward`.
*   **Deviations/Stops:**
    *   The `simulate_backward` function is the most prominent example of a planned feature that was not fully developed.
    *   The `parallel` flag in `simulate_forward` indicates an unimplemented feature path.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`simulation_engine.worldstate.WorldState`](simulation_engine/worldstate.py) (or [`.worldstate.WorldState`](simulation_engine/worldstate.py))
*   [`diagnostics.shadow_model_monitor.ShadowModelMonitor`](diagnostics/shadow_model_monitor.py) (with a fallback)
*   [`simulation_engine.state_mutation.decay_overlay`](simulation_engine/state_mutation.py)
*   [`simulation_engine.rule_engine.run_rules`](simulation_engine/rule_engine.py)
*   [`trust_system.forecast_episode_logger.log_episode_event`](trust_system/forecast_episode_logger.py)
*   [`symbolic_system.symbolic_state_tagger.tag_symbolic_state`](symbolic_system/symbolic_state_tagger.py) (with fallback)
*   [`symbolic_system.symbolic_trace_scorer.score_symbolic_trace`](symbolic_system/symbolic_trace_scorer.py)
*   [`simulation_engine.utils.simulation_trace_logger.log_simulation_trace`](simulation_engine/utils/simulation_trace_logger.py)
*   [`simulation_engine.rules.reverse_rule_mapper.match_rule_by_delta`](simulation_engine/rules/reverse_rule_mapper.py), [`get_all_rule_fingerprints()`](simulation_engine/rules/reverse_rule_mapper.py)
*   [`learning.learning.LearningEngine`](learning/learning.py)
*   [`core.pulse_learning_log.log_learning_event`](core/pulse_learning_log.py)
*   [`symbolic_system.gravity.symbolic_gravity_fabric.create_default_fabric`](symbolic_system/gravity/symbolic_gravity_fabric.py) (imported within [`simulate_turn()`](simulation_engine/simulator_core.py:157))
*   [`simulation_engine.state_mutation.update_numeric_variable`](simulation_engine/state_mutation.py), [`adjust_overlay()`](simulation_engine/state_mutation.py), [`adjust_capital()`](simulation_engine/state_mutation.py) (imported within [`simulate_forward()`](simulation_engine/simulator_core.py:581))
*   [`core.variable_accessor.set_variable`](core/variable_accessor.py) (imported within [`simulate_forward()`](simulation_engine/simulator_core.py:581))
*   [`core.bayesian_trust_tracker.bayesian_trust_tracker`](core/bayesian_trust_tracker.py) (imported within [`simulate_forward()`](simulation_engine/simulator_core.py:581))
*   [`trust_system.trust_engine.TrustEngine`](trust_system/trust_engine.py) (imported within [`simulate_turn()`](simulation_engine/simulator_core.py:157) and [`simulate_forward()`](simulation_engine/simulator_core.py:581))
*   [`simulation_engine.rules.reverse_rule_engine.trace_causal_paths`](simulation_engine/rules/reverse_rule_engine.py), [`get_fingerprints()`](simulation_engine/rules/reverse_rule_engine.py), [`suggest_new_rule_if_no_match()`](simulation_engine/rules/reverse_rule_engine.py) (imported within [`reverse_rule_engine()`](simulation_engine/simulator_core.py:1101))
*   [`simulation_engine.worldstate_monitor.display_gravity_correction_details`](simulation_engine/worldstate_monitor.py) (imported in `__main__`)
*   [`symbolic_system.gravity.gravity_config.ResidualGravityConfig`](symbolic_system/gravity/gravity_config.py) (imported in `__main__`)

### External Library Dependencies:
*   `logging`
*   `typing`
*   `copy`
*   `datetime`
*   `json`
*   `argparse` (in `__main__` block)

### Interaction via Shared Data:
*   Primarily through the `WorldState` object, which is passed and mutated.
*   Checkpoint files (JSON format) if checkpointing is enabled via [`simulate_forward()`](simulation_engine/simulator_core.py:581) (lines 719-727).
*   Log files potentially generated by [`log_simulation_trace()`](simulation_engine/utils/simulation_trace_logger.py) or the custom [`log_to_file()`](simulation_engine/simulator_core.py:1094) utility.

### Input/Output Files:
*   **Input:**
    *   Potentially a `WorldState` loaded from a checkpoint file (a TODO feature).
*   **Output:**
    *   Simulation results (returned as a list of dictionaries).
    *   Checkpoint files: `[checkpoint_path]_turn_[turn_number].json`.
    *   Trace logs via [`log_simulation_trace()`](simulation_engine/utils/simulation_trace_logger.py).
    *   Backward trace logs via [`log_to_file()`](simulation_engine/simulator_core.py:1094) if the `--save-backtrace` CLI option is used.
    *   Gravity explanation files if the `--explain-gravity` CLI option is used.

## 5. Function and Class Example Usages

*   **[`simulate_forward(state, turns, ...)`simulation_engine/simulator_core.py:581]:**
    The primary function for running multi-turn simulations.
    ```python
    from simulation_engine.worldstate import WorldState
    from simulation_engine.simulator_core import simulate_forward

    ws = WorldState()
    ws.sim_id = "example_simulation"
    # Initialize ws.overlays, ws.variables as needed
    # e.g., ws.overlays = {"hope": 0.5, "fear": 0.2}
    #       ws.variables = {"resource_level": 100.0}

    simulation_output = simulate_forward(ws, turns=10, use_symbolism=True, return_mode="summary")
    for turn_result in simulation_output:
        print(f"Turn {turn_result['turn']}: Deltas = {turn_result['deltas']}, Tag = {turn_result.get('symbolic_tag', 'N/A')}")
    ```

*   **[`simulate_turn(state, ...)`simulation_engine/simulator_core.py:157]:**
    Executes a single simulation turn. Typically called internally by [`simulate_forward()`](simulation_engine/simulator_core.py:581).
    ```python
    # Conceptual usage, not usually called directly by end-users
    # current_world_state = WorldState(...)
    # turn_result = simulate_turn(current_world_state, use_symbolism=True)
    ```

*   **[`simulate_counterfactual(initial_state, fork_vars, turns, ...)`simulation_engine/simulator_core.py:916]:**
    Runs a base simulation and a forked simulation with modified initial variables, then compares their traces.
    ```python
    from simulation_engine.worldstate import WorldState
    from simulation_engine.simulator_core import simulate_counterfactual

    initial_ws = WorldState()
    initial_ws.overlays = {"optimism": 0.6, "pessimism": 0.3}
    initial_ws.variables = {"project_progress": 0.2}

    fork_conditions = {"optimism": 0.8} # Fork: increase initial optimism

    counterfactual_results = simulate_counterfactual(initial_ws, fork_conditions, turns=5)
    for divergence_info in counterfactual_results["divergence"]:
        print(f"Turn {divergence_info['turn']}: Overlay Delta = {divergence_info['overlay_delta']}")
    ```

*   **[`validate_variable_trace(var_name, known_trace, state, ...)`simulation_engine/simulator_core.py:747]:**
    Validates a known historical trace for a single variable by reconstructing a trace backward.
    ```python
    from simulation_engine.worldstate import WorldState
    from simulation_engine.simulator_core import validate_variable_trace

    current_ws = WorldState()
    current_ws.overlays = {"stability": 0.75} # Current value at T0

    # Known historical values for 'stability' at T-3, T-2, T-1
    historical_stability_trace = [0.72, 0.73, 0.74]

    validation_report = validate_variable_trace("stability", historical_stability_trace, current_ws)
    print(f"Validation for 'stability': Match = {validation_report['match_percent']}%")
    print(f"Expected: {validation_report['expected']}, Reconstructed: {validation_report['reconstructed']}")
    ```

*   **[`reset_state(state)`simulation_engine/simulator_core.py:109]:**
    Resets overlays, variables, turn count, and event log of a `WorldState` object.
    ```python
    from simulation_engine.worldstate import WorldState
    from simulation_engine.simulator_core import reset_state, simulate_forward

    ws = WorldState()
    ws.overlays = {"excitement": 0.9}
    ws.turn = 5
    simulate_forward(ws, turns=2) # ws is now modified

    reset_state(ws)
    # ws.overlays values are reset (e.g., to 0.0), ws.turn is 0, ws.event_log is empty
    print(f"After reset: Turn = {ws.turn}, Excitement = {ws.overlays.get('excitement', 0.0)}")
    ```

## 6. Hardcoding Issues

*   **Default Values:**
    *   Decay rate in [`inverse_decay()`](simulation_engine/simulator_core.py:740) (`rate: float = 0.01`).
    *   Decay rate in [`simulate_backward()`](simulation_engine/simulator_core.py:839) (`decay_rate: float = 0.01`).
    *   Absolute tolerance `atol: float = 1e-2` in [`validate_variable_trace()`](simulation_engine/simulator_core.py:747).
    *   Default `sim_id` components in test/demo functions (e.g., `"selftest"`, `"backward_test"`, `"demo_sim"`).
*   **String Literals:**
    *   Symbolic tags: `"error"` (line 527), `"disabled"` (line 534), placeholder tags in [`simulate_backward()`](simulation_engine/simulator_core.py:839).
    *   CLI default values and choices (lines 1196-1207).
*   **File Path Construction:**
    *   Checkpoint file naming: `f"{checkpoint_path}_turn_{i+1}.json"` (line 722).
*   **Magic Numbers:**
    *   Threshold for significant gravity delta: `1e-6` (lines 341, 644).
    *   Parameters for `trace_causal_paths` in [`reverse_rule_engine()`](simulation_engine/simulator_core.py:1101): `max_depth=3`, `min_match=0.5` (line 1129).

## 7. Coupling Points

*   **`WorldState` Object:** This is the central data structure. Most functions in the module operate on or expect a `WorldState` instance, making the module tightly coupled to its definition and structure.
*   **Rule Engine ([`simulation_engine.rule_engine.run_rules`](simulation_engine/rule_engine.py)):** A critical dependency for applying the core simulation logic that modifies the `WorldState`.
*   **State Mutation ([`simulation_engine.state_mutation`](simulation_engine/state_mutation.py)):** Functions like [`decay_overlay()`](simulation_engine/state_mutation.py) are directly responsible for specific state changes.
*   **Symbolic System (`symbolic_system` directory):**
    *   [`symbolic_state_tagger.tag_symbolic_state`](symbolic_system/symbolic_state_tagger.py)
    *   [`symbolic_trace_scorer.score_symbolic_trace`](symbolic_system/symbolic_trace_scorer.py)
    *   Symbolic Gravity components (e.g., [`symbolic_gravity_fabric`](symbolic_system/gravity/symbolic_gravity_fabric.py)).
    These indicate a strong coupling for advanced symbolic processing and state correction features.
*   **Trust System (`trust_system` directory):**
    *   [`TrustEngine`](trust_system/trust_engine.py) and [`forecast_episode_logger.log_episode_event`](trust_system/forecast_episode_logger.py) are used for enriching simulation output with trust-related metadata.
*   **Learning Engine ([`learning.learning.LearningEngine`](learning/learning.py)):** Integrated into the simulation loop via [`process_turn()`](learning/learning.py) hooks.
*   **Diagnostics ([`diagnostics.shadow_model_monitor.ShadowModelMonitor`](diagnostics/shadow_model_monitor.py)):** Integrated to monitor critical variables, particularly in relation to the gravity system.
*   **Logging Mechanism:** The module uses both a module-level `logging.getLogger(__name__)` and allows for an optional callable `logger` to be passed into main simulation functions, creating a dependency on logging infrastructure.

## 8. Existing Tests

*   **Internal Self-Tests:**
    *   [`_self_test()`](simulation_engine/simulator_core.py:1172): Runs a basic forward simulation.
    *   [`_backward_self_test()`](simulation_engine/simulator_core.py:1182): Runs the placeholder backward simulation.
    These are invoked via CLI arguments (`--selftest`).
*   **CLI-Based Testing:** The `if __name__ == "__main__":` block (lines 1193-1293) provides various command-line options that can be used for testing different functionalities, such as:
    *   Running forward simulations with different parameters.
    *   Invoking the placeholder backward simulation.
    *   Validating variable traces using [`validate_variable_trace()`](simulation_engine/simulator_core.py:747).
*   **Formal Test Suite:**
    *   The module's docstring includes a TODO for "Add unit tests and validation utilities" (line 37), indicating a recognized need for more formal and comprehensive testing.
    *   A dedicated test file like `tests/test_simulator_core.py` is not directly referenced or apparent from within this module's code. External test files like `tests/test_integration_simulation_forecast.py` or `tests/test_property_based_simulation_engine.py` might provide some coverage, but specific unit tests for `simulator_core.py` functions are likely needed.

## 9. Module Architecture and Flow

### Core Simulation Flow (`simulate_forward` -> `simulate_turn`):
1.  **`simulate_forward(state, turns, ...)`:**
    *   Manages the overall simulation for a given number of `turns`.
    *   Handles optional retrodiction logic (injecting ground truth or comparing against it).
    *   Calls [`simulate_turn()`](simulation_engine/simulator_core.py:157) for each turn.
    *   Manages optional checkpointing of the `WorldState`.
    *   Aggregates results from each turn.
    *   Can invoke progress callbacks.
2.  **`simulate_turn(state, ...)`:**
    *   **Initialization:** Validates the input `WorldState`, copies the initial overlay state (`pre_overlay`) for delta calculation, and captures initial critical variables if a `shadow_monitor_instance` is provided.
    *   **Decay Phase:** Applies [`decay_overlay()`](simulation_engine/state_mutation.py) to all overlays in the `WorldState`.
    *   **Rule Execution:** Calls [`run_rules()`](simulation_engine/rule_engine.py) to apply causal rules, modifying `state.overlays` and `state.variables`.
    *   **Symbolic Gravity (Optional):**
        *   If `gravity_enabled` is true, it attempts to apply corrections using the `symbolic_gravity_fabric`.
        *   Calculates causal deltas (changes before gravity).
        *   The gravity fabric's `bulk_apply_correction` method adjusts `state.variables`.
        *   Gravity deltas are calculated.
        *   The `shadow_monitor_instance` records these changes and checks for triggers if gravity influence is too high.
        *   The gravity fabric itself is stepped (`state._gravity_fabric.step(state)`).
    *   **Learning Engine (Optional):** If a `learning_engine` is provided, its [`process_turn()`](learning/learning.py) method is called.
    *   **Delta Calculation:** Computes the changes (deltas) between `pre_overlay` and the current `overlays_now`.
    *   **Symbolic Tagging (Optional):** If `use_symbolism` is true and the tagging module is available, [`tag_symbolic_state()`](symbolic_system/symbolic_state_tagger.py) is called to generate a symbolic tag and score for the current state.
    *   **Trust Enrichment:** The output is processed by [`TrustEngine.enrich_trust_metadata()`](trust_system/trust_engine.py).
    *   **Return:** Returns a dictionary containing turn number, timestamp, current overlays, deltas, symbolic information, and potentially the full state or fired rules depending on `return_mode`.

### Key Components:
*   **`WorldState`:** The central data object holding all simulation state (overlays, variables, turn count, events, etc.).
*   **Simulation Functions:**
    *   [`simulate_forward()`](simulation_engine/simulator_core.py:581): Main loop for multiple turns.
    *   [`simulate_turn()`](simulation_engine/simulator_core.py:157): Logic for a single turn.
    *   [`simulate_counterfactual()`](simulation_engine/simulator_core.py:916): Compares base vs. forked simulations.
    *   [`simulate_backward()`](simulation_engine/simulator_core.py:839): Placeholder for reverse simulation.
    *   [`validate_variable_trace()`](simulation_engine/simulator_core.py:747): Validates historical data.
*   **Helper/Utility Functions:**
    *   [`_validate_overlay()`](simulation_engine/simulator_core.py:94), [`_copy_overlay()`](simulation_engine/simulator_core.py:105), [`reset_state()`](simulation_engine/simulator_core.py:109), [`_get_dict_from_vars()`](simulation_engine/simulator_core.py:130), [`inverse_decay()`](simulation_engine/simulator_core.py:740), [`get_overlays_dict()`](simulation_engine/simulator_core.py:1076), [`log_to_file()`](simulation_engine/simulator_core.py:1094).
*   **External System Integrations:**
    *   Symbolic System (tagging, scoring, gravity).
    *   Trust System.
    *   Learning Engine.
    *   Shadow Model Monitor.

### Data Flow:
*   The `WorldState` object is the primary data carrier, passed into simulation functions and mutated by internal operations (decay, rules, gravity).
*   Simulation functions return lists of dictionaries, where each dictionary represents the outcome of a turn.
*   Data can be persisted via checkpointing or logging utilities.

## 10. Naming Conventions

*   **PEP 8 Adherence:** The module generally follows PEP 8 guidelines:
    *   `snake_case` for functions and variables (e.g., [`simulate_forward()`](simulation_engine/simulator_core.py:581), `pre_overlay`).
    *   `PascalCase` for classes (e.g., `WorldState`, `ShadowModelMonitor`, `LearningEngine` - imported).
*   **Clarity of Names:**
    *   Most variable and function names are descriptive and clearly indicate their purpose (e.g., `gravity_correction_details`, `causal_deltas_monitor`, [`validate_variable_trace()`](simulation_engine/simulator_core.py:747)).
    *   Type hints like `_SMM_TypeForHint` (line 49) and fallback classes like `_ShadowModelMonitorFallback` (line 64) are clearly named for their specific roles.
    *   The prefix `_` is used for internal helper functions (e.g., [`_validate_overlay()`](simulation_engine/simulator_core.py:94), [`_copy_overlay()`](simulation_engine/simulator_core.py:105)) and some dynamically attached attributes on `WorldState` (e.g., `_gravity_fabric`, `_gravity_disable`, `_pre_simulation_vars`) to denote internal state or configuration for features like gravity.
*   **Consistency:** Naming conventions appear consistent throughout the module.
*   **Potential AI Assumption Errors:** No obvious errors in naming that would suggest misinterpretation by an AI or significant deviations from common Python practices. The naming is conventional and human-readable.