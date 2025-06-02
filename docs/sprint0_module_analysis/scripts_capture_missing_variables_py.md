# Module Analysis: `scripts/capture_missing_variables.py`
## 1. Module Intent/Purpose

The primary role of this module is to fetch, process, and store historical data for a predefined set of economic variables: `real_gdp`, `inflation`, and `nonfarm_payroll`. It utilizes the Alpha Vantage API as the data source. The script aims to retrieve at least 5 years of historical data, apply data cleaning techniques (including type conversion and sorting), and perform imputation (linear interpolation, forward/backward fill) for any missing values. The processed data is then saved in a structured format for potential downstream use within the Pulse system.

## 2. Operational Status/Completeness

The module appears to be largely complete for its defined scope. Key functionalities include:
*   Checking for the necessary Alpha Vantage API key from environment variables.
*   Initializing and using the `AlphaVantagePlugin` for API interaction.
*   Iterating through the target variables to fetch data.
*   Processing the raw data into a pandas DataFrame, handling date conversions, and numeric conversions.
*   Applying imputation strategies (linear interpolation, ffill, bfill).
*   Persisting data at various stages: raw API response, fully processed data, and individual data points incrementally.
*   Basic error handling for API key issues, plugin enablement, data retrieval failures, and general processing exceptions.

There are no obvious `TODO` comments or incomplete critical sections.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Configuration for Variables &amp; API Endpoints:**
    *   The `TARGET_VARIABLES` list ([`scripts/capture_missing_variables.py:41`](scripts/capture_missing_variables.py:41)) is hardcoded.
    *   The mapping of these variables to specific Alpha Vantage API `function` names is hardcoded within an `if/elif` structure in [`fetch_and_store_variable()`](scripts/capture_missing_variables.py:107-112). This makes adding new variables cumbersome. A configuration file or a dictionary mapping would improve extensibility.
*   **Interval Parameterization:** The data fetching interval is hardcoded within the `params` dictionary in [`fetch_and_store_variable()`](scripts/capture_missing_variables.py:126) (`"quarterly"` for `REAL_GDP`, `"monthly"` for others), overriding the function's `interval` parameter.
*   **Data Validation:** Beyond checking for the presence of a `"data"` key in the API response, there's no deeper validation of the data's structure, type, or content integrity.
*   **Advanced Imputation:** The script uses basic linear interpolation and ffill/bfill. For more robust data quality, more sophisticated imputation techniques could be considered.
*   **`YEARS_OF_DATA` Constant:** The constant `YEARS_OF_DATA = 5` ([`scripts/capture_missing_variables.py:40`](scripts/capture_missing_variables.py:40)) is defined but not actively used to limit the historical data fetched; Alpha Vantage typically provides all available data for the specified economic indicators.
*   **No explicit follow-up actions** are defined within this module, though its output is clearly intended for other system components.
## 4. Connections &amp; Dependencies

*   **Direct Project Module Imports:**
    *   `from ingestion.iris_plugins_variable_ingestion.alpha_vantage_plugin import AlphaVantagePlugin` ([`scripts/capture_missing_variables.py:22`](scripts/capture_missing_variables.py:22))
    *   `from ingestion.iris_utils.ingestion_persistence import ensure_data_directory, save_to_file, save_request_metadata, save_api_response, save_processed_data, save_data_point_incremental` ([`scripts/capture_missing_variables.py:23`](scripts/capture_missing_variables.py:23))
*   **External Library Dependencies:**
    *   `os`
    *   `sys`
    *   `datetime` (via pandas)
    *   `json` (implicitly by persistence functions)
    *   `logging`
    *   `pandas`
    *   `numpy` (via pandas)
    *   `pathlib` (implicitly by persistence functions)
*   **Interaction via Shared Data:**
    *   Writes data to the `data/historical_timeline/` directory, which is expected to be consumed by other parts of the Pulse system.
    *   Relies on `AlphaVantagePlugin` to interact with the external Alpha Vantage API.
*   **Input/Output Files:**
    *   **Input:** Reads the `ALPHA_VANTAGE_KEY` environment variable.
    *   **Output (per variable):**
        *   Log messages (console/file).
        *   Directory: `data/historical_timeline/{variable_name}/`
        *   Files within the directory:
            *   `request_metadata.json`
            *   `api_response_raw.json`
            *   `processed_data.json`
            *   Individual data points: `data_points/{date_str}.json`

## 5. Function and Class Example Usages

