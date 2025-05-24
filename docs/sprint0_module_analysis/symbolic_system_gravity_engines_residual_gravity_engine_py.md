# Module Analysis: `symbolic_system.gravity.engines.residual_gravity_engine`

**File Path:** [`symbolic_system/gravity/engines/residual_gravity_engine.py`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:1)
**Test File Path:** [`tests/symbolic_system/gravity/test_residual_gravity_engine.py`](../../tests/symbolic_system/gravity/test_residual_gravity_engine.py:1)

## 1. Module Intent/Purpose

The primary role of the [`residual_gravity_engine.py`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:1) module is to implement the `ResidualGravityEngine`. This engine is a core component of the Symbolic Gravity System. Its main responsibility is to learn a low-rank residual correction, mathematically represented as `g_t = B * s_t`. This correction "nudges" simulation outputs (x^_t+1) closer to observed reality (y_t+1) by applying an adjustment based on symbolic pillar intensities (`s_t`) and a dynamically learned impact matrix (`B`). The learning process utilizes online ridge-regression with a momentum term. The corrected state is then `x*_t+1 = x^_t+1 + λ * g_t+1`.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational.
- It features a comprehensive [`GravityEngineConfig`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:26) class for managing numerous parameters with defaults sourced from [`config.gravity_config`](../../config/gravity_config.py:1).
- The main [`ResidualGravityEngine`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:129) class is well-developed, including functionalities for:
    - Computing gravity corrections ([`compute_gravity()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:278)).
    - Updating the impact matrix ([`update_impact_matrix()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:341)).
    - Applying corrections to simulation vectors ([`apply_gravity_correction()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:451)).
    - Adaptive lambda adjustment ([`_update_adaptive_lambda()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:577)).
    - Fragility calculation ([`_calculate_fragility()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:632)).
    - A "Shadow Model Trigger" mechanism ([`process_and_correct()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:722)) to flag potential issues if the gravity model explains too much variance.
    - Diagnostic tools ([`get_stats()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:962), [`check_health()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:1020)).
    - Serialization and deserialization capabilities ([`to_dict()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:1116), [`from_dict()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:1140)).
- It includes considerations for backward compatibility for single-dimensional state representations.
- Docstrings and inline comments are extensive, explaining the mathematical underpinnings and implementation choices.
- No explicit "TODO" markers or obvious unfinished placeholders were found within the code.

## 3. Implementation Gaps / Unfinished Next Steps

- **Full Transition to Impact Matrix:** The module notes that legacy attributes `weights` (dictionary) and `_v` (momentum buffer dictionary) are for backward compatibility with single-dimensional states and will be deprecated in favor of `impact_matrix_B` and `_v_matrix` for multi-dimensional states. This suggests an ongoing or planned full transition.
- **Shadow Model Trigger Downstream Actions:** While the shadow model trigger mechanism is implemented to flag a `review_needed_flag`, the specific actions or system responses that occur when this flag is true are not detailed within this module. This likely integrates with a broader monitoring or operational review process.
- **Automated Health Recommendations:** The [`check_health()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:1020) method provides textual recommendations. Further development could involve more automated responses or integrations based on these health checks.
- **EWMA Tuning:** The Exponentially Weighted Moving Average (EWMA) decay for the impact matrix is implemented. However, the optimal `ewma_span` and its real-world effectiveness might require further empirical validation and tuning within the live system.

## 4. Connections & Dependencies

### Direct Project Module Imports:
-   [`utils.log_utils`](../../utils/log_utils.py:1): For `get_logger`.
-   [`config.gravity_config`](../../config/gravity_config.py:1) (as `grav_cfg`): Provides default configuration values and various thresholds.
-   [`symbolic_system.gravity.symbolic_pillars.SymbolicPillarSystem`](../../symbolic_system/gravity/symbolic_pillars.py:25): Type hint and used in [`process_with_pillar_system()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:776).
-   [`symbolic_system.context.is_symbolic_enabled`](../../symbolic_system/context.py:1): Runtime check to conditionally bypass gravity computation.

