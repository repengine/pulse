# Module Analysis: `iris/iris_plugins_finance.py`

## 1. Module Intent/Purpose

The primary role of [`iris/iris_plugins_finance.py`](../../../iris/iris_plugins_finance.py) is to provide finance-focused data ingestion plugins for the IRIS system. It is responsible for fetching financial data (e.g., stock prices, macroeconomic indicators, sentiment scores) from various external APIs, normalizing this data into a standardized "signal" format, and making it available for consumption by other parts of the IRIS application, likely an `IrisPluginManager`. The module aims to be dependency-light, relying only on the `requests` library for HTTP calls, and uses environment variables for API key management.

## 2. Operational Status/Completeness

The module appears partially operational.
*   Plugins for Alpha Vantage (daily adjusted close for a watchlist) and Finnhub (real-time quote and news sentiment) are implemented and seem functional, assuming the respective API keys are provided via environment variables.
*   A significant discrepancy exists: the module's docstring ([`iris/iris_plugins_finance.py:17`](../../../iris/iris_plugins_finance.py:17)) lists a "FRED" plugin as implemented for selected macro indicators. However, there is no corresponding `_fred_build_signals()` helper function or its integration into the main [`finance_plugins()`](../../../iris/iris_plugins_finance.py:158) aggregator function. This indicates a major incompleteness.
*   No explicit "TODO" comments are present, but the missing FRED plugin is a clear sign of unfinished work.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Missing FRED Plugin:** The most critical gap is the unimplemented FRED plugin, despite its mention in the documentation ([`iris/iris_plugins_finance.py:17`](../../../iris/iris_plugins_finance.py:17)).
*   **Static Symbol Lists:** The financial symbols fetched by Alpha Vantage ([`_ALPHA_SYMBOLS`](../../../iris/iris_plugins_finance.py:74)) and Finnhub ([`_FINNHUB_SYMBOLS`](../../../iris/iris_plugins_finance.py:119)) are hardcoded and very limited. A more robust implementation would allow these symbols to be configured externally (e.g., via a configuration file or environment variable).
*   **Limited Error Handling for API Specifics:** While the [`_safe_get()`](../../../iris/iris_plugins_finance.py:46) function provides generic retry logic for network requests, the module lacks specific error handling for API rate limits (especially relevant for Alpha Vantage's free tier) or other API-specific error responses beyond basic parsing.
*   **Basic Sentiment Integration:** The Finnhub plugin fetches a `companyNewsScore` ([`iris/iris_plugins_finance.py:137-150`](../../../iris/iris_plugins_finance.py:137-150)), but its use is minimal. Further processing or more sophisticated integration of this sentiment data could be a logical next step.
*   **Extensibility for More Plugins:** The docstring ([`iris/iris_plugins_finance.py:24`](../../../iris/iris_plugins_finance.py:24)) encourages adding more plugins by following the existing template, implying an intent for broader financial data source coverage.

## 4. Connections & Dependencies

*   **Direct Imports from Other Project Modules:** None. This module appears designed to be self-contained in terms of internal project dependencies.
*   **External Library Dependencies:**
    *   `requests` ([`iris/iris_plugins_finance.py:35`](../../../iris/iris_plugins_finance.py:35)): Used for making HTTP GET requests to external financial data APIs.
*   **Interaction with Other Modules via Shared Data:**
    *   The primary interaction is with an implied `IrisPluginManager`, which is expected to call the [`finance_plugins()`](../../../iris/iris_plugins_finance.py:158) function and consume the list of signal dictionaries it returns.
*   **Input/Output Files (and Environment Variables):**
    *   **Input (Environment Variables):**
        *   `ALPHA_VANTAGE_KEY` ([`iris/iris_plugins_finance.py:72`](../../../iris/iris_plugins_finance.py:72)): API key for Alpha Vantage.
        *   `FINNHUB_KEY` ([`iris/iris_plugins_finance.py:117`](../../../iris/iris_plugins_finance.py:117)): API key for Finnhub.
        *   `IRIS_API_TIMEOUT` ([`iris/iris_plugins_finance.py:38`](../../../iris/iris_plugins_finance.py:38)): Timeout for HTTP requests (defaults to "10" seconds).
    *   **Output:**
        *   Log messages via the standard `logging` module.
        *   The main programmatic output is a `List[Dict]` returned by [`finance_plugins()`](../../../iris/iris_plugins_finance.py:158), where each dictionary represents a financial signal.
        *   If run directly (`if __name__ == "__main__":`), it prints the fetched signals as a JSON formatted string to standard output ([`iris/iris_plugins_finance.py:170-172`](../../../iris/iris_plugins_finance.py:170-172)).

## 5. Function and Class Example Usages

*   **`_safe_get(url: str, params: dict[str, str] | None = None) -> Optional[dict]` ([`iris/iris_plugins_finance.py:46`](../../../iris/iris_plugins_finance.py:46))**
    *   **Description:** A wrapper for `requests.get` that includes retry logic with back-off for transient network errors and parses the JSON response.
    *   **Usage:** `data = _safe_get(API_URL, api_params)`
*   **`_to_timestamp(date_str: str | _dt.datetime) -> str` ([`iris/iris_plugins_finance.py:60`](../../../iris/iris_plugins_finance.py:60))**
    *   **Description:** Normalizes a date string (expected to be ISO format) or a `datetime` object into a UTC ISO-8601 timestamp string. Defaults to current UTC time if parsing fails.
    *   **Usage:** `timestamp_str = _to_timestamp(api_date_field)`
*   **`_alpha_build_signals() -> List[Dict]` ([`iris/iris_plugins_finance.py:80`](../../../iris/iris_plugins_finance.py:80))**
    *   **Description:** Fetches daily adjusted closing prices for symbols defined in `_ALPHA_SYMBOLS` from the Alpha Vantage API.
    *   **Usage:** Called internally by [`finance_plugins()`](../../../iris/iris_plugins_finance.py:158).
*   **`_finnhub_build_signals() -> List[Dict]` ([`iris/iris_plugins_finance.py:125`](../../../iris/iris_plugins_finance.py:125))**
    *   **Description:** Fetches current stock quotes and optionally news sentiment scores for symbols in `_FINNHUB_SYMBOLS` from the Finnhub API.
    *   **Usage:** Called internally by [`finance_plugins()`](../../../iris/iris_plugins_finance.py:158).
*   **`finance_plugins() -> List[Dict]` ([`iris/iris_plugins_finance.py:158`](../../../iris/iris_plugins_finance.py:158))**
    *   **Description:** The main public entry point for this plugin module. It aggregates results from all individual `_*_build_signals()` helper functions.
    *   **Intended Usage:** `all_financial_signals = finance_plugins()` (called by `IrisPluginManager`).

## 6. Hardcoding Issues

*   **API Base URLs:**
    *   Alpha Vantage: `_ALPHA_URL = "https://www.alphavantage.co/query"` ([`iris/iris_plugins_finance.py:73`](../../../iris/iris_plugins_finance.py:73))
    *   Finnhub: `_FINNHUB_URL = "https://finnhub.io/api/v1"` ([`iris/iris_plugins_finance.py:118`](../../../iris/iris_plugins_finance.py:118))
*   **Symbol Lists for APIs:**
    *   `_ALPHA_SYMBOLS = {"spx_close": "SPY", "btc_usd_close": "BTCUSD"}` ([`iris/iris_plugins_finance.py:74-77`](../../../iris/iris_plugins_finance.py:74-77))
    *   `_FINNHUB_SYMBOLS = {"aapl_close": "AAPL", "msft_close": "MSFT"}` ([`iris/iris_plugins_finance.py:119-122`](../../../iris/iris_plugins_finance.py:119-122))
*   **Retry Logic Parameters:**
    *   `_RETRY_WAIT = 1.5` seconds ([`iris/iris_plugins_finance.py:39`](../../../iris/iris_plugins_finance.py:39))
    *   `_MAX_RETRIES = 2` ([`iris/iris_plugins_finance.py:40`](../../../iris/iris_plugins_finance.py:40))
    (Note: `_REQUEST_TIMEOUT` is configurable via `IRIS_API_TIMEOUT` env var ([`iris/iris_plugins_finance.py:38`](../../../iris/iris_plugins_finance.py:38)))
*   **API-Specific Request Parameters & Response Keys:**
    *   Alpha Vantage: `function: "TIME_SERIES_DAILY_ADJUSTED"` ([`iris/iris_plugins_finance.py:87`](../../../iris/iris_plugins_finance.py:87)), `outputsize: "compact"` ([`iris/iris_plugins_finance.py:89`](../../../iris/iris_plugins_finance.py:89)), response key `"5. adjusted close"` ([`iris/iris_plugins_finance.py:100`](../../../iris/iris_plugins_finance.py:100)).
    *   Finnhub: Response keys `"c"` (current price) ([`iris/iris_plugins_finance.py:132`](../../../iris/iris_plugins_finance.py:132), [`iris/iris_plugins_finance.py:134`](../../../iris/iris_plugins_finance.py:134)), `"t"` (timestamp) ([`iris/iris_plugins_finance.py:135`](../../../iris/iris_plugins_finance.py:135)), `"companyNewsScore"` ([`iris/iris_plugins_finance.py:140`](../../../iris/iris_plugins_finance.py:140), [`iris/iris_plugins_finance.py:144`](../../../iris/iris_plugins_finance.py:144)).
*   **Source Identifier Strings:**
    *   `"alpha_vantage"` ([`iris/iris_plugins_finance.py:107`](../../../iris/iris_plugins_finance.py:107))
    *   `"finnhub"` ([`iris/iris_plugins_finance.py:136`](../../../iris/iris_plugins_finance.py:136))
    *   `"finnhub_sentiment"` ([`iris/iris_plugins_finance.py:145`](../../../iris/iris_plugins_finance.py:145))

## 7. Coupling Points

*   **External APIs:** The module is tightly coupled to the specific request parameters and response structures of the Alpha Vantage and Finnhub APIs. Any changes to these external APIs would likely necessitate code modifications in this module.
*   **Environment Variables:** Functionality depends on the presence and correctness of `ALPHA_VANTAGE_KEY`, `FINNHUB_KEY`, and optionally `IRIS_API_TIMEOUT` in the execution environment.
*   **Implied `IrisPluginManager`:** The design of [`finance_plugins()`](../../../iris/iris_plugins_finance.py:158) and its return signature (List[Dict] with specific keys: `name`, `value`, `source`, `timestamp`) implies a contract with an external calling component (the `IrisPluginManager`).
*   **Logging Configuration:** Relies on an external setup of the `logging` module for how its log messages are handled and displayed.

## 8. Existing Tests

*   **No Dedicated Unit Test File:** There is no `test_iris_plugins_finance.py` or similar file apparent in the project structure provided, indicating a lack of dedicated automated unit tests for this module.
*   **Manual Test Block:** The module includes a `if __name__ == "__main__":` block ([`iris/iris_plugins_finance.py:170-172`](../../../iris/iris_plugins_finance.py:170-172)) for quick manual testing. This block is marked with `# pragma: no cover`, suggesting it is intentionally excluded from code coverage metrics.
*   **Assessment:** The absence of automated tests is a significant gap, especially for a module interacting with external, potentially unreliable, APIs. This makes it harder to ensure continued correctness and to refactor with confidence.

## 9. Module Architecture and Flow

1.  **Initialization:**
    *   Sets up a `logger` instance.
    *   Defines module-level constants: `_REQUEST_TIMEOUT` (from `IRIS_API_TIMEOUT` env var or default 10s), `_RETRY_WAIT` (1.5s), and `_MAX_RETRIES` (2).
2.  **Helper Functions:**
    *   [`_safe_get()`](../../../iris/iris_plugins_finance.py:46): Handles HTTP GET requests with retries and JSON parsing. Returns `None` on persistent failure.
    *   [`_to_timestamp()`](../../../iris/iris_plugins_finance.py:60): Converts date strings or `datetime` objects to standardized ISO-8601 UTC strings.
3.  **API-Specific Signal Builders (`_*_build_signals`):**
    *   Example: [`_alpha_build_signals()`](../../../iris/iris_plugins_finance.py:80), [`_finnhub_build_signals()`](../../../iris/iris_plugins_finance.py:125).
    *   Each builder:
        *   Checks for its required API key (e.g., `_ALPHA_KEY` from `ALPHA_VANTAGE_KEY` env var). If missing, logs a message and returns an empty list.
        *   Iterates over a hardcoded dictionary of symbols (e.g., `_ALPHA_SYMBOLS`).
        *   For each symbol:
            *   Constructs API request parameters.
            *   Calls [`_safe_get()`](../../../iris/iris_plugins_finance.py:46) to fetch data.
            *   If data is successfully fetched and valid:
                *   Parses the response to extract the relevant financial value (e.g., price) and timestamp.
                *   Uses [`_to_timestamp()`](../../../iris/iris_plugins_finance.py:60) to normalize the timestamp.
                *   Creates a dictionary with keys `name`, `value`, `source`, and `timestamp`.
                *   Appends this dictionary to a list of signals.
        *   Returns the list of collected signals for that API.
4.  **Main Public Interface (`finance_plugins()`):**
    *   [`finance_plugins()`](../../../iris/iris_plugins_finance.py:158) is the primary entry point.
    *   It initializes an empty list `signals`.
    *   It iterates through a tuple of all implemented builder functions (e.g., `(_alpha_build_signals, _finnhub_build_signals)`).
    *   For each builder, it calls the function in a `try-except` block.
        *   If successful, it extends the main `signals` list with the results from the builder.
        *   If an exception occurs during a builder's execution, it logs an error (including the builder's name and the exception) and continues to the next builder.
    *   Returns the aggregated `signals` list.
