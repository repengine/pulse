# Module Analysis: `iris/high_frequency_ingestion.py`

## 1. Module Intent/Purpose

The primary role of the [`iris/high_frequency_ingestion.py`](iris/high_frequency_ingestion.py:1) module is to handle the ingestion of high-frequency stock data specifically from the Alpha Vantage API. It is responsible for:
*   Interacting with the `AlphaVantagePlugin`.
*   Managing data entitlements (e.g., 'delayed' vs. 'realtime').
*   Implementing rate limiting to adhere to API usage policies.
*   Fetching, processing, and storing the retrieved stock data using `HighFrequencyDataStore`.

## 2. Operational Status/Completeness

The module appears to be largely functional for its defined scope of fetching intraday stock data from Alpha Vantage.
*   It includes a mechanism for rate limiting ([`_wait_for_rate_limit()`](iris/high_frequency_ingestion.py:31)).
*   It processes and stores data points for open, high, low, close, and volume.
*   The example usage block (`if __name__ == "__main__":`) is present but commented out, requiring an API key for activation ([`iris/high_frequency_ingestion.py:113-141`](iris/high_frequency_ingestion.py:113)).
*   A comment, "# Optionally save error details" ([`iris/high_frequency_ingestion.py:107`](iris/high_frequency_ingestion.py:107)), suggests that error logging could be more robust.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Error Handling:** The error handling during data processing ([`iris/high_frequency_ingestion.py:105-107`](iris/high_frequency_ingestion.py:105)) is basic, with a placeholder comment for saving error details. A more structured error logging and retry mechanism could be beneficial.
*   **Configuration:**
    *   The `outputsize` parameter for the API call is hardcoded to `"compact"` ([`iris/high_frequency_ingestion.py:64`](iris/high_frequency_ingestion.py:64)). This could be made configurable.
    *   While `entitlement` and `rate_limit_per_minute` are configurable during class instantiation, the stock symbols are fetched from `self.alpha_vantage_plugin.STOCK_SYMBOLS` ([`iris/high_frequency_ingestion.py:55`](iris/high_frequency_ingestion.py:55)), making the list of symbols dependent on the plugin's configuration.
*   **Unused Import:** The function [`save_processed_data`](iris/iris_utils/ingestion_persistence.py) is imported from [`ingestion.iris_utils.ingestion_persistence`](iris/iris_utils/ingestion_persistence.py) ([`iris/high_frequency_ingestion.py:12`](iris/high_frequency_ingestion.py:12)) but is not used within the module.
*   **Extensibility:** The module is tightly coupled to Alpha Vantage. Future extensions might involve abstracting the data source to support other high-frequency data providers.

## 4. Connections & Dependencies

### Internal Project Dependencies:
*   [`ingestion.iris_plugins_variable_ingestion.alpha_vantage_plugin.AlphaVantagePlugin`](iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py): Used for making API calls to Alpha Vantage. An instance is passed to the constructor.
*   [`data.high_frequency_data_store.HighFrequencyDataStore`](data/high_frequency_data_store.py): Used for storing the processed high-frequency data. An instance is created in the constructor.
*   [`ingestion.iris_utils.ingestion_persistence.save_processed_data`](iris/iris_utils/ingestion_persistence.py): Imported but currently unused.

### External Library Dependencies:
*   `time`: Used for rate limiting and timestamping requests ([`iris/high_frequency_ingestion.py:5-6`](iris/high_frequency_ingestion.py:5)). (Note: Duplicate import on lines 5 and 6).
*   `datetime` (as `dt`): Used for timestamp conversion ([`iris/high_frequency_ingestion.py:7`](iris/high_frequency_ingestion.py:7)).
*   `typing` (Dict, List, Any, Optional): Used for type hinting ([`iris/high_frequency_ingestion.py:8`](iris/high_frequency_ingestion.py:8)).
*   `sys`, `os`: Used only within the `if __name__ == "__main__":` block for path manipulation to enable example execution ([`iris/high_frequency_ingestion.py:115-116`](iris/high_frequency_ingestion.py:115)).

### Data Interaction:
*   **Input:** Fetches data from the Alpha Vantage API via `AlphaVantagePlugin`.
*   **Output:** Stores processed data points (open, high, low, close, volume) into `HighFrequencyDataStore`.
*   Logs informational messages and errors to standard output using `print()`.

## 5. Function and Class Example Usages

### Class: `HighFrequencyIngestion`
```python
from ingestion.iris_plugins_variable_ingestion.alpha_vantage_plugin import AlphaVantagePlugin
from ingestion.high_frequency_ingestion import HighFrequencyIngestion

# Assuming AlphaVantagePlugin is initialized, e.g.:
# av_plugin = AlphaVantagePlugin(api_key="YOUR_API_KEY")
# Ensure ALPHA_VANTAGE_KEY environment variable is set or provide api_key directly

# Initialize the ingestion module
# ingestion_module = HighFrequencyIngestion(
#     alpha_vantage_plugin=av_plugin,
#     entitlement='delayed',  # or 'realtime' if applicable
#     rate_limit_per_minute=150
# )

# Fetch and store stock data for a specified interval
# ingestion_module.fetch_and_store_stock_data(interval='1min')
```
This usage pattern is derived from the commented-out example in the module's `if __name__ == "__main__":` block ([`iris/high_frequency_ingestion.py:130-138`](iris/high_frequency_ingestion.py:130)).

## 6. Hardcoding Issues

