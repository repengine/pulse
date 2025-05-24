# Module Analysis: recursive_training.metrics.bayesian_adapter

## 1. Module Path

[`recursive_training/metrics/bayesian_adapter.py`](recursive_training/metrics/bayesian_adapter.py:1)

## 2. Purpose & Functionality

The `bayesian_adapter.py` module serves as a crucial bridge between the metrics generated during recursive training and Pulse's core Bayesian trust system, nominally located at [`core/bayesian_trust_tracker.py`](core/bayesian_trust_tracker.py:1). Its primary purpose is to interpret various performance metrics and translate them into quantifiable trust scores for different entities within the Pulse system, such as rules or models.

Key functionalities include:

*   **Trust Score Calculation:** Converts performance metrics (e.g., MSE, RMSE, MAE, accuracy, computational cost) into a normalized trust score.
*   **Trust System Integration:** Updates Pulse's central Bayesian trust tracker with these calculated trust scores. If the primary trust tracker is unavailable, it gracefully falls back to an internal, simpler trust mechanism.
*   **Trust Data Retrieval:** Allows querying for current trust scores and historical trust evolution for specific entities.
*   **Confidence Assessment:** Calculates a confidence level for the trust scores based on the volume and consistency of historical data.
*   **Threshold-based Entity Identification:** Identifies entities that meet or exceed specified trust and confidence thresholds.
*   **Batch Operations:** Supports updating trust scores for multiple entities simultaneously.
*   **Trust Decay:** Implements a time-based decay mechanism for trust scores of entities that have not been recently updated, gradually moving them towards a neutral value.
*   **Fallback Mechanism:** Includes a `FallbackTrustTracker` class to ensure continued operation, albeit with a simpler model, if the main [`core.bayesian_trust_tracker`](core/bayesian_trust_tracker.py:1) module is not accessible.

This module plays a vital role in the `recursive_training/metrics/` subdirectory by providing the means to dynamically assess and quantify the reliability and performance of various components as the system learns and evolves. Within the broader Pulse application, it underpins the mechanisms for adaptive decision-making and self-improvement by maintaining a dynamic understanding of component trustworthiness.

## 3. Key Components / Classes / Functions

### Class: `BayesianAdapter`

This is the main class of the module.

*   **[`__init__(self, config: Optional[Dict[str, Any]] = None)`](recursive_training/metrics/bayesian_adapter.py:57):**
    *   Initializes the adapter.
    *   Sets up logging.
    *   Loads configuration (e.g., weights for error/cost in trust calculation, confidence limits, decay rates).
    *   Initializes a connection to the [`MetricsStore`](recursive_training/metrics/metrics_store.py:1).
    *   Attempts to connect to Pulse's [`bayesian_trust_tracker`](core/bayesian_trust_tracker.py:1); uses [`FallbackTrustTracker`](recursive_training/metrics/bayesian_adapter.py:509) if unavailable.
*   **[`get_trust_score(self, entity_id: str) -> float`](recursive_training/metrics/bayesian_adapter.py:86):**
    *   Retrieves the current trust score for a specified `entity_id`.
*   **[`update_trust_from_metrics(self, entity_id: str, metrics: Dict[str, float], weight: float = 1.0, tags: Optional[List[str]] = None) -> float`](recursive_training/metrics/bayesian_adapter.py:109):**
    *   Calculates a performance score from the provided `metrics`.
    *   Updates the trust score for the `entity_id` in the trust system.
    *   Records the trust update.
*   **[`_fallback_update_trust(self, entity_id: str, prior_trust: float, performance_score: float, weight: float) -> float`](recursive_training/metrics/bayesian_adapter.py:178):**
    *   A private method providing a simplified trust update (weighted average) if the primary trust system's update mechanism fails or is unavailable.
*   **[`_calculate_performance_score(self, metrics: Dict[str, float]) -> float`](recursive_training/metrics/bayesian_adapter.py:211):**
    *   A private method that converts a dictionary of raw performance metrics (e.g., `mse`, `accuracy`, `cost`) into a single normalized performance score (0.0-1.0).
