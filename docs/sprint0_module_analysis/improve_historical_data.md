# Module Analysis: `improve_historical_data.py`

## 1. Module Intent/Purpose

The primary purpose of the [`improve_historical_data.py`](../../improve_historical_data.py:1) module is to enhance historical timeline data, specifically for use in retrodiction training. It achieves this by:

1.  Modifying the `historical_ingestion_plugin.py` to extend the data retrieval period for historical data to 5 years.
2.  Focusing data processing efforts on a predefined list of `PRIORITY_VARIABLES` (e.g., financial and economic indicators).
3.  Implementing data cleaning strategies, primarily handling missing (`NaN`) values through linear interpolation and forward/backward fill.
4.  Executing the data ingestion process using the modified plugin.
5.  Saving raw, processed, and transformed data, along with visualizations for each priority variable.
6.  Updating a `verification_report.json` with statistics about the processed data.
7.  Logging the entire process for monitoring and debugging.

## 2. Operational Status/Completeness

-   **Operational:** The module appears to be operational and provides an end-to-end workflow for its defined tasks.
-   **Completeness:**
    -   It successfully orchestrates data ingestion, cleaning, saving, and reporting.
    -   Basic data imputation (linear interpolation, ffill/bfill) is implemented in [`clean_and_impute_data()`](../../improve_historical_data.py:157).
    -   Visualization of data series is included via [`visualize_data()`](../../improve_historical_data.py:249).
    -   Logging is established for tracking script execution.
    -   A [`CustomJSONEncoder`](../../improve_historical_data.py:22) is implemented to handle serialization of `datetime` and `pandas.Timestamp` objects.

## 3. Implementation Gaps / Unfinished Next Steps

-   **Anomaly Detection:** The [`clean_and_impute_data()`](../../improve_historical_data.py:157) function includes a placeholder comment: `'anomalies_count': 0 # Anomaly detection would go here` (line 221). This functionality is not implemented.
-   **Advanced Imputation:** Current imputation methods are basic. More sophisticated techniques (e.g., seasonal decomposition, machine learning-based imputation) could be beneficial depending on data characteristics.
-   **Robust Plugin Modification:** The [`modify_historical_ingestion_plugin()`](../../improve_historical_data.py:101) function uses direct string replacement to alter another Python file. This is highly fragile and prone to breaking if the target file's structure or specific string changes. An AST-based modification or more robust regex approach would be preferable.
-   **Configuration Management:** Many paths and parameters (e.g., `HISTORICAL_TIMELINE_DIR`, `PRIORITY_VARIABLES`, imputation methods) are hardcoded. Externalizing these to a configuration file would improve flexibility.
-   **Error Handling in Data Parsing:** While [`execute_data_ingestion()`](../../improve_historical_data.py:322) logs warnings for unexpected signal formats (line 381), it could benefit from more robust error handling or reporting for missing/malformed priority variable data.
-   **Unit Testing:** The module lacks dedicated unit tests.

## 4. Connections & Dependencies

### Internal Project Dependencies:

-   **`iris.iris_plugins_variable_ingestion.historical_ingestion_plugin`**:
    -   Dynamically imported and executed by [`execute_data_ingestion()`](../../improve_historical_data.py:329).
    -   Source code is directly modified by [`modify_historical_ingestion_plugin()`](../../improve_historical_data.py:101) (target path: [`iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py`](../../iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:1)).

### External Library Dependencies:

-   `os`
-   `json`
-   `numpy`
-   `pandas`
-   `logging`
-   `datetime` (as `dt`, `datetime`, `date`)
-   `pathlib`
-   `matplotlib.pyplot`
-   `sys`
-   `typing` (Dict, List, Any, Optional, Tuple)

### Shared Data & I/O Files:

