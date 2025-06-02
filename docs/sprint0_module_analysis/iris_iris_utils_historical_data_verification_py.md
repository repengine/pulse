# Module Analysis: `iris/iris_utils/historical_data_verification.py`

## 1. Module Intent/Purpose

The primary role of the [`historical_data_verification.py`](iris/iris_utils/historical_data_verification.py) module is to provide comprehensive verification and quality assurance for historical time-series data. It builds upon basic verification capabilities by incorporating more sophisticated data quality assessment methods. These include:

*   Time series continuity analysis (detecting gaps, irregular intervals).
*   Statistical outlier detection (e.g., Z-score, IQR methods).
*   Trend break detection.
*   Cross-correlation between related variables (mentioned in docstring, specific function not prominent).
*   Seasonal pattern verification.
*   Cross-source validation.
*   Calculation of a comprehensive data quality score.

The module aims to identify anomalies, gaps, trend breaks, and assess overall data integrity, providing reports and visualizations to aid in data quality improvement.

## 2. Operational Status/Completeness

The module appears largely operational and complete for its defined core functionalities.
*   It successfully implements several anomaly detection methods (Z-score, IQR, Isolation Forest), gap analysis, trend break detection, and seasonality checks.
*   Dataclasses are well-defined for structuring results (`DataQualityScore`, `Anomaly`, `TimeSeriesGap`, `TrendBreak`, `QualityCheckResult`, `CrossValidationResult`).
*   Functions for loading data, performing checks, generating JSON reports, and creating `matplotlib`-based visualizations are present.

However, there are a few areas indicating incompleteness:
*   The `AnomalyDetectionMethod` enum ([`iris/iris_utils/historical_data_verification.py:103`](iris/iris_utils/historical_data_verification.py:103)) includes `LOCAL_OUTLIER_FACTOR` ([`iris/iris_utils/historical_data_verification.py:108`](iris/iris_utils/historical_data_verification.py:108)) and `DBSCAN` ([`iris/iris_utils/historical_data_verification.py:109`](iris/iris_utils/historical_data_verification.py:109)), but these are explicitly marked as "not yet implemented" in the `detect_anomalies` function, falling back to Z-score ([`iris/iris_utils/historical_data_verification.py:680-682`](iris/iris_utils/historical_data_verification.py:680-682)).
*   The "Data Completeness Calendar Heatmap" visualization is mentioned as a placeholder, with the current implementation using a simpler bar chart ([`iris/iris_utils/historical_data_verification.py:1846-1849`](iris/iris_utils/historical_data_verification.py:1846-1849)).

## 3. Implementation Gaps / Unfinished Next Steps

*   **Missing Anomaly Detection Methods:** As noted above, `LOCAL_OUTLIER_FACTOR` and `DBSCAN` are defined but not implemented ([`iris/iris_utils/historical_data_verification.py:680-682`](iris/iris_utils/historical_data_verification.py:680-682)). Completing these would enhance the module's anomaly detection capabilities.
*   **Advanced Calendar Heatmap:** The placeholder for the calendar heatmap ([`iris/iris_utils/historical_data_verification.py:1846-1849`](iris/iris_utils/historical_data_verification.py:1846-1849)) suggests an intent to use more specialized libraries (e.g., `calmap`) for a more intuitive visualization of data completeness over time.
*   **Configurable Variable Ranges:** The `DEFAULT_VARIABLE_RANGES` constant ([`iris/iris_utils/historical_data_verification.py:92`](iris/iris_utils/historical_data_verification.py:92)) has a comment "to be configured for each variable type," implying a more dynamic or external configuration mechanism might have been planned.
*   **Cross-Variable Correlation:** The module docstring mentions "Cross-correlation between related variables" ([`iris/iris_utils/historical_data_verification.py:12`](iris/iris_utils/historical_data_verification.py:12)) as a feature. While cross-source validation for the *same* variable is implemented ([`cross_validate_sources`](iris/iris_utils/historical_data_verification.py:1228)), a dedicated function for analyzing correlations between *different but related* variables is not apparent. This could be a logical next step.
*   **Refined Seasonality Periods:** The `detect_seasonality` function ([`iris/iris_utils/historical_data_verification.py:814`](iris/iris_utils/historical_data_verification.py:814)) infers some default periods based on data frequency but could benefit from more robust or configurable period detection.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`ingestion.iris_utils.historical_data_retriever`](iris/iris_utils/historical_data_retriever.py):
    *   `load_variable_catalog` ([`iris/iris_utils/historical_data_verification.py:69`](iris/iris_utils/historical_data_verification.py:69))
    *   `get_priority_variables` ([`iris/iris_utils/historical_data_verification.py:70`](iris/iris_utils/historical_data_verification.py:70))
    *   `HISTORICAL_DATA_BASE_DIR` ([`iris/iris_utils/historical_data_verification.py:71`](iris/iris_utils/historical_data_verification.py:71))

