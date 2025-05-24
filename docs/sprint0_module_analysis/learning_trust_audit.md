# Module Analysis: `learning/trust_audit.py`

## 1. Module Path

[`learning/trust_audit.py`](learning/trust_audit.py:1)

## 2. Purpose & Functionality

The [`learning/trust_audit.py`](learning/trust_audit.py:1) module is designed to provide a strategic summary and audit of recent forecasts stored in the "foresight memory." Its primary functions include:

*   Calculating and reporting counts of forecasts within different trust bands (Trusted, Moderate, Fragile).
*   Computing and reporting average scores for confidence, fragility, and retrodiction of these forecasts.
*   Tracking and reporting age statistics of forecasts (average and maximum age).
*   Performing a "trust loop integrity check" to identify inconsistencies, such as:
    *   Trusted forecasts exhibiting low retrodiction scores or high fragility.
    *   Fragile forecasts showing unexpectedly high confidence scores.
*   Handling potentially compressed forecast formats by expanding them for individual analysis.

This module acts as a crucial checkpoint, typically used after simulation runs, to assess the reliability and health of the forecasting mechanisms and the trust system's calibration.

## 3. Key Components / Classes / Functions

*   **[`trust_band(trace)`](learning/trust_audit.py:22):**
    *   Determines the trust band for a given forecast trace based on its confidence score.
    *   Categories: "🟢 Trusted" (confidence >= 0.75), "⚠️ Moderate" (confidence >= 0.5), "🔴 Fragile" (confidence < 0.5).
*   **[`trust_loop_integrity_issues(forecasts)`](learning/trust_audit.py:32):**
    *   Analyzes a list of forecasts to detect potential integrity failures in the trust assessment logic.
    *   Identifies trusted forecasts with low retrodiction (`< 0.5`) or high fragility (`> 0.7`).
    *   Identifies fragile forecasts with high confidence (`> 0.7`).
    *   Returns a list of warning messages detailing any issues found.
*   **[`audit_forecasts(memory=None, recent_n: int = 10)`](learning/trust_audit.py:62):**
    *   The main function that orchestrates the trust audit.
    *   Retrieves the `recent_n` latest forecasts from memory (e.g., [`PFPA_ARCHIVE`](forecast_output/pfpa_logger.py:1) via [`get_latest_forecasts()`](forecast_output/pfpa_logger.py:1)) or uses a provided `memory` object.
    *   Expands forecasts if they are in a compressed format (containing an "examples" list).
    *   Calculates statistics for trust bands, average confidence, fragility, retrodiction, priority, and age.
    *   Logs a formatted report of these statistics.
    *   Calls [`trust_loop_integrity_issues()`](learning/trust_audit.py:32) and logs any detected integrity problems.
*   **[`audit_trust()`](learning/trust_audit.py:58):**
    *   Currently appears to be a placeholder function with only a logging statement. It is not called by other functions in the module.

## 4. Dependencies

### Internal Pulse Modules:

*   **[`forecast_output.pfpa_logger`](forecast_output/pfpa_logger.py:1):**
    *   [`PFPA_ARCHIVE`](forecast_output/pfpa_logger.py:1) (imported but not directly used in the snippet, implies interaction with a forecast archive).
    *   [`get_latest_forecasts()`](forecast_output/pfpa_logger.py:1) (used to fetch recent forecast data).
*   **[`utils.log_utils`](utils/log_utils.py:1):**
    *   [`get_logger()`](utils/log_utils.py:1) (for application-wide logging).
*   **[`core.pulse_config`](core/pulse_config.py:1):**
    *   [`CONFIDENCE_THRESHOLD`](core/pulse_config.py:1) (imported but notably not used in [`trust_band()`](learning/trust_audit.py:22) which uses hardcoded values).
    *   [`MODULES_ENABLED`](core/pulse_config.py:1) (imported but not used in the provided snippet).

### External Libraries:

