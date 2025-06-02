# SPARC Analysis: simulation_engine/causal_rules.py

## Module Intent/Purpose (Specification)

The [`simulation_engine/causal_rules.py`](simulation_engine/causal_rules.py:1) module serves as the unified causal rule engine for the Pulse simulation. Its primary responsibility is to define, manage, and apply a set of causal rules that govern the interactions between symbolic overlays, numeric variables, and capital exposure within the simulation's [`WorldState`](simulation_engine/worldstate.py:471). It handles transformations such as symbolic-to-symbolic, variable-to-symbolic, and variable-to-capital, incorporating symbolic tagging for traceability and leveraging a Bayesian trust tracker to modulate rule effects based on their historical performance.

## Operational Status/Completeness

The module appears to be operational and relatively complete for its defined scope. It defines a set of 15 rules ([`RULES`](simulation_engine/causal_rules.py:22)) with descriptions, categories, and importance scores. The core functions for applying rules ([`apply_rule()`](simulation_engine/causal_rules.py:100), [`apply_causal_rules()`](simulation_engine/causal_rules.py:143)) and generating rule statistics ([`generate_rule_statistics()`](simulation_engine/causal_rules.py:327)) are implemented.

- No obvious placeholders like `pass` in critical logic paths.
- No explicit TODO comments were found.

## Implementation Gaps / Unfinished Next Steps

- **Dynamic Rule Loading:** The rules are currently hardcoded within the `RULES` dictionary. A more flexible system might load rules from an external configuration file or database, allowing for easier modification and expansion without code changes.
- **Advanced Condition/Effect Logic:** The current rule conditions and effects are defined using lambda functions. While concise, this might become unwieldy for more complex rules. A more structured approach for defining complex rule logic could be beneficial.
- **Rule Validation:** While [`apply_rule()`](simulation_engine/causal_rules.py:100) checks for unknown `rule_id`s, there's no explicit validation of the rule definitions themselves (e.g., ensuring necessary keys like 'description', 'category', 'importance' exist, or that importance is within a valid range).
- **Test Coverage (SPARC Refinement):** The module itself does not contain inline tests, and the existence and coverage of external tests are unknown from this file alone. Comprehensive unit tests for rule conditions, effects, and the [`BayesianTrustTracker`](core/bayesian_trust_tracker.py:17) interactions are crucial.

## Connections & Dependencies (Modularity/Architecture)

### Direct Imports:

*   **Project Modules:**
    *   [`engine.worldstate`](simulation_engine/worldstate.py:1) (specifically [`WorldState`](simulation_engine/worldstate.py:471))
    *   [`engine.state_mutation`](simulation_engine/state_mutation.py:1) (specifically [`adjust_overlay()`](simulation_engine/state_mutation.py:94), [`update_numeric_variable()`](simulation_engine/state_mutation.py:27), [`adjust_capital()`](simulation_engine/state_mutation.py:151))
    *   [`core.variable_accessor`](core/variable_accessor.py:1) (specifically [`get_variable()`](core/variable_accessor.py:11), [`get_overlay()`](core/variable_accessor.py:42))
    *   [`core.pulse_config`](core/pulse_config.py:1) (specifically [`CONFIDENCE_THRESHOLD`](core/pulse_config.py:42), [`DEFAULT_FRAGILITY_THRESHOLD`](core/pulse_config.py:43))
    *   [`core.pulse_learning_log`](core/pulse_learning_log.py:1) (specifically [`log_bayesian_trust_metrics()`](core/pulse_learning_log.py:307))
    *   [`core.bayesian_trust_tracker`](core/bayesian_trust_tracker.py:1) (specifically [`bayesian_trust_tracker`](core/bayesian_trust_tracker.py:213))
*   **External Libraries:**
    *   `logging` (standard Python library)

### Touched Project Files (for dependency mapping):

To understand the full context and dependencies of [`simulation_engine/causal_rules.py`](simulation_engine/causal_rules.py:1), the following project files were read and analyzed:

1.  [`simulation_engine/worldstate.py`](simulation_engine/worldstate.py:1)
2.  [`simulation_engine/state_mutation.py`](simulation_engine/state_mutation.py:1)
3.  [`core/variable_accessor.py`](core/variable_accessor.py:1)
4.  [`core/pulse_config.py`](core/pulse_config.py:1)
5.  [`core/pulse_learning_log.py`](core/pulse_learning_log.py:1)
6.  [`core/bayesian_trust_tracker.py`](core/bayesian_trust_tracker.py:1)
7.  [`core/variable_registry.py`](core/variable_registry.py:1) (dependency of [`core/variable_accessor.py`](core/variable_accessor.py:9))
8.  [`core/path_registry.py`](core/path_registry.py:1) (dependency of [`core/pulse_config.py`](core/pulse_config.py:14), [`core/pulse_learning_log.py`](core/pulse_learning_log.py:25), and [`core/variable_registry.py`](core/variable_registry.py:16))