### External Library Dependencies:
*   `datetime` (as `dt`)
*   `json`
*   `logging`
*   `os`
*   `warnings`
*   `dataclasses` (`dataclass`, `field`)
*   `enum` (`Enum`)
*   `pathlib` (`Path`)
*   `typing` (various types)
*   `matplotlib.pyplot` (as `plt`) ([`iris/iris_utils/historical_data_verification.py:62`](iris/iris_utils/historical_data_verification.py:62))
*   `numpy` (as `np`) ([`iris/iris_utils/historical_data_verification.py:63`](iris/iris_utils/historical_data_verification.py:63))
*   `pandas` (as `pd`) ([`iris/iris_utils/historical_data_verification.py:64`](iris/iris_utils/historical_data_verification.py:64))
*   `scipy.stats` ([`iris/iris_utils/historical_data_verification.py:65`](iris/iris_utils/historical_data_verification.py:65))
*   `scipy.signal.find_peaks` ([`iris/iris_utils/historical_data_verification.py:66`](iris/iris_utils/historical_data_verification.py:66))
*   `sklearn.ensemble.IsolationForest` (optional, with fallback; [`iris/iris_utils/historical_data_verification.py:643-644`](iris/iris_utils/historical_data_verification.py:643-644))
*   `statsmodels.tsa.stattools.pacf` (optional, with fallback; [`iris/iris_utils/historical_data_verification.py:947-948`](iris/iris_utils/historical_data_verification.py:947-948))

### Interactions via Shared Data:
*   Reads processed data from JSON files (e.g., `*_processed.json`) located within a directory structure defined by `HISTORICAL_DATA_BASE_DIR`. This implies that [`historical_data_retriever.py`](iris/iris_utils/historical_data_retriever.py) or a similar module is responsible for generating these input files.
*   Accesses `variable_catalog.json` through the `load_variable_catalog` function imported from [`historical_data_retriever.py`](iris/iris_utils/historical_data_retriever.py).

### Input/Output Files:
*   **Input:**
    *   Processed historical data files: `{HISTORICAL_DATA_BASE_DIR}/{variable_name}/*_processed.json` (e.g., loaded by [`load_processed_data`](iris/iris_utils/historical_data_verification.py:293)).
    *   Variable catalog: `variable_catalog.json` (accessed via imported functions).
*   **Output:**
    *   JSON quality reports: `{HISTORICAL_DATA_BASE_DIR}/reports/quality_report_{timestamp}.json` (generated by [`generate_quality_report`](iris/iris_utils/historical_data_verification.py:1509)).
    *   Image files for visualizations (e.g., `.png`, `.pdf`): Stored in `{HISTORICAL_DATA_BASE_DIR}/visualizations/{variable_name}/` (generated by [`visualize_data_quality`](iris/iris_utils/historical_data_verification.py:1650)).
    *   Standard logging output via the `logging` module.

## 5. Function and Class Example Usages

The module docstring ([`iris/iris_utils/historical_data_verification.py:17-46`](iris/iris_utils/historical_data_verification.py:17-46)) provides good examples.

*   **[`perform_quality_check(variable_name)`](iris/iris_utils/historical_data_verification.py:1003):**
    ```python
    # from ingestion.iris_utils.historical_data_verification import perform_quality_check
    # quality_report_result = perform_quality_check("spx_close")
    # print(quality_report_result.quality_score.overall_score)
    # for anomaly in quality_report_result.anomalies:
    #     print(anomaly.to_dict())
    ```
    This function is central, returning a `QualityCheckResult` object containing scores, detected anomalies, gaps, etc.

*   **[`detect_anomalies(series, method, threshold)`](iris/iris_utils/historical_data_verification.py:522):**
    ```python
    # from ingestion.iris_utils.historical_data_verification import detect_anomalies, load_processed_data
    # series_data = load_processed_data("spx_close")
    # anomalies_list = detect_anomalies(series_data, method="iqr", threshold=1.5)
    # for anomaly_obj in anomalies_list:
    #     print(f"Anomaly at {anomaly_obj.timestamp}: value {anomaly_obj.value}")
    ```

