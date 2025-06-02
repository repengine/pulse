# Module Analysis: `iris/iris_utils/ingestion_persistence.py`

## 1. Module Intent/Purpose

The primary role of the [`iris/iris_utils/ingestion_persistence.py`](../../../iris/iris_utils/ingestion_persistence.py) module is to provide a standardized and reusable set of utilities for persisting data ingested from various API sources. It handles tasks such as creating directory structures, saving raw API responses, storing processed data, managing request metadata, and masking sensitive information within that metadata. This centralization aims to ensure consistency in how data is saved and organized across different ingestion plugins.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope. It provides core functionalities for:
*   Directory creation ([`ensure_data_directory`](../../../iris/iris_utils/ingestion_persistence.py:64)).
*   Saving data in JSON and CSV formats ([`save_to_file`](../../../iris/iris_utils/ingestion_persistence.py:88)).
*   Masking sensitive parameters ([`mask_sensitive_data`](../../../iris/iris_utils/ingestion_persistence.py:170)).
*   Saving request metadata ([`save_request_metadata`](../../../iris/iris_utils/ingestion_persistence.py:205)).
*   Saving raw API responses ([`save_api_response`](../../../iris/iris_utils/ingestion_persistence.py:256)).
*   Saving processed data ([`save_processed_data`](../../../iris/iris_utils/ingestion_persistence.py:314)).
*   Finding the latest saved file for a dataset ([`find_latest_file`](../../../iris/iris_utils/ingestion_persistence.py:360)).
*   Incrementally saving data points to JSONL files ([`save_data_point_incremental`](../../../iris/iris_utils/ingestion_persistence.py:410)).

There are no obvious TODOs or major placeholders within the implemented functions. The docstrings and comments are generally informative.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Error Handling and Resilience:** While the module creates directories and writes files, explicit error handling for I/O operations (e.g., disk full, permission errors) is minimal. More robust error handling and logging could be beneficial.
*   **Data Format Extensibility:** Currently, it primarily supports JSON and CSV. While there's a fallback to save unsupported formats as plain text ([`save_to_file`](../../../iris/iris_utils/ingestion_persistence.py:161-163)), a more structured way to add support for other formats (e.g., Parquet, XML) could be considered if needed.
*   **Configuration of Base Directory:** The `DEFAULT_BASE_DIR` is hardcoded as [`"data/api_ingestion"`](../../../iris/iris_utils/ingestion_persistence.py:55). While it can be overridden in function calls, a project-level configuration mechanism for this base path might be more flexible.
*   **Log File Management:** The module logs events but doesn't manage log files themselves (e.g., rotation, size limits). This is likely handled by the broader logging setup of the application.
*   **Atomic Writes:** For critical data, ensuring atomic write operations (e.g., writing to a temporary file then renaming) could prevent data corruption if a write is interrupted. This is not explicitly implemented.
*   **Asynchronous Operations:** For high-throughput ingestion, asynchronous file I/O could be a potential enhancement, though it would add complexity.

## 4. Connections & Dependencies

### Direct Project Imports
*   None explicitly listed beyond standard library imports. It's designed as a utility module.

