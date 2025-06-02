# Module Analysis: `simulation_engine/rule_engine.py`

**SPARC Sprint 0 Codebase Analysis**

## 1. Module Intent/Purpose (Specification)

The primary purpose of the [`simulation_engine/rule_engine.py`](simulation_engine/rule_engine.py:1) module is to execute a set of predefined static causal rules against the current `WorldState` of the simulation. It mutates the `WorldState` based on the conditions and effects defined in these rules. The module also generates an audit trail of triggered rules, capturing changes to variables and overlays, which can be used for downstream processes like scoring, memory, and drift monitoring.

## 2. Operational Status/Completeness

The module appears to be operational and relatively complete for its defined scope.
- It loads rules using [`build_static_rules()`](simulation_engine/rules/static_rules.py:17).
- It iterates through rules, checks conditions, and applies effects.
- It logs rule execution and errors.
- It uses a `SymbolicBiasTracker` to record the usage of symbolic tags associated with rules.
- It generates an `execution_log` detailing triggered rules and their impact.

No obvious placeholders (e.g., `pass` statements in critical logic paths) or major TODOs are visible within this specific module's core logic.

## 3. Implementation Gaps / Unfinished Next Steps

- **Dynamic Rule Loading/Modification:** While [`static_rules.py`](simulation_engine/rules/static_rules.py:1) has a mechanism to load proposed rule changes via [`load_proposed_rule_changes()`](pipeline/rule_applier.py:6) and [`apply_rule_changes()`](pipeline/rule_applier.py:27) from [`pipeline/rule_applier.py`](pipeline/rule_applier.py:1), the `rule_engine.py` itself always calls [`build_static_rules()`](simulation_engine/rules/static_rules.py:17) without passing `param_overrides`. This suggests that dynamic rule parameterization or more sophisticated rule management might be planned but not fully integrated into the `run_rules` flow.
- **Error Handling Granularity:** The `try-except` block within the rule loop (lines 38-56 in [`simulation_engine/rule_engine.py`](simulation_engine/rule_engine.py:38)) catches generic `Exception`s. More specific error handling could be beneficial for robustness and debugging.
- **Verbose Flag Usage:** The `verbose` flag (line 18 in [`simulation_engine/rule_engine.py`](simulation_engine/rule_engine.py:18)) is used to log non-triggered rules. The utility and necessity of this in all contexts could be reviewed.

## 4. Connections & Dependencies

### Direct Imports (Project Modules):

-   [`engine.worldstate`](simulation_engine/worldstate.py:1): Provides the `WorldState` class, which is the central data structure the rule engine operates on.
-   [`engine.rules.static_rules`](simulation_engine/rules/static_rules.py:1): Provides the [`build_static_rules()`](simulation_engine/rules/static_rules.py:17) function to load the set of rules to be executed.
-   [`engine.rules.rule_audit_layer`](simulation_engine/rules/rule_audit_layer.py:1): Provides the [`audit_rule()`](simulation_engine/rules/rule_audit_layer.py:18) function to create detailed audit logs for triggered rules.
-   [`symbolic_system.symbolic_bias_tracker`](symbolic_system/symbolic_bias_tracker.py:1): Provides the `SymbolicBiasTracker` class used to record the frequency of symbolic tags associated with triggered rules.

### Direct Imports (External Libraries):

-   `copy`: Used for `deepcopy` to create a snapshot of the `WorldState` before applying rule effects, ensuring accurate auditing of changes.

### Touched Project Files (for dependency mapping):

To understand the full context and dependencies of [`simulation_engine/rule_engine.py`](simulation_engine/rule_engine.py:1), the following project files were read and analyzed:

1.  [`simulation_engine/rule_engine.py`](simulation_engine/rule_engine.py:1) (The module being analyzed)
2.  [`simulation_engine/worldstate.py`](simulation_engine/worldstate.py:1) (Defines `WorldState`, `SymbolicOverlays`, `CapitalExposure`, `Variables`)
3.  [`simulation_engine/rules/static_rules.py`](simulation_engine/rules/static_rules.py:1) (Defines [`build_static_rules()`](simulation_engine/rules/static_rules.py:17), imports from `core` and `pipeline`)
4.  [`simulation_engine/rules/rule_audit_layer.py`](simulation_engine/rules/rule_audit_layer.py:1) (Defines [`audit_rule()`](simulation_engine/rules/rule_audit_layer.py:18), imports `WorldState`)
5.  [`symbolic_system/symbolic_bias_tracker.py`](symbolic_system/symbolic_bias_tracker.py:1) (Defines `SymbolicBiasTracker`, imports from `core.path_registry`)
6.  [`core/pulse_config.py`](core/pulse_config.py:1) (Imported by [`simulation_engine/rules/static_rules.py`](simulation_engine/rules/static_rules.py:10), defines various configuration constants)
7.  [`core/variable_accessor.py`](core/variable_accessor.py:1) (Imported by [`simulation_engine/rules/static_rules.py`](simulation_engine/rules/static_rules.py:11), provides safe access to `WorldState` variables and overlays)
8.  [`core/path_registry.py`](core/path_registry.py:1) (Imported by [`simulation_engine/rules/static_rules.py`](simulation_engine/rules/static_rules.py:12) and [`symbolic_system/symbolic_bias_tracker.py`](symbolic_system/symbolic_bias_tracker.py:17), manages file paths)
9.  [`pipeline/rule_applier.py`](pipeline/rule_applier.py:1) (Imported by [`simulation_engine/rules/static_rules.py`](simulation_engine/rules/static_rules.py:15), handles loading and applying proposed rule changes)
10. [`core/variable_registry.py`](core/variable_registry.py:1) (Imported by [`core/variable_accessor.py`](core/variable_accessor.py:9), defines a registry of known variables)

### Interactions:

-   **`WorldState` Object:** The primary interaction is with the `WorldState` object. The [`run_rules()`](simulation_engine/rule_engine.py:18) function takes a `WorldState` instance as input, reads its properties (variables, overlays) to evaluate rule conditions, and mutates it by applying rule effects. It also calls [`state.log_event()`](simulation_engine/worldstate.py:520) to record rule triggers and errors.
-   **Rule Definitions:** Interacts with rule structures (dictionaries) provided by [`build_static_rules()`](simulation_engine/rules/static_rules.py:17). These rule dictionaries are expected to have "id", "condition" (a callable), "effects" (a callable), and optionally "enabled" and "symbolic_tags".
-   **Symbolic Bias Log File:** The `SymbolicBiasTracker` writes to a log file defined by `BIAS_LOG_PATH` in [`symbolic_system/symbolic_bias_tracker.py`](symbolic_system/symbolic_bias_tracker.py:20) (e.g., "logs/symbolic_bias_log.jsonl").

### Input/Output Files:

-   **Input:**
    -   Implicitly, through [`build_static_rules()`](simulation_engine/rules/static_rules.py:17) which calls [`load_proposed_rule_changes()`](pipeline/rule_applier.py:6), it might read rule changes from a JSON file (default: "pipeline/rule_proposals/proposed_rule_changes.json").
-   **Output:**
    -   The `SymbolicBiasTracker` appends to a JSONL file (e.g., "logs/symbolic_bias_log.jsonl") as defined in [`symbolic_system/symbolic_bias_tracker.py`](symbolic_system/symbolic_bias_tracker.py:20).

## 5. Function and Class Example Usages

**`run_rules(state: WorldState, verbose: bool = True) -> list[dict]`**

