# Module Analysis: `symbolic_system/gravity/integration.py`

## 1. Module Intent/Purpose

This module serves as an **integration layer** designed to bridge the new "Symbolic Gravity" system, specifically its pillar-based gravity fabric, with the existing Pulse codebase. Its primary role is to facilitate a smooth transition from the older overlay system to the new pillar-based approach by providing:
*   Adapters for data synchronization between overlays and pillars.
*   Hooks into the simulation lifecycle.
*   Control functions to enable/disable and manage the gravity system's influence.
*   Mechanisms to apply gravity-based corrections to predictions and record residuals for system learning.

## 2. Operational Status/Completeness

The module appears substantially complete for its defined integration role. Key functionalities include:
*   Initialization of gravity system components ([`initialize_gravity_system()`](symbolic_system/gravity/integration.py:33)).
*   Control functions ([`enable_gravity_system()`](symbolic_system/gravity/integration.py:119), [`disable_gravity_system()`](symbolic_system/gravity/integration.py:126), [`is_gravity_enabled()`](symbolic_system/gravity/integration.py:133)).
*   Data adaptation functions ([`adapt_overlays_to_pillars()`](symbolic_system/gravity/integration.py:146), [`adapt_pillars_to_overlays()`](symbolic_system/gravity/integration.py:162)).
*   Simulation lifecycle hooks ([`pre_simulation_hook()`](symbolic_system/gravity/integration.py:185), [`post_simulation_hook()`](symbolic_system/gravity/integration.py:203)).
*   Correction and learning mechanisms ([`apply_gravity_correction()`](symbolic_system/gravity/integration.py:226), [`record_prediction_residual()`](symbolic_system/gravity/integration.py:249), [`gravity_correction_decorator()`](symbolic_system/gravity/integration.py:273)).
*   Diagnostic functions ([`get_gravity_diagnostic_report()`](symbolic_system/gravity/integration.py:312), [`get_pillar_values()`](symbolic_system/gravity/integration.py:327)).

However, there are placeholder default values for `dt` (delta time) and `state_dimensionality` within the [`initialize_gravity_system()`](symbolic_system/gravity/integration.py:33) function (lines 71-72) when configuring the `ResidualGravityEngine`. These might require more dynamic or context-aware configuration.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Parameterization of `ResidualGravityEngine`:** The placeholder values for `dt` and `state_dimensionality` (lines 71-72 in [`initialize_gravity_system()`](symbolic_system/gravity/integration.py:33)) need to be addressed. These should likely be derived from the simulation's context or made explicitly configurable rather than using fixed defaults.
*   **Transition Strategy:** While this module facilitates the transition, the long-term plan for the overlay system (e.g., eventual deprecation) is not detailed here. Future work might involve simplifying this layer as the pillar system becomes primary.
*   **Error Handling:** Enhanced error handling and more detailed logging for edge cases during the overlay-pillar adaptation process (e.g., if an overlay expected by a pillar is missing) could improve robustness.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`simulation_engine.worldstate.WorldState`](simulation_engine/worldstate.py)
*   [`simulation_engine.state_mutation.adjust_overlay`](simulation_engine/state_mutation.py:18)
*   [`symbolic_system.gravity.symbolic_pillars.SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:20)
*   [`symbolic_system.gravity.engines.residual_gravity_engine.ResidualGravityEngine`](symbolic_system/gravity/engines/residual_gravity_engine.py:21)
*   [`symbolic_system.gravity.engines.residual_gravity_engine.GravityEngineConfig`](symbolic_system/gravity/engines/residual_gravity_engine.py:21)
*   [`symbolic_system.gravity.gravity_fabric.SymbolicGravityFabric`](symbolic_system/gravity/gravity_fabric.py:22)
*   [`symbolic_system.gravity.gravity_config.ResidualGravityConfig`](symbolic_system/gravity/gravity_config.py:23)

### External Library Dependencies:
*   `logging`
*   `typing` (Dict, List, Optional, Union, Any, Callable, Tuple)
*   `functools`
*   `numpy` (as `np`, though not directly used in this file, its import suggests potential use in underlying gravity components it initializes/interacts with)

### Interaction via Shared Data:
*   Reads from and writes to the `overlays` attribute of [`WorldState`](simulation_engine/worldstate.py) objects.
*   Manages and provides access to global instances: `_pillar_system` ([`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:20)) and `_gravity_fabric` ([`SymbolicGravityFabric`](symbolic_system/gravity/gravity_fabric.py:22)).

### Input/Output Files:
*   Primarily generates logging output via the `logging` module.
*   No direct data file input or output is apparent within this module.

## 5. Function and Class Example Usages