*   **[`_record_trust_update(self, entity_id: str, prior_trust: float, updated_trust: float, performance_score: float, metrics: Dict[str, float], tags: Optional[List[str]] = None) -> None`](recursive_training/metrics/bayesian_adapter.py:256):**
    *   A private method to log the details of a trust update, including timestamp, prior/updated trust, performance score, and original metrics, to both an internal history and the [`MetricsStore`](recursive_training/metrics/metrics_store.py:1).
*   **[`batch_update_trust(self, metrics_by_entity: Dict[str, Dict[str, float]], weight: float = 1.0) -> Dict[str, float]`](recursive_training/metrics/bayesian_adapter.py:307):**
    *   Updates trust scores for multiple entities based on their respective metrics.
*   **[`get_trust_history(self, entity_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]`](recursive_training/metrics/bayesian_adapter.py:333):**
    *   Retrieves the historical record of trust updates for a given `entity_id`.
*   **[`calculate_confidence(self, entity_id: str, default_confidence: float = 0.5) -> float`](recursive_training/metrics/bayesian_adapter.py:356):**
    *   Calculates a confidence score for an entity's trust score, based on the amount and consistency of its trust history.
*   **[`get_trusted_entities(self, threshold: float = 0.7, confidence_threshold: float = 0.5, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]`](recursive_training/metrics/bayesian_adapter.py:391):**
    *   Queries the [`MetricsStore`](recursive_training/metrics/metrics_store.py:1) and current trust states to return a list of entities that meet specified trust and confidence thresholds.
*   **[`decay_trust_over_time(self, decay_factor: Optional[float] = None) -> Dict[str, float]`](recursive_training/metrics/bayesian_adapter.py:438):**
    *   Applies a time-based decay to trust scores for entities that haven't been updated recently, nudging their trust towards a neutral 0.5.

### Class: `FallbackTrustTracker`

A simple, self-contained trust tracker used if [`core.bayesian_trust_tracker`](core/bayesian_trust_tracker.py:1) is not available.

*   **[`__init__(self)`](recursive_training/metrics/bayesian_adapter.py:514):** Initializes an in-memory dictionary to store trust scores.
*   **[`get_trust(self, entity_id: str) -> float`](recursive_training/metrics/bayesian_adapter.py:519):** Returns the trust score for an entity, defaulting to 0.5.
*   **[`set_trust(self, entity_id: str, trust_score: float) -> None`](recursive_training/metrics/bayesian_adapter.py:531):** Sets the trust score for an entity, clamping it between 0.0 and 1.0.
*   **[`update_trust(self, entity_id: str, evidence: float, weight: float = 1.0) -> float`](recursive_training/metrics/bayesian_adapter.py:541):** Updates an entity's trust score using a simple weighted average with new evidence.

## 4. Dependencies

### Internal Pulse Modules:

*   [`core.bayesian_trust_tracker`](core/bayesian_trust_tracker.py:1): This is an optional dependency. The adapter attempts to import `bayesian_trust_tracker` from this module. If the import fails, it uses its internal `FallbackTrustTracker`.
*   [`recursive_training.metrics.metrics_store`](recursive_training/metrics/metrics_store.py:1): Specifically, the `get_metrics_store` function is used to obtain an instance of the metrics store for recording trust updates.

### External Libraries:

*   `logging`: For standard Python logging.
*   `json`: (Not directly used in the provided snippet, but often relevant for config or data handling).
*   `datetime`: For timestamping trust updates and calculating time differences for decay.
*   `typing`: For type hinting (`Any`, `Dict`, `List`, `Optional`, `Union`, `Tuple`, `Set`, `Callable`, `TypeVar`, `cast`).

## 5. SPARC Analysis