### External Library Dependencies:
-   `numpy` (as `np`): Extensively used for numerical computations, especially matrix and vector operations.
-   `collections.defaultdict`, `collections.deque`: Used for internal data structures (e.g., `weights`, `recent_residuals`).
-   `typing`: For type hinting (`Dict`, `List`, `Optional`, etc.).

### Interactions:
-   **Simulation System:** Consumes `sim_vec` (simulation output) and `truth_vec` (observed reality) from an external source.
-   **Symbolic Pillar System:** Receives `symbol_vec` (symbol intensities) from a [`SymbolicPillarSystem`](../../symbolic_system/gravity/symbolic_pillars.py:25) or equivalent source.
-   **Logging System:** Outputs logs via the logger obtained from [`utils.log_utils`](../../utils/log_utils.py:1).
-   **Persistence/Sharing:** The `to_dict` and `from_dict` methods imply that the engine's state (including the `impact_matrix_B`) can be serialized, suggesting potential persistence or sharing with other components.

### Input/Output Files:
-   **Logs:** Generates log messages.
-   No direct reading or writing of data/metadata files, but supports serialization which could be used for such purposes by other modules.

## 5. Function and Class Example Usages

### [`GravityEngineConfig`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:26)
```python
from symbolic_system.gravity.engines.residual_gravity_engine import GravityEngineConfig

# Initialize with specific parameters, others will use defaults
config = GravityEngineConfig(
    lambda_=0.1,
    learning_rate=0.01,
    regularization_strength=0.001
)
```

### [`ResidualGravityEngine`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:129)
```python
import numpy as np
from symbolic_system.gravity.engines.residual_gravity_engine import ResidualGravityEngine, GravityEngineConfig

# Configuration
pillar_names = ['hope', 'despair', 'market_sentiment']
engine_config = GravityEngineConfig(lambda_=0.1, learning_rate=0.005)
state_dim = 1 # or > 1 for multi-dimensional state
dt_val = 1.0

# Initialization
engine = ResidualGravityEngine(
    config=engine_config,
    dt=dt_val,
    state_dimensionality=state_dim,
    pillar_names=pillar_names
)

# Example Data
sim_output = np.array([10.0]) if state_dim > 1 else 10.0
truth_observation = np.array([10.5]) if state_dim > 1 else 10.5
symbol_intensities = {'hope': 0.8, 'despair': -0.3, 'market_sentiment': 0.5}

# Combined processing: calculate residual, update impact matrix, apply correction
corrected_prediction, review_needed = engine.process_and_correct(
    sim_vec=sim_output,
    truth_vec=truth_observation,
    symbol_vec=symbol_intensities,
    update_weights=True
)
# corrected_prediction is the simulation output adjusted by the gravity engine
# review_needed is a flag from the shadow model trigger

# Individual steps (can also be called separately):
# 1. Compute gravity based on current impact matrix and symbols
# gravity_val = engine.compute_gravity(symbol_intensities)

# 2. Calculate residual (externally or internally)
# residual = truth_observation - sim_output

# 3. Update impact matrix
# engine.update_impact_matrix(residual, symbol_intensities)

# 4. Apply correction
# correction_amount, corrected_sim = engine.apply_gravity_correction(sim_output, symbol_intensities)

# Get statistics
stats = engine.get_stats()
# health_status = engine.check_health()
```

## 6. Hardcoding Issues

The module generally avoids hardcoding critical parameters by sourcing them from [`config.gravity_config`](../../config/gravity_config.py:1). This includes:
- Default values for all parameters in [`GravityEngineConfig`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:26).
- Thresholds for circuit breakers, weight pruning, fragility detection.
- Parameters for adaptive lambda and shadow model triggers.
- Thresholds used in health checks (e.g., `CRITICAL_MAX_WEIGHT_THRESHOLD`, `UNHEALTHY_RMS_WEIGHT_THRESHOLD`).

Minor, acceptable hardcoding:
- Epsilon value `1e-6` is used in a few places ([`apply_gravity_correction()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:544), [`_calculate_fragility()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:658)) to prevent division by zero, which is a standard numerical stability practice.

## 7. Coupling Points

