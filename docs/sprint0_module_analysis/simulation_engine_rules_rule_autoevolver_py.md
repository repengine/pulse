# Module Analysis: `simulation_engine/rules/rule_autoevolver.py`

## 1. Module Intent/Purpose

The primary role of this module is to provide meta-learning capabilities for managing simulation rules. It is responsible for evaluating, mutating, promoting, and deprecating rules based on their performance, observed drift, and coherence within the rule set. It aims to automate the evolution of the rule base for the simulation engine.

## 2. Operational Status/Completeness

The module appears to be operational with core functionalities implemented, including rule scoring (though currently a stub), mutation proposal, deprecation, and promotion of candidate rules. A command-line interface (CLI) is provided for manual execution of these operations.

Key observations:
*   The rule scoring function, [`score_rule_from_forecast()`](simulation_engine/rules/rule_autoevolver.py:44), is explicitly marked as a "Placeholder" and "stub" (see lines 46, 49). This indicates it requires significant further development to incorporate more sophisticated metrics beyond the current use of `forecast.get('confidence', 0.5)`.
*   Logging for rule mutations and trust scores is implemented, writing to [`logs/rule_mutation_log.jsonl`](logs/rule_mutation_log.jsonl) and [`logs/rule_trust_log.jsonl`](logs/rule_trust_log.jsonl) respectively.
*   The module initializes and uses a [`RuleRegistry`](simulation_engine/rules/rule_registry.py) instance.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Rule Scoring Sophistication:** The most critical gap is the placeholder implementation of [`score_rule_from_forecast()`](simulation_engine/rules/rule_autoevolver.py:44). The docstring (line 46) mentions extending it with "PFPA, regret, etc.", which is essential for meaningful rule evaluation.
*   **Automated Evolution Loop:** While individual functions for scoring, mutating, deprecating, and promoting exist, there's no overarching function or mechanism that orchestrates these into a continuous, automated rule evolution loop. The current design seems to rely on external triggers or manual CLI calls.
*   **Persistence of Mutations:** The [`propose_mutation()`](simulation_engine/rules/rule_autoevolver.py:65) function updates rules in the local `_registry.rules` list (line 79) if not a `dry_run`. It's unclear if or how these mutations are persisted back to the original rule definition files or a central rule storage. This is crucial for mutations to be effective in subsequent system runs. The [`RuleRegistry`](simulation_engine/rules/rule_registry.py) might handle persistence, but this interaction isn't explicit within this module.
*   **Integration of Supporting Utilities:**
    *   [`scan_rule_coherence()`](simulation_engine/rules/rule_coherence_checker.py) is imported but not actively used to influence scoring or mutation decisions.
    *   [`get_all_rule_fingerprints()`](simulation_engine/rules/pulse_rule_expander.py) and [`explain_forecast()`](simulation_engine/rules/pulse_rule_explainer.py) are imported but not directly used in the core auto-evolution logic. These could enhance rule analysis or mutation strategies.
    *   [`summarize_rule_clusters()`](memory/rule_cluster_engine.py) is imported but not utilized, suggesting an unimplemented feature related to leveraging rule clustering for evolution.
*   **Drift Analysis Actionability:** While [`detect_drifted_rules()`](simulation_engine/rules/rule_autoevolver.py:54) is present, its output isn't explicitly fed into the mutation or deprecation logic.

## 4. Connections & Dependencies

*   **Direct Project Module Imports:**
    *   [`simulation_engine.rules.rule_registry.RuleRegistry`](simulation_engine/rules/rule_registry.py)
    *   [`simulation_engine.rule_mutation_engine.propose_rule_mutations`](simulation_engine/rule_mutation_engine.py)
    *   [`simulation_engine.simulation_drift_detector.run_simulation_drift_analysis`](simulation_engine/simulation_drift_detector.py)
    *   [`simulation_engine.rules.rule_coherence_checker.scan_rule_coherence`](simulation_engine/rules/rule_coherence_checker.py)
    *   [`simulation_engine.rules.pulse_rule_expander.get_all_rule_fingerprints`](simulation_engine/rules/pulse_rule_expander.py)
    *   [`simulation_engine.rules.pulse_rule_explainer.explain_forecast`](simulation_engine/rules/pulse_rule_explainer.py)
    *   [`memory.rule_cluster_engine.summarize_rule_clusters`](memory/rule_cluster_engine.py)
*   **External Library Dependencies:**
    *   `json`
    *   `logging`
    *   `os`
    *   `typing` (Dict, Any, List, Optional)
    *   `argparse` (for CLI functionality)
