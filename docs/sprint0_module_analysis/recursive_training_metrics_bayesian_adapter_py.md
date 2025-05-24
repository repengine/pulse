# Module Analysis: `recursive_training/metrics/bayesian_adapter.py`

## 1. Module Intent/Purpose

The module [`recursive_training/metrics/bayesian_adapter.py`](../../recursive_training/metrics/bayesian_adapter.py:1) serves as an adapter to integrate metrics from the recursive training process with Pulse's Bayesian trust system. Its core responsibilities include:

*   Translating performance metrics (e.g., error rates, cost) into trust scores.
*   Updating the Pulse trust system (if available) or a fallback mechanism with these scores.
*   Retrieving current trust scores and historical trust data for entities (e.g., rules, models).
*   Calculating confidence in trust scores.
*   Managing trust decay over time.
*   Providing a list of entities that meet specified trust and confidence thresholds.

It aims to provide a bidirectional communication channel between training performance and the system's trust assessment of its components.

## 2. Operational Status/Completeness

The module appears largely complete for its defined scope.
*   It implements core functionalities for trust calculation, update, retrieval, history, confidence, and decay.
*   It includes a [`FallbackTrustTracker`](../../recursive_training/metrics/bayesian_adapter.py:509) class, ensuring basic operation even if the primary `core.bayesian_trust_tracker` is not available. This fallback provides resilience.
*   Methods are generally well-documented with docstrings explaining their purpose, arguments, and return values.
*   Configuration parameters are handled via an optional `config` dictionary, allowing for some flexibility.

Notable points:
*   There is a duplicate docstring for the [`BayesianAdapter`](../../recursive_training/metrics/bayesian_adapter.py:33) class (lines 34-44 and 45-55). This should be consolidated.
*   No explicit "TODO" comments or major obvious placeholders for core logic were observed.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Hybrid Rules Evaluation:** The feature list in the docstring mentions "Support hybrid rules evaluation" ([`BayesianAdapter`](../../recursive_training/metrics/bayesian_adapter.py:43), [`BayesianAdapter`](../../recursive_training/metrics/bayesian_adapter.py:54)). However, there's no direct implementation or further detail on this within the module. This might be an intended future extension or handled by other components that use this adapter.
*   **Trust Tracker Interface Assumption:** The adapter assumes the `core.bayesian_trust_tracker` (if available) has methods like `get_trust`, `update_trust`, and `set_trust`. The use of `cast(Any, ...)` and `hasattr` ([`recursive_training/metrics/bayesian_adapter.py:98`](../../recursive_training/metrics/bayesian_adapter.py:98), [`recursive_training/metrics/bayesian_adapter.py:134`](../../recursive_training/metrics/bayesian_adapter.py:134)) provides some flexibility, but a more formally defined interface would be beneficial. If the actual trust tracker deviates significantly, the adapter might not function as intended with it.
*   **Efficiency of `decay_trust_over_time`:** The [`decay_trust_over_time`](../../recursive_training/metrics/bayesian_adapter.py:438) method queries all "trust_update" metrics from the `metrics_store` to find the latest update for each entity. For systems with many entities or extensive history, this could become inefficient. A more optimized approach might involve the trust tracker managing decay internally or the `metrics_store` providing a more direct way to query the latest update per entity.
*   **Error Metric Prioritization:** The `_calculate_performance_score` method has a fixed prioritization for error metrics (RMSE > MSE > MAE) ([`recursive_training/metrics/bayesian_adapter.py:227-233`](../../recursive_training/metrics/bayesian_adapter.py:227-233)). This might not be optimal for all scenarios and could be made more configurable.

## 4. Connections & Dependencies

*   **Direct Project Module Imports:**
    *   `core.bayesian_trust_tracker` ([`recursive_training/metrics/bayesian_adapter.py:19`](../../recursive_training/metrics/bayesian_adapter.py:19)): Optional import for the main Pulse trust system. The adapter is designed to function with or without it.
    *   `recursive_training.metrics.metrics_store.get_metrics_store` ([`recursive_training/metrics/bayesian_adapter.py:30`](../../recursive_training/metrics/bayesian_adapter.py:30)): Used to obtain an instance of the metrics store for persisting trust update history.
