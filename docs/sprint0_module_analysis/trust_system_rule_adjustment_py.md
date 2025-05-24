# Analysis of trust_system/rule_adjustment.py

## 1. Module Intent/Purpose

The primary role of `trust_system/rule_adjustment.py` is to adapt the Pulse system's rules and symbolic interpretations based on learned performance. It takes a `learning_profile` (presumably containing performance metrics for symbolic arcs and tags) and adjusts the \"trust weights\" associated with them. This mechanism allows the system to self-correct or refine its internal models over time.

Key responsibilities include:
-   Processing a `learning_profile` that contains performance data (e.g., \"win rates\") for symbolic arcs and tags.
-   Adjusting the trust scores of rules associated with these arcs. If an arc performs poorly (low win rate), the trust in rules associated with that arc is decreased. If it performs well (high win rate), trust is increased.
-   Adjusting the trust weights associated with symbolic tags. Similar to arcs, if a tag is associated with poor performance, its trust weight is decreased, and vice-versa.
-   Persisting these trust weight changes:
    -   For arcs, it updates the trust score directly in the `RuleRegistry` (assuming arcs can be mapped to rule IDs or that `update_trust_score` can handle arc names).
    -   For tags, it registers/updates a special variable in the `VariableRegistry` (e.g., `tag_weight_fear`) and also adjusts the trust scores of all rules associated with that tag in the `RuleRegistry`.
-   Logging these weight changes using [`core.pulse_learning_log.log_variable_weight_change()`](core/pulse_learning_log.py:1).

## 2. Operational Status/Completeness

The module appears to be a functional implementation of a rule/tag trust adjustment mechanism based on performance feedback.
-   **Core Logic:** The core logic of iterating through arc and tag performance data and applying adjustments based on thresholds (0.3 and 0.8 win rates) is implemented.
-   **Registry Interaction:** It correctly interacts with `RuleRegistry` to load rules and update trust scores, and with `VariableRegistry` to store tag-specific trust weights.
-   **Logging:** It logs weight changes, which is important for traceability and understanding system evolution.

However, there are aspects that suggest it might be an \"example\" or a foundational implementation:
-   The docstring for [`adjust_rules_from_learning()`](trust_system/rule_adjustment.py:5) mentions \"Example: adjust trust for arcs\" and \"Example: adjust trust for tags,\" implying the current logic might be illustrative.
-   The adjustment deltas (`-0.1`, `+0.1` for arcs; `-0.05`, `+0.05` for tag-based rule updates) are hardcoded.

## 3. Implementation Gaps / Unfinished Next Steps

-   **Signs of Intended Extension:**
    -   **Sophistication of Adjustments:** The current adjustment logic is simple (fixed deltas based on hardcoded win rate thresholds). A more advanced system might use more nuanced calculations for `new_weight` (e.g., proportional to the deviation from a target win rate, incorporating learning rates, momentum, or Bayesian updating).
    -   **Definition of \"Learning Profile\":** The structure and origin of the `learning_profile` input are not defined within this module. It's assumed to be a dictionary with `\"arc_performance\"` and `\"tag_performance\"` keys, each containing items with `\"rate\"` and `\"weight\"` keys.
    -   **Persistence of `RuleRegistry` Changes:** The module calls `rule_registry.update_trust_score()`. It's crucial that the `RuleRegistry` itself has a mechanism to persist these changes if they are intended to be permanent across sessions. The `RuleRegistry` code ([`simulation_engine/rules/rule_registry.py`](simulation_engine/rules/rule_registry.py:1)) has an `export_rules` method but doesn't automatically save on every `update_trust_score` call. This module doesn't explicitly save the `RuleRegistry` state after modifications.
    -   **Persistence of `VariableRegistry` Changes:** Similarly, while `variable_registry.register_variable()` is called, the persistence of the `VariableRegistry` (e.g., `configs/variable_registry.json`) is handled within the `VariableRegistry` class itself (via its `_save` method, which is called by `register_variable`).
-   **Implied but Missing Features/Modules:**
    -   **Learning Profile Generator:** A module or system that generates the `learning_profile` based on actual forecast outcomes and system performance is a critical upstream dependency.
    -   **Tag Registry:** The code mentions \"Persist new_weight to tag registry\" in comments ([`trust_system/rule_adjustment.py:39`](trust_system/rule_adjustment.py:39), [`trust_system/rule_adjustment.py:60`](trust_system/rule_adjustment.py:60)), but then proceeds to store tag weights in the `VariableRegistry`. If a dedicated \"tag registry\" for managing trust weights of tags was intended, it's not implemented here. The current approach of using `VariableRegistry` is viable but might be less direct if tags are first-class citizens in the trust model.
    -   **Arc-to-Rule Mapping:** The code `rule_registry.update_trust_score(arc, -0.1)` ([`trust_system/rule_adjustment.py:25`](trust_system/rule_adjustment.py:25)) implies that `arc` (an arc label string) can be used as an identifier in `update_trust_score`. The `RuleRegistry.update_trust_score` method typically expects a `rule_id`. This suggests either `arc` is a `rule_id` or `update_trust_score` needs to be able to resolve arc labels to affected rules, or this part of the logic is simplified.
-   **Indications of Deviated/Stopped Development:**
    -   The \"Example:\" comments and hardcoded adjustment values suggest this might be a proof-of-concept or an initial version that could be expanded. It's functional but lacks the configurability and sophistication one might expect in a mature learning component.

## 4. Connections & Dependencies

-   **Direct Imports from Other Project Modules:**
    -   From [`core.pulse_learning_log`](core/pulse_learning_log.py:1): [`log_variable_weight_change()`](core/pulse_learning_log.py:1).
    -   From [`simulation_engine.rules.rule_registry`](simulation_engine/rules/rule_registry.py:2): [`RuleRegistry`](simulation_engine/rules/rule_registry.py:31) class.
    -   From [`core.variable_registry`](core/variable_registry.py:3): `registry` (imported as `variable_registry`).
-   **External Library Dependencies:**
    -   None directly, but dependencies of imported modules apply (e.g., `RuleRegistry` uses `json`, `pathlib`, `importlib`).
-   **Interaction with Other Modules (Implied):**
    -   **Learning System:** Depends on an upstream system to generate the `learning_profile`.
    -   **Rule Execution Engine ([`simulation_engine.rule_engine`](simulation_engine/rule_engine.py:1)):** The adjustments made by this module to rule trust weights in `RuleRegistry` would affect how the rule engine prioritizes or uses rules in subsequent simulations.
    -   **Variable Consumers:** Any part of the system that reads `tag_weight_*` variables from the `VariableRegistry` would be affected by the adjustments made here.
-   **Input/Output Files:**
    -   **Input:** Implicitly reads rule definitions when `RuleRegistry().load_all_rules()` is called (from `simulation_engine/rules/static_rules.py`, `simulation_engine/rules/rule_fingerprints.json`, `data/candidate_rules.json`). It also reads the `VariableRegistry`'s persisted state (e.g., `configs/variable_registry.json`).
    -   **Output:**
        -   Modifies the in-memory state of `rule_registry` and `variable_registry`.
        -   Persistence of these changes depends on the save mechanisms within `RuleRegistry` and `VariableRegistry`. `VariableRegistry` saves on `register_variable`. `RuleRegistry` would need an explicit save call.
        -   Writes to the learning log via [`log_variable_weight_change()`](core/pulse_learning_log.py:1).

## 5. Function and Class Example Usages

-   **Adjusting rules based on a learning profile:**
    ```python
    from trust_system.rule_adjustment import adjust_rules_from_learning

    # Example learning profile structure
    mock_learning_profile = {
        \"arc_performance\": {
            \"Hope_Arc_Positive_Outcome\": {\"rate\": 0.9, \"weight\": 0.8}, # Good performance
            \"Despair_Arc_Negative_Outcome\": {\"rate\": 0.2, \"weight\": 0.7} # Poor performance
        },
        \"tag_performance\": {
            \"optimism_tag\": {\"rate\": 0.85, \"weight\": 0.9},
            \"market_crash_warning_tag\": {\"rate\": 0.15, \"weight\": 0.6}
        }
    }

    # This function will load rules, adjust weights, and log changes.
    # Note: For changes to persist across sessions, RuleRegistry might need explicit saving.
    adjust_rules_from_learning(mock_learning_profile)
    ```

## 6. Hardcoding Issues

-   **Performance Thresholds:** The win rate thresholds (0.3 for downgrade, 0.8 for upgrade) are hardcoded.
-   **Adjustment Deltas:** The amounts by which trust weights are adjusted (+/- 0.1 for arcs, +/- 0.05 for tag-related rule updates) are hardcoded.
-   **Tag Weight Variable Prefix:** The prefix `\"tag_weight_\"` for storing tag trust weights in the `VariableRegistry` is hardcoded.
-   **Default Weights in Profile:** The code assumes `learning_profile` entries have a `\"weight\"` key and defaults to `1.0` if missing. This default might not always be appropriate.
    -   **Pros:** Simplicity for the current implementation.
    -   **Cons:** Reduces flexibility and adaptability. Optimal thresholds and adjustment magnitudes might vary or need tuning.
    -   **Mitigation/Recommendation:** These values should ideally be configurable, possibly loaded from `core.pulse_config` or passed as parameters to [`adjust_rules_from_learning()`](trust_system/rule_adjustment.py:5).

## 7. Coupling Points

-   **`learning_profile` Structure:** Tightly coupled to the expected dictionary structure of `learning_profile` and its nested keys (`\"arc_performance\"`, `\"tag_performance\"`, `\"rate\"`, `\"weight\"`).
-   **[`RuleRegistry`](simulation_engine/rules/rule_registry.py:31):** Relies on `RuleRegistry` methods like `load_all_rules()`, `update_trust_score()`, and `get_rules_by_symbolic_tag()`. Changes to these methods' signatures or behavior could break this module. The assumption about `update_trust_score` accepting arc labels as `rule_id` is a potential point of fragility if not explicitly supported by `RuleRegistry`.
-   **[`VariableRegistry`](core/variable_registry.py:3):** Relies on `variable_registry.register_variable()` for storing tag trust weights.
-   **[`core.pulse_learning_log`](core/pulse_learning_log.py:1):** Depends on [`log_variable_weight_change()`](core/pulse_learning_log.py:1) for logging.

## 8. Existing Tests

-   No inline `if __name__ == \"__main__\":` test block or dedicated test files are apparent for this module from the provided content.
-   **Assessment:** The module lacks explicit tests.
-   **Recommendation:** Create a dedicated test file (e.g., `tests/trust_system/test_rule_adjustment.py`).
    -   Mock `RuleRegistry`, `VariableRegistry`, and `log_variable_weight_change`.
    -   Test with various `learning_profile` inputs to ensure:
        -   Correct identification of underperforming/overperforming arcs and tags.
        -   Correct calculation of `new_weight`.
        -   Appropriate calls to `rule_registry.update_trust_score` with correct identifiers and deltas.
        -   Correct registration of `tag_weight_*` variables in `variable_registry` with proper metadata.
        -   Correct logging calls.
    -   Test edge cases (e.g., empty `learning_profile`, missing keys, win rates at thresholds).

## 9. Module Architecture and Flow

-   **Single Function Module:** The core logic is encapsulated in the single function [`adjust_rules_from_learning()`](trust_system/rule_adjustment.py:5).
-   **Initialization within Function:** `RuleRegistry` is instantiated and rules are loaded *inside* this function each time it's called. This ensures it works with the latest rule set but might be inefficient if called very frequently with a large rule base, as rules would be reloaded repeatedly.
-   **Data Flow:**
    1.  Takes `learning_profile` as input.
    2.  Iterates through `arc_performance`.
        a.  Calculates `new_weight` based on `rate`.
        b.  Logs the change.
        c.  Calls `rule_registry.update_trust_score()` for the arc.
    3.  Iterates through `tag_performance`.
        a.  Calculates `new_weight` based on `rate`.
        b.  Logs the change.
        c.  Registers/updates a `tag_weight_{tag}` variable in `variable_registry`.
        d.  Iterates through rules associated with the tag and calls `rule_registry.update_trust_score()` for each rule.
-   **State Modification:** Modifies the state of the `rule_registry` and `variable_registry` instances it interacts with.

## 10. Naming Conventions

-   **Module Name:** `rule_adjustment.py` is clear.
-   **Function Name:** [`adjust_rules_from_learning()`](trust_system/rule_adjustment.py:5) is descriptive.
-   **Variable Names:** Generally clear and use `snake_case` (e.g., `learning_profile`, `arc_perf`, `win_rate`, `tag_var_name`).
-   **Overall:** Naming is consistent and Pythonic.