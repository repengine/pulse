# Module Analysis: `symbolic_system/gravity/gravity_fabric.py`

## 1. Module Intent/Purpose

The primary role of the [`gravity_fabric.py`](symbolic_system/gravity/gravity_fabric.py:) module is to implement the core **Symbolic Gravity Fabric** for the Pulse system. This fabric utilizes "symbolic pillars" to dynamically support and adjust a "residual gravity field." The purpose of this field is to correct the outputs of simulations, aligning them more closely with observed reality by accounting for discrepancies or "residuals" between predicted and actual values. It aims to improve simulation accuracy by learning from these residuals.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope.
- It defines core data structures like [`ResidualPoint`](symbolic_system/gravity/gravity_fabric.py:28) and [`GravityFabricMetrics`](symbolic_system/gravity/gravity_fabric.py:140).
- The main class, [`SymbolicGravityFabric`](symbolic_system/gravity/gravity_fabric.py:217), is well-developed with methods for applying gravity corrections, recording residuals, managing pillars, and generating diagnostics.
- Configuration options are integrated via [`ResidualGravityConfig`](symbolic_system/gravity/gravity_config.py:1).
- There are no obvious `TODO` comments or major placeholders within the primary logic of the `SymbolicGravityFabric` class.
- Default values and configurations (e.g., `DEFAULT_CONFIG` from [`gravity_config.py`](symbolic_system/gravity/gravity_config.py:1)) are used, suggesting a functional baseline.

## 3. Implementation Gaps / Unfinished Next Steps

- **Extensibility:** While functional, the "natural pillar interactions" ([`pillar_system.apply_interactions()`](symbolic_system/gravity/gravity_fabric.py:347)) are managed by [`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:1), and the complexity/sophistication of these interactions isn't detailed within `gravity_fabric.py` itself. The current implementation might be a foundational version, with more complex interaction logic potentially planned for `SymbolicPillarSystem`.
- **Advanced Learning/Adaptation:** The weight update mechanism ([`gravity_engine.update_weights()`](symbolic_system/gravity/gravity_fabric.py:363)) is based on residuals. More advanced adaptive learning algorithms or meta-learning strategies for the fabric's parameters (e.g., learning rate, lambda) could be future enhancements. The `enable_adaptive_lambda` config suggests some adaptiveness, but its full extent isn't clear from this module alone.
- **Dynamic Pillar Management:** While pillars can be added ([`add_pillar()`](symbolic_system/gravity/gravity_fabric.py:568)), mechanisms for automatic discovery, pruning, or merging of pillars based on performance or redundancy are not explicitly present and could be a logical next step.
- **State Dimensionality/dt in Engine:** The [`ResidualGravityEngine`](symbolic_system/gravity/engines/residual_gravity_engine.py:1) is initialized with placeholder `dt=1.0` and `state_dimensionality=1` ([`gravity_fabric.py:291-292`](symbolic_system/gravity/gravity_fabric.py:291-292)). This suggests that these parameters might need to be dynamically set or configured based on the specific context or variable being corrected, which is not explicitly handled during the `SymbolicGravityFabric` initialization. This might be handled at a higher level or is an area for refinement.

## 4. Connections & Dependencies

### Direct Project Module Imports:
- [`engine.worldstate`](simulation_engine/worldstate.py:): Imports [`WorldState`](simulation_engine/worldstate.py:1) for accessing current simulation state.
- [`symbolic_system.gravity.symbolic_pillars`](symbolic_system/gravity/symbolic_pillars.py:): Imports [`SymbolicPillar`](symbolic_system/gravity/symbolic_pillars.py:1) and [`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:1) for managing the symbolic pillars.
- [`symbolic_system.gravity.engines.residual_gravity_engine`](symbolic_system/gravity/engines/residual_gravity_engine.py:): Imports [`ResidualGravityEngine`](symbolic_system/gravity/engines/residual_gravity_engine.py:1) and [`GravityEngineConfig`](symbolic_system/gravity/engines/residual_gravity_engine.py:1) for the core correction calculations.
- [`symbolic_system.gravity.gravity_config`](symbolic_system/gravity/gravity_config.py:): Imports [`ResidualGravityConfig`](symbolic_system/gravity/gravity_config.py:1) and `DEFAULT_CONFIG` for configuration.

### External Library Dependencies:
- `logging`: Standard Python logging.
- `numpy` (as `np`): Used for numerical operations, particularly `np.mean` ([`gravity_fabric.py:200`](symbolic_system/gravity/gravity_fabric.py:200), [`gravity_fabric.py:878`](symbolic_system/gravity/gravity_fabric.py:878)).
- `typing`: For type hints (`Dict`, `List`, `Optional`, `Tuple`, `Any`, `Union`, `Set`).
- `time`: For timestamping ([`ResidualPoint.timestamp`](symbolic_system/gravity/gravity_fabric.py:52), performance tracking).
- `dataclasses`: For creating `ResidualPoint` and `GravityFabricMetrics`.
- `datetime`: For converting timestamps to ISO format in [`ResidualPoint.to_dict()`](symbolic_system/gravity/gravity_fabric.py:116).

