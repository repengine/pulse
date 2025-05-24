# Module Analysis: `scripts/data_management/improve_historical_data.py`

## 1. Module Intent/Purpose

The primary role of the `improve_historical_data.py` script is to enhance and prepare historical timeline data, specifically for use in retrodiction training. Its key responsibilities include:

*   Ensuring historical data spans a consistent period (TARGET_YEARS = 5 years).
*   Focusing processing efforts on a predefined list of `PRIORITY_VARIABLES`.
*   Implementing data cleaning strategies, primarily through imputation of missing values.
*   Ensuring temporal alignment of the data.
*   Generating visualizations and updated verification reports for the processed data.
*   Modifying the `historical_ingestion_plugin.py` to align its data retrieval period with the script's target.

## 2. Operational Status/Completeness

The module appears largely operational and complete concerning its defined scope. It includes:

*   Structured logging to a file (`historical_data_improvement.log`) and console.
*   A clear, sequential main execution flow ([`main()`](scripts/data_management/improve_historical_data.py:488)).
*   Error handling (try-except blocks) at various stages.
*   Functions for data loading, cleaning, saving, and visualization.

One identified placeholder for future enhancement is within the [`clean_and_impute_data()`](scripts/data_management/improve_historical_data.py:157) function, which notes: `anomalies_count': 0 # Anomaly detection would go here` ([`scripts/data_management/improve_historical_data.py:221`](scripts/data_management/improve_historical_data.py:221)).

## 3. Implementation Gaps / Unfinished Next Steps

*   **Anomaly Detection:** Anomaly detection is explicitly marked as a future addition within the data cleaning process ([`scripts/data_management/improve_historical_data.py:221`](scripts/data_management/improve_historical_data.py:221)).
*   **Advanced Imputation Methods:** The current imputation uses linear interpolation followed by forward/backward fill ([`scripts/data_management/improve_historical_data.py:189-193`](scripts/data_management/improve_historical_data.py:189-193)). More sophisticated, domain-specific imputation techniques could be beneficial depending on variable characteristics.
*   **Robustness of Plugin Modification:** The [`modify_historical_ingestion_plugin()`](scripts/data_management/improve_historical_data.py:101) function uses direct string replacement to alter the `RETRODICTION_TIMELINE_YEARS` constant in another Python file. This method is fragile and could break if the target file's formatting or structure changes. An AST-based modification or a configuration-driven approach for the plugin would be more robust.
*   **Usage of Variable Catalog:** The [`load_variable_catalog()`](scripts/data_management/improve_historical_data.py:76) function is defined, and [`VARIABLE_CATALOG_PATH`](scripts/data_management/improve_historical_data.py:43) is set, but the catalog itself is not actively used in the main data processing workflow of this script. Its intended integration or purpose within this specific script's logic is unclear.
*   **Data Ingestion Parsing:** The parsing logic in [`execute_data_ingestion()`](scripts/data_management/improve_historical_data.py:322) for data returned by `historical_ingestion_plugin` ([`scripts/data_management/improve_historical_data.py:356-381`](scripts/data_management/improve_historical_data.py:356-381)) handles expected dictionary structures but could be enhanced with more comprehensive schema validation for robustness against unexpected data formats.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   `from iris.iris_plugins_variable_ingestion.historical_ingestion_plugin import historical_ingestion_plugin` ([`scripts/data_management/improve_historical_data.py:329`](scripts/data_management/improve_historical_data.py:329)): This is a critical dependency for sourcing the initial historical data.

### External Library Dependencies:
*   `os`
*   `json`
*   `numpy` (as `np`)
*   `pandas` (as `pd`)
*   `logging`
*   `datetime` (as `dt`, and `datetime`, `date` from `datetime`)
*   `pathlib` (specifically `Path`)
*   `matplotlib.pyplot` (as `plt`)
*   `sys`

