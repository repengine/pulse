# Module Analysis: manual_opec_plugin.py

## Module Intent/Purpose

The primary role of this module is to provide a manual method for ingesting historical OPEC crude oil price data into the Pulse system. It specifically reads data from a local zip file (`QDL_OPEC_7f41729ade733436c2dc493d282cef69.zip`) located in the `data/manual_bulk_data` directory, processes the CSV file within, and creates "orb_price" signals. This serves as an alternative to API-based ingestion, useful when the original data source is unavailable or requires credentials.

## Operational Status/Completeness

The module appears functionally complete for its stated purpose of reading from a local zip file. It includes error handling for missing files, bad zip files, and issues processing individual rows. There are comments indicating potential areas for improvement regarding incremental saving for very large files, but the core logic for reading and processing the provided zip file seems implemented.

## Implementation Gaps / Unfinished Next Steps

*   **Incremental Saving:** A comment on lines 99-104 and 123-130 notes that incremental saving for very large files would require modification to `save_processed_data` or implementing new logic. The current implementation saves the entire list of signals at once, which might be inefficient for massive datasets.
*   **CSV Filename Assumption:** The code assumes a CSV file exists within the zip and takes the first one found (lines 60-64). A more robust approach might involve checking for a specific filename or handling multiple CSVs if applicable.
*   **Data Source Verification:** While it reads from a local file, there's no explicit mechanism to verify the integrity or source of the data within the zip file itself.

## Connections & Dependencies

*   **Direct Imports:**
    *   [`datetime`](#) as `dt`
    *   [`logging`](#)
    *   [`os`](#)
    *   [`zipfile`](#)
    *   [`csv`](#)
    *   [`typing`](#) (`Dict`, `List`, `Any`, `Optional`)
    *   [`iris.iris_plugins.IrisPluginManager`](iris/iris_plugins.py)
    *   [`iris.iris_utils.ingestion_persistence.save_processed_data`](iris/iris_utils/ingestion_persistence.py)
*   **External Library Dependencies:** Standard Python libraries (`datetime`, `logging`, `os`, `zipfile`, `csv`, `typing`).
*   **Interaction with other modules:** Interacts with `iris.iris_plugins.IrisPluginManager` by inheriting from it and with `iris.iris_utils.ingestion_persistence.save_processed_data` to save processed data.
*   **Input/Output Files:**
    *   Input: `data/manual_bulk_data/QDL_OPEC_7f41729ade733436c2dc493d282cef69.zip`
    *   Output: Data saved via `save_processed_data`, likely to a persistence layer managed by that utility.

## Function and Class Example Usages

*   **`ManualOPECPlugin` Class:** Inherits from `IrisPluginManager`. The core logic resides in the `fetch_signals` method.
*   **`fetch_signals()` method:** This method is the main entry point for the plugin. It is expected to be called by the `IrisPluginManager` to retrieve data signals. It handles file reading, CSV parsing, data transformation, and saving.

```python
# Example (conceptual) of how the plugin would be used by IrisPluginManager
from iris.iris_plugins import IrisPluginManager
from iris.iris_plugins_variable_ingestion.manual_opec_plugin import ManualOPECPlugin

# Assuming the zip file is in place
mgr = IrisPluginManager()
mgr.register_plugin(ManualOPECPlugin)
signals = mgr.run_plugins() # This would call fetch_signals internally
print(signals)
```

## Hardcoding Issues

*   **Zip File Path:** The path to the zip file (`data/manual_bulk_data/QDL_OPEC_7f41729ade733436c2dc493d282cef69.zip`) is hardcoded in the `_OPEC_ZIP_PATH` constant (line 38).
*   **Source Name:** The source name `manual_opec` is hardcoded in `_SOURCE_NAME` (line 35).
*   **Signal Name:** The signal name `orb_price` is hardcoded (line 89).
*   **Dataset ID:** The dataset ID `OPEC/ORB` is hardcoded (line 93 and 133).
*   **Date Format:** The date format string `"%Y-%m-%d"` is hardcoded for parsing (line 85).
*   **Column Names:** Assumes 'date' and 'value' column names in the CSV (lines 77-78).

## Coupling Points

*   Strongly coupled with the specific structure and naming of the input zip file and the CSV within it.
*   Coupled with the `IrisPluginManager` interface by inheriting from it.
*   Coupled with the `save_processed_data` function from `iris.iris_utils.ingestion_persistence`.

## Existing Tests

Based on the file structure provided in `environment_details`, there is no dedicated test file specifically for `manual_opec_plugin.py` (e.g., `tests/iris/iris_plugins_variable_ingestion/test_manual_opec_plugin.py`). There is a general test file for plugins at [`iris/test_plugins.py`](iris/test_plugins.py), but it's unclear if this specific manual plugin is covered.

## Module Architecture and Flow

The module follows a simple architecture:
1.  It defines a class `ManualOPECPlugin` that extends `IrisPluginManager`.
2.  The core logic is within the `fetch_signals` method.
3.  `fetch_signals` checks for the existence of the hardcoded zip file.
4.  If found, it opens the zip, finds the first CSV file, and reads its content.
5.  It iterates through CSV rows, parses date and value, and creates signal dictionaries.
6.  Processed signals are collected in a list.
7.  Error handling is included for file operations and data parsing.
8.  Finally, the collected signals are passed to `save_processed_data` and returned.

## Naming Conventions

Naming conventions generally follow Python standards (PEP 8). Class names use CapWords (`ManualOPECPlugin`), function names use snake_case (`fetch_signals`, `save_processed_data`), and constants use SCREAMING_SNAKE_CASE (`_SOURCE_NAME`, `_OPEC_ZIP_PATH`). Variable names within `fetch_signals` are descriptive (`data_filename`, `reader`, `row`, `date_str`, `value_str`, `timestamp`, `value`, `signal`). There are no immediately obvious AI assumption errors or significant deviations from standard practices.