# Module Analysis: symbolic_system.gravity.integration_example

**File Path:** [`symbolic_system/gravity/integration_example.py`](../../symbolic_system/gravity/integration_example.py)
## 1. Module Intent/Purpose

The primary role of this module is to serve as a practical example and demonstration of how to integrate the Symbolic Gravity system within a Pulse simulation environment. It specifically illustrates the transition from an older overlay system to the newer pillar-based gravity fabric approach. It provides runnable examples for both integrated simulation usage and standalone component usage.

## 2. Operational Status/Completeness

- The module appears functionally complete for its intended purpose as an example.
- It includes two main demonstration functions: [`example_with_simulation()`](../../symbolic_system/gravity/integration_example.py:58) and [`example_standalone_usage()`](../../symbolic_system/gravity/integration_example.py:119).
- The [`example_with_simulation()`](../../symbolic_system/gravity/integration_example.py:58) function contains a placeholder comment `"# ... Rest of simulation setup ..."` ([`symbolic_system/gravity/integration_example.py:80`](../../symbolic_system/gravity/integration_example.py:80)), indicating that a full simulation setup is intentionally omitted for conciseness, which is appropriate for an example.
- By default, when run as a script, it executes [`example_standalone_usage()`](../../symbolic_system/gravity/integration_example.py:187).
- There are no apparent TODOs or critical placeholders that would prevent the examples from running.

## 3. Implementation Gaps / Unfinished Next Steps

- As an example module, it is not designed to be an extensive, production-ready component.
- The main "gap" is the aforementioned `"# ... Rest of simulation setup ..."` ([`symbolic_system/gravity/integration_example.py:80`](../../symbolic_system/gravity/integration_example.py:80)) in [`example_with_simulation()`](../../symbolic_system/gravity/integration_example.py:58), which is an intentional simplification.
- The module successfully fulfills its role of demonstrating the usage of the gravity system and does not inherently suggest missing follow-up modules or features beyond what it showcases.
- There are no indications of development starting on a planned path and then deviating or stopping short.

## 4. Connections & Dependencies

### Internal Project Dependencies:
- [`simulation_engine.worldstate.WorldState`](../../simulation_engine/worldstate.py): Used for managing simulation state in examples. ([`symbolic_system/gravity/integration_example.py:15`](../../symbolic_system/gravity/integration_example.py:15))
- [`simulation_engine.simulation_executor.SimulationExecutor`](../../simulation_engine/simulation_executor.py): Used as the backbone for the integrated simulation example. ([`symbolic_system/gravity/integration_example.py:16`](../../symbolic_system/gravity/integration_example.py:16))
- [`symbolic_system.gravity.gravity_config.ResidualGravityConfig`](../../symbolic_system/gravity/gravity_config.py): Used for configuring the gravity system. ([`symbolic_system/gravity/integration_example.py:18`](../../symbolic_system/gravity/integration_example.py:18))
- [`symbolic_system.gravity.integration`](../../symbolic_system/gravity/integration.py): Core functions for interacting with the gravity system. ([`symbolic_system/gravity/integration_example.py:19-24`](../../symbolic_system/gravity/integration_example.py:19-24))
  - [`initialize_gravity_system()`](../../symbolic_system/gravity/integration.py)
  - [`enable_gravity_system()`](../../symbolic_system/gravity/integration.py)
  - [`pre_simulation_hook()`](../../symbolic_system/gravity/integration.py)
  - [`post_simulation_hook()`](../../symbolic_system/gravity/integration.py)
  - [`record_prediction_residual()`](../../symbolic_system/gravity/integration.py)
  - [`apply_gravity_correction()`](../../symbolic_system/gravity/integration.py)
  - [`get_gravity_fabric()`](../../symbolic_system/gravity/integration.py)
  - [`get_pillar_system()`](../../symbolic_system/gravity/integration.py)

### External Library Dependencies:
- `logging`: For informational output. ([`symbolic_system/gravity/integration_example.py:11`](../../symbolic_system/gravity/integration_example.py:11))
- `numpy`: For numerical operations, particularly `np.random.normal()` in data simulation. ([`symbolic_system/gravity/integration_example.py:12`](../../symbolic_system/gravity/integration_example.py:12))
- `typing`: For type hints (`Dict`, `List`, `Tuple`, `Any`, `Optional`). ([`symbolic_system/gravity/integration_example.py:13`](../../symbolic_system/gravity/integration_example.py:13))

