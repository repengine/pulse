# Module Analysis: `simulation_engine/causal_rules.py`

## 1. Module Intent/Purpose

The module [`simulation_engine/causal_rules.py`](../../simulation_engine/causal_rules.py) serves as the unified causal rule engine for the Pulse simulation. Its primary responsibility is to define, manage, and apply a set of rules that dictate how the simulation's `WorldState` evolves. These rules handle transformations between symbolic states (e.g., "hope", "despair"), numeric variables (e.g., "inflation_index"), and capital asset values (e.g., "NVDA", "IBIT"). A key feature is the integration of a Bayesian trust mechanism, where the impact of each rule is modulated by its historical effectiveness and predefined importance. The module also includes functionality for symbolic tagging of rule applications for traceability and for generating statistics on rule performance.

## 2. Operational Status/Completeness

The module appears to be operational and largely complete for its defined scope as of "Pulse v0.4" (indicated by comments). It has a well-defined structure for:
*   Declaring rules with associated metadata.
*   A generic rule application function (`apply_rule`) that incorporates trust modulation.
*   A main function (`apply_causal_rules`) that orchestrates the application of all defined rules.
*   A utility to generate rule statistics (`generate_rule_statistics`).

There are no explicit "TODO" comments or obvious placeholders indicating unfinished critical functionality within the core logic. The comment "Author: Pulse v0.32" suggests it has been iterated upon.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Externalized Rule Definitions:** Rules are currently hardcoded within the `RULES` dictionary and the `apply_causal_rules` function. A more flexible system might load rules from external configuration files (e.g., JSON, YAML) or a database, allowing for easier updates and expansion without direct code modification.
*   **Automated Rule Generation/Discovery:** A comment on [line 150](../../simulation_engine/causal_rules.py:150) ("Remove all programmatically generated (AUTO_RULE) and placeholder rules. Only keep real, interpretable rules.") hints at a potential past or future capability for automatic rule generation, which is not implemented in the current version of this module.
*   **Dynamic Rule Adaptation:** While the module uses a `bayesian_trust_tracker` to modulate rule effects and logs metrics, there's no mechanism within this module itself to dynamically adapt the rules (e.g., change importance, retire ineffective rules, or auto-adjust thresholds) based on the generated statistics. This adaptation logic is likely handled by or intended for other parts of the system.
*   **Advanced Condition/Effect Logic:** The current rule conditions and effects are defined via lambda functions. For more complex rules, a more structured approach (e.g., dedicated classes per rule or a domain-specific language) might be beneficial.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`engine.worldstate.WorldState`](../../simulation_engine/worldstate.py)
*   [`engine.state_mutation.adjust_overlay`](../../simulation_engine/state_mutation.py:line)
*   [`engine.state_mutation.update_numeric_variable`](../../simulation_engine/state_mutation.py:line)
*   [`engine.state_mutation.adjust_capital`](../../simulation_engine/state_mutation.py:line)
*   [`core.variable_accessor.get_variable`](../../core/variable_accessor.py:line)
*   [`core.variable_accessor.get_overlay`](../../core/variable_accessor.py:line)
*   [`core.pulse_config.CONFIDENCE_THRESHOLD`](../../core/pulse_config.py:line)
*   [`core.pulse_config.DEFAULT_FRAGILITY_THRESHOLD`](../../core/pulse_config.py:line)
*   [`core.pulse_learning_log.log_bayesian_trust_metrics`](../../core/pulse_learning_log.py:line)
*   [`core.bayesian_trust_tracker.bayesian_trust_tracker`](../../core/bayesian_trust_tracker.py)

### External Library Dependencies:
*   `logging` (Python standard library)

### Interactions via Shared Data:
*   Modifies `WorldState` objects passed to its functions.
*   Relies on the external `bayesian_trust_tracker` for trust scores, implying shared state or a persistent data store managed by the tracker.

### Input/Output Files:
*   No direct file I/O for rule definitions.
*   Logs events and errors using the `logging` module, outputting to a configured destination.

## 5. Function and Class Example Usages

