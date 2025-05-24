# Module Analysis: `recursive_training.data.data_store`

## 1. Module Intent/Purpose

The primary role of the [`RecursiveDataStore`](recursive_training/data/data_store.py:49) module is to provide a unified and robust system for storing and retrieving data within the recursive training framework. It aims to offer a comprehensive data management solution with features including:

*   Data versioning and lineage tracking.
*   Data compression for efficient storage.
*   Indexing capabilities for fast and flexible data retrieval.
*   Efficient querying mechanisms.
*   Management of datasets as collections of individual data items.
*   Automatic cleanup of old data based on retention policies.
*   Tracking of storage statistics.

The module is designed to be a central component for data persistence, intended to work in conjunction with other modules like `RecursiveDataIngestionManager` and `RecursiveFeatureProcessor`.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational. It implements a comprehensive set of features expected from a data store, including:
*   Singleton access pattern ([`get_instance`](recursive_training/data/data_store.py:68)).
*   Configuration loading with fallbacks (e.g., for [`PulseConfig`](recursive_training/data/data_store.py:35)).
*   File system-based storage with structured directory layouts.
*   Serialization (pickle with JSON fallback) and compression (gzip).
*   Detailed indexing for various metadata attributes (ID, type, source, timestamp, tags).
*   Full CRUD-like operations for individual items and datasets ([`store`](recursive_training/data/data_store.py:402), [`retrieve`](recursive_training/data/data_store.py:526), [`retrieve_by_query`](recursive_training/data/data_store.py:578), [`store_dataset`](recursive_training/data/data_store.py:635), [`retrieve_dataset`](recursive_training/data/data_store.py:679)).
*   Versioning with cleanup of old versions ([`_cleanup_old_versions`](recursive_training/data/data_store.py:499)).
*   Overall data retention policy enforcement ([`cleanup`](recursive_training/data/data_store.py:796)).
*   Optional export to pandas DataFrame ([`export_to_dataframe`](recursive_training/data/data_store.py:754)).
*   Use of [`ThreadPoolExecutor`](recursive_training/data/data_store.py:135) for potential parallel operations.

No explicit "TODO" comments or obvious major placeholders were found in the code.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Hybrid Storage Details:** The class docstring mentions a "Hybrid storage approach (optimized for different data types)" ([`RecursiveDataStore`](recursive_training/data/data_store.py:54)), but the current implementation primarily details a file-system based approach. Further clarification or implementation of how different data types are optimized or if other backends (e.g., databases for metadata) are part of this "hybrid" nature might be beneficial. The existence of [`test_s3_data_store.py`](tests/recursive_training/test_s3_data_store.py:1) suggests other backends might exist or are planned.
*   **`ThreadPoolExecutor` Usage:** While a [`ThreadPoolExecutor`](recursive_training/data/data_store.py:135) is initialized, its explicit use in performance-critical or bulk operations is not immediately apparent from the main `store`/`retrieve` flows. Its intended application could be further clarified or expanded.
*   **Advanced Indexing:** The current indexing ([`_find_matching_ids`](recursive_training/data/data_store.py:600)) relies on Python dictionaries. For extremely large-scale deployments, integrating more specialized indexing libraries or a database for index management could be a future enhancement.
*   **Cleanup Efficiency:** The [`_update_storage_stats_after_cleanup`](recursive_training/data/data_store.py:857) method recalculates statistics by scanning the entire data directory. This could be inefficient for very large stores. An incremental update approach during deletion might be more performant.
*   **Error Handling Specificity:** Some error handling uses generic `except Exception as e:`. Using more specific exception types could improve debuggability and robustness.

## 4. Connections & Dependencies

*   **Internal Project Modules:**
    *   [`core.pulse_config.PulseConfig`](recursive_training/data/data_store.py:35): Used for configuration management, with a fallback class provided if the main one is unavailable.
*   **External Libraries:**
    *   `json`, `logging`, `os`, `pickle`, `gzip`, `hashlib`, `datetime`, `pathlib`, `typing`, `concurrent.futures`: Standard Python libraries.
    *   `pandas`: Optional dependency ([`PANDAS_AVAILABLE`](recursive_training/data/data_store.py:22) flag) for data export.