5.  **Manual Execution (`if __name__ == "__main__":`):**
    *   If the script is executed directly ([`iris/iris_plugins_finance.py:170-172`](../../../iris/iris_plugins_finance.py:170-172)):
        *   Configures basic logging to INFO level.
        *   Calls [`finance_plugins()`](../../../iris/iris_plugins_finance.py:158).
        *   Prints the returned signals as a JSON string to the console, indented for readability.

## 10. Naming Conventions

*   **Functions:** Adhere to PEP 8 `snake_case` (e.g., [`_safe_get()`](../../../iris/iris_plugins_finance.py:46), [`finance_plugins()`](../../../iris/iris_plugins_finance.py:158)). Internal/helper functions are prefixed with a single underscore.
*   **Variables:**
    *   Local variables use `snake_case` (e.g., `var_name`, `latest_date`, `signals`).
    *   Module-level constants (API keys, URLs, symbol lists, retry parameters) use `_UPPER_SNAKE_CASE` with a leading underscore (e.g., `_ALPHA_KEY`, `_FINNHUB_URL`, `_MAX_RETRIES`). This convention typically denotes internal module constants.
*   **Output Dictionary Keys:** The keys in the dictionaries returned by the plugins (`name`, `value`, `source`, `timestamp`) are `snake_case`, as specified in the module docstring ([`iris/iris_plugins_finance.py:4-8`](../../../iris/iris_plugins_finance.py:4-8)).
*   **Consistency:** Naming conventions are applied consistently throughout the module.
*   **Potential AI Assumption Errors/Deviations:** No obvious errors or deviations from standard Python (PEP 8) or project-specific conventions are apparent. The generated signal names (e.g., `spx_close`, `aapl_news_sentiment`) are descriptive and follow a consistent pattern based on the hardcoded inputs.
