# Module Analysis: `iris/iris_plugins_variable_ingestion/gdelt_plugin.py`

## 1. Module Intent/Purpose

The primary role of the [`gdelt_plugin.py`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:0) module is to connect to the GDELT (Global Database of Events, Language, and Tone) v2 REST API. It is designed to track global geopolitical events and media narratives, transforming this data into signals that provide insights into global conflicts, cooperation, political stability, and media attention across various predefined regions and thematic categories.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational. Key functionalities include:
*   Fetching data from two GDELT API endpoints: Events API ([`EVENT_API_BASE_URL`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:40)) and GKG (Global Knowledge Graph) API ([`GKG_API_BASE_URL`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:41)).
*   Processing the retrieved data into structured signals.
*   Implementation of error handling, request retries ([`MAX_RETRIES`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:44)), and timeout management ([`REQUEST_TIMEOUT`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:42)).
*   Persistence of request metadata, raw API responses, and processed data using utilities from [`iris.iris_utils.ingestion_persistence`](iris/iris_utils/ingestion_persistence.py:0).
*   A basic daily rotation mechanism ([`_get_rotation_region()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:120), [`_get_rotation_theme()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:126)) to distribute API load across different regions and themes.
The module does not contain obvious placeholders like `TODO` comments or `pass` statements in critical logic sections, suggesting a finished state for its current scope.

## 3. Implementation Gaps / Unfinished Next Steps

While functional, several areas could be expanded or refined:
*   **Sophisticated Query Strategy:** The current daily rotation for API queries is simplistic. A more advanced strategy could prioritize volatile regions/themes or adjust dynamically based on observed activity levels.
*   **Deeper GKG Analysis:** Processing of GKG data could be extended beyond themes and overall tone to include analysis of relationships between entities, specific named locations (more granular than country codes), or sentiment towards particular actors/organizations.
*   **Event Detail Granularity:** The `maxrows` parameter is fixed at 250 ([`_fetch_events_data()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:196), [`_fetch_gkg_data()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:240)). In high-activity scenarios, this might lead to missed data. Implementing pagination or more targeted querying could address this.
*   **Actor Analysis:** The module tracks unique actor codes but does not perform deeper analysis on actor types, their relationships, or potential influence.
*   **Configuration Flexibility:** Regions ([`REGIONS`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:47)), event types ([`EVENT_TYPES`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:58)), and themes ([`THEMES`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:68)) are hardcoded. Allowing dynamic configuration or user-defined queries would enhance flexibility.
*   **Historical Data Ingestion:** The plugin is configured to fetch data for the last 24 hours ([`timespan: "24h"`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:197)). There is no built-in mechanism for fetching or backfilling historical GDELT data, which could be a valuable extension for broader trend analysis.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`IrisPluginManager`](iris/iris_plugins.py:0) from [`iris.iris_plugins`](iris/iris_plugins.py:0)
*   [`ensure_data_directory`](iris/iris_utils/ingestion_persistence.py:22), [`save_request_metadata`](iris/iris_utils/ingestion_persistence.py:23), [`save_api_response`](iris/iris_utils/ingestion_persistence.py:24), [`save_processed_data`](iris/iris_utils/ingestion_persistence.py:25) from [`iris.iris_utils.ingestion_persistence`](iris/iris_utils/ingestion_persistence.py:0)

