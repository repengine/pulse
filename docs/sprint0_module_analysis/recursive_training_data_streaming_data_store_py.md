# Module Analysis: `recursive_training.data.streaming_data_store`

## 1. Module Intent/Purpose

The primary role of the [`StreamingDataStore`](recursive_training/data/streaming_data_store.py:60) module is to provide an advanced data storage and retrieval mechanism with a strong emphasis on streaming capabilities. It extends the [`OptimizedDataStore`](recursive_training/data/optimized_data_store.py:) to handle large datasets more efficiently by reducing memory footprint and improving performance. This is achieved through features like:

*   Streaming data loading and processing without requiring full data materialization in memory.
*   Integration with Apache Arrow and Parquet for efficient columnar data storage and access.
*   Advanced prefetching and caching strategies to anticipate data needs.
*   Progressive loading of data in memory-efficient chunks.

## 2. Operational Status/Completeness

The module appears to be largely operational and complete for its defined scope. It implements the core streaming, prefetching, and storage functionalities. Fallbacks are in place for optional dependencies like PyArrow.

One area noted for potential future enhancement is the predictive loading mechanism ([`_predict_next_access`](recursive_training/data/streaming_data_store.py:170)), which currently uses a simple heuristic. While functional, the comment "More sophisticated prediction could be implemented here" ([`recursive_training/data/streaming_data_store.py:185`](recursive_training/data/streaming_data_store.py:185)) suggests it's a known point for improvement rather than an incomplete feature.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Sophisticated Predictive Loading:** The current access pattern prediction in [`_predict_next_access`](recursive_training/data/streaming_data_store.py:170) is basic. A more advanced predictive model could significantly improve prefetching efficiency.
*   **PyArrow Flight Integration:** The module checks for PyArrow Flight availability ([`recursive_training/data/streaming_data_store.py:35-41`](recursive_training/data/streaming_data_store.py:35-41)) but does not seem to utilize it actively. This could be an intended future integration for further optimizing data transfer, especially in distributed environments.
*   **Configuration for Parquet:** Parquet compression method (`'snappy'`) is hardcoded ([`recursive_training/data/streaming_data_store.py:581`](recursive_training/data/streaming_data_store.py:581)). Making this configurable could be beneficial.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`recursive_training.data.optimized_data_store.OptimizedDataStore`](recursive_training/data/optimized_data_store.py:)
*   [`recursive_training.data.optimized_data_store.PYARROW_AVAILABLE`](recursive_training/data/optimized_data_store.py:)
*   [`recursive_training.data.optimized_data_store.H5PY_AVAILABLE`](recursive_training/data/optimized_data_store.py:)

### External Library Dependencies:
*   `os`
*   `json`
*   `numpy`
*   `pandas`
*   `logging`
*   `time`
*   `threading`
*   `queue`
*   `datetime`
*   `pathlib`
*   `typing`
*   `functools.lru_cache`
*   `concurrent.futures` (`ThreadPoolExecutor`, `Future`)
*   `pyarrow` (optional, includes `pa`, `pq`, `csv`, `ds`, `pc`, `flight`)

### Interactions via Shared Data:
*   Inherits from and extends [`OptimizedDataStore`](recursive_training/data/optimized_data_store.py:), thus interacting with its file-based storage mechanisms (JSON for metadata, Parquet/HDF5 for data).
*   Manages files within `self.base_path / "streaming"` and `self.base_path / "optimized"` directories.

### Input/Output Files:
*   **Reads/Writes:** Parquet files for optimized data storage.
*   **Reads/Writes:** JSON files for metadata (inherited behavior).
*   **Writes:** Log files via the `logging` module.

## 5. Function and Class Example Usages

*   **Singleton Access:**
    ```python
    from recursive_training.data.streaming_data_store import StreamingDataStore
    config = {"chunk_size": 5000, "prefetch_chunks": 3}
    data_store = StreamingDataStore.get_instance(config)
    ```

