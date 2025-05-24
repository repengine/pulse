# Module Analysis: simulation_engine/rule_engine.py

**Version:** As of commit/date relevant to sprint 0 analysis
**Author:** Pulse v0.20 (as per file header)
**Last Updated:** (Date of this analysis)

## 1. Module Intent/Purpose

The primary role of the [`rule_engine.py`](simulation_engine/rule_engine.py) module is to execute a predefined set of static causal rules against the current `WorldState` of a simulation. It is responsible for checking the conditions of these rules and, if met, applying their effects to mutate the `WorldState`. Additionally, it generates an audit trail of triggered rules, capturing details about the changes made.

## 2. Operational Status/Completeness

The module appears to be functionally complete for its core responsibility of iterating through static rules, evaluating conditions, applying effects, and logging outcomes. It includes basic error handling for rule execution and verbosity control for logging. There are no obvious `TODO` comments or incomplete `pass` statements within the main operational flow.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Dynamic Rule Loading:** The rules are currently sourced via [`build_static_rules()`](simulation_engine/rules/static_rules.py:0). If the system requires rules to be loaded dynamically, modified at runtime, or sourced from external configurations beyond the current static setup, this module (or its dependencies) would need significant extension.
*   **Advanced Error Handling:** The current error handling logs an event upon exception ([`simulation_engine/rule_engine.py:56`](simulation_engine/rule_engine.py:56)). More sophisticated mechanisms for error recovery, rule-specific error strategies, or halting/pausing the engine on critical failures might be beneficial in a more robust system.
*   **`SymbolicBiasTracker` Utility:** While [`SymbolicBiasTracker`](symbolic_system/symbolic_bias_tracker.py:0) is used to record tags from triggered rules ([`simulation_engine/rule_engine.py:51`](simulation_engine/rule_engine.py:51)), its full impact and how this bias information is utilized downstream is not evident from this module alone. Further exploration of its integration could reveal more about its intended completeness or potential extensions.
*   **Performance Considerations:** For a very large number of rules or a highly complex `WorldState`, the deepcopy operation ([`simulation_engine/rule_engine.py:40`](simulation_engine/rule_engine.py:40)) for auditing could become a performance bottleneck. Optimization strategies might be needed if this becomes an issue.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`simulation_engine.worldstate.WorldState`](simulation_engine/worldstate.py): Used as the primary data structure that rules operate upon.
*   [`simulation_engine.rules.static_rules.build_static_rules`](simulation_engine/rules/static_rules.py): Function to load the set of static rules.
*   [`simulation_engine.rules.rule_audit_layer.audit_rule`](simulation_engine/rules/rule_audit_layer.py): Used to create detailed audit logs for triggered rules.
*   [`symbolic_system.symbolic_bias_tracker.SymbolicBiasTracker`](symbolic_system/symbolic_bias_tracker.py): Used to track symbolic tags associated with triggered rules.

### External Library Dependencies:
*   `copy`: Standard Python library, specifically `copy.deepcopy()` is used for creating a snapshot of the `WorldState` before modifications.

### Interactions via Shared Data:
*   Modifies the `WorldState` object instance passed into [`run_rules()`](simulation_engine/rule_engine.py:18).
*   Reads rule definitions which are provided by the `static_rules` module.
*   Updates the shared (or globally accessible) `bias_tracker` instance.

### Input/Output Files:
*   **Input:** Indirectly consumes rule definitions, which might originate from files loaded by [`build_static_rules()`](simulation_engine/rules/static_rules.py:0).
*   **Output:** Does not directly write to files. However, it calls [`state.log_event()`](simulation_engine/worldstate.py:0), which implies that the `WorldState` object is responsible for handling the persistence or display of these log events (potentially to console or a log file). The returned `execution_log` could also be written to a file by the calling code.

## 5. Function and Class Example Usages

### `run_rules(state: WorldState, verbose: bool = True) -> list[dict]`

This is the core function of the module.

**Description:**
It takes the current simulation `WorldState` and an optional `verbose` flag. It iterates through all active rules loaded by [`build_static_rules()`](simulation_engine/rules/static_rules.py:0). For each rule, it checks if its `condition` (a callable function) evaluates to `True` given the current `state`. If true, the rule's `effects` (another callable function) are applied, modifying the `state`. An audit dictionary detailing the rule's activation and impact is generated and collected.

**Conceptual Usage:**

```python
from simulation_engine.worldstate import WorldState
from simulation_engine.rule_engine import run_rules

# Assume 'initial_state' is a properly initialized WorldState object
initial_state = WorldState(...) # Parameters depend on WorldState's __init__
initial_state.turn = 1 # Example: Set current turn

print(f"WorldState before rules: {initial_state.get_variable('some_var')}")

triggered_audits = run_rules(initial_state, verbose=True)

print(f"WorldState after rules: {initial_state.get_variable('some_var')}")

if triggered_audits:
    print("\nTriggered Rule Audits:")
    for audit_info in triggered_audits:
        print(f"  Rule ID: {audit_info['rule_id']}")
        print(f"    Timestamp: {audit_info['timestamp']}")
        print(f"    Symbolic Tags: {audit_info['symbolic_tags']}")
        print(f"    Variables Changed: {audit_info['variables_changed']}")
        # print(f"    Overlays Changed: {audit_info['overlays_changed']}") # If applicable
else:
    print("\nNo rules were triggered in this cycle.")

# Further processing of triggered_audits or the mutated initial_state
```

