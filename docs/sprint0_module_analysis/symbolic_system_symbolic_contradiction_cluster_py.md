# Module Analysis: `symbolic_system/symbolic_contradiction_cluster.py`

## 1. Module Intent/Purpose

The primary role of the [`symbolic_system/symbolic_contradiction_cluster.py`](../../symbolic_system/symbolic_contradiction_cluster.py:0) module is to identify and group forecasts that exhibit symbolic contradictions. It achieves this by analyzing symbolic overlay divergence (specifically "hope" and "despair" values) and differences in "arc opposition" (represented by `arc_label`).

As stated in its docstring, the module is intended for:
- Symbolic audit
- Strategic coherence checks
- Contradiction memory tagging (though tagging itself is not implemented within this module)

## 2. Operational Status/Completeness

- The module appears to be a small, focused utility, likely complete for its currently defined scope.
- It consists of two main functions: [`cluster_symbolic_conflicts()`](../../symbolic_system/symbolic_contradiction_cluster.py:16) for identifying conflicts and [`summarize_contradiction_clusters()`](../../symbolic_system/symbolic_contradiction_cluster.py:46) for printing a summary.
- An `if __name__ == "__main__":` block ([`symbolic_system/symbolic_contradiction_cluster.py:56-61`](../../symbolic_system/symbolic_contradiction_cluster.py:56)) provides a basic demonstration, indicating it's runnable.
- No explicit `TODO` comments or obvious placeholders are present in the code.

## 3. Implementation Gaps / Unfinished Next Steps

- **Narrative Alignment Mismatch:** The module's docstring ([`symbolic_system/symbolic_contradiction_cluster.py:5`](../../symbolic_system/symbolic_contradiction_cluster.py:5)) mentions clustering based on "narrative alignment mismatch," but this specific logic is not visibly implemented in the [`cluster_symbolic_conflicts()`](../../symbolic_system/symbolic_contradiction_cluster.py:16) function. This might be an intended simplification or a gap.
- **Contradiction Memory Tagging:** The docstring ([`symbolic_system/symbolic_contradiction_cluster.py:7`](../../symbolic_system/symbolic_contradiction_cluster.py:7)) also states the module is used for "contradiction memory tagging." However, the module only identifies and summarizes conflicts; the actual tagging mechanism would likely reside in a separate, consuming module.
- **Configurable Thresholds:** The conflict detection for "Hope vs Despair Paradox" uses a hardcoded threshold of `0.6` ([`symbolic_system/symbolic_contradiction_cluster.py:37`](../../symbolic_system/symbolic_contradiction_cluster.py:37)). Making this configurable could enhance flexibility.
- **Advanced Conflict Types:** The module could be extended to detect more nuanced types of symbolic contradictions beyond the current two.

## 4. Connections & Dependencies