*   **Streaming Data (Pandas):**
    ```python
    for df_chunk in data_store.stream_dataset("my_dataset_name"):
        process_dataframe_chunk(df_chunk)
    ```

*   **Streaming Data (Arrow):**
    ```python
    if PYARROW_AVAILABLE:
        for arrow_batch in data_store.stream_dataset_arrow("my_dataset_name"):
            process_arrow_batch(arrow_batch)
    ```

*   **Storing Data:**
    ```python
    data_items = [{"id": 1, "value": 100, "timestamp": "2023-01-01T12:00:00Z"}, ...]
    metadata = {"source": "sensor_A"}
    dataset_id = data_store.store_dataset("sensor_data", data_items, metadata)
    ```

*   **Storing Data from a Stream:**
    ```python
    def data_generator():
        for i in range(100000):
            yield {"id": i, "value": i*2, "timestamp": datetime.now(timezone.utc).isoformat()}

    dataset_id = data_store.store_dataset_streaming("generated_data", data_generator())
    ```

*   **Creating and Storing an Arrow Table:**
    ```python
    if PYARROW_AVAILABLE:
        dataset_id, arrow_table = data_store.create_arrow_table("arrow_dataset", data_items, metadata)
    ```

## 6. Hardcoding Issues

*   Default configuration values in [`__init__`](recursive_training/data/streaming_data_store.py:90):
    *   `chunk_size`: `10000` ([`recursive_training/data/streaming_data_store.py:106`](recursive_training/data/streaming_data_store.py:106))
    *   `prefetch_chunks`: `2` ([`recursive_training/data/streaming_data_store.py:107`](recursive_training/data/streaming_data_store.py:107))
    *   `max_worker_threads`: `min(32, (os.cpu_count() or 4))` ([`recursive_training/data/streaming_data_store.py:108`](recursive_training/data/streaming_data_store.py:108))
    *   `stream_buffer_size`: `5` ([`recursive_training/data/streaming_data_store.py:109`](recursive_training/data/streaming_data_store.py:109))
*   Access pattern history length: `10` ([`recursive_training/data/streaming_data_store.py:167`](recursive_training/data/streaming_data_store.py:167))
*   Parquet compression Codec: `'snappy'` ([`recursive_training/data/streaming_data_store.py:581`](recursive_training/data/streaming_data_store.py:581))
*   Dataset ID format string: `f"dataset_{dataset_name}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"` ([`recursive_training/data/streaming_data_store.py:636`](recursive_training/data/streaming_data_store.py:636))
*   File naming conventions for metadata (`_metadata.json`) and item lists (`_items.json`) are inherited and consistently used.

## 7. Coupling Points

*   **Strong Inheritance:** Tightly coupled to its parent class, [`OptimizedDataStore`](recursive_training/data/optimized_data_store.py:), inheriting and overriding its behavior.
*   **File System Dependency:** Relies heavily on the file system for storing Parquet data files and JSON metadata files, following conventions from parent classes.
*   **PyArrow Dependency:** Core streaming and optimized storage functionalities are significantly enhanced by PyArrow. While fallbacks exist, performance and features are reduced without it.
*   **Configuration Driven:** Behavior (chunking, prefetching) is influenced by configuration parameters passed during instantiation or via `get_instance`.

## 8. Existing Tests

A test file exists at [`tests/recursive_training/test_streaming_data_store.py`](tests/recursive_training/test_streaming_data_store.py:). This indicates that unit tests are in place for this module. The specific coverage and nature of these tests would require examining the test file itself.

## 9. Module Architecture and Flow

