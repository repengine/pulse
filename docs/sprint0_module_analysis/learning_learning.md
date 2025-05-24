# Module Analysis: learning/learning.py

## SPARC Sprint 0 Analysis Report

**Module Path:** [`learning/learning.py`](learning/learning.py:1)
**Analysis Date:** 2025-05-13

### 1. Module Intent/Purpose (SPARC: Specification)

The [`learning/learning.py`](learning/learning.py:1) module serves as the core "Pulse Meta-Learning Engine". Its primary purpose is to evolve symbolic overlays, variable trust scores, and system memory. It achieves this by analyzing simulation lineage, forecast regret, and symbolic divergence, integrating data from various sources like trace memory, variable performance logs, symbolic arc analyzers, and trust/PFPA deltas.

### 2. Operational Status/Completeness

The module is partially implemented, containing several placeholder classes:
*   [`AnomalyRemediationEngine`](learning/learning.py:51)
*   [`FeatureDiscoveryEngine`](learning/learning.py:54)
*   [`AuditReportingEngine`](learning/learning.py:57)
*   [`CausalInferenceEngine`](learning/learning.py:60)
*   [`ContinuousLearningEngine`](learning/learning.py:63)
*   [`ExternalIntegrationEngine`](learning/learning.py:66)
*   [`ActiveExperimentationEngine`](learning/learning.py:69)

The `LearningEngine.run_meta_update()` method is commented out with a `# Implement as needed` note, indicating a significant piece of core functionality is missing.

### 3. Implementation Gaps / Unfinished Next Steps

*   Implementation of the placeholder engine classes is required.
*   The core meta-update logic within `LearningEngine.run_meta_update()` needs to be defined and implemented.
*   Error handling in several functions (e.g., `integrate_external_data`, `analyze_trust_patterns`, `analyze_symbolic_correlation`, `explain_forecast_with_shap`, `update_variable_weights`, `apply_variable_mutation_pressure`, `apply_rule_mutation_pressure`, `compute_retrodiction_error`, `retrodict_error_score`) is basic (`try...except Exception`) and should be refined to catch specific exceptions and provide more informative logging or error handling.
*   The logic for concept drift detection and semi-supervised blending in `integrate_external_data` appears experimental and may require further development and validation.
*   The use of `print` statements for logging (e.g., lines 295, 306, 309, 316, 319, 323, 324, 326, 340, 343, 347, 348, 350, 352, 358, 361) should be replaced with the configured `logging` module for consistent output management.

### 4. Connections & Dependencies

*   **Direct Imports:**
    *   Standard Libraries: `logging`, `typing`, `datetime`, `math`, `datetime.timezone`
    *   External Libraries (conditionally imported): `statsmodels.api` (sm), `shap`, `sklearn.feature_selection.mutual_info_regression`, `networkx` (nx), `pandas` (pd)
    *   Internal Modules:
        *   [`memory.trace_memory`](memory/trace_memory.py:1)
        *   [`memory.variable_performance_tracker`](memory/variable_performance_tracker.py:1)
        *   [`core.variable_registry`](core/variable_registry.py:1)
        *   [`core.bayesian_trust_tracker`](core/bayesian_trust_tracker.py:1)
        *   [`core.optimized_trust_tracker`](core/optimized_bayesian_trust_tracker.py:1)
        *   [`learning.output_data_reader`](learning/output_data_reader.py:1)
        *   [`trust_system.trust_engine`](trust_system/trust_engine.py:1)
        *   [`simulation_engine.rule_mutation_engine`](simulation_engine/rule_mutation_engine.py:1)
        *   [`memory.variable_cluster_engine`](memory/variable_cluster_engine.py:1)
        *   [`memory.rule_cluster_engine`](memory/rule_cluster_engine.py:1)
        *   [`symbolic_system.symbolic_contradiction_cluster`](symbolic_system/symbolic_contradiction_cluster.py:1)
        *   [`core.pulse_learning_log`](core/pulse_learning_log.py:1)
        *   [`operator_interface.rule_cluster_digest_formatter`](operator_interface/rule_cluster_digest_formatter.py:1)
        *   [`operator_interface.variable_cluster_digest_formatter`](operator_interface/variable_cluster_digest_formatter.py:1)
        *   [`operator_interface.mutation_digest_exporter`](operator_interface/mutation_digest_exporter.py:1)
        *   [`operator_interface.symbolic_contradiction_digest`](operator_interface/symbolic_contradiction_digest.py:1)
