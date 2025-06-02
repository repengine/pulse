# Analysis Report for learning/learning.py

**Version:** Pulse Meta-Learning Engine v0.30
**Author:** Pulse AI Engine

## 1. Module Intent/Purpose

The primary role of the `learning.py` module is to serve as the meta-learning engine for the Pulse system. It is responsible for evolving and adapting the system's understanding and performance over time. This includes:

*   Analyzing simulation lineage and forecast regret.
*   Updating variable trust scores based on performance.
*   Managing and evolving symbolic overlays and their influence on forecasts.
*   Detecting and responding to concept drift and symbolic contradictions.
*   Integrating various specialized sub-engines for tasks like anomaly remediation, feature discovery, causal inference, and audit reporting.
*   Performing retrospective analysis to identify misalignments and improve future predictions.
*   Logging learning activities and generating summaries for operational insight.

The module defines two main classes:
*   `AdvancedLearningEngine`: Focuses on data integration, advanced analytics (trust patterns, symbolic correlations, SHAP explanations), plugin management, and callbacks.
*   `LearningEngine`: The core engine that orchestrates various learning processes, integrates the `AdvancedLearningEngine` and other placeholder/specialized engines, updates variable and rule weights, and performs audits.

## 2. Operational Status/Completeness

The module appears to be partially complete, with a foundational structure and several implemented functionalities, but also significant placeholders and areas for further development.

**Completed Aspects:**
*   Basic structure for `LearningEngine` and `AdvancedLearningEngine`.
*   Integration of `TraceMemory`, `VariablePerformanceTracker`, and `VariableRegistry`.
*   Mechanisms for updating variable weights based on performance and profiles.
*   Rudimentary concept drift detection and data blending.
*   Analysis of trust patterns (OLS regression) and symbolic overlay correlation (mutual information).
*   SHAP value computation (if `shap` is installed).
*   Basic memory management (`remember`, `recall`, `sync_memory`).
*   Plugin registration and summarization framework.
*   Callback mechanism for the learning loop.
*   Logging of learning summaries and generation of digests.
*   Retrodiction utilities for error calculation and past state reconstruction.
*   Auditing of variable and rule cluster volatility.
*   Detection of symbolic contradictions.

**Obvious Placeholders/TODOs:**
*   **Placeholder Engines:** Several engines are defined as placeholder classes with only a `__str__` method:
    *   [`AnomalyRemediationEngine`](learning/learning.py:51)
    *   [`FeatureDiscoveryEngine`](learning/learning.py:54)
    *   [`AuditReportingEngine`](learning/learning.py:57)
    *   [`CausalInferenceEngine`](learning/learning.py:60)
    *   [`ContinuousLearningEngine`](learning/learning.py:63)
    *   [`ExternalIntegrationEngine`](learning/learning.py:66)
    *   [`ActiveExperimentationEngine`](learning/learning.py:69)
    These are instantiated in `LearningEngine` and registered as plugins, but their core logic is missing.
