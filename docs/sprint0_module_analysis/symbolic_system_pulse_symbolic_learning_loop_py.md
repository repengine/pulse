# Module Analysis: `symbolic_system/pulse_symbolic_learning_loop.py`

## 1. Module Intent/Purpose

The primary role of the [`pulse_symbolic_learning_loop.py`](symbolic_system/pulse_symbolic_learning_loop.py:) module is to learn symbolic strategy preferences. It achieves this by analyzing revision logs and repair outcomes from a "tuning engine." The module tracks the performance (recoverability, risk) of symbolic arcs and tags, aiming to inform which strategies should be revised more or less frequently in future operations.

## 2. Operational Status/Completeness

The module appears relatively complete for its defined scope. It includes:
*   Functions to load and parse tuning logs ([`learn_from_tuning_log()`](symbolic_system/pulse_symbolic_learning_loop.py:24)).
*   Logic to score symbolic paths (arcs and tags) based on success/failure ([`score_symbolic_paths()`](symbolic_system/pulse_symbolic_learning_loop.py:58)).
*   A function to generate a learning profile summarizing these scores ([`generate_learning_profile()`](symbolic_system/pulse_symbolic_learning_loop.py:95)).
*   A mechanism to log the generated profile ([`log_symbolic_learning()`](symbolic_system/pulse_symbolic_learning_loop.py:133)).
*   A basic inline test function ([`_test_symbolic_learning_loop()`](symbolic_system/pulse_symbolic_learning_loop.py:151)) for self-checking.

There are no explicit "TODO" comments or obvious major placeholders for its current functionality.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Sophistication of Learning:** The current learning mechanism is based on simple success/failure counts and win rates. More advanced learning algorithms (e.g., Bayesian updating, confidence intervals, or a simple reinforcement learning approach) could provide more nuanced insights.
*   **Input Source Definition:** The module consumes logs from an external "tuning engine," but the specifics of this engine and the generation of its logs are not defined within this module. The interaction is one-way (reading output).
*   **Application of Learning:** While the module generates a "learning profile" intended for "future tuning," the exact mechanism or downstream modules that consume and apply this profile are not detailed here.
*   **Data Aging/Weighting:** There's no apparent mechanism to age out old data from the learning log or to give more weight to recent revision outcomes. The profile is generated from all records in the input log each time.
*   **Error Handling in Profile Application:** The profile identifies "high-confidence upgrades and risk flags," but how these flags translate into actionable changes in the symbolic system's behavior is not part of this module.

## 4. Connections & Dependencies

*   **Direct Project Module Imports:** None.
*   **External Library Dependencies:**
    *   `json`: For loading and dumping data from/to JSONL files.
    *   `os`: For path operations (e.g., [`os.path.exists()`](symbolic_system/pulse_symbolic_learning_loop.py:39)).
    *   `logging`: For internal logging of warnings and errors.
    *   `typing` ([`Dict`](symbolic_system/pulse_symbolic_learning_loop.py:16), [`List`](symbolic_system/pulse_symbolic_learning_loop.py:16), [`Any`](symbolic_system/pulse_symbolic_learning_loop.py:16)): For type hinting.
    *   `collections` ([`Counter`](symbolic_system/pulse_symbolic_learning_loop.py:17)): Imported but not explicitly used in the provided code snippet (though it could be useful for similar counting tasks).
*   **Interaction via Shared Data:**
    *   Reads from a tuning log file, expected in JSONL format, specified via a path argument to [`learn_from_tuning_log()`](symbolic_system/pulse_symbolic_learning_loop.py:24).
    *   Writes (appends) its generated learning profile to a JSONL file, defaulting to [`LEARNING_LOG_PATH`](symbolic_system/pulse_symbolic_learning_loop.py:19) ([`logs/symbolic_learning_log.jsonl`](logs/symbolic_learning_log.jsonl:19)).
*   **Input/Output Files:**
    *   **Input:** A `.jsonl` file containing tuning results (e.g., from a tuning engine). The path is configurable.
    *   **Output:** A `.jsonl` file ([`logs/symbolic_learning_log.jsonl`](logs/symbolic_learning_log.jsonl:19) by default) where generated learning profiles are appended.

## 5. Function and Class Example Usages

The module primarily consists of functions. Their intended usage pattern is:

1.  **Load Data:**
    ```python
    tuning_results = learn_from_tuning_log("path/to/tuning_engine_output.jsonl")
    ```
2.  **Generate Profile:**
    ```python
    learning_profile = generate_learning_profile(tuning_results)
    ```