### External Library Dependencies
*   [`datetime`](https://docs.python.org/3/library/datetime.html) (as `dt`): For timestamp generation and manipulation.
*   [`json`](https://docs.python.org/3/library/json.html): For saving and loading data in JSON format.
*   [`logging`](https://docs.python.org/3/library/logging.html): For application-level logging.
*   [`os`](https://docs.python.org/3/library/os.html): Used implicitly by `pathlib` for path operations.
*   [`pathlib`](https://docs.python.org/3/library/pathlib.html): For object-oriented filesystem path manipulation.
*   [`csv`](https://docs.python.org/3/library/csv.html): For saving data in CSV format.
*   `typing` ( [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict), [`List`](https://docs.python.org/3/library/typing.html#typing.List), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any), [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional), [`Union`](https://docs.python.org/3/library/typing.html#typing.Union), [`Tuple`](https://docs.python.org/3/library/typing.html#typing.Tuple), [`Set`](https://docs.python.org/3/library/typing.html#typing.Set) ): For type hinting.

### Interaction with Other Modules
*   This module is intended to be used by various API data ingestion plugins within the `iris` system. These plugins would call its functions to save data.
*   The function [`save_data_point_incremental`](../../../iris/iris_utils/ingestion_persistence.py:410) mentions it follows an approach used by `HighFrequencyDataStore.store_data_point()`, suggesting an interaction pattern or shared design philosophy with a high-frequency data storage component, though not a direct code dependency within this file.

### Input/Output Files
*   **Output:**
    *   Creates directories under a base path (default: [`data/api_ingestion/`](data/api_ingestion/)).
    *   Saves API request metadata as JSON files (e.g., `[dataset_id]_request_metadata_[timestamp].json`).
    *   Saves API responses and processed data as JSON or CSV files (e.g., `[dataset_id]/[dataset_id]_[timestamp].json`).
    *   Saves incremental data points as JSONL files (e.g., `[dataset_id]/[variable_name].jsonl`).
*   **Input:**
    *   The [`find_latest_file`](../../../iris/iris_utils/ingestion_persistence.py:360) function reads directory listings to find the most recent file for a dataset.

## 5. Function and Class Example Usages

The module docstring provides a clear usage example:

```python
from ingestion.iris_utils.ingestion_persistence import (
    ensure_data_directory,
    save_to_file,
    save_request_metadata,
    mask_sensitive_data
)

# Create data directory
data_dir = ensure_data_directory("my_api_source")

# Save API request metadata
metadata_file = save_request_metadata(
    "my_dataset", 
    {"api_key": "secret", "param1": "value1"}
)

# Save API response
response_file = save_to_file("my_dataset", response_data) # Assuming response_data is defined

# Save processed data
processed_file = save_to_file(
    "my_dataset_processed", 
    processed_data, # Assuming processed_data is defined
    timestamp="2025-01-01T12:00:00"
)
```

Key functions and their intended use:
*   [`ensure_data_directory(source_name, base_dir)`](../../../iris/iris_utils/ingestion_persistence.py:64): Call this first to create the necessary directory structure for a given API source.
*   [`save_to_file(dataset_id, data, source_name, ...)`](../../../iris/iris_utils/ingestion_persistence.py:88): Generic function to save data (raw responses, processed data) to a timestamped file in JSON or CSV format.
*   [`mask_sensitive_data(params, sensitive_params, mask_char)`](../../../iris/iris_utils/ingestion_persistence.py:170): Utility to hide sensitive values (like API keys) in a dictionary before saving or logging.
*   [`save_request_metadata(dataset_id, params, source_name, ...)`](../../../iris/iris_utils/ingestion_persistence.py:205): Saves request parameters (with sensitive data masked) and other metadata related to an API call.
*   [`save_api_response(dataset_id, response_data, source_name, ...)`](../../../iris/iris_utils/ingestion_persistence.py:256): Specifically for saving the raw API response, potentially including HTTP status codes and headers.
*   [`save_processed_data(dataset_id, processed_data, source_name, ...)`](../../../iris/iris_utils/ingestion_persistence.py:314): For saving data after it has undergone some transformation or processing.
*   [`find_latest_file(dataset_id, source_name, ...)`](../../../iris/iris_utils/ingestion_persistence.py:360): Useful for retrieving the most recently saved data file for a particular dataset, perhaps for incremental processing.
*   [`save_data_point_incremental(dataset_id, timestamp, value, ...)`](../../../iris/iris_utils/ingestion_persistence.py:410): Appends individual data points to a JSONL file, suitable for high-frequency data or streaming scenarios.

## 6. Hardcoding Issues

*   **`DEFAULT_BASE_DIR`**: The default base directory for storing all API ingestion data is hardcoded to [`"data/api_ingestion"`](../../../iris/iris_utils/ingestion_persistence.py:55). While this can be overridden per function call, a more centralized configuration might be preferable for project-wide changes.
*   **`DEFAULT_SENSITIVE_PARAMS`**: The set of parameter names considered sensitive for masking is hardcoded ([`DEFAULT_SENSITIVE_PARAMS`](../../../iris/iris_utils/ingestion_persistence.py:58-61)). This list is fairly comprehensive but might need additions or modifications depending on new API integrations.
*   **File Suffixes/Naming Conventions**:
    *   The suffix `"_request_metadata"` is appended when saving metadata ([`save_request_metadata`](../../../iris/iris_utils/ingestion_persistence.py:249)).
    *   The suffix `"_processed"` is appended when saving processed data ([`save_processed_data`](../../../iris/iris_utils/ingestion_persistence.py:339)).
    *   Timestamps are formatted as `"%Y%m%d_%H%M%S"` ([`save_to_file`](../../../iris/iris_utils/ingestion_persistence.py:120)).
    These are internal conventions but represent hardcoded string formatting.
*   **Masking Character**: The default masking character is `"*"` ([`mask_sensitive_data`](../../../iris/iris_utils/ingestion_persistence.py:173)).
*   **Masking Logic**: The logic to preserve the first and last character for values longer than 4 characters during masking ([`mask_sensitive_data`](../../../iris/iris_utils/ingestion_persistence.py:197-200)) contains the magic number `4`.
*   **CSV Fallback**: When writing CSVs, if data is not a list of dicts or a single dict, it falls back to `str(data)` ([`save_to_file`](../../../iris/iris_utils/ingestion_persistence.py:157-159)). This is a simple fallback.
*   **Default Source Name**: The `source_name` parameter in several functions defaults to `"default"` (e.g., [`save_to_file`](../../../iris/iris_utils/ingestion_persistence.py:91)). This implies a generic category if a specific source isn't provided.

## 7. Coupling Points

*   **Ingestion Plugins:** This module is tightly coupled with any API ingestion plugins that use it for data persistence. Changes to function signatures or behavior in this module would directly impact those plugins.
*   **File System Structure:** The module defines and relies on a specific directory structure (`base_dir/source_name/dataset_id/filename`). Any other part of the system that reads this data must adhere to this structure.
*   **Data Format:** Consumers of the data saved by this module are coupled to the chosen formats (JSON, CSV, JSONL).
*   **`HighFrequencyDataStore` (Conceptual):** The [`save_data_point_incremental`](../../../iris/iris_utils/ingestion_persistence.py:410) function's docstring mentions its design is similar to `HighFrequencyDataStore.store_data_point()`, indicating a conceptual coupling or shared design pattern with another (potentially unimported) component responsible for high-frequency data.

## 8. Existing Tests

*   A specific test file for `ingestion_persistence.py` was not found in the `tests/iris/iris_utils/` directory.
*   The `iris/iris_utils/` directory contains a [`conftest.py`](../../../iris/iris_utils/conftest.py:1) and a [`test_historical_data_pipeline.py`](../../../iris/iris_utils/test_historical_data_pipeline.py:1), but these do not appear to directly target the `ingestion_persistence.py` module's individual functions.
*   Given the module's role in file I/O and data structuring, unit tests would be crucial to ensure its reliability. These tests would ideally cover:
    *   Correct directory creation.
    *   File saving in all supported formats (JSON, CSV, JSONL).
    *   Correct timestamping and filename generation.
    *   Proper masking of sensitive data.
    *   Correct handling of various input data types for CSV conversion.
    *   Accurate retrieval of the latest file.
    *   Edge cases (e.g., empty data, invalid characters in dataset IDs).

The absence of dedicated tests is a significant gap.

## 9. Module Architecture and Flow

The module is procedural, consisting of a set of utility functions. There are no classes.

**Key Architectural Points:**
*   **Centralized Configuration (Defaults):** Uses module-level constants for `DEFAULT_BASE_DIR` and `DEFAULT_SENSITIVE_PARAMS`.
*   **Layered Structure for Saving:**
    1.  [`ensure_data_directory`](../../../iris/iris_utils/ingestion_persistence.py:64) creates the base and source-specific directories.
    2.  [`save_to_file`](../../../iris/iris_utils/ingestion_persistence.py:88) is a general-purpose saving function that handles dataset-specific subdirectories, timestamping, and format-specific writing (JSON, CSV).
    3.  Specialized functions like [`save_request_metadata`](../../../iris/iris_utils/ingestion_persistence.py:205), [`save_api_response`](../../../iris/iris_utils/ingestion_persistence.py:256), and [`save_processed_data`](../../../iris/iris_utils/ingestion_persistence.py:314) build upon [`save_to_file`](../../../iris/iris_utils/ingestion_persistence.py:88) by preparing the data (e.g., masking, adding metadata) and calling [`save_to_file`](../../../iris/iris_utils/ingestion_persistence.py:88) with specific dataset ID conventions.
*   **Incremental Saving:** The [`save_data_point_incremental`](../../../iris/iris_utils/ingestion_persistence.py:410) function provides a different persistence pattern, appending to JSONL files, suitable for streaming data.
*   **Data Retrieval:** [`find_latest_file`](../../../iris/iris_utils/ingestion_persistence.py:360) provides a basic mechanism to locate the most recent data.

**Primary Control Flow (Example: Saving an API Response):**
1.  An ingestion plugin calls [`save_api_response()`](../../../iris/iris_utils/ingestion_persistence.py:256).
2.  [`save_api_response()`](../../../iris/iris_utils/ingestion_persistence.py:256) may wrap the `response_data` with additional metadata (status code, headers).
3.  It then calls [`save_to_file()`](../../../iris/iris_utils/ingestion_persistence.py:88).
4.  [`save_to_file()`](../../../iris/iris_utils/ingestion_persistence.py:88) calls [`ensure_data_directory()`](../../../iris/iris_utils/ingestion_persistence.py:64) to make sure `base_dir/source_name/` exists.
5.  [`save_to_file()`](../../../iris/iris_utils/ingestion_persistence.py:88) creates `base_dir/source_name/safe_dataset_id/`.
6.  It generates a filename like `safe_dataset_id_YYYYMMDD_HHMMSS.json`.
7.  It writes the data to this file using either `json.dump()` or `csv.writer()`.
8.  The path to the saved file is returned up the call stack.

## 10. Naming Conventions

*   **Functions:** Use `snake_case` (e.g., [`ensure_data_directory`](../../../iris/iris_utils/ingestion_persistence.py:64), [`save_to_file`](../../../iris/iris_utils/ingestion_persistence.py:88)), which is consistent with PEP 8.
*   **Variables:** Generally use `snake_case` (e.g., `data_dir`, `safe_dataset_id`, `masked_params`).
*   **Constants:** Use `UPPER_SNAKE_CASE` (e.g., [`DEFAULT_BASE_DIR`](../../../iris/iris_utils/ingestion_persistence.py:55), [`DEFAULT_SENSITIVE_PARAMS`](../../../iris/iris_utils/ingestion_persistence.py:58)), also PEP 8 compliant.
*   **Parameters:** Use `snake_case`.
*   **Module Name:** `ingestion_persistence.py` is descriptive.
*   **Clarity:** Names are generally clear and indicate the purpose of functions and variables.
    *   `safe_dataset_id` clearly indicates that the dataset ID has been sanitized for use in file paths.
    *   `mask_sensitive_data` is self-explanatory.
*   **Potential AI Assumption Errors/Deviations:**
    *   No obvious AI-like naming conventions (e.g., overly verbose or generic names like `process_data_and_save_to_storage_location`) are present. The naming seems human-generated and follows Python best practices.
    *   The use of `dt` as an alias for `datetime` is a common Python convention.

Overall, the naming conventions are good and adhere to PEP 8.