*   **Default Rate Limit:** `rate_limit_per_minute` defaults to `150` ([`iris/high_frequency_ingestion.py:16`](iris/high_frequency_ingestion.py:16)), though configurable.
*   **Default Entitlement:** `entitlement` defaults to `'delayed'` ([`iris/high_frequency_ingestion.py:16`](iris/high_frequency_ingestion.py:16)), though configurable.
*   **Time Constant:** `60` (seconds) is used for rate limit calculations ([`iris/high_frequency_ingestion.py:37,41`](iris/high_frequency_ingestion.py:37)).
*   **API Parameters:**
    *   `"function": "TIME_SERIES_INTRADAY"` ([`iris/high_frequency_ingestion.py:61`](iris/high_frequency_ingestion.py:61)).
    *   `"outputsize": "compact"` ([`iris/high_frequency_ingestion.py:64`](iris/high_frequency_ingestion.py:64)).
    *   `"datatype": "json"` ([`iris/high_frequency_ingestion.py:65`](iris/high_frequency_ingestion.py:65)).
*   **Dataset ID Prefix:** `dataset_id` is formatted as `f"high_freq_stock_{symbol}_{interval}"` ([`iris/high_frequency_ingestion.py:59`](iris/high_frequency_ingestion.py:59)).
*   **Alpha Vantage JSON Keys:** Specific keys like `"Time Series ({interval})"`, `"1. open"`, `"2. high"`, etc., are used to parse the API response ([`iris/high_frequency_ingestion.py:71,75,87-91`](iris/high_frequency_ingestion.py:71)).
*   **Timestamp Format:** `'%Y-%m-%d %H:%M:%S'` for parsing incoming timestamps ([`iris/high_frequency_ingestion.py:82`](iris/high_frequency_ingestion.py:82)).
*   **Variable Naming Convention:** Stored variable names are constructed as `f"{var_name}_{metric}"` ([`iris/high_frequency_ingestion.py:97`](iris/high_frequency_ingestion.py:97)).

## 7. Coupling Points

*   **`AlphaVantagePlugin`:** Tightly coupled. The module requires an instance of `AlphaVantagePlugin` for its core functionality (fetching data, accessing `STOCK_SYMBOLS`).
*   **`HighFrequencyDataStore`:** Tightly coupled. An instance is created and used for all data persistence.
*   **Alpha Vantage API Structure:** The processing logic is dependent on the specific JSON structure and keys returned by the Alpha Vantage API for intraday time series. Changes in the API response format would require code modifications.

## 8. Existing Tests

*   There is no dedicated test file (e.g., `tests/test_high_frequency_ingestion.py`) apparent from the provided file listing.
*   The `if __name__ == "__main__":` block ([`iris/high_frequency_ingestion.py:113-141`](iris/high_frequency_ingestion.py:113)) contains commented-out example code that can serve as a manual integration test or usage demonstration. It requires an Alpha Vantage API key to be functional. This is not a substitute for automated unit or integration tests.

## 9. Module Architecture and Flow

1.  **Initialization (`HighFrequencyIngestion.__init__`)**:
    *   Accepts an `AlphaVantagePlugin` instance, `entitlement` type, and `rate_limit_per_minute`.
    *   Initializes an empty list `self.request_timestamps` for rate limiting.
    *   Instantiates `HighFrequencyDataStore` as `self.data_store`.
2.  **Rate Limiting (`_wait_for_rate_limit`)**:
    *   This private method is called before each API request.
    *   It prunes `self.request_timestamps` to keep only requests made in the last 60 seconds.
    *   If the count of recent requests meets or exceeds `self.rate_limit_per_minute`, it calculates the necessary wait time and pauses execution using `time.sleep()`.
3.  **Data Fetching and Storing (`fetch_and_store_stock_data`)**:
    *   Takes an `interval` string (e.g., '1min') as an argument.
    *   Iterates through stock symbols defined in `self.alpha_vantage_plugin.STOCK_SYMBOLS`.
    *   For each symbol:
        *   Calls `_wait_for_rate_limit()`.
        *   Appends the current time to `self.request_timestamps`.
        *   Constructs API request parameters.
        *   Calls `self.alpha_vantage_plugin._safe_get()` to retrieve data.
        *   If data retrieval is successful and data is valid:
            *   Extracts the time series data.
            *   Iterates over each timestamp and corresponding OHLCV (Open, High, Low, Close, Volume) values.
            *   Converts the timestamp string to ISO format.
            *   For each metric (open, high, low, close, volume), it calls `self.data_store.store_data_point()` with a constructed `variable_name` (e.g., `STOCKSYMBOL_open`), the ISO timestamp, and the metric's value.
            *   Handles `ValueError` or `KeyError` during data point processing by printing an error message.
        *   Prints the number of processed data points for the symbol.

## 10. Naming Conventions

*   **Class Name:** `HighFrequencyIngestion` (PascalCase) - Adheres to PEP 8.
*   **Method Names:** `__init__`, `_wait_for_rate_limit`, `fetch_and_store_stock_data` (snake_case, with leading underscore for `_wait_for_rate_limit` indicating intended privacy) - Adheres to PEP 8.
*   **Variable Names:** Generally snake_case (e.g., `alpha_vantage_plugin`, `rate_limit_per_minute`, `time_series_data`) - Adheres to PEP 8.
*   **Constants:** `STOCK_SYMBOLS` (referenced from `AlphaVantagePlugin`) is expected to be uppercase.
*   **Consistency:** Naming is consistent within the module.
*   **Clarity:** Names are generally descriptive and understandable.
*   **Duplicate Import:** `import time` is present on both line 5 and line 6. This should be cleaned up.