```python
from engine.worldstate import WorldState, Variables, SymbolicOverlays
from engine.rule_engine import run_rules

# Initialize a WorldState instance
current_state = WorldState()

# Set some initial variables that might trigger rules
# (assuming 'energy_price_index' and 'public_trust_level' are relevant for R001 and R002)
current_state.variables.data["energy_price_index"] = 0.7 # Example value
current_state.variables.data["inflation_index"] = 0.02    # Initial inflation
current_state.variables.data["public_trust_level"] = 0.7 # Example value
current_state.variables.data["ai_policy_risk"] = 0.5     # Initial AI policy risk

# Run the rule engine
triggered_audits = run_rules(state=current_state, verbose=True)

# Print the audit log of triggered rules
print("Triggered Rule Audits:")
for audit_entry in triggered_audits:
    print(audit_entry)

# Print changes to WorldState variables
print("\nWorldState Variables after rule execution:")
print(current_state.variables.as_dict())

# Print WorldState event log
print("\nWorldState Event Log:")
for event in current_state.event_log:
    print(event)
```

## 6. Hardcoding Issues (SPARC Critical)

-   **Log File Path in `SymbolicBiasTracker`:** The `BIAS_LOG_PATH` in [`symbolic_system/symbolic_bias_tracker.py`](symbolic_system/symbolic_bias_tracker.py:20) defaults to `"logs/symbolic_bias_log.jsonl"`. While it uses `PATHS.get()`, the fallback is a hardcoded string. This is a minor issue as `PATHS` provides a layer of indirection.
-   **Default Rule Change File Path:** The [`load_proposed_rule_changes()`](pipeline/rule_applier.py:6) function in [`pipeline/rule_applier.py`](pipeline/rule_applier.py:1) has a default `file_path` argument set to `"pipeline/rule_proposals/proposed_rule_changes.json"`. This is a direct dependency of `static_rules.py`, which `rule_engine.py` uses.

No other direct critical hardcoding (secrets, absolute paths for primary operations, API keys) was observed within `rule_engine.py` itself. The primary dependencies for file paths rely on [`core.path_registry`](core/path_registry.py:1).

## 7. Coupling Points

-   **`WorldState` Structure:** Tightly coupled to the structure of the `WorldState` object, specifically its `variables` and `overlays` attributes, and the `log_event` method. Changes to `WorldState`'s core design would directly impact this module.
-   **Rule Definition Format:** Depends on the dictionary structure of rules returned by [`build_static_rules()`](simulation_engine/rules/static_rules.py:17) (keys like "id", "condition", "effects", "symbolic_tags", "enabled").
-   **`SymbolicBiasTracker` API:** Coupled to the [`record()`](symbolic_system/symbolic_bias_tracker.py:27) method of the `SymbolicBiasTracker`.
-   **`audit_rule` Function Signature:** Coupled to the signature and return structure of the [`audit_rule()`](simulation_engine/rules/rule_audit_layer.py:18) function from [`rule_audit_layer.py`](simulation_engine/rules/rule_audit_layer.py:1).

## 8. Existing Tests (SPARC Refinement)

The provided context does not include information about specific tests for [`simulation_engine/rule_engine.py`](simulation_engine/rule_engine.py:1). A comprehensive test suite for this module would be crucial and should cover:
-   Rules triggering correctly based on `WorldState` conditions.
-   Rule effects correctly modifying `WorldState` variables and overlays.
-   Correct generation of `execution_log` entries by [`audit_rule()`](simulation_engine/rules/rule_audit_layer.py:18).
-   Correct interaction with `SymbolicBiasTracker`.
-   Handling of disabled rules.
-   Error handling when a rule's condition or effect functions raise exceptions.
-   Behavior with the `verbose` flag.
-   Edge cases, such as empty rule sets or `WorldState` with missing variables.

## 9. Module Architecture and Flow (SPARC Architecture)

