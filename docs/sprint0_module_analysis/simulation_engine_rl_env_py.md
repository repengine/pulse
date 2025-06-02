# Module Analysis: `simulation_engine/rl_env.py`

## 1. Module Intent/Purpose

The module [`simulation_engine/rl_env.py`](../../simulation_engine/rl_env.py) defines the `SimulationEnv` class, an OpenAI Gym-style environment. Its primary role is to facilitate Reinforcement Learning (RL) based rule adaptation within the Pulse simulation engine. This allows an RL agent to learn optimal rule parameters by interacting with the simulation environment, receiving observations, taking actions (adjusting parameters), and getting rewards based on simulation outcomes.

## 2. Operational Status/Completeness

The module appears to be a core, functional component for RL integration. It correctly implements the standard `gym.Env` interface, including methods like `__init__` ([simulation_engine/rl_env.py:10](simulation_engine/rl_env.py:10)), `reset` ([simulation_engine/rl_env.py:27](simulation_engine/rl_env.py:27)), and `step` ([simulation_engine/rl_env.py:50](simulation_engine/rl_env.py:50)). The `compute_robustness_reward` ([simulation_engine/rl_env.py:36](simulation_engine/rl_env.py:36)) method defines a specific reward logic based on simulation outcomes (fragility, confidence, drift). No obvious placeholders (e.g., `pass`, `NotImplementedError`) or "TODO" comments are visible in the provided code, suggesting it's in a relatively complete state for its defined scope.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Reward Function Sophistication:** The current reward function (`confidence - fragility - drift`) is functional but could be enhanced with more sophisticated reward shaping techniques for better agent learning.
*   **Observation Space:** The observation space currently consists of the rule parameters. It could potentially be augmented with other simulation state information to provide more context for the RL agent.
*   **Episode Dynamics:** The `turns_per_episode` ([simulation_engine/rl_env.py:10](simulation_engine/rl_env.py:10)) is fixed at initialization. Exploring dynamic episode lengths or more complex termination/truncation conditions could be beneficial.
*   **`options` Parameter:** The `options` parameter in the `reset` ([simulation_engine/rl_env.py:27](simulation_engine/rl_env.py:27)) method is part of the `gym.Env` interface but is not currently used.
*   **Advanced RL Features:** While foundational, further development could involve more complex agent training scripts, hyperparameter tuning specific to this RL environment, and integration with a wider variety of simulation scenarios.

## 4. Connections & Dependencies

*   **Direct Imports from Project Modules:**
    *   [`engine.rules.static_rules.build_static_rules()`](../../simulation_engine/rules/static_rules.py:6) (also at [simulation_engine/rl_env.py:39](simulation_engine/rl_env.py:39))
    *   [`engine.rules.rule_param_registry.RULE_PARAM_REGISTRY`](../../simulation_engine/rules/rule_param_registry.py:7)
    *   [`engine.simulator_core.simulate_forward()`](../../simulation_engine/simulator_core.py:37) (local import within `compute_robustness_reward`)
    *   [`engine.worldstate.WorldState`](../../simulation_engine/worldstate.py:38) (local import within `compute_robustness_reward`)
*   **External Library Dependencies:**
    *   `gym`
    *   `numpy`
*   **Interaction via Shared Data:**
    *   Relies heavily on [`RULE_PARAM_REGISTRY`](../../simulation_engine/rules/rule_param_registry.py:7) for defining the action space, observation space, and default state based on rule parameters.
*   **Input/Output Files:**
    *   The module itself does not directly manage file I/O. However, the simulations it triggers via [`simulate_forward()`](../../simulation_engine/simulator_core.py:37) might produce logs or data files.

## 5. Function and Class Example Usages

*   **`SimulationEnv` Class:**
    ```python
    # from engine.rl_env import SimulationEnv
    # # Assumes RULE_PARAM_REGISTRY is populated correctly
    #
    # env = SimulationEnv(turns_per_episode=10)
    # observation, info = env.reset()
    #
    # for _ in range(1000): # Example training loop
    #     action = env.action_space.sample()  # Replace with RL agent's action
    #     observation, reward, terminated, truncated, info = env.step(action)
    #
    #     if terminated or truncated:
    #         print("Episode finished.")
    #         observation, info = env.reset()
    #
    # env.close() # If any resources need cleanup (though not explicitly shown here)
    ```