### Interaction via Shared Data:
*   **File System:**
    *   Reads from and writes to multiple JSON files and creates PNG visualizations within the `data/historical_timeline/` directory and its subdirectories.
    *   Directly modifies the Python file: [`iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py) ([`scripts/data_management/improve_historical_data.py:103`](scripts/data_management/improve_historical_data.py:103)).
*   **Configuration Files (Implicit):**
    *   Relies on the structure and content of [`data/historical_timeline/variable_catalog.json`](data/historical_timeline/variable_catalog.json) (defined, not actively used) and [`data/historical_timeline/verification_report.json`](data/historical_timeline/verification_report.json) (read and updated).

### Input/Output Files:
*   **Inputs:**
    *   [`data/historical_timeline/variable_catalog.json`](data/historical_timeline/variable_catalog.json) ([`scripts/data_management/improve_historical_data.py:43`](scripts/data_management/improve_historical_data.py:43))
    *   [`data/historical_timeline/verification_report.json`](data/historical_timeline/verification_report.json) ([`scripts/data_management/improve_historical_data.py:44`](scripts/data_management/improve_historical_data.py:44))
    *   Processed data files: `data/historical_timeline/historical_ingestion_plugin/{variable_name}_processed/{variable_name}_processed_*.json` (e.g., via [`get_processed_data_path()`](scripts/data_management/improve_historical_data.py:126))
    *   Source code of [`iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py) for modification.