*   **`process_variable_data(variable_name, data)`** ([`scripts/capture_missing_variables.py:44`](scripts/capture_missing_variables.py:44)):
    *   **Description:** Takes a variable name (e.g., `"inflation"`) and the raw JSON data dictionary fetched from Alpha Vantage. It converts this data into a pandas DataFrame, processes it (date conversion, sorting, numeric conversion), and applies imputation for missing values.
    *   **Usage:**
        ```python
        # Conceptual example, as data is fetched internally by another function
        # raw_api_data = {"data": [{"date": "2023-01-01", "value": "2.5"}, {"date": "2023-02-01", "value": "2.6"}]}
        # processed_df = process_variable_data("inflation", raw_api_data)
        # if processed_df is not None:
        #     print(processed_df.head())
        ```
*   **`fetch_and_store_variable(plugin, variable_name, interval="quarterly")`** ([`scripts/capture_missing_variables.py:92`](scripts/capture_missing_variables.py:92)):
    *   **Description:** Orchestrates fetching data for a single variable using the provided `AlphaVantagePlugin` instance. It handles API parameter setup, calls the plugin, processes the response using [`process_variable_data()`](scripts/capture_missing_variables.py:44), and saves the raw, processed, and incremental data to the file system.
    *   **Usage:**
        ```python
        # Conceptual example
        # from ingestion.iris_plugins_variable_ingestion.alpha_vantage_plugin import AlphaVantagePlugin
        # av_plugin = AlphaVantagePlugin() # Assuming API key is set and plugin enables
        # if av_plugin.enabled:
        #     success = fetch_and_store_variable(av_plugin, "nonfarm_payroll")
        #     print(f"Fetching nonfarm_payroll: {'Success' if success else 'Failed'}")
        ```
*   **`main()`** ([`scripts/capture_missing_variables.py:203`](scripts/capture_missing_variables.py:203)):
    *   **Description:** The main entry point of the script. It checks for the Alpha Vantage API key, initializes the plugin, iterates through the `TARGET_VARIABLES`, calls [`fetch_and_store_variable()`](scripts/capture_missing_variables.py:92) for each, and logs a summary of the outcomes.
    *   **Usage:** Executed when the script is run directly: `python scripts/capture_missing_variables.py`

## 6. Hardcoding Issues

*   **`YEARS_OF_DATA = 5`** ([`scripts/capture_missing_variables.py:40`](scripts/capture_missing_variables.py:40)): Defined but not used to limit data fetched.
*   **`TARGET_VARIABLES = ["real_gdp", "inflation", "nonfarm_payroll"]`** ([`scripts/capture_missing_variables.py:41`](scripts/capture_missing_variables.py:41)): List of variables to process is fixed.
*   **API Function Mapping:** The mapping from internal variable names to Alpha Vantage API `function` parameters (e.g., `"REAL_GDP"`) is hardcoded in [`fetch_and_store_variable()`](scripts/capture_missing_variables.py:107-112).
*   **Data Storage Paths:**
    *   Base directory for data output is hardcoded as `"data"` and `"data/historical_timeline"` in calls to persistence utilities (e.g., [`scripts/capture_missing_variables.py:118`](scripts/capture_missing_variables.py:118), [`scripts/capture_missing_variables.py:134`](scripts/capture_missing_variables.py:134)).
    *   The `dataset_id` prefix is hardcoded as `"economic_"` ([`scripts/capture_missing_variables.py:121`](scripts/capture_missing_variables.py:121)).
*   **API Request Intervals:** Data intervals (`"quarterly"` or `"monthly"`) are hardcoded within the `params` dictionary for API calls ([`scripts/capture_missing_variables.py:126`](scripts/capture_missing_variables.py:126)).
*   **`source_name="alpha_vantage"`:** This string is hardcoded in multiple calls to data persistence functions (e.g., [`scripts/capture_missing_variables.py:133`](scripts/capture_missing_variables.py:133)).
## 7. Coupling Points

*   **`AlphaVantagePlugin`:** Tightly coupled to this specific plugin from `ingestion.iris_plugins_variable_ingestion` for all data fetching operations.
*   **`ingestion.iris_utils.ingestion_persistence`:** Tightly coupled to the `save_*` and `ensure_data_directory` functions from this utility module for all file system operations.
*   **Alpha Vantage API Response Structure:** The script expects a specific JSON structure from the Alpha Vantage API, notably a `"data"` key containing a list of date/value objects.
*   **Environment Variable `ALPHA_VANTAGE_KEY`:** The script's operation is dependent on this environment variable being correctly set.
*   **File System Data Structure:** The script creates and relies on a specific directory structure under `data/historical_timeline/`. Downstream consumers of this data will also depend on this structure.