*   **Commented-out `run_meta_update()`:** The `if __name__ == "__main__":` block (line 444) has `engine.run_meta_update()` commented out, indicating a primary execution loop or method is not yet implemented or finalized.
*   **Fallback Data Loading:** [`LearningEngine.consume_simulation_trace()`](learning/learning.py:243) uses `get_all_metadata` as a fallback if `load_trace` doesn't exist on the data loader, suggesting `load_trace` might be a preferred but potentially unimplemented method.
*   **Error Handling:** Some error handling logs warnings (e.g., "Concept drift blending failed", "Trust regression failed") but might require more robust recovery or response mechanisms.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Full Implementation of Placeholder Engines:** The most significant gap is the lack of implementation for the specialized engines listed above. Their integration suggests a plan for a comprehensive learning system, but their current state is skeletal.
*   **`run_meta_update()` Method:** The core meta-update loop, hinted at by the commented-out line, needs to be implemented. This would likely orchestrate the various learning tasks, engine calls, and updates.
*   **Advanced Data Integration:** While basic data blending is present, more sophisticated methods for handling concept drift, integrating diverse data sources, and ensuring data quality could be developed.
*   **Symbolic Overlay Evolution:** The module analyzes symbolic overlay correlation and adds edges to an `overlay_graph`, but the mechanisms for actively evolving or mutating these overlays based on the analysis are not explicitly detailed.
*   **Rule Mutation Details:** [`LearningEngine.apply_rule_mutation_pressure()`](learning/learning.py:308) calls an external `apply_rule_mutations()` function, but the specifics of how rules are selected for mutation or how new rules are generated/evaluated within this module are not detailed.
*   **Callback Usage:** Callbacks are registered, but the specific events or stages in the learning loop that trigger these callbacks are not fully defined beyond a general summary trigger.
*   **WorldState Interaction:** The `worldstate` attribute in `LearningEngine` is attached but its full utilization throughout the learning processes isn't extensively shown beyond the `on_simulation_turn_end` method.
*   **Refinement of Audits:** The audit functions print information and can trigger weight adjustments. More sophisticated responses to audit findings (e.g., automated remediation, detailed reporting through the `AuditReportingEngine`) could be future steps.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`from analytics.trace_memory import TraceMemory`](learning/learning.py:44)
*   [`from analytics.variable_performance_tracker import VariablePerformanceTracker`](learning/learning.py:45)
*   [`from core.variable_registry import VariableRegistry`](learning/learning.py:46)
*   [`from core.bayesian_trust_tracker import bayesian_trust_tracker`](learning/learning.py:47)
*   [`from core.optimized_trust_tracker import optimized_bayesian_trust_tracker`](learning/learning.py:48)
*   [`from analytics.output_data_reader import OutputDataReader`](learning/learning.py:78) (within `AdvancedLearningEngine.__init__`)
*   [`from trust_system.trust_engine import TrustEngine`](learning/learning.py:237) (within `LearningEngine.on_simulation_turn_end`)
*   [`from core.pulse_learning_log import log_variable_weight_change, log_learning_summary`](learning/learning.py:271) (and other methods)
*   [`from engine.rule_mutation_engine import apply_rule_mutations`](learning/learning.py:310) (within `LearningEngine.apply_rule_mutation_pressure`)
*   [`from analytics.variable_cluster_engine import summarize_clusters`](learning/learning.py:320) (within `LearningEngine.audit_cluster_volatility`)
*   [`from analytics.rule_cluster_engine import summarize_rule_clusters`](learning/learning.py:344) (within `LearningEngine.audit_rule_clusters`)
*   [`from symbolic_system.symbolic_contradiction_cluster import cluster_symbolic_conflicts`](learning/learning.py:355) (within `LearningEngine.audit_symbolic_contradictions`)
*   [`from operator_interface.rule_cluster_digest_formatter import format_cluster_digest_md`](learning/learning.py:375)
*   [`from operator_interface.variable_cluster_digest_formatter import format_variable_cluster_digest_md`](learning/learning.py:384)
*   [`from operator_interface.mutation_digest_exporter import export_full_digest`](learning/learning.py:388)
*   [`from operator_interface.symbolic_contradiction_digest import export_contradiction_digest_md`](learning/learning.py:389)

### External Library Dependencies:
*   `logging`
*   `typing` (Any, Dict, List, Optional, Callable)
*   `datetime` (datetime, timezone)
*   `math`
*   `statsmodels.api` (optional, aliased as `sm`)
*   `shap` (optional)
*   `sklearn.feature_selection.mutual_info_regression` (optional)
*   `networkx` (optional, aliased as `nx`)
*   `pandas` (optional, aliased as `pd`)