- **[`config.gravity_config`](../../config/gravity_config.py:1):** Highly coupled. The engine's default behavior and many operational thresholds are directly determined by this configuration module.
- **[`SymbolicPillarSystem`](../../symbolic_system/gravity/symbolic_pillars.py:25) (or equivalent symbol provider):** The engine requires a `symbol_vec` (dictionary of symbol intensities) and an ordered list of `pillar_names` for its core operations.
- **[`symbolic_system.context`](../../symbolic_system/context.py:1):** Depends on `is_symbolic_enabled()` to determine if gravity corrections should be applied.
- **External Simulation/Observation Source:** The engine is designed to process `sim_vec` and `truth_vec`, implying tight coupling with the system(s) that provide these simulation outputs and ground truth observations.
- **Logging Infrastructure ([`utils.log_utils`](../../utils/log_utils.py:1)):** For emitting operational logs.

## 8. Existing Tests

Test file: [`tests/symbolic_system/gravity/test_residual_gravity_engine.py`](../../tests/symbolic_system/gravity/test_residual_gravity_engine.py:1)

- **Current State:** The test suite contains two primary test cases:
    - [`test_residual_gravity_converges_positive_residual()`](../../tests/symbolic_system/gravity/test_residual_gravity_engine.py:5): Verifies convergence with a positive residual.
    - [`test_residual_gravity_converges_negative_residual()`](../../tests/symbolic_system/gravity/test_residual_gravity_engine.py:61): Verifies convergence with a negative residual.
- Both tests focus on the convergence of the `compute_gravity` method after 1000 iterations of `process_and_correct` for a single-dimensional state (`state_dimensionality=1`). They use fixed inputs and assert the final computed gravity value against an expected value. Momentum and EWMA are disabled in these tests for predictability.

- **Coverage & Gaps:**
    - The existing tests cover the basic learning loop and gravity computation for the 1D case.
    - **Significant Gaps:**
        - **Multi-dimensional State:** No tests specifically validate behavior when `state_dimensionality > 1`. The matrix operations and logic differ in this scenario.
        - **Adaptive Lambda:** The adaptive lambda feature ([`_update_adaptive_lambda()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:577)) is not tested as `enable_adaptive_lambda` is `False` in tests.
        - **Weight Pruning:** The [`_prune_weights()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:860) functionality is not explicitly tested.
        - **Circuit Breaker:** The circuit breaker logic within [`apply_gravity_correction()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:451) is untested.
        - **Fragility Calculation:** The [`_calculate_fragility()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:632) mechanism and its influence on `effective_lambda` are not covered.
        - **Shadow Model Trigger:** The logic for the shadow model trigger within [`process_and_correct()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:675) (setting `review_needed_flag`) is not tested.
        - **EWMA Decay:** While disabled for convergence tests, the effect of EWMA decay on the `impact_matrix_B` is not independently verified.
        - **Serialization/Deserialization:** The [`to_dict()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:1116) and [`from_dict()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:1140) methods are not tested.
        - **Diagnostic Methods:** The output and behavior of [`get_stats()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:962) and [`check_health()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:1020) under various conditions (e.g., ensuring specific warnings are generated) are not tested.
        - **Edge Cases:** Testing with empty `symbol_vec`, zero `pillar_names`, or other boundary conditions is missing.

The current tests provide a basic sanity check for convergence in a simplified 1D scenario but do not cover the full range of features or complexities of the module.

## 9. Module Architecture and Flow

1.  **Configuration ([`GravityEngineConfig`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:26)):** A class that holds all tunable parameters, initialized with defaults from `grav_cfg`.
2.  **Engine Initialization ([`ResidualGravityEngine.__init__()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:150)):**
    *   Stores the configuration.
    *   Initializes parameters (lambda, learning rate, regularization, etc.).
    *   Sets up the `impact_matrix_B` (shape: `state_dimensionality` x `num_pillars`) and its momentum buffer `_v_matrix`.
    *   Initializes legacy `weights` and `_v` attributes for 1D backward compatibility.
    *   Prepares data structures (deques) for adaptive lambda and shadow model residuals if those features are enabled.