### Initialization and Control:
```python
from symbolic_system.gravity.integration import initialize_gravity_system, enable_gravity_system, is_gravity_enabled
from symbolic_system.gravity.gravity_config import ResidualGravityConfig

# Initialize with custom config
config = ResidualGravityConfig(lambda_=0.05)
pillar_sys, fabric = initialize_gravity_system(config)

if not is_gravity_enabled():
    enable_gravity_system()
```

### Applying Gravity Correction:
```python
from symbolic_system.gravity.integration import apply_gravity_correction

# Assuming gravity system is initialized and enabled
raw_prediction = 100.0
# 'variable_name' should correspond to a known pillar or variable context
corrected_prediction = apply_gravity_correction("some_economic_indicator", raw_prediction)
print(f"Raw: {raw_prediction}, Corrected: {corrected_prediction}")
```

### Recording Prediction Residual:
```python
from symbolic_system.gravity.integration import record_prediction_residual

# After obtaining an actual value for a prediction
predicted_val = 105.0
actual_val = 102.0
record_prediction_residual("some_economic_indicator", predicted_val, actual_val)
```

### Simulation Hooks (Conceptual Usage):
```python
# Within the main simulation loop:
# current_world_state = ...
# pre_simulation_hook(current_world_state)
# ... run simulation logic for one step, potentially updating current_world_state ...
# post_simulation_hook(current_world_state)
```

### Decorator for Gravity Correction:
```python
from symbolic_system.gravity.integration import gravity_correction_decorator

@gravity_correction_decorator
def my_predictive_function(param1, variable_name="target_variable_pillar_name"):
    # ... logic to produce a raw prediction ...
    raw_prediction = 10.0 # example
    return raw_prediction

# If gravity system is enabled, 'value' will be the corrected prediction
value = my_predictive_function("some_input_parameter")
```

## 6. Hardcoding Issues

*   **[`initialize_gravity_system()`](symbolic_system/gravity/integration.py:33):**
    *   `dt=1.0` (line 71): Explicitly commented as a "Default placeholder value". This likely needs to be configurable or derived from simulation settings.
    *   `state_dimensionality=1` (line 72): Also commented as a "Default placeholder value". This should reflect the actual dimensionality of the state vectors used by the `ResidualGravityEngine`.
*   **[`adapt_pillars_to_overlays()`](symbolic_system/gravity/integration.py:162):**
    *   `0.001` (line 179): Used as a fixed threshold to determine if a difference between a pillar value and an overlay value is significant enough to warrant an adjustment. This "magic number" could potentially be made configurable.
*   **[`gravity_correction_decorator()`](symbolic_system/gravity/integration.py:273):**
    *   `0.001` (line 302): Used as a fixed threshold for logging a gravity correction if the change is deemed significant. This could also be a configurable logging threshold.

## 7. Coupling Points