### Interaction with Other Modules via Shared Data:
*   **Input Files:**
    *   Reads from `data/outputs` via `OutputDataReader` (instantiated in [`AdvancedLearningEngine`](learning/learning.py:79)).
    *   Reads `"logs/retrodiction_result_log.jsonl"` (line 97) for concept drift detection.
*   **Output Files:**
    *   Writes to `"logs/learning_summary_with_digest.md"` (line 380).
    *   Implicitly, `VariableRegistry._save()` (line 273) would write to its configured persistence layer.
    *   `operator_interface` functions like `export_full_digest()` and `export_contradiction_digest_md()` likely write files.
*   **Databases/Message Queues:** No explicit interactions with databases or message queues are visible in this module.

## 5. Function and Class Example Usages

*   **`AdvancedLearningEngine`:**
    *   Intended to be instantiated, potentially with a custom `data_path`.
    *   `integrate_external_data(source_df)`: Called to load and blend data, triggering trust and symbolic analyses.
    *   `analyze_trust_patterns(df)`: Internally called to perform regression on trust scores.
    *   `analyze_symbolic_correlation(df)`: Internally called to calculate mutual information for symbolic overlays.
    *   `explain_forecast_with_shap(model, X)`: Can be used to get SHAP explanations if a model and data are provided.
    *   `remember(key, value)` / `recall(key)`: Basic key-value store.
    *   `register_plugin(plugin)`: Used to add plugin instances.
    *   `register_callback(callback)`: Used to add callback functions.

*   **`LearningEngine`:**
    *   Instantiated as `engine = LearningEngine()` (line 445).
    *   `attach_worldstate(state)`: To link a `WorldState` object.
    *   `on_simulation_turn_end(state_snapshot)`: Called after each simulation turn to log traces.
    *   `consume_simulation_trace(trace_path)`: To process simulation trace data.
    *   `update_variable_weights(variable_id, outcome)`: To adjust weights based on direct outcomes.
    *   `update_variable_weights_from_profile(variable_id, profile_outcome)`: To adjust weights based on learning profile outcomes.
    *   `apply_variable_mutation_pressure(variable_id, mutation_success)`: To apply downward pressure on weights of drifting variables.
    *   `apply_rule_mutation_pressure(rule_id, mutation_success)`: To trigger rule mutations.
    *   `audit_cluster_volatility()`: To scan and react to volatile variable clusters.
    *   `audit_rule_clusters()`: To scan rule clusters.
    *   `audit_symbolic_contradictions(forecasts)`: To find and report symbolic conflicts.
    *   `log_learning_summary()`: To log completion and generate digests.

*   **Retrodiction Utilities:**
    *   `compute_retrodiction_error(forecast, current_state, keys)`: Calculates error between a forecast's initial state and a current state.
    *   `reconstruct_past_state(forecast)`: Extracts a simplified past state from a forecast object.
    *   `retrodict_error_score(past_state, current_state, symbolic_weight, capital_weight)`: Computes a weighted error score.
    *   `retrospective_analysis_batch(forecasts, current_state, threshold)`: Processes a batch of forecasts to add retrodiction error and flags.

## 6. Hardcoding Issues

*   **File Paths:**
    *   `data_path: str = "data/outputs"` (default in [`AdvancedLearningEngine.__init__`](learning/learning.py:74))
    *   `"logs/retrodiction_result_log.jsonl"` (in [`AdvancedLearningEngine.integrate_external_data`](learning/learning.py:97))
    *   `"logs/learning_summary_with_digest.md"` (in [`LearningEngine.log_learning_summary`](learning/learning.py:380))
*   **Magic Numbers:**
    *   Concept drift threshold `0.1` (line 103)
    *   Rolling window size `5` for fragility (line 124)
    *   Variable drift threshold `0.25` (line 294)
    *   Trust weight decay factor `0.85` (lines 299, 332)
    *   Minimum trust weight `0.1` (lines 299, 332)
    *   Rule cluster volatility threshold `0.4` (line 349)
    *   Variable cluster volatility threshold `0.5` (line 325)
    *   Retrodiction error threshold `1.5` (line 435)
    *   Default trust weight `1.0` (various locations)
    *   Capital normalization factor `1000.0` (line 432)
    *   Default symbolic values `0.5` (lines 416-419, 427)