### External Library Dependencies:
*   `datetime` (as `dt`)
*   `logging`
*   `time`
*   `typing` (Dict, List, Any, Optional, Tuple, Set, Union)
*   `urllib.parse` (specifically `urlencode`)
*   `re`
*   `random` (imported but not explicitly used in the provided code)
*   `collections` (Counter, defaultdict)
*   `requests`
*   `json` (imported locally within methods like [`_fetch_events_data()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:176))

### Interactions via Shared Data:
*   The module uses functions from [`ingestion_persistence`](iris/iris_utils/ingestion_persistence.py:0) to save data under the source name `_SOURCE_NAME = "gdelt"` ([iris/iris_plugins_variable_ingestion/gdelt_plugin.py:32](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:32)). This implies that other modules within the Iris system might consume this persisted data.

### Input/Output Files:
*   **Output:** The module outputs data by saving:
    *   Request metadata.
    *   Raw API responses (truncated to the first 10,000 characters).
    *   Processed signals.
    These are saved to file paths determined by the [`ensure_data_directory()`](iris/iris_utils/ingestion_persistence.py:22) function and dynamic `dataset_id` values generated within the persistence utilities.
*   **Logs:** The module utilizes the standard Python `logging` module for logging information, warnings, and errors.

## 5. Function and Class Example Usages

*   **`GdeltPlugin` Class ([`GdeltPlugin`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:34)):**
    *   This class is intended to be instantiated and managed by a plugin framework (likely the one that uses [`IrisPluginManager`](iris/iris_plugins.py:0)).
    *   The primary method for interaction is [`fetch_signals()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:82).
    ```python
    # Conceptual usage within a plugin management system:
    # from iris.iris_plugins_variable_ingestion.gdelt_plugin import GdeltPlugin
    #
    # gdelt_plugin_instance = GdeltPlugin()
    # signals = gdelt_plugin_instance.fetch_signals()
    #
    # for signal in signals:
    #     print(f"Signal: {signal['name']}, Value: {signal['value']}")
    ```

*   **[`fetch_signals()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:82) Method:**
    *   This method orchestrates the entire data fetching and processing pipeline for the plugin. It calls internal methods to get data from GDELT's Events and GKG APIs and then processes these into a list of signal dictionaries.

*   **[`_safe_get()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:132) Method:**
    *   A utility function for making HTTP GET requests to the GDELT API. It incorporates retry logic, timeout handling, and saves request/response metadata via persistence utilities.
    ```python
    # Conceptual internal usage:
    # params = {"query": "some_query", "format": "json"}
    # dataset_id = "my_custom_dataset"
    # response_text = self._safe_get(self.EVENT_API_BASE_URL, params, dataset_id)
    # if response_text:
    #     # Process response
    #     pass
    ```

## 6. Hardcoding Issues

The module contains several hardcoded values, common for API client configurations but important to note:
*   **API Endpoints:**
    *   [`EVENT_API_BASE_URL = "https://api.gdeltproject.org/api/v2/events/events"`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:40)
    *   [`GKG_API_BASE_URL = "https://api.gdeltproject.org/api/v2/gkg/gkg"`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:41)
*   **Request Parameters & Limits:**
    *   [`REQUEST_TIMEOUT = 30.0`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:42)
    *   [`RETRY_WAIT = 2.0`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:43)
    *   [`MAX_RETRIES = 3`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:44)
    *   `maxrows: 250` (for Events API at line [`196`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:196) and GKG API at line [`240`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:240))
    *   `timespan: "24h"` (for Events API at line [`197`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:197) and GKG API at line [`241`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:241))
    *   `format: "json"` used in API requests.
*   **Data Definitions:**
    *   [`REGIONS`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:47): Dictionary mapping region keys to CAMEO country codes.
    *   [`EVENT_TYPES`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:58): Dictionary mapping event type keys to lists/ranges of CAMEO event codes.
    *   [`THEMES`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:68): Dictionary mapping theme keys to lists of GKG theme prefixes.
*   **Plugin Configuration:**
    *   [`_SOURCE_NAME = "gdelt"`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:32)
    *   [`plugin_name = "gdelt_plugin"`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:35)
    *   [`enabled = True`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:36)
    *   [`concurrency = 2`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:37)
*   **Magic Numbers/Strings:**
    *   Response truncation: `resp.text[:10000]` ([`_safe_get()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:160)).
    *   Default event code: `event.get("EventCode", "0")` ([`_process_events_data()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:294)).
    *   String splitting indices for parsing GDELT fields:
        *   `tone_parts[0]` for V2Tone ([`_process_gkg_data()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:430)).
        *   `parts[2]` for V2Locations country code ([`_process_gkg_data()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:441)).
    *   Various string literals used in signal metadata (e.g., `"scale": "goldstein"`, `"interpretation": "higher=more positive tone"`).

## 7. Coupling Points

*   **GDELT API:** The module is tightly coupled to the GDELT v2 API's structure, query parameters, and response formats for both its Events and GKG services. Any significant changes to the GDELT API would likely require modifications to this plugin.
*   **Iris Plugin Framework:** Dependency on [`iris.iris_plugins.IrisPluginManager`](iris/iris_plugins.py:0) for its base class and integration into the broader Iris plugin system.
*   **Iris Persistence Utilities:** Relies on the interface and behavior of functions within [`iris.iris_utils.ingestion_persistence`](iris/iris_utils/ingestion_persistence.py:0) for data storage.
*   **Signal Structure:** The format of the generated signals (dictionaries with `name`, `value`, `source`, `timestamp`, `metadata` keys) forms a contract with any downstream modules or systems that consume these signals.

## 8. Existing Tests

*   A specific test file for this module (e.g., `tests/test_gdelt_plugin.py` or `tests/plugins/test_gdelt_plugin.py`) was not identified in the provided file listing.
*   While a generic [`tests/test_plugins.py`](tests/test_plugins.py:0) exists, it is unlikely to contain specific unit or integration tests for the GDELT plugin's unique logic (API interaction, data processing).
*   **Conclusion:** There appears to be a lack of dedicated tests for the `gdelt_plugin.py` module.

## 9. Module Architecture and Flow

The module follows a clear, sequential flow for fetching and processing data:
1.  **Initialization (`__init__`)**:
    *   Ensures the data directory for the `_SOURCE_NAME` ("gdelt") exists using [`ensure_data_directory()`](iris/iris_utils/ingestion_persistence.py:22).
2.  **Signal Fetching (`fetch_signals`)**: This is the main entry point.
    *   Determines the current region and theme for API calls using a daily rotation mechanism ([`_get_rotation_region()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:120), [`_get_rotation_theme()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:126)).
    *   Calls [`_fetch_events_data()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:176) to get data from the GDELT Events API for the selected region.
    *   If event data is successfully fetched, it calls [`_process_events_data()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:268) to transform this data into event-based signals.
    *   Calls [`_fetch_gkg_data()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:224) to get data from the GDELT GKG API for the selected theme.
    *   If GKG data is successfully fetched, it calls [`_process_gkg_data()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:398) to transform this data into GKG-based signals.
    *   Returns a combined list of all generated signals.
3.  **Data Fetching (Internal Methods: `_fetch_events_data`, `_fetch_gkg_data`)**:
    *   Construct appropriate query parameters, including filters for location/theme, `maxrows`, and `timespan`.
    *   Utilize the [`_safe_get()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:132) method to execute the API request.
    *   Parse the JSON response from GDELT.
4.  **Safe API Request (`_safe_get`)**:
    *   Saves request metadata using [`save_request_metadata()`](iris/iris_utils/ingestion_persistence.py:23).
    *   Performs the HTTP GET request with configured timeout and retry logic.
    *   Upon a successful response, saves the (truncated) API response using [`save_api_response()`](iris/iris_utils/ingestion_persistence.py:24).
    *   Includes error handling and logging for failed requests.
5.  **Data Processing (Internal Methods: `_process_events_data`, `_process_gkg_data`)**:
    *   Iterate through the records received from the API.
    *   Extract relevant fields (e.g., event codes, Goldstein scale, actor codes from events data; tone, locations, themes from GKG data).
    *   Aggregate data as needed (e.g., counting events by type, calculating average tone).
    *   Construct signal dictionaries with a standardized structure (`name`, `value`, `source`, `timestamp`, `metadata`).
    *   Save each processed signal using [`save_processed_data()`](iris/iris_utils/ingestion_persistence.py:25).

## 10. Naming Conventions

*   **Class Name:** `GdeltPlugin` follows PascalCase, which is standard for Python classes.
*   **Method Names:**
    *   Public methods like [`fetch_signals()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:82) use snake_case.
    *   Internal/protected methods such as [`_get_rotation_region()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:120), [`_safe_get()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:132), etc., use snake_case prefixed with a single underscore, correctly indicating their intended internal use.
*   **Variable Names:** Generally follow snake_case (e.g., `region_key`, `event_counts`, `iso_timestamp`), enhancing readability.
*   **Constants:** Defined in UPPER_SNAKE_CASE (e.g., [`EVENT_API_BASE_URL`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:40), [`REGIONS`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:47), [`_SOURCE_NAME`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:32)), which is the correct PEP 8 convention.
*   **Consistency:** Naming is largely consistent and adheres to PEP 8 guidelines.
*   **Potential AI Assumption Errors or Deviations:**
    *   The local import of `json` within [`_fetch_events_data()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:211) and [`_fetch_gkg_data()`](iris/iris_plugins_variable_ingestion/gdelt_plugin.py:255) is slightly unconventional. Typically, all imports are grouped at the top of the module. This is a style choice rather than an error.
    *   The `random` module is imported at the beginning of the file but does not appear to be used in the subsequent code. This might be a remnant from previous development or intended for future functionality.