### Interactions:

*   **Shared Data Structures:**
    *   Reads from and mutates the [`WorldState`](simulation_engine/worldstate.py:471) object, specifically its `overlays`, `variables`, and `capital` attributes.
    *   Uses configuration values from [`core.pulse_config`](core/pulse_config.py:1) like [`CONFIDENCE_THRESHOLD`](core/pulse_config.py:42) and [`DEFAULT_FRAGILITY_THRESHOLD`](core/pulse_config.py:43).
    *   Interacts with the singleton [`bayesian_trust_tracker`](core/bayesian_trust_tracker.py:213) to get trust scores for rules and log metrics.
*   **Files:**
    *   Implicitly, through [`core.pulse_learning_log`](core/pulse_learning_log.py:1), it writes to the learning log file (default: `logs/pulse_learning_log.jsonl`).
    *   Implicitly, through [`core.bayesian_trust_tracker`](core/bayesian_trust_tracker.py:1), it can read/write trust data if `export_to_file` or `import_from_file` methods are called elsewhere.
*   **Databases/Queues:** No direct interactions with databases or message queues are apparent from this module.

### Input/Output Files:

*   **Input:**
    *   Relies on the initial state of the [`WorldState`](simulation_engine/worldstate.py:471) object passed to [`apply_causal_rules()`](simulation_engine/causal_rules.py:143).
    *   Indirectly depends on configuration files read by [`core.pulse_config`](core/pulse_config.py:1) (e.g., `thresholds.json`, `default_config.json`).
    *   Indirectly depends on the Bayesian trust data file if imported by [`core.bayesian_trust_tracker`](core/bayesian_trust_tracker.py:1).
*   **Output:**
    *   Mutates the passed-in [`WorldState`](simulation_engine/worldstate.py:471) object.
    *   Logs events to the standard Python `logging` system (logger name: "causal_rules").
    *   Writes to the Pulse learning log via [`core.pulse_learning_log.log_bayesian_trust_metrics()`](core/pulse_learning_log.py:307).

## Function and Class Example Usages

**1. `apply_rule(state: WorldState, rule_id: str, condition_func, effect_func) -> bool`**
   This is a core helper function used internally by [`apply_causal_rules()`](simulation_engine/causal_rules.py:143).
   ```python
   # (Inside apply_causal_rules)
   # Example for R001_HopeTrust
   triggered = apply_rule(
       state, 
       "R001_HopeTrust",
       lambda s: get_overlay(s, "hope") > CONFIDENCE_THRESHOLD and get_overlay(s, "fatigue") < DEFAULT_FRAGILITY_THRESHOLD,
       lambda s, mod: (
           adjust_overlay(s, "trust", +0.02 * mod),
           update_numeric_variable(s, "hope_surge_count", +1, max_val=100),
           s.log_event(f"SYMBOLIC: hope → trust (tag: optimism) [mod={mod:.2f}]")
       )
   )
   if triggered:
       activated_rules.append("R001_HopeTrust")
   ```

**2. `apply_causal_rules(state: WorldState) -> List[str]`**
   This is the main function to execute all defined causal rules.
   ```python
   # Assuming 'current_world_state' is an instance of WorldState
   activated_rule_ids = apply_causal_rules(current_world_state)
   print(f"Activated rules this turn: {activated_rule_ids}")
   # current_world_state is now mutated based on triggered rules.
   ```

**3. `generate_rule_statistics() -> dict`**
   This function compiles statistics about each rule's performance using the Bayesian trust tracker.
   ```python
   rule_stats = generate_rule_statistics()
   for rule_id, stats in rule_stats.items():
       print(f"Rule: {rule_id} ({stats['description']})")
       print(f"  Trust: {stats['trust']:.2f}, Confidence: {stats['confidence']:.2f}, Samples: {stats['sample_size']}")
   ```

## Hardcoding Issues (SPARC Critical)