## 6. Hardcoding Issues

*   **Default Verbosity:** The `verbose` parameter in [`run_rules()`](simulation_engine/rule_engine.py:18) defaults to `True`. This could lead to extensive logging in environments where detailed rule checking logs are not always desired, potentially impacting performance or log readability if not explicitly set to `False`.
*   **Rule Dictionary Keys:** The module relies on specific string keys within the rule dictionaries (e.g., `"enabled"`, `"condition"`, `"effects"`, `"id"`, `"symbolic_tags"`). While this defines an implicit interface with [`static_rules`](simulation_engine/rules/static_rules.py:0), changes to these key names would require updates in both locations.
*   **Log Message Formats:** Log messages, such as `f"Rule triggered: {rule['id']} → tags={rule.get('symbolic_tags')}"` ([`simulation_engine/rule_engine.py:52`](simulation_engine/rule_engine.py:52)) and error messages ([`simulation_engine/rule_engine.py:56`](simulation_engine/rule_engine.py:56)), are hardcoded. Centralizing log message formats or using a more structured logging approach could improve maintainability.

## 7. Coupling Points

*   **`WorldState`:** Tightly coupled to the [`WorldState`](simulation_engine/worldstate.py:0) object's interface, including its attributes (e.g., `turn`) and methods (e.g., [`log_event()`](simulation_engine/worldstate.py:0), methods to get/set variables used by rule conditions/effects).
*   **`static_rules` Module:** Dependent on the structure and content of rules provided by [`build_static_rules()`](simulation_engine/rules/static_rules.py:0). The rule dictionaries must conform to the expected format (callable `condition` and `effects`, presence of `id`, optional `enabled` and `symbolic_tags`).
*   **`rule_audit_layer` Module:** Relies on [`audit_rule()`](simulation_engine/rules/rule_audit_layer.py:0) for creating the audit trail, coupling it to the signature and return structure of this function.
*   **`SymbolicBiasTracker`:** Coupled to the [`SymbolicBiasTracker`](symbolic_system/symbolic_bias_tracker.py:0) class and its [`record()`](symbolic_system/symbolic_bias_tracker.py:0) method.

## 8. Existing Tests

A review of the provided file list does not show a dedicated test file specifically for [`simulation_engine/rule_engine.py`](simulation_engine/rule_engine.py) (e.g., `tests/simulation_engine/test_rule_engine.py`).
*   There is a file [`tests/test_reverse_rule_engine.py`](tests/test_reverse_rule_engine.py:0), which seems to test a different, though related, concept.
*   **Potential Gap:** The absence of direct unit tests for `rule_engine.py` is a significant gap. Tests should cover various scenarios, including:
    *   Rules being enabled/disabled.
    *   Rules whose conditions are met/not met.
    *   Correct application of rule effects.
    *   Accurate audit log generation.
    *   Handling of exceptions during rule execution.
    *   Interaction with the `verbose` flag.
    *   Correct recording of symbolic tags with the `bias_tracker`.

## 9. Module Architecture and Flow

The module's architecture is straightforward, centered around the [`run_rules()`](simulation_engine/rule_engine.py:18) function:
1.  **Initialization:**
    *   Rules are loaded via [`build_static_rules()`](simulation_engine/rules/static_rules.py:0).
    *   An empty `execution_log` list is prepared.
2.  **Rule Iteration:** The engine iterates through each rule.
3.  **Rule Evaluation:**
    *   **Enabled Check:** Skips disabled rules.
    *   **Condition Check:** Executes the rule's `condition` function, passing the current `WorldState`.
    *   **Effects Application (if condition met):**
        *   A deep copy of `WorldState` is taken (`state_before`) for auditing.
        *   The rule's `effects` function is executed, modifying the `WorldState` (`state`).
        *   An `audit` record is generated using [`audit_rule()`](simulation_engine/rules/rule_audit_layer.py:0), comparing `state_before` and `state_after` (`state`).
        *   The `audit` record is appended to `execution_log`.
        *   Symbolic tags are recorded using `bias_tracker.record()`.
        *   A "Rule triggered" event is logged to `WorldState`.
    *   **Condition Not Met (if verbose):** A "Rule checked but not triggered" event is logged.
4.  **Error Handling:** Any `Exception` during a rule's condition check or effect application is caught, and a "[RULE ERROR]" event is logged to `WorldState`.
5.  **Return Value:** The function returns the `execution_log`, which is a list of dictionaries, each representing an audit of a triggered rule.

## 10. Naming Conventions

*   **Functions:** [`run_rules()`](simulation_engine/rule_engine.py:18) uses snake_case, which is standard Python practice.
*   **Variables:** Variables like `state`, `rules`, `execution_log`, `state_before`, `audit` are clear and use snake_case.
*   **Classes (Imported):** [`WorldState`](simulation_engine/worldstate.py:0) and [`SymbolicBiasTracker`](symbolic_system/symbolic_bias_tracker.py:0) use PascalCase, adhering to Python conventions for class names.
*   **Module Name:** [`rule_engine.py`](simulation_engine/rule_engine.py) is descriptive.
*   **Consistency:** Naming appears consistent and generally follows PEP 8 guidelines within the provided code. No significant deviations or potential AI assumption errors in naming are immediately apparent.