The module defines a single primary function, [`run_rules()`](simulation_engine/rule_engine.py:18).
The architectural flow is as follows:
1.  Initialize `SymbolicBiasTracker`.
2.  The [`run_rules()`](simulation_engine/rule_engine.py:18) function is called with a `WorldState` object.
3.  It fetches the list of rules using [`build_static_rules()`](simulation_engine/rules/static_rules.py:17) (which itself might load and apply proposed changes from a file).
4.  It iterates through each rule:
    a.  Skips disabled rules.
    b.  Evaluates the rule's `condition` function against the current `WorldState`.
    c.  If the condition is true:
        i.  A deep copy of the `WorldState` is made (state_before).
        ii. The rule's `effects` function is called, mutating the `WorldState`.
        iii. [`audit_rule()`](simulation_engine/rules/rule_audit_layer.py:18) is called to generate an audit entry comparing `state_before` and the mutated `state_after`.
        iv. The audit entry is added to `execution_log`.
        v.  Symbolic tags from the rule are recorded by the `bias_tracker`.
        vi. An event is logged in the `WorldState`.
    d.  If the condition is false and `verbose` is true, an event is logged.
    e.  Any exceptions during condition evaluation or effect application are caught, and an error event is logged in the `WorldState`.
5.  The `execution_log` (a list of audit dictionaries) is returned.

The module is fairly modular, delegating rule loading, auditing, and bias tracking to other specialized modules. Its core responsibility is the orchestration of rule execution.

## 10. Naming Conventions (SPARC Maintainability)

-   **Module Name:** [`rule_engine.py`](simulation_engine/rule_engine.py:1) is clear and descriptive.
-   **Function Name:** [`run_rules()`](simulation_engine/rule_engine.py:18) is clear and indicates its action.
-   **Variable Names:**
    -   `state`: Clear, refers to `WorldState`.
    -   `rules`: Clear.
    -   `execution_log`: Clear.
    -   `state_before`, `state_after`: Clear in the context of auditing.
    -   `bias_tracker`: Clear.
-   **Docstrings:** The module and the [`run_rules()`](simulation_engine/rule_engine.py:18) function have docstrings explaining their purpose, arguments, and return values. The return structure for the audit log is also documented.

Overall, naming conventions are good and contribute to maintainability.

## 11. SPARC Compliance Summary

-   **Specification:** The module's purpose is well-defined in its docstring and adhered to in its implementation. It focuses on executing rules and auditing their impact.
-   **Modularity/Architecture:**
    -   The module exhibits good modularity by delegating tasks like rule definition ([`static_rules.py`](simulation_engine/rules/static_rules.py:1)), state representation ([`worldstate.py`](simulation_engine/worldstate.py:1)), auditing ([`rule_audit_layer.py`](simulation_engine/rules/rule_audit_layer.py:1)), and bias tracking ([`symbolic_bias_tracker.py`](symbolic_system/symbolic_bias_tracker.py:1)).
    -   The architecture is straightforward: load rules, iterate, check conditions, apply effects, audit.
-   **Refinement Focus:**
    -   **Testability:** While the code structure is amenable to testing, the absence of provided tests is a gap. Unit tests are essential.
    -   **Security (Hardcoding):** No critical hardcoding issues like secrets or API keys. File path management for logs and rule proposals is mostly handled via [`core.path_registry`](core/path_registry.py:1) or has configurable defaults, which is good. The default path in [`load_proposed_rule_changes()`](pipeline/rule_applier.py:6) is a minor point but acceptable for internal tooling.
    -   **Maintainability:** Code is clear, well-commented, and uses descriptive names. Docstrings are present. The use of `copy.deepcopy` for auditing is a good practice for ensuring accurate change tracking.
-   **No Hardcoding (Critical):** Compliant.

**Overall SPARC Assessment:**

The module is largely SPARC-compliant. Its main strengths are its clear specification, modular design, and good maintainability. The primary area for improvement under SPARC principles would be the explicit definition and integration of a comprehensive test suite. Further refinement could involve more granular error handling and potentially a more dynamic way to integrate rule parameter overrides if complex scenarios demand it.