*   **Rule Definitions (`RULES` dictionary):** The entire set of causal rules, including their IDs, descriptions, categories, importance scores, conditions, and effects, is hardcoded directly in the [`RULES`](simulation_engine/causal_rules.py:22) dictionary and within the [`apply_causal_rules()`](simulation_engine/causal_rules.py:143) function's logic. This makes adding, removing, or modifying rules cumbersome and error-prone, requiring direct code changes.
    *   Example: Rule definitions from lines [`23-97`](simulation_engine/causal_rules.py:23-97).
    *   Example: Rule application logic, like for `R001_HopeTrust`, from lines [`153-163`](simulation_engine/causal_rules.py:153-163).
*   **Magic Numbers/Strings in Rule Logic:**
    *   Thresholds for overlay values (e.g., `get_overlay(s, "despair") > 0.6` in [`R002_DespairFatigue`](simulation_engine/causal_rules.py:168)). While some thresholds like [`CONFIDENCE_THRESHOLD`](core/pulse_config.py:42) are imported, others are directly embedded.
    *   Delta values for adjustments (e.g., `+0.02 * mod` for trust in [`R001_HopeTrust`](simulation_engine/causal_rules.py:158)).
    *   Asset names like "nvda", "ibit", "msft", "spy" are hardcoded in capital adjustment rules (e.g., [`R004_TrustCapital`](simulation_engine/causal_rules.py:192), [`R005_FatigueCapital`](simulation_engine/causal_rules.py:203), [`R012_FedRateEffect`](simulation_engine/causal_rules.py:285)).
    *   Symbolic tags like `"(tag: optimism)"` in [`R001_HopeTrust`](simulation_engine/causal_rules.py:160).
*   **Logger Name:** The logger name `"causal_rules"` is hardcoded ([`line 19`](simulation_engine/causal_rules.py:19)). This is minor but could be made configurable if needed.

## Coupling Points (Modularity/Architecture)

*   **Tight Coupling to `WorldState` Structure:** The module is tightly coupled to the specific structure of the [`WorldState`](simulation_engine/worldstate.py:471) object and its sub-objects (`overlays`, `capital`, `variables`). Changes in [`WorldState`](simulation_engine/worldstate.py:471) would likely require changes here.
*   **Direct Calls to Mutation Functions:** It directly calls functions from [`engine.state_mutation`](simulation_engine/state_mutation.py:1) (e.g., [`adjust_overlay()`](simulation_engine/state_mutation.py:94), [`adjust_capital()`](simulation_engine/state_mutation.py:151)).
*   **Dependency on `core` Modules:** Strong dependencies on several `core` modules:
    *   [`core.variable_accessor`](core/variable_accessor.py:1) for getting variable and overlay values.
    *   [`core.pulse_config`](core/pulse_config.py:1) for global thresholds.
    *   [`core.pulse_learning_log`](core/pulse_learning_log.py:1) and [`core.bayesian_trust_tracker`](core/bayesian_trust_tracker.py:1) for rule performance tracking and trust modulation. Changes in the APIs of these modules would directly impact `causal_rules.py`.
*   **Hardcoded Rule Logic:** As mentioned, the rule logic (conditions and effects) is hardcoded within lambda functions in [`apply_causal_rules()`](simulation_engine/causal_rules.py:143), creating a tight coupling between the rule definition and its implementation.

## Existing Tests (SPARC Refinement)

No inline tests (e.g., doctests or a `if __name__ == "__main__":` block with test calls) are present within this module. The existence and coverage of external unit tests in a dedicated test suite (e.g., in the `tests/` directory) cannot be determined from this file alone. Given the critical nature of the rule engine, comprehensive testing is essential.

## Module Architecture and Flow (SPARC Architecture)

1.  **Rule Definitions (`RULES`):** A dictionary stores metadata (description, category, importance) for each rule, identified by a unique rule ID.
2.  **`apply_rule()` Function:**
    *   Takes a [`WorldState`](simulation_engine/worldstate.py:471), `rule_id`, a `condition_func`, and an `effect_func`.
    *   Checks if the rule ID is known.
    *   Evaluates `condition_func(state)`. If false, logs and returns.
    *   Retrieves the rule's trust score from [`bayesian_trust_tracker`](core/bayesian_trust_tracker.py:213) and its predefined importance.
    *   Calculates a `modulation` factor (`trust * importance`).
    *   Calls `effect_func(state, modulation)` to apply the rule's effects, scaled by the modulation factor.
    *   Logs the rule trigger and updates Bayesian trust metrics via [`log_bayesian_trust_metrics()`](core/pulse_learning_log.py:307).
    *   Includes basic error handling for exceptions during effect application.
