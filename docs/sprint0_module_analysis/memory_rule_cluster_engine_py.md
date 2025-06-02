# Module Analysis: `memory/rule_cluster_engine.py`

## 1. Module Intent/Purpose

The primary role of the [`memory/rule_cluster_engine.py`](memory/rule_cluster_engine.py:) module is to cluster and score simulation rules. This analysis is intended for use in meta-learning processes, specifically for targeting rules for mutation, detecting redundancy among rules, and evolving the trust scores associated with rules. It plays a role in prioritizing which rules should undergo mutation.

## 2. Operational Status/Completeness

The module appears to be operationally functional and complete for its stated purpose as described in its docstring and implemented functions. It successfully loads rules, clusters them by domain, scores their volatility based on a mutation log, and exports a summary. There are no obvious TODO comments or placeholder code sections within the provided file content.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Advanced Scoring/Clustering:** While the module scores rules based on mutation volatility and clusters them by domain, more advanced techniques could be implemented. For example, clustering could consider rule content similarity (e.g., using NLP techniques on rule descriptions or conditions) or performance impact. Scoring could also incorporate rule effectiveness or contribution to simulation accuracy.
*   **Trust Evolution Integration:** The docstring mentions "trust evolution" as a use case. While volatility scores could feed into a trust system, the direct mechanisms for evolving trust are not part of this module and would likely reside in a separate system that consumes this module's output.
*   **Redundancy Detection:** The module mentions "redundancy detection." Grouping by domain is a first step, but more sophisticated redundancy analysis (e.g., identifying rules with overlapping conditions or identical actions within the same domain) is not explicitly implemented.
*   **Error Handling in Log Parsing:** The [`score_rule_volatility`](memory/rule_cluster_engine.py:36) function has a general `except Exception` block. More specific error handling for `json.JSONDecodeError` or `KeyError` during log parsing could improve robustness.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`core.path_registry.PATHS`](core/path_registry.py:) (specifically for `RULE_MUTATION_LOG` path)
*   [`engine.rules.rule_registry.RuleRegistry`](simulation_engine/rules/rule_registry.py:)

### External Library Dependencies:
*   `json`
*   `os`
*   `collections.defaultdict`
*   `typing.Dict`, `typing.List`, `typing.Optional`

### Interaction via Shared Data:
*   **Input File:** Reads from a rule mutation log file. The default path is configured via `PATHS.get("RULE_MUTATION_LOG", "logs/rule_mutation_log.jsonl")` (see [`RULE_MUTATION_LOG`](memory/rule_cluster_engine.py:17)). This file is expected to be a JSONL file where each line is a JSON object containing mutation details, specifically a `mutation.rule` field indicating the rule ID.
*   **Output File:** Writes a summary of rule clusters to a JSON file. The default path is `"logs/rule_cluster_summary.json"` as specified in the [`export_cluster_summary`](memory/rule_cluster_engine.py:89) function.

## 5. Function and Class Example Usages

*   **`get_all_rules() -> dict`**:
    *   Retrieves all rules loaded by the global `_registry` (an instance of `RuleRegistry`).
    *   Returns a dictionary mapping rule IDs to rule metadata.
    *   Usage: `rules_data = get_all_rules()`

*   **`cluster_rules_by_domain(rules: Dict[str, Dict]) -> Dict[str, List[str]]`**:
    *   Takes a dictionary of rules (as returned by `get_all_rules`).
    *   Groups rule IDs by the "domain" specified in their metadata. If no domain is found, it defaults to "unknown".
    *   Usage: `domain_clusters = cluster_rules_by_domain(rules_data)`

*   **`score_rule_volatility(rules: Dict[str, Dict], log_path: Optional[str] = None) -> Dict[str, float]`**:
    *   Calculates a volatility score for each rule based on its historical mutation frequency.
    *   Reads mutation counts from the `log_path` (defaults to `RULE_MUTATION_LOG`).
    *   Returns a dictionary mapping rule IDs to a normalized volatility score (0-1).
    *   Usage: `volatility_scores = score_rule_volatility(rules_data)`

*   **`summarize_rule_clusters(verbose: bool = False) -> List[Dict]`**:
    *   Orchestrates the process of getting rules, clustering them by domain, and scoring their volatility.
    *   Computes average volatility for each cluster.
    *   Returns a list of dictionaries, each summarizing a cluster (domain label, rule IDs, average volatility score, size).
    *   Usage: `cluster_summary = summarize_rule_clusters(verbose=True)`

*   **`export_cluster_summary(path: str = "logs/rule_cluster_summary.json")`**:
    *   Calls `summarize_rule_clusters()` to get the summary.
    *   Writes this summary to the specified `path` as a JSON file.
    *   Usage: `export_cluster_summary()`

The `if __name__ == "__main__":` block (lines [`100-107`](memory/rule_cluster_engine.py:100-107)) demonstrates a typical command-line usage, printing a verbose summary of rule clusters.

## 6. Hardcoding Issues