*   **File System Interactions:**
    *   The module heavily interacts with the file system, creating and managing directories and files under a configurable `base_path` (default: [`./data/recursive_training`](recursive_training/data/data_store.py:103)).
    *   **Data Files:** Stored under `[base_path]/data/[id_prefix]/[item_id]/v[version].data` or `latest.data`.
    *   **Metadata Files:** Stored as `[base_path]/data/[id_prefix]/[item_id]/metadata.json`.
    *   **Index Files:** Main index at `[base_path]/indices/main_indices.json`.
    *   **Statistics Files:** Storage stats at `[base_path]/metadata/storage_stats.json`.
    *   **Dataset Files:** Dataset definitions under `[base_path]/data/datasets/[dataset_name]/`.
*   **Inter-module Communication:**
    *   Designed to be used by `RecursiveDataIngestionManager` and `RecursiveFeatureProcessor` (as per docstring [`RecursiveDataStore`](recursive_training/data/data_store.py:61)), which would call its public methods like [`store()`](recursive_training/data/data_store.py:402) and [`retrieve()`](recursive_training/data/data_store.py:526).

## 5. Function and Class Example Usages

### `RecursiveDataStore` Singleton Access
```python
# config_options = {"storage_path": "/mnt/custom_data_store"}
# data_store = RecursiveDataStore.get_instance(config_options)
data_store = RecursiveDataStore.get_instance()
```

### Storing an Item
```python
item_data = {"feature_x": 100, "feature_y": "alpha"}
item_metadata = {
    "type": "sensor_reading",
    "source_id": "sensor_001",
    "tags": ["raw_data", "priority_high"]
}
item_id = data_store.store(item_data, item_metadata)
print(f"Stored item with ID: {item_id}")
```

### Retrieving an Item
```python
retrieved_item_data = data_store.retrieve(item_id)
if retrieved_item_data:
    print("Retrieved data:", retrieved_item_data)

# Retrieve a specific version if versioning is enabled
# versioned_data = data_store.retrieve(item_id, version=1)
```

### Retrieving Metadata
```python
metadata = data_store.retrieve_metadata(item_id)
if metadata:
    print("Retrieved metadata:", metadata)
```

### Querying Data
```python
query_params = {"type": "sensor_reading", "tag": "raw_data"}
results = data_store.retrieve_by_query(query_params)
for r_id, r_data in results:
    print(f"Query result - ID: {r_id}, Data: {r_data}")
```

### Storing a Dataset
```python
dataset_items_list = [
    {"data": {"val": 10}, "metadata": {"id": "d_item1", "type": "typeA"}},
    {"data": {"val": 20}, "metadata": {"id": "d_item2", "type": "typeA"}}
]
dataset_info = {"description": "A collection of Type A items."}
dataset_id = data_store.store_dataset("typeA_collection", dataset_items_list, dataset_info)
print(f"Stored dataset with ID: {dataset_id}")
```

### Retrieving a Dataset
```python
items, meta = data_store.retrieve_dataset("typeA_collection")
print(f"Retrieved {len(items)} items from dataset. Metadata: {meta}")
```

## 6. Hardcoding Issues

*   **Default Paths & Filenames:**
    *   Base storage path: [`./data/recursive_training`](recursive_training/data/data_store.py:103) (configurable, but default is hardcoded).
    *   Index file: [`main_indices.json`](recursive_training/data/data_store.py:144).
    *   Stats file: [`storage_stats.json`](recursive_training/data/data_store.py:172).
    *   Internal directory names: `"data"`, `"indices"`, `"metadata"`, `"datasets"`.
    *   File naming patterns: `v{version}.data`, `latest.data`, `metadata.json`.
*   **Default Configuration Values:**
    *   `max_workers` for `ThreadPoolExecutor`: `4` ([`__init__`](recursive_training/data/data_store.py:135)).
    *   `compression_level`: `6` ([`__init__`](recursive_training/data/data_store.py:129)).
    *   `max_versions_per_item`: `5` ([`__init__`](recursive_training/data/data_store.py:132)).
    *   `retention_days`: `30` ([`cleanup`](recursive_training/data/data_store.py:806)).
*   **Algorithms/Parameters:**
    *   Hashing algorithm for ID generation: `md5` ([`_generate_item_id`](recursive_training/data/data_store.py:206)).
    *   Directory sharding prefix length: `2` (e.g., `item_id[:2]`, [`_get_storage_path`](recursive_training/data/data_store.py:220)).

While many of these are reasonable defaults, awareness is key for deployment in varied environments.

## 7. Coupling Points