*   **Specification:**
    *   **Clarity of Purpose:** The module's purpose is clearly defined in its docstring: to adapt recursive training metrics for Pulse's Bayesian trust system.
    *   **Well-Defined Requirements:** The functionalities (translating metrics, updating trust, retrieving scores, handling history, confidence, decay) suggest a well-understood set of requirements for integrating metrics with a trust evaluation framework.

*   **Architecture & Modularity:**
    *   **Well-Structured:** The module is organized around the `BayesianAdapter` class, which encapsulates all primary logic. The `FallbackTrustTracker` class provides a clean separation for the alternative mechanism.
    *   **Clear Responsibilities:** The `BayesianAdapter` is responsible for all aspects of interaction between metrics and the trust system. The `FallbackTrustTracker` has the sole responsibility of providing a basic trust store if the main one is absent.
    *   **Modularity:** The design promotes modularity. The adapter can operate with or without the main `bayesian_trust_tracker`, and its dependency on `metrics_store` is through an accessor function, allowing flexibility.

*   **Refinement - Testability:**
    *   **Existing Tests:** No tests are present within this file. Unit tests would typically be in a parallel `tests` directory (e.g., `tests/recursive_training/test_bayesian_adapter.py`).
    *   **Design for Testability:** The module is generally well-designed for testability:
        *   Dependencies (like `config`, `metrics_store`, and `bayesian_trust_tracker`) are either injected or handled in a way that allows for mocking (e.g., the fallback mechanism for the trust tracker).
        *   Methods have clear inputs and outputs.
        *   Configuration-driven behavior allows for testing different scenarios by varying the input `config`.

*   **Refinement - Maintainability:**
    *   **Clarity & Readability:** The code is generally clear, with descriptive variable and method names.
    *   **Documentation:** Docstrings are provided for the module, classes, and most public/important methods, explaining their purpose, arguments, and return values. The class docstring for `BayesianAdapter` (lines 34-44) is duplicated (lines 45-55) and should be removed.
    *   **Type Hinting:** Extensive use of type hints significantly improves readability and helps in understanding data structures and function signatures.
    *   **Logging:** Logging is used to report warnings (e.g., trust tracker unavailability) and errors, aiding in debugging and monitoring.
    *   **`cast(Any, ...)` Usage:** The use of `cast(Any, self.trust_tracker)` followed by `hasattr` checks (e.g., in [`get_trust_score()`](recursive_training/metrics/bayesian_adapter.py:98:99) and [`update_trust_from_metrics()`](recursive_training/metrics/bayesian_adapter.py:134:137)) to interact with the trust tracker suggests a lack of a formal interface or protocol. This can make static analysis harder and is a potential point of brittleness if the tracker's API changes unexpectedly.

*   **Refinement - Security:**
    *   **Obvious Concerns:** No direct security vulnerabilities (like SQL injection, path traversal, or command injection) are apparent. The module primarily processes internal data (metrics) and interacts with other internal systems.
    *   **Data Handling:** It handles configuration data, but there's no indication of sensitive information like passwords or API keys being processed directly by this module in an insecure way.

*   **Refinement - No Hardcoding:**
    *   **Configuration Parameters:** Many operational parameters (e.g., `error_weight`, `cost_weight`, `min_confidence`, `max_confidence`, `trust_decay_rate`, `max_error`, `max_cost`, `max_history_per_entity`) are configurable via the `config` dictionary passed during initialization, with sensible defaults provided. This is good practice.
    *   **Potential Minor Hardcoding:**
        *   In [`_calculate_performance_score()`](recursive_training/metrics/bayesian_adapter.py:211), the preference order for error metrics (RMSE then MSE then MAE) is hardcoded.
        *   In [`calculate_confidence()`](recursive_training/metrics/bayesian_adapter.py:356), the scaling factors (e.g., `len(history) / 10`, `variance * 4`) are hardcoded. While these might be empirically derived, making them named constants or configurable could improve clarity and tunability.

## 6. Identified Gaps & Areas for Improvement

