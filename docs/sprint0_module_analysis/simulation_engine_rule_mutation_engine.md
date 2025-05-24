# SPARC Analysis: simulation_engine/rule_mutation_engine.py

**Version:** Pulse v0.36
**Author:** Pulse v0.36

## 1. Module Intent/Purpose (Specification)

The [`simulation_engine/rule_mutation_engine.py`](simulation_engine/rule_mutation_engine.py:1) module is responsible for proposing and applying mutations to causal rule weights, thresholds, or structures. These mutations are driven by factors such as retrodiction error, symbolic misalignment, or trust regret. Its primary role is to adapt and evolve the rule set used in the simulation to improve its accuracy and relevance over time.

## 2. Operational Status/Completeness

The module appears to be operational and relatively complete for its defined scope.
- It can load rules, propose mutations based on volatility, and log these mutations.
- It includes a basic test function [`test_rule_mutation_engine()`](simulation_engine/rule_mutation_engine.py:86) for the mutation proposal logic.
- Logging is implemented for both individual mutations and batch applications.

No obvious placeholders (e.g., `pass` statements in critical logic blocks) or major `TODO` comments indicating unfinished core functionality were found.

## 3. Implementation Gaps / Unfinished Next Steps

- **Sophistication of Mutation Strategy:** The current mutation strategy in [`propose_rule_mutations()`](simulation_engine/rule_mutation_engine.py:36) is relatively simple, focusing on mutating the 'threshold' field by a random percentage (±20%) for rules in high-volatility clusters. More sophisticated mutation strategies could be implemented, such as:
    - Mutating other rule parameters (e.g., 'effect_size', conditions, effects).
    - Structural mutations (e.g., adding/removing conditions, splitting/merging rules).
    - Mutations guided by specific error signals (retrodiction error, symbolic misalignment, trust regret) rather than just general volatility.
- **Persistence of Mutated Rules:** The [`apply_rule_mutations()`](simulation_engine/rule_mutation_engine.py:62) function logs mutations but does not appear to save the mutated rules back to their original storage (e.g., static rules files, fingerprint files, candidate rules files). The `_registry.rules` object is modified in memory during [`propose_rule_mutations()`](simulation_engine/rule_mutation_engine.py:36), but these changes are not persisted by this module. The `RuleRegistry` itself has an `export_rules` method, but it's not called here after mutation.
- **Integration with Retrodiction/Trust Feedback:** The docstring mentions mutations based on "retrodiction error, symbolic misalignment, or trust regret," but the current implementation primarily uses `score_rule_volatility` from [`memory/rule_cluster_engine.py`](memory/rule_cluster_engine.py:17) which is based on historical mutation frequency. A more direct feedback loop from performance metrics could enhance mutation targeting.

## 4. Connections & Dependencies

### Direct Imports:
- **Standard Library:** `random`, `json`, `logging`, `os`, `datetime` (from `datetime`), `Dict`, `List`, `Any` (from `typing`).
- **Project Modules:**
    - [`core.path_registry.PATHS`](core/path_registry.py:16)
    - [`memory.rule_cluster_engine.score_rule_volatility`](memory/rule_cluster_engine.py:17)
    - [`simulation_engine.rules.rule_registry.RuleRegistry`](simulation_engine/rules/rule_registry.py:18)
    - [`core.pulse_learning_log.log_learning_event`](core/pulse_learning_log.py:19)