*   **Default Log Path:** The fallback path for `RULE_MUTATION_LOG` is hardcoded to `"logs/rule_mutation_log.jsonl"` within the `PATHS.get()` call (line [`17`](memory/rule_cluster_engine.py:17)). While configurable through `PATHS`, this default is embedded.
*   **Default Export Path:** The default output file path in [`export_cluster_summary`](memory/rule_cluster_engine.py:89) is hardcoded to `"logs/rule_cluster_summary.json"`.
*   **Default Domain:** In [`cluster_rules_by_domain`](memory/rule_cluster_engine.py:27), if a rule's metadata lacks a "domain", it defaults to the string `"unknown"` (line [`31`](memory/rule_cluster_engine.py:31)).
*   **Rule ID Fallback:** In [`get_all_rules`](memory/rule_cluster_engine.py:22), if a rule lacks `rule_id` or `id`, it defaults to its stringified enumeration index `str(i)` (line [`24`](memory/rule_cluster_engine.py:24)).

## 7. Coupling Points

*   **`RuleRegistry`:** The module is tightly coupled to [`engine.rules.rule_registry.RuleRegistry`](simulation_engine/rules/rule_registry.py:) for accessing rule definitions and their metadata. Changes to `RuleRegistry`'s structure or how rules are stored/accessed could impact this module.
*   **`RULE_MUTATION_LOG` Format:** The [`score_rule_volatility`](memory/rule_cluster_engine.py:36) function expects `RULE_MUTATION_LOG` to be a JSONL file where each line is a JSON object with a specific structure (i.e., `entry.get("mutation", {}).get("rule")` to extract the rule ID). Changes to this log format would break the volatility scoring.
*   **`core.path_registry.PATHS`:** Dependency on `PATHS` for resolving the `RULE_MUTATION_LOG` path creates coupling with the path configuration system.
*   **Rule Metadata Structure:** The module relies on rules having specific keys in their metadata, such as `"domain"` for clustering (line [`31`](memory/rule_cluster_engine.py:31)) and `"rule_id"` or `"id"` for identification (line [`24`](memory/rule_cluster_engine.py:24)).

## 8. Existing Tests

Based on the provided file listing for the `tests/` directory, there is no specific test file named `test_rule_cluster_engine.py` or similar. This suggests that dedicated unit tests for this module might be missing or integrated into broader test suites not immediately identifiable. The absence of direct tests is a potential gap.

## 9. Module Architecture and Flow

The module follows a straightforward procedural approach:
1.  **Initialization:** A global `_registry` (instance of `RuleRegistry`) is created and all rules are loaded into it ([`lines 19-20`](memory/rule_cluster_engine.py:19-20)).
2.  **Rule Retrieval ([`get_all_rules`](memory/rule_cluster_engine.py:22)):** Fetches all loaded rules from the `_registry`.
3.  **Clustering ([`cluster_rules_by_domain`](memory/rule_cluster_engine.py:27)):** Takes the retrieved rules and groups them into clusters based on the "domain" field in their metadata.
4.  **Volatility Scoring ([`score_rule_volatility`](memory/rule_cluster_engine.py:36)):**
    *   Reads the `RULE_MUTATION_LOG` file.
    *   Counts the occurrences (mutations) for each rule ID found in the log.
    *   Normalizes these counts to produce a volatility score between 0 and 1 for each rule.
5.  **Summarization ([`summarize_rule_clusters`](memory/rule_cluster_engine.py:58)):**
    *   Calls `get_all_rules()`.
    *   Calls `cluster_rules_by_domain()` using the fetched rules.
    *   Calls `score_rule_volatility()` using the fetched rules.
    *   For each domain cluster, it calculates the average volatility score based on its member rules.
    *   Compiles a list of dictionaries, each representing a cluster with its domain, member rule IDs, average volatility, and size.
    *   Optionally prints verbose output during summarization.
6.  **Export ([`export_cluster_summary`](memory/rule_cluster_engine.py:89)):**
    *   Calls `summarize_rule_clusters()` to generate the summary data.
    *   Writes this data to a JSON file.
The main execution block (`if __name__ == "__main__":`) demonstrates this flow by calling [`summarize_rule_clusters`](memory/rule_cluster_engine.py:58) with `verbose=True` and printing the results.

## 10. Naming Conventions

*   **Functions:** Use `snake_case` (e.g., [`cluster_rules_by_domain`](memory/rule_cluster_engine.py:27), [`score_rule_volatility`](memory/rule_cluster_engine.py:36)), which is consistent with PEP 8.
*   **Variables:** Primarily `snake_case` (e.g., `rule_id`, `avg_v`, `log_path`).
*   **Constants:** Use `UPPER_SNAKE_CASE` for module-level constants (e.g., `RULE_MUTATION_LOG` on line [`17`](memory/rule_cluster_engine.py:17)).
*   **Module-level "Private" Variable:** `_registry` (line [`19`](memory/rule_cluster_engine.py:19)) uses a leading underscore, conventionally indicating it's intended for internal use within the module.
*   **Clarity:** Names are generally descriptive and understandable (e.g., `volatility`, `clusters`, `summary`).
*   **AI Assumption Errors:** No obvious AI-generated naming errors or significant deviations from Python community standards are apparent. The author tag "Pulse v0.38 – Full C Test Refined" suggests a versioning or generation note rather than an AI naming artifact within the code itself.