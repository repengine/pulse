# Module Analysis: `iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py`

## 1. Module Intent/Purpose

The primary role of the [`alpha_vantage_plugin.py`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:) module is to connect to the Alpha Vantage API and fetch various financial market data. This includes daily stock prices, Forex (foreign exchange) rates, cryptocurrency prices, and selected economic indicators. It functions as a data ingestion plugin within the Iris system, transforming and persisting the retrieved data for further use.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope.
*   It correctly handles the presence or absence of the `ALPHA_VANTAGE_KEY` environment variable, disabling itself if the key is not found.
*   API request mechanisms include retries, error handling for HTTP issues, and checks for API-specific error messages in responses.
*   It implements a basic strategy to mitigate API rate-limiting by fetching only a subset of configured symbols/indicators during each execution cycle.
*   Data persistence is handled through the `ingestion_persistence` utility, saving raw responses, processed data, and metadata.
*   There are no obvious major placeholders (e.g., `pass` statements in critical functions or extensive `TODO` comments indicating unfinished core functionality).

## 3. Implementation Gaps / Unfinished Next Steps

*   **Rate Limiting Strategy:** The current method of cycling through symbols/indicators using `dt.datetime.now().day % N` (e.g., in [`_fetch_stock_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:180), [`_fetch_crypto_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:246)) is a simple approach to stay within free tier limits. A more robust system (e.g., a persistent queue, stateful round-robin, or tracking last fetch times) could ensure more even and comprehensive data collection, especially if the plugin doesn't run strictly daily.
*   **Symbol/Indicator Configuration:** The lists of stock symbols ([`STOCK_SYMBOLS`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:45)), crypto symbols ([`CRYPTO_SYMBOLS`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:61)), forex pairs ([`FOREX_SYMBOLS`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:67)), and economic indicators ([`ECONOMIC_INDICATORS`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:74)) are hardcoded. Making these configurable (e.g., via an external configuration file or database) would enhance flexibility.
*   **Historical Data Ingestion:** The plugin primarily focuses on fetching current or latest data points (e.g., using `GLOBAL_QUOTE`, `CURRENCY_EXCHANGE_RATE`). While Alpha Vantage provides extensive historical data endpoints, this plugin does not seem to utilize them for backfilling or fetching time series beyond the most recent data point for economic indicators.
*   **API Entitlement:** The API parameter `"entitlement": "delayed"` is hardcoded in the [`_safe_get()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:118) method. This could be made configurable if users have premium keys with real-time data access.
*   **Expanded Data Coverage:** Alpha Vantage offers a wider array of data (e.g., technical indicators, more granular fundamental data, sector performances). The plugin currently only scratches the surface of available endpoints.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   `from iris.iris_plugins import IrisPluginManager` ([`iris/iris_plugins.py`](../../../iris/iris_plugins.py:18))
*   `from iris.iris_utils.ingestion_persistence import ensure_data_directory, save_to_file, save_request_metadata, save_api_response, save_processed_data, save_data_point_incremental` ([`iris/iris_utils/ingestion_persistence.py`](../../../iris/iris_utils/ingestion_persistence.py:19))

### External Library Dependencies:
*   `datetime` (imported as `dt`)
*   `logging`
*   `os`
*   `time`
*   `requests`

### Interaction with Other Modules via Shared Data:
*   The plugin writes data to the file system using functions from [`ingestion_persistence.py`](../../../iris/iris_utils/ingestion_persistence.py:19). This data is organized under a source-specific directory (defined by [`_SOURCE_NAME = "alpha_vantage"`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:31)) and is presumably consumed by other parts of the Iris system for analysis or further processing.

### Input/Output Files:
*   **Input:**
    *   Reads the `ALPHA_VANTAGE_KEY` from environment variables during initialization ([`__init__()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:84)).
*   **Output:**
    *   Log messages via the `logging` module.
    *   Data files: Saves raw API responses, processed data, incremental data points, and request/error metadata. These are stored in a structured directory like `data/alpha_vantage/`, with filenames derived from `dataset_id` (e.g., `stock_AAPL.json`, `crypto_BTCUSD_error.json`). Examples:
        *   [`save_request_metadata()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:127)
        *   [`save_api_response()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:149)
        *   [`save_data_point_incremental()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:217)
        *   [`save_processed_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:227)
        *   [`save_to_file()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:238) (for errors)

## 5. Function and Class Example Usages

*   **`AlphaVantagePlugin` Class ([`AlphaVantagePlugin`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:33))**
    *   This class is intended to be instantiated and managed by the Iris plugin system. Its `fetch_signals()` method is the main entry point for data retrieval.
    ```python
    # Hypothetical usage within Iris plugin management
    # from iris.iris_plugins_variable_ingestion.alpha_vantage_plugin import AlphaVantagePlugin
    #
    # alpha_plugin = AlphaVantagePlugin()
    # if alpha_plugin.enabled:
    #     financial_signals = alpha_plugin.fetch_signals()
    #     for signal in financial_signals:
    #         # Process each signal
    #         print(signal)
    ```

*   **`fetch_signals()` Method ([`fetch_signals()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:93))**
    *   Orchestrates the fetching of data for stocks, crypto, forex, and economic indicators by calling respective private methods.
    *   Returns a list of dictionaries, where each dictionary represents a data signal.