3.  **`apply_causal_rules()` Function:**
    *   Iterates through a predefined sequence of rule applications.
    *   For each rule, it calls [`apply_rule()`](simulation_engine/causal_rules.py:100) with specific lambda functions defining the condition and effect.
    *   Conditions typically involve checking overlay values against thresholds (e.g., `get_overlay(s, "hope") > CONFIDENCE_THRESHOLD`) or variable values (e.g., `get_variable(s, "inflation_index") > 0.05`).
    *   Effects involve calling mutation functions from [`engine.state_mutation`](simulation_engine/state_mutation.py:1) (e.g., [`adjust_overlay()`](simulation_engine/state_mutation.py:94), [`update_numeric_variable()`](simulation_engine/state_mutation.py:27), [`adjust_capital()`](simulation_engine/state_mutation.py:151)) and logging symbolic tags.
    *   Collects and returns a list of activated rule IDs.
4.  **`generate_rule_statistics()` Function:**
    *   Iterates through the `RULES` dictionary.
    *   For each rule, it fetches trust, confidence strength, sample size, and confidence interval from the [`bayesian_trust_tracker`](core/bayesian_trust_tracker.py:213).
    *   Compiles these statistics along with rule metadata into a dictionary.

The flow is sequential within [`apply_causal_rules()`](simulation_engine/causal_rules.py:143), with each rule being checked and potentially applied in a fixed order. The effect of one rule can influence the conditions for subsequent rules within the same turn.

## Naming Conventions (SPARC Maintainability)

*   **Constants:** `RULES`, [`CONFIDENCE_THRESHOLD`](core/pulse_config.py:42), [`DEFAULT_FRAGILITY_THRESHOLD`](core/pulse_config.py:43) are in `UPPER_SNAKE_CASE`, which is good.
*   **Functions:** [`apply_rule()`](simulation_engine/causal_rules.py:100), [`apply_causal_rules()`](simulation_engine/causal_rules.py:143), [`generate_rule_statistics()`](simulation_engine/causal_rules.py:327) use `snake_case`, which is Pythonic.
*   **Variables:** Local variables like `state`, `rule_id`, `condition_func`, `effect_func`, `trust`, `importance`, `modulation`, `activated_rules` are clear and use `snake_case`.
*   **Rule IDs:** Rule IDs like `"R001_HopeTrust"` use a prefix (`R###`) followed by a descriptive `PascalCase` name, which is reasonably clear.
*   **Symbolic Tags:** Tags like `"(tag: optimism)"` are embedded in log strings.
*   **Clarity:** Function and variable names are generally descriptive and convey their purpose well.
*   **Docstrings:** The module and its public functions have docstrings, although the function docstrings could be more detailed regarding specific interactions with `WorldState` components or the Bayesian trust tracker.

## SPARC Compliance Summary

*   **Specification:** The module's purpose is clearly defined in its docstring. The rules themselves have descriptions.
*   **Modularity/Architecture:**
    *   The module encapsulates rule application logic.
    *   However, it's tightly coupled to `WorldState` and other `core` modules.
    *   The hardcoding of rules and their logic within the main application function ([`apply_causal_rules()`](simulation_engine/causal_rules.py:143)) reduces modularity and makes extensions difficult without code modification.
*   **Refinement Focus:**
    *   **Testability:** Lack of inline tests is a concern. The design with lambda functions for conditions/effects might make unit testing of individual rule components slightly more complex than if they were separate, named functions.
    *   **Security (No Hardcoding):**
        *   **CRITICAL:** Significant hardcoding of rule definitions, thresholds (some), effect magnitudes, asset names, and symbolic tags. This violates the "No Hardcoding" principle and makes the system rigid.
        *   No direct hardcoding of secrets, API keys, or sensitive file paths was observed *within this module*. However, it relies on [`core.path_registry`](core/path_registry.py:1) for some path definitions, and the security of those paths depends on that module.
    *   **Maintainability:**
        *   Naming conventions are generally good.
        *   Code clarity is reasonable for the current complexity.
        *   Documentation (docstrings) is present but could be improved for specific functions.
        *   The primary maintainability issue is the hardcoding of rules, which would make updates and debugging challenging as the number of rules grows.
*   **Overall SPARC Compliance:**
    *   **Strengths:** Clear intent, basic logging, integration with a trust tracking mechanism.
    *   **Weaknesses (SPARC Violations):**
        *   **Significant Hardcoding:** Rule definitions, logic, and many parameters are hardcoded. This is the most critical SPARC violation.
        *   **Modularity:** Could be improved by decoupling rule definitions from application logic.
        *   **Testability:** Needs explicit and comprehensive tests.

This module forms a critical part of the simulation but would benefit significantly from refactoring to address the hardcoding and improve modularity and testability, aligning it more closely with SPARC principles.