### Interaction with Other Modules via Shared Data:
- **[`WorldState`](simulation_engine/worldstate.py:1) Object:** The fabric reads pillar values from and potentially updates overlays in the `WorldState` object passed to its methods (e.g., [`apply_gravity()`](symbolic_system/gravity/gravity_fabric.py:309), [`apply_to_world_state()`](symbolic_system/gravity/gravity_fabric.py:711)). This is the primary mechanism for shared data interaction.
- **Configuration Objects:** Relies on [`ResidualGravityConfig`](symbolic_system/gravity/gravity_config.py:1) and [`GravityEngineConfig`](symbolic_system/gravity/engines/residual_gravity_engine.py:1) which may be instantiated and passed from higher-level orchestrating modules.

### Input/Output Files:
- **Logs:** Uses standard Python `logging`, so log output location depends on the overall system's logging configuration.
- **Data Files/Metadata:** The module itself does not directly read from or write to persistent data files or metadata stores. State (like pillar weights in `ResidualGravityEngine`) is maintained in memory. Persistence would likely be handled by an orchestrating layer or if `ResidualGravityEngine` itself has such capabilities (not evident from this module).

## 5. Function and Class Example Usages

### [`ResidualPoint`](symbolic_system/gravity/gravity_fabric.py:28)
Represents a single data point comparing a prediction to an actual value, along with any gravity correction applied.
```python
# Example (conceptual)
point = ResidualPoint(
    variable_name="temperature_forecast",
    predicted=25.5,
    actual=26.1,
    symbolic_state={"season_summer": 0.8, "time_of_day_noon": 0.9}
)
point.corrected = 25.8 # After gravity fabric applies correction
print(point.to_dict())
```

### [`GravityFabricMetrics`](symbolic_system/gravity/gravity_fabric.py:140)
Tracks metrics related to the fabric's operation, like number of corrections and dominant pillars.
```python
# Example (conceptual, typically used internally by SymbolicGravityFabric)
metrics = GravityFabricMetrics(max_history=1000)
metrics.record_correction(magnitude=0.3)
metrics.record_residual(magnitude=0.6)
metrics.record_dominant_pillars(["season_summer"])
print(metrics.get_avg_correction())
```

### [`SymbolicGravityFabric`](symbolic_system/gravity/gravity_fabric.py:217)
The main class for applying corrections.
```python
# Conceptual Usage
from engine.worldstate import WorldState # Assuming WorldState is defined
from symbolic_system.gravity.gravity_config import DEFAULT_CONFIG

# Initialize
fabric = SymbolicGravityFabric(
    pillar_names=["pillar_A", "pillar_B"], 
    config=DEFAULT_CONFIG
)
current_world_state = WorldState() # Populate with actual data

# Set some pillar values in the world state (or fabric directly)
# current_world_state.set_symbolic_value("pillar_A", 0.7) 
# fabric.set_pillar_value("pillar_A", 0.7) # Alternative

# Apply gravity to a single prediction
predicted_val = 10.0
actual_val = 10.5 # Ground truth
corrected_val, info = fabric.apply_gravity(current_world_state, predicted_val, truth=actual_val)
print(f"Original: {predicted_val}, Corrected: {corrected_val}, Actual: {actual_val}")

# Record a residual (if truth is known later or separately)
# fabric.record_residual("my_variable", predicted_value=10.0, actual_value=10.5)

# Get diagnostics
report = fabric.generate_diagnostic_report()
print(report["suggestions"])
```

## 6. Hardcoding Issues

- **Default `dt` and `state_dimensionality` for `ResidualGravityEngine`:** During initialization of `ResidualGravityEngine` within `SymbolicGravityFabric.__init__()`, `dt` is hardcoded to `1.0` and `state_dimensionality` to `1` ([`gravity_fabric.py:291-292`](symbolic_system/gravity/gravity_fabric.py:291-292)). While these might be placeholders or sensible defaults for some contexts, they are not dynamically configured based on the variable or system being modeled. This could limit the engine's adaptability if not overridden or handled elsewhere.
- **Magic Numbers for Error/Improvement Thresholds:**
    - `1e-10` is used as a threshold for near-zero original error in [`ResidualPoint.improvement_pct()`](symbolic_system/gravity/gravity_fabric.py:110) and [`SymbolicGravityFabric.get_improvement_percentage()`](symbolic_system/gravity/gravity_fabric.py:908).
    - `1e-10` is used as a threshold for near-zero total weight in [`SymbolicGravityFabric.get_pillar_contributions()`](symbolic_system/gravity/gravity_fabric.py:929).
    These are common for floating-point comparisons but could ideally be constants or configurable.