*   **[`cross_validate_sources(variable_name)`](iris/iris_utils/historical_data_verification.py:1228):**
    ```python
    # from ingestion.iris_utils.historical_data_verification import cross_validate_sources
    # validation_result = cross_validate_sources("unemployment_rate")
    # print(validation_result.correlation_matrix)
    # print(validation_result.recommendation)
    ```

*   **Dataclasses (e.g., `Anomaly`, `TimeSeriesGap`):**
    These are primarily used internally to structure data but their `to_dict()` methods are useful for serialization.
    ```python
    # anomaly_instance = Anomaly(variable_name="test", timestamp=datetime.now(), value=100.0)
    # print(anomaly_instance.to_dict())
    ```

## 6. Hardcoding Issues

*   **`QUALITY_SCORE_WEIGHTS` ([`iris/iris_utils/historical_data_verification.py:82-89`](iris/iris_utils/historical_data_verification.py:82-89)):** Weights for calculating the overall quality score are hardcoded. External configuration would offer more flexibility.
*   **`DEFAULT_VARIABLE_RANGES` ([`iris/iris_utils/historical_data_verification.py:92-100`](iris/iris_utils/historical_data_verification.py:92-100)):** Default min/max values for different variable types (e.g., "percentage", "price") are hardcoded. The accompanying comment "to be configured for each variable type" suggests this was intended to be more dynamic.
*   **Anomaly Detection Parameters:**
    *   Default `threshold` (e.g., `3.0` for Z-score in [`detect_anomalies`](iris/iris_utils/historical_data_verification.py:525)).
    *   `contamination=0.05` for `IsolationForest` ([`iris/iris_utils/historical_data_verification.py:651`](iris/iris_utils/historical_data_verification.py:651)).
    *   `random_state=42` for `IsolationForest` ([`iris/iris_utils/historical_data_verification.py:651`](iris/iris_utils/historical_data_verification.py:651)).
    *   ACF threshold `0.3` for seasonality detection ([`iris/iris_utils/historical_data_verification.py:872`](iris/iris_utils/historical_data_verification.py:872)).
*   **File Paths & Naming Conventions:**
    *   Subdirectory names "reports" and "visualizations" within `HISTORICAL_DATA_BASE_DIR` are hardcoded.
    *   Report filename pattern `quality_report_{timestamp}.json` ([`iris/iris_utils/historical_data_verification.py:1640`](iris/iris_utils/historical_data_verification.py:1640)).
    *   Visualization filename patterns (e.g., `{variable_name}_time_series_quality.{save_format}`).
*   **Default Frequencies/Periods:**
    *   Default frequency `freq = "D"` in [`detect_gaps`](iris/iris_utils/historical_data_verification.py:386) if auto-detection fails.
    *   Default seasonality periods in [`detect_seasonality`](iris/iris_utils/historical_data_verification.py:841-849) if not provided and frequency is inferred.

## 7. Coupling Points

*   **High Coupling with [`historical_data_retriever.py`](iris/iris_utils/historical_data_retriever.py):** This module is tightly coupled with [`ingestion.iris_utils.historical_data_retriever`](iris/iris_utils/historical_data_retriever.py) for obtaining the base data directory path (`HISTORICAL_DATA_BASE_DIR`), loading the variable catalog, and fetching priority variables. Changes in the retriever's API or data structures could significantly impact this verification module.
*   **File System Structure Dependency:** Relies on a specific directory structure and file naming convention (`*_processed.json`) for input data, managed externally (likely by the retriever module).
*   **Internal Orchestration:** The [`perform_quality_check`](iris/iris_utils/historical_data_verification.py:1003) function acts as a central orchestrator, calling numerous other specialized detection and calculation functions within the module, leading to significant internal coupling.
*   **Visualization Library:** The [`visualize_data_quality`](iris/iris_utils/historical_data_verification.py:1650) function is tightly coupled to `matplotlib` for generating plots.

## 8. Existing Tests

*   A test file [`iris/iris_utils/test_historical_data_pipeline.py`](iris/iris_utils/test_historical_data_pipeline.py) exists. It's plausible that this file includes tests covering aspects of the data verification process if verification is integrated into the broader data pipeline. However, without inspecting its contents, the exact coverage for `historical_data_verification.py` is unknown.
*   The module itself contains a `if __name__ == "__main__":` block ([`iris/iris_utils/historical_data_verification.py:1970-1996`](iris/iris_utils/historical_data_verification.py:1970-1996)) with `argparse`. This allows for basic command-line execution of its core functions (quality check, anomaly detection, gap analysis, cross-validation, visualization), suggesting a form of manual or developer-level testing.
*   There is no dedicated test file named `test_historical_data_verification.py` apparent in the `iris/iris_utils/` directory from the provided file listing. This could indicate a gap in focused unit testing for this specific module's components.

