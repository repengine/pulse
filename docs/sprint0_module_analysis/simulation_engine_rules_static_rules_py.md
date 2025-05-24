# Module Analysis: `simulation_engine/rules/static_rules.py`

## 1. Module Intent/Purpose

The primary role of [`simulation_engine/rules/static_rules.py`](simulation_engine/rules/static_rules.py:) is to define and manage a basic registry of static causal rules used within the Pulse simulation environment. These rules dictate how different variables within the simulation state influence each other based on predefined conditions and effects. The module also provides a mechanism to initialize these rules with optional parameter overrides and to apply externally proposed modifications to the rule set.

## 2. Operational Status/Completeness

The module appears to be operational for its core purpose of defining and providing a list of static rules. It includes:
*   A function [`build_static_rules()`](simulation_engine/rules/static_rules.py:17) to construct the rule list.
*   Two example rules (`R001_EnergySpike`, `R002_TrustRebound`) demonstrating the rule structure.
*   Integration with an external mechanism ([`pipeline.rule_applier`](pipeline/rule_applier.py:)) to load and apply rule changes ([`simulation_engine/rules/static_rules.py:48-51`](simulation_engine/rules/static_rules.py:48-51)).

A commented-out import `from forecast_tags import ...` ([`simulation_engine/rules/static_rules.py:13`](simulation_engine/rules/static_rules.py:13)) suggests a potentially incomplete or deprecated feature related to forecast tagging. The current rule set is minimal and likely serves as a foundational placeholder.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Forecast Tagging:** The commented-out import `from forecast_tags import ...` ([`simulation_engine/rules/static_rules.py:13`](simulation_engine/rules/static_rules.py:13)) suggests that functionality related to `forecast_tags` might have been planned or partially implemented but is currently inactive.
*   **Limited Rule Set:** The module currently defines only two basic rules. For a comprehensive simulation, a significantly larger and more diverse set of rules would be necessary.
*   **External Rule Source Details:** While the module integrates `load_proposed_rule_changes()` ([`simulation_engine/rules/static_rules.py:15`](simulation_engine/rules/static_rules.py:15)), the specifics of where these changes originate (e.g., format, location beyond the hint of [`pipeline/rule_proposals/proposed_rule_changes.json`](pipeline/rule_proposals/proposed_rule_changes.json)) and the full capabilities of `apply_rule_changes()` ([`simulation_engine/rules/static_rules.py:15`](simulation_engine/rules/static_rules.py:15)) are not detailed within this module itself.
*   **Path Registry Usage:** The import of `PATHS` from [`core.path_registry`](core/path_registry.py:) ([`simulation_engine/rules/static_rules.py:12`](simulation_engine/rules/static_rules.py:12)) is present, but `PATHS` is not utilized in the provided code, suggesting it might be for future expansion or a remnant.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`core.pulse_config`](core/pulse_config.py:): Imports `CONFIDENCE_THRESHOLD`, `DEFAULT_FRAGILITY_THRESHOLD` ([`simulation_engine/rules/static_rules.py:10`](simulation_engine/rules/static_rules.py:10)).
*   [`core.variable_accessor`](core/variable_accessor.py:): Imports `get_variable()`, `set_variable()`, `get_overlay()` ([`simulation_engine/rules/static_rules.py:11`](simulation_engine/rules/static_rules.py:11)).
*   [`core.path_registry`](core/path_registry.py:): Imports `PATHS` ([`simulation_engine/rules/static_rules.py:12`](simulation_engine/rules/static_rules.py:12)) (currently unused).
*   [`pipeline.rule_applier`](pipeline/rule_applier.py:): Imports `load_proposed_rule_changes()`, `apply_rule_changes()` ([`simulation_engine/rules/static_rules.py:15`](simulation_engine/rules/static_rules.py:15)).

### External Library Dependencies:
*   None apparent beyond standard Python libraries.