*   **Architecture:** Implemented as a singleton class ([`StreamingDataStore`](recursive_training/data/streaming_data_store.py:60)) that extends [`OptimizedDataStore`](recursive_training/data/optimized_data_store.py:). It utilizes a [`ThreadPoolExecutor`](recursive_training/data/streaming_data_store.py:112) for asynchronous data prefetching. Thread-safe queues ([`queue.Queue`](recursive_training/data/streaming_data_store.py:115)) and locks ([`threading.RLock`](recursive_training/data/streaming_data_store.py:117)) are used to manage concurrent access to data buffers and prefetch operations. Apache Arrow is leveraged for efficient in-memory representation and Parquet file I/O.
*   **Key Components:**
    *   [`__init__`](recursive_training/data/streaming_data_store.py:90): Initializes paths, configuration options (chunk size, prefetch settings), and the prefetching thread pool.
    *   [`stream_dataset()`](recursive_training/data/streaming_data_store.py:318) / [`stream_dataset_arrow()`](recursive_training/data/streaming_data_store.py:401): Core public methods for yielding data in chunks, either as Pandas DataFrames or Arrow RecordBatches.
    *   [`_prefetch_data()`](recursive_training/data/streaming_data_store.py:188): Internal method responsible for loading individual data chunks. It attempts to use PyArrow for Parquet files and falls back to parent class methods if necessary.
    *   [`_initialize_stream_buffer()`](recursive_training/data/streaming_data_store.py:288): Sets up and manages the prefetch queues and futures for a given dataset stream.
    *   [`_track_access_pattern()`](recursive_training/data/streaming_data_store.py:142) / [`_predict_next_access()`](recursive_training/data/streaming_data_store.py:170): Implement a basic mechanism for predictive loading by tracking and predicting data access.
    *   [`store_dataset()`](recursive_training/data/streaming_data_store.py:591), [`store_dataset_streaming()`](recursive_training/data/streaming_data_store.py:605), [`create_arrow_table()`](recursive_training/data/streaming_data_store.py:539): Public methods for persisting data. These methods prioritize creating Parquet files to support efficient streaming.
*   **Primary Data/Control Flows:**
    *   **Streaming Read:** A call to [`stream_dataset()`](recursive_training/data/streaming_data_store.py:318) (or `stream_dataset_arrow`) initiates the process. [`_initialize_stream_buffer()`](recursive_training/data/streaming_data_store.py:288) is called, which in turn submits multiple [`_prefetch_data()`](recursive_training/data/streaming_data_store.py:188) tasks to the `ThreadPoolExecutor`. As the consumer iterates through the yielded chunks, completed futures are retrieved, and new prefetch tasks for subsequent chunks are submitted.
    *   **Streaming Write:** [`store_dataset_streaming()`](recursive_training/data/streaming_data_store.py:605) consumes items from an input generator. Data is buffered and written in batches using [`_store_batch()`](recursive_training/data/streaming_data_store.py:695) (which stores individual items as JSONs via parent class methods) and then consolidated into an optimized Parquet format via [`_store_as_optimized_batch()`](recursive_training/data/streaming_data_store.py:724).
    *   **Standard Write:** The overridden [`store_dataset()`](recursive_training/data/streaming_data_store.py:591) method ensures that data is stored both in the original JSON format (via `OptimizedDataStore`'s parent) and as an optimized Parquet file, making it readily available for streaming operations.

## 10. Naming Conventions

*   **Class Names:** `StreamingDataStore` follows PascalCase, adhering to PEP 8.
*   **Method Names:** Public methods like [`stream_dataset`](recursive_training/data/streaming_data_store.py:318) and internal/protected methods like [`_prefetch_data`](recursive_training/data/streaming_data_store.py:188) use snake_case, consistent with PEP 8.
*   **Variable Names:** Variables such as `chunk_size`, `buffer_key`, and `prefetch_executor` are in snake_case.
*   **Constants:** Constants like `PYARROW_AVAILABLE` and `FLIGHT_AVAILABLE` use UPPER_SNAKE_CASE.

The naming conventions are generally consistent throughout the module and align well with PEP 8 guidelines. There are no apparent AI assumption errors or significant deviations from standard Python naming practices.