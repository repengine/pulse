# Module Analysis: `iris/variable_ingestion.py`

## 1. Module Intent/Purpose

The primary role of the [`iris/variable_ingestion.py`](../../../iris/variable_ingestion.py) module is to fetch a small, curated set of real-world financial and economic variables. This provides the Pulse system with initial, meaningful data points with minimal setup requirements. It currently sources data from:

*   **FRED (Federal Reserve Economic Data):** US 10-year Treasury yield, Consumer Price Index (CPI YoY).
*   **Yahoo Finance:** S&P 500 closing price, VIX (Volatility Index) closing price.

The module is designed to be dependency-light and to fail silently for individual data points to ensure fast application boot times, even if external services are unavailable. It also mentions Google Trends as a potential (currently unimplemented) data source.

## 2. Operational Status/Completeness

The module appears operational and complete for its explicitly stated and implemented scope: fetching data from FRED and Yahoo Finance.

*   It successfully fetches the defined variables from these two sources.
*   Error handling is present, allowing the module to skip individual data points that fail to load, rather than halting the entire process.
*   The docstring mentions Google Trends via `pytrends` as an optional source ([`iris/variable_ingestion.py:7`](../../../iris/variable_ingestion.py:7)), but this functionality is not implemented in the current code.
*   There are no explicit `TODO` comments or obvious placeholders for the implemented FRED and Yahoo Finance integrations.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Google Trends Integration:** The most notable gap is the unimplemented Google Trends data fetching mentioned in the module's docstring ([`iris/variable_ingestion.py:7`](../../../iris/variable_ingestion.py:7)).
*   **Basic Error Handling:** The current error handling uses a broad `except Exception:` clause ([`iris/variable_ingestion.py:37`](../../../iris/variable_ingestion.py:37), [`iris/variable_ingestion.py:47`](../../../iris/variable_ingestion.py:47)). This could be refined to catch more specific exceptions and potentially log errors for better diagnostics, rather than just returning `None`.
*   **Limited Variable Set:** As per its design, the module ingests a very small set of variables. Future extensions could involve adding more variables from existing sources or integrating new data sources.
*   **Configuration of Variables:** The series IDs and tickers are hardcoded. A more flexible approach might involve configuration-driven variable selection.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`core.variable_registry`](../../../core/variable_registry.py): Specifically, the `registry` object is imported ([`iris/variable_ingestion.py:21`](../../../iris/variable_ingestion.py:21)) and used to bind the ingested data via [`registry.bind_external_ingestion()`](../../../iris/variable_ingestion.py:72).

### External Library Dependencies:
*   `yfinance`: Used for fetching market data from Yahoo Finance ([`iris/variable_ingestion.py:18`](../../../iris/variable_ingestion.py:18)).
*   `fredapi`: Used for fetching economic data from FRED ([`iris/variable_ingestion.py:19`](../../../iris/variable_ingestion.py:19)).
*   Standard Python libraries: `datetime`, `os`, `sys`.

### Interaction with Other Modules via Shared Data:
*   The primary interaction is with the `core.variable_registry` module. The [`ingest_live_variables()`](../../../iris/variable_ingestion.py:51) function registers a lambda that provides a copy of the fetched data to the registry.

### Input/Output:
*   **Input:**
    *   Requires the `FRED_KEY` environment variable to be set for accessing the FRED API ([`iris/variable_ingestion.py:26`](../../../iris/variable_ingestion.py:26)).
*   **Output:**
    *   Prints debug information about the Python executable and `sys.path` to standard output upon import ([`iris/variable_ingestion.py:23-24`](../../../iris/variable_ingestion.py:23-24)).
    *   The [`ingest_live_variables()`](../../../iris/variable_ingestion.py:51) function returns a dictionary of the fetched variable names and their float values.

## 5. Function and Class Example Usages

### [`ingest_live_variables() -> dict[str, float]`](../../../iris/variable_ingestion.py:51)
This is the main public function of the module. It orchestrates the fetching of all defined live variables from their respective sources.