3.  **Log Profile:**
    ```python
    log_symbolic_learning(learning_profile) # Logs to default path
    # or
    log_symbolic_learning(learning_profile, "custom/path/to/learning_profile.jsonl")
    ```

The [`_test_symbolic_learning_loop()`](symbolic_system/pulse_symbolic_learning_loop.py:151) function provides a concise example of this flow using dummy data.

## 6. Hardcoding Issues

*   **Default Log Path:** [`LEARNING_LOG_PATH = "logs/symbolic_learning_log.jsonl"`](symbolic_system/pulse_symbolic_learning_loop.py:19) hardcodes the default output path for learning profiles. While [`log_symbolic_learning()`](symbolic_system/pulse_symbolic_learning_loop.py:133) allows overriding this, the default is fixed.
*   **Input Data Structure Keys:** The keys used to parse the input dictionaries (e.g., `"symbolic_revision_plan"`, `"arc_label"`, `"symbolic_tag"`, `"revised_license"`, `"timestamp"`) are hardcoded within the functions. Any change in the input log's schema would require code modification.
*   **Success Condition String:** The success of a revision is determined by `r.get("revised_license") == "✅ Approved"`. The string `"✅ Approved"` is hardcoded. This is fragile if the source system changes its success indicators.

## 7. Coupling Points

*   **Input Log Format:** The module is tightly coupled to the specific JSON structure and key names of the input tuning log file.
*   **Output Profile Consumers:** The structure of the output learning profile implicitly defines an interface for downstream consumers (e.g., "future tuning" processes). Changes here would affect those consumers.
*   **Success/Failure Semantics:** The interpretation of what constitutes a "success" (i.e., `"revised_license": "✅ Approved"`) is a critical coupling point with the system that generates the revision logs.

## 8. Existing Tests

*   The module includes an inline test function: [`_test_symbolic_learning_loop()`](symbolic_system/pulse_symbolic_learning_loop.py:151).
*   This function is executed when the script is run directly (`if __name__ == "__main__":`).
*   It uses a small set of `dummy_results` to test the profile generation logic, asserting the presence of expected keys and the total record count.
*   There is no indication of a separate, dedicated test file (e.g., in a `tests/symbolic_system/` directory) for this module based on the provided file listing. Coverage is limited to this internal test.

## 9. Module Architecture and Flow

The module follows a simple, sequential batch-processing architecture:

1.  **Load Data:** The [`learn_from_tuning_log()`](symbolic_system/pulse_symbolic_learning_loop.py:24) function reads all entries from the specified JSONL input file. It performs basic validation (path is string, ends with `.jsonl`, file exists) and handles JSON decoding errors.
2.  **Score Paths:** The [`score_symbolic_paths()`](symbolic_system/pulse_symbolic_learning_loop.py:58) function iterates through the loaded results. For each entry, it extracts the `arc_label` and `symbolic_tag` from the `symbolic_revision_plan` and checks the `revised_license` to determine if it was a success or failure. It aggregates these into counts for each arc and tag.
3.  **Generate Profile:** The [`generate_learning_profile()`](symbolic_system/pulse_symbolic_learning_loop.py:95) function takes these scores, calculates win rates (`success / total`), and ranks arcs and tags by their win rate. It also includes metadata like the timestamp of the last record and the total number of records processed.
4.  **Log Profile:** The [`log_symbolic_learning()`](symbolic_system/pulse_symbolic_learning_loop.py:133) function appends the generated profile (as a JSON string) to the specified log file.

Logging is used throughout to report warnings (e.g., malformed input, file not found) and errors (e.g., JSON decoding issues, failure to write log).

## 10. Naming Conventions

*   **Functions and Variables:** Generally adhere to PEP 8 standards, using `snake_case` (e.g., [`learn_from_tuning_log`](symbolic_system/pulse_symbolic_learning_loop.py:24), `arc_scores`).
*   **Constants:** The global constant [`LEARNING_LOG_PATH`](symbolic_system/pulse_symbolic_learning_loop.py:19) is in `UPPER_SNAKE_CASE`, which is appropriate.
*   **Clarity:** Names are generally descriptive and clearly indicate the purpose of functions and variables (e.g., `symbolic_revision_plan`, `win_rate`).
*   **Consistency:** Terms like `arc_label`, `symbolic_tag`, `profile`, `results` are used consistently.
*   **AI Assumption Errors:** No obvious errors in naming that would suggest misinterpretation by an AI or deviation from common Python practices.