### Data Interaction:
- Interacts with the simulation state (an instance of `WorldState`) by getting and setting attributes (e.g., `market_stress`, `spx_predicted`, `vix_corrected`) using `getattr` and direct assignment.
- No direct file input/output is performed by this module, aside from console logging.

## 5. Function and Class Example Usages

- **[`configure_simulation_with_gravity(simulation: SimulationExecutor, gravity_config: Optional[ResidualGravityConfig] = None)`](../../symbolic_system/gravity/integration_example.py:29-56):**
    - **Purpose:** Configures a given `SimulationExecutor` instance to utilize the Symbolic Gravity system.
    - **Usage Example:**
      ```python
      simulation = SimulationExecutor()
      gravity_config = ResidualGravityConfig(lambda_=0.3, eta=0.02) # Optional
      configure_simulation_with_gravity(simulation, gravity_config)
      ```
    - **Key Actions:** Initializes the gravity system, enables it, and registers pre-simulation and post-simulation hooks with the `SimulationExecutor`.

- **[`example_with_simulation()`](../../symbolic_system/gravity/integration_example.py:58-117):**
    - **Purpose:** Demonstrates the integration and runtime usage of the Symbolic Gravity system within a mock simulation loop.
    - **Key Actions:**
        - Sets up and configures a `SimulationExecutor` with the gravity system.
        - Iterates through simulated steps, showing how to:
            - Adjust pillar values dynamically (e.g., `pillar_system.adjust_pillar("despair", 0.05)`).
            - Record prediction residuals (e.g., `record_prediction_residual('SPX', predicted_value, actual_value)`).
            - Apply gravity corrections to predictions (e.g., `apply_gravity_correction('VIX', raw_prediction)`).
        - Generates and prints a diagnostic report from the gravity fabric at the end.

- **[`example_standalone_usage()`](../../symbolic_system/gravity/integration_example.py:119-183):**
    - **Purpose:** Illustrates how to use the components of the Symbolic Gravity system (pillars, fabric) independently of a full `SimulationExecutor`.
    - **Key Actions:**
        - Initializes and enables the gravity system.
        - Directly interacts with the `PillarSystem` and `GravityFabric`.
        - Simulates data, records residuals (e.g., `fabric.record_residual("SPX", predicted_value, true_value)`).
        - Adjusts pillar values and observes their impact.
        - Retrieves and prints various metrics like recent residuals, Mean Absolute Error (MAE), improvement percentages, and pillar contributions.

## 6. Hardcoding Issues

The module contains several hardcoded values, which are generally acceptable for an example module but would require parameterization in a production system:
- **Configuration Parameters:** Default values for `ResidualGravityConfig` if not provided, and specific values within [`example_with_simulation()`](../../symbolic_system/gravity/integration_example.py:69-75) (e.g., `lambda_=0.3`, `eta=0.02`).
- **Pillar Names (Magic Strings):** "hope", "despair", "rage" are used directly as strings (e.g., [`symbolic_system/gravity/integration_example.py:93`](../../symbolic_system/gravity/integration_example.py:93), [`symbolic_system/gravity/integration_example.py:132`](../../symbolic_system/gravity/integration_example.py:132)).
- **Variable Names for Residuals/Corrections (Magic Strings):** 'SPX', 'VIX' (e.g., [`symbolic_system/gravity/integration_example.py:101`](../../symbolic_system/gravity/integration_example.py:101), [`symbolic_system/gravity/integration_example.py:105`](../../symbolic_system/gravity/integration_example.py:105)).
- **State Attribute Names (Magic Strings):** Accessed via `getattr` (e.g., `market_stress`, `spx_predicted`, `spx_actual`, `vix_predicted` in [`symbolic_system/gravity/integration_example.py:91-104`](../../symbolic_system/gravity/integration_example.py:91-104)).
- **Numerical Values:** Loop iteration counts (100, 50), thresholds (0.7), pillar adjustment magnitudes (0.05, -0.03), and parameters for simulated data generation.

## 7. Coupling Points