*   **`statistics`:**
    *   [`mean()`](https://docs.python.org/3/library/statistics.html#statistics.mean) (used for calculating average scores).

## 5. SPARC Analysis

*   **Specification:**
    *   **Clarity:** The module's purpose is clearly stated in its docstring: to provide a strategic summary of recent foresight memory and act as a checkpoint.
    *   **Requirements Definition:** Requirements are implicitly defined by the metrics calculated and the integrity checks performed. The specific thresholds for these checks are embedded in the code.

*   **Architecture & Modularity:**
    *   **Structure:** The module is well-structured with functions dedicated to specific sub-tasks (determining trust bands, checking integrity, the main audit logic).
    *   **Responsibilities:** Functions have clear, distinct responsibilities, contributing to modularity.

*   **Refinement - Testability:**
    *   **Existing Tests:** No unit tests are present within this module file. The broader test suite would need to be examined to confirm coverage.
    *   **Design for Testability:**
        *   [`trust_band()`](learning/trust_audit.py:22) and [`trust_loop_integrity_issues()`](learning/trust_audit.py:32) are pure functions (dependent only on their inputs) and are thus highly testable.
        *   [`audit_forecasts()`](learning/trust_audit.py:62) has side effects (logging) and external dependencies ([`get_latest_forecasts()`](forecast_output/pfpa_logger.py:1)). The ability to pass `memory` as an argument is good for testability, allowing injection of test data. The logger could also be injected for more isolated testing.

*   **Refinement - Maintainability:**
    *   **Clarity & Readability:** The code is generally clear, with descriptive variable and function names.
    *   **Documentation:** The module has a good top-level docstring, and most functions also have docstrings explaining their purpose.
    *   **Complexity:** The logic for handling compressed forecasts within [`audit_forecasts()`](learning/trust_audit.py:62) introduces some nesting but remains manageable.

*   **Refinement - Security:**
    *   **Obvious Concerns:** No direct security vulnerabilities are apparent within this module. It primarily reads and processes data. Its security is contingent on the security of the data sources it reads from (e.g., `PFPA_ARCHIVE`).

*   **Refinement - No Hardcoding:**
    *   **Thresholds:**
        *   The [`trust_band()`](learning/trust_audit.py:22) function uses hardcoded confidence thresholds (`0.75`, `0.5`) for categorizing forecasts, despite [`CONFIDENCE_THRESHOLD`](core/pulse_config.py:1) being imported from [`core.pulse_config`](core/pulse_config.py:1). This is an inconsistency and a point for improvement.
        *   The [`trust_loop_integrity_issues()`](learning/trust_audit.py:32) function uses hardcoded thresholds for retrodiction (`0.5`) and fragility (`0.7`).
    *   **Parameters:** The `recent_n` parameter in [`audit_forecasts()`](learning/trust_audit.py:62) has a default value of `10`, which is acceptable as a configurable default.
    *   **Paths:** No file paths are hardcoded directly for data input beyond what might be configured within `PFPA_ARCHIVE`.

## 6. Identified Gaps & Areas for Improvement

*   **Hardcoded Thresholds:** Critical thresholds in [`trust_band()`](learning/trust_audit.py:22) (lines 24, 26) and [`trust_loop_integrity_issues()`](learning/trust_audit.py:32) (lines 47, 50, 53) should be sourced from configuration (e.g., [`core.pulse_config`](core/pulse_config.py:1)) rather than being hardcoded. This would improve consistency and configurability.
*   **Unused Import/Functionality:**
    *   [`CONFIDENCE_THRESHOLD`](core/pulse_config.py:1) is imported but not utilized where it seems most relevant (in [`trust_band()`](learning/trust_audit.py:22)).
    *   The [`audit_trust()`](learning/trust_audit.py:58) function appears to be a stub and is not used. It should either be implemented or removed.
*   **Test Coverage:** The module would benefit from dedicated unit tests, especially for [`trust_band()`](learning/trust_audit.py:22), [`trust_loop_integrity_issues()`](learning/trust_audit.py:32), and the forecast expansion logic within [`audit_forecasts()`](learning/trust_audit.py:62).
*   **Logging Consistency:** While logging is used, ensuring consistent log levels and messages across the application could be beneficial.
*   **Error Handling:** The forecast expansion logic includes basic type checking and warnings for unexpected data structures (lines 81, 85). More robust error handling or schema validation for forecast objects could be considered if input data quality is variable.
*   **Clarity of "Fragility":** The code uses `f.get("fragility_score", f.get("fragility", 0))` (line 91). Clarifying the primary source for fragility and the reason for a fallback could improve understanding.

## 7. Overall Assessment & Next Steps

The [`learning/trust_audit.py`](learning/trust_audit.py:1) module is a valuable component for monitoring and understanding the performance and reliability of the Pulse system's forecasts. It is generally well-written, modular, and serves a clear, important purpose within the `learning/` subsystem. Its role is to provide actionable insights into the trust metrics of generated forecasts, which is crucial for iterative improvement of the learning and trust mechanisms.

**Quality:** Good, with clear areas for enhancement.

**Completeness:** Mostly complete for its defined scope, with the exception of the unused [`audit_trust()`](learning/trust_audit.py:58) function and the reliance on some hardcoded values.

**Next Steps:**

1.  **Refactor Hardcoded Thresholds:** Modify the module to use centrally configured thresholds from [`core.pulse_config`](core/pulse_config.py:1) for confidence, retrodiction, and fragility.
2.  **Address [`audit_trust()`](learning/trust_audit.py:58):** Decide whether to fully implement this function or remove it if it's redundant.
3.  **Develop Unit Tests:** Create unit tests for key functions to ensure correctness and facilitate future refactoring.
4.  **Review `PFPA_ARCHIVE` Interaction:** Confirm how [`PFPA_ARCHIVE`](forecast_output/pfpa_logger.py:1) is utilized and if its interaction can be made more explicit or testable if it's a global object.
5.  **Clarify Fragility Source:** Add comments or refactor to make the source of the `fragility` metric clearer.