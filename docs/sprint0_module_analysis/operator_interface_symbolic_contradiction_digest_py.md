# Module Analysis: `operator_interface/symbolic_contradiction_digest.py`

## 1. Module Intent/Purpose

The primary role of [`operator_interface/symbolic_contradiction_digest.py`](operator_interface/symbolic_contradiction_digest.py:1) is to process symbolic contradiction cluster events from a log file and render them into a human-readable Markdown summary.

As stated in its docstring (lines 4-5):
> Renders markdown summaries of symbolic contradiction clusters.
> Used in Strategos Digest, foresight trust audits, and symbolic drift visualization.

It achieves this by loading relevant log entries, formatting them, and exporting the result as a Markdown file.

## 2. Operational Status/Completeness

The module appears to be **complete and operational** for its defined scope.
- It successfully loads data, formats it, and writes output.
- Error handling for file operations (loading and saving) is implemented.
- There are no explicit `TODO` comments or obvious placeholders suggesting unfinished work within its current functionality.

## 3. Implementation Gaps / Unfinished Next Steps

- **No major gaps for current scope:** The module is small and focused. There are no strong indications that it was intended to be significantly more extensive than it currently is.
- **No implied missing features:** For the task of digesting contradiction clusters into Markdown, the existing functionality seems sufficient.
- **Development appears complete:** The module fulfills its stated purpose without obvious deviations or abrupt stops in development.

## 4. Connections & Dependencies