*   **File System Structure:** The module is tightly coupled to its self-defined directory and file naming conventions on the file system.
*   **[`PulseConfig`](recursive_training/data/data_store.py:35):** Relies on this for external configuration, though a fallback is provided.
*   **Serialization Format:** Primarily uses `pickle`, which can lead to coupling if data needs to be accessed by non-Python systems or if class definitions change. The JSON fallback mitigates this to some extent.
*   **`pandas`:** For the [`export_to_dataframe`](recursive_training/data/data_store.py:754) feature, creating an optional dependency.

## 8. Existing Tests

The project structure indicates the presence of tests for this module:
*   [`tests/recursive_training/test_data_store.py`](tests/recursive_training/test_data_store.py:1): Likely contains direct unit tests for `RecursiveDataStore`.
*   Related test files like [`tests/recursive_training/test_optimized_data_store.py`](tests/recursive_training/test_optimized_data_store.py:1), [`tests/recursive_training/test_s3_data_store.py`](tests/recursive_training/test_s3_data_store.py:1), and [`tests/recursive_training/test_streaming_data_store.py`](tests/recursive_training/test_streaming_data_store.py:1) suggest a broader testing strategy for data storage components and potentially alternative or specialized data store implementations within the `recursive_training` package.

The existence of these files is a positive indicator of test coverage, though the specifics of coverage and test quality would require examining their content.

## 9. Module Architecture and Flow

*   **Architecture:**
    *   Implements the Singleton pattern for global access.
    *   Uses a file-system backend, organizing data into a structured hierarchy (sharded by ID prefix).
    *   Maintains separate storage for data, metadata, indices, and statistics.
    *   Supports versioning for individual data items.
    *   Provides an indexing mechanism (by ID, type, source, timestamp, tags) for efficient lookups.
    *   Abstracts collections of items as "datasets."
*   **Key Components:**
    *   [`RecursiveDataStore`](recursive_training/data/data_store.py:49) class: The central orchestrator of all data operations.
    *   Internal helper methods for path management, ID generation, serialization/compression, index updates, and version control.
    *   Public API for storing, retrieving, querying, and managing data.
*   **Primary Data/Control Flows:**
    1.  **Initialization:** Loads configuration, sets up file paths, and loads existing indices and statistics from disk.
    2.  **Store Operation ([`store`](recursive_training/data/data_store.py:402)):**
        *   Input: Data object and optional metadata.
        *   Process: Generates ID, handles versioning, serializes, compresses, writes data and metadata to files, updates indices, manages old versions, and updates storage statistics.
        *   Output: Item ID.
    3.  **Retrieve Operation ([`retrieve`](recursive_training/data/data_store.py:526)):**
        *   Input: Item ID and optional version.
        *   Process: Determines file path, reads, decompresses, and deserializes data.
        *   Output: Retrieved data object.
    4.  **Query Operation ([`retrieve_by_query`](recursive_training/data/data_store.py:578)):**
        *   Input: Query dictionary.
        *   Process: Uses internal indices ([`_find_matching_ids`](recursive_training/data/data_store.py:600)) to find matching item IDs, then retrieves each item.
        *   Output: List of (item_id, data) tuples.
    5.  **Cleanup Operation ([`cleanup`](recursive_training/data/data_store.py:796)):**
        *   Input: Optional retention days.
        *   Process: Identifies items older than the retention period, removes their files and directories, updates indices, and recalculates storage statistics.
        *   Output: Count of removed items.

## 10. Naming Conventions

*   **Classes:** `RecursiveDataStore`, `PulseConfig` (PascalCase) - Adheres to PEP 8.
*   **Methods:**
    *   Public methods like [`store`](recursive_training/data/data_store.py:402), [`retrieve`](recursive_training/data/data_store.py:526) use snake_case.
    *   Internal/protected methods like [`_load_indices`](recursive_training/data/data_store.py:137), [`_generate_item_id`](recursive_training/data/data_store.py:189) use a leading underscore with snake_case.
    Both are consistent with Python conventions.
*   **Variables:** `base_path`, `item_id`, `compressed_data` (snake_case) - Adheres to PEP 8.
*   **Constants/Flags:** `PANDAS_AVAILABLE`, `PULSE_CONFIG_AVAILABLE` (UPPER_SNAKE_CASE) - Adheres to PEP 8.
*   **File/Directory Names:** `main_indices.json`, `storage_stats.json` (snake_case) - Consistent.
*   **Metadata Keys & Index Names:** `ingestion_timestamp`, `by_id` (snake_case) - Clear and consistent.

The naming conventions are generally consistent, follow PEP 8 guidelines, and are descriptive. No significant deviations or potential AI assumption errors in naming were observed.