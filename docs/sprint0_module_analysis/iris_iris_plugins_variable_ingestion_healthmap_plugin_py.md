# Module Analysis: `iris/iris_plugins_variable_ingestion/healthmap_plugin.py`

## 1. Module Intent/Purpose

The primary role of the [`healthmap_plugin.py`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py) module is to connect to HealthMap RSS feeds to track global disease outbreaks and health events. It aggregates reports from various sources, providing real-time monitoring of emerging public health threats. The plugin aims to collect data on global disease outbreak counts, regional health event activity, top disease trends, and health alert levels by country/region. It does not require an API key, as it uses publicly available RSS feeds.

## 2. Operational Status/Completeness

The module appears to be operationally complete for its defined scope of fetching data from HealthMap RSS feeds, parsing the XML, and transforming the data into signals. It includes error handling, request retries, and data persistence. There are no explicit "TODO" comments or obvious placeholders indicating unfinished core functionality.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Feed Rotation Logic:** The current feed rotation mechanism ([`_get_rotation_region()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:111)) is based on the day of the month. This could be made more sophisticated, perhaps by tracking last-queried times or distributing requests more evenly if the number of feeds changes.
*   **Data Extraction:**
    *   Location extraction ([`_extract_location()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:220)) relies on splitting the title string. This might be fragile if title formats change or vary significantly.
    *   Category extraction ([`_extract_category()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:227)) uses simple keyword matching against a predefined list and some common terms. This could be enhanced using more advanced NLP techniques for better accuracy and coverage of unknown or new disease categories.
*   **Signal Granularity:** While it generates signals for total events, top categories, average alert levels, and specific countries, more granular or derived signals could be developed (e.g., rate of change of events, specific outbreak alerts).
*   **Configuration Management:** Many parameters like `FEEDS`, `CATEGORIES`, `REGION_COUNTRIES`, and `ALERT_LEVEL_MAP` are hardcoded. These could be moved to a configuration file for easier updates and maintenance.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`ingestion.iris_plugins.IrisPluginManager`](iris/iris_plugins.py) (as base class)
*   Functions from [`ingestion.iris_utils.ingestion_persistence`](iris/iris_utils/ingestion_persistence.py):
    *   [`ensure_data_directory()`](iris/iris_utils/ingestion_persistence.py)
    *   [`save_request_metadata()`](iris/iris_utils/ingestion_persistence.py)
    *   [`save_api_response()`](iris/iris_utils/ingestion_persistence.py)
    *   [`save_processed_data()`](iris/iris_utils/ingestion_persistence.py)

### External Library Dependencies:
*   [`datetime`](https://docs.python.org/3/library/datetime.html) (as `dt`)
*   [`logging`](https://docs.python.org/3/library/logging.html)
*   [`time`](https://docs.python.org/3/library/time.html)
*   `typing` ([`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict), [`List`](https://docs.python.org/3/library/typing.html#typing.List), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any), [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional), [`Counter`](https://docs.python.org/3/library/typing.html#typing.Counter) as `CounterType`)
*   [`collections.Counter`](https://docs.python.org/3/library/collections.html#collections.Counter)
*   [`re`](https://docs.python.org/3/library/re.html)
*   [`xml.etree.ElementTree`](https://docs.python.org/3/library/xml.etree.elementtree.html) (as `ET`)
*   [`urllib.parse.urlparse`](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse), [`urllib.parse.parse_qs`](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.parse_qs)
*   [`requests`](https://requests.readthedocs.io/en/latest/)

### Interaction with Other Modules via Shared Data:
*   The module writes data (request metadata, API responses, processed signals) to disk using the `ingestion_persistence` utilities. This data is stored in a directory structure based on the `_SOURCE_NAME` ("healthmap"), making it potentially accessible to other modules that might read from this data store.

### Input/Output Files:
*   **Input:**
    *   HealthMap RSS feeds (XML data fetched via HTTP GET requests from `https://www.healthmap.org/rss/...`).
*   **Output:**
    *   Log files (via the standard `logging` module).
    *   Persisted data files created by `ingestion_persistence` utilities, likely stored under a `data/healthmap/` directory (structure defined by `ingestion_persistence`):
        *   Request metadata files.
        *   API response files (truncated).
        *   Processed signal data files.

## 5. Function and Class Example Usages

*   **[`HealthmapPlugin`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:39) class:**
    *   This class is intended to be instantiated and managed by the Iris plugin framework.
    *   Its primary public method is [`fetch_signals()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:88).
    ```python
    # Conceptual usage by a plugin manager
    # healthmap_plugin_instance = HealthmapPlugin()
    # signals = healthmap_plugin_instance.fetch_signals()
    # for signal in signals:
    #     print(signal)
    ```

*   **[`fetch_signals()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:88):**
    *   Orchestrates the data collection process. It selects a region based on daily rotation, fetches events from the corresponding RSS feed, and processes these events into a list of signal dictionaries.
    ```python
    # Called internally or by the plugin manager
    # signals: List[Dict[str, Any]] = self.fetch_signals()
    ```

*   **[`_safe_get(url: str, dataset_id: str)`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:121):**
    *   An internal helper method to perform HTTP GET requests with error handling, retries, and persistence of request/response metadata.
    ```python
    # response_text = self._safe_get("https://example.com/data.xml", "example_dataset")
    ```

*   **[`_fetch_health_events(feed_url: str, region_key: str)`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:159):**
    *   Fetches raw data from a given HealthMap RSS feed URL, parses the XML, and extracts relevant fields for each event.
    ```python
    # events: Optional[List[Dict[str, Any]]] = self._fetch_health_events(
    #     "https://www.healthmap.org/rss/healthmap.php", "global"
    # )
    ```

*   **[`_process_health_events(events: List[Dict[str, Any]], region_key: str, timestamp: dt.datetime)`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:260):**
    *   Takes a list of parsed health events and transforms them into structured signal dictionaries, including counts, averages, and metadata.
    ```python
    # now = dt.datetime.now(dt.timezone.utc)
    # processed_signals: List[Dict[str, Any]] = self._process_health_events(
    #     parsed_events, "global", now
    # )
    ```

## 6. Hardcoding Issues

The module contains several hardcoded values:

*   **Source Name:** [`_SOURCE_NAME = "healthmap"`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:37) (used for data persistence paths).
*   **API Configuration:**
    *   [`BASE_URL = "https://www.healthmap.org/rss"`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:45)
    *   [`REQUEST_TIMEOUT = 15.0`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:46)
    *   [`RETRY_WAIT = 1.0`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:47)
    *   [`MAX_RETRIES = 2`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:48)
*   **Feed Definitions:**
    *   [`FEEDS`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:51): Dictionary of RSS feed paths for different regions.
*   **Data Categories & Mappings:**
    *   [`CATEGORIES`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:61): Predefined list of disease categories to track.
    *   [`REGION_COUNTRIES`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:67): Mapping of regions to lists of countries.
    *   [`ALERT_LEVEL_MAP`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:76): Mapping of HealthMap color codes (from URL parameters) to numerical alert levels.
*   **Extraction Logic Defaults:**
    *   Default location "Unknown" in [`_extract_location()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:220) if parsing fails.
    *   Default category "Unknown" in [`_extract_category()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:227) if no match.
    *   Keywords like "covid", "coronavirus", "flu" for category extraction are hardcoded in [`_extract_category()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:237-240).
    *   Default alert level `0` (Information only) in [`_extract_alert_level()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:244) if color code is not found or parsing fails.
*   **Signal Generation:**
    *   Signal name prefixes (e.g., `"healthmap_"`).
    *   Metadata interpretation strings (e.g., `"higher=more health events reported"`).
    *   Limiting category signals to the top 5 most common: `category_counts.most_common(5)` ([`_process_health_events()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:313)).
*   **Data Saving:**
    *   Truncation of API response text to the first 10,000 characters: `resp.text[:10000]` ([`_safe_get()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:143)).
    *   Default `dataset_id` of `"unknown"` in [`_safe_get()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:121) if not provided.

## 7. Coupling Points

*   **HealthMap RSS Feed Structure:** The plugin is tightly coupled to the specific XML structure of HealthMap's RSS feeds and the way alert levels are encoded in URL parameters (e.g., `?c=red`). Changes to the feed format or URL parameter scheme by HealthMap would likely break the plugin.
*   **`IrisPluginManager`:** Dependency on the [`IrisPluginManager`](iris/iris_plugins.py) class for its inheritance and expected plugin interface.
*   **`ingestion_persistence` Utilities:** Relies on the functions provided by [`ingestion.iris_utils.ingestion_persistence`](iris/iris_utils/ingestion_persistence.py) for saving data. Changes to this utility's API or behavior could affect the plugin.
*   **Network Availability:** Dependent on network access to `healthmap.org`.

## 8. Existing Tests

Based on the provided file list, there is no specific test file named `test_healthmap_plugin.py`. There is a generic [`tests/test_plugins.py`](tests/test_plugins.py), but its coverage of this specific HealthMap plugin is unknown without inspecting its contents.
It is recommended to have dedicated unit and integration tests for this plugin, covering:
*   RSS feed parsing with various valid and invalid inputs.
*   Location, category, and alert level extraction logic.
*   Signal generation logic.
*   Interaction with `_safe_get` and data persistence (possibly using mocks).
*   Feed rotation logic.

## 9. Module Architecture and Flow

The plugin operates as follows:

1.  **Initialization (`__init__`)**:
    *   Ensures the necessary data directory for storing "healthmap" source data exists, using [`ensure_data_directory()`](iris/iris_utils/ingestion_persistence.py).

2.  **Signal Fetching (`fetch_signals`)**:
    *   Determines the current UTC timestamp.
    *   Selects a HealthMap RSS feed URL to query based on a daily rotation scheme ([`_get_rotation_region()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:111), [`_get_feed_url()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:117)).
    *   Calls [`_fetch_health_events()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:159) to get data from the selected feed.
        *   **`_fetch_health_events`**:
            *   Uses [`_safe_get()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:121) to make the HTTP request.
                *   **`_safe_get`**: Saves request metadata, performs the GET request with timeout and retries, saves the (truncated) API response, and returns the response text.
            *   If the request is successful, parses the XML response text using `xml.etree.ElementTree`.
            *   Iterates through each `<item>` in the RSS feed.
            *   For each item, extracts:
                *   `title`, `description`, `link`, `pubDate`.
                *   Location using [`_extract_location()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:220).
                *   Category using [`_extract_category()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:227).
                *   Alert level using [`_extract_alert_level()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:244) (parses URL parameters from the item's link).
            *   Returns a list of dictionaries, each representing a parsed health event.
    *   If events are successfully fetched, calls [`_process_health_events()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:260) to transform them into signals.
        *   **`_process_health_events`**:
            *   Counts events by category and location using `collections.Counter`.
            *   Calculates the average alert level from all events.
            *   Constructs several types of signal dictionaries:
                1.  Total event count for the region.
                2.  Event counts for the top 5 disease categories.
                3.  Average alert level for the region.
                4.  Event counts for specific countries within the queried region (if defined in `REGION_COUNTRIES`).
            *   For each generated signal, it calls [`save_processed_data()`](iris/iris_utils/ingestion_persistence.py) to persist the signal.
            *   Appends each signal to a list.
    *   Returns the list of generated signal dictionaries.

## 10. Naming Conventions

*   **Class Name:** `HealthmapPlugin` follows PascalCase, which is standard for Python classes.
*   **Method Names:** Public methods like [`fetch_signals()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:88) use snake_case. Internal helper methods are correctly prefixed with a single underscore (e.g., [`_safe_get()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:121), [`_extract_location()`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:220)).
*   **Constants:** Module-level and class-level constants like `_SOURCE_NAME`, `BASE_URL`, `FEEDS`, `CATEGORIES`, `REGION_COUNTRIES`, `ALERT_LEVEL_MAP` are in UPPER_SNAKE_CASE.
*   **Variables:** Local variables (e.g., `region_key`, `feed_url`, `response_text`, `category_counts`) use snake_case.
*   **Plugin Name Attribute:** [`plugin_name = "healthmap_plugin"`](iris/iris_plugins_variable_ingestion/healthmap_plugin.py:40) is descriptive.
*   **Signal Naming:** Signal names are constructed programmatically (e.g., `f"healthmap_{region_key}_events_total"`) and follow a consistent pattern.
*   **Overall:** The naming conventions are consistent and largely adhere to PEP 8 guidelines. No significant AI assumption errors or deviations were noted.
