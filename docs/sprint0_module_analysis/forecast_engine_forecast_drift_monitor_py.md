# Module Analysis: `forecast_engine/forecast_drift_monitor.py`

## 1. Purpose

The `forecast_drift_monitor.py` module is designed to compare symbolic-tagged forecast cluster summaries from two distinct forecast runs. Its primary objective is to detect "narrative drift" or significant changes in "symbolic trust volatility" between these runs. This helps in understanding the evolution and stability of forecasts over time.

## 2. Key Functionalities

*   **Cluster Normalization:** The module normalizes input forecast clusters, which are lists of dictionaries, into a standardized dictionary format keyed by tags. This involves extracting tags, average confidence (defaulting to 0.5 if missing or invalid), and counts ([`normalize_forecast_clusters()`](../../forecast_engine/forecast_drift_monitor.py:46)).
*   **Drift Scoring:** It calculates a `drift_score` by comparing the normalized `avg_confidence` for each tag between the 'before' and 'after' runs. The score is the average absolute difference in confidence across all tags ([`score_drift()`](../../forecast_engine/forecast_drift_monitor.py:58)).
*   **Symbolic Flip Detection:** Identifies "symbolic flips," which occur when a tag's `avg_confidence` changes significantly (e.g., from > 0.6 in the 'before' run to < 0.4 in the 'after' run) ([`compare_forecast_clusters()`](../../forecast_engine/forecast_drift_monitor.py:76)).
*   **Logging:** Results of the drift analysis, including `run_id`, `drift_score`, `tag_deltas`, and `symbolic_flips`, are logged to a JSONL file (default: [`logs/forecast_drift_log.jsonl`](../../logs/forecast_drift_log.jsonl)).
*   **Advanced Drift Detection (Optional):**
    *   Integrates with the `river` library (if installed) to provide more advanced drift detection mechanisms:
        *   **ADWIN (Adaptive Windowing):** Detects drift in a numeric series using an adaptive window size ([`detect_adwin_drift()`](../../forecast_engine/forecast_drift_monitor.py:121)).
        *   **KSWIN (Kolmogorov-Smirnov Windowing):** Detects drift based on the Kolmogorov-Smirnov test within a sliding window ([`detect_kswin_drift()`](../../forecast_engine/forecast_drift_monitor.py:136)).

## 3. Role within `forecast_engine/`

Within the `forecast_engine/` directory, this module acts as a crucial monitoring and quality assurance component. It provides insights into:
*   **Forecast Stability:** How much forecasts are changing between runs.
*   **Model Behavior:** Unexpectedly high drift or frequent symbolic flips might indicate issues with underlying models, data inputs, or significant real-world changes.
*   **Interpretability:** The `tag_deltas` provide a granular view of how confidence in specific symbolic tags is shifting, aiding in the interpretation of forecast evolution.

It supports an iterative forecasting process by allowing for systematic comparison and evaluation of forecast outputs.

## 4. Dependencies

### Internal Pulse Modules:
*   [`utils.log_utils.get_logger`](../../utils/log_utils.py)
*   [`core.path_registry.PATHS`](../../core/path_registry.py)

### External Libraries:
*   `json` (Python standard library)
*   `os` (Python standard library)
*   `typing.List`, `typing.Dict`, `typing.Optional` (Python standard library)
*   `river.drift.ADWIN`, `river.drift.KSWIN` (Optional, from the `river` library)

## 5. Adherence to SPARC Principles

*   **Simplicity:** The core logic for comparing cluster confidences and calculating drift is straightforward. Functions are well-defined and focused on specific sub-tasks.
*   **Iterate:** The module is inherently designed for iterative processes, comparing different "runs" of forecasts to monitor changes.
*   **Focus:** It maintains a clear focus on detecting and quantifying drift in forecast cluster summaries.
*   **Quality:**
    *   The module includes a comprehensive docstring detailing its purpose, inputs, outputs, and planned enhancements.
    *   Type hinting is used for function signatures, improving code readability and maintainability.
    *   Logging mechanisms are in place for both results and errors.
    *   The optional dependency on the `river` library is handled gracefully, allowing the core functionality to operate even if `river` is not installed.
    *   Input validation and robust handling of partial/missing clusters are mentioned as enhancements.
*   **Collaboration:** The generated drift scores, symbolic flip warnings, and log files provide actionable information that can be used by other system components or human analysts to assess forecast quality and stability.

## 6. Overall Assessment

*   **Completeness:** The module is substantially complete for its primary task of comparing two sets of forecast clusters and identifying drift based on confidence scores. The addition of `ADWIN` and `KSWIN` provides robust, established algorithms for more general drift detection on numerical series, which can be applied to confidence scores over time.
*   **Clarity:** The code is well-structured with clear function names (e.g., [`normalize_forecast_clusters()`](../../forecast_engine/forecast_drift_monitor.py:46), [`score_drift()`](../../forecast_engine/forecast_drift_monitor.py:58)). The initial docstring is highly informative, setting a clear context for the module's functionality.
*   **Quality:** The code quality is good. It employs standard Python practices, includes error handling for file operations, and manages optional dependencies effectively. The logging to a structured format (JSONL) is a good practice for monitoring tools. The "Status: ✅ Enhanced + Ready" in the docstring suggests it has undergone some level of review and improvement.