### `apply_causal_rules(state: WorldState)`
Executes all defined causal rules on the provided `WorldState` object, mutating it based on rule conditions and effects.
```python
from engine.worldstate import WorldState
from engine.causal_rules import apply_causal_rules

# Assuming 'current_world_state' is an initialized WorldState object
# current_world_state = WorldState()
# ... (initialize current_world_state with overlays, variables, capital) ...

activated_rules_list = apply_causal_rules(current_world_state)
print(f"Activated rules during this step: {activated_rules_list}")
# current_world_state is now updated based on the rules triggered.
```

### `apply_rule(state: WorldState, rule_id: str, condition_func, effect_func)`
A generic internal function to apply a single rule, including condition checking and trust modulation. It's primarily used by `apply_causal_rules`.

### `generate_rule_statistics() -> dict`
Retrieves and returns statistics for all defined rules from the `bayesian_trust_tracker`.
```python
from engine.causal_rules import generate_rule_statistics

rule_stats = generate_rule_statistics()
for rule_id, stats in rule_stats.items():
    print(f"Rule ID: {rule_id}")
    print(f"  Description: {stats['description']}")
    print(f"  Trust: {stats['trust']:.3f}")
    print(f"  Confidence: {stats['confidence']:.3f}")
    print(f"  Sample Size: {stats['sample_size']}")
```

## 6. Hardcoding Issues

*   **Rule Definitions:** The entire set of rules (IDs, descriptions, categories, importance values, conditions, and effects) is hardcoded in the `RULES` dictionary (lines [22-98](../../simulation_engine/causal_rules.py:22-98)) and within the lambda functions in `apply_causal_rules` (lines [152-324](../../simulation_engine/causal_rules.py:152-324)). This significantly hinders maintainability and extensibility.
*   **Magic Numbers:** Numerous numeric literals are used directly in rule conditions and effects (e.g., `0.02`, `100`, `0.6`, `0.015`, `500`, `-250`). These values lack descriptive names and make the rules harder to understand and adjust.
    *   Example: `adjust_overlay(s, "trust", +0.02 * mod)` ([line 158](../../simulation_engine/causal_rules.py:158)) - `0.02` is a magic number.
    *   Example: `get_overlay(s, "despair") > 0.6` ([line 168](../../simulation_engine/causal_rules.py:168)) - `0.6` is a magic number.
*   **Symbolic Tags & Identifiers:**
    *   Symbolic tags used in logging events (e.g., `"optimism"`) are hardcoded.
    *   Capital asset identifiers (e.g., `"nvda"`, `"ibit"`, `"msft"`, `"spy"`) are hardcoded strings.
    *   Names of symbolic overlays and numeric variables used in `get_overlay` and `get_variable` calls are hardcoded strings.

## 7. Coupling Points

*   **`WorldState` Object:** Tightly coupled to the specific structure, available overlays, numeric variables, and capital assets defined within the `WorldState` class.
*   **Internal Modules:**
    *   [`engine.state_mutation`](../../simulation_engine/state_mutation.py): For all state modifications.
    *   [`core.variable_accessor`](../../core/variable_accessor.py): For reading state.
    *   [`core.pulse_config`](../../core/pulse_config.py): For global simulation parameters like `CONFIDENCE_THRESHOLD`.
*   **`bayesian_trust_tracker`:** Critically dependent on this external component for rule trust scores, which directly influence rule impact. Changes to the tracker's API or behavior would significantly affect this module.
*   **`core.pulse_learning_log`:** For logging metrics essential for the `bayesian_trust_tracker`.
*   **Hardcoded Rule Logic:** The specific logic within each rule's condition and effect lambdas creates strong coupling. If the meaning or name of an overlay/variable changes, or if the expected range of values shifts, many rules might silently fail or behave incorrectly.

## 8. Existing Tests

*   The project structure includes a `tests/` directory.
*   A file named [`tests/test_causal_benchmarks.py`](../../tests/test_causal_benchmarks.py) exists, which may include tests related to the outcomes or performance of the causal rule system.
*   There is no specific file like `tests/test_causal_rules.py` apparent in the provided file listing. This suggests that dedicated unit tests for the individual rule logic, condition evaluations, effect applications, and the `apply_rule` function itself might be missing or integrated into broader tests.
*   Without examining the content of existing test files, the exact coverage and nature of tests for this module cannot be fully ascertained. Given the module's complexity and the number of distinct rules, comprehensive unit testing would be highly beneficial.

