# Module Analysis: iris/iris_utils/historical_data_retriever.py

## Module Intent/Purpose

This module is responsible for retrieving historical time-series data for variables defined in a variable catalog. It handles fetching data from external sources (currently FRED and Yahoo Finance), applying basic transformations, verifying data quality, and persisting the data and associated metadata. It also provides a command-line interface for triggering data retrieval.

## Operational Status/Completeness

The module appears functional for its implemented data sources (FRED, Yahoo Finance). It includes core logic for data fetching, error handling (retries, backoff), basic analysis, and persistence. There are no explicit `TODO` comments or placeholders indicating unfinished core functionality within the existing data source implementations.

## Implementation Gaps / Unfinished Next Steps

*   **Limited Data Source Support:** The module currently only supports FRED and Yahoo Finance. Extending support to other data sources defined in the variable catalog would be a logical next step.
*   **Analysis Refinement:** The data analysis functions (`analyze_data`) use simple heuristics (e.g., fixed gap size, 5 days) and anomaly detection (3 standard deviations) that may need refinement or parameterization based on the characteristics of different time series data.
*   **Error Handling Granularity:** While retries are implemented, more specific error handling based on API responses might be beneficial.
*   **Variable Catalog Loading:** The `load_variable_catalog` function assumes the catalog exists and raises a `FileNotFoundError`. More robust error handling or creation of a default catalog might be considered.

## Connections & Dependencies

*   **Internal Modules:**
    *   [`ingestion.iris_utils.ingestion_persistence`](iris/iris_utils/ingestion_persistence.py) - Used for saving retrieved data, raw API responses, and request metadata.
*   **External Libraries:**
    *   `argparse` - For command-line interface parsing.
    *   `datetime` - For date and time manipulation.
    *   `json` - For handling JSON data (variable catalog, saving reports).
    *   `logging` - For logging information, warnings, and errors.
    *   `os` - For accessing environment variables (`FRED_API_KEY`).
    *   `random` - Used in retry backoff for jitter.
    *   `time` - Used for rate limiting and retry delays.
    *   `dataclasses` - Used for the `RetrievalStats` data class.
    *   `pathlib` - For path manipulation.
    *   `typing` - For type hints.
    *   `pandas` - Heavily used for data manipulation and analysis (Series, DataFrame, DatetimeIndex).
    *   `requests` - Used indirectly by `fredapi` and potentially other future API calls.
    *   `yfinance` - Used for fetching Yahoo Finance data.
    *   `fredapi` - Used for fetching FRED data.
*   **Data Interactions:**
    *   Reads from [`data/historical_timeline/variable_catalog.json`](data/historical_timeline/variable_catalog.json).
    *   Writes processed data to `data/historical_timeline/historical_data/<variable_name>/processed_data.json`.
    *   Writes raw API responses to `data/historical_timeline/historical_data/<variable_name>/raw_api_response.json`.
    *   Writes request metadata to `data/historical_timeline/historical_data/<variable_name>/request_metadata.json`.
    *   Writes a verification report to [`data/historical_timeline/verification_report.json`](data/historical_timeline/verification_report.json).
    *   Interacts with external FRED and Yahoo Finance APIs over the network.

## Function and Class Example Usages

*   [`retrieve_historical_data(variable_info, years, end_date, rate_limit_delay)`](iris/iris_utils/historical_data_retriever.py:208)
    *   Retrieves data for a single variable based on its information from the catalog.
    *   Example (from docstring):
    ```python
    from ingestion.iris_utils.historical_data_retriever import retrieve_historical_data
    import datetime as dt

    variable_info = {
        "variable_name": "spx_close",
        "source": "historical_ingestion_plugin",
        "api_endpoint": "^GSPC",
        "required_parameters": {"source": "YahooFinance"}
    }
    data = retrieve_historical_data(variable_info, years=5, end_date=dt.datetime.now())
    ```