### Touched Project Files (for dependency mapping):
To understand the full context of `simulation_engine/rule_mutation_engine.py`, the following project files were read and analyzed:
- [`simulation_engine/rule_mutation_engine.py`](simulation_engine/rule_mutation_engine.py:1) (The module itself)
- [`core/path_registry.py`](core/path_registry.py:16)
- [`memory/rule_cluster_engine.py`](memory/rule_cluster_engine.py:17)
- [`simulation_engine/rules/rule_registry.py`](simulation_engine/rules/rule_registry.py:18)
- [`core/pulse_learning_log.py`](core/pulse_learning_log.py:19)
- [`simulation_engine/rules/rule_coherence_checker.py`](simulation_engine/rules/rule_coherence_checker.py:25) (via `rule_registry.py` and `rule_cluster_engine.py`)
- [`simulation_engine/rules/static_rules.py`](simulation_engine/rules/static_rules.py:27) (via `rule_registry.py`)
- [`core/pulse_config.py`](core/pulse_config.py:10) (via `static_rules.py`)
- [`core/variable_accessor.py`](core/variable_accessor.py:11) (via `static_rules.py`)
- [`pipeline/rule_applier.py`](pipeline/rule_applier.py:15) (via `static_rules.py`)
- [`core/variable_registry.py`](core/variable_registry.py:9) (via `variable_accessor.py`)
- [`core/bayesian_trust_tracker.py`](core/bayesian_trust_tracker.py:27) (via `pulse_learning_log.py`)
- [`simulation_engine/rules/rule_matching_utils.py`](simulation_engine/rules/rule_matching_utils.py:22) (via `rule_coherence_checker.py`)


### Interactions:
- **Rule Registry:** Reads all rules via `RuleRegistry().load_all_rules()` and `get_all_rules()`. Modifies rule thresholds in memory.
- **Rule Cluster Engine:** Uses `score_rule_volatility()` to determine which rules are candidates for mutation.
- **Learning Log:** Logs mutation events using `log_learning_event()`.
- **File System (Output):**
    - Appends mutation details to a JSONL file specified by `RULE_MUTATION_LOG` (default: `logs/rule_mutation_log.jsonl`), which is retrieved from `PATHS`.

### Input/Output Files:
- **Input:**
    - Implicitly, rule files loaded by `RuleRegistry` (e.g., `simulation_engine/rules/rule_fingerprints.json`, `data/candidate_rules.json`, and static rules defined in `simulation_engine.rules.static_rules.py`).
    - `logs/rule_mutation_log.jsonl` (read by `score_rule_volatility` in the dependency `memory/rule_cluster_engine.py`).
- **Output:**
    - `logs/rule_mutation_log.jsonl`: Appends JSON line entries for each mutation applied.

## 5. Function and Class Example Usages

### `get_all_rules() -> dict`
- **Purpose:** Retrieves all rules from the `RuleRegistry` instance, keyed by `rule_id` or a generated ID.
- **Usage:**
  ```python
  all_rules = get_all_rules()
  if all_rules:
      # Process rules
      pass
  ```

### `propose_rule_mutations(rules: Dict[str, Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]`
- **Purpose:** Identifies the top N rules based on volatility and proposes mutations to their 'threshold' values.
- **Usage:**
  ```python
  current_rules = get_all_rules()
  proposed_mutations = propose_rule_mutations(current_rules, top_n=3)
  for mutation in proposed_mutations:
      print(f"Proposed: Rule {mutation['rule']} threshold {mutation['from']} -> {mutation['to']}")
  ```

### `apply_rule_mutations() -> None`
- **Purpose:** Orchestrates loading rules, proposing mutations, and logging these mutations.
- **Usage:**
  ```python
  # This function is typically called as the main entry point of the script
  apply_rule_mutations()
  ```
  Or, if run as a script: `python simulation_engine/rule_mutation_engine.py`

### `test_rule_mutation_engine()`
- **Purpose:** A basic test function to verify the `propose_rule_mutations` logic with dummy rules.
- **Usage:**
  ```python
  # Typically run via the script's __main__ block with --test argument
  # python simulation_engine/rule_mutation_engine.py --test
  test_rule_mutation_engine()
  ```

## 6. Hardcoding Issues (SPARC Critical)

- **Default Log Path:** The `RULE_MUTATION_LOG` path defaults to `"logs/rule_mutation_log.jsonl"` if not found in `PATHS`. While `PATHS` provides centralization, this fallback is a form of hardcoding.
  ```python
  RULE_MUTATION_LOG = PATHS.get("RULE_MUTATION_LOG", "logs/rule_mutation_log.jsonl") # line 22
  ```
