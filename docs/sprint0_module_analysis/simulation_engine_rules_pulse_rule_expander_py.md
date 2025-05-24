# Module Analysis: `simulation_engine/rules/pulse_rule_expander.py`

**Version:** v0.101.0
**Author:** Pulse AI Engine

## Table of Contents
1.  [Module Intent/Purpose](#1-module-intentpurpose)
2.  [Operational Status/Completeness](#2-operational-statuscompleteness)
3.  [Implementation Gaps / Unfinished Next Steps](#3-implementation-gaps--unfinished-next-steps)
4.  [Connections & Dependencies](#4-connections--dependencies)
5.  [Function and Class Example Usages](#5-function-and-class-example-usages)
6.  [Hardcoding Issues](#6-hardcoding-issues)
7.  [Coupling Points](#7-coupling-points)
8.  [Existing Tests](#8-existing-tests)
9.  [Module Architecture and Flow](#9-module-architecture-and-flow)
10. [Naming Conventions](#10-naming-conventions)

---

## 1. Module Intent/Purpose

The primary role of the [`pulse_rule_expander.py`](../../simulation_engine/rules/pulse_rule_expander.py) module is to generate candidate new rules for the simulation engine. It achieves this by analyzing regret chains, forecast arc shifts (planned), and symbolic deltas (planned) that are not covered by existing, known rule fingerprints. The goal is to identify patterns in simulation outcomes or data that suggest new causal relationships or adjustments needed in the rule set.

---

## 2. Operational Status/Completeness

The module appears functional for its currently implemented scope, which focuses on generating rules from regret chains loaded from [`data/regret_chain.jsonl`](../../data/regret_chain.jsonl:).
Key observations:
*   The feature to "Suggest rules from common regret arcs" (line 10 of the module code) is implemented.
*   The features to "Detect frequent symbolic shifts not caused by any rule" (line 11) and analyze "forecast arc shifts" (line 7) appear to be planned but are not yet implemented in the current code structure. The module primarily processes regret data.
*   There are no explicit `TODO` comments or obvious placeholders in the implemented sections.
*   The module includes a CLI interface for triggering the rule expansion process.

---

## 3. Implementation Gaps / Unfinished Next Steps

*   **Expanded Data Sources:** The module's docstring mentions analyzing "forecast arc shifts, and symbolic deltas" ([`simulation_engine/rules/pulse_rule_expander.py:7`](../../simulation_engine/rules/pulse_rule_expander.py:7)), but the implementation primarily focuses on regret arcs from [`REGRET_FILE`](../../simulation_engine/rules/pulse_rule_expander.py:24). Future development could involve:
    *   Implementing functions to load and process data related to forecast arc shifts.
    *   Adding logic to analyze symbolic deltas not covered by existing rules.
*   **Sophisticated Rule Generation:** The current [`generate_candidate_rules`](../../simulation_engine/rules/pulse_rule_expander.py:61) function creates fairly generic rule triggers (e.g., `{"symbolic_trace": f"leading to {arc}"}`). This could be enhanced to:
    *   Infer more specific trigger conditions from the content of the regret entries or other data sources.
    *   Potentially suggest more complex rule effects or metadata.
*   **Integration with Symbolic Deltas:** The feature to "Detect frequent symbolic shifts not caused by any rule" ([`simulation_engine/rules/pulse_rule_expander.py:11`](../../simulation_engine/rules/pulse_rule_expander.py:11)) needs implementation. This would likely involve comparing symbolic trace data against rule fingerprints to find unexplainable shifts.

---

## 4. Connections & Dependencies

### Direct Project Module Imports
*   [`simulation_engine.rules.rule_matching_utils.get_all_rule_fingerprints`](../../simulation_engine/rules/rule_matching_utils.py:21)
*   [`simulation_engine.rules.rule_registry.RuleRegistry`](../../simulation_engine/rules/rule_registry.py:22)

### External Library Dependencies
*   `json` (Python standard library)
*   `collections.defaultdict` (Python standard library)
*   `typing.List, Dict, Tuple, Optional` (Python standard library)
*   `argparse` (Python standard library, for CLI functionality)

### Interaction via Shared Data
*   Interacts with [`RuleRegistry`](../../simulation_engine/rules/rule_registry.py:) to load all existing rules and their fingerprints.
*   Relies on [`rule_matching_utils`](../../simulation_engine/rules/rule_matching_utils.py:) to provide rule fingerprints.

### Input/Output Files
*   **Input:**
    *   [`data/regret_chain.jsonl`](../../data/regret_chain.jsonl:) (defined by `REGRET_FILE` constant on [`simulation_engine/rules/pulse_rule_expander.py:24`](../../simulation_engine/rules/pulse_rule_expander.py:24)) - Contains records of simulation regrets.
    *   Implicitly, rule definition files loaded by [`RuleRegistry`](../../simulation_engine/rules/rule_registry.py:) and fingerprinted by [`get_all_rule_fingerprints()`](../../simulation_engine/rules/rule_matching_utils.py:).
*   **Output:**
    *   [`data/candidate_rules.json`](../../data/candidate_rules.json:) (defined by `SUGGESTED_FILE` constant on [`simulation_engine/rules/pulse_rule_expander.py:26`](../../simulation_engine/rules/pulse_rule_expander.py:26)) - Stores the generated candidate rules.

---

## 5. Function and Class Example Usages

Key functions and their intended usage:

*   **`load_regrets(path: str = REGRET_FILE) -> List[Dict]`** ([`simulation_engine/rules/pulse_rule_expander.py:32`](../../simulation_engine/rules/pulse_rule_expander.py:32))
    *   Loads regret data from a specified JSONL file.
    ```python
    regrets_data = load_regrets("data/custom_regret_chain.jsonl")
    ```

*   **`load_rules(path: Optional[str] = None) -> Dict[str, Dict]`** ([`simulation_engine/rules/pulse_rule_expander.py:43`](../../simulation_engine/rules/pulse_rule_expander.py:43))
    *   Retrieves all rule fingerprints, keyed by rule ID.
    ```python
    existing_rules = load_rules()
    ```

*   **`extract_unmatched_arcs(regrets: List[Dict], rules: Dict[str, Dict]) -> List[Tuple[str, int]]`** ([`simulation_engine/rules/pulse_rule_expander.py:49`](../../simulation_engine/rules/pulse_rule_expander.py:49))
    *   Identifies arcs present in regret data that are not covered by any existing rule's `arc_label`.
    ```python
    unmatched_arcs_data = extract_unmatched_arcs(regrets_data, existing_rules)
    ```

*   **`generate_candidate_rules(unmatched_arcs: List[Tuple[str, int]]) -> List[Dict]`** ([`simulation_engine/rules/pulse_rule_expander.py:61`](../../simulation_engine/rules/pulse_rule_expander.py:61))
    *   Creates new candidate rule structures based on the identified unmatched arcs.
    ```python
    candidate_rules_list = generate_candidate_rules(unmatched_arcs_data)
    ```

*   **`export_candidate_rules(candidates: List[Dict], path: str = SUGGESTED_FILE) -> None`** ([`simulation_engine/rules/pulse_rule_expander.py:76`](../../simulation_engine/rules/pulse_rule_expander.py:76))
    *   Saves the list of candidate rules to a JSON file.
    ```python
    export_candidate_rules(candidate_rules_list, "output/suggested_new_rules.json")
    ```

*   **`expand_rules_from_regret() -> Dict`** ([`simulation_engine/rules/pulse_rule_expander.py:83`](../../simulation_engine/rules/pulse_rule_expander.py:83))
    *   The main function that orchestrates the process of loading regrets, loading rules, finding unmatched arcs, generating candidates, and exporting them.
    *   Typically invoked via the CLI.
    ```bash
    python simulation_engine/rules/pulse_rule_expander.py --expand
    ```

---

## 6. Hardcoding Issues

*   **File Paths:** Several file paths are hardcoded as global constants:
    *   `REGRET_FILE = "data/regret_chain.jsonl"` ([`simulation_engine/rules/pulse_rule_expander.py:24`](../../simulation_engine/rules/pulse_rule_expander.py:24))
    *   `FINGERPRINT_FILE = "data/rule_fingerprints.json"` ([`simulation_engine/rules/pulse_rule_expander.py:25`](../../simulation_engine/rules/pulse_rule_expander.py:25)) (Note: This constant is defined but not directly used in `load_rules`; `get_all_rule_fingerprints` is called instead).
    *   `SUGGESTED_FILE = "data/candidate_rules.json"` ([`simulation_engine/rules/pulse_rule_expander.py:26`](../../simulation_engine/rules/pulse_rule_expander.py:26))
    These could be made configurable, perhaps via CLI arguments or a configuration file, for greater flexibility.
*   **Candidate Rule Structure:** The structure for generated candidate rules, particularly the `trigger` field (`{"symbolic_trace": f"leading to {arc}"}` on [`simulation_engine/rules/pulse_rule_expander.py:69`](../../simulation_engine/rules/pulse_rule_expander.py:69)), is hardcoded. More dynamic or configurable rule generation logic could be beneficial.

---

## 7. Coupling Points

*   **Data Format Dependency:** The module is tightly coupled to the specific JSONL structure of the `regret_chain.jsonl` file and the expected structure of rule fingerprints returned by `get_all_rule_fingerprints()`.
*   **Module Dependencies:**
    *   Strong dependency on [`simulation_engine.rules.rule_matching_utils`](../../simulation_engine/rules/rule_matching_utils.py:) for providing rule fingerprints.
    *   Relies on [`simulation_engine.rules.rule_registry.RuleRegistry`](../../simulation_engine/rules/rule_registry.py:) for accessing the comprehensive set of rules. Changes in these modules, especially their interfaces or data structures, could impact this expander.
*   **Output Format:** The output format for `candidate_rules.json` is specific. Downstream processes consuming this file would depend on this structure.

---

## 8. Existing Tests

*   A specific test file for this module (e.g., `tests/simulation_engine/rules/test_pulse_rule_expander.py`) was not identified in the provided workspace file listing.
*   Without a dedicated test file, it's assumed that direct unit tests for the functions within `pulse_rule_expander.py` may be limited or missing.
*   The module's functionality might be covered by broader integration tests, but this cannot be confirmed without further information on the test suite.

---

## 9. Module Architecture and Flow

The module follows a straightforward procedural approach:

1.  **Initialization (Global Scope):**
    *   A [`RuleRegistry`](../../simulation_engine/rules/rule_registry.py:) instance is created.
    *   All rules are loaded into the registry using `_registry.load_all_rules()` ([`simulation_engine/rules/pulse_rule_expander.py:30`](../../simulation_engine/rules/pulse_rule_expander.py:30)).

2.  **CLI Entry Point (`if __name__ == "__main__":`)** ([`simulation_engine/rules/pulse_rule_expander.py:96`](../../simulation_engine/rules/pulse_rule_expander.py:96)):
    *   Parses command-line arguments.
    *   If the `--expand` flag is provided, it calls the main orchestrator function `expand_rules_from_regret()`.
    *   Prints the JSON result returned by `expand_rules_from_regret()`.

3.  **Core Logic - `expand_rules_from_regret()` function** ([`simulation_engine/rules/pulse_rule_expander.py:83`](../../simulation_engine/rules/pulse_rule_expander.py:83)):
    *   **Load Data:**
        *   Calls [`load_regrets()`](../../simulation_engine/rules/pulse_rule_expander.py:32) to read regret data from `REGRET_FILE`.
        *   Calls [`load_rules()`](../../simulation_engine/rules/pulse_rule_expander.py:43) (which internally uses `get_all_rule_fingerprints()`) to get existing rule fingerprints.
    *   **Process Data:**
        *   Calls [`extract_unmatched_arcs()`](../../simulation_engine/rules/pulse_rule_expander.py:49) to compare regret arcs with rule fingerprints and identify frequent arcs not covered by any known rule.
    *   **Generate Candidates:**
        *   Calls [`generate_candidate_rules()`](../../simulation_engine/rules/pulse_rule_expander.py:61) to create new rule definitions based on these unmatched arcs. The generated rules have a basic structure.
    *   **Export Results:**
        *   Calls [`export_candidate_rules()`](../../simulation_engine/rules/pulse_rule_expander.py:76) to save the generated candidate rules to `SUGGESTED_FILE`.
    *   Returns a dictionary summarizing the operation (number of unmatched arcs, count of suggested rules, and output file path).

The data flow is sequential: Regrets & Rules -> Unmatched Arcs -> Candidate Rules -> JSON Output.

---

## 10. Naming Conventions

*   **Consistency:** The module generally adheres to Python's PEP 8 naming conventions.
    *   Functions and variables use `snake_case` (e.g., `load_regrets`, `unmatched_arcs`).
    *   Global constants use `UPPER_SNAKE_CASE` (e.g., `REGRET_FILE`, `SUGGESTED_FILE`).
    *   A private global variable `_registry` is prefixed with an underscore.
*   **Clarity:** Names are generally descriptive and clearly indicate the purpose of variables and functions (e.g., `extract_unmatched_arcs`, `generate_candidate_rules`).
*   **AI/PEP 8 Adherence:** No significant deviations from PEP 8 or common Python practices were observed. The naming does not suggest obvious AI-generated errors or misunderstandings of conventions.