**Presumed Usage:**
```python
from iris.variable_ingestion import ingest_live_variables

live_economic_data = ingest_live_variables()
if live_economic_data:
    print("Successfully ingested live variables:")
    for key, value in live_economic_data.items():
        print(f"  {key}: {value}")
else:
    print("No live variables were ingested.")

# Example output (if all sources are successful):
# Successfully ingested live variables:
#   us_10y_yield: 0.045
#   cpi_yoy: 300.2
#   spx_close: 5000.10
#   vix_close: 15.5
#   macro_heat: 0.007
```

### [`_fred_series(series_id: str) -> float | None`](../../../iris/variable_ingestion.py:31)
An internal helper function to fetch the latest value for a given `series_id` from FRED. It returns `None` if the `FRED_KEY` is not set or if any error occurs during fetching or processing.

### [`_yfinance_close(ticker: str) -> float | None`](../../../iris/variable_ingestion.py:41)
An internal helper function to fetch the latest closing price for a given `ticker` from Yahoo Finance for a 30-day window. It returns `None` if any error occurs.

## 6. Hardcoding Issues

The module contains several hardcoded values:

*   **FRED Series IDs:**
    *   `"DGS10"` (US 10-Year Treasury Constant Maturity Rate) ([`iris/variable_ingestion.py:56`](../../../iris/variable_ingestion.py:56))
    *   `"CPIAUCSL"` (Consumer Price Index for All Urban Consumers: All Items in U.S. City Average) ([`iris/variable_ingestion.py:58`](../../../iris/variable_ingestion.py:58))
*   **Yahoo Finance Tickers:**
    *   `"^GSPC"` (S&P 500) ([`iris/variable_ingestion.py:62`](../../../iris/variable_ingestion.py:62))
    *   `"^VIX"` (CBOE Volatility Index) ([`iris/variable_ingestion.py:64`](../../../iris/variable_ingestion.py:64))
*   **Output Variable Names (Dictionary Keys):**
    *   `"us_10y_yield"` ([`iris/variable_ingestion.py:57`](../../../iris/variable_ingestion.py:57))
    *   `"cpi_yoy"` ([`iris/variable_ingestion.py:59`](../../../iris/variable_ingestion.py:59))
    *   `"spx_close"` ([`iris/variable_ingestion.py:63`](../../../iris/variable_ingestion.py:63))
    *   `"vix_close"` ([`iris/variable_ingestion.py:65`](../../../iris/variable_ingestion.py:65))
    *   `"macro_heat"` (synthetic variable) ([`iris/variable_ingestion.py:69`](../../../iris/variable_ingestion.py:69))
*   **Date Range for Yahoo Finance:** Data is fetched for the last 30 days (`_30D_AGO`) ([`iris/variable_ingestion.py:28`](../../../iris/variable_ingestion.py:28), [`iris/variable_ingestion.py:43`](../../../iris/variable_ingestion.py:43)).
*   **Magic Numbers/Strings:**
    *   Division by `100` for `us_10y_yield` because FRED returns it as a percentage ([`iris/variable_ingestion.py:57`](../../../iris/variable_ingestion.py:57)).
    *   Divisor `1000` in the `macro_heat` calculation ([`iris/variable_ingestion.py:69`](../../../iris/variable_ingestion.py:69)).
    *   The string `"Close"` is used to access the closing price column from Yahoo Finance data ([`iris/variable_ingestion.py:44`](../../../iris/variable_ingestion.py:44), [`iris/variable_ingestion.py:46`](../../../iris/variable_ingestion.py:46)).
*   **Environment Variable Name:** `"FRED_KEY"` ([`iris/variable_ingestion.py:26`](../../../iris/variable_ingestion.py:26)).

## 7. Coupling Points

*   **External Libraries:** Tightly coupled to the specific APIs and data formats of the `fredapi` and `yfinance` libraries. Changes in these libraries could break the module.
*   **`core.variable_registry`:** Directly depends on the `registry` object and its [`bind_external_ingestion()`](../../../iris/variable_ingestion.py:72) method from [`core.variable_registry`](../../../core/variable_registry.py).
*   **Environment Variable:** Relies on the `FRED_KEY` environment variable being correctly set for FRED data access.
*   **Network Availability:** Dependent on network connectivity to FRED and Yahoo Finance servers.

## 8. Existing Tests