-   **Input Files:**
    -   [`data/historical_timeline/variable_catalog.json`](../../data/historical_timeline/variable_catalog.json) (loaded by [`load_variable_catalog()`](../../improve_historical_data.py:76), though not used in the main flow).
    -   [`data/historical_timeline/verification_report.json`](../../data/historical_timeline/verification_report.json) (loaded by [`load_verification_report()`](../../improve_historical_data.py:81)).
    -   Processed data files: `data/historical_timeline/historical_ingestion_plugin/{variable_name}_processed/{variable_name}_processed_*.json` (loaded via [`get_processed_data_path()`](../../improve_historical_data.py:126) and [`load_processed_data()`](../../improve_historical_data.py:148)).
-   **Output/Modified Files:**
    -   [`iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py`](../../iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:1) (modified).
    -   [`historical_data_improvement.log`](../../historical_data_improvement.log:1) (log output).
    -   Transformation results: `data/historical_timeline/{variable_name}/transformations/{timestamp}_transform_result.json` (saved by [`save_processed_data()`](../../improve_historical_data.py:229)).
    -   Visualizations: `data/historical_timeline/{variable_name}/visualizations/{timestamp}_visualization.png` (saved by [`visualize_data()`](../../improve_historical_data.py:249)).
    -   [`data/historical_timeline/verification_report.json`](../../data/historical_timeline/verification_report.json) (updated by [`update_verification_report()`](../../improve_historical_data.py:283)).
    -   Raw data: `data/historical_timeline/historical_ingestion_plugin/{variable_name}_raw/{variable_name}_raw_{timestamp}.json` (saved by [`execute_data_ingestion()`](../../improve_historical_data.py:322)).
    -   Initial processed data: `data/historical_timeline/historical_ingestion_plugin/{variable_name}_processed/{variable_name}_processed_{timestamp}.json` (saved by [`execute_data_ingestion()`](../../improve_historical_data.py:322)).
-   **Directory Creation:** The script creates various subdirectories within `data/historical_timeline/` if they do not exist.

## 5. Function and Class Example Usages

-   **`CustomJSONEncoder` Class ([`improve_historical_data.py:22`](../../improve_historical_data.py:22))**
    ```python
    # Used internally by json.dump to handle datetime and pandas Timestamp objects
    # json.dump(my_data, file_handle, cls=CustomJSONEncoder)
    ```
-   **`clean_and_impute_data(data: dict)` ([`improve_historical_data.py:157`](../../improve_historical_data.py:157))**
    ```python
    # sample_data = {
    #     'variable_name': 'example_var',
    #     'values': [
    #         {'date': '2023-01-01T00:00:00', 'value': 100},
    #         {'date': '2023-01-02T00:00:00', 'value': None}, # Missing value
    #         {'date': '2023-01-03T00:00:00', 'value': 102}
    #     ],
    #     'metadata': {}
    # }
    # cleaned_data = clean_and_impute_data(sample_data)
    # # cleaned_data will have the None value imputed
    ```
-   **`execute_data_ingestion()` ([`improve_historical_data.py:322`](../../improve_historical_data.py:322))**
    ```python
    # This function is called internally by main()
    # It runs the historical_ingestion_plugin and saves initial raw/processed files.
    # success = execute_data_ingestion()
    # if success:
    #     logger.info("Data ingestion successful.")
    ```
-   **`process_priority_variables()` ([`improve_historical_data.py:439`](../../improve_historical_data.py:439))**
    ```python
    # This function is called internally by main()
    # It iterates PRIORITY_VARIABLES, loads, cleans, saves, and visualizes data.
    # results = process_priority_variables()
    # for var, res_data in results.items():
    #     if res_data.get("success"):
    #         logger.info(f"Processed {var}, stats: {res_data.get('stats')}")
    ```

## 6. Hardcoding Issues

The module contains several hardcoded values and paths, which can affect maintainability and flexibility:

-   **Directory Paths:**
    -   `HISTORICAL_TIMELINE_DIR = "data/historical_timeline"` ([`improve_historical_data.py:42`](../../improve_historical_data.py:42))
    -   Paths for `variable_catalog.json` and `verification_report.json` are derived from this ([`improve_historical_data.py:43-44`](../../improve_historical_data.py:43-44)).
    -   Output directories for raw, processed, transformed data, and visualizations are constructed using this base path (e.g., [`improve_historical_data.py:128`](../../improve_historical_data.py:128), [`improve_historical_data.py:232`](../../improve_historical_data.py:232), [`improve_historical_data.py:269`](../../improve_historical_data.py:269)).
