# Module Analysis: `iris/iris_plugins_variable_ingestion/google_trends_plugin.py`

## 1. Module Intent/Purpose

The primary role of the [`google_trends_plugin.py`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:1) module is to connect to the Google Trends API using the `pytrends` library. It aims to monitor search interest across various predefined topics and geographic regions, transforming this data into signals for the Iris system. It does not require an API key but relies on the unofficial `pytrends` wrapper.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope.
- It checks for the availability of the `pytrends` library and disables itself if not found ([`PYTRENDS_AVAILABLE`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:23), [`enabled`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:35)).
- It implements fetching mechanisms for interest over time, related topics, and interest by region.
- Data persistence for requests, API responses, and processed signals is handled via utilities from [`iris.iris_utils.ingestion_persistence`](iris/iris_utils/ingestion_persistence.py).
- Basic error handling (try-except blocks) and logging are implemented.
- There are no explicit "TODO" comments or obvious major placeholders.

## 3. Implementation Gaps / Unfinished Next Steps

- **Keyword/Region Rotation:** The current mechanism for rotating through `TOPIC_CATEGORIES` and `GEO_REGIONS` uses `now.day % len(...)` ([`fetch_signals`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:107), [`fetch_signals`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:112)). This is a simple daily rotation. A more configurable or sophisticated scheduling/prioritization system could be beneficial.
- **Keyword Coverage:**
    - For "interest over time," only the first 5 keywords from a selected category are processed due to API limits ([`fetch_signals`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:118)). Categories with more keywords will not have all keywords tracked in a single execution.
    - For "related topics" and "interest by region," data is fetched only for the *first* keyword in the selected category's list ([`fetch_signals`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:126), [`fetch_signals`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:134)). Expanding this to cover more (or all) keywords in a category could provide richer data.
- **Regional Data Resolution:** The `_get_interest_by_region` method uses `resolution='COUNTRY'` for both global and specific country requests ([`_get_interest_by_region`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:323-328)). This might be intentional, but if `pytrends` supports finer resolutions (e.g., 'CITY', 'REGION' within a country), this could be an area for enhancement.
- **Variance Calculation:** The manual variance calculation in [`_get_interest_by_region`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:373-386) with a comment about avoiding complex number issues suggests potential past instability with pandas' default methods. This could be revisited for robustness or clarity.

## 4. Connections & Dependencies

-   **Direct Project Imports:**
    *   `from iris.iris_plugins import IrisPluginManager` ([`IrisPluginManager`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:13))
    *   `from iris.iris_utils.ingestion_persistence import ensure_data_directory, save_request_metadata, save_api_response, save_processed_data` ([`ensure_data_directory`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:14), [`save_request_metadata`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:14), [`save_api_response`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:14), [`save_processed_data`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:14))
-   **External Library Dependencies:**
    *   `datetime` (as `dt`) ([`dt`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:7))
    *   `logging` ([`logging`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:8))
    *   `time` ([`time`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:9))
    *   `typing` (Dict, List, Any, Optional) ([`Dict`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:10))
    *   `requests` (imported, likely used by `pytrends`) ([`requests`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:12))
    *   `pytrends.request.TrendReq` (conditionally imported, core dependency) ([`TrendReq`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:22))
-   **Shared Data Interaction:**
    *   Persists data using functions from [`iris.iris_utils.ingestion_persistence`](iris/iris_utils/ingestion_persistence.py), identified by `_SOURCE_NAME = "google_trends"` ([`_SOURCE_NAME`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:31)). This data is likely consumed by other parts of the Iris system.
-   **Input/Output Files:**
    *   **Outputs:**
        *   Request metadata files.
        *   Raw API response files.
        *   Processed signal data files.
        *   (All managed by [`ingestion_persistence`](iris/iris_utils/ingestion_persistence.py) within a directory structure related to `_SOURCE_NAME`).
    *   **Logs:** Standard Python `logging` output.

## 5. Function and Class Example Usages

-   **`GoogleTrendsPlugin` Class:**
    *   This class is designed to be instantiated and managed by the Iris plugin framework. Its [`fetch_signals()`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:98) method is the main entry point for data collection.
    ```python
    # Conceptual usage within the Iris system:
    # if GoogleTrendsPlugin.enabled:
    #     plugin_instance = GoogleTrendsPlugin()
    #     signals_data = plugin_instance.fetch_signals()
    #     # Further processing of signals_data
    ```

-   **Internal Data Fetching Methods:**
    *   [`_get_interest_over_time(keywords, category, region_name, region_code)`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:140):
        ```python
        # Example: self._get_interest_over_time(
        #     keywords=["inflation", "recession"],
        #     category="finance",
        #     region_name="us",
        #     region_code="US"
        # )
        ```
    *   [`_get_related_topics(keyword, category, region_name, region_code)`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:217):
        ```python
        # Example: self._get_related_topics(
        #     keyword="artificial intelligence",
        #     category="technology",
        #     region_name="global",
        #     region_code=""
        # )
        ```
    *   [`_get_interest_by_region(keyword, category, region_name, region_code)`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:296):
        ```python
        # Example: self._get_interest_by_region(
        #     keyword="climate change",
        #     category="climate",
        #     region_name="eu",
        #     region_code="EU"
        # )
        ```

## 6. Hardcoding Issues