## 9. Module Architecture and Flow

1.  **Configuration & Setup:**
    *   Defines constants for quality scoring (`QUALITY_SCORE_WEIGHTS`, `DEFAULT_VARIABLE_RANGES`).
    *   Sets up logging.
    *   Defines Enums (`AnomalyDetectionMethod`, `QualityDimension`) and Dataclasses for structured results.

2.  **Data Loading:**
    *   [`load_processed_data(variable_name)`](iris/iris_utils/historical_data_verification.py:293): Loads a single variable's processed data from a JSON file into a pandas Series.
    *   [`load_multi_source_data(variable_name)`](iris/iris_utils/historical_data_verification.py:347): Loads data for a variable from potentially multiple source files, identified via the variable catalog.

3.  **Core Detection Functions:**
    *   [`detect_gaps(...)`](iris/iris_utils/historical_data_verification.py:384): Identifies time gaps based on expected frequency.
    *   [`detect_anomalies(...)`](iris/iris_utils/historical_data_verification.py:522): Implements various methods (Z-score, IQR, range checks, placeholder for Isolation Forest) to find outliers.
    *   [`detect_trend_breaks(...)`](iris/iris_utils/historical_data_verification.py:730): Uses linear regression on rolling windows to find significant changes in trend.
    *   [`detect_seasonality(...)`](iris/iris_utils/historical_data_verification.py:814): Checks for seasonal patterns using autocorrelation (`calculate_autocorrelation`, `calculate_partial_autocorrelation`).

4.  **Main Analysis Functions (Orchestration):**
    *   [`perform_quality_check(variable_name, ...)`](iris/iris_utils/historical_data_verification.py:1003): Orchestrates the execution of gap, anomaly, trend, and seasonality detection for a single variable. Calculates individual and overall quality scores. Returns a `QualityCheckResult`.
    *   [`cross_validate_sources(variable_name)`](iris/iris_utils/historical_data_verification.py:1228): Compares data from different sources for the same variable, calculating correlations and differences. Returns a `CrossValidationResult`.
    *   [`analyze_gaps(variable_name, ...)`](iris/iris_utils/historical_data_verification.py:1371): Provides a focused report on data gaps.

5.  **Reporting and Visualization:**
    *   [`generate_quality_report(variable_names, ...)`](iris/iris_utils/historical_data_verification.py:1509): Aggregates `QualityCheckResult` for multiple variables, calculates overall statistics, and saves a comprehensive JSON report.
    *   [`visualize_data_quality(variable_name, ...)`](iris/iris_utils/historical_data_verification.py:1650): Generates various plots using `matplotlib` (time series with issues highlighted, quality score radar chart, completeness plot, cross-source comparison) and saves them as image files.

6.  **Command-Line Interface (for testing):**
    *   The `if __name__ == "__main__":` block ([`iris/iris_utils/historical_data_verification.py:1970`](iris/iris_utils/historical_data_verification.py:1970)) provides a simple CLI to test individual functionalities.

## 10. Naming Conventions

*   **Overall Adherence:** The module generally adheres to PEP 8 naming conventions.
    *   Classes (`DataQualityScore`, `AnomalyDetectionMethod`) use PascalCase.
    *   Functions (`perform_quality_check`, `detect_anomalies`) and variables (`variable_name`, `quality_score`) use snake_case.
    *   Constants (`QUALITY_SCORE_WEIGHTS`, `HISTORICAL_DATA_BASE_DIR`) use UPPER_SNAKE_CASE.
    *   Enum members (`ZSCORE`, `IQR`) are in uppercase.
*   **Clarity and Descriptiveness:** Names are generally clear, descriptive, and contextually appropriate (e.g., `detect_gaps`, `anomaly_free`, `trend_stability`).
*   **Consistency:** Naming is consistent throughout the module. For instance, functions that detect issues are prefixed with `detect_`, and result objects follow a `*Result` pattern.
*   **Private/Internal Indicators:** The parameter `_series` in [`perform_quality_check`](iris/iris_utils/historical_data_verification.py:1010) suggests an internal or test-oriented way to pass data directly, though it's not a strictly private member.
*   **AI Assumption Errors:** No obvious naming errors that would suggest misinterpretation by an AI or significant deviations from common Python practices were observed. The names appear to be thoughtfully chosen by a human developer.