*   **External Library Dependencies:**
    *   `logging` ([`recursive_training/metrics/bayesian_adapter.py:9`](../../recursive_training/metrics/bayesian_adapter.py:9)): Standard Python logging.
    *   `json` ([`recursive_training/metrics/bayesian_adapter.py:10`](../../recursive_training/metrics/bayesian_adapter.py:10)): Standard Python JSON library (imported but not directly used in the visible code, possibly for config or future use).
    *   `datetime` (from `datetime` import `datetime`, `timezone`) ([`recursive_training/metrics/bayesian_adapter.py:11`](../../recursive_training/metrics/bayesian_adapter.py:11)): For timestamping trust updates.
    *   `typing` (various types) ([`recursive_training/metrics/bayesian_adapter.py:12`](../../recursive_training/metrics/bayesian_adapter.py:12), [`recursive_training/metrics/bayesian_adapter.py:15`](../../recursive_training/metrics/bayesian_adapter.py:15)): For type hinting.
*   **Interaction via Shared Data:**
    *   The module interacts with the `core.bayesian_trust_tracker` by invoking its methods if available.
    *   It uses the `metrics_store` to persist and query trust-related metrics, implying a shared data store (e.g., database, file system) managed by `metrics_store`.
*   **Input/Output Files:**
    *   **Logs:** Generates logs via the `logging` module.
    *   **Metrics Data:** Indirectly interacts with data files or databases via the `metrics_store`. The specifics of this storage are abstracted by the store.

## 5. Function and Class Example Usages

### `BayesianAdapter` Class

```python
from recursive_training.metrics.bayesian_adapter import BayesianAdapter

# Configuration for the adapter (optional)
adapter_config = {
    "error_weight": 0.6, 
    "cost_weight": 0.4, 
    "max_error": 10.0,  # Expected maximum error for normalization
    "max_cost": 1.0,    # Expected maximum cost for normalization
    "min_confidence": 0.1,
    "max_confidence": 0.9,
    "trust_decay_rate": 0.02, # Daily decay rate
    "max_history_per_entity": 50 
}

# Initialize the adapter
adapter = BayesianAdapter(config=adapter_config)

# --- Update trust for an entity ---
entity_id_model_A = "model_alpha_v1.2"
model_A_metrics = {"rmse": 1.5, "cost": 0.05, "accuracy": 0.85} # Example metrics
update_weight = 0.7 # How much this new evidence should influence the trust

updated_trust_A = adapter.update_trust_from_metrics(
    entity_id_model_A, 
    model_A_metrics, 
    weight=update_weight,
    tags=["experiment_X", "validation_set"]
)
print(f"Updated trust for {entity_id_model_A}: {updated_trust_A:.4f}")

# --- Get current trust score ---
current_trust_A = adapter.get_trust_score(entity_id_model_A)
print(f"Current trust for {entity_id_model_A}: {current_trust_A:.4f}")

# --- Get trust history ---
history_A = adapter.get_trust_history(entity_id_model_A, limit=5)
print(f"\nTrust history for {entity_id_model_A} (last 5):")
for record in history_A:
    print(f"  Timestamp: {record['timestamp']}, Trust: {record['updated_trust']:.4f}, Perf Score: {record['performance_score']:.4f}")

# --- Calculate confidence ---
confidence_A = adapter.calculate_confidence(entity_id_model_A)
print(f"\nConfidence in trust for {entity_id_model_A}: {confidence_A:.4f}")

# --- Get trusted entities ---
# First, let's add another entity
entity_id_rule_B = "rule_beta_processor"
rule_B_metrics = {"accuracy": 0.95, "cost": 0.01}
adapter.update_trust_from_metrics(entity_id_rule_B, rule_B_metrics, weight=0.9)

trusted_entities_list = adapter.get_trusted_entities(threshold=0.8, confidence_threshold=0.5)
print("\nHighly trusted entities (Trust > 0.8, Confidence > 0.5):")
for entity_info in trusted_entities_list:
    print(f"  ID: {entity_info['entity_id']}, Trust: {entity_info['trust_score']:.4f}, Confidence: {entity_info['confidence']:.4f}")

# --- Decay trust over time (simulate this being called periodically) ---
# Note: This would typically be called by a scheduler.
# For this example, we'll assume some time has passed and call it.
# If no updates happened for a while, scores might decay.
# decayed_scores = adapter.decay_trust_over_time()
# print("\nTrust scores after potential decay:")
# for entity, score in decayed_scores.items():
#     print(f"  {entity}: {score:.4f}")
```

### `FallbackTrustTracker` Class

This class is primarily for internal use by [`BayesianAdapter`](../../recursive_training/metrics/bayesian_adapter.py:33) when `core.bayesian_trust_tracker` is unavailable. Direct instantiation and use by external client code is unlikely.

## 6. Hardcoding Issues

Several default values and magic numbers are present, mostly as fallbacks if not provided in the configuration or as fixed parameters in calculations:

