# Module Analysis: `recursive_training.data.optimized_data_store`

**File Path:** [`recursive_training/data/optimized_data_store.py`](recursive_training/data/optimized_data_store.py)

## 1. Module Intent/Purpose

The `OptimizedDataStore` module provides an enhanced version of the `RecursiveDataStore` (from [`recursive_training.data.data_store`](recursive_training/data/data_store.py:)). Its primary role is to offer optimized data storage and retrieval mechanisms, specifically tailored for improved performance when handling large datasets and time-series data. Key optimizations include:

*   Vectorized operations for efficient time-series filtering.
*   Memory-mapping capabilities for large datasets (when using Parquet).
*   Batch data retrieval for improved efficiency with multiple items.
*   An LRU caching mechanism for frequently accessed datasets.
*   Support for more efficient storage formats like Apache Parquet and HDF5, with a fallback to Python's `pickle` format if dependencies are unavailable or another format is configured.

It aims to maintain compatibility with the base `RecursiveDataStore` while providing a more performant layer for data operations.

## 2. Operational Status/Completeness

*   **Status:** Appears largely complete and operational.
*   **Completeness:**
    *   Core functionalities for storing, retrieving (with filtering), and caching datasets in optimized formats are implemented.
    *   Graceful fallbacks are in place for optional dependencies (`pyarrow` for Parquet, `h5py` for HDF5), defaulting to `pickle` if necessary.
    *   Logging is integrated throughout the module using the Python `logging` framework.
    *   A singleton pattern ensures a single instance of the data store.
    *   No `TODO` comments or obvious major placeholders were identified in the code.
    *   A diagnostic step in [`store_dataset_optimized`](recursive_training/data/optimized_data_store.py:268-272) suggests attention to specific data handling issues encountered during development.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Enhanced Error Reporting:** Some errors print directly to `stdout` (e.g., [`_dataframe_to_optimized_storage:183`](recursive_training/data/optimized_data_store.py:183)) in addition to logging, which might be undesirable in production. More structured custom exceptions could be beneficial.
*   **Advanced Configuration:** The current configuration is dictionary-based. A more robust system with schema validation could improve maintainability.
*   **Sophisticated Caching:** The LRU cache is functional. Exploring options like size-based eviction or time-to-live (TTL) could offer more flexibility.
*   **Security of Pickle:** The fallback to `pickle` for storage ([`__init__:102`](recursive_training/data/optimized_data_store.py:102), [`_dataframe_to_optimized_storage:197`](recursive_training/data/optimized_data_store.py:197), [`_optimized_storage_to_dataframe:235`](recursive_training/data/optimized_data_store.py:235)) introduces potential security risks if data sources are not trusted.
*   **Timestamp Filtering Logic:** The date normalization logic in [`retrieve_dataset_optimized`](recursive_training/data/optimized_data_store.py:363-390) (normalizing start to day start, end to next day start) is specific and might warrant review for all intended use cases or edge conditions.
*   **Asynchronous Operations:** While `ThreadPoolExecutor` is used for [`batch_retrieve`](recursive_training/data/optimized_data_store.py:399-425), extending async operations to storage I/O could further improve performance in I/O-bound scenarios.

## 4. Connections & Dependencies

*   **Project-Internal Dependencies:**
    *   [`recursive_training.data.data_store.RecursiveDataStore`](recursive_training/data/data_store.py:45): Inherits from this base class, calling its methods for non-optimized storage and metadata handling.
*   **External Library Dependencies:**
    *   `os`: For path operations and CPU count.
    *   `json`: (Likely used by the parent class, not directly in `OptimizedDataStore` methods beyond what `RecursiveDataStore` handles).
    *   `numpy` (as `np`): Used by `pandas`.
    *   `pandas` (as `pd`): Core library for DataFrame manipulation.
    *   `logging`: For application logging.
    *   `time`: For LRU cache timestamping.
    *   `datetime`, `timezone` (from `datetime`): For handling timestamps.
    *   `pathlib.Path`: For path manipulations.
    *   `typing`: For type hinting.
    *   `functools.lru_cache`: Imported but not directly applied as a decorator in the provided code.
    *   `threading.RLock`: For cache synchronization.
    *   `concurrent.futures.ThreadPoolExecutor`: For parallel batch retrieval.
    *   `pyarrow`, `pyarrow.parquet` (optional): For Parquet file operations.
    *   `h5py` (optional): For HDF5 file operations. A mock class is provided if `h5py` is not installed.
