# Module Analysis: `simulation_engine/rule_mutation_engine.py`

## 1. Module Intent/Purpose

The primary role of the [`simulation_engine/rule_mutation_engine.py`](../../../simulation_engine/rule_mutation_engine.py:) module is to propose and apply mutations to causal rules. According to its docstring, this should be based on retrodiction error, symbolic misalignment, or trust regret, and target rule weights, thresholds, or structures. Currently, its implementation focuses on mutating the 'threshold' property of rules, primarily driven by rule volatility scores.

## 2. Operational Status/Completeness

The module is partially complete. It successfully implements threshold mutation for rules based on volatility. However, the broader scope outlined in its docstring (mutation of weights and structures, and triggers like retrodiction error, symbolic misalignment, or trust regret) is not yet implemented. There are no explicit "TODO" comments, but the discrepancy between the documented intent and current functionality indicates incompleteness.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Broader Mutation Types:** The module was intended to mutate rule 'weights' and 'structures', but currently only mutates 'thresholds' (see [`propose_rule_mutations()`](../../../simulation_engine/rule_mutation_engine.py:36)).
*   **Advanced Mutation Triggers:** The docstring mentions mutations based on "retrodiction error, symbolic misalignment, or trust regret" (see [module docstring](../../../simulation_engine/rule_mutation_engine.py:1-8)). The current implementation primarily uses rule volatility (via [`score_rule_volatility()`](../../../memory/rule_cluster_engine.py:0)) as the basis for selecting rules to mutate.
*   **Configuration for Mutation Parameters:** The mutation strength (currently ±20% for thresholds, see [`propose_rule_mutations()`](../../../simulation_engine/rule_mutation_engine.py:55)) and the number of rules to mutate (`top_n`, default 5) are hardcoded or have fixed defaults. These could be made configurable.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`core.path_registry.PATHS`](../../../core/path_registry.py:) (from [`core.path_registry`](../../../core/path_registry.py:16))
*   [`analytics.rule_cluster_engine.score_rule_volatility`](../../../memory/rule_cluster_engine.py:) (from [`analytics.rule_cluster_engine`](../../../memory/rule_cluster_engine.py:17))
*   [`engine.rules.rule_registry.RuleRegistry`](../../../simulation_engine/rules/rule_registry.py:) (from [`engine.rules.rule_registry`](../../../simulation_engine/rules/rule_registry.py:18))
*   [`core.pulse_learning_log.log_learning_event`](../../../core/pulse_learning_log.py:) (from [`core.pulse_learning_log`](../../../core/pulse_learning_log.py:19))

### External Library Dependencies:
*   `random`
*   `json`
*   `logging`
*   `os` (imported but not directly used; potentially via `PATHS`)
*   `typing` (Dict, List, Any)
*   `datetime` (from datetime)

### Shared Data Interactions:
*   **Rule Loading:** Reads rules via the `RuleRegistry` instance. The actual source of these rules (e.g., JSON files) is managed by the `RuleRegistry`.
*   **Volatility Scoring:** Interacts with [`analytics.rule_cluster_engine`](../../../memory/rule_cluster_engine.py:) by calling [`score_rule_volatility()`](../../../memory/rule_cluster_engine.py:).
*   **Logging:**
    *   Writes mutation details to a JSONL file specified by `RULE_MUTATION_LOG` (default: [`logs/rule_mutation_log.jsonl`](../../../logs/rule_mutation_log.jsonl), configured via [`PATHS`](../../../core/path_registry.py:22)).
    *   Uses [`log_learning_event()`](../../../core/pulse_learning_log.py:) to record mutation events.

### Input/Output Files:
*   **Input:** Rule definitions (indirectly via `RuleRegistry`).
*   **Output:** Mutation log file ([`logs/rule_mutation_log.jsonl`](../../../logs/rule_mutation_log.jsonl) by default).

## 5. Function and Class Example Usages

*   **`get_all_rules() -> dict`**:
    *   Retrieves all loaded rules from the global `RuleRegistry`.
    *   Usage: `rules = get_all_rules()` as seen in [`apply_rule_mutations()`](../../../simulation_engine/rule_mutation_engine.py:66).

*   **`propose_rule_mutations(rules: Dict[str, Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]`**:
    *   Identifies top N rules based on volatility and proposes changes to their 'threshold' values.
    *   Usage: `mutations = propose_rule_mutations(rules)` as seen in [`apply_rule_mutations()`](../../../simulation_engine/rule_mutation_engine.py:71).
    *   Test Usage: `mutations = propose_rule_mutations(dummy_rules, top_n=2)` in [`test_rule_mutation_engine()`](../../../simulation_engine/rule_mutation_engine.py:96).

*   **`apply_rule_mutations() -> None`**:
    *   Orchestrates the process: loads rules, proposes mutations, and logs these mutations to a file. This function doesn't actually save the mutated rules back to the registry or their source files; it only logs the proposed changes.
    *   Usage: Called when the script is run directly: `apply_rule_mutations()` (see [`if __name__ == "__main__":`](../../../simulation_engine/rule_mutation_engine.py:102-108)).

