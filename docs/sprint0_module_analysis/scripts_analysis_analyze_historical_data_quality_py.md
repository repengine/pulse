# Module Analysis: `scripts/analysis/analyze_historical_data_quality.py`

## 1. Module Intent/Purpose

The primary role of the [`scripts/analysis/analyze_historical_data_quality.py`](../../../scripts/analysis/analyze_historical_data_quality.py) module is to assess the quality of historical timeline data intended for retrodiction training. Its key responsibilities, as outlined in its docstring ([`scripts/analysis/analyze_historical_data_quality.py:1-8`](../../../scripts/analysis/analyze_historical_data_quality.py:1-8)), include:

*   Evaluating data completeness for a predefined list of priority variables.
*   Verifying the historical depth of the data, aiming for at least 3-5 years.
*   Checking for missing values within the datasets.
*   Analyzing the temporal alignment of data across different variables.
*   Generating a comprehensive HTML summary report, complete with visualizations, to present these findings.

## 2. Operational Status/Completeness

The module appears to be largely complete and functional for its defined scope. It successfully performs data loading, analysis of individual variables, temporal alignment checks, visualization generation, and HTML report creation. The main execution flow is handled by the [`main()`](../../../scripts/analysis/analyze_historical_data_quality.py:435) function. Error handling is implemented using `try-except` blocks, and logging ([`scripts/analysis/analyze_historical_data_quality.py:21-28`](../../../scripts/analysis/analyze_historical_data_quality.py:21-28)) is established to track the process and any issues. No explicit "TODO" comments or obvious placeholders for core functionality were observed.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Imputation Effectiveness Analysis:** The module's docstring mentions "imputation effectiveness" as an analysis point. However, the current implementation primarily identifies missing values ([`analyze_variable_data()`](../../../scripts/analysis/analyze_historical_data_quality.py:109-169)) rather than evaluating the quality or impact of any prior imputation methods. This could be a potential area for future enhancement.
*   **Actionability of Recommendations:** The recommendations generated in the HTML report ([`generate_report()`](../../../scripts/analysis/analyze_historical_data_quality.py:298-433)) are somewhat generic (e.g., "Increase historical depth," "Improve data completeness"). Future iterations could provide more specific, actionable advice, possibly suggesting data sources or repair techniques for identified issues.
*   **Dynamic Variable Selection:** The analysis operates on a hardcoded list of `PRIORITY_VARIABLES` ([`scripts/analysis/analyze_historical_data_quality.py:40-66`](../../../scripts/analysis/analyze_historical_data_quality.py:40-66)). While a comment suggests this list is consistent with [`improve_historical_data.py`](../../../scripts/data_management/improve_historical_data.py), a more robust solution might involve dynamic loading of this list from a shared configuration file or another module.
*   **Reporting System Integration:** The module outputs a standalone HTML report. For ongoing data quality monitoring, integrating these reports into a persistent dashboard or a system that tracks quality metrics over time would be a logical next step.
*   **Unused Metadata Loading:** The functions [`load_variable_catalog()`](../../../scripts/analysis/analyze_historical_data_quality.py:68) and [`load_verification_report()`](../../../scripts/analysis/analyze_historical_data_quality.py:73) are defined to load `variable_catalog.json` and `verification_report.json` respectively. However, these loaded data are not explicitly used within the main analysis workflow orchestrated by the [`main()`](../../../scripts/analysis/analyze_historical_data_quality.py:435) function. Their inclusion might be for future extensions or manual debugging purposes.

## 4. Connections & Dependencies

### 4.1. Direct Imports from Other Project Modules
No direct imports from other custom project modules within the `Pulse` codebase are apparent in this script. It functions as a standalone analysis tool.

### 4.2. External Library Dependencies
The module relies on the following standard Python libraries and third-party packages:
*   `os`
*   `json`
*   `numpy`
*   `pandas`
*   `logging`
*   `datetime`
*   `pathlib`
*   `matplotlib.pyplot`
*   `typing` (specifically `Dict`, `List`, `Any`, `Optional`)

### 4.3. Interaction via Shared Data
The module interacts with other parts of the system (presumably data preparation and transformation pipelines) through the file system:
*   It reads a variable catalog from [`data/historical_timeline/variable_catalog.json`](../../../data/historical_timeline/variable_catalog.json) (via [`VARIABLE_CATALOG_PATH`](../../../scripts/analysis/analyze_historical_data_quality.py:33)).
*   It reads a verification report from [`data/historical_timeline/verification_report.json`](../../../data/historical_timeline/verification_report.json) (via [`VERIFICATION_REPORT_PATH`](../../../scripts/analysis/analyze_historical_data_quality.py:34)).
*   Crucially, it reads processed time-series data for each variable from JSON files located at `data/historical_timeline/<variable_name>/transformations/*_transform_result.json`. The logic for finding the latest such file is in [`get_latest_transformation()`](../../../scripts/analysis/analyze_historical_data_quality.py:78-98).

