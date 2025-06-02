# Module Analysis: `iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py`

## 1. Module Intent/Purpose

The primary role of the [`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:1) module is to connect to the CoinMarketCap API and fetch cryptocurrency market data. This includes prices, market capitalizations, trading volumes, and other metrics for a predefined list of top cryptocurrencies, as well as global market metrics. It then processes this data into a standardized signal format for use within the Iris system and persists the raw and processed data.

## 2. Operational Status/Completeness

The module appears largely complete for its defined scope of fetching current data for a list of top cryptocurrencies and global metrics.
- It includes API key handling (disabling the plugin if the key is not found via the `COINMARKETCAP_API_KEY` environment variable).
- It implements retry logic for API requests ([`_safe_get`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:105)).
- It handles data persistence for API requests, responses, and processed signals using utilities from [`ingestion.iris_utils.ingestion_persistence`](../../iris/iris_utils/ingestion_persistence.py:).
- There are no obvious TODO comments or major placeholders for its current functionality.

## 3. Implementation Gaps / Unfinished Next Steps

- **Configurability:** The list of `TOP_CRYPTOS` ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:41`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:41)) and `SIGNAL_TYPES` ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:55`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:55)) are hardcoded. These could be made configurable, perhaps through a configuration file or environment variables.
- **Expanded Data Fetching:** The plugin currently fetches latest quotes. It could be extended to:
    - Fetch historical data for cryptocurrencies.
    - Fetch data for a broader range of cryptocurrencies beyond the hardcoded top list.
    - Fetch other types of data available from the API (e.g., exchange data, detailed coin information).
- **Dynamic Fetch Frequency:** The fetch frequency for global metrics is hardcoded to run approximately every 6 hours within the first 15 minutes of the hour ([`fetch_signals`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:98)). This could be made more configurable.
- **Error Handling Granularity:** While there's retry logic, more specific error handling for different API error codes from CoinMarketCap could be beneficial. Currently, any non-zero `error_code` in the API response status is treated similarly ([`_safe_get`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:147)).

## 4. Connections & Dependencies

### Direct Project Module Imports:
- [`ingestion.iris_plugins.IrisPluginManager`](../../iris/iris_plugins.py:) ([`CoinMarketCapPlugin`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:29))
- From [`ingestion.iris_utils.ingestion_persistence`](../../iris/iris_utils/ingestion_persistence.py:):
    - [`ensure_data_directory`](../../iris/iris_utils/ingestion_persistence.py:)
    - [`save_request_metadata`](../../iris/iris_utils/ingestion_persistence.py:)
    - [`save_api_response`](../../iris/iris_utils/ingestion_persistence.py:)
    - [`save_processed_data`](../../iris/iris_utils/ingestion_persistence.py:)

### External Library Dependencies:
- `requests` (for making HTTP API calls)
- Standard Python libraries: `datetime`, `logging`, `time`, `os`, `typing`, `json`.

### Interaction with Other Modules via Shared Data:
- The module interacts with the file system by saving data via the `ingestion_persistence` utilities. Data is stored in a directory structure based on the `_SOURCE_NAME` ("coinmarketcap"). This implies that other modules might consume this persisted data.

### Input/Output Files:
- **Input:**
    - Environment Variable: `COINMARKETCAP_API_KEY` is required for the plugin to be enabled and function.
- **Output (via `ingestion_persistence`):**
    - Request metadata files (JSON).
    - API response files (JSON).
    - Processed data files (JSON), containing the extracted signals.
    - Log files (standard logging).

## 5. Function and Class Example Usages

- **`CoinMarketCapPlugin` Class:**
  ```python
  # Typically instantiated and managed by a plugin framework
  # Assuming 'plugin_manager' handles plugin loading
  # coin_plugin = CoinMarketCapPlugin()
  # if coin_plugin.enabled:
  #     signals = coin_plugin.fetch_signals()
  #     for signal in signals:
  #         print(signal)
  ```
- **[`fetch_signals()`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:76):**
  The main method called by the Iris system to retrieve data. It orchestrates calls to fetch data for top cryptocurrencies and global market metrics, then processes them.
- **[`_safe_get(endpoint: str, params: dict, dataset_id: str)`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:105):**
  An internal helper method to make robust GET requests to the CoinMarketCap API, handling retries and basic error checking.
- **[`_fetch_latest_crypto_data()`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:168):**
  Fetches the latest market data for the cryptocurrencies listed in `TOP_CRYPTOS`.
- **[`_fetch_global_metrics()`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:189):**
  Fetches global cryptocurrency market metrics.
- **[`_process_crypto_data(crypto_data: Dict, timestamp: dt.datetime)`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:206):**
  Transforms the raw JSON response for cryptocurrency data into a list of standardized signal dictionaries.
- **[`_process_global_metrics(global_data: Dict, timestamp: dt.datetime)`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:325):**
  Transforms the raw JSON response for global metrics into a list of standardized signal dictionaries.

## 6. Hardcoding Issues

- **API Configuration:**
    - `_SOURCE_NAME = "coinmarketcap"` ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:27`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:27))
    - `plugin_name = "coinmarketcap_plugin"` ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:30`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:30))
    - `enabled = False` (default state, can be overridden if API key is present) ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:31`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:31))
    - `concurrency = 1` ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:32`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:32))
    - `BASE_URL = "https://pro-api.coinmarketcap.com/v1"` ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:35`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:35))
    - `REQUEST_TIMEOUT = 30.0` ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:36`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:36))
    - `RETRY_WAIT = 5.0` ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:37`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:37))
    - `MAX_RETRIES = 2` ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:38`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:38))
- **Data Scope:**
    - `TOP_CRYPTOS`: List of cryptocurrency symbols (e.g., "BTC", "ETH") ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:41-52`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:41-52)).
    - `SIGNAL_TYPES`: List of metrics to extract (e.g., "price", "market_cap") ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:55-61`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:55-61)).
- **Environment Variable Name:**
    - `"COINMARKETCAP_API_KEY"` for the API key ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:66`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:66)).