*   **Interaction via Shared Data:**
    *   Relies heavily on [`RuleRegistry`](simulation_engine/rules/rule_registry.py) for loading and managing rules, implying rules are stored in a format/location (likely JSON files) accessible by the registry.
    *   Reads forecast data from JSON files (e.g., in [`batch_score_rules()`](simulation_engine/rules/rule_autoevolver.py:111) and the [`score`](simulation_engine/rules/rule_autoevolver.py:157) CLI command).
*   **Input/Output Files:**
    *   **Input:**
        *   Forecast files (JSON format, e.g., `forecast.json` for scoring).
        *   Rule definition files (implicitly, via [`RuleRegistry`](simulation_engine/rules/rule_registry.py)).
        *   Trace identifiers (strings `prev_trace`, `curr_trace`) for drift detection.
    *   **Output:**
        *   [`logs/rule_mutation_log.jsonl`](logs/rule_mutation_log.jsonl) (append mode)
        *   [`logs/rule_trust_log.jsonl`](logs/rule_trust_log.jsonl) (append mode)
        *   Console output (summaries, CLI results).

## 5. Function and Class Example Usages

*   **[`score_rule_from_forecast(rule_id: str, forecast: dict, outcome: dict) -> float`](simulation_engine/rules/rule_autoevolver.py:44):**
    *   *Description:* Calculates a trust score for a rule based on its forecast performance. Currently a placeholder.
    *   *Example (conceptual):*
        ```python
        # forecast_data = {"confidence": 0.8, "trace_id": "trace123", "outcome": {"actual_value": 10}}
        # score = score_rule_from_forecast(rule_id="rule_abc", forecast=forecast_data, outcome=forecast_data.get('outcome'))
        # logger.info(f"Rule score for rule_abc: {score}")
        ```

*   **[`propose_mutation(rule_id: str, dry_run: bool = False) -> Optional[Dict]`](simulation_engine/rules/rule_autoevolver.py:65):**
    *   *Description:* Suggests changes (mutations) to a rule's parameters, effects, or tags by calling [`propose_rule_mutations()`](simulation_engine/rule_mutation_engine.py:).
    *   *Example:*
        ```python
        # mutation_suggestion = propose_mutation(rule_id="rule_xyz", dry_run=True)
        # if mutation_suggestion:
        #     logger.info(f"Proposed mutation for rule_xyz: {mutation_suggestion}")
        ```

*   **[`deprecate(rule_id: str, dry_run: bool = False) -> bool`](simulation_engine/rules/rule_autoevolver.py:83):**
    *   *Description:* Disables a rule by setting its 'enabled' flag to `False` within the loaded registry.
    *   *Example:*
        ```python
        # success = deprecate(rule_id="rule_old_and_busted", dry_run=False)
        # logger.info(f"Rule rule_old_and_busted deprecated: {success}")
        ```

*   **CLI Usage Examples:**
    *   Propose mutation for a rule:
        ```bash
        python simulation_engine/rules/rule_autoevolver.py --mutate my_rule_001 --dry-run
        ```
    *   Score a rule against a forecast file:
        ```bash
        python simulation_engine/rules/rule_autoevolver.py --score my_rule_002 path/to/forecast_data.json
        ```
    *   Promote eligible candidate rules:
        ```bash
        python simulation_engine/rules/rule_autoevolver.py --promote-candidates --verbose
        ```
    *   View audit summary:
        ```bash
        python simulation_engine/rules/rule_autoevolver.py --audit-summary
        ```

## 6. Hardcoding Issues

*   **Log File Paths:**
    *   [`MUTATION_LOG_PATH = "logs/rule_mutation_log.jsonl"`](simulation_engine/rules/rule_autoevolver.py:26)
    *   [`TRUST_LOG_PATH = "logs/rule_trust_log.jsonl"`](simulation_engine/rules/rule_autoevolver.py:27)
    These paths are hardcoded. Using a configuration mechanism would offer more flexibility.
*   **Default Score Value:** In [`score_rule_from_forecast()`](simulation_engine/rules/rule_autoevolver.py:44), the default confidence `0.5` (line 50) is hardcoded. This is part of the placeholder logic but should be configurable or derived.
*   **Mutation Proposal Count:** In [`propose_mutation()`](simulation_engine/rules/rule_autoevolver.py:65), `top_n=1` (line 75) is hardcoded when calling [`propose_rule_mutations()`](simulation_engine/rule_mutation_engine.py:).
*   **Audit Summary Log Lines:** In [`audit_summary()`](simulation_engine/rules/rule_autoevolver.py:129), `readlines()[-10:]` (lines 136, 141) hardcodes the display to the last 10 log entries.

## 7. Coupling Points