-   **Configuration Constants:**
    -   `TARGET_YEARS = 5` ([`improve_historical_data.py:45`](../../improve_historical_data.py:45))
    -   `PRIORITY_VARIABLES` list ([`improve_historical_data.py:48-74`](../../improve_historical_data.py:48-74))
-   **Plugin Modification:**
    -   Path to `historical_ingestion_plugin.py`: `"iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py"` ([`improve_historical_data.py:103`](../../improve_historical_data.py:103)).
    -   Specific strings to search/replace within the plugin: `"RETRODICTION_TIMELINE_YEARS = 5"` and `"RETRODICTION_TIMELINE_YEARS = 1"` ([`improve_historical_data.py:110-115`](../../improve_historical_data.py:110-115)).
-   **Data Processing Parameters:**
    -   Imputation method (`method='linear'`) in [`clean_and_impute_data()`](../../improve_historical_data.py:189).
-   **Logging Configuration:**
    -   Log file name: `"historical_data_improvement.log"` ([`improve_historical_data.py:35`](../../improve_historical_data.py:35)).

## 7. Coupling Points

-   **Very High Coupling with `historical_ingestion_plugin.py`:**
    -   The script directly modifies the source code of this plugin using string replacement, creating a fragile dependency.
    -   It relies on the successful execution and specific output format of this plugin.
-   **High Coupling with File System Structure:** The script assumes a specific directory layout under `data/historical_timeline/`. Changes to this structure would likely break the script.
-   **Data Format Coupling:** Assumes specific JSON structures for input files (e.g., `verification_report.json`) and the data returned by the ingestion plugin.
-   **`PRIORITY_VARIABLES` List:** The main processing loop in [`process_priority_variables()`](../../improve_historical_data.py:439) is tightly coupled to this hardcoded list.

## 8. Existing Tests

-   There are no unit tests (e.g., using `unittest` or `pytest`) present within the [`improve_historical_data.py`](../../improve_historical_data.py:1) module itself.
-   The script does not import or invoke any external test suites.
-   Verification of functionality seems to rely on manual checks of output files, visualizations, and the `verification_report.json`.

## 9. Module Architecture and Flow

The module follows a sequential, procedural flow orchestrated by the [`main()`](../../improve_historical_data.py:488) function:

1.  **Initialization:**
    -   Sets up logging ([`improve_historical_data.py:31`](../../improve_historical_data.py:31)).
    -   Defines global constants (paths, `TARGET_YEARS`, `PRIORITY_VARIABLES`).
2.  **Modify Ingestion Plugin ([`modify_historical_ingestion_plugin()`](../../improve_historical_data.py:101)):**
    -   Reads the content of `historical_ingestion_plugin.py`.
    -   Replaces the `RETRODICTION_TIMELINE_YEARS` parameter to `TARGET_YEARS` (5 years).
    -   Writes the modified content back to the plugin file.
3.  **Execute Data Ingestion ([`execute_data_ingestion()`](../../improve_historical_data.py:322)):**
    -   Adds the project root to `sys.path`.
    -   Dynamically imports `historical_ingestion_plugin` from `iris.iris_plugins_variable_ingestion`.
    -   Runs the plugin.
    -   Creates necessary output directories for each priority variable (raw, processed, transformations, visualizations).
    -   Parses the plugin's output, extracts data for each priority variable.
    -   Saves the initial raw data and a basic processed version (with start/end dates and completeness) as JSON files.
