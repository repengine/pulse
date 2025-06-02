# Module Analysis: `rules/engine.py` (or enhanced `simulation_engine/rule_engine.py`)

## 1. Module Intent/Purpose

The module [`rules/engine.py`](rules/engine.py) (or the enhanced version of [`simulation_engine/rule_engine.py`](simulation_engine/rule_engine.py)) is the core execution component for the declarative causal rules defined in Pulse v0.10. Its primary responsibility is to take `Rule` objects (parsed from YAML via [`rules/loader.py`](rules/loader.py) and defined by [`rules/schemas.py`](rules/schemas.py)), evaluate their conditions against the current `WorldStateV2`, and apply their effects if the conditions are met. It maintains compatibility with the existing rule engine interface where possible.

## 2. Key Functionalities

*   **Rule Execution Loop (`run_rules` or similar function):**
    *   Accepts a `WorldStateV2` object.
    *   Retrieves active, Pydantic-based `Rule` objects (likely via `RuleRegistry`).
    *   Iterates through rules (potentially considering `priority`).
*   **Declarative Condition Evaluation:**
    *   Parses the `conditions: list[ConditionComponent]` from each `Rule`.
    *   Dynamically accesses `WorldStateV2` attributes based on `variable_path` in each `ConditionComponent`.
    *   Applies the specified `operator` (e.g., "gt", "eq", "lt") with the given `value`.
    *   Handles logical grouping of conditions (e.g., all conditions must be true - AND logic).
*   **Declarative Effect Application:**
    *   If all conditions for a rule are met, parses the `effects: list[EffectComponent]` from the `Rule`.
    *   Dynamically modifies `WorldStateV2` attributes based on `action` (e.g., "set_variable", "adjust_variable") and `target_path` in each `EffectComponent`.
*   **Auditing:**
    *   Integrates with the existing audit mechanism ([`simulation_engine/rules/rule_audit_layer.py`](simulation_engine/rules/rule_audit_layer.py)) or an enhanced version to log triggered rules and their impact on `WorldStateV2`.
    *   The audit log structure should be consistent with previous versions.
*   **Error Handling:** Manages errors during condition evaluation or effect application for individual rules, ensuring the engine can continue processing other rules if appropriate.

## 3. Operational Status/Completeness

This module (or the significant enhancement of the existing one) is a key development item for Pulse v0.10. The logic for interpreting and executing declarative rules is the most complex part of the new causal rule subsystem.

## 4. Connections & Dependencies

*   **`rules.schemas.Rule`**: Consumes `Rule` objects.
*   **`core.worldstate_v2.WorldStateV2`**: Reads from and mutates `WorldStateV2` instances.
*   **`engine.rules.rule_registry`**: To obtain the rules to be executed.
*   **`engine.rules.rule_audit_layer`**: For logging rule activations and changes.
*   May require utility functions for dynamic attribute access and type conversion based on `variable_path`, `target_path`, and `value_type` specified in conditions/effects.

*(Further details to be added as development progresses.)*