-   **Direct Project Imports:** None. The module is self-contained in terms of direct project module imports.
-   **External Library Dependencies:**
    -   [`typing`](https://docs.python.org/3/library/typing.html) (`List`, `Dict`, `Tuple`): For type hinting.
    -   [`collections.defaultdict`](https://docs.python.org/3/library/collections.html#collections.defaultdict): Used for grouping forecasts.
    -   [`itertools.combinations`](https://docs.python.org/3/library/itertools.html#itertools.combinations): Used for pairing forecasts.
-   **Shared Data Interaction:**
    -   **Input:** Expects a list of forecast dictionaries (`List[Dict]`). The structure of these dictionaries (keys like `origin_turn`, `trace_id`, `forecast.symbolic_change.hope`, `forecast.symbolic_change.despair`, `arc_label`) is crucial.
    -   **Output:** [`cluster_symbolic_conflicts()`](../../symbolic_system/symbolic_contradiction_cluster.py:16) returns a list of dictionaries representing conflict clusters. [`summarize_contradiction_clusters()`](../../symbolic_system/symbolic_contradiction_cluster.py:46) prints to the command-line interface.
-   **Input/Output Files:** No direct file I/O for logs, data, or metadata. Operates on in-memory data structures and prints to stdout.

## 5. Function and Class Example Usages

### [`cluster_symbolic_conflicts(forecasts: List[Dict]) -> List[Dict]`](../../symbolic_system/symbolic_contradiction_cluster.py:16)

This function takes a list of forecast dictionaries and returns a list of clusters, where each cluster identifies conflicting forecasts from the same `origin_turn`.

```python
# Sample forecast data
f1 = {
    "trace_id": "T1",
    "origin_turn": 3,
    "arc_label": "Hope Surge",
    "forecast": {"symbolic_change": {"hope": 0.9, "despair": 0.1}}
}
f2 = {
    "trace_id": "T2",
    "origin_turn": 3,
    "arc_label": "Collapse Risk",
    "forecast": {"symbolic_change": {"hope": 0.2, "despair": 0.8}}
}
f3 = { # Different turn, should not conflict with f1, f2 in the same cluster
    "trace_id": "T3",
    "origin_turn": 4,
    "arc_label": "Stability",
    "forecast": {"symbolic_change": {"hope": 0.5, "despair": 0.5}}
}

forecast_data = [f1, f2, f3]
conflict_clusters = cluster_symbolic_conflicts(forecast_data)
# Expected output for conflict_clusters:
# [
#     {
#         "origin_turn": 3,
#         "conflicts": [
#             ("T1", "T2", "Hope vs Despair Paradox"),
#             ("T1", "T2", "Arc Conflict: Hope Surge vs Collapse Risk")
#         ]
#     }
# ]
# Note: f3 is not part of this conflict cluster as it's from a different origin_turn.
```

### [`summarize_contradiction_clusters(conflict_clusters: List[Dict]) -> None`](../../symbolic_system/symbolic_contradiction_cluster.py:46)

This function takes the output from [`cluster_symbolic_conflicts()`](../../symbolic_system/symbolic_contradiction_cluster.py:16) and prints a human-readable summary to the console.

```python
# Assuming conflict_clusters from the example above
# summarize_contradiction_clusters(conflict_clusters)

# Console Output:
#
# 🧠 Symbolic Contradiction Cluster Summary:
#
# 📦 Origin Turn: 3 | Conflicts: 2
#  - T1 vs T2 → Hope vs Despair Paradox
#  - T1 vs T2 → Arc Conflict: Hope Surge vs Collapse Risk
```
The `if __name__ == "__main__":` block ([`symbolic_system/symbolic_contradiction_cluster.py:56-61`](../../symbolic_system/symbolic_contradiction_cluster.py:56)) in the module provides a direct, runnable example.

## 6. Hardcoding Issues

-   **Default Values for Missing Keys:**
    -   `origin_turn`: Defaults to `-1` if missing ([`symbolic_system/symbolic_contradiction_cluster.py:25`](../../symbolic_system/symbolic_contradiction_cluster.py:25)).
    -   `trace_id`: Defaults to `"?1"` or `"?2"` if missing ([`symbolic_system/symbolic_contradiction_cluster.py:31-32`](../../symbolic_system/symbolic_contradiction_cluster.py:31)).
    -   `hope`/`despair`: Default to `0.5` if missing within `symbolic_change` ([`symbolic_system/symbolic_contradiction_cluster.py:35-36`](../../symbolic_system/symbolic_contradiction_cluster.py:35)).
-   **Magic Numbers:**
    -   The threshold `0.6` for determining significant `hgap` (hope gap) and `dgap` (despair gap) is hardcoded ([`symbolic_system/symbolic_contradiction_cluster.py:37`](../../symbolic_system/symbolic_contradiction_cluster.py:37)).
-   **Strings:**
    -   Conflict reason strings like `"Hope vs Despair Paradox"` ([`symbolic_system/symbolic_contradiction_cluster.py:38`](../../symbolic_system/symbolic_contradiction_cluster.py:38)) and the format for `"Arc Conflict: ..."` ([`symbolic_system/symbolic_contradiction_cluster.py:40`](../../symbolic_system/symbolic_contradiction_cluster.py:40)) are hardcoded.
    -   Output formatting strings in [`summarize_contradiction_clusters()`](../../symbolic_system/symbolic_contradiction_cluster.py:46) are hardcoded.

## 7. Coupling Points

-   **Input Data Structure:** The module is tightly coupled to the specific dictionary structure of input forecasts. Any changes to keys like `origin_turn`, `trace_id`, `forecast`, `symbolic_change`, `hope`, `despair`, or `arc_label` in the forecast data would require modifications to this module.
-   **Conflict Logic:** The definition of what constitutes a "symbolic conflict" (i.e., the hope/despair gap logic and arc label comparison) is specific to the symbolic system's internal concepts and is embedded within this module.

## 8. Existing Tests

-   **Test Files:** No dedicated test file (e.g., `tests/symbolic_system/test_symbolic_contradiction_cluster.py`) was identified in the provided file listing.
-   **Inline Tests:** The `if __name__ == "__main__":` block ([`symbolic_system/symbolic_contradiction_cluster.py:56-61`](../../symbolic_system/symbolic_contradiction_cluster.py:56)) serves as a very basic, inline demonstration for a single scenario.
-   **Coverage Gaps:**
    -   No tests for empty input `forecasts` list.
    -   No tests for forecasts missing essential keys (to see how default fallbacks behave).
    -   No tests for scenarios with no conflicts.
    -   No tests for multiple conflict groups across different `origin_turn`s.
    -   No tests for multiple conflicts within the same `origin_turn` involving more than two forecasts.

## 9. Module Architecture and Flow

The module's architecture is simple, centered around two functions:

1.  **[`cluster_symbolic_conflicts(forecasts)`](../../symbolic_system/symbolic_contradiction_cluster.py:16):**
    *   **Grouping:** Forecasts are first grouped by their `origin_turn` into a dictionary where keys are turn numbers and values are lists of forecasts for that turn.
    *   **Pairwise Comparison:** For each turn's group, all unique pairs of forecasts are generated using `itertools.combinations`.
    *   **Conflict Detection:** Each pair is checked against predefined conflict conditions:
        1.  **Hope vs Despair Paradox:** If the absolute difference in 'hope' values AND 'despair' values between the two forecasts both exceed `0.6`.
        2.  **Arc Conflict:** If the `arc_label` values of the two forecasts are different.
    *   **Result Aggregation:** Identified conflicts (including trace IDs of conflicting forecasts and the reason) are collected.
    *   **Return Value:** A list of dictionaries is returned, each containing an `origin_turn` and a list of `conflicts` found for that turn.

2.  **[`summarize_contradiction_clusters(conflict_clusters)`](../../symbolic_system/symbolic_contradiction_cluster.py:46):**
    *   **Input:** Takes the list of conflict clusters generated by the first function.
    *   **Iteration & Formatting:** Iterates through each cluster and then through each conflict within that cluster.
    *   **Output:** Prints a formatted summary of the contradictions to the standard output (CLI).

The control flow is sequential within each function, involving iteration, dictionary lookups, and conditional checks.

## 10. Naming Conventions

-   **Module Name:** `symbolic_contradiction_cluster.py` is descriptive and follows Python conventions.
-   **Function Names:** [`cluster_symbolic_conflicts()`](../../symbolic_system/symbolic_contradiction_cluster.py:16) and [`summarize_contradiction_clusters()`](../../symbolic_system/symbolic_contradiction_cluster.py:46) use `snake_case` and are descriptive of their actions.
-   **Variable Names:**
    -   Generally clear and follow `snake_case` (e.g., `turn_map`, `conflict_clusters`, `origin_turn`, `hgap`, `dgap`).
    -   Short variable names like `f1`, `f2` (for forecasts), `s1`, `s2` (for symbolic changes), `c` (for cluster), `a`, `b` (for trace_ids in summary) are used in limited scopes where their meaning is clear from context.
-   **Docstrings:** The module and functions have docstrings explaining their purpose. The author is listed as "Pulse v0.40" ([`symbolic_system/symbolic_contradiction_cluster.py:9`](../../symbolic_system/symbolic_contradiction_cluster.py:9)), suggesting AI or automated generation.
-   **Consistency:** Naming appears consistent with common Python (PEP 8) styling. No obvious AI assumption errors in naming were noted.