### 4.4. Input/Output Files
*   **Input Files:**
    *   [`data/historical_timeline/variable_catalog.json`](../../../data/historical_timeline/variable_catalog.json)
    *   [`data/historical_timeline/verification_report.json`](../../../data/historical_timeline/verification_report.json)
    *   `data/historical_timeline/<variable_name>/transformations/*_transform_result.json` (multiple files, one per variable, latest is chosen)
*   **Output Files:**
    *   `historical_data_analysis.log`: Log file for tracking script execution and errors.
    *   [`data/historical_timeline/reports/historical_depth.png`](../../../data/historical_timeline/reports/historical_depth.png): PNG image visualizing historical depth per variable.
    *   [`data/historical_timeline/reports/data_completeness.png`](../../../data/historical_timeline/reports/data_completeness.png): PNG image visualizing data completeness per variable.
    *   [`data/historical_timeline/reports/summary_metrics.png`](../../../data/historical_timeline/reports/summary_metrics.png): PNG image displaying summary metrics as a table.
    *   `data/historical_timeline/reports/historical_data_quality_report_<timestamp>.html`: The main HTML report summarizing the analysis.

## 5. Function and Class Example Usages

The module is script-based and does not define classes. Key functions include:

*   **`main()`**:
    ```python
    # This function is the main entry point when the script is executed.
    # It orchestrates the entire analysis process.
    if __name__ == "__main__":
        main()
    ```
*   **`analyze_variable_data(variable_name: str) -> Dict[str, Any]`**:
    Analyzes data for a single specified variable.
    ```python
    # results_for_gdp = analyze_variable_data("gdp_growth_annual")
    # print(results_for_gdp["historical_years"])
    ```
*   **`get_latest_transformation(variable_name: str) -> Optional[str]`**:
    Retrieves the file path of the most recent transformation data for a variable.
    ```python
    # transform_file = get_latest_transformation("spx_close")
    # if transform_file:
    #     data = load_transformation_data(transform_file)
    ```
*   **`generate_report(...) -> str`**:
    Generates the final HTML report.
    ```python
    # report_path = generate_report(variable_analysis_results, temporal_alignment_summary, viz_paths)
    # if report_path:
    #     print(f"Report generated at: {report_path}")
    ```

## 6. Hardcoding Issues

Several hardcoded values and paths are present:

*   **File Paths & Directory Structure:**
    *   [`HISTORICAL_TIMELINE_DIR = "data/historical_timeline"`](../../../scripts/analysis/analyze_historical_data_quality.py:32)
    *   [`VARIABLE_CATALOG_PATH`](../../../scripts/analysis/analyze_historical_data_quality.py:33) derived from `HISTORICAL_TIMELINE_DIR`.
    *   [`VERIFICATION_REPORT_PATH`](../../../scripts/analysis/analyze_historical_data_quality.py:34) derived from `HISTORICAL_TIMELINE_DIR`.
    *   [`OUTPUT_DIR`](../../../scripts/analysis/analyze_historical_data_quality.py:35) derived from `HISTORICAL_TIMELINE_DIR`.
    *   Log file name: `"historical_data_analysis.log"` ([`scripts/analysis/analyze_historical_data_quality.py:25`](../../../scripts/analysis/analyze_historical_data_quality.py:25)).
    *   The structure `f"{HISTORICAL_TIMELINE_DIR}/{variable_name}/transformations"` ([`scripts/analysis/analyze_historical_data_quality.py:80`](../../../scripts/analysis/analyze_historical_data_quality.py:80)) and file pattern `f"*_transform_result.json"` ([`scripts/analysis/analyze_historical_data_quality.py:88`](../../../scripts/analysis/analyze_historical_data_quality.py:88)) are hardcoded.
*   **Numerical Constants (Magic Numbers):**
    *   [`MIN_YEARS = 3`](../../../scripts/analysis/analyze_historical_data_quality.py:36) (minimum historical depth target).
    *   [`TARGET_YEARS = 5`](../../../scripts/analysis/analyze_historical_data_quality.py:37) (ideal historical depth target).
    *   `365.25`: Used to convert days to years ([`scripts/analysis/analyze_historical_data_quality.py:147`](../../../scripts/analysis/analyze_historical_data_quality.py:147)).
    *   `95`, `99`: Completeness percentage thresholds used in visualizations and report generation ([`scripts/analysis/analyze_historical_data_quality.py:242-245`](../../../scripts/analysis/analyze_historical_data_quality.py:242-245), [`scripts/analysis/analyze_historical_data_quality.py:375`](../../../scripts/analysis/analyze_historical_data_quality.py:375), [`scripts/analysis/analyze_historical_data_quality.py:404`](../../../scripts/analysis/analyze_historical_data_quality.py:404)).
    *   `80`, `50`: Percentage thresholds for coloring report metrics ([`scripts/analysis/analyze_historical_data_quality.py:339-340`](../../../scripts/analysis/analyze_historical_data_quality.py:339-340)).
