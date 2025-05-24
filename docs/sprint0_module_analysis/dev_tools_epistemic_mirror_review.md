# Module Analysis: `dev_tools/epistemic_mirror_review.py`

## 1. Module Intent/Purpose

The [`dev_tools/epistemic_mirror_review.py`](dev_tools/epistemic_mirror_review.py:1) module serves as a utility to help developers review and understand data related to "epistemic mirroring." This involves summarizing "foreign causal fingerprints" (likely causal relationships identified by external models like GPT that are not yet in Pulse's native model) and "divergence logs" (records of discrepancies or differences found during forecast comparisons or model interactions). The tool aims to provide insights for operator review and to inform curriculum learning within the Pulse system.

## 2. Key Functionalities

*   **Argument Parsing:** Uses `argparse` to accept command-line flags:
    *   `--summarize-foreign-fingerprints`: Triggers the summarization of foreign causal fingerprints.
    *   `--summarize-divergence-log`: Triggers the summarization of the divergence log.
    *   `--export-md <output.md>`: Exports both summaries into a specified Markdown file.
*   **Summarize Foreign Fingerprints ([`summarize_foreign_fingerprints()`](dev_tools/epistemic_mirror_review.py:18)):**
    *   Reads data from a hardcoded JSONL file: [`GPT/foreign_causal_archive.jsonl`](GPT/foreign_causal_archive.jsonl).
    *   Counts occurrences of unique "variable: consequence" pairs.
    *   Prints a summary of these counts to the console.
    *   Handles `FileNotFoundError` if the archive is missing.
*   **Summarize Divergence Log ([`summarize_divergence_log()`](dev_tools/epistemic_mirror_review.py:33)):**
    *   Reads data from a hardcoded JSONL file: [`GPT/gpt_forecast_divergence_log.jsonl`](GPT/gpt_forecast_divergence_log.jsonl).
    *   Counts occurrences of `divergence_type`.
    *   Prints a summary of these counts to the console.
    *   Handles `FileNotFoundError` if the log is missing.
*   **Export Markdown Summary ([`export_md_summary()`](dev_tools/epistemic_mirror_review.py:48)):**
    *   Reads data from both [`GPT/foreign_causal_archive.jsonl`](GPT/foreign_causal_archive.jsonl) and [`GPT/gpt_forecast_divergence_log.jsonl`](GPT/gpt_forecast_divergence_log.jsonl).
    *   Formats the summaries into a Markdown structure.
        *   For foreign fingerprints, it groups consequences by variable.
        *   For divergence logs, it lists counts by `divergence_type`.
    *   Writes the combined summary to the specified output Markdown file.
    *   Handles `FileNotFoundError` for both input files, noting their absence in the output.
*   **Main Execution Block ([`main()`](dev_tools/epistemic_mirror_review.py:77)):**
    *   Parses arguments and calls the appropriate function(s) based on the flags provided.

## 3. Role within `dev_tools/`

This script is a developer utility for inspecting and understanding the outputs of processes that compare Pulse's internal knowledge with external sources or detect divergences in forecasts. It aids in identifying new causal links or areas where Pulse's understanding differs, which can be crucial for model improvement and learning.

## 4. Dependencies

### Internal Pulse Modules:
*   None directly imported as Python modules. However, it relies on the existence and format of:
    *   [`GPT/foreign_causal_archive.jsonl`](GPT/foreign_causal_archive.jsonl)
    *   [`GPT/gpt_forecast_divergence_log.jsonl`](GPT/gpt_forecast_divergence_log.jsonl)

### External Libraries:
*   `argparse`: For command-line argument parsing.
*   `json`: For loading data from JSONL files.
*   `collections.Counter`: For counting item frequencies.
*   `collections.defaultdict`: For grouping items in the Markdown export.

## 5. SPARC Principles Adherence

*   **Module Intent/Purpose:**
    *   Clearly stated in the docstring. The purpose is to summarize specific log files for review.
*   **Operational Status/Completeness:**
    *   Appears operational for its defined scope. It reads, processes, and outputs summaries as described.
    *   Includes basic `FileNotFoundError` handling for its input files.
*   **Implementation Gaps / Unfinished Next Steps:**
    *   The paths to the input files ([`FOREIGN_ARCHIVE`](dev_tools/epistemic_mirror_review.py:15) and [`DIVERGENCE_LOG`](dev_tools/epistemic_mirror_review.py:16)) are hardcoded. Making these configurable via CLI arguments would increase flexibility.
    *   Error handling for JSON parsing within the files could be more robust (currently, a malformed JSON line would cause the script to crash).
*   **Connections & Dependencies:**
    *   Relies heavily on the structure and content of the two JSONL files in the `GPT/` directory.
*   **Function and Class Example Usages:**
    *   Usage examples are provided in the module's docstring:
        ```bash
        python dev_tools/epistemic_mirror_review.py --summarize-foreign-fingerprints
        python dev_tools/epistemic_mirror_review.py --summarize-divergence-log
        python dev_tools/epistemic_mirror_review.py --export-md <output.md>
        ```
*   **Hardcoding Issues:**
    *   The primary hardcoding issue is the paths to [`GPT/foreign_causal_archive.jsonl`](GPT/foreign_causal_archive.jsonl) and [`GPT/gpt_forecast_divergence_log.jsonl`](GPT/gpt_forecast_divergence_log.jsonl).
*   **Coupling Points:**
    *   Tightly coupled to the schema of the JSON objects within the input files (e.g., expects keys like "variable", "consequence", "divergence_type").
*   **Existing Tests:**
    *   Test coverage is not determinable from this file. Tests for this CLI tool would likely involve creating mock input files and verifying console output or the content of the exported Markdown.
*   **Module Architecture and Flow:**
    *   Simple architecture:
        1.  Define file paths.
        2.  Define functions for each summarization/export task.
        3.  [`main()`](dev_tools/epistemic_mirror_review.py:77) function parses arguments and dispatches to the appropriate task function.
    *   The flow is straightforward and suitable for a utility script.
*   **Naming Conventions:**
    *   Follows Python's snake_case for functions and variables, and UPPER_CASE for constants.

## 6. Overall Assessment

*   **Completeness:** The module is complete for its described functionality of summarizing and exporting data from the specified log files.
*   **Quality:** The code is generally clear and readable. The use of `Counter` and `defaultdict` is appropriate. The main area for improvement would be making input file paths configurable and potentially adding more robust error handling for file content. For a `dev_tools` script, its quality is adequate.

## 7. Summary Note for Main Report

The [`dev_tools/epistemic_mirror_review.py`](dev_tools/epistemic_mirror_review.py:1) module provides CLI utilities to summarize "foreign causal fingerprints" from [`GPT/foreign_causal_archive.jsonl`](GPT/foreign_causal_archive.jsonl) and "divergence logs" from [`GPT/gpt_forecast_divergence_log.jsonl`](GPT/gpt_forecast_divergence_log.jsonl), with an option to export findings to Markdown.