### Interaction via Shared Data:
*   Interacts with the simulation state (referred to as `s` in lambda functions) by reading and writing variable values using `get_variable()` and `set_variable()`.
*   The `load_proposed_rule_changes()` function implies reading from an external data source, likely a JSON file such as [`pipeline/rule_proposals/proposed_rule_changes.json`](pipeline/rule_proposals/proposed_rule_changes.json), to get rule modifications.

### Input/Output Files:
*   **Input:** Potentially reads rule definitions or modifications from a file via `load_proposed_rule_changes()`.
*   **Output:** The primary output is the list of rule dictionaries returned by `build_static_rules()`.

## 5. Function and Class Example Usages

### `build_static_rules(param_overrides=None)`
This function constructs and returns the list of static rules.

*   **Default Usage:**
    ```python
    from simulation_engine.rules.static_rules import build_static_rules

    # Get the default set of static rules
    default_rules = build_static_rules()
    # 'default_rules' will contain the initial rules, potentially modified by proposed changes.
    ```

*   **Usage with Parameter Overrides:**
    The `param_overrides` argument allows modification of specific rule parameters (like `threshold` or `effect_size`) at runtime.
    ```python
    from simulation_engine.rules.static_rules import build_static_rules

    overrides = {
        "R001_EnergySpike": {
            "threshold": 0.75,  # Override default threshold for R001
            "effect_size": 0.02   # Override default effect_size for R001
        },
        "R002_TrustRebound": {
            "enabled": False     # This parameter is not directly handled by the override logic in the snippet
                                 # but illustrates the structure. The current override logic only fetches
                                 # 'threshold' and 'effect_size'.
        }
    }
    customized_rules = build_static_rules(param_overrides=overrides)
    # 'customized_rules' will have R001_EnergySpike's threshold and effect_size
    # updated if the override logic in build_static_rules is extended or if
    # these are the only parameters it's designed to override.
    # The current implementation only overrides 'threshold' and 'effect_size'.
    ```

## 6. Hardcoding Issues

*   **Rule IDs:** Strings like `"R001_EnergySpike"` ([`simulation_engine/rules/static_rules.py:25`](simulation_engine/rules/static_rules.py:25)) and `"R002_TrustRebound"` ([`simulation_engine/rules/static_rules.py:36`](simulation_engine/rules/static_rules.py:36)) are hardcoded.
*   **Default Thresholds/Effect Sizes:**
    *   The default threshold for `R002_TrustRebound` is `0.65` ([`simulation_engine/rules/static_rules.py:38`](simulation_engine/rules/static_rules.py:38), [`simulation_engine/rules/static_rules.py:40`](simulation_engine/rules/static_rules.py:40)).
    *   Default effect sizes (e.g., `0.01` for `R001` ([`simulation_engine/rules/static_rules.py:28`](simulation_engine/rules/static_rules.py:28), [`simulation_engine/rules/static_rules.py:30`](simulation_engine/rules/static_rules.py:30)) and `0.02` for `R002` ([`simulation_engine/rules/static_rules.py:39`](simulation_engine/rules/static_rules.py:39), [`simulation_engine/rules/static_rules.py:41`](simulation_engine/rules/static_rules.py:41))) are hardcoded as fallbacks if not overridden by `param_overrides` or defined in [`core.pulse_config`](core/pulse_config.py:).
*   **Variable Names:** Simulation variable names such as `"energy_price_index"`, `"inflation_index"`, `"public_trust_level"`, and `"ai_policy_risk"` are hardcoded as strings within the lambda functions defining rule conditions and effects ([`simulation_engine/rules/static_rules.py:29-30`](simulation_engine/rules/static_rules.py:29-30), [`simulation_engine/rules/static_rules.py:40-41`](simulation_engine/rules/static_rules.py:40-41)).
*   **Symbolic Tags:** Lists of strings like `["fear", "despair"]` ([`simulation_engine/rules/static_rules.py:31`](simulation_engine/rules/static_rules.py:31)) and `["hope", "stability"]` ([`simulation_engine/rules/static_rules.py:42`](simulation_engine/rules/static_rules.py:42)) are hardcoded.
*   **Rule Types:** Strings like `"economic"` ([`simulation_engine/rules/static_rules.py:32`](simulation_engine/rules/static_rules.py:32)) and `"regulatory"` ([`simulation_engine/rules/static_rules.py:43`](simulation_engine/rules/static_rules.py:43)) are hardcoded.