*   **Magic Strings (Keys/Labels):**
    *   DataFrame columns: `"fragility"`, `"trust_score"`, `"symbolic_overlay"`, `"forecast_success"`, `"error_score"`, `"source"`.
    *   Memory keys: `"trust_model_summary"`, `"last_drift_report"`.
    *   Symbolic overlay keys: `"hope"`, `"despair"`, `"fatigue"`, `"rage"` (lines 416-419, 424).
    *   Trace ID: `"sim_turn"` (line 239).
    *   Retrodiction flag: `"⚠️ Symbolic misalignment"` (line 441).

## 7. Coupling Points

The module is significantly coupled with several other parts of the Pulse system:

*   **`memory` package:**
    *   `TraceMemory`: For logging and summarizing simulation traces.
    *   `VariablePerformanceTracker`: For scoring variable effectiveness and detecting drift.
    *   `variable_cluster_engine`: For summarizing variable clusters.
    *   `rule_cluster_engine`: For summarizing rule clusters.
*   **`core` package:**
    *   `VariableRegistry`: For managing variable metadata and trust weights.
    *   `bayesian_trust_tracker` / `optimized_bayesian_trust_tracker`: For updating and retrieving trust scores for variables and rules.
    *   `pulse_learning_log`: For logging specific learning events like weight changes and summaries.
*   **`learning` package (itself):**
    *   `OutputDataReader`: For loading external data.
*   **`trust_system` package:**
    *   `TrustEngine`: For enriching state snapshots with trust metadata.
*   **`simulation_engine` package:**
    *   `rule_mutation_engine`: For applying mutations to causal rules.
*   **`symbolic_system` package:**
    *   `symbolic_contradiction_cluster`: For identifying conflicts in forecasts.
*   **`operator_interface` package:**
    *   Modules for formatting and exporting various digests (rule clusters, variable clusters, mutations, contradictions).
*   **External Data Format:** Assumes specific structures for forecast objects, state snapshots, and data read from files (e.g., `retrodiction_result_log.jsonl`).

## 8. Existing Tests

*   Based on the provided file list for the `tests/` directory, there is **no specific test file named `test_learning.py`**.
*   There is a [`tests/test_learning_profile.py`](tests/test_learning_profile.py:1), which would test the separate `learning_profile.py` module, not this one.
*   **Gap:** This indicates a lack of dedicated unit tests for the `LearningEngine` and `AdvancedLearningEngine` classes and their methods within this module. While some functionalities might be indirectly tested via integration tests or tests for coupled modules (e.g., `VariablePerformanceTracker`), direct testing of this module's logic is missing.

## 9. Module Architecture and Flow

The module is architected around two primary classes:

1.  **`AdvancedLearningEngine`**:
    *   **Purpose**: Handles more specialized analytical tasks, data integration, and serves as a hub for plugins and callbacks.
    *   **Key Components**:
        *   `memory`: An internal dictionary for persistent storage of analytical results (e.g., model summaries).
        *   `plugins`: A list to register and manage plugin engines.
        *   `overlay_graph`: A `networkx.DiGraph` to model symbolic influence paths.
        *   `data_loader`: An instance of `OutputDataReader` to fetch external data.
        *   `callbacks`: A list of functions to be called, typically with an analytics summary.
    *   **Flow**:
        *   Integrates external data (e.g., from simulation outputs, retrodiction logs).
        *   Performs concept drift detection and blends data.
        *   Analyzes trust patterns using OLS regression (trust vs. fragility).
        *   Analyzes symbolic overlay correlation with forecast success using mutual information.
        *   Can provide SHAP explanations for models.
        *   Exports an analytics summary and triggers registered callbacks.