*   [`retrieve_priority_variables(priority, years, end_date, rate_limit_delay)`](iris/iris_utils/historical_data_retriever.py:534)
    *   Retrieves data for all variables in the catalog with a specified priority level.
    *   Example (from docstring):
    ```python
    from ingestion.iris_utils.historical_data_retriever import retrieve_priority_variables

    priority_data = retrieve_priority_variables(priority=1)
    ```
*   [`create_verification_report(results)`](iris/iris_utils/historical_data_retriever.py:577)
    *   Generates a report summarizing the retrieval statistics for multiple variables.
    *   Example:
    ```python
    from ingestion.iris_utils.historical_data_retriever import create_verification_report

    # Assuming 'retrieval_results' is a dictionary of results from retrieve_historical_data calls
    verification_report = create_verification_report(retrieval_results)
    ```
*   [`RetrievalStats`](iris/iris_utils/historical_data_retriever.py:85)
    *   A dataclass used to hold statistical information about the retrieved data for a single variable.

## Hardcoding Issues

*   Default values for years (`DEFAULT_YEARS`), retry attempts (`DEFAULT_RETRY_ATTEMPTS`), base delay (`DEFAULT_RETRY_BASE_DELAY`), and rate limit delay (`DEFAULT_RATE_LIMIT_DELAY`) are hardcoded constants.
*   Paths to the variable catalog (`VARIABLE_CATALOG_PATH`) and historical data base directory (`HISTORICAL_DATA_BASE_DIR`) are hardcoded.
*   The FRED API key relies on an environment variable (`FRED_API_KEY`) but has a hardcoded empty string default if the variable is not set, which will cause FRED data retrieval to fail if the key is not configured.
*   Thresholds for gap detection (5 days) and anomaly detection (3 standard deviations) are hardcoded within the `analyze_data` function.

## Coupling Points

*   Tight coupling with the expected structure and content of the `variable_catalog.json` file.
*   Direct dependencies on `yfinance` and `fredapi` libraries and their specific API interfaces and data formats.
*   Dependency on the `ingestion_persistence` module's functions (`ensure_data_directory`, `save_api_response`, `save_processed_data`, `save_request_metadata`) and the data formats it expects.
*   Reliance on the `FRED_API_KEY` environment variable being set for FRED data retrieval.

## Existing Tests

Based on the file structure, there is a test file located at [`tests/iris/iris_utils/test_historical_data_pipeline.py`](tests/iris/iris_utils/test_historical_data_pipeline.py). This suggests that the data retrieval and processing pipeline has some test coverage, although the extent and nature of these tests are not known without examining the test file's content. There is no dedicated test file specifically for `historical_data_retriever.py`.

## Module Architecture and Flow

The module follows a procedural and function-oriented architecture. The main flow, typically initiated via the command-line interface (`main` function), involves:
1.  Loading the variable catalog using `load_variable_catalog`.
2.  Identifying variables to retrieve based on command-line arguments (single variable, priority level, or all).
3.  For each selected variable:
    *   Calculating the date range using `get_date_range`.
    *   Fetching data from the specified source (FRED or Yahoo Finance) using `fetch_fred_data` or `fetch_yahoo_finance_data`, which incorporate the `retry_with_backoff` decorator for resilience.
    *   Applying any specified transformations.
    *   Analyzing the retrieved data for statistics, gaps, and anomalies using `analyze_data`.
    *   Saving the raw response, request metadata, and processed data using functions from the `ingestion_persistence` module.
    *   Pausing briefly using `time.sleep` to respect rate limits.
4.  After processing all selected variables, generating a verification report using `create_verification_report` and saving it using `save_verification_report`.
The command-line interface (`main` function) parses arguments and orchestrates this flow, handling potential errors during the process.

## Naming Conventions

Naming conventions generally adhere to Python standards (PEP 8). Functions and variables use `snake_case`, while the `RetrievalStats` class uses `PascalCase`. Constants are in `UPPER_SNAKE_CASE`. The use of `_FRED` for a module-level variable is a common convention for indicating internal use. Overall, naming is consistent and readable within the module.