- **Default `max_history` for `GravityFabricMetrics`:** The `max_history` for metrics is taken from `self.config.max_history` ([`gravity_fabric.py:296`](symbolic_system/gravity/gravity_fabric.py:296)), which is good. However, `SymbolicPillar` also uses `max_history` ([`gravity_fabric.py:592`](symbolic_system/gravity/gravity_fabric.py:592)) taken from the same config, ensuring consistency.
- **Health Suggestion Thresholds:** In [`suggest_fixes()`](symbolic_system/gravity/gravity_fabric.py:661):
    - Fragility threshold: `0.7` ([`gravity_fabric.py:674`](symbolic_system/gravity/gravity_fabric.py:674))
    - Average residual magnitude threshold: `2.0` ([`gravity_fabric.py:689`](symbolic_system/gravity/gravity_fabric.py:689))
    - Dominant pillar threshold: `0.8` (80% of total corrections) ([`gravity_fabric.py:697`](symbolic_system/gravity/gravity_fabric.py:697))
    These thresholds are hardcoded and might benefit from being configurable for different operational contexts.

## 7. Coupling Points

- **[`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:1):** Tightly coupled. `SymbolicGravityFabric` instantiates and heavily relies on `SymbolicPillarSystem` for managing pillar states, interactions, and retrieving pillar values.
- **[`ResidualGravityEngine`](symbolic_system/gravity/engines/residual_gravity_engine.py:1):** Tightly coupled. `SymbolicGravityFabric` instantiates and delegates the core correction logic and weight updates to `ResidualGravityEngine`. The configuration of the engine is derived from `SymbolicGravityFabric`'s own configuration.
- **[`WorldState`](simulation_engine/worldstate.py:1):** `SymbolicGravityFabric` methods frequently require a `WorldState` object as input to load pillar values and potentially update overlays. This makes it dependent on the structure and interface of `WorldState`.
- **[`ResidualGravityConfig`](symbolic_system/gravity/gravity_config.py:1):** The behavior of the fabric is significantly driven by this configuration object.
- **Implicit Data Flow for Pillar Values:** Pillar values are read from `WorldState` (or set directly), processed by `SymbolicPillarSystem`, then fed as a `symbol_vec` (dictionary) to `ResidualGravityEngine`. The flow is clear but creates dependencies across these components.

## 8. Existing Tests

- A file [`test_residual_gravity_engine.py`](tests/symbolic_system/gravity/test_residual_gravity_engine.py:) exists in the `tests/symbolic_system/gravity/` directory. This indicates that the `ResidualGravityEngine`, a core component used by `SymbolicGravityFabric`, has dedicated tests.
- There is **no specific test file** named `test_gravity_fabric.py` or similar that directly targets the `SymbolicGravityFabric` class and its integrated behavior (including its interaction with `SymbolicPillarSystem`).
- **Coverage Gap:** This suggests a potential gap in testing for the `SymbolicGravityFabric` class itself. While its components (`ResidualGravityEngine`, `SymbolicPillarSystem` if it has its own tests) might be unit-tested, integration tests for `SymbolicGravityFabric` ensuring all parts work together correctly (pillar loading, interaction, correction application, metric recording, diagnostics) appear to be missing or are not obviously named.
- The existing tests for `ResidualGravityEngine` would cover the mathematical core of the correction mechanism, but not the orchestration, state management, or metric tracking logic within `SymbolicGravityFabric`.

## 9. Module Architecture and Flow

### Architecture:
The module defines three main classes:
1.  **[`ResidualPoint`](symbolic_system/gravity/gravity_fabric.py:28):** A dataclass representing a single instance of prediction, actual value, and correction. It includes metadata like timestamp and symbolic state.
2.  **[`GravityFabricMetrics`](symbolic_system/gravity/gravity_fabric.py:140):** A dataclass for collecting and reporting various metrics about the fabric's performance (e.g., number of corrections, average magnitudes, dominant pillars).
3.  **[`SymbolicGravityFabric`](symbolic_system/gravity/gravity_fabric.py:217):** The central class. It orchestrates the gravity correction process.
    *   It owns an instance of [`SymbolicPillarSystem`](symbolic_system/gravity/symbolic_pillars.py:1) to manage the state and interactions of symbolic pillars.
    *   It owns an instance of [`ResidualGravityEngine`](symbolic_system/gravity/engines/residual_gravity_engine.py:1) to perform the actual calculation of corrections and update underlying weights.
    *   It maintains a history of [`ResidualPoint`](symbolic_system/gravity/gravity_fabric.py:28)s and an instance of [`GravityFabricMetrics`](symbolic_system/gravity/gravity_fabric.py:140).

### Primary Data/Control Flows:
1.  **Initialization:**
    *   `SymbolicGravityFabric` is initialized with configuration, pillar names (or a pre-configured `SymbolicPillarSystem`), and an optional pre-configured `ResidualGravityEngine`.
    *   It sets up its internal `SymbolicPillarSystem` and `ResidualGravityEngine`.
2.  **Applying Correction (e.g., [`apply_gravity()`](symbolic_system/gravity/gravity_fabric.py:309)):**
    *   Input: Current [`WorldState`](simulation_engine/worldstate.py:1), predicted value, optional ground truth.
    *   Pillar values are loaded from `WorldState` into `SymbolicPillarSystem`.
    *   `SymbolicPillarSystem` may apply internal interactions among pillars.
    *   Current pillar values (symbolic state) are retrieved as a dictionary (`symbol_vec`).
    *   `ResidualGravityEngine.apply_correction()` is called with the predicted value and `symbol_vec` to get the corrected value.
    *   Metrics are updated (correction magnitude, dominant pillars).
    *   If ground truth is provided:
        *   Residual (truth - predicted) is calculated.
        *   `ResidualGravityEngine.update_weights()` is called with the residual and `symbol_vec`.
        *   Metrics (residual magnitude, update count) are updated.
        *   A [`ResidualPoint`](symbolic_system/gravity/gravity_fabric.py:28) is created and stored (via [`record_residual()`](symbolic_system/gravity/gravity_fabric.py:770)).
    *   `SymbolicPillarSystem` may update overlays in the `WorldState` with new pillar values post-interaction.
    *   Output: Corrected value and diagnostic information.
3.  **Recording Residuals (e.g., [`record_residual()`](symbolic_system/gravity/gravity_fabric.py:770)):**
    *   Similar to the truth-provided path in `apply_gravity`, but can be called independently.
    *   Calculates residual, updates engine weights, records metrics, and stores a `ResidualPoint`.
4.  **Diagnostics & Pillar Management:**
    *   Methods exist to get metrics ([`get_metrics()`](symbolic_system/gravity/gravity_fabric.py:597)), diagnostic reports ([`generate_diagnostic_report()`](symbolic_system/gravity/gravity_fabric.py:935)), suggest fixes ([`suggest_fixes()`](symbolic_system/gravity/gravity_fabric.py:661)), and manage pillars (add, set/get values).

## 10. Naming Conventions

- **Classes:** Use PascalCase (e.g., `SymbolicGravityFabric`, `ResidualPoint`, `GravityFabricMetrics`), which is standard (PEP 8).
- **Methods & Functions:** Use snake_case (e.g., `apply_gravity`, `record_residual`, `get_top_contributors`), which is standard (PEP 8).
- **Variables:** Generally use snake_case (e.g., `pillar_system`, `gravity_engine`, `symbol_vec`, `predicted_value`).
- **Constants/Defaults:** `DEFAULT_CONFIG` is uppercase, which is standard.
- **Clarity:** Names are generally descriptive and clearly indicate their purpose (e.g., `ResidualPoint`, `correction_magnitudes`, `apply_gravity_batch`).
- **`variable` vs. `variable_name` in `ResidualPoint`:** The class `ResidualPoint` has `variable_name` as an attribute and a property `variable` that aliases `variable_name` for "backward compatibility" ([`gravity_fabric.py:70-79`](symbolic_system/gravity/gravity_fabric.py:70-79)). This is a good way to handle a rename while maintaining compatibility.
- **`lambda_`:** The configuration parameter `lambda_` ([`gravity_fabric.py:280`](symbolic_system/gravity/gravity_fabric.py:280), [`gravity_fabric.py:643`](symbolic_system/gravity/gravity_fabric.py:643)) uses a trailing underscore to avoid clashing with Python's `lambda` keyword. This is a common and accepted PEP 8 practice.
- **Potential AI Assumption Errors/Deviations:**
    - The author is listed as "Pulse v3.5" ([`gravity_fabric.py:10`](symbolic_system/gravity/gravity_fabric.py:10)), suggesting AI generation or significant AI contribution.
    - Naming conventions are largely consistent with Python best practices (PEP 8). No obvious deviations that would clearly indicate AI misinterpretation of common patterns were observed. The code structure and naming are quite conventional for Python.
    - The use of "compatibility method" in the comment for [`reset_weights()`](symbolic_system/gravity/gravity_fabric.py:985) is clear.

Overall, the naming is clear, consistent, and follows Python conventions well.