3.  **Core Processing Cycle (typically driven by [`process_and_correct()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:675)):**
    a.  **Input:** Receives `sim_vec` (simulation output), `truth_vec` (observed reality), and `symbol_vec` (symbol intensities).
    b.  **Calculate Causal Residual:** `residual = truth_vec - sim_vec`.
    c.  **Update Impact Matrix (Learning Step - if `update_weights` is `True`):**
        i.  The [`update_impact_matrix()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:341) method is invoked.
        ii. Converts `symbol_vec` (dict) to an ordered `symbol_array` (numpy array).
        iii.Calculates the gradient for each element/column of `impact_matrix_B` based on the `residual_array`, `symbol_array`, and L2 regularization term.
        iv. Updates the momentum buffer `_v_matrix`.
        v.  Applies the update to `impact_matrix_B` using the learning rate (`η`) and momentum.
        vi. If EWMA is enabled (`ewma_alpha < 1.0`), applies EWMA decay to `impact_matrix_B`.
        vii.Calls [`_update_adaptive_lambda()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:577) to potentially adjust `self.lambda_` based on recent residual magnitudes.
    d.  **Compute Gravity Correction Term (`g_t`):**
        i.  The [`compute_gravity()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:278) method calculates `g_t = impact_matrix_B @ symbol_array`.
    e.  **Apply Correction to Simulation Output:**
        i.  The [`apply_gravity_correction()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:451) method calculates the final `correction_amount = effective_lambda * g_t`.
        ii. `effective_lambda` is derived from `self.lambda_`, potentially reduced by fragility ([`_calculate_fragility()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:632)) and circuit breaker conditions.
        iii.The `correction_amount` is capped by `self.config.max_correction`.
        iv. The `corrected_prediction = sim_vec + correction_amount`.
    f.  **Shadow Model Check (within [`process_and_correct()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:675)):**
        i.  Calculates `gravity_residual = truth_vec - corrected_prediction`.
        ii. Stores recent causal residuals and gravity residuals in deques.
        iii.If sufficient samples are collected, it calculates the variance of causal residuals and gravity residuals.
        iv. Determines the variance explained by the gravity model (`VE_gravity = 1 - (var_gravity_res / var_causal_res)`).
        v.  If `VE_gravity` exceeds `self.config.shadow_model_variance_threshold`, it sets `review_needed_flag = True` and logs a critical message.
4.  **Output:** Returns the `corrected_prediction` and the `review_needed_flag`.
5.  **Diagnostics & Health:** Provides methods like [`get_stats()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:962), [`check_health()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:1020), [`weight_snapshot()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:812), and [`rms_weight()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:834) for monitoring the engine's internal state, performance, and stability.

## 10. Naming Conventions

- **Classes:** `GravityEngineConfig`, `ResidualGravityEngine` follow PascalCase, which is standard and clear.
- **Methods:** Primarily use snake_case (e.g., [`compute_gravity()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:278), [`update_impact_matrix()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:341)). Some aliases exist for backward compatibility (e.g., `gravity` for `compute_gravity`). Internal helper methods are prefixed with an underscore (e.g., [`_dict_to_ordered_array()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:248), [`_prune_weights()`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:860)).
- **Variables & Attributes:**
    - Generally snake_case (e.g., `pillar_names`, `state_dimensionality`, `impact_matrix_B`).
    - Parameters within [`GravityEngineConfig`](../../symbolic_system/gravity/engines/residual_gravity_engine.py:26) use `lambda_` because `lambda` is a Python keyword.
    - Mathematical symbols are used for some attributes where common and documented (e.g., `self.η` for learning rate, `self.β` for momentum factor, `self.reg` for regularization strength).
    - Internal buffers like `_v` (legacy dict) and `_v_matrix` (numpy array), and `_stats` (dict) use a leading underscore.
- **Constants/Defaults:** Configuration defaults are sourced from the `grav_cfg` module (e.g., `grav_cfg.DEFAULT_LAMBDA`), which presumably uses UPPER_SNAKE_CASE.
- **PEP 8 Adherence:** The code generally adheres to PEP 8 guidelines. Some lines, particularly in docstrings or complex calculations, might exceed the typical length but are usually clear.