No dedicated test file, such as `tests/iris/test_variable_ingestion.py`, was found in the `tests/iris` directory. The `list_files` command for `tests/iris` returned "No files found." This indicates a lack of specific unit tests for this module in that location. Tests might exist elsewhere in the project or may need to be created.

## 9. Module Architecture and Flow

1.  **Initialization:**
    *   Upon import, the module attempts to initialize a `Fred` client object (`_FRED`) if the `FRED_KEY` environment variable is found ([`iris/variable_ingestion.py:26`](../../../iris/variable_ingestion.py:26)). If the key is not present, `_FRED` remains `None`.
    *   Current UTC time (`_NOW`) and a datetime 30 days ago (`_30D_AGO`) are established ([`iris/variable_ingestion.py:27-28`](../../../iris/variable_ingestion.py:27-28)).
    *   Debug information about the Python environment is printed ([`iris/variable_ingestion.py:23-24`](../../../iris/variable_ingestion.py:23-24)).

2.  **Helper Functions:**
    *   [`_fred_series(series_id)`](../../../iris/variable_ingestion.py:31):
        *   Checks if `_FRED` is initialized. If not, returns `None`.
        *   Attempts to fetch data for the given `series_id` using `_FRED.get_series()`.
        *   Extracts the last non-null value, converts it to `float`, and returns it.
        *   Returns `None` on any exception.
    *   [`_yfinance_close(ticker)`](../../../iris/variable_ingestion.py:41):
        *   Attempts to download data for the given `ticker` for the last 30 days using `yf.download()`.
        *   Checks if data was returned and if the "Close" column exists.
        *   Extracts the last non-null "Close" price, converts it to `float`, and returns it.
        *   Returns `None` on any exception.

3.  **Main Ingestion Logic ([`ingest_live_variables()`](../../../iris/variable_ingestion.py:51)):**
    *   Initializes an empty dictionary `out` to store results.
    *   **FRED Data:**
        *   Calls [`_fred_series()`](../../../iris/variable_ingestion.py:31) for "DGS10". If a value is returned, it's divided by 100 and stored as `"us_10y_yield"`.
        *   Calls [`_fred_series()`](../../../iris/variable_ingestion.py:31) for "CPIAUCSL". If a value is returned, it's stored as `"cpi_yoy"`.
    *   **Yahoo Finance Data:**
        *   Calls [`_yfinance_close()`](../../../iris/variable_ingestion.py:41) for "^GSPC". If a value is returned, it's stored as `"spx_close"`.
        *   Calls [`_yfinance_close()`](../../../iris/variable_ingestion.py:41) for "^VIX". If a value is returned, it's stored as `"vix_close"`.
    *   **Synthetic Variable:**
        *   If both `"us_10y_yield"` and `"vix_close"` are present in `out`, a `"macro_heat"` variable is calculated and added.
    *   **Registry Binding:**
        *   Calls [`registry.bind_external_ingestion()`](../../../iris/variable_ingestion.py:72) with a lambda function that returns a copy of the `out` dictionary. This makes the ingested data available to other parts of the system via the variable registry.
    *   Returns the `out` dictionary.

## 10. Naming Conventions

*   **Functions and Variables:** Generally adhere to PEP 8 standards, using `snake_case` (e.g., [`ingest_live_variables`](../../../iris/variable_ingestion.py:51), `us_10y_yield`).
*   **Internal Helpers:** Prefixed with a single underscore (e.g., [`_fred_series`](../../../iris/variable_ingestion.py:31), [`_yfinance_close`](../../../iris/variable_ingestion.py:41)), which is a common Python convention for internal use.
*   **Constants/Module-Level Globals:** Written in `UPPER_SNAKE_CASE` when intended as true constants (e.g., `_FRED`, `_NOW`, `_30D_AGO`). The leading underscore suggests they are primarily for module-internal use.
*   **Clarity:** Names are generally descriptive and understandable (e.g., `series_id`, `ticker`, `cpi_yoy`).
*   **AI Assumption Errors:** No obvious errors in naming conventions that would suggest misinterpretation by AI or significant deviations from Python standards were noted. The debug print statements ([`iris/variable_ingestion.py:23-24`](../../../iris/variable_ingestion.py:23-24)) are clearly marked `[DEBUG]`.