## 9. Module Architecture and Flow

The module operates based on the following architecture:

1.  **Rule Definition Store (`RULES`):** A global dictionary stores metadata for each rule (ID, description, category, importance).
2.  **Generic Rule Application (`apply_rule` function):**
    *   Validates the `rule_id`.
    *   Evaluates a `condition_func` based on the current `WorldState`.
    *   If the condition is met, it fetches a trust score for the rule from `bayesian_trust_tracker`.
    *   Calculates a `modulation` factor by combining the rule's `importance` and its current `trust` score.
    *   Executes an `effect_func`, passing the `WorldState` and the `modulation` factor, to apply the rule's consequences.
    *   Logs the event and relevant metrics for the Bayesian trust system.
3.  **Main Orchestration (`apply_causal_rules` function):**
    *   This function contains the explicit, hardcoded logic for applying each defined rule in sequence.
    *   For each rule, it calls `apply_rule` with specific lambda functions defining the precise conditions and effects on the `WorldState` (symbolic overlays, numeric variables, capital).
    *   It collects and returns a list of `rule_id`s that were activated.
4.  **Statistics Generation (`generate_rule_statistics` function):**
    *   Iterates through the defined `RULES`.
    *   For each rule, queries the `bayesian_trust_tracker` to get performance statistics (trust, confidence, sample size, confidence interval).
    *   Compiles and returns these statistics.

**Data Flow:**
*   **Input:** A `WorldState` object.
*   **Processing:**
    *   Reads current values of symbolic overlays and numeric variables from the `WorldState`.
    *   Evaluates rule conditions.
    *   If conditions are met, calculates modulated effects.
    *   Writes changes back to the `WorldState` by adjusting overlays, updating numeric variables, or modifying capital values.
    *   Interacts with `bayesian_trust_tracker` (read trust) and `core.pulse_learning_log` (write metrics).
*   **Output:**
    *   A mutated `WorldState` object.
    *   A list of `rule_id`s for rules that were triggered.
    *   Optionally, a dictionary of rule statistics via `generate_rule_statistics`.

## 10. Naming Conventions

*   **Functions and Variables:** Generally adhere to PEP 8 standards (e.g., `apply_causal_rules`, `rule_id`, `modulation_factor`).
*   **Constants:** Global constants like `RULES`, `CONFIDENCE_THRESHOLD` are in uppercase.
*   **Rule IDs:** Consistent pattern (e.g., `R001_HopeTrust`, `R015_EnergySpike`).
*   **Symbolic/Numeric Names:** Strings used for overlays ("hope", "trust"), variables ("inflation_index"), and capital ("nvda") are generally descriptive.
*   **Potential Issues/Deviations:**
    *   The "Author" in the module docstring is listed as "Pulse v0.32" ([line 8](../../simulation_engine/causal_rules.py:8)), which is unconventional and likely an AI artifact or placeholder.
    *   **Rule `R015_EnergySpike` ([line 93](../../simulation_engine/causal_rules.py:93)):**
        *   Its description "Hope builds trust based on trust score" is nearly identical to `R001_HopeTrust`'s intent.
        *   Its effect `adjust_overlay(s, "trust", +0.01 * mod)` also targets "trust".
        *   However, its condition `get_variable(s, "energy_price_index") > 1.5` seems unrelated to "hope" or "trust" directly.
        *   The log event `s.log_event(f"SYMBOLIC: hope builds trust based on trust score [mod={mod:.2f}]")` further reinforces the "hope/trust" theme.
        *   This suggests a potential copy-paste error during rule creation, a misnamed rule, or a rule with a mismatched description and condition. This specific rule definition appears problematic and may not function as intuitively expected.

Overall, naming conventions are largely consistent and follow Python best practices, with the notable exception of the `R015_EnergySpike` definition.