*   **Shared Data Interactions:**
    *   **File System:** Reads and writes optimized dataset files (Parquet, HDF5, Pickle) under `self.base_path / "optimized"`. Also interacts with files managed by the parent `RecursiveDataStore`.
*   **Input/Output Files:**
    *   **Input:** Optimized data files (`.parquet`, `.h5`, `.pkl`) from the `optimized` subdirectory. Data and metadata files via `RecursiveDataStore`.
    *   **Output:** Optimized data files to the `optimized` subdirectory. Data and metadata files via `RecursiveDataStore`.
    *   **Logs:** Generates logs via a logger named `"OptimizedDataStore"`.

## 5. Function and Class Example Usages

*   **Class Instantiation (Singleton):**
    ```python
    # from recursive_training.data.optimized_data_store import OptimizedDataStore
    # config = {"storage_format": "parquet", "cache_size": 200, "base_path": "./my_data"}
    # data_store = OptimizedDataStore.get_instance(config)
    ```
*   **Storing a Dataset:**
    ```python
    # data_items = [
    #     {"id": "a", "value": 10, "timestamp": "2023-01-01T00:00:00Z"},
    #     {"id": "b", "value": 20, "timestamp": "2023-01-01T01:00:00Z"}
    # ]
    # metadata = {"source": "test_source"}
    # dataset_id = data_store.store_dataset_optimized("my_dataset", data_items, metadata)
    # print(f"Stored dataset with ID: {dataset_id}")
    ```
*   **Retrieving a Dataset (Optimized):**
    ```python
    # df, meta = data_store.retrieve_dataset_optimized(
    #     "my_dataset",
    #     start_time="2023-01-01T00:00:00Z",
    #     columns=["value", "timestamp"]
    # )
    # print("Retrieved DataFrame:", df.head())
    # print("Metadata:", meta)
    ```
*   **Batch Retrieving Items (from base store):**
    ```python
    # Assuming 'item_id_1', 'item_id_2' are retrievable via RecursiveDataStore's 'retrieve'
    # item_ids_to_fetch = ["item_id_1", "item_id_2"]
    # results = data_store.batch_retrieve(item_ids_to_fetch)
    # print("Batch results:", results)
    ```
*   **Retrieving with Custom Filter:**
    ```python
    # def my_filter(dataframe):
    #     return dataframe[dataframe['value'] > 15]
    #
    # filtered_df, meta = data_store.retrieve_filtered_dataset("my_dataset", my_filter)
    # print("Filtered DataFrame:", filtered_df.head())
    ```

## 6. Hardcoding Issues

*   **Default Configuration Values:**
    *   `use_memory_mapping`: `True` ([`__init__:93`](recursive_training/data/optimized_data_store.py:93))
    *   `storage_format`: `"parquet"` ([`__init__:96`](recursive_training/data/optimized_data_store.py:96))
    *   `cache_size`: `128` ([`__init__:104`](recursive_training/data/optimized_data_store.py:104))
    *   `batch_size`: `1000` ([`__init__:105`](recursive_training/data/optimized_data_store.py:105))
    *   `max_workers`: `min(32, (os.cpu_count() or 4))` ([`__init__:115`](recursive_training/data/optimized_data_store.py:115))
    (These are configurable but represent hardcoded defaults.)
