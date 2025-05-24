# Module Analysis: capital_engine/capital_digest_formatter.py

## 1. Module Path

[`capital_engine/capital_digest_formatter.py`](capital_engine/capital_digest_formatter.py:1)

## 2. Purpose & Functionality

This module is responsible for generating human-readable, Markdown-formatted summaries of capital-related data. Specifically, it formats:
- Shortview capital forecasts, including symbolic fragility, symbolic changes, and capital delta.
- Portfolio snapshots, listing assets and their values.
- Portfolio alignment tags.

The generated Markdown is intended for use in various parts of the Pulse application, such as the Strategos Digest, command-line interface (CLI) operator views, and learning log snapshots, providing clear and concise representations of complex capital and symbolic alignment information.

## 3. Key Components / Classes / Functions

The module consists of several key functions:

- **[`format_shortview_markdown(forecast: Dict[str, Any]) -> str`](capital_engine/capital_digest_formatter.py:17):**
    - Takes a dictionary representing a shortview capital forecast.
    - Expected keys in the `forecast` dictionary include `duration_days`, `symbolic_fragility`, `symbolic_change`, `capital_delta`, and `portfolio_alignment`.
    - Returns a Markdown string summarizing the forecast, including duration, fragility index, symbolic overlay changes, capital delta, and alignment tags.
    - Handles missing or malformed data gracefully by inserting '?' or default messages.

- **[`render_portfolio_snapshot(snapshot: Dict[str, Union[float, str]]) -> str`](capital_engine/capital_digest_formatter.py:92):**
    - Takes a dictionary mapping asset names to their values.
    - Returns a Markdown string listing each asset and its formatted value.
    - Handles empty snapshots and non-numeric values gracefully.

- **[`summarize_alignment_tags(tags: Dict[str, str]) -> str`](capital_engine/capital_digest_formatter.py:113):**
    - Takes a dictionary of portfolio alignment tags.
    - Returns a Markdown string listing each tag and its value.
    - Handles cases with no tags.

- **[`_test()`](capital_engine/capital_digest_formatter.py:132):**
    - A private helper function used for minimal inline testing of the formatting functions. It demonstrates usage with both valid and somewhat invalid/missing data. This function is executed when the script is run directly (`if __name__ == "__main__":`).

## 4. Dependencies

- **Internal Pulse Modules:**
    - No direct imports from other custom Pulse modules are present within this file. It functions as a standalone utility formatter.
- **External Libraries:**
    - `typing` (standard Python library): Used for type hinting (`Dict`, `Any`, `Optional`, `Union`).

## 5. SPARC Analysis

-   **Specification:**
    -   **Clarity of Purpose:** The module's purpose is clearly stated in its docstring ([`capital_engine/capital_digest_formatter.py:1-5`](capital_engine/capital_digest_formatter.py:1)): "Generates markdown-formatted summaries of shortview capital forecasts and symbolic alignment insights."
    -   **Well-Defined Requirements:** The requirements for input data structures (dictionaries with specific keys) and output format (Markdown) are well-defined within the docstrings of each function (e.g., [`format_shortview_markdown`](capital_engine/capital_digest_formatter.py:17)).

-   **Architecture & Modularity:**
    -   **Structure:** The module is well-structured, consisting of a few distinct, focused functions.
    -   **Responsibilities:** Each function has a clear and single responsibility (formatting a specific piece of capital-related information). This promotes reusability and maintainability.
    -   **Modularity:** The module is highly modular and can be easily used by other parts of the `capital_engine` or the broader Pulse application that require Markdown summaries of capital data.

-   **Refinement - Testability:**
    -   **Existing Tests:** The module includes a `_test()` function ([`capital_engine/capital_digest_formatter.py:132`](capital_engine/capital_digest_formatter.py:132)) which provides basic inline tests for the formatting functions. This demonstrates testability with sample valid and invalid inputs.
    -   **Design for Testability:** The functions are pure (they take inputs and produce outputs without side effects, other than the `print` statements in `_test`), making them inherently easy to test with standard unit testing frameworks.

-   **Refinement - Maintainability:**
    -   **Clarity & Readability:** The code is clear, readable, and uses descriptive variable and function names.
    -   **Documentation:** The module and its functions are well-documented with docstrings explaining their purpose, arguments, and return values. Inline comments are used where appropriate.
    -   **Error Handling:** The functions include `try-except` blocks to handle potential `TypeError` or `ValueError` exceptions during data conversion (e.g., converting to `float`), ensuring robustness when encountering malformed input data.

-   **Refinement - Security:**
    -   **Security Concerns:** No obvious security concerns were identified. The module primarily performs string formatting on data passed to it. It does not handle authentication, authorization, direct file I/O (outside of `print` in `_test`), or network communication. If the input data itself is sensitive, the calling modules are responsible for its handling prior to formatting.

-   **Refinement - No Hardcoding:**
    -   **Formatting Strings:** Markdown section headers (e.g., "### 🧠 Shortview Capital Forecast") are hardcoded. This is generally acceptable and expected for a module dedicated to producing a specific Markdown output format.
    -   **Thresholds/Parameters:** No critical operational thresholds, business logic parameters, or sensitive configuration values appear to be hardcoded. The module formats the data it receives.

## 6. Identified Gaps & Areas for Improvement

-   **Formal Unit Tests:** While the inline `_test()` function ([`capital_engine/capital_digest_formatter.py:132`](capital_engine/capital_digest_formatter.py:132)) is a good start, creating formal unit tests using a framework like `pytest` would be beneficial. This would allow for more comprehensive testing of various scenarios, edge cases, and easier integration into an automated testing pipeline.
-   **Configuration for Headers/Prefixes:** While not strictly necessary, if the exact wording of Markdown headers (e.g., "### 🧠 Shortview Capital Forecast") needed to be configurable or localized in the future, this could be an area for enhancement. Currently, they are fixed.
-   **Extensibility for New Fields:** The `format_shortview_markdown` function ([`capital_engine/capital_digest_formatter.py:17`](capital_engine/capital_digest_formatter.py:17)) processes a fixed set of expected keys. If new fields are frequently added to the `forecast` dictionary, the function would need manual updates. A more data-driven approach could be considered if this becomes a frequent maintenance point, but for the current scope, it's adequate.

## 7. Overall Assessment & Next Steps

-   **Overall Assessment:**
    -   The [`capital_engine/capital_digest_formatter.py`](capital_engine/capital_digest_formatter.py:1) module is a well-written, focused, and maintainable utility. It effectively serves its purpose of converting capital-related data structures into human-readable Markdown.
    -   It adheres well to SPARC principles, particularly in terms of specification, modularity, and maintainability.
    -   The inclusion of type hints and basic inline tests enhances its quality.
-   **Next Steps:**
    -   **Primary Recommendation:** Develop a formal suite of unit tests (e.g., using `pytest`) to cover various input scenarios and ensure long-term reliability.
    -   Consider if any part of the formatting (like headers) might need to be configurable in the future, though this is a low priority.
    -   No immediate, critical changes are required for its current functionality.