- **Mutation Parameters:**
    - The mutation percentage range (`random.uniform(0.8, 1.2)` for ±20%) is hardcoded in [`propose_rule_mutations()`](simulation_engine/rule_mutation_engine.py:55).
    - The clamping bounds `[0.0, 1.0]` for the threshold are hardcoded.
    - The default threshold value `0.5` used if a rule lacks one is hardcoded ([`propose_rule_mutations()`](simulation_engine/rule_mutation_engine.py:50)).
- **`top_n` Default:** The default number of rules to mutate (`top_n=5`) is hardcoded in the function signature of [`propose_rule_mutations()`](simulation_engine/rule_mutation_engine.py:36).

These hardcoded values should ideally be configurable, perhaps through `pulse_config.py` or a dedicated configuration file for the mutation engine, to allow for easier tuning and adaptation without code changes.

## 7. Coupling Points

- **`core.path_registry`:** Tightly coupled for resolving the `RULE_MUTATION_LOG` path.
- **`memory.rule_cluster_engine`:** Directly calls `score_rule_volatility` to guide mutation candidate selection. This creates a dependency on the specific scoring logic of that module.
- **`simulation_engine.rules.rule_registry.RuleRegistry`:** Heavily coupled for loading and accessing all rules. The mutation engine directly modifies rule dictionaries obtained from this registry (in memory).
- **`core.pulse_learning_log`:** Coupled for logging learning events related to mutations.
- **File I/O for `RULE_MUTATION_LOG`:** Direct file writing operations for logging.

## 8. Existing Tests (SPARC Refinement)

- A single test function, [`test_rule_mutation_engine()`](simulation_engine/rule_mutation_engine.py:86), exists within the module.
- **Coverage:** This test focuses on the [`propose_rule_mutations()`](simulation_engine/rule_mutation_engine.py:36) function. It checks:
    - That the correct number of mutations (`top_n`) are proposed.
    - That mutated threshold values remain within the `[0.0, 1.0]` bounds.
- **Quality & Gaps:**
    - The test uses dummy rules, which is good for isolation.
    - It does not test the `apply_rule_mutations()` function, particularly the file logging aspect.
    - It does not test edge cases, such as:
        - Empty input `rules` dictionary to `propose_rule_mutations()`. (Handled by a warning in the main code).
        - Rules with invalid or missing 'threshold' fields. (Handled by a warning and skip in the main code).
        - Behavior when `score_rule_volatility` returns empty or unexpected results.
    - No checks are made on the actual content of the `RULE_MUTATION_LOG` after `apply_rule_mutations()`.
    - The test is inline with the module code and run via `if __name__ == "__main__":` block, which is common for utility scripts but less ideal for a formal test suite (e.g., using `pytest`).
    - The test relies on `print()` for success indication rather than more robust assertion messages or test framework reporting.

## 9. Module Architecture and Flow (SPARC Architecture)

The module follows a relatively straightforward procedural flow:

1.  **Initialization:**
    *   Logging is configured.
    *   A `RuleRegistry` instance is created and all rules are loaded into memory (`_registry.load_all_rules()`). This happens at the module level.
2.  **`apply_rule_mutations()` (Main Operational Flow):**
    *   Calls [`get_all_rules()`](simulation_engine/rule_mutation_engine.py:32) to get a dictionary of current rules from the `_registry`.
    *   If rules exist, it calls [`propose_rule_mutations()`](simulation_engine/rule_mutation_engine.py:36) with these rules.
    *   **`propose_rule_mutations()`:**
        *   Calls `score_rule_volatility()` (from `memory.rule_cluster_engine`) to get volatility scores for rules.
        *   Sorts rules by volatility and selects the `top_n` candidates.
        *   For each candidate:
            *   Mutates the 'threshold' by a random factor (±20%), clamping it between 0 and 1.
            *   Updates the rule dictionary *in memory*.
            *   Logs the individual mutation event using `log_learning_event()`.
            *   Collects mutation details.
        *   Returns a list of mutation details.
    *   If mutations were proposed, `apply_rule_mutations()` then appends these mutation details to the `RULE_MUTATION_LOG` file.
    *   Logs a batch mutation event.