*   **Configuration Defaults in `__init__`:**
    *   `error_weight`: `0.7` ([`recursive_training/metrics/bayesian_adapter.py:77`](../../recursive_training/metrics/bayesian_adapter.py:77))
    *   `cost_weight`: `0.3` ([`recursive_training/metrics/bayesian_adapter.py:78`](../../recursive_training/metrics/bayesian_adapter.py:78))
    *   `min_confidence`: `0.1` ([`recursive_training/metrics/bayesian_adapter.py:79`](../../recursive_training/metrics/bayesian_adapter.py:79))
    *   `max_confidence`: `0.9` ([`recursive_training/metrics/bayesian_adapter.py:80`](../../recursive_training/metrics/bayesian_adapter.py:80))
    *   `trust_decay_rate`: `0.05` ([`recursive_training/metrics/bayesian_adapter.py:81`](../../recursive_training/metrics/bayesian_adapter.py:81))
*   **`_calculate_performance_score` Defaults:**
    *   `max_error`: `10.0` ([`recursive_training/metrics/bayesian_adapter.py:236`](../../recursive_training/metrics/bayesian_adapter.py:236))
    *   `max_cost`: `1.0` ([`recursive_training/metrics/bayesian_adapter.py:247`](../../recursive_training/metrics/bayesian_adapter.py:247))
    *   Initial `error_score` and `cost_score`: `0.5` ([`recursive_training/metrics/bayesian_adapter.py:222-223`](../../recursive_training/metrics/bayesian_adapter.py:222-223))
*   **`_record_trust_update` Defaults:**
    *   `max_history_per_entity`: `100` ([`recursive_training/metrics/bayesian_adapter.py:289`](../../recursive_training/metrics/bayesian_adapter.py:289))
    *   `metric_type` string: `"trust_update"` ([`recursive_training/metrics/bayesian_adapter.py:296`](../../recursive_training/metrics/bayesian_adapter.py:296))
*   **`calculate_confidence` Magic Numbers:**
    *   History length scaling factor: `10` (in `len(history) / 10`) ([`recursive_training/metrics/bayesian_adapter.py:375`](../../recursive_training/metrics/bayesian_adapter.py:375))
    *   Number of history records for variance: `5` (in `history[:5]`) ([`recursive_training/metrics/bayesian_adapter.py:379`](../../recursive_training/metrics/bayesian_adapter.py:379))
    *   Variance scaling factor: `4` (in `variance * 4`) ([`recursive_training/metrics/bayesian_adapter.py:381`](../../recursive_training/metrics/bayesian_adapter.py:381))
    *   Default `consistency_confidence`: `0.5` ([`recursive_training/metrics/bayesian_adapter.py:383`](../../recursive_training/metrics/bayesian_adapter.py:383))
    *   Weights for combining history and consistency confidence: `0.6` and `0.4` ([`recursive_training/metrics/bayesian_adapter.py:386`](../../recursive_training/metrics/bayesian_adapter.py:386))
*   **Default Trust Score:** A neutral trust score of `0.5` is used as a default or fallback in multiple places (e.g., [`get_trust_score`](../../recursive_training/metrics/bayesian_adapter.py:103), [`FallbackTrustTracker.get_trust`](../../recursive_training/metrics/bayesian_adapter.py:529)).
*   **Batch Update Tag:** The tag `"batch_update"` is hardcoded in [`batch_update_trust`](../../recursive_training/metrics/bayesian_adapter.py:327).
*   **Decay Target:** Trust decay moves towards `0.5` ([`recursive_training/metrics/bayesian_adapter.py:484-487`](../../recursive_training/metrics/bayesian_adapter.py:484-487)).

While many of these are configurable or serve as reasonable defaults, centralizing them (e.g., in a configuration schema or constants module) could improve maintainability.

## 7. Coupling Points

*   **`core.bayesian_trust_tracker`:** This is the most significant external coupling point. The adapter's primary mode of operation relies on the presence and specific API (method names like `get_trust`, `update_trust`, `set_trust`) of this module. The fallback mechanism mitigates this, but full functionality depends on the main tracker.
*   **`recursive_training.metrics.metrics_store`:** The adapter is tightly coupled with the `metrics_store` for persisting and retrieving trust update history. The structure of the data stored (e.g., `metric_type="trust_update"`, specific keys in the metric dictionary) creates a dependency.
*   **Configuration Dictionary Structure:** The behavior of the adapter (e.g., weights, thresholds, normalization parameters) is heavily influenced by the structure and keys expected in the `config` dictionary passed during initialization.
*   **Metric Names:** The `_calculate_performance_score` method specifically looks for metric keys like `"mse"`, `"rmse"`, `"mae"`, `"accuracy"`, and `"cost"` ([`recursive_training/metrics/bayesian_adapter.py:226-248`](../../recursive_training/metrics/bayesian_adapter.py:226-248)). Changes to these metric names in the input data would require updates to the adapter.