*   **Outputs:**
    *   Log file: `historical_data_improvement.log` ([`scripts/data_management/improve_historical_data.py:35`](scripts/data_management/improve_historical_data.py:35))
    *   Modified Python file: [`iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py)
    *   Raw data: `data/historical_timeline/historical_ingestion_plugin/{variable_name}_raw/{variable_name}_raw_{timestamp}.json`
    *   Initially processed data: `data/historical_timeline/historical_ingestion_plugin/{variable_name}_processed/{variable_name}_processed_{timestamp}.json`
    *   Transformed (cleaned/imputed) data: `data/historical_timeline/{variable_name}/transformations/{timestamp}_transform_result.json`
    *   Visualizations: `data/historical_timeline/{variable_name}/visualizations/{timestamp}_visualization.png`
    *   Updated report: [`data/historical_timeline/verification_report.json`](data/historical_timeline/verification_report.json)

## 5. Function and Class Example Usages

*   **[`CustomJSONEncoder(json.JSONEncoder)`](scripts/data_management/improve_historical_data.py:22):**
    *   **Purpose:** Handles serialization of `pandas.Timestamp`, `datetime.datetime`, `datetime.date` objects to ISO format strings, and `pd.NA` to `None` for JSON output.
    *   **Usage:** Passed as the `cls` argument to `json.dump()`.
      ```python
      # Example from save_processed_data()
      # json.dump(data, f, indent=2, cls=CustomJSONEncoder)
      ```

*   **[`modify_historical_ingestion_plugin()`](scripts/data_management/improve_historical_data.py:101):**
    *   **Purpose:** Ensures the data ingestion plugin is configured to retrieve 5 years of historical data by modifying its `RETRODICTION_TIMELINE_YEARS` constant.
    *   **Usage:** Called once at the beginning of the [`main()`](scripts/data_management/improve_historical_data.py:488) execution flow.

*   **[`execute_data_ingestion()`](scripts/data_management/improve_historical_data.py:322):**
    *   **Purpose:** Runs the `historical_ingestion_plugin`, processes its output, and saves initial raw and processed data files for each priority variable.
    *   **Usage:** Called in [`main()`](scripts/data_management/improve_historical_data.py:488) after the plugin is potentially modified.

*   **[`clean_and_impute_data(data: dict)`](scripts/data_management/improve_historical_data.py:157):**
    *   **Purpose:** Takes a dictionary of time-series data, converts values to a Pandas DataFrame, imputes missing data using linear interpolation and ffill/bfill, and updates metadata.
    *   **Usage:**
      ```python
      # data_dict = {'values': [{'date': '2023-01-01', 'value': 10}, {'date': '2023-01-02', 'value': None}], ...}
      # cleaned_data_dict = clean_and_impute_data(data_dict)
      ```

*   **[`process_priority_variables()`](scripts/data_management/improve_historical_data.py:439):**
    *   **Purpose:** Orchestrates the loading, cleaning, imputation, saving, and visualization for each variable listed in `PRIORITY_VARIABLES`.
    *   **Usage:** Called in [`main()`](scripts/data_management/improve_historical_data.py:488) after initial data ingestion.

## 6. Hardcoding Issues

*   **File Paths & Directory Structures:**
    *   `HISTORICAL_TIMELINE_DIR = "data/historical_timeline"` ([`scripts/data_management/improve_historical_data.py:42`](scripts/data_management/improve_historical_data.py:42)).
    *   `VARIABLE_CATALOG_PATH` ([`scripts/data_management/improve_historical_data.py:43`](scripts/data_management/improve_historical_data.py:43)), `VERIFICATION_REPORT_PATH` ([`scripts/data_management/improve_historical_data.py:44`](scripts/data_management/improve_historical_data.py:44)).
    *   Path to `historical_ingestion_plugin.py`: `"iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py"` ([`scripts/data_management/improve_historical_data.py:103`](scripts/data_management/improve_historical_data.py:103)).
    *   Output directory patterns for raw, processed, transformed data, and visualizations are constructed using f-strings with hardcoded subdirectories (e.g., `/{variable_name}/transformations/`).
*   **Configuration Values:**
    *   `TARGET_YEARS = 5` ([`scripts/data_management/improve_historical_data.py:45`](scripts/data_management/improve_historical_data.py:45)).
    *   Strings for plugin modification: `"RETRODICTION_TIMELINE_YEARS = 5"` and `"RETRODICTION_TIMELINE_YEARS = 1"` ([`scripts/data_management/improve_historical_data.py:110-115`](scripts/data_management/improve_historical_data.py:110-115)).
*   **`PRIORITY_VARIABLES` List:** The extensive list of variable names ([`scripts/data_management/improve_historical_data.py:48-74`](scripts/data_management/improve_historical_data.py:48-74)) is hardcoded. Externalizing this to a configuration file (e.g., JSON, YAML) would improve maintainability.
*   **Logging:** Log file name `"historical_data_improvement.log"` ([`scripts/data_management/improve_historical_data.py:35`](scripts/data_management/improve_historical_data.py:35)).
*   **Source Identifier:** The string `"historical_ingestion_plugin"` is used as a data source identifier in metadata ([`scripts/data_management/improve_historical_data.py:298`](scripts/data_management/improve_historical_data.py:298), [`scripts/data_management/improve_historical_data.py:389`](scripts/data_management/improve_historical_data.py:389)).

## 7. Coupling Points

*   **[`iris.iris_plugins_variable_ingestion.historical_ingestion_plugin`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py):**
    *   **Very High Coupling:** The script directly modifies the source code of this plugin ([`scripts/data_management/improve_historical_data.py:101-121`](scripts/data_management/improve_historical_data.py:101-121)) and executes it ([`scripts/data_management/improve_historical_data.py:329-333`](scripts/data_management/improve_historical_data.py:329-333)). Changes to the plugin's internal constant name, file structure, or output data format would likely break this script.
*   **File System Structure:**
    *   **High Coupling:** The script relies on a specific, hardcoded directory structure within `data/historical_timeline/` for reading inputs and writing outputs. Any deviation would require code changes.
*   **[`verification_report.json`](data/historical_timeline/verification_report.json):**
    *   **Medium Coupling:** The script reads and writes this JSON file, assuming a particular structure for its content. Changes to the report's schema by other tools could lead to errors.
*   **Data File Format:**
    *   **Medium Coupling:** Assumes a consistent JSON structure for data files it processes (e.g., containing `'values'` as a list of dicts, `'metadata'`, etc.).

## 8. Existing Tests

*   There is no evidence of dedicated unit tests or integration tests for `improve_historical_data.py` within the project structure (e.g., no corresponding `test_improve_historical_data.py` file).
*   The script's successful operation is implicitly tested by its end-to-end execution.
*   The generation and update of [`verification_report.json`](data/historical_timeline/verification_report.json) provide a summary of processing outcomes, which can serve as a manual check or a basis for assertions if integrated into a testing framework.
*   The script includes logging which aids in debugging and verifying behavior during execution.

## 9. Module Architecture and Flow

The script follows a sequential, procedural approach orchestrated by the [`main()`](scripts/data_management/improve_historical_data.py:488) function:

1.  **Initialization:**
    *   Logging is configured.
    *   Global constants for paths, target years, and priority variables are defined.
2.  **Plugin Modification ([`modify_historical_ingestion_plugin()`](scripts/data_management/improve_historical_data.py:101)):**
    *   The `historical_ingestion_plugin.py` file is read, its `RETRODICTION_TIMELINE_YEARS` constant is updated to `5` (if not already), and the file is rewritten.
3.  **Data Ingestion ([`execute_data_ingestion()`](scripts/data_management/improve_historical_data.py:322)):**
    *   The (now modified) `historical_ingestion_plugin` is imported and executed.
    *   The returned data (expected to be `historical_data_by_date`) is parsed.
    *   For each variable in `PRIORITY_VARIABLES`:
        *   Necessary output directories are created if they don't exist.
        *   Data for the current variable is extracted.
        *   Raw data is saved to `{variable_name}_raw_{timestamp}.json`.
        *   Initially processed data (with basic metadata) is saved to `{variable_name}_processed_{timestamp}.json`.
4.  **Priority Variable Processing ([`process_priority_variables()`](scripts/data_management/improve_historical_data.py:439)):**
    *   Iterates through each `variable_name` in `PRIORITY_VARIABLES`.
    *   For each variable:
        *   Retrieves the path to its latest processed data file ([`get_processed_data_path()`](scripts/data_management/improve_historical_data.py:126)).
        *   Loads the data ([`load_processed_data()`](scripts/data_management/improve_historical_data.py:148)).
        *   Cleans and imputes missing values ([`clean_and_impute_data()`](scripts/data_management/improve_historical_data.py:157)). This involves converting to a Pandas DataFrame, interpolating, and ffill/bfill.
        *   Saves the transformed data ([`save_processed_data()`](scripts/data_management/improve_historical_data.py:229)).
        *   Generates and saves a plot of the data ([`visualize_data()`](scripts/data_management/improve_historical_data.py:249)).
        *   Results (paths, stats) are collected.
5.  **Report Update ([`update_verification_report()`](scripts/data_management/improve_historical_data.py:283)):**
    *   The existing `verification_report.json` is loaded.
    *   It's updated with the processing results and overall metrics derived from the `PRIORITY_VARIABLES` processing step.
    *   The updated report is saved.
6.  **Logging:** Throughout the process, informational messages, warnings, and errors are logged.

Helper functions are used for tasks like JSON encoding ([`CustomJSONEncoder`](scripts/data_management/improve_historical_data.py:22)), loading data, and managing file paths.

## 10. Naming Conventions

*   **Functions and Variables:** Adhere well to PEP 8, using `snake_case` (e.g., [`load_variable_catalog()`](scripts/data_management/improve_historical_data.py:76), [`priority_variables`](scripts/data_management/improve_historical_data.py:48)). Names are generally descriptive and clear.
*   **Constants:** Use `UPPER_SNAKE_CASE` as per PEP 8 (e.g., [`HISTORICAL_TIMELINE_DIR`](scripts/data_management/improve_historical_data.py:42), [`TARGET_YEARS`](scripts/data_management/improve_historical_data.py:45)).
*   **Classes:** Use `CapWords` (e.g., [`CustomJSONEncoder`](scripts/data_management/improve_historical_data.py:22)).
*   **File Naming:** The script itself (`improve_historical_data.py`) uses snake_case. Output files incorporate variable names, timestamps, and processing stage indicators (e.g., `spx_close_raw_20230101_120000.json`, `gdp_growth_annual_processed_20230101_120000.json`).
*   **Consistency:** Naming is consistent throughout the module.