*   **Strings:**
    *   [`PRIORITY_VARIABLES`](../../../scripts/analysis/analyze_historical_data_quality.py:40-66): A hardcoded list of financial and economic indicators.
    *   Expected keys in JSON data (e.g., `'values'`, `'date'`, `'value'`) are implicitly hardcoded by their usage.
    *   The entire HTML structure and CSS styling for the report are hardcoded within the [`generate_report()`](../../../scripts/analysis/analyze_historical_data_quality.py:298-433) function.

## 7. Coupling Points

*   **File System Dependency:** The module is tightly coupled to the specific directory structure rooted at `data/historical_timeline/`. Any changes to this structure (e.g., locations of variable data, transformation results, catalog files) would likely break the script.
*   **Data Format Dependency:** It expects specific JSON structures for the `variable_catalog.json`, `verification_report.json`, and particularly the `*_transform_result.json` files (e.g., a list of dictionaries with 'date' and 'value' keys).
*   **`PRIORITY_VARIABLES` List:** The script's core analysis loop is driven by this hardcoded list. If the set of relevant variables changes, this list requires manual updates.
*   **Upstream Data Processing:** The quality of the analysis is entirely dependent on the correctness and availability of the `*_transform_result.json` files, which are assumed to be generated by an upstream process.

## 8. Existing Tests

Based on a file system check of `tests/scripts/analysis/`, no dedicated test files (e.g., `test_analyze_historical_data_quality.py`) exist for this module. This indicates a lack of unit or integration tests, which is a significant gap for ensuring reliability and maintainability.

## 9. Module Architecture and Flow

The script follows a sequential, procedural flow:

1.  **Setup:** Initializes logging and defines global constants (paths, analysis thresholds, and the list of `PRIORITY_VARIABLES`).
2.  **Main Execution (`main()` function):**
    a.  Iterates through each `variable_name` in `PRIORITY_VARIABLES`.
    b.  For each variable, it calls [`analyze_variable_data()`](../../../scripts/analysis/analyze_historical_data_quality.py:109). This function:
        i.  Locates the latest transformation data file using [`get_latest_transformation()`](../../../scripts/analysis/analyze_historical_data_quality.py:78).
        ii. Loads the JSON data using [`load_transformation_data()`](../../../scripts/analysis/analyze_historical_data_quality.py:100).
        iii. Converts the data into a Pandas DataFrame for analysis.
        iv. Calculates metrics: historical depth in years, number of data points, completeness percentage, count of missing values, date range, and basic statistics (min, max, mean).
    c.  Aggregates results from all variables and passes them to [`analyze_temporal_alignment()`](../../../scripts/analysis/analyze_historical_data_quality.py:171) to compute overall statistics (min/max/avg years, percentage of variables meeting targets).
    d.  Generates visualizations (bar charts for historical depth and completeness, summary table image) using [`generate_visualizations()`](../../../scripts/analysis/analyze_historical_data_quality.py:193) with Matplotlib.
    e.  Compiles all information (summary statistics, visualizations, detailed variable metrics, and recommendations) into an HTML report using [`generate_report()`](../../../scripts/analysis/analyze_historical_data_quality.py:298).
3.  **Helper Functions:**
    *   [`load_variable_catalog()`](../../../scripts/analysis/analyze_historical_data_quality.py:68) and [`load_verification_report()`](../../../scripts/analysis/analyze_historical_data_quality.py:73): Load metadata JSON files. As noted, their direct use in the main flow isn't apparent.

## 10. Naming Conventions

*   **Functions:** Adhere to PEP 8, using `snake_case` (e.g., [`analyze_variable_data`](../../../scripts/analysis/analyze_historical_data_quality.py:109), [`generate_visualizations`](../../../scripts/analysis/analyze_historical_data_quality.py:193)).
*   **Variables:** Primarily use `snake_case` (e.g., `variable_name`, `historical_years`, `alignment_results`).
*   **Constants:** Use `UPPER_SNAKE_CASE` (e.g., [`HISTORICAL_TIMELINE_DIR`](../../../scripts/analysis/analyze_historical_data_quality.py:32), [`MIN_YEARS`](../../../scripts/analysis/analyze_historical_data_quality.py:36), [`PRIORITY_VARIABLES`](../../../scripts/analysis/analyze_historical_data_quality.py:40)).
*   **Clarity:** Names are generally descriptive and clearly convey their purpose.
*   No significant deviations from Python community standards (PEP 8) were observed. The comment regarding `PRIORITY_VARIABLES` ([`scripts/analysis/analyze_historical_data_quality.py:39`](../../../scripts/analysis/analyze_historical_data_quality.py:39)) suggests an effort towards consistency with other parts of the project.