## 8. Existing Tests

Based on the provided file list in the environment details, there is **no specific test file** named `test_bayesian_adapter.py` within the `tests/recursive_training/metrics/` directory.
While related modules like `metrics_store` might have tests (`tests/recursive_training/test_metrics_store.py`), this indicates a potential gap in dedicated unit tests for the `BayesianAdapter` class itself.
Such tests would be crucial for verifying:
*   Correct performance score calculation from various metrics.
*   Proper interaction with both the (mocked) `core.bayesian_trust_tracker` and the `FallbackTrustTracker`.
*   Accuracy of trust history recording and retrieval.
*   Correctness of confidence calculation logic.
*   Functionality of trust decay.
*   Behavior with different configurations.

## 9. Module Architecture and Flow

The module is structured around two main classes:

1.  **`BayesianAdapter`:**
    *   **Initialization (`__init__`)**:
        *   Sets up logging.
        *   Stores the provided configuration.
        *   Initializes `metrics_store`.
        *   Checks for `core.bayesian_trust_tracker`; if not found, uses `FallbackTrustTracker`.
        *   Loads various weighting and threshold parameters from the configuration or uses defaults.
        *   Initializes an in-memory `trust_history` dictionary.
    *   **Core Logic**:
        *   [`update_trust_from_metrics`](../../recursive_training/metrics/bayesian_adapter.py:109):
            1.  Calculates a normalized `performance_score` from input `metrics` using [`_calculate_performance_score`](../../recursive_training/metrics/bayesian_adapter.py:211). This involves weighting error/accuracy and cost components.
            2.  Retrieves the `prior_trust` using [`get_trust_score`](../../recursive_training/metrics/bayesian_adapter.py:86).
            3.  Attempts to update trust in the `self.trust_tracker` (either Pulse's or fallback) using its `update_trust` method. If that fails or the method is absent, it uses [`_fallback_update_trust`](../../recursive_training/metrics/bayesian_adapter.py:178) (a simple weighted average).
            4.  Records the update (prior trust, new trust, performance score, metrics, tags) to `self.trust_history` and the `metrics_store` via [`_record_trust_update`](../../recursive_training/metrics/bayesian_adapter.py:256).
        *   [`get_trust_score`](../../recursive_training/metrics/bayesian_adapter.py:86): Retrieves the current trust score from `self.trust_tracker`.
        *   [`calculate_confidence`](../../recursive_training/metrics/bayesian_adapter.py:356): Calculates confidence based on the amount and consistency of trust history.
        *   [`decay_trust_over_time`](../../recursive_training/metrics/bayesian_adapter.py:438): Queries `metrics_store` for the latest updates, calculates decay for entities not updated recently, and updates their scores in `self.trust_tracker`.
        *   Other methods provide batch updates, history retrieval, and lists of trusted entities.

2.  **`FallbackTrustTracker`:**
    *   A simple, self-contained class that maintains trust scores in an in-memory dictionary.
    *   Provides `get_trust`, `set_trust`, and `update_trust` methods, mimicking a basic trust tracker interface.

**Primary Data Flow for Trust Update:**
`Input Metrics` -> `_calculate_performance_score` -> `Normalized Performance Score` -> `trust_tracker.update_trust` (or fallback) -> `Updated Trust Score` -> `_record_trust_update` -> (`self.trust_history` & `metrics_store`).

## 10. Naming Conventions

*   **Classes:** `BayesianAdapter`, `FallbackTrustTracker` follow PascalCase, which is standard (PEP 8).
*   **Methods:** Generally use snake_case (e.g., `get_trust_score`, `_calculate_performance_score`), with leading underscores for "protected" helper methods. This is consistent with PEP 8.
*   **Variables:** Local variables and attributes also use snake_case (e.g., `entity_id`, `error_weight`).
*   **Constants:** `TRUST_TRACKER_AVAILABLE` is in UPPER_SNAKE_CASE, which is correct.
*   **Type Hinting:** The module uses type hints from the `typing` module. A `TypeVar` (`TrustTrackerType`) is defined but `self.trust_tracker` is ultimately typed as `Any` after `cast`. This could potentially be refined if a more formal interface for the trust tracker were available for type hinting.
*   **Docstrings:** Generally good, though the `BayesianAdapter` class has a duplicated docstring section.

Overall, naming conventions are clear, descriptive, and largely adhere to Python community standards (PEP 8). No significant deviations or potential AI assumption errors in naming were noted beyond the duplicated docstring.