## 8. Existing Tests

*   No dedicated test file (e.g., `tests/scripts/test_capture_missing_variables.py`) is apparent in the project structure provided.
*   The script itself does not contain self-tests or assertions beyond basic error logging.
*   Consequently, test coverage for this module is likely minimal or non-existent.

## 9. Module Architecture and Flow

1.  **Setup:**
    *   Imports necessary libraries and project modules.
    *   Configures basic logging.
    *   Defines global constants (e.g., `TARGET_VARIABLES`).
    *   Modifies `sys.path` to allow imports from the project root.
2.  **Main Execution (`main()` function):**
    *   Retrieves `ALPHA_VANTAGE_KEY` from environment variables; exits if not found.
    *   Initializes an `AlphaVantagePlugin` instance; exits if the plugin is not enabled.
    *   Iterates through each `variable` in the `TARGET_VARIABLES` list:
        *   Calls [`fetch_and_store_variable(plugin, variable)`](scripts/capture_missing_variables.py:92).
        *   Stores the success/failure status.
    *   Logs a summary of the processing results for each variable.
3.  **Data Fetching and Storing (`fetch_and_store_variable()` function):**
    *   Determines the Alpha Vantage API `function` string based on `variable_name`.
    *   Ensures the target data directory exists (e.g., `data/historical_timeline/real_gdp/`).
    *   Constructs a `dataset_id` (e.g., `"economic_real_gdp"`).
    *   Prepares API request parameters, including the hardcoded interval.
    *   Saves request metadata to a file.
    *   Uses the `plugin._safe_get()` method to fetch data from Alpha Vantage.
    *   If data retrieval fails or returns no data, logs an error and returns `False`.
    *   Saves the raw API response to a file.
    *   Calls [`process_variable_data(variable_name, data)`](scripts/capture_missing_variables.py:44) to clean and impute the data.
    *   If processing fails, returns `False`.
    *   Iterates through the processed DataFrame:
        *   Saves each data point incrementally to a separate file.
        *   Collects data points into a list for the final processed data structure.
    *   Saves the aggregated processed data (containing all points for the variable) to a file.
    *   Logs success and returns `True`.
    *   Includes a `try-except` block to catch and log any errors during the process.
4.  **Data Processing (`process_variable_data()` function):**
    *   Checks if the `"data"` key exists in the input.
    *   Converts the list of data points into a pandas DataFrame.
    *   Converts the `'date'` column to datetime objects and sets it as the DataFrame index.
    *   Sorts the DataFrame by date.
    *   Converts the `'value'` column to numeric, coercing errors.
    *   Applies linear interpolation to fill `NaN` values.
    *   Applies forward fill (`ffill`) then backward fill (`bfill`) for any remaining `NaN` values.
    *   Logs the number of processed data points and returns the DataFrame.

**Control Flow:** The script executes sequentially, driven by the `main` function. It processes each target variable one after the other.
**Data Flow:** `ALPHA_VANTAGE_KEY` (env) -> `AlphaVantagePlugin` -> Alpha Vantage API (external) -> Raw JSON Response -> Pandas DataFrame (in-memory processing) -> Multiple JSON files (persistent storage under `data/historical_timeline/`).

## 10. Naming Conventions

*   **Modules:** `capture_missing_variables.py` (snake_case).
*   **Functions:** `process_variable_data`, `fetch_and_store_variable`, `main` (snake_case, PEP 8 compliant).
*   **Variables:** `variable_name`, `api_key`, `processed_df` (snake_case, PEP 8 compliant).
*   **Constants:** `YEARS_OF_DATA`, `TARGET_VARIABLES` (UPPER_SNAKE_CASE, PEP 8 compliant).
*   **Classes:** `AlphaVantagePlugin` (imported, PascalCase, PEP 8 compliant).
*   **Logging Instance:** `logger` (standard practice).

The naming conventions are generally consistent and adhere to PEP 8 guidelines. There are no apparent AI assumption errors in naming; names are descriptive and relevant to their functionality. The import path `ingestion.iris_plugins_variable_ingestion.alpha_vantage_plugin` ([`scripts/capture_missing_variables.py:22`](scripts/capture_missing_variables.py:22)) is used consistently, assuming it's a valid path within the `iris` module structure.