- **Operational Logic:**
    - Global metrics fetch condition: `if now.hour % 6 == 0 and now.minute < 15:` ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:98`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:98)).
    - Dataset ID strings for persistence, e.g., `"crypto_data_{len(self.TOP_CRYPTOS)}_currencies"` ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:180`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:180)) and `"global_metrics"` ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:197`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:197)).
    - Default currency for conversion: `"USD"` in API parameters ([`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:176`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:176), [`iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:193`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:193)).
- **Signal Construction:**
    - Signal names are constructed with hardcoded prefixes like `"crypto_"` and source `"coinmarketcap"`.

## 7. Coupling Points

- **`IrisPluginManager`:** The module is tightly coupled to the [`IrisPluginManager`](../../iris/iris_plugins.py:) base class, inheriting its structure and expected methods (like `fetch_signals`).
- **`ingestion_persistence` Utilities:** Significant coupling with the functions from [`ingestion.iris_utils.ingestion_persistence`](../../iris/iris_utils/ingestion_persistence.py:) for all data storage operations. Changes to this utility module's API could break this plugin.
- **CoinMarketCap API:** Directly dependent on the CoinMarketCap API's endpoints, request/response structure, and authentication mechanism. API changes would require updates to this plugin.
- **Environment Variable:** Relies on the specific environment variable `COINMARKETCAP_API_KEY` being set.
- **Signal Format:** Produces signals in a specific dictionary format, which consumers of these signals will expect.

## 8. Existing Tests

Based on the provided file list, there is no specific test file named `test_coinmarketcap_plugin.py` or similar within the `tests/iris/` or `tests/plugins/` directories. While general plugin loading tests might exist (e.g., [`iris/test_plugins.py`](../../iris/test_plugins.py:)), it is likely that dedicated unit or integration tests for the specific functionality of the `CoinMarketCapPlugin` (such as API interaction mocking, data processing logic, and error handling) are missing.

## 9. Module Architecture and Flow

1.  **Initialization (`CoinMarketCapPlugin.__init__`)**:
    *   Retrieves the `COINMARKETCAP_API_KEY` from environment variables.
    *   Sets `self.enabled = True` if the key is found; otherwise, logs a warning and remains disabled.
    *   Calls [`ensure_data_directory(_SOURCE_NAME)`](../../iris/iris_utils/ingestion_persistence.py:) to prepare the storage location.
2.  **Signal Fetching (`fetch_signals`)**:
    *   Checks if the plugin is enabled and has an API key. Returns an empty list if not.
    *   Calls [`_fetch_latest_crypto_data()`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:168) to get data for `TOP_CRYPTOS`.
    *   If successful, processes the data using [`_process_crypto_data()`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:206).
    *   Conditionally (every 6 hours), calls [`_fetch_global_metrics()`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:189).
    *   If successful, processes global metrics using [`_process_global_metrics()`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:325).
    *   Aggregates and returns all collected signals.
3.  **API Interaction (`_safe_get`)**:
    *   Constructs the API URL and headers (including the API key).
    *   Saves request metadata using [`save_request_metadata()`](../../iris/iris_utils/ingestion_persistence.py:).
    *   Performs a `requests.get()` call with a timeout.
    *   Implements a retry loop (`MAX_RETRIES`).
    *   On successful HTTP response:
        *   Parses JSON.
        *   Saves the API response using [`save_api_response()`](../../iris/iris_utils/ingestion_persistence.py:).
        *   Checks the `status` field in the JSON data for API-level errors. If an error is found and retries are available, it waits and retries.
        *   Returns the parsed JSON data.
    *   Handles `requests.exceptions.RequestException` and `json.JSONDecodeError`.
    *   Logs errors if all retries fail.
4.  **Data Processing (`_process_crypto_data`, `_process_global_metrics`)**:
    *   Iterate through the raw API data.
    *   Extract specific fields based on `SIGNAL_TYPES` or predefined metric names.
    *   Construct signal dictionaries with a standard structure: `name`, `value`, `source`, `timestamp`, `metadata`.
    *   Save each processed signal using [`save_processed_data()`](../../iris/iris_utils/ingestion_persistence.py:).
    *   Handle potential `KeyError` or `TypeError` during data extraction.

## 10. Naming Conventions

- **Class Name:** `CoinMarketCapPlugin` follows PascalCase, which is standard for Python classes.
- **Method Names:**
    - Public methods like [`fetch_signals()`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:76) use snake_case.
    - Internal/protected methods like [`_safe_get()`](../../iris/iris_plugins_variable_ingestion/coinmarketcap_plugin.py:105) are prefixed with a single underscore and use snake_case.
- **Constants:** Variables intended as constants like `BASE_URL`, `TOP_CRYPTOS`, `_SOURCE_NAME` use UPPER_SNAKE_CASE.
- **Local Variables:** Generally use snake_case (e.g., `api_key`, `response_data`, `iso_timestamp`).
- **Signal Naming:** Signal names are dynamically constructed (e.g., `f"crypto_{symbol.lower()}_price"`), resulting in a consistent `crypto_<symbol>_<metric>` pattern.
- **Overall Consistency:** Naming conventions appear consistent throughout the module and largely adhere to PEP 8 guidelines. There are no obvious AI assumption errors or significant deviations from common Python practices.
