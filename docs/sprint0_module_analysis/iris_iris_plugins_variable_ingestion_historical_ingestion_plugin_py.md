# Module Analysis: `iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py`

## 1. Module Intent/Purpose

The primary role of the [`historical_ingestion_plugin.py`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:1) module is to serve as a data ingestion plugin for the Pulse IRIS system. Its responsibilities include:

*   Fetching actual historical time-series data for a predefined set of economic, financial, and market variables from external sources, specifically FRED (Federal Reserve Economic Data) and Yahoo Finance.
*   Generating synthetic historical data for other variables registered in the Pulse system but not covered by the available external data sources.
*   Returning this data as a time-ordered list of signal collections. Each collection (an inner list) contains all signals (both real and synthetic) for a specific date, covering a retrodiction period defined by `RETRODICTION_TIMELINE_YEARS` (currently 5 years).

## 2. Operational Status/Completeness

The module appears largely complete and operational for its defined scope.
*   It successfully implements data fetching from FRED and Yahoo Finance.
*   It includes a mechanism for generating basic synthetic data.
*   The main plugin function, [`historical_ingestion_plugin()`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:286), correctly orchestrates data acquisition and formatting.
*   There are no explicit "TODO" comments or obvious major placeholders within the core logic that would prevent its current operation.
*   The `if __name__ == "__main__":` block (lines [432-445](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:432)) provides a functional example of its usage and output structure.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Snapshot Creation:** The module notes (lines [443-445](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:443)) that creating `WorldState` snapshots from its output is a subsequent step, likely to be handled by adapting [`simulation_engine/utils/worldstate_io.py`](simulation_engine/utils/worldstate_io.py) or a new script. This is an external integration point rather than an internal incompleteness.
*   **Advanced Synthetic Data:** The synthetic data generation ([`generate_synthetic_historical_data()`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:266)) is currently a simple random walk. Future enhancements could involve more sophisticated or configurable models for generating synthetic data to better reflect realistic variable behavior.
*   **Configuration for Data Sources:** The `EXTERNAL_DATA_MAP` (lines [42-229](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:42)) is hardcoded. A more flexible system for defining and adding new data sources or variables (e.g., via configuration files) could be beneficial.
*   **Robustness in API Interaction:** While basic error handling for API calls exists (e.g., in [`fetch_historical_fred_series()`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:231)), features like automated retries or more granular error classification could improve resilience.
*   **Rate Limiting:** A fixed `time.sleep(0.5)` (line [349](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:349)) is used for FRED API calls. A more dynamic or configurable rate-limiting strategy might be necessary for larger data pulls or stricter API limits.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`core.variable_registry`](core/variable_registry.py): Uses `registry` to access metadata about variables (e.g., default values, ranges for synthetic data generation).

### External Library Dependencies:
*   `datetime` (as `dt`): For date and time manipulations.
*   `logging`: For logging information and errors.
*   `os`: Used for accessing environment variables (e.g., `FRED_API_KEY`).
*   `typing`: For type hinting (`List`, `Dict`, `Any`, `Optional`, `Callable`).
*   `time`: Used for implementing delays in API calls ([`time.sleep()`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:16)).
*   `requests`: Used by `fredapi` for HTTP requests; explicitly caught in error handling.
*   `yfinance` (as `yf`): For fetching data from Yahoo Finance.
*   `fredapi`: Specifically, the `Fred` class for interacting with the FRED API.
*   `pandas` (as `pd`): For data manipulation, especially time-series data (`DatetimeIndex`, `Series.reindex`, `ffill`).
*   `numpy` (as `np`): Used for generating random numbers in synthetic data generation.

### Interaction with Other Modules via Shared Data:
*   Relies on the structure and content provided by [`core.variable_registry`](core/variable_registry.py).
*   The output format (a list of lists of signal dictionaries) is designed for consumption by other parts of the Pulse system, likely for initializing simulations or analyses.

### Input/Output Files:
*   **Input:**
    *   Reads the `FRED_API_KEY` from an environment variable ([`os.getenv("FRED_API_KEY", "")`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:38)).
*   **Output:**
    *   The primary output is the Python list structure returned by the [`historical_ingestion_plugin()`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:286) function.
    *   Logs information and errors using the `logging` module.
    *   The `if __name__ == "__main__":` block prints example output to standard output.

## 5. Function and Class Example Usages

