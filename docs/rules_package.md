# Module Analysis: `rules` (Package)

## 1. Module Intent/Purpose

The `rules` package is responsible for the new causal rule subsystem in Pulse v0.10. It defines the structure for declarative rules using Pydantic schemas, handles loading these rules from YAML definition files, and integrates with the rule execution engine. This package is central to the de-symbolized, causal-rule-driven architecture.

## 2. Key Components

*   **`rules/schemas.py`**: Defines Pydantic models for `Rule`, `ConditionComponent`, and `EffectComponent`.
*   **`rules/loader.py`**: Implements YAML loading functionality to parse rule definitions into Pydantic `Rule` objects.
*   **`rules/engine.py`** (or enhancements to `simulation_engine/rule_engine.py`): Responsible for interpreting and executing the declarative rules against `WorldStateV2`.
*   **`rules/definitions/`** (subdirectory): Contains the YAML files where actual rules are defined.

## 3. Operational Status/Completeness

This package is newly introduced in Pulse v0.10. Its components will be developed as part of this version.

## 4. Connections & Dependencies

*   **`simulation_engine.rule_engine` (or `rules.engine`)**: For executing the loaded rules.
*   **`simulation_engine.rules.rule_registry`**: For managing and providing access to the loaded rules.
*   **`core.worldstate_v2`**: The rules operate on and mutate `WorldStateV2` objects.
*   **Pydantic**: For schema definition and validation.
*   **PyYAML**: For loading rules from YAML files.

*(Further details to be added as development progresses.)*