*   **`reset()` method:**
    *   Initializes or resets the environment to a starting state.
    *   *Usage:* `observation, info = env.reset()`
*   **`step(action)` method:**
    *   The RL agent provides an `action` (a NumPy array of rule parameter values).
    *   The environment updates its state, runs a simulation with these parameters, computes a reward.
    *   *Usage:* `next_observation, reward, terminated, truncated, info = env.step(action_values)`
*   **`compute_robustness_reward(param_overrides)` method:**
    *   Called internally by `step` ([simulation_engine/rl_env.py:50](simulation_engine/rl_env.py:50)) to calculate the reward for an action.
    *   It runs a simulation using [`simulate_forward()`](../../simulation_engine/simulator_core.py:37) with the given `param_overrides` and derives a reward from simulation metrics like `fragility`, `confidence`, and `drift`.

## 6. Hardcoding Issues

*   **Default `turns_per_episode`:** The default value of `5` for `turns_per_episode` is hardcoded in the `__init__` ([simulation_engine/rl_env.py:10](simulation_engine/rl_env.py:10)) method's signature. This can be overridden during instantiation.
*   **Reward Calculation Metrics & Formula:**
    *   The specific metrics (`fragility`, `confidence`, `drift`) used for reward calculation are hardcoded within `compute_robustness_reward` ([simulation_engine/rl_env.py:44-46](simulation_engine/rl_env.py:44-46)).
    *   The formula `reward = confidence - fragility - drift` ([simulation_engine/rl_env.py:47](simulation_engine/rl_env.py:47)) is hardcoded.
    *   Default values for these metrics if not found in simulation results (e.g., `fragility` defaults to `1.0`) are also hardcoded ([simulation_engine/rl_env.py:44-46](simulation_engine/rl_env.py:44-46)).
*   **`simulate_forward` `return_mode`:** In `compute_robustness_reward` ([simulation_engine/rl_env.py:42](simulation_engine/rl_env.py:42)), the [`simulate_forward()`](../../simulation_engine/simulator_core.py:37) function is called with `return_mode="summary"`.

## 7. Coupling Points

*   **`RULE_PARAM_REGISTRY`:** The environment is strongly coupled to [`RULE_PARAM_REGISTRY`](../../simulation_engine/rules/rule_param_registry.py:7). Changes to the structure, content, or availability of this registry would directly impact the environment's action space, observation space, and initialization.
*   **Simulation Core:** Tightly coupled with [`engine.simulator_core.simulate_forward()`](../../simulation_engine/simulator_core.py:37) and [`engine.worldstate.WorldState`](../../simulation_engine/worldstate.py:38) for its reward computation. The behavior, inputs, and outputs of `simulate_forward` are critical.
*   **Static Rules:** Depends on [`engine.rules.static_rules.build_static_rules()`](../../simulation_engine/rules/static_rules.py:6) to construct rules based on parameter overrides provided by the RL agent's actions.

## 8. Existing Tests

*   No specific test file (e.g., `tests/simulation_engine/test_rl_env.py`) is immediately apparent from the provided file list.
*   It is possible that this module is tested indirectly through higher-level tests, such as those for an RL agent training script (e.g., if [`simulation_engine/train_rl_agent.py`](../../simulation_engine/train_rl_agent.py) has associated tests).
*   Without dedicated unit tests, assessing coverage is difficult. Unit tests for `reset` ([simulation_engine/rl_env.py:27](simulation_engine/rl_env.py:27)), `step` ([simulation_engine/rl_env.py:50](simulation_engine/rl_env.py:50)) (with various valid and edge-case actions), and `compute_robustness_reward` ([simulation_engine/rl_env.py:36](simulation_engine/rl_env.py:36)) (potentially by mocking simulation results) would be highly beneficial.

## 9. Module Architecture and Flow

