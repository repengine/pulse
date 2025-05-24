# Module Analysis: `operator_interface/mutation_digest_exporter.py`

## 1. Module Intent/Purpose

The primary role of [`operator_interface/mutation_digest_exporter.py`](operator_interface/mutation_digest_exporter.py:1) is to generate a unified Markdown digest. This digest consolidates information about:
- Rule cluster volatility
- Variable cluster instability
- Recent learning/mutation events

The generated report is intended for use in "Strategos Digest," weekly foresight reports, and trust evolution audits, as stated in its docstring.

## 2. Operational Status/Completeness

The module appears to be functionally complete for its defined scope. It contains two primary functions:
- [`render_learning_summary_md(limit: int = 15)`](operator_interface/mutation_digest_exporter.py:25): Formats recent learning events into Markdown.
- [`export_full_digest()`](operator_interface/mutation_digest_exporter.py:36): Orchestrates the creation of the full digest by calling helper formatters and [`render_learning_summary_md()`](operator_interface/mutation_digest_exporter.py:25), then writes the output to a file.

The module includes a `if __name__ == "__main__":` block, allowing it to be executed directly to produce the digest. There are no explicit "TODO" comments or obvious placeholders indicating unfinished sections. The mention of "Pulse v0.39" suggests it's part of a versioned and operational system.

## 3. Implementation Gaps / Unfinished Next Steps

- **Extensibility:** While complete for its current task, the module is specific. Future enhancements could involve:
    - Support for different output formats (e.g., HTML, JSON) beyond Markdown.
    - More configurable digest content (e.g., selecting specific sections to include/exclude).
    - Integration with a dynamic reporting dashboard rather than a static file.
- **Error Handling:** The [`export_full_digest()`](operator_interface/mutation_digest_exporter.py:36) function has a general `except Exception as e:` block, which is good for catching errors during file I/O. However, errors from the imported formatter functions or [`load_log()`](operator_interface/mutation_log_viewer.py:1) might not be handled with specific user feedback, potentially leading to incomplete digests if those dependencies fail silently or raise exceptions caught by the general handler.
- **Configuration:** Limits for the number of items to display from cluster digests (hardcoded to `5`) and learning events (default `15`) are set within [`export_full_digest()`](operator_interface/mutation_digest_exporter.py:36). These could be made configurable, perhaps via command-line arguments or a configuration file.

There are no strong indications that the module was intended to be significantly more extensive for its current, narrowly defined purpose, nor are there signs of development that started and then stopped short.

## 4. Connections & Dependencies

### Direct Project Module Imports:
- [`operator_interface.rule_cluster_digest_formatter.format_cluster_digest_md`](operator_interface/rule_cluster_digest_formatter.py)
- [`operator_interface.variable_cluster_digest_formatter.format_variable_cluster_digest_md`](operator_interface/variable_cluster_digest_formatter.py)
- [`operator_interface.mutation_log_viewer.load_log`](operator_interface/mutation_log_viewer.py)
- [`core.path_registry.PATHS`](core/path_registry.py)

### External Library Dependencies:
- `os`
- `datetime.datetime`, `datetime.timezone`

### Interaction via Shared Data:
- **Input File:** Reads learning events from a log file specified by `LEARNING_LOG = PATHS.get("LEARNING_LOG", "logs/pulse_learning_log.jsonl")`. This file is presumably written by other system components that log learning and mutation activities.
- The imported formatter functions ([`format_cluster_digest_md`](operator_interface/rule_cluster_digest_formatter.py) and [`format_variable_cluster_digest_md`](operator_interface/variable_cluster_digest_formatter.py)) likely read other data sources (e.g., cluster status files, database entries) to generate their respective parts of the digest, creating indirect data dependencies.

### Input/Output Files:
- **Input:**
    - `LEARNING_LOG`: Default path [`logs/pulse_learning_log.jsonl`](logs/pulse_learning_log.jsonl) (JSON Lines format).
- **Output:**
    - `DIGEST_OUT`: Path [`logs/full_mutation_digest.md`](logs/full_mutation_digest.md) (Markdown format).

## 5. Function and Class Example Usages

- **[`render_learning_summary_md(limit: int = 15) -> str`](operator_interface/mutation_digest_exporter.py:25):**
    - **Purpose:** Loads the most recent `limit` learning/mutation events from the log file and formats them as a Markdown section.
    - **Usage:** Called by [`export_full_digest()`](operator_interface/mutation_digest_exporter.py:36) to include recent learning events in the main digest.
    ```python
    # Example (conceptual, as it's used internally)
    # learning_summary = render_learning_summary_md(limit=10)
    # print(learning_summary)
    ```

- **[`export_full_digest()`](operator_interface/mutation_digest_exporter.py:36):**
    - **Purpose:** Generates the complete mutation digest by combining formatted sections for rule clusters, variable clusters, and learning events. It then writes this digest to a Markdown file.
    - **Usage:** This is the main function of the module. It can be called directly if the script is run as `__main__`.
    ```python
    # To run from command line:
    # python operator_interface/mutation_digest_exporter.py
    ```

## 6. Hardcoding Issues

- **File Paths:**
    - `LEARNING_LOG`: The default path `"logs/pulse_learning_log.jsonl"` is hardcoded as a fallback if not found in `PATHS`.
    - `DIGEST_OUT = "logs/full_mutation_digest.md"`: The output file path is hardcoded.