-   **Configuration Data:**
    *   `_SOURCE_NAME = "google_trends"` ([`_SOURCE_NAME`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:31)): Defines the source name for data persistence.
    *   `REQUEST_TIMEOUT = 30.0` ([`REQUEST_TIMEOUT`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:39)), `RETRY_WAIT = 5.0` ([`RETRY_WAIT`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:40)), `MAX_RETRIES = 3` ([`MAX_RETRIES`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:41)): API request parameters.
    *   `TOPIC_CATEGORIES` ([`TOPIC_CATEGORIES`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:44)): Predefined dictionary of topic categories and associated keywords.
    *   `GEO_REGIONS` ([`GEO_REGIONS`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:68)): Predefined dictionary of geographic regions and their codes.
    *   *Suggestion:* `TOPIC_CATEGORIES` and `GEO_REGIONS` could be externalized to a configuration file for easier modification without code changes.
-   **API Parameters:**
    *   Timeframe for `pytrends` requests is hardcoded to `"today 3-m"` (last 90 days) in all data fetching methods (e.g., [`_get_interest_over_time`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:147)).
    *   `cat=0` (all categories) is used in `pytrends.build_payload()` calls (e.g., [`_get_interest_over_time`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:164)).
    *   `TrendReq` initialization uses `hl='en-US'` (language) and `tz=0` (timezone) ([`__init__`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:92)).
    *   *Suggestion:* These API parameters could be made configurable.
-   **Operational Parameters:**
    *   `time.sleep(1.0)`: Fixed delay between certain API calls ([`fetch_signals`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:123), [`fetch_signals`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:131)).
-   **Signal Formatting:**
    *   Signal names are constructed with hardcoded prefixes like `"gtrends_"` (e.g., [`_get_interest_over_time`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:191)).
    *   Related topic titles are normalized and truncated to 20 characters: `normalized_topic = topic_title.replace(" ", "_").lower()[:20]` ([`_get_related_topics`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:267)).

## 7. Coupling Points

-   **`pytrends` Library:** The module is tightly coupled to the `pytrends` library. Any breaking changes in `pytrends` or its underlying access to Google Trends would directly impact this plugin.
-   **Iris Plugin System:** Relies on `iris.iris_plugins.IrisPluginManager` ([`IrisPluginManager`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:13)) as its base class.
-   **Iris Ingestion Persistence:** Depends on [`iris.iris_utils.ingestion_persistence`](iris/iris_utils/ingestion_persistence.py) for saving all data. Changes to this utility's interface or behavior could break the plugin.
-   **Signal Structure:** The format of the generated signal dictionaries (containing keys like "name", "value", "source", "timestamp", "metadata") forms a contract with downstream data consumers within the Iris system.

## 8. Existing Tests

-   A specific test file for this module (e.g., `test_google_trends_plugin.py`) was not immediately identifiable in the provided project structure.
-   There is a generic [`tests/test_plugins.py`](tests/test_plugins.py), which might provide some level of testing, but dedicated tests for the Google Trends plugin's specific logic, API interactions (possibly mocked), and data transformations appear to be a potential gap.

## 9. Module Architecture and Flow

1.  **Initialization (`__init__`)**:
    *   Sets up the data directory via [`ensure_data_directory()`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:15).
    *   Conditionally enables the plugin based on `pytrends` availability.
    *   Initializes a `pytrends.request.TrendReq` object ([`TrendReq`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:22)) for API communication.
2.  **Signal Fetching (`fetch_signals`)**:
    *   This is the main public method.
    *   Selects a topic category and geographic region based on a daily rotation.
    *   Limits keyword processing per category (currently up to 5 for interest over time, 1 for related/regional).
    *   Orchestrates calls to private methods:
        *   [`_get_interest_over_time()`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:140)
        *   [`_get_related_topics()`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:217)
        *   [`_get_interest_by_region()`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:296)
    *   Introduces delays (`time.sleep(1.0)`) between different types of API calls to mitigate rate-limiting.
    *   Collects and returns a list of signal dictionaries.
3.  **Private Data Fetching Methods** (e.g., [`_get_interest_over_time`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:140)):
    *   Each method is responsible for a specific type of Google Trends query.
    *   Constructs parameters for the `pytrends` API call.
    *   Persists request metadata using [`save_request_metadata()`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:16).
    *   Executes the query using the `self.pytrends` object.
    *   Persists the raw API response using [`save_api_response()`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:17).
    *   Transforms the `pytrends` response (typically a pandas DataFrame) into the plugin's standard signal dictionary format.
    *   Persists the processed signal data using [`save_processed_data()`](iris/iris_plugins_variable_ingestion/google_trends_plugin.py:18).
    *   Includes error handling and logs warnings on failure.

## 10. Naming Conventions

-   **Class:** `GoogleTrendsPlugin` (PascalCase) - Adheres to PEP 8.
-   **Constants:** `_SOURCE_NAME`, `REQUEST_TIMEOUT`, `TOPIC_CATEGORIES`, `GEO_REGIONS`, `PYTRENDS_AVAILABLE` (UPPER_SNAKE_CASE) - Adheres to PEP 8. The leading underscore in `_SOURCE_NAME` suggests internal use.
-   **Methods:** `fetch_signals`, `_get_interest_over_time` (snake_case) - Adheres to PEP 8. Leading underscores correctly denote protected/internal methods.
-   **Variables:** Generally snake_case (e.g., `category_idx`, `interest_over_time_df`, `normalized_keyword`).
-   **Generated Signal Names:** Constructed dynamically (e.g., `f"gtrends_{category}_{normalized_keyword}_{region_name}"`). They are descriptive and include normalization (lowercase, underscores).
-   **`dataset_id`:** Consistently formatted (e.g., `f"{category}_interest_time"`).
-   Overall, naming conventions are consistent and follow Python community standards (PEP 8). No significant deviations or potential AI assumption errors were noted.