1.  **Initialization (`__init__`)**:
    *   Sets `turns_per_episode`.
    *   Retrieves rule IDs and parameter names from [`RULE_PARAM_REGISTRY`](../../simulation_engine/rules/rule_param_registry.py:7).
    *   Defines `action_space` as a `gym.spaces.Box`. The bounds (low/high) for each parameter are derived from [`RULE_PARAM_REGISTRY`](../../simulation_engine/rules/rule_param_registry.py:7). An action is a vector of values for all registered rule parameters.
    *   Defines `observation_space` as a `gym.spaces.Box`, representing the current values of all rule parameters.
    *   Calls `reset()` ([simulation_engine/rl_env.py:27](simulation_engine/rl_env.py:27)) to establish the initial state.
2.  **Reset (`reset`)**:
    *   Resets `current_turn` to `0`.
    *   Sets the internal `state` (which forms the observation) to the default parameter values specified in [`RULE_PARAM_REGISTRY`](../../simulation_engine/rules/rule_param_registry.py:7).
    *   Returns a copy of the state array and an empty info dictionary.
3.  **Step (`step`)**:
    *   Receives an `action` (a NumPy array of new parameter values).
    *   Clips the action values to ensure they are within the defined `action_space` bounds.
    *   Updates the internal `state` to reflect the (clipped) action.
    *   Transforms the flat `action` array into a `param_overrides` dictionary, structured by rule ID and parameter name.
    *   Calls `compute_robustness_reward` ([simulation_engine/rl_env.py:36](simulation_engine/rl_env.py:36)) with these `param_overrides` to get the reward.
    *   Increments `current_turn`.
    *   Determines `terminated` status: `True` if `current_turn` reaches `turns_per_episode`, `False` otherwise.
    *   `truncated` status is always `False`.
    *   Returns the new state (a copy), the calculated reward, terminated status, truncated status, and an info dictionary containing the `param_overrides`.
4.  **Reward Computation (`compute_robustness_reward`)**:
    *   Locally imports necessary components: [`simulate_forward()`](../../simulation_engine/simulator_core.py:37), [`WorldState`](../../simulation_engine/worldstate.py:38), and [`build_static_rules()`](../../simulation_engine/rules/static_rules.py:6).
    *   Creates a new [`WorldState`](../../simulation_engine/worldstate.py:38) instance.
    *   Builds the simulation rules using [`build_static_rules()`](../../simulation_engine/rules/static_rules.py:6) with the `param_overrides` from the current action.
    *   Runs a simulation via [`simulate_forward()`](../../simulation_engine/simulator_core.py:37) for `self.turns_per_episode`, requesting a "summary" return mode.
    *   Extracts `fragility`, `confidence`, and `drift` from the last step of the simulation results (with defaults if metrics are missing).
    *   Calculates and returns the reward: `confidence - fragility - drift`.

## 10. Naming Conventions

*   **Class Name:** `SimulationEnv` ([simulation_engine/rl_env.py:9](simulation_engine/rl_env.py:9)) follows PascalCase, which is standard for Python classes.
*   **Method Names:** `__init__` ([simulation_engine/rl_env.py:10](simulation_engine/rl_env.py:10)), `reset` ([simulation_engine/rl_env.py:27](simulation_engine/rl_env.py:27)), `step` ([simulation_engine/rl_env.py:50](simulation_engine/rl_env.py:50)), `compute_robustness_reward` ([simulation_engine/rl_env.py:36](simulation_engine/rl_env.py:36)) use snake_case, adhering to PEP 8 for functions and methods.
*   **Variable Names:** Variables like `turns_per_episode`, `current_turn`, `rule_ids`, `param_names`, `action_space`, `observation_space`, `param_overrides` generally follow snake_case.
*   **Constants/Registries:** [`RULE_PARAM_REGISTRY`](../../simulation_engine/rules/rule_param_registry.py:7) is in SCREAMING_SNAKE_CASE, appropriate for global constants or registries.
*   **Loop Variables:** The use of `rid` for "rule ID" and `p` for "parameter name" in loops (e.g., [simulation_engine/rl_env.py:15](simulation_engine/rl_env.py:15), [simulation_engine/rl_env.py:17](simulation_engine/rl_env.py:17)) is concise and clear within their local context.
*   Overall, naming conventions are consistent and largely follow PEP 8 guidelines. No obvious AI assumption errors or significant deviations were noted in the naming.