*   **Interactions:** The module interacts heavily with memory components (`TraceMemory`, `VariablePerformanceTracker`), core components (`VariableRegistry`, `BayesianTrustTracker`), trust system, simulation engine, symbolic system, and operator interface for logging and reporting. It also interacts with the filesystem for reading input data and writing logs/digests.
*   **Input/Output Files:**
    *   Reads from: `"logs/retrodiction_result_log.jsonl"` (hardcoded path)
    *   Reads from: Data files via `OutputDataReader` (default path `"data/outputs"`, hardcoded)
    *   Writes to: `"logs/learning_summary_with_digest.md"` (hardcoded path)

### 5. Function and Class Example Usages

*   **`AdvancedLearningEngine`**: Intended for advanced analytics like integrating external data, analyzing trust patterns using `statsmodels`, analyzing symbolic correlation using `sklearn`, and explaining forecasts with `shap`.
    ```python
    advanced_engine = AdvancedLearningEngine(data_path="path/to/data")
    advanced_engine.integrate_external_data(some_dataframe)
    advanced_engine.analyze_trust_patterns(another_dataframe)
    ```
*   **`LearningEngine`**: The main orchestrator. Intializes various sub-engines (currently placeholders) and provides methods for handling simulation turns, consuming traces, processing drift reports, updating variable/rule weights, auditing clusters, and logging summaries.
    ```python
    learning_engine = LearningEngine()
    learning_engine.attach_worldstate(world_state_object)
    learning_engine.on_simulation_turn_end(snapshot)
    learning_engine.update_variable_weights("variable_abc", True)
    ```
*   **`compute_retrodiction_error`**: Calculates the squared error between forecast and current state overlays.
    ```python
    error = compute_retrodiction_error(forecast_dict, current_state_dict)
    ```
*   **`reconstruct_past_state`**: Reconstructs a simplified past state from a forecast dictionary.
    ```python
    past_state = reconstruct_past_state(forecast_dict)
    ```
*   **`retrodict_error_score`**: Computes a weighted error score based on symbolic and capital differences between a past and current state.
    ```python
    score = retrodict_error_score(past_state_dict, current_state_dict)
    ```
*   **`retrospective_analysis_batch`**: Processes a batch of forecasts, computes retrodiction errors, and flags those exceeding a threshold.
    ```python
    analyzed_forecasts = retrospective_analysis_batch(list_of_forecasts, current_state_dict, threshold=2.0)
    ```

### 6. Hardcoding Issues (SPARC: Security)

The following hardcoded values were identified:

*   **File Paths:**
    *   `"data/outputs"` (line 74) - Default data path for `OutputDataReader`.
    *   `"logs/retrodiction_result_log.jsonl"` (line 97) - Path to the retrodiction result log.
    *   `"logs/learning_summary_with_digest.md"` (line 380) - Path for writing the learning summary digest.
*   **Magic Numbers:**
    *   `5` (line 124) - Window size for rolling fragility mean.
    *   `0.1` (line 103, 299, 332) - Threshold for concept drift detection and minimum trust weight.
    *   `0.25` (line 294) - Threshold for variable drift detection.
    *   `1.0` (line 265, 284, 298, 331, 423, 423) - Default trust weight, symbolic/capital weights in `retrodict_error_score`.
    *   `0.85` (line 299, 332) - Multiplier for reducing trust weight under mutation pressure.
    *   `0.5` (line 325, 416, 417, 418, 419, 427, 427) - Volatility score threshold, default symbolic overlay values.
    *   `0.4` (line 349) - Volatility score threshold for rule clusters.
    *   `1000.0` (line 432) - Divisor for capital difference in `retrodict_error_score`.
    *   `4` (line 410, 433) - Rounding precision.
    *   `1.5` (line 435) - Default threshold for flagging retrodiction errors.
    *   `5` (line 376, 385) - Limit for digest formatting.

