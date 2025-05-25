# Module Analysis: `rules/schemas.py`

## 1. Module Intent/Purpose

The module [`rules/schemas.py`](rules/schemas.py) defines the Pydantic data models for the causal rule subsystem. These schemas ensure that rules loaded from YAML files (or other sources) are well-structured and validated. They provide a clear contract for what constitutes a rule, its conditions, and its effects within the Pulse v0.10 system.

## 2. Key Pydantic Models

*   **`ConditionComponent`**: Defines the structure for a single piece of a rule's condition.
    *   Example fields: `variable_path: str` (e.g., "worldstate.metrics.inflation"), `operator: str` (e.g., "gt", "lt", "eq"), `value: Any`, `value_type: str` (e.g., "float", "int", "str").
    *   May include support for comparing against other `WorldState` variables.
*   **`EffectComponent`**: Defines the structure for a single action a rule can take.
    *   Example fields: `action: str` (e.g., "set_variable", "adjust_variable", "log_event"), `target_path: str` (e.g., "worldstate.actions.interest_rate_delta"), `value: Any` (for set) or `delta: Any` (for adjust), `value_type: str`.
*   **`Rule`**: The main model representing a causal rule.
    *   Fields:
        *   `id: str` (Unique identifier for the rule)
        *   `description: str` (Human-readable description)
        *   `priority: int = 0` (For ordering rule execution if needed)
        *   `source: str` (Origin of the rule, e.g., "core_ruleset_v1")
        *   `enabled: bool = True` (Whether the rule is active)
        *   `conditions: list[ConditionComponent]` (A list of conditions, typically ANDed together, though OR groups could be an extension)
        *   `effects: list[EffectComponent]` (A list of effects to apply if conditions are met)

## 3. Operational Status/Completeness

This module is newly introduced in Pulse v0.10. Its Pydantic models will be defined and refined as part of this version's development.

## 4. Connections & Dependencies

*   **Pydantic**: Heavily reliant on Pydantic for model definition and validation.
*   **`rules/loader.py`**: The loader will use these schemas to parse and validate YAML rule definitions.
*   **`rules/engine.py`** (or equivalent): The rule engine will consume instances of these Pydantic models to execute rules.
*   **`core.worldstate_v2`**: The `variable_path` and `target_path` fields in conditions/effects will refer to paths within `WorldStateV2`.

*(Further details to be added as development progresses.)*