*   **File Extensions:** Implicitly defined by `storage_format` in [`_get_optimized_storage_path`](recursive_training/data/optimized_data_store.py:133-141) (e.g., `.parquet`, `.h5`, `.pkl`).
*   **HDF5 Key:** The string `'data'` is used as the key for HDF5 storage ([`_dataframe_to_optimized_storage:189`](recursive_training/data/optimized_data_store.py:189), [`_optimized_storage_to_dataframe:228`](recursive_training/data/optimized_data_store.py:228)).
*   **Parquet Compression:** `"snappy"` is hardcoded ([`_dataframe_to_optimized_storage:180`](recursive_training/data/optimized_data_store.py:180)).
*   **Optimized Path Subdirectory:** The name `"optimized"` for the subdirectory is hardcoded ([`__init__:88`](recursive_training/data/optimized_data_store.py:88)).
*   **Logger Name:** `"OptimizedDataStore"` is hardcoded ([`__init__:118`](recursive_training/data/optimized_data_store.py:118)).

## 7. Coupling Points

*   **`RecursiveDataStore`:** Tightly coupled as its base class. `OptimizedDataStore` relies on `super()` calls for fundamental storage operations and metadata management.
*   **File System:** Direct and significant interaction for reading/writing optimized data files within the `self.base_path / "optimized"` directory.
*   **Pandas:** Heavily reliant on `pandas.DataFrame` as the central data structure for optimized operations.
*   **Optional Libraries (`pyarrow`, `h5py`):** Functionality changes based on their availability (conditional coupling).
*   **Configuration Dictionary:** The module's behavior is strongly tied to the structure and keys of the input configuration dictionary.

## 8. Existing Tests

*   A dedicated test file exists at [`tests/recursive_training/test_optimized_data_store.py`](tests/recursive_training/test_optimized_data_store.py:).
*   The content and coverage of these tests would require a separate review of the test file itself.
*   Internal comments (e.g., "Diagnostic step... mimics part of the flow in the working test_streaming_store" in [`store_dataset_optimized`](recursive_training/data/optimized_data_store.py:268-270)) suggest that testing, including for specific scenarios like streaming, has been part of the development process.

## 9. Module Architecture and Flow

*   **Singleton Design:** Employs [`get_instance`](recursive_training/data/optimized_data_store.py:62-75) to provide a single, shared instance.
*   **Layered Storage:**
    1.  Calls `super().store_dataset()` to save data in the base `RecursiveDataStore` format (likely JSON).
    2.  Converts data to a `pandas.DataFrame`.
    3.  Saves the DataFrame to an optimized format (Parquet, HDF5, or Pickle) in a separate `optimized` directory.
*   **Retrieval Strategy:**
    1.  Checks an in-memory LRU cache (`dataset_cache`).
    2.  If not in cache, attempts to load from the optimized file storage.
    3.  If not in optimized storage, falls back to `super().retrieve_dataset()` (JSON), converts to DataFrame, and stores it in the optimized format for future retrievals.
    4.  Applies time-based and column-based filters using vectorized Pandas operations.
*   **Caching:** Implements an LRU cache (`dataset_cache`, `dataset_access_times`, [`_update_cache_access`](recursive_training/data/optimized_data_store.py:143-161)) for DataFrames to speed up repeated access.
*   **Concurrency:** Uses a `ThreadPoolExecutor` for the [`batch_retrieve`](recursive_training/data/optimized_data_store.py:399-425) method to fetch multiple items in parallel.
*   **Configuration-Driven Behavior:** Key aspects like storage format, cache size, and memory mapping are controlled via an initial configuration dictionary.
*   **Error Handling & Fallbacks:** Includes `try-except` blocks for file operations and for optional dependencies, falling back to `pickle` if preferred formats are unavailable.

## 10. Naming Conventions

*   **Overall:** Adheres well to Python's PEP 8 naming conventions.
*   **Classes:** `OptimizedDataStore`, `MockH5py` use PascalCase.
*   **Methods & Functions:** `get_instance`, `_get_optimized_storage_path`, `store_dataset_optimized` use snake_case. Protected members are prefixed with a single underscore.
*   **Variables & Attributes:** `optimized_path`, `storage_format`, `PYARROW_AVAILABLE` (constants in uppercase) generally use snake_case or uppercase for constants.
*   **Clarity:** Names are generally descriptive and understandable.
*   **Type Hinting:** Extensive use of type hints improves code readability and maintainability.
*   No significant deviations or potential AI assumption errors in naming were observed. The direct `print` statement on line 183 is stylistically unusual for a library but not a naming issue.