These hardcoded values should be moved to a configuration file or managed through a dedicated configuration system to improve flexibility and adherence to the SPARC security principle of avoiding hardcoded sensitive/configurable data.

### 7. Coupling Points

The module exhibits significant coupling with numerous other components of the Pulse system:

*   **Memory:** Directly interacts with `TraceMemory` and `VariablePerformanceTracker`.
*   **Core:** Depends on `VariableRegistry`, `BayesianTrustTracker`, and `PulseLearningLog`.
*   **Trust System:** Calls `TrustEngine.enrich_trust_metadata`.
*   **Simulation Engine:** Calls `rule_mutation_engine.apply_rule_mutations`.
*   **Memory Clustering:** Calls `variable_cluster_engine.summarize_clusters` and `rule_cluster_engine.summarize_rule_clusters`.
*   **Symbolic System:** Calls `symbolic_contradiction_cluster.cluster_symbolic_conflicts`.
*   **Operator Interface:** Calls various formatter and exporter functions for reporting.
*   **Filesystem:** Reads from and writes to specific file paths.

This high degree of coupling suggests potential challenges for independent testing and future modifications.

### 8. Existing Tests (SPARC: Refinement - Testability)

Based on the previous attempt insights and the provided file list, the test file [`tests/test_learning.py`](tests/test_learning.py:1) is either missing or has inadequate test coverage. This is a major gap in adherence to the SPARC refinement principle of testability. Comprehensive unit and integration tests are needed to verify the functionality of the `LearningEngine`, `AdvancedLearningEngine`, and the utility functions, especially given the complex interactions and calculations involved.

### 9. Module Architecture and Flow (SPARC: Architecture)

The module follows a composite pattern, with the main `LearningEngine` orchestrating several sub-engines (currently placeholders). The `AdvancedLearningEngine` handles specific analytical tasks. The overall flow involves:

1.  Initialization of memory trackers, registries, and sub-engines.
2.  Integration of simulation traces and external data.
3.  Processing of drift reports.
4.  Updating variable and rule weights based on performance and mutation pressure.
5.  Auditing variable and rule clusters for volatility.
6.  Auditing symbolic contradictions.
7.  Logging learning summaries and exporting digests.
8.  Utility functions for retrodiction analysis.

The architecture relies heavily on shared state managed by external components (e.g., `VariableRegistry`, `TrustTracker`) and direct calls to functions in other modules, indicating a somewhat procedural flow within the object-oriented structure.

### 10. Naming Conventions (SPARC: Maintainability)

Naming conventions generally appear to follow PEP 8 guidelines (e.g., `snake_case` for functions and variables, `CamelCase` for classes). Variable names are reasonably descriptive. Docstrings are present for the module and the main `LearningEngine` class, but are missing for `AdvancedLearningEngine` and most individual methods and functions, which hinders maintainability and understanding. The use of single-letter variable names like `X` and `y` in `analyze_symbolic_correlation` is acceptable in the context of machine learning conventions but could be slightly more descriptive.

### 11. SPARC Compliance Summary

*   **Specification:** The module's purpose is clearly defined.
*   **Modularity/Architecture:** The module attempts a modular design with sub-engines, but the high degree of coupling with external modules and reliance on shared state reduces its overall modularity and independence. The presence of placeholder classes indicates an incomplete architecture.
*   **Refinement (Testability, Security, Maintainability):**
    *   **Testability:** Major gap due to missing or inadequate tests for [`tests/test_learning.py`](tests/test_learning.py:1).
    *   **Security (No Hardcoding):** Significant violations due to numerous hardcoded file paths and magic numbers.
    *   **Maintainability:** Hindered by missing docstrings for most functions/methods, basic error handling, and the use of `print` for logging. Naming conventions are mostly compliant but could be improved with more descriptive variable names in some cases.
*   **Overall:** The module has a clear defined purpose but falls short on key SPARC refinement principles, particularly testability and the avoidance of hardcoded values. The architecture is a work in progress with significant coupling.