*   **Formal Trust Tracker Interface:**
    *   **Issue:** The current approach uses `cast(Any, ...)` and `hasattr` to interact with the `bayesian_trust_tracker` and `FallbackTrustTracker`. This bypasses static type checking for these interactions.
    *   **Recommendation:** Define a formal `Protocol` or Abstract Base Class (ABC) that both [`core.bayesian_trust_tracker.BayesianTrustTracker`](core/bayesian_trust_tracker.py:1) (assuming its structure) and [`FallbackTrustTracker`](recursive_training/metrics/bayesian_adapter.py:509) would implement. This would provide type safety and clearer contracts.
*   **Configuration of Calculation Logic:**
    *   **Issue:** Some logic within [`_calculate_performance_score()`](recursive_training/metrics/bayesian_adapter.py:211) (e.g., error metric preference, `max_error`, `max_cost`) and [`calculate_confidence()`](recursive_training/metrics/bayesian_adapter.py:356) (magic numbers for scaling) is hardcoded or uses fixed defaults.
    *   **Recommendation:** Expose more of these parameters through the configuration dictionary for greater flexibility and easier tuning without code changes.
*   **Docstring Duplication:**
    *   **Issue:** The class docstring for `BayesianAdapter` is duplicated (lines 34-44 and 45-55).
    *   **Recommendation:** Remove the duplicate block.
*   **Timestamp Parsing Robustness:**
    *   **Issue:** In [`decay_trust_over_time()`](recursive_training/metrics/bayesian_adapter.py:467), `timestamp_str.replace('Z', '+00:00')` is used before `datetime.fromisoformat`.
    *   **Recommendation:** Ensure that `datetime.fromisoformat` can robustly handle all expected timestamp formats from the `metrics_store`. If formats vary, more sophisticated parsing might be needed. The current approach is common but assumes a specific 'Z' suffix for UTC.
*   **Completeness of `FallbackTrustTracker` Docstrings:**
    *   **Issue:** While the `FallbackTrustTracker` class has a docstring, its methods ([`get_trust()`](recursive_training/metrics/bayesian_adapter.py:519), [`set_trust()`](recursive_training/metrics/bayesian_adapter.py:531), [`update_trust()`](recursive_training/metrics/bayesian_adapter.py:541)) lack them.
    *   **Recommendation:** Add brief docstrings to these methods for consistency and completeness, even if their functionality is straightforward.

## 7. Overall Assessment & Next Steps

**Overall Assessment:**

The [`recursive_training/metrics/bayesian_adapter.py`](recursive_training/metrics/bayesian_adapter.py:1) module is a well-developed and crucial component for enabling adaptive trust within the Pulse system. It demonstrates good design principles by being configurable, providing a fallback mechanism for a core dependency, and including logging and type hinting. The logic for translating metrics into trust and confidence scores, along with features like batch updates and trust decay, provides a comprehensive toolkit for managing trust dynamically.

The quality of the code is generally high, with clear structure and comments. The identified areas for improvement are mostly refinements that would enhance robustness, maintainability, and configurability rather than indicating fundamental flaws.

**Next Steps:**

1.  **Implement Formal Trust Tracker Interface:** Define a `Protocol` or ABC for trust trackers and refactor `BayesianAdapter` to use it, removing `cast(Any, ...)` and `hasattr` checks.
2.  **Enhance Configurability:** Make the performance score calculation logic (metric preferences, scaling factors) and confidence calculation parameters more configurable.
3.  **Address Minor Cleanups:** Remove the duplicated docstring in `BayesianAdapter`. Add missing docstrings to `FallbackTrustTracker` methods.
4.  **Review Timestamp Handling:** Confirm the robustness of timestamp parsing in [`decay_trust_over_time()`](recursive_training/metrics/bayesian_adapter.py:438) against actual data from the `metrics_store`.
5.  **Ensure Comprehensive Testing:** Verify or create thorough unit tests for all functionalities of `BayesianAdapter`, including scenarios with the primary trust tracker and the `FallbackTrustTracker`, various metric inputs, and edge cases for confidence and decay calculations.