*   **`_safe_get(params: dict, dataset_id: str)` Method ([`_safe_get()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:118))**
    *   An internal helper method responsible for making HTTP GET requests to the Alpha Vantage API. It incorporates error handling, retries, and saves request/response metadata using `ingestion_persistence` utilities.

*   **`_fetch_stock_data()`, `_fetch_crypto_data()`, `_fetch_forex_data()`, `_fetch_economic_data()` Methods**
    *   These private methods handle the specifics of fetching data for each category:
        *   [`_fetch_stock_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:180)
        *   [`_fetch_crypto_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:246)
        *   [`_fetch_forex_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:309)
        *   [`_fetch_economic_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:372)
    *   They construct API parameters, call `_safe_get()`, parse the response, format the data into the standard signal structure, and persist it.

*   **`_to_timestamp(date_str: str)` Method ([`_to_timestamp()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:445))**
    *   A utility function to convert date strings (potentially with or without time components) from API responses into a standardized ISO-8601 UTC timestamp string. If parsing fails, it defaults to the current UTC time.

## 6. Hardcoding Issues

The module contains several hardcoded values:

*   **Configuration Constants:**
    *   `_SOURCE_NAME = "alpha_vantage"` ([line 31](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:31))
    *   `plugin_name = "alpha_vantage_plugin"` ([line 34](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:34))
    *   `concurrency = 2` ([line 36](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:36))
    *   `BASE_URL = "https://www.alphavantage.co/query"` ([line 39](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:39))
    *   `REQUEST_TIMEOUT = 10.0` ([line 40](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:40))
    *   `RETRY_WAIT = 1.5` ([line 41](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:41))
    *   `MAX_RETRIES = 2` ([line 42](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:42))
*   **Symbol Definitions:** The core data points to fetch are hardcoded:
    *   [`STOCK_SYMBOLS`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:45) (e.g., `"aapl_price": "AAPL"`)
    *   [`CRYPTO_SYMBOLS`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:61) (e.g., `"btc_usd": "BTCUSD"`)
    *   [`FOREX_SYMBOLS`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:67) (e.g., `"eur_usd": "EURUSD"`)
    *   [`ECONOMIC_INDICATORS`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:74) (e.g., `"real_gdp": "REAL_GDP"`)
*   **API Parameters:**
    *   `"entitlement": "delayed"` in [`_safe_get()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:124).
*   **Rate Limiting Logic:**
    *   Magic numbers for selecting subsets of symbols/indicators (e.g., `day % 5` in [`_fetch_stock_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:185), `day % 2` in [`_fetch_crypto_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:251)).
*   **Default/Fallback Values:**
    *   Default values in `.get()` calls when parsing API responses (e.g., `0`, `"0%"` in [`_fetch_stock_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:200)).
*   **Source Strings:**
    *   Strings like `"alpha_vantage"`, `"alpha_vantage_crypto"`, etc., used in the `source` field of signal dictionaries ([line 207](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:207), [line 275](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:275)).
*   **Timestamp Formatting:**
    *   Default time `T12:00:00` added to date-only strings in [`_to_timestamp()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:452).

## 7. Coupling Points

*   **`IrisPluginManager`:** The [`AlphaVantagePlugin`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:33) class inherits from [`IrisPluginManager`](../../../iris/iris_plugins.py:18), making it dependent on this base class for its structure and integration into the Iris plugin framework.
*   **`iris.iris_utils.ingestion_persistence`:** The module is tightly coupled with the functions provided by [`ingestion_persistence.py`](../../../iris/iris_utils/ingestion_persistence.py:19) for all its data and metadata saving operations. Changes to the API of `ingestion_persistence` would likely require updates in this plugin.
*   **Alpha Vantage API Structure:** The plugin's parsing logic is specific to the JSON response structures of the Alpha Vantage API. Any changes to the API's output format would necessitate modifications to the data extraction logic in methods like [`_fetch_stock_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:180), etc.
*   **Environment Variable:** Relies on the `ALPHA_VANTAGE_KEY` environment variable for API authentication.

## 8. Existing Tests