*   **`test_rule_mutation_engine()`**:
    *   A basic inline test function to verify the core logic of `propose_rule_mutations`.
    *   Usage: Called when the script is run with `--test` argument.

## 6. Hardcoding Issues

*   **Default Log Path:** The fallback path for `RULE_MUTATION_LOG` is hardcoded to `"logs/rule_mutation_log.jsonl"` if not found in `PATHS` (see [`RULE_MUTATION_LOG`](../../../simulation_engine/rule_mutation_engine.py:22)).
*   **Mutation Factor:** The mutation for thresholds is fixed to a range of ±20% (`random.uniform(0.8, 1.2)`) (see [`propose_rule_mutations()`](../../../simulation_engine/rule_mutation_engine.py:55)).
*   **Default Threshold Value:** If a rule lacks a 'threshold', it's assumed to be `0.5` during mutation proposal (see [`propose_rule_mutations()`](../../../simulation_engine/rule_mutation_engine.py:50)).
*   **`top_n` Default:** The `top_n` parameter in [`propose_rule_mutations()`](../../../simulation_engine/rule_mutation_engine.py:36) defaults to `5`.

## 7. Coupling Points

*   **`RuleRegistry` ([`engine.rules.rule_registry`](../../../simulation_engine/rules/rule_registry.py:18)):** Tightly coupled for loading and accessing rule definitions.
*   **`score_rule_volatility` ([`analytics.rule_cluster_engine`](../../../memory/rule_cluster_engine.py:17)):** Dependency for determining which rules are candidates for mutation.
*   **`PATHS` ([`core.path_registry`](../../../core/path_registry.py:16)):** Used for resolving the path to the rule mutation log file.
*   **`log_learning_event` ([`core.pulse_learning_log`](../../../core/pulse_learning_log.py:19)):** Used for logging learning-related events.
*   **Mutation Log File Structure:** Implicit coupling with any system that might consume or parse [`logs/rule_mutation_log.jsonl`](../../../logs/rule_mutation_log.jsonl).

## 8. Existing Tests

*   The module contains an inline test function: [`test_rule_mutation_engine()`](../../../simulation_engine/rule_mutation_engine.py:86-100).
*   This test focuses on [`propose_rule_mutations()`](../../../simulation_engine/rule_mutation_engine.py:36), checking:
    *   If the correct number of mutations (`top_n`) are generated.
    *   If the mutated 'to' threshold values are within the valid `[0.0, 1.0]` bounds.
*   It's a basic unit test and does not cover file I/O aspects (logging mutations) or integration with a live `RuleRegistry`.
*   There is no clear indication of a separate test file (e.g., `tests/simulation_engine/test_rule_mutation_engine.py`) from the provided context.

## 9. Module Architecture and Flow

1.  **Initialization:**
    *   Standard logging is configured.
    *   A global `RuleRegistry` instance (`_registry`) is created and all rules are loaded into it via [`_registry.load_all_rules()`](../../../simulation_engine/rule_mutation_engine.py:30).
2.  **Main Execution (`apply_rule_mutations()`):**
    *   Retrieves all rules using [`get_all_rules()`](../../../simulation_engine/rule_mutation_engine.py:32).
    *   Calls [`propose_rule_mutations()`](../../../simulation_engine/rule_mutation_engine.py:36) to get a list of proposed changes.
        *   Inside [`propose_rule_mutations()`](../../../simulation_engine/rule_mutation_engine.py:36):
            *   Rules are scored for volatility using [`score_rule_volatility()`](../../../memory/rule_cluster_engine.py:).
            *   The `top_n` most volatile rules are selected.
            *   For each selected rule, its 'threshold' is mutated (multiplied by a random factor between 0.8 and 1.2) and clamped to `[0.0, 1.0]`.
            *   Each proposed mutation is logged via [`log_learning_event()`](../../../core/pulse_learning_log.py:).
    *   The list of proposed mutations is then written to the `RULE_MUTATION_LOG` file.
    *   A summary `log_learning_event` for the batch of mutations is recorded.
    *   **Important Note:** The mutations are *proposed* and *logged*, but the `apply_rule_mutations` function does not appear to save these changes back to the `RuleRegistry` or the original rule source files. The rules in `_registry` remain unchanged by this process within the scope of this function.
3.  **Test Execution (`test_rule_mutation_engine()`):**
    *   If the script is run with `--test`, this function is called.
    *   It uses a set of dummy rules to test the logic of `propose_rule_mutations()`.

## 10. Naming Conventions

*   **Module Name:** `rule_mutation_engine.py` is descriptive and follows Python conventions.
*   **Functions:** `get_all_rules`, `propose_rule_mutations`, `apply_rule_mutations`, `test_rule_mutation_engine` use `snake_case` and are descriptive.
*   **Constants:** `RULE_MUTATION_LOG` is in `UPPER_CASE_SNAKE_CASE`.
*   **Variables:** Local variables (`rules`, `volatility`, `sorted_rules`, `mutations`, `old`, `new_threshold`) are generally clear and use `snake_case`. The global `_registry` uses a leading underscore, conventionally indicating internal use.
*   The naming largely adheres to PEP 8 guidelines. No significant deviations or AI-induced naming errors were observed.