## 7. Coupling Points

*   **Simulation State Structure:** Tightly coupled to the expected structure of the simulation state object (`s`) and the specific variable names accessible via `get_variable()` and `set_variable()`.
*   **`core.pulse_config`:** Relies on `CONFIDENCE_THRESHOLD` from [`core.pulse_config`](core/pulse_config.py:) as a default for rule thresholds.
*   **`pipeline.rule_applier`:** Depends on [`pipeline.rule_applier`](pipeline/rule_applier.py:) for the functionality of loading and applying external rule changes. Changes to the interface of these functions would directly impact this module.
*   **Rule Dictionary Structure:** The functionality of `build_static_rules()` and the processing by `apply_rule_changes()` depend on the specific keys and structure of the rule dictionaries (e.g., `id`, `threshold`, `effect_size`, `condition`, `effects`).

## 8. Existing Tests

Based on the provided workspace file list, a specific test file such as `tests/simulation_engine/rules/test_static_rules.py` does not appear to exist. Therefore, it's likely that there are no dedicated unit tests for this module in isolation. Broader integration tests might cover its functionality indirectly.

## 9. Module Architecture and Flow

1.  The primary function is [`build_static_rules(param_overrides=None)`](simulation_engine/rules/static_rules.py:17).
2.  Inside this function, an initial list of `rules` (each a dictionary) is defined.
    *   Each rule dictionary contains keys like `id`, `description`, `threshold`, `effect_size`, `condition` (a lambda function), `effects` (a lambda function), `symbolic_tags`, `type`, and `enabled`.
    *   Default values for `threshold` and `effect_size` are sourced from `param_overrides` if provided for a given rule ID; otherwise, they fall back to values from [`core.pulse_config`](core/pulse_config.py:) (e.g., `CONFIDENCE_THRESHOLD`) or hardcoded defaults within the rule definition itself.
3.  The function then calls `load_proposed_rule_changes()` from [`pipeline.rule_applier`](pipeline/rule_applier.py:) to fetch any external modifications to the rules ([`simulation_engine/rules/static_rules.py:49`](simulation_engine/rules/static_rules.py:49)).
4.  If `proposed_changes` are found, `apply_rule_changes()` (also from [`pipeline.rule_applier`](pipeline/rule_applier.py:)) is used to update the `rules` list with these changes ([`simulation_engine/rules/static_rules.py:51`](simulation_engine/rules/static_rules.py:51)).
5.  The final, potentially modified, list of `rules` is returned.

## 10. Naming Conventions

*   **Functions:** [`build_static_rules()`](simulation_engine/rules/static_rules.py:17) uses `snake_case`, adhering to PEP 8.
*   **Variables:** Local variables like `param_overrides`, `rules`, `proposed_changes` use `snake_case`.
*   **Dictionary Keys:** Keys within the rule dictionaries (e.g., `effect_size`, `symbolic_tags`, `ai_policy_risk`) consistently use `snake_case`.
*   **Rule IDs:** Rule identifiers like `R001_EnergySpike` use a PascalCase-like prefix (`R001`) followed by `_` and PascalCase, which is a consistent internal convention.
*   **Lambda Parameters:**
    *   `s`: Used to represent the simulation state in lambda functions. While concise, `state` could be more descriptive.
    *   `th`: Used for `threshold` in lambda functions.
    *   `eff`: Used for `effect_size` in lambda functions.
    These short names are generally understandable within the immediate context of the lambdas.
*   **Overall:** Naming is largely consistent and follows Python conventions. No significant deviations or potential AI assumption errors in naming are apparent.