- **High Coupling with `simulation_engine`:** Specifically with [`SimulationExecutor`](../../simulation_engine/simulation_executor.py) (hook system, step execution) and the implicit structure of [`WorldState`](../../simulation_engine/worldstate.py) (attribute access).
- **High Coupling with `symbolic_system.gravity.integration`:** This module acts as the primary API for the gravity system, so the example is tightly bound to its functions.
- **Configuration Coupling:** Depends on [`ResidualGravityConfig`](../../symbolic_system/gravity/gravity_config.py) for setting up the gravity system.

## 8. Existing Tests

- This module is an example and, as such, does not have its own dedicated unit tests (e.g., no `test_integration_example.py` was found).
- It functions as an integration demonstration. The core components it utilizes (e.g., `GravityFabric`, `PillarSystem`, `ResidualGravityEngine`) are expected to be tested in their respective dedicated test files (e.g., [`tests/symbolic_system/gravity/test_residual_gravity_engine.py`](../../tests/symbolic_system/gravity/test_residual_gravity_engine.py)).

## 9. Module Architecture and Flow

### Architecture:
- The module consists of three primary functions:
    1.  [`configure_simulation_with_gravity()`](../../symbolic_system/gravity/integration_example.py:29): A helper to integrate the gravity system into a `SimulationExecutor`.
    2.  [`example_with_simulation()`](../../symbolic_system/gravity/integration_example.py:58): Demonstrates the gravity system within a simulated environment loop.
    3.  [`example_standalone_usage()`](../../symbolic_system/gravity/integration_example.py:119): Shows direct usage of gravity system components.
- A global logger ([`logger`](../../symbolic_system/gravity/integration_example.py:26)) is initialized.

### Control Flow:
- **Script Execution (`if __name__ == "__main__":`)**:
    - Calls [`example_standalone_usage()`](../../symbolic_system/gravity/integration_example.py:187) by default.
    - [`example_with_simulation()`](../../symbolic_system/gravity/integration_example.py:190) is present but commented out.
- **[`example_with_simulation()`](../../symbolic_system/gravity/integration_example.py:58) Flow:**
    1.  Initializes logging and creates `SimulationExecutor` and `ResidualGravityConfig`.
    2.  Calls [`configure_simulation_with_gravity()`](../../symbolic_system/gravity/integration_example.py:78).
    3.  Enters a loop simulating time steps:
        - Advances simulation (`simulation.step_forward()`).
        - Retrieves current state.
        - Optionally adjusts pillars based on state (e.g., `state.market_stress`).
        - Records prediction residuals (e.g., for 'SPX').
        - Applies gravity correction (e.g., for 'VIX').
        - Stores corrected prediction in the state.
    4.  Prints a diagnostic report from the gravity fabric.
- **[`example_standalone_usage()`](../../symbolic_system/gravity/integration_example.py:119) Flow:**
    1.  Initializes and enables the gravity system directly.
    2.  Retrieves `PillarSystem` and `GravityFabric` instances.
    3.  Sets initial values for pillars.
    4.  Enters a loop simulating predictions and actuals:
        - Generates synthetic data for predictions and actuals, incorporating pillar influence.
        - Records residuals directly using `fabric.record_residual()`.
        - Periodically adjusts pillar values.
    5.  Prints various metrics: recent residuals, MAE, improvement percentage, pillar contributions, and top contributing pillars from the engine.

## 10. Naming Conventions

- **Functions and Variables:** Follow PEP 8 `snake_case` (e.g., [`configure_simulation_with_gravity`](../../symbolic_system/gravity/integration_example.py:29), `pillar_system`).
- **Class Names:** Imported classes like `SimulationExecutor` and `ResidualGravityConfig` use `PascalCase`, consistent with Python conventions.
- **Constants/Magic Strings:** Strings such as "hope", "despair", "SPX", "VIX" are used directly. While common in examples, these might be defined as constants in production code for better maintainability.
- **Author Tag:** The author is listed as "Pulse v3.5" ([`symbolic_system/gravity/integration_example.py:8`](../../symbolic_system/gravity/integration_example.py:8)), which might be an AI-generated placeholder or a versioning note.
- The naming is generally descriptive and does not show obvious errors or deviations from common Python standards.