*   **`historical_ingestion_plugin() -> List[List[Dict[str, Any]]]`** (line [286](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:286)):
    *   This is the main entry point of the plugin. It orchestrates the fetching of real and generation of synthetic data.
    *   Usage example from the module's `if __name__ == "__main__":` block:
        ```python
        historical_data_by_date = historical_ingestion_plugin()
        print(f"Plugin returned data for {len(historical_data_by_date)} dates.")
        if historical_data_by_date:
            print("Signals for the first date:")
            for signal in historical_data_by_date[0]:
                # Example signal: {'name': 'us_10y_yield', 'value': 0.015, ...}
                print(f"  {signal['name']}: {signal['value']} ({signal['timestamp']})")
        ```

*   **`fetch_historical_fred_series(series_id: str, start_date: dt.datetime, end_date: dt.datetime) -> pd.Series | None`** (line [231](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:231)):
    *   Fetches a specific time series from FRED.
    *   Example (conceptual, as it's called internally):
        ```python
        # Conceptual usage
        # fred_key = os.getenv("FRED_API_KEY")
        # if fred_key:
        #     start = dt.datetime(2020, 1, 1)
        #     end = dt.datetime(2020, 1, 31)
        #     dgs10_series = fetch_historical_fred_series("DGS10", start, end)
        #     if dgs10_series is not None:
        #         print(dgs10_series.head())
        ```

*   **`fetch_historical_yfinance_close(ticker: str, start_date: dt.datetime, end_date: dt.datetime) -> pd.Series | None`** (line [254](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:254)):
    *   Fetches historical closing prices for a given ticker from Yahoo Finance.
    *   Example (conceptual):
        ```python
        # Conceptual usage
        # start = dt.datetime(2020, 1, 1)
        # end = dt.datetime(2020, 1, 31)
        # aapl_series = fetch_historical_yfinance_close("AAPL", start, end)
        # if aapl_series is not None:
        #     print(aapl_series.head())
        ```

*   **`generate_synthetic_historical_data(variable_name: str, timeline_dates: list[dt.datetime]) -> dict[dt.datetime, float]`** (line [266](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:266)):
    *   Generates synthetic data for a variable using a random walk, bounded by optional range in variable registry.
    *   Example (conceptual):
        ```python
        # Conceptual usage
        # from core.variable_registry import registry
        # registry.register("synthetic_var", default=10, range=(5,15))
        # dates = pd.date_range(start="2023-01-01", periods=5, freq='D').to_pydatetime().tolist()
        # synthetic_data = generate_synthetic_historical_data("synthetic_var", dates)
        # print(synthetic_data)
        ```

## 6. Hardcoding Issues

*   **`RETRODICTION_TIMELINE_YEARS = 5`** (line [33](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:33)): The look-back period for historical data is fixed.
*   **`HISTORY_SNAPSHOT_PREFIX = "turn_history_"`** (line [35](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:35)): A prefix for snapshot files, though not used for saving within this plugin itself.
*   **`EXTERNAL_DATA_MAP: Dict[str, Dict[str, Any]]`** (lines [42-229](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:42)): This large dictionary defines the mapping of Pulse variables to external data sources (FRED IDs, Yahoo Finance tickers) and includes data transformation lambdas. This is a significant block of hardcoded configuration.
*   **API Call Delay:** `time.sleep(0.5)` (line [349](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:349)) for FRED API rate limiting is a fixed value.
*   **Synthetic Data Parameters:**
    *   The noise characteristics in [`generate_synthetic_historical_data()`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:266) are hardcoded (e.g., `np.random.normal(0, 0.01)` on line [276](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:276)).
    *   A default value of `0.5` is used if variable metadata or a default is missing (line [270](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:270)).
*   **Source String:** The "source" field in the output signals is hardcoded to `"historical_ingestion_plugin"` (line [422](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:422)).

## 7. Coupling Points

*   **`core.variable_registry`**: Tightly coupled for obtaining variable metadata (default values, ranges) which influences synthetic data generation and identifying variables.
*   **External APIs (FRED & Yahoo Finance)**: Directly dependent on the `fredapi` and `yfinance` libraries and the stability of their respective APIs. Changes in these external services could break functionality.
*   **`EXTERNAL_DATA_MAP`**: The structure and content of this map create a strong coupling. Any changes to Pulse variable names or the identifiers/structure of data from FRED/Yahoo Finance necessitate direct code modification here.
*   **Environment Variables**: Relies on the `FRED_API_KEY` environment variable being set for FRED data fetching.
*   **Output Data Structure**: The specific structure of the returned list of lists of signal dictionaries is an implicit contract with downstream consumers.

## 8. Existing Tests

*   No dedicated automated test file (e.g., `tests/iris/iris_plugins_variable_ingestion/test_historical_ingestion_plugin.py`) is apparent in the provided project structure.
*   The module contains an `if __name__ == "__main__":` block (lines [432-445](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:432)) which serves as a basic execution script and prints sample output. This is useful for manual testing or demonstration but does not constitute automated unit or integration tests.
*   **Conclusion:** There is a lack of automated tests for this module.

## 9. Module Architecture and Flow

The plugin operates as follows:

1.  **Configuration & Initialization**:
    *   Sets `RETRODICTION_TIMELINE_YEARS` to 5.
    *   Initializes the FRED API client (`_FRED`) if `FRED_API_KEY` is available in environment variables.
    *   Defines `EXTERNAL_DATA_MAP` linking internal variable names to external data sources and transformation functions.

2.  **Timeline Definition** (within [`historical_ingestion_plugin()`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:286)):
    *   Calculates `start_date` (5 years ago from now) and `end_date` (now).
    *   Generates `timeline_dates_index`, a pandas `DatetimeIndex` with daily frequency, localized to UTC.

3.  **Fetch Real Historical Data**:
    *   Iterates through `EXTERNAL_DATA_MAP`:
        *   **FRED Data**: If `source` is "FRED":
            *   Calls [`fetch_historical_fred_series()`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:231) with the series ID, start, and end dates.
            *   Fetched data index is localized to UTC.
            *   The series is `reindex`ed against `timeline_dates_index` using forward fill (`ffill`) to align data points.
            *   The specified `transform` lambda function is applied.
            *   Resulting data (datetime -> value) is stored in `historical_data`.
            *   A `time.sleep(0.5)` is introduced to mitigate FRED API rate limiting.
        *   **Yahoo Finance Data**: If `source` is "YahooFinance":
            *   Calls [`fetch_historical_yfinance_close()`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:254) with the ticker, start, and end dates.
            *   Fetched data index is made UTC-aware.
            *   The series is `reindex`ed against `timeline_dates_index` using `ffill`.
            *   The specified `transform` lambda is applied.
            *   Resulting data is stored in `historical_data`.

4.  **Generate Synthetic Historical Data**:
    *   Retrieves all registered variable names from [`core.variable_registry`](core/variable_registry.py).
    *   Identifies variables that are not in `EXTERNAL_DATA_MAP`.
    *   For each such variable, calls [`generate_synthetic_historical_data()`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:266) with the variable name and the list of timeline dates (converted to naive datetimes).
        *   This function uses the variable's default value (from registry, or 0.5) as a starting point.
        *   It generates a random walk, optionally clamping values within the `range` specified in the variable's registry metadata.
        *   Synthetic data is stored in `historical_data`.

5.  **Structure Output Data**:
    *   Initializes `historical_signals_timeline` as an empty list.
    *   Iterates through each `current_date` in `timeline_dates_index`:
        *   Initializes `signals_for_date` as an empty list.
        *   Iterates through `all_variables` from the registry:
            *   Retrieves the value for `var_name` at `current_date` from `historical_data`.
            *   Constructs a `signal` dictionary containing: `name`, `value`, `source` ("historical_ingestion_plugin"), `timestamp` (ISO format of `current_date`), and `meta` (description).
            *   Appends the `signal` to `signals_for_date`.
        *   Appends `signals_for_date` to `historical_signals_timeline`.

6.  **Return Value**:
    *   Logs the number of dates for which signals were generated.
    *   Returns `historical_signals_timeline`.

## 10. Naming Conventions

*   **Functions**: Adhere to PEP 8 (snake_case), e.g., [`historical_ingestion_plugin`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:286), [`fetch_historical_fred_series`](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:231). Names are generally descriptive.
*   **Variables**: Mostly use snake_case (e.g., `start_date`, `series_data`, `aligned_data`).
*   **Constants**: Use uppercase snake_case (e.g., `RETRODICTION_TIMELINE_YEARS`, `EXTERNAL_DATA_MAP`, `FRED_KEY`).
*   **"Private" Globals**: `_FRED` (line [39](iris/iris_plugins_variable_ingestion/historical_ingestion_plugin.py:39)) is used for the FRED API client instance, conventionally indicating it's intended for internal module use.
*   **Clarity & Consistency**: Naming is generally clear and consistent within the module.
*   **Potential AI Assumption Errors/Deviations**:
    *   The variable names used as keys in `EXTERNAL_DATA_MAP` (e.g., `"us_10y_yield"`, `"cpi_yoy"`, `"spx_close"`) are specific to the Pulse system's internal nomenclature. These are not errors but reflect project-specific naming standards.
    *   No significant deviations from common Python naming conventions (PEP 8) were observed.