*   A corresponding test file, [`iris/test_alpha_vantage.py`](../../../iris/test_alpha_vantage.py:0), exists in the project structure.
*   Without examining the contents of [`test_alpha_vantage.py`](../../../iris/test_alpha_vantage.py:0), the exact nature, coverage, and effectiveness of these tests cannot be fully determined.
*   It is presumed that these tests would involve mocking the `requests.get` calls to simulate API responses and verifying the correct parsing, data transformation, error handling, and interaction with the `ingestion_persistence` module.

## 9. Module Architecture and Flow

1.  **Initialization (`__init__`)**:
    *   The [`AlphaVantagePlugin`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:33) class is initialized.
    *   It attempts to load the `ALPHA_VANTAGE_KEY` from environment variables ([`os.getenv()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:86)).
    *   If the key is not found, the plugin's `enabled` status is set to `False`, and warnings are logged.
2.  **Signal Fetching (`fetch_signals`)**:
    *   This is the main public method called to retrieve data.
    *   If the plugin is not `enabled` (no API key), it returns an empty list.
    *   It sequentially calls private methods to fetch different categories of data:
        *   [`_fetch_stock_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:180)
        *   [`_fetch_crypto_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:246)
        *   [`_fetch_forex_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:309)
        *   [`_fetch_economic_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:372) (for a single, rotated indicator).
    *   The results (lists of signal dictionaries) from these calls are aggregated and returned.
3.  **Category-Specific Data Fetching (e.g., `_fetch_stock_data`)**:
    *   A subset of symbols for the category is selected based on the current day (e.g., `dt.datetime.now().day % 5` ([line 185](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:185))) to manage rate limits.
    *   For each selected symbol:
        *   A `dataset_id` is created (e.g., `f"stock_{symbol}"`).
        *   API request parameters are prepared (e.g., `function`, `symbol`).
        *   The [`_safe_get()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:118) method is called to execute the API request.
        *   If data is successfully retrieved and valid:
            *   The relevant part of the JSON response is extracted.
            *   Data points (price, timestamp) are parsed and type-converted.
            *   Timestamps are standardized to ISO-8601 UTC using [`_to_timestamp()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:445).
            *   A signal dictionary is constructed.
            *   The data is persisted using [`save_data_point_incremental()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:217) and [`save_processed_data()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:227).
            *   Error handling (try-except blocks) is in place for parsing issues, logging errors, and saving error information.
4.  **Safe API Request (`_safe_get`)**:
    *   Ensures the data directory exists via [`ensure_data_directory()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:121).
    *   Appends the API key and `"entitlement": "delayed"` to the request parameters.
    *   Saves request metadata using [`save_request_metadata()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:127).
    *   Enters a retry loop (`for attempt in range(self.MAX_RETRIES + 1)` ([line 134](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:134))):
        *   Makes an HTTP GET request using `requests.get()`.
        *   Checks for HTTP errors (`resp.raise_for_status()`).
        *   Parses the JSON response.
        *   Checks for Alpha Vantage specific error messages (e.g., `"Error Message"` in `data`). If found, logs and saves the error response.
        *   If successful, saves the API response using [`save_api_response()`](../../../iris/iris_plugins_variable_ingestion/alpha_vantage_plugin.py:158) and returns the data.
        *   If an exception occurs, logs a warning and sleeps before retrying (if attempts remain).
    *   If all retries fail, saves an error response indicating request failure and returns `None`.
5.  **Timestamp Conversion (`_to_timestamp`)**:
    *   Takes a date string as input.
    *   Attempts to parse it. If it's a date without time, `T12:00:00` is appended.
    *   Converts the datetime object to UTC and formats it as an ISO-8601 string.
    *   If parsing fails, it defaults to the current UTC datetime in ISO-8601 format.

## 10. Naming Conventions

*   **Class Names:** `AlphaVantagePlugin` uses PascalCase, adhering to PEP 8.
*   **Method Names:** Public methods like `fetch_signals()` and private/internal methods like `_safe_get()`, `_fetch_stock_data()` use snake_case. Private methods are correctly prefixed with a single underscore. This aligns with PEP 8.
*   **Variable Names:** Local variables (e.g., `var_name`, `symbol`, `dataset_id`, `iso_timestamp`) and instance variables (e.g., `api_key`) use snake_case, which is standard.
*   **Constant Names:** Module-level and class-level constants (e.g., `_SOURCE_NAME`, `BASE_URL`, `STOCK_SYMBOLS`, `MAX_RETRIES`) use UPPER_SNAKE_CASE, which is the correct convention.
*   **Module Name:** `alpha_vantage_plugin.py` is in snake_case, which is appropriate for Python modules.
*   **Overall:** The naming conventions are consistent and largely follow PEP 8 guidelines. There are no obvious AI assumption errors or significant deviations from standard Python naming practices. The names are generally descriptive of their purpose.