4.  **Process Priority Variables ([`process_priority_variables()`](../../improve_historical_data.py:439)):**
    -   Iterates through each `variable_name` in `PRIORITY_VARIABLES`.
    -   For each variable:
        -   [`get_processed_data_path()`](../../improve_historical_data.py:126): Finds the most recent processed JSON file.
        -   [`load_processed_data()`](../../improve_historical_data.py:148): Loads the data from this file.
        -   [`clean_and_impute_data()`](../../improve_historical_data.py:157): Converts data to a Pandas DataFrame, performs linear interpolation for `NaN` values, then ffill/bfill. Updates metadata with statistics (min, max, mean, completeness, etc.).
        -   [`save_processed_data()`](../../improve_historical_data.py:229): Saves the cleaned and imputed data to a new JSON file in the `transformations` directory.
        -   [`visualize_data()`](../../improve_historical_data.py:249): Generates a line plot of the data and saves it as a PNG image in the `visualizations` directory.
    -   Collects results (success status, paths, stats) for each variable.
5.  **Update Verification Report ([`update_verification_report()`](../../improve_historical_data.py:283)):**
    -   Loads the existing `verification_report.json` (or creates a new one if not found).
    -   Updates the report with overall processing statistics and detailed metrics for each successfully processed variable.
    -   Saves the updated report back to JSON, using `CustomJSONEncoder`.
6.  **Logging Summary:** The [`main()`](../../improve_historical_data.py:488) function logs a final summary of how many variables were successfully processed.

Helper functions are provided for tasks like loading JSON, path manipulation, and the core data processing steps.

## 10. Naming Conventions

-   **Constants:** `UPPER_CASE_WITH_UNDERSCORES` (e.g., `HISTORICAL_TIMELINE_DIR`, `PRIORITY_VARIABLES`). This is consistent and follows Python best practices (PEP 8).
-   **Functions:** `lower_case_with_underscores` (e.g., [`load_variable_catalog()`](../../improve_historical_data.py:76), [`clean_and_impute_data()`](../../improve_historical_data.py:157)). Consistent and PEP 8 compliant.
-   **Class:** `PascalCase` (e.g., [`CustomJSONEncoder`](../../improve_historical_data.py:22)). Consistent and PEP 8 compliant.
-   **Variables:** Generally `lower_case_with_underscores` (e.g., `variable_name`, `cleaned_data`).
-   **File Naming:** Output files include timestamps and descriptive names (e.g., `{timestamp}_transform_result.json`).
-   The use of f-strings for path construction is modern and readable.
-   Log messages are generally informative.

Overall, naming conventions are clear, consistent, and adhere to standard Python style guides.

## 11. SPARC Compliance Summary

-   **Simplicity:** The script's core logic is procedural and relatively easy to follow. However, the direct modification of another script's source code ([`modify_historical_ingestion_plugin()`](../../improve_historical_data.py:101)) introduces significant complexity and fragility, deviating from simplicity.
-   **Iterate:** The module iterates on existing data by cleaning, imputing, and extending its temporal range.
-   **Focus:** The script is well-focused on its task of improving historical data for a specific set of variables.
-   **Quality:**
    -   **Logging:** Implemented throughout the script.
    -   **Error Handling:** Basic `try-except` blocks are used in most functions.
    -   **Data Cleaning:** Basic imputation is performed.
    -   **Testing:** Lacks automated unit tests, which is a significant quality gap.
    -   **Hardcoding:** Extensive hardcoding of paths, filenames, and configurations (like `PRIORITY_VARIABLES` and plugin modification details) reduces robustness and maintainability.
    -   **Fragile Dependencies:** The method of modifying `historical_ingestion_plugin.py` is a major concern for code quality and reliability.
-   **Documentation:**
    -   A module-level docstring explains the script's purpose.
    -   Most functions have docstrings.
    -   Inline comments are used where appropriate.
-   **Environment Variables:** The script does not appear to use environment variables for configuration; paths and parameters are hardcoded directly.
-   **File Size:** The script is 517 lines, which is manageable.

**Key SPARC Non-Compliance:**
-   The direct, fragile modification of another Python script is a major deviation from promoting maintainable and robust solutions.
-   Lack of automated tests.
-   Over-reliance on hardcoded configurations and paths.