3.  **`test_rule_mutation_engine()` (Test Flow):**
    *   Creates a set of dummy rules.
    *   Calls `propose_rule_mutations()` with these dummy rules.
    *   Asserts the number of mutations and the validity of new threshold values.

**Modularity:**
- The module is reasonably modular, focusing on the task of rule mutation.
- It delegates rule loading/storage to `RuleRegistry` and volatility scoring to `rule_cluster_engine`.
- Logging is handled via `pulse_learning_log`.

**Concerns:**
- The module-level instantiation and loading of `RuleRegistry` (`_registry = RuleRegistry(); _registry.load_all_rules()`) means rules are loaded as soon as this module is imported. This could have side effects or performance implications if the module is imported but not immediately used for its primary functions. It might be better to load rules explicitly within the functions that need them or pass a `RuleRegistry` instance.
- As noted, mutated rules are modified in the `_registry`'s in-memory list but not explicitly saved back to persistent storage by this module. This could lead to inconsistencies if not handled carefully by the calling system.

## 10. Naming Conventions (SPARC Maintainability)

- **Variable Names:** Generally clear and descriptive (e.g., `RULE_MUTATION_LOG`, `sorted_rules`, `new_threshold`).
    - `_registry`: Standard Python convention for internal/module-level variables.
    - `m` as a loop variable for mutations is short but acceptable in a small loop.
- **Function Names:** Clear and action-oriented (e.g., `get_all_rules`, `propose_rule_mutations`, `apply_rule_mutations`, `test_rule_mutation_engine`).
- **Constants:** `RULE_MUTATION_LOG` is in uppercase, following Python conventions.
- **Docstrings:** Present for the module and all functions, explaining their purpose, and sometimes arguments/returns. They are generally clear.
- **Comments:** Used sparingly but effectively to explain specific logic, like the mutation clamping.

Overall, naming conventions are good and contribute to maintainability.

## 11. SPARC Compliance Summary

- **Specification:** The module's purpose is clearly defined in its docstring. It aims to mutate rules based on certain criteria.
- **Modularity/Architecture:**
    - Good separation of concerns by using `RuleRegistry`, `rule_cluster_engine`, and `pulse_learning_log`.
    - The flow is logical.
    - Concern: Module-level rule loading could be improved.
    - Concern: Persistence of mutated rules is not handled within this module, which might be an architectural decision but needs to be clear.
- **Refinement Focus:**
    - **Testability:** Basic test exists but could be significantly expanded for better coverage, edge cases, and integration with a formal test framework. The current test is more of a basic sanity check.
    - **Security:**
        - No hardcoded secrets, API keys, or obviously sensitive data paths were found.
        - File paths like `logs/rule_mutation_log.jsonl` are managed via `PATHS` or fallbacks, which is better than direct hardcoding within functions, but the fallback itself is hardcoded.
    - **Maintainability:**
        - Code is generally clear and well-commented.
        - Naming conventions are good.
        - The hardcoding of mutation parameters (percentage, default threshold) reduces maintainability for tuning these aspects.
- **No Hardcoding (Critical):**
    - Several instances of hardcoded values were identified (default log path fallback, mutation percentages, default threshold for mutation, `top_n` default). These should be made configurable.

**Overall SPARC Assessment:**
The module is a good foundational piece for rule mutation. It adheres to some SPARC principles well (clear specification, reasonable modularity, good naming). However, it falls short in areas like comprehensive testability and the avoidance of hardcoded configuration values. The lack of explicit rule persistence after mutation is a significant point that needs clarification in the broader system architecture – either this module should handle it, or the calling system must be responsible.