- **Content Limits:**
    - In [`export_full_digest()`](operator_interface/mutation_digest_exporter.py:36), the `limit` parameter for [`format_cluster_digest_md()`](operator_interface/rule_cluster_digest_formatter.py) and [`format_variable_cluster_digest_md()`](operator_interface/variable_cluster_digest_formatter.py) is hardcoded to `5`.
    - The `limit` for [`render_learning_summary_md()`](operator_interface/mutation_digest_exporter.py:25) is also hardcoded to `15` when called from [`export_full_digest()`](operator_interface/mutation_digest_exporter.py:36).
- **Report Strings:**
    - The report title `"# 🧠 Pulse Mutation Digest"` is hardcoded.
    - The footer `"Pulse v0.39 | Strategos Audit Layer"` is hardcoded, including the version number.
- **Log Entry Structure Assumption:**
    - [`render_learning_summary_md()`](operator_interface/mutation_digest_exporter.py:25) assumes a specific structure for log entries (e.g., keys like `'timestamp'`, `'event_type'`, `'data'`).

## 7. Coupling Points

- **Internal Module Dependencies:** Tightly coupled to the interfaces and output formats of:
    - [`operator_interface.rule_cluster_digest_formatter`](operator_interface/rule_cluster_digest_formatter.py)
    - [`operator_interface.variable_cluster_digest_formatter`](operator_interface/variable_cluster_digest_formatter.py)
    - [`operator_interface.mutation_log_viewer`](operator_interface/mutation_log_viewer.py) (specifically the [`load_log()`](operator_interface/mutation_log_viewer.py:1) function and its expected log entry format).
- **Data Format Dependency:** Relies on the specific JSON Lines format of the `pulse_learning_log.jsonl` file.
- **Configuration Dependency:** Depends on [`core.path_registry.PATHS`](core/path_registry.py) for resolving the path to `LEARNING_LOG`.
- **Output Format:** The primary purpose is to generate a Markdown file ([`logs/full_mutation_digest.md`](logs/full_mutation_digest.md)), making it coupled to Markdown syntax.

## 8. Existing Tests

Based on the provided file list, there is no specific test file named `test_mutation_digest_exporter.py` in the `tests/` or `tests/operator_interface/` directories. There is a file [`tests/test_digest_exporter.py`](tests/test_digest_exporter.py:1), but its name suggests it might be for a different `digest_exporter.py` module (e.g., [`forecast_output/digest_exporter.py`](forecast_output/digest_exporter.py:1)).

**Assessment:** It is likely that this specific module, [`operator_interface/mutation_digest_exporter.py`](operator_interface/mutation_digest_exporter.py:1), does not have dedicated unit tests.
- **Gaps:** Lack of tests means that changes to this module, or its dependencies (like the formatters or log reader), could break its functionality without being caught automatically.
- **Coverage:** Assumed to be low or none for this specific module.

## 9. Module Architecture and Flow

The module's architecture is straightforward:

1.  **Initialization:** Defines constants for the learning log path (`LEARNING_LOG`) and the output digest path (`DIGEST_OUT`).
2.  **Learning Event Rendering (`render_learning_summary_md`)**:
    *   Takes an optional `limit` for the number of log entries.
    *   Calls [`load_log()`](operator_interface/mutation_log_viewer.py:1) (from [`operator_interface.mutation_log_viewer`](operator_interface/mutation_log_viewer.py)) to fetch recent log entries from `LEARNING_LOG`.
    *   Formats these entries into a Markdown string.
3.  **Full Digest Export (`export_full_digest`)**:
    *   This is the main entry point when the script is run.
    *   It assembles a list of Markdown content sections:
        *   A main title.
        *   A generation timestamp.
        *   Content from [`format_cluster_digest_md()`](operator_interface/rule_cluster_digest_formatter.py) (limited to 5 items).
        *   Content from [`format_variable_cluster_digest_md()`](operator_interface/variable_cluster_digest_formatter.py) (limited to 5 items).
        *   Content from [`render_learning_summary_md()`](operator_interface/mutation_digest_exporter.py:25) (limited to 15 items).
        *   A footer.
    *   It creates the output directory if it doesn't exist.
    *   It writes the joined Markdown sections to the `DIGEST_OUT` file.
    *   Includes basic error handling for the file writing process.
4.  **Execution Block**:
    *   The `if __name__ == "__main__":` block calls [`export_full_digest()`](operator_interface/mutation_digest_exporter.py:36), allowing the script to be run directly to generate the report.

**Data Flow:**
- Log data (`.jsonl`) -> [`load_log()`](operator_interface/mutation_log_viewer.py:1) -> Python list of dicts.
- This list, along with outputs from other formatters (presumably also Markdown strings), are combined.
- Combined string -> Written to `.md` file.

## 10. Naming Conventions

- **Modules:** The module name [`mutation_digest_exporter.py`](operator_interface/mutation_digest_exporter.py:1) is descriptive.
- **Functions:** [`render_learning_summary_md`](operator_interface/mutation_digest_exporter.py:25) and [`export_full_digest`](operator_interface/mutation_digest_exporter.py:36) use snake_case and are descriptive of their actions.
- **Constants:** `LEARNING_LOG` and `DIGEST_OUT` use UPPER_SNAKE_CASE, which is standard for Python constants.
- **Variables:** Local variables (e.g., `entries`, `lines`, `e`, `k`, `v`, `digest`) are generally clear and concise for their scope.
- **Parameters:** `limit` is a clear parameter name.
- **Overall:** The naming conventions appear consistent with PEP 8 and are generally easy to understand. No obvious AI-related naming errors or significant deviations from standard Python practices were noted.