### Direct Imports:
-   **Standard Libraries:**
    -   [`os`](https://docs.python.org/3/library/os.html): Used for path manipulation (e.g., [`os.path.exists`](operator_interface/symbolic_contradiction_digest.py:19), [`os.makedirs`](operator_interface/symbolic_contradiction_digest.py:43), [`os.path.dirname`](operator_interface/symbolic_contradiction_digest.py:43)).
    -   [`json`](https://docs.python.org/3/library/json.html): Used for parsing JSON lines from the input log file ([`json.loads`](operator_interface/symbolic_contradiction_digest.py:23)).
    -   `typing.List`, `typing.Dict`: For type hinting.
-   **Project Modules:**
    -   `from core.path_registry import PATHS`: Imports the `PATHS` object from [`core/path_registry.py`](core/path_registry.py) to resolve the path for the learning log.

### External Library Dependencies:
-   None beyond the standard Python library.

### Interaction with Other Modules via Shared Data:
-   **Input:** Reads from a JSONL (JSON Lines) file, the path to which is retrieved via `PATHS.get("LEARNING_LOG", "logs/pulse_learning_log.jsonl")` (line 15). This implies a dependency on whatever module(s) produce this `pulse_learning_log.jsonl` file and the structure of its entries.
-   **Output:** Writes a Markdown file, by default to `"logs/symbolic_contradiction_digest.md"` (line 16). This digest can then be consumed by other processes or for manual review.

### Input/Output Files:
-   **Input File:**
    -   `LEARNING_LOG`: Default path is [`logs/pulse_learning_log.jsonl`](logs/pulse_learning_log.jsonl:0) (line 15). The module filters lines containing the string `'symbolic_contradiction_cluster'` (line 23).
-   **Output File:**
    -   `DIGEST_OUT`: Default path is [`logs/symbolic_contradiction_digest.md`](logs/symbolic_contradiction_digest.md:0) (line 16).

## 5. Function and Class Example Usages

The module consists of functions. There are no classes.

-   **[`load_symbolic_conflict_events() -> List[Dict]`](operator_interface/symbolic_contradiction_digest.py:18):**
    -   **Purpose:** Loads and parses log entries that represent symbolic contradiction clusters from the `LEARNING_LOG` file.
    -   **Usage:** Called internally by [`export_contradiction_digest_md()`](operator_interface/symbolic_contradiction_digest.py:39).
    ```python
    # Example (conceptual, as it's usually called internally)
    # Assuming LEARNING_LOG exists and has relevant entries
    conflict_events = load_symbolic_conflict_events()
    # conflict_events would be a list of dictionaries, e.g.:
    # [
    #   {"event_type": "symbolic_contradiction_cluster", "data": {"origin_turn": 5, "conflicts": [["A", "B", "Reason1"]]}},
    #   ...
    # ]
    ```

-   **[`format_contradiction_cluster_md(clusters: List[Dict]) -> str`](operator_interface/symbolic_contradiction_digest.py:28):**
    -   **Purpose:** Formats a list of contradiction cluster dictionaries into a Markdown string.
    -   **Usage:** Called internally by [`export_contradiction_digest_md()`](operator_interface/symbolic_contradiction_digest.py:39).
    ```python
    # Example (conceptual)
    clusters_data = [
        {"data": {"origin_turn": 10, "conflicts": [["sym1", "sym2", "Contradiction A"], ["sym3", "sym4", "Contradiction B"]]}},
        {"data": {"origin_turn": 12, "conflicts": [["symX", "symY", "Contradiction C"]]}}
    ]
    markdown_output = format_contradiction_cluster_md(clusters_data)
    # markdown_output would be a string like:
    # "### ♻️ Symbolic Contradiction Digest\n\n#### 🌀 Origin Turn: 10\n- `sym1` vs `sym2` → **Contradiction A**\n- `sym3` vs `sym4` → **Contradiction B**\n\n#### 🌀 Origin Turn: 12\n- `symX` vs `symY` → **Contradiction C**\n"
    ```

-   **[`export_contradiction_digest_md(path: str = DIGEST_OUT)`](operator_interface/symbolic_contradiction_digest.py:39):**
    -   **Purpose:** Main function to orchestrate the loading of conflict events, formatting them into Markdown, and writing the output to a specified file.
    -   **Usage:** This is the primary entry point for using the module's functionality. It can be called directly or run as a script.
    ```python
    # To generate the digest at the default location:
    export_contradiction_digest_md()

    # To generate the digest at a custom location:
    export_contradiction_digest_md(path="custom_reports/contradictions.md")
    ```
    The `if __name__ == "__main__":` block (line 50) calls [`export_contradiction_digest_md()`](operator_interface/symbolic_contradiction_digest.py:51), allowing the script to be run directly from the command line to produce the digest.

## 6. Hardcoding Issues

-   **Default File Paths:**
    -   `LEARNING_LOG = PATHS.get("LEARNING_LOG", "logs/pulse_learning_log.jsonl")` (line 15): The fallback path `"logs/pulse_learning_log.jsonl"` is hardcoded. If `PATHS` registry doesn't define `LEARNING_LOG`, this default is used.
    -   `DIGEST_OUT = "logs/symbolic_contradiction_digest.md"` (line 16): The default output path for the Markdown digest is hardcoded.
-   **Log Filtering String:**
    -   The string `'symbolic_contradiction_cluster'` (line 23) used to identify relevant log lines is hardcoded. Changes in the log event naming would require updating this string.
-   **Markdown Formatting Strings:**
    -   Various Markdown structural elements and labels are hardcoded within [`format_contradiction_cluster_md`](operator_interface/symbolic_contradiction_digest.py:28), such as:
        -   `"### ♻️ Symbolic Contradiction Digest\n"` (line 29)
        -   `"#### 🌀 Origin Turn: {turn}"` (line 32)
        -   The format `"- `{a}` vs `{b}` → **{reason}**"` (line 35)
-   **JSON Structure Keys:**
    -   The function [`format_contradiction_cluster_md`](operator_interface/symbolic_contradiction_digest.py:28) expects specific keys in the input dictionaries: `"data"`, `"origin_turn"`, and `"conflicts"` (lines 31, 33).

## 7. Coupling Points

-   **Input Data Structure:** The module is tightly coupled to the expected JSON structure of events within the `LEARNING_LOG` file. Specifically, it relies on the presence and structure of the `'symbolic_contradiction_cluster'` events, including nested keys like `data`, `origin_turn`, and `conflicts`.
-   **Path Registry:** Dependency on [`core.path_registry.PATHS`](core/path_registry.py:0) for resolving the `LEARNING_LOG` path. If this registry changes or fails to provide the path, the module falls back to a hardcoded default.
-   **Output Format:** While generating Markdown, the specific structure and styling are determined within this module. Consumers of this Markdown file (e.g., "Strategos Digest") would be coupled to this format.

## 8. Existing Tests

-   **No dedicated unit tests:** Based on the provided file list, there is no apparent dedicated test file (e.g., `tests/operator_interface/test_symbolic_contradiction_digest.py`).
-   **Script execution:** The `if __name__ == "__main__":` block (lines 50-51) allows the script to be run directly. This can serve as a basic form of integration testing, verifying that the script runs and produces an output file if the input log exists and is correctly formatted. However, it doesn't cover edge cases or specific function behaviors systematically.

## 9. Module Architecture and Flow

The module follows a simple linear flow:

1.  **Initialization:** Defines default input (`LEARNING_LOG`) and output (`DIGEST_OUT`) paths. The `LEARNING_LOG` path is preferentially sourced from [`core.path_registry.PATHS`](core/path_registry.py:0).
2.  **Main Export Function (`export_contradiction_digest_md`)**:
    a.  Calls [`load_symbolic_conflict_events()`](operator_interface/symbolic_contradiction_digest.py:18) to get data.
    b.  [`load_symbolic_conflict_events()`](operator_interface/symbolic_contradiction_digest.py:18):
        i.  Checks if `LEARNING_LOG` exists. Returns empty list if not.
        ii. Reads the `LEARNING_LOG` file line by line.
        iii. Parses each line as JSON.
        iv. Filters for lines containing `'symbolic_contradiction_cluster'`.
        v.  Returns a list of these parsed JSON objects (dictionaries). Includes basic error handling for file loading.
    c.  The list of cluster events is passed to [`format_contradiction_cluster_md()`](operator_interface/symbolic_contradiction_digest.py:28).
    d.  [`format_contradiction_cluster_md()`](operator_interface/symbolic_contradiction_digest.py:28):
        i.  Initializes a list of strings with a main header.
        ii. Iterates through each cluster:
            - Extracts `origin_turn` and `conflicts` from the cluster data.
            - Formats this information into Markdown lines.
        iii. Joins all formatted lines into a single Markdown string.
    e.  The generated Markdown string is written to the specified output `path` (defaulting to `DIGEST_OUT`). Ensures the output directory exists. Includes basic error handling for file writing.
3.  **Script Execution:** If run as `__main__`, it calls [`export_contradiction_digest_md()`](operator_interface/symbolic_contradiction_digest.py:39) with default settings.

## 10. Naming Conventions

-   **Module Name:** `symbolic_contradiction_digest.py` - Clear and descriptive.
-   **Function Names:**
    -   [`load_symbolic_conflict_events`](operator_interface/symbolic_contradiction_digest.py:18)
    -   [`format_contradiction_cluster_md`](operator_interface/symbolic_contradiction_digest.py:28)
    -   [`export_contradiction_digest_md`](operator_interface/symbolic_contradiction_digest.py:39)
    All use `snake_case` and are descriptive, adhering to PEP 8.
-   **Constant Variables:**
    -   `LEARNING_LOG` (line 15)
    -   `DIGEST_OUT` (line 16)
    Both use `UPPER_SNAKE_CASE`, adhering to PEP 8 for constants.
-   **Local Variables:**
    -   `clusters`, `lines`, `c` (for cluster), `turn`, `conflicts`, `a`, `b`, `reason`, `md`, `path`, `f` (for file handle), `e` (for exception) are generally clear and follow `snake_case` or are conventional single-letter iterators/exception variables.
-   **Overall:** Naming conventions are consistent and follow Python community standards (PEP 8). There are no obvious AI assumption errors in naming.