2.  **`LearningEngine`**:
    *   **Purpose**: The main orchestrator for meta-learning activities within Pulse. It integrates various sub-systems and specialized engines to adapt the system.
    *   **Key Components**:
        *   `trace`: `TraceMemory` instance.
        *   `tracker`: `VariablePerformanceTracker` instance.
        *   `registry`: `VariableRegistry` instance.
        *   `advanced_engine`: An instance of `AdvancedLearningEngine`.
        *   Instances of placeholder engines (Anomaly Remediation, Feature Discovery, etc.).
        *   `worldstate`: Optional attachment to a `WorldState` object.
    *   **Flow**:
        *   **Initialization**: Sets up core components and registers placeholder engines as plugins to the `advanced_engine`.
        *   **Event Handling**:
            *   `on_simulation_turn_end()`: Logs enriched state snapshots to trace memory.
        *   **Data Consumption**:
            *   `consume_simulation_trace()`: Uses `advanced_engine` to integrate trace data.
        *   **Weight/Trust Updates**:
            *   `update_variable_weights()`: Adjusts variable trust weights based on performance scores from `tracker` and updates `optimized_bayesian_trust_tracker`.
            *   `update_variable_weights_from_profile()`: Adjusts weights based on `LearningProfile` outcomes.
        *   **Mutation Pressure**:
            *   `apply_variable_mutation_pressure()`: Reduces trust weights for variables exhibiting drift.
            *   `apply_rule_mutation_pressure()`: Triggers external rule mutation processes and updates trust for the rule.
        *   **Auditing**:
            *   `audit_cluster_volatility()`: Checks variable clusters for high volatility and applies mutation pressure.
            *   `audit_rule_clusters()`: Scans rule clusters for volatility.
            *   `audit_symbolic_contradictions()`: Detects and reports conflicting symbolic information in forecasts.
        *   **Reporting**:
            *   `log_learning_summary()`: Logs completion, generates, prints, and saves various operational digests.

**Overall Flow**: The `LearningEngine` acts as the central coordinator. It consumes data from simulations and external logs, uses its components (like `VariablePerformanceTracker` and `AdvancedLearningEngine`) to analyze this data, and then applies updates to variable weights, rule trust, and potentially triggers mutations. It also performs periodic audits and generates reports. The `AdvancedLearningEngine` provides more focused analytical capabilities that the `LearningEngine` leverages.

## 10. Naming Conventions

*   **Classes**: Generally follow PEP 8 `PascalCase` (e.g., `AdvancedLearningEngine`, `LearningEngine`). Placeholder engine classes also follow this.
*   **Methods and Functions**: Mostly follow PEP 8 `snake_case` (e.g., `integrate_external_data`, `compute_retrodiction_error`).
*   **Variables**: Mostly follow PEP 8 `snake_case` (e.g., `overlay_graph`, `source_df`).
*   **Constants/Magic Strings/Numbers**: As noted in "Hardcoding Issues," these are present. Some string keys are descriptive (e.g., `trust_model_summary`).
*   **Consistency**: The naming is largely consistent within the module.
*   **AI Assumption Errors/Deviations**:
    *   The module header attributes authorship to "Pulse AI Engine," which is consistent with an AI-generated or heavily AI-assisted codebase.
    *   Names are generally conventional for Python and do not exhibit obvious or awkward AI-generated patterns that deviate significantly from common practice.
    *   The use of placeholder classes with simple `__str__` methods is a common pattern for scaffolding and might be indicative of an iterative development process, possibly AI-assisted.
    *   The docstrings are informative but sometimes high-level, which can be typical of initial AI generation before detailed human refinement.

No major deviations from PEP 8 or project standards (assuming standard Python conventions) are immediately apparent in naming, beyond the presence of hardcoded values.