*   **Internal Gravity System:** High coupling with other modules within the `symbolic_system.gravity` subpackage, especially:
    *   [`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:20)
    *   [`SymbolicGravityFabric`](symbolic_system/gravity/gravity_fabric.py:22)
    *   [`ResidualGravityEngine`](symbolic_system/gravity/engines/residual_gravity_engine.py:21)
    *   Configuration objects like [`ResidualGravityConfig`](symbolic_system/gravity/gravity_config.py:23) and [`GravityEngineConfig`](symbolic_system/gravity/engines/residual_gravity_engine.py:21).
*   **Simulation Engine:** Strong dependency on:
    *   The [`WorldState`](simulation_engine/worldstate.py) object structure, particularly its `overlays` attribute.
    *   The [`adjust_overlay()`](simulation_engine/state_mutation.py:18) function from [`simulation_engine.state_mutation`](simulation_engine/state_mutation.py:18).
*   **Global State:** The use of module-level global variables (`_pillar_system`, `_gravity_fabric`, `_gravity_enabled`) for managing the state of the gravity system introduces global coupling. Access to these is generally managed via getter functions (e.g., [`get_pillar_system()`](symbolic_system/gravity/integration.py:89)), which mitigates direct global access but still represents a centralized state.
*   **Simulation Lifecycle:** The simulation hooks ([`pre_simulation_hook()`](symbolic_system/gravity/integration.py:185) and [`post_simulation_hook()`](symbolic_system/gravity/integration.py:203)) create an explicit dependency on the timing and calling conventions of the main simulation loop.

## 8. Existing Tests

*   A dedicated test file specifically for `symbolic_system/gravity/integration.py` (e.g., `test_integration.py`) was **not found** in the [`tests/symbolic_system/gravity/`](tests/symbolic_system/gravity/) directory.
*   The directory contains [`test_residual_gravity_engine.py`](tests/symbolic_system/gravity/test_residual_gravity_engine.py), which tests a core component utilized by this integration module, but it does not directly test the integration logic itself.
*   **Identified Gap:** There is a lack of direct unit tests for the functionalities provided by this module. This includes:
    *   The initialization and control flow (enable/disable).
    *   The correctness of data adaptation between overlays and pillars ([`adapt_overlays_to_pillars()`](symbolic_system/gravity/integration.py:146), [`adapt_pillars_to_overlays()`](symbolic_system/gravity/integration.py:162)).
    *   The behavior of simulation hooks.
    *   The application of the [`gravity_correction_decorator()`](symbolic_system/gravity/integration.py:273).
    *   The interaction logic for applying corrections and recording residuals.

## 9. Module Architecture and Flow

The module is structured around providing a clear API for integrating the Symbolic Gravity system:

1.  **Initialization and Global Access:**
    *   [`initialize_gravity_system()`](symbolic_system/gravity/integration.py:33) is the main entry point for setting up the `SymbolicPillarSystem`, `ResidualGravityEngine`, and `SymbolicGravityFabric`. These are stored as module-level global instances.
    *   Getter functions ([`get_pillar_system()`](symbolic_system/gravity/integration.py:89), [`get_gravity_fabric()`](symbolic_system/gravity/integration.py:104)) provide controlled access and ensure on-demand initialization if not already done.

2.  **Operational Control:**
    *   A global boolean flag, `_gravity_enabled`, controls whether gravity corrections are active.
    *   Functions ([`enable_gravity_system()`](symbolic_system/gravity/integration.py:119), [`disable_gravity_system()`](symbolic_system/gravity/integration.py:126), [`is_gravity_enabled()`](symbolic_system/gravity/integration.py:133)) manage this flag.

3.  **Data Synchronization (Overlay-Pillar Bridge):**
    *   [`adapt_overlays_to_pillars()`](symbolic_system/gravity/integration.py:146): Called to update the pillar system with values from the current `WorldState` overlays. This typically happens before gravity calculations.
    *   [`adapt_pillars_to_overlays()`](symbolic_system/gravity/integration.py:162): Called to update the `WorldState` overlays with values from the pillar system. This typically happens after pillar interactions or gravity effects have been processed.

4.  **Simulation Lifecycle Integration (Hooks):**
    *   [`pre_simulation_hook()`](symbolic_system/gravity/integration.py:185): Designed to be called before each simulation step. If gravity is enabled, it syncs overlays to pillars.
    *   [`post_simulation_hook()`](symbolic_system/gravity/integration.py:203): Designed to be called after each simulation step. If gravity is enabled, it allows the pillar system to apply its internal interactions and then syncs pillar values back to overlays.

5.  **Gravity Application and Learning:**
    *   [`apply_gravity_correction()`](symbolic_system/gravity/integration.py:226): Takes a variable name and a predicted value, and returns a corrected value by querying the `SymbolicGravityFabric`.
    *   [`record_prediction_residual()`](symbolic_system/gravity/integration.py:249): Allows the main system to feed back the difference between a prediction and an actual observed value to the `SymbolicGravityFabric` for learning and adaptation.
    *   [`gravity_correction_decorator()`](symbolic_system/gravity/integration.py:273): A utility to wrap predictive functions, automatically applying gravity corrections to their results if the system is enabled.

6.  **Diagnostics:**
    *   [`get_gravity_diagnostic_report()`](symbolic_system/gravity/integration.py:312): Provides a status report from the `SymbolicGravityFabric`.
    *   [`get_pillar_values()`](symbolic_system/gravity/integration.py:327): Returns a dictionary of current pillar names and their values from the `SymbolicPillarSystem`.

The overall flow is designed to allow the existing simulation engine to operate with minimal changes, while the gravity system can be toggled on/off to influence its behavior and learn from its outcomes.

## 10. Naming Conventions

*   The module generally adheres well to **PEP 8** standards for Python code, using `snake_case` for functions, methods, and variables.
*   Module-level global variables intended for internal use (`_pillar_system`, `_gravity_fabric`, `_gravity_enabled`) are prefixed with a single underscore, which is a common convention.
*   Function and parameter names are descriptive and clearly convey their purpose (e.g., [`initialize_gravity_system()`](symbolic_system/gravity/integration.py:33), [`adapt_overlays_to_pillars()`](symbolic_system/gravity/integration.py:146), `variable_name`, `predicted_value`).
*   Type hints are used extensively, improving code clarity and maintainability.
*   There are no obvious deviations from standard Python naming conventions or signs of AI-assumption errors in naming. The naming is consistent and human-readable.