*   **[`RuleRegistry`](simulation_engine/rules/rule_registry.py):** Tightly coupled. The module instantiates and directly manipulates a `_registry` object for all rule access, loading, and state modifications (promotion, enabling/disabling).
*   **[`simulation_engine.rule_mutation_engine`](simulation_engine/rule_mutation_engine.py):** High coupling. The core mutation logic relies entirely on the external [`propose_rule_mutations()`](simulation_engine/rule_mutation_engine.py:) function.
*   **[`simulation_engine.simulation_drift_detector`](simulation_engine/simulation_drift_detector.py):** Dependency for drift analysis via [`run_simulation_drift_analysis()`](simulation_engine/simulation_drift_detector.py:).
*   **Log Files:** The hardcoded log file paths create an implicit coupling if other system components need to consume or be aware of these specific log files.
*   **Forecast File Schema:** Assumes a specific JSON structure for forecast files in [`batch_score_rules()`](simulation_engine/rules/rule_autoevolver.py:111) and the CLI scoring mechanism. Changes to this schema would break functionality.

## 8. Existing Tests

*   A review of the provided file list (from `environment_details`) does not show a dedicated test file such as `tests/simulation_engine/rules/test_rule_autoevolver.py`.
*   While related test files like [`tests/test_rule_adjustment.py`](tests/test_rule_adjustment.py:) and [`tests/test_rule_consistency.py`](tests/test_rule_consistency.py:) exist, they likely do not provide specific coverage for the auto-evolution logic, CLI operations, or the integration points within `rule_autoevolver.py` itself.
*   **Conclusion:** There appears to be a gap in dedicated unit and integration tests for this module's specific functionalities.

## 9. Module Architecture and Flow

*   **Initialization:** A module-level [`RuleRegistry`](simulation_engine/rules/rule_registry.py:) instance (`_registry`) is created, and [`_registry.load_all_rules()`](simulation_engine/rules/rule_registry.py:) is called immediately to populate it.
*   **Core Functional Units:** The module is structured as a collection of functions, each responsible for a specific aspect of rule evolution:
    *   Logging: [`log_action()`](simulation_engine/rules/rule_autoevolver.py:35)
    *   Scoring: [`score_rule_from_forecast()`](simulation_engine/rules/rule_autoevolver.py:44), [`batch_score_rules()`](simulation_engine/rules/rule_autoevolver.py:111)
    *   Drift Detection: [`detect_drifted_rules()`](simulation_engine/rules/rule_autoevolver.py:54)
    *   Mutation: [`propose_mutation()`](simulation_engine/rules/rule_autoevolver.py:65)
    *   Deprecation: [`deprecate()`](simulation_engine/rules/rule_autoevolver.py:83)
    *   Promotion: [`promote_from_candidate()`](simulation_engine/rules/rule_autoevolver.py:97)
    *   Auditing: [`audit_summary()`](simulation_engine/rules/rule_autoevolver.py:129)
*   **Data Flow:**
    *   Rules are sourced from the `_registry`.
    *   Forecast data is read from external JSON files.
    *   Rule state modifications (scores, mutations, status) are primarily updated within the `_registry` instance. Persistence of these changes beyond the current session is managed by `RuleRegistry` or is a potential gap for mutations.
    *   Actions and scores are logged to JSONL files.
*   **Control Flow:** Primarily event-driven via external function calls or through the CLI. There is no internal, continuous loop managing the rule evolution process automatically.
*   **CLI Interface:** Uses `argparse` to provide command-line access to most of the module's functions, allowing for manual intervention and batch operations.

## 10. Naming Conventions

*   **Functions:** Adhere to PEP 8 (e.g., [`score_rule_from_forecast`](simulation_engine/rules/rule_autoevolver.py:44), [`propose_mutation`](simulation_engine/rules/rule_autoevolver.py:65)).
*   **Variables:** Mostly snake_case (e.g., `rule_id`, `dry_run`, `forecast_file`). The module-level `_registry` uses a leading underscore, conventionally indicating an internal or protected variable.
*   **Constants:** [`MUTATION_LOG_PATH`](simulation_engine/rules/rule_autoevolver.py:26) and [`TRUST_LOG_PATH`](simulation_engine/rules/rule_autoevolver.py:27) use uppercase with underscores, following Python conventions.
*   **Clarity & Consistency:** Names are generally descriptive and consistently applied within the module.
*   **Handling Key Variations:** The pattern `rule.get('rule_id', rule.get('id'))` (e.g., line 89) suggests a pragmatic approach to handling potential inconsistencies in rule dictionary key names (`rule_id` vs. `id`), which is a robust practice.
*   No obvious deviations from PEP 8 or project standards that would indicate AI assumption errors were noted.