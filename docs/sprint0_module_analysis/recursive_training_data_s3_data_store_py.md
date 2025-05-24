# Module Analysis: `recursive_training/data/s3_data_store.py`

## Table of Contents
- [Module Intent/Purpose](#module-intentpurpose)
- [Operational Status/Completeness](#operational-statuscompleteness)
- [Implementation Gaps / Unfinished Next Steps](#implementation-gaps--unfinished-next-steps)
- [Connections & Dependencies](#connections--dependencies)
- [Function and Class Example Usages](#function-and-class-example-usages)
- [Hardcoding Issues](#hardcoding-issues)
- [Coupling Points](#coupling-points)
- [Existing Tests](#existing-tests)
- [Module Architecture and Flow](#module-architecture-and-flow)
- [Naming Conventions](#naming-conventions)

## Module Intent/Purpose
The primary role of the [`S3DataStore`](recursive_training/data/s3_data_store.py:56) class within this module is to provide an enhanced data storage solution with AWS S3 integration. It extends the `StreamingDataStore` to allow for loading, streaming, and caching data from S3 buckets, supporting various formats like Parquet, HDF5, and Pickle. It aims to offer efficient data transfer and management between local storage and S3.

## Operational Status/Completeness
The module appears to be largely complete and operational for its defined scope.
- It implements core functionalities for S3 interaction: initialization, key generation, caching, download/upload, listing datasets, and metadata retrieval.
- It handles different data formats and provides mechanisms for direct S3 reads (for Parquet) and cached reads.
- Error handling for S3 client initialization and operations (e.g., `NoSuchKey`) is present.
- Logging is implemented throughout the module.
- It includes a singleton pattern for the `S3DataStore` class ([`get_instance()`](recursive_training/data/s3_data_store.py:75)).
- Cache management ([`_manage_cache_size()`](recursive_training/data/s3_data_store.py:448)) is implemented to control local disk usage.

There are no obvious major placeholders (like `pass` in critical methods or extensive TODO comments indicating unfinished core logic).

## Implementation Gaps / Unfinished Next Steps
- **More Robust Error Handling/Retries:** While basic error handling exists, more sophisticated retry mechanisms for S3 operations (beyond the `s3_retry_attempts` config which isn't explicitly used in download/upload methods shown) could be beneficial, especially for transient network issues. The `retry_attempts` config is initialized ([`self.retry_attempts`](recursive_training/data/s3_data_store.py:110)) but not visibly used in the provided [`_download_from_s3()`](recursive_training/data/s3_data_store.py:229) or [`_upload_to_s3()`](recursive_training/data/s3_data_store.py:263) methods.
- **Advanced S3 Features:** The module could be extended to support more advanced S3 features like:
    - Multipart uploads for very large files (though `upload_file` might handle this transparently via `boto3`).
    - S3 object versioning.
    - S3 lifecycle policies for data management directly from the store.
    - More granular error reporting or specific exception types for S3 operations.
- **Security Enhancements:** While it uses `boto3` which handles credentials, explicit discussion or configuration options for IAM roles, temporary credentials, or encryption (client-side/server-side) are not detailed within this module's code, relying on the environment's `boto3` setup.
- **Asynchronous Operations:** The current `s3_executor` ([`self.s3_executor`](recursive_training/data/s3_data_store.py:128)) is a `ThreadPoolExecutor`. For highly I/O-bound S3 operations, an `asyncio` based approach could offer better performance, though this would be a significant architectural change.
- **Cache Invalidation Strategy:** The current cache invalidation is based on age ([`cache_expiration_hours`](recursive_training/data/s3_data_store.py:116)). More sophisticated strategies (e.g., based on S3 object ETag or LastModified timestamp comparisons before downloading) could ensure fresher data without relying solely on time-based expiry. The [`_get_s3_object_metadata()`](recursive_training/data/s3_data_store.py:353) fetches ETag and LastModified, but [`_is_in_cache()`](recursive_training/data/s3_data_store.py:204) only checks file existence and age.

## Connections & Dependencies
### Direct Imports from Other Project Modules:
- [`recursive_training.data.streaming_data_store.StreamingDataStore`](recursive_training/data/streaming_data_store.py) ([`StreamingDataStore`](recursive_training/data/s3_data_store.py:29))
- [`recursive_training.data.streaming_data_store.PYARROW_AVAILABLE`](recursive_training/data/streaming_data_store.py) ([`PYARROW_AVAILABLE`](recursive_training/data/s3_data_store.py:30))
- [`recursive_training.data.streaming_data_store.H5PY_AVAILABLE`](recursive_training/data/streaming_data_store.py) ([`H5PY_AVAILABLE`](recursive_training/data/s3_data_store.py:31))

### External Library Dependencies:
- `os`
- `json`
- `logging`
- `time`
- `threading`
- `datetime`
- `pathlib`
- `typing`
- `functools` ([`lru_cache`](recursive_training/data/s3_data_store.py:20) - though not explicitly used in the provided code snippet, it's imported)
- `concurrent.futures` ([`ThreadPoolExecutor`](recursive_training/data/s3_data_store.py:21))
- `numpy` (as `np`)
- `pandas` (as `pd`)
- `boto3` (optional, with fallback mock)
- `botocore.exceptions.ClientError` (optional)
- `pyarrow` (as `pa`, optional)
- `pyarrow.parquet` (as `pq`, optional)
- `pyarrow.dataset` (as `ds`, optional)
- `shutil` (used in [`_ensure_dataset_in_cache()`](recursive_training/data/s3_data_store.py:437))

### Interaction with Other Modules via Shared Data:
- Inherits from and extends [`StreamingDataStore`](recursive_training/data/streaming_data_store.py), implying interaction with its methods and storage mechanisms (e.g., local optimized storage as a fallback).
- Data is stored and retrieved from AWS S3, which acts as a shared data source/sink.

### Input/Output Files:
- **Input:** Reads data files (Parquet, HDF5, Pickle) from AWS S3 buckets.
- **Output:** Writes data files (Parquet, HDF5, Pickle) to AWS S3 buckets.
- **Local Cache:** Creates and manages files in a local cache directory ([`self.cache_dir`](recursive_training/data/s3_data_store.py:114)).
- **Logs:** Generates logs via the `logging` module.

## Function and Class Example Usages
### `S3DataStore` Class
**Initialization:**
```python
config = {
    "s3_data_bucket": "my-data-bucket",
    "s3_results_bucket": "my-results-bucket",
    "s3_prefix": "processed_data/",
    "s3_region": "us-west-2",
    "s3_cache_dir": "/tmp/s3_cache",
    "max_cache_size_gb": 5,
    "storage_format": "parquet" # Inherited from StreamingDataStore
}
s3_store = S3DataStore.get_instance(config)
# or
# s3_store = S3DataStore(config) # if not using singleton
```

**Storing Data:**
```python
data_items = [{"id": 1, "value": 100, "timestamp": "2023-01-01T12:00:00Z"}, {"id": 2, "value": 150, "timestamp": "2023-01-01T13:00:00Z"}]
metadata = {"source": "sensor_A", "version": "1.1"}
dataset_id = s3_store.store_dataset_s3("my_sensor_data", data_items, metadata)
# This also stores it locally first via super().store_dataset_optimized()
```

**Retrieving Data:**
```python
df, meta = s3_store.retrieve_dataset_s3("my_sensor_data")
# Retrieve specific columns or time range
df_filtered, meta_filtered = s3_store.retrieve_dataset_s3(
    "my_sensor_data",
    start_time="2023-01-01T12:30:00Z",
    columns=["id", "value"]
)
```

**Streaming Data:**
```python
for chunk_df in s3_store.stream_dataset_s3("large_dataset", columns=["feature1", "feature2"]):
    process_chunk(chunk_df)
```

**Listing Datasets in S3:**
```python
s3_datasets = s3_store.list_s3_datasets()
print(s3_datasets)
```

**Copying Local Dataset to S3:**
```python
# Assuming "local_only_data" was stored using store_dataset_optimized but not yet in S3
s3_store.copy_dataset_to_s3("local_only_data")
```

## Hardcoding Issues
- **Default S3 Bucket Names:**
    - [`s3_data_bucket`](recursive_training/data/s3_data_store.py:103): Defaults to `"pulse-retrodiction-data-poc"`.
    - [`s3_results_bucket`](recursive_training/data/s3_data_store.py:104): Defaults to `"pulse-retrodiction-results-poc"`.
    These are configurable but having "poc" (Proof of Concept) in default production-intended code might be an oversight.
- **Default S3 Prefix:**
    - [`s3_prefix`](recursive_training/data/s3_data_store.py:105): Defaults to `"datasets/"`.
- **Default S3 Region:**
    - [`s3_region`](recursive_training/data/s3_data_store.py:106): Defaults to `"us-east-1"`.
- **Default Cache Directory Suffix:**
    - [`s3_cache_dir`](recursive_training/data/s3_data_store.py:114): Defaults to `str(self.base_path / "s3_cache")`. The "s3_cache" part is hardcoded.
- **Default Max Cache Size:**
    - [`max_cache_size_gb`](recursive_training/data/s3_data_store.py:115): Defaults to `10` GB.
- **Default Cache Expiration:**
    - [`cache_expiration_hours`](recursive_training/data/s3_data_store.py:116): Defaults to `24` hours.
- **Default Download Chunk Size:**
    - [`download_chunk_size`](recursive_training/data/s3_data_store.py:111): Defaults to `8 * 1024 * 1024` (8MB).
- **HDF5 Key:**
    - When reading HDF5 from cache ([`retrieve_dataset_s3()`](recursive_training/data/s3_data_store.py:638)), the key is hardcoded to `'data'`: `df = pd.read_hdf(cache_path, key='data')`. This assumes all HDF5 files stored will use this key.

While these are defaults and configurable, their presence as hardcoded strings within the `__init__` method is notable.

## Coupling Points
- **`StreamingDataStore`:** Tightly coupled to its parent class [`StreamingDataStore`](recursive_training/data/streaming_data_store.py) through inheritance, calling its methods (e.g., [`super().__init__()`](recursive_training/data/s3_data_store.py:97), [`super().store_dataset_optimized()`](recursive_training/data/s3_data_store.py:540), [`super().retrieve_dataset_optimized()`](recursive_training/data/s3_data_store.py:692), [`super().stream_dataset()`](recursive_training/data/s3_data_store.py:795)). It relies on the parent's local storage mechanisms as fallbacks or primary local persistence.
- **AWS S3 Service:** Directly interacts with AWS S3 via the `boto3` library. Availability and configuration of AWS credentials and network access to S3 are critical.
- **Configuration Dictionary:** Relies on a configuration dictionary passed during initialization for S3 parameters, cache settings, etc. The structure and keys of this dictionary form a coupling point.
- **File Formats (Parquet, HDF5, Pickle):** The module's ability to handle these formats depends on the availability of `pyarrow` and `h5py`, and the internal logic is specific to reading/writing these formats.
- **`pandas` DataFrame:** The primary data structure for datasets is `pandas.DataFrame`.
- **Local Filesystem:** Interacts with the local filesystem for caching S3 data.

## Existing Tests
The file list provided in the prompt shows a test file that seems relevant:
- [`tests/recursive_training/test_s3_data_store.py`](tests/recursive_training/test_s3_data_store.py)

Without inspecting the content of this test file, we can infer:
- **Existence:** Tests specifically for `S3DataStore` exist.
- **Potential Coverage:** Likely covers core functionalities like storing to S3, retrieving from S3, caching, and possibly streaming.
- **Nature of Tests:** Expected to be integration tests involving `boto3` (possibly mocked for unit tests) and filesystem interactions.

Obvious gaps or problematic tests cannot be determined without viewing the test file's content. However, testing interactions with a live S3 bucket can be slow and costly, so robust mocking strategies (e.g., using `moto`) would be important for efficient and reliable unit/integration testing.

## Module Architecture and Flow
1.  **Initialization ([`__init__()`](recursive_training/data/s3_data_store.py:89)):**
    *   Initializes the parent [`StreamingDataStore`](recursive_training/data/streaming_data_store.py).
    *   Loads S3-specific configurations (bucket names, region, cache settings).
    *   Creates the local S3 cache directory.
    *   Initializes the `boto3` S3 client and resource ([`_init_s3_client()`](recursive_training/data/s3_data_store.py:139)).
    *   Sets up a `ThreadPoolExecutor` for S3 transfers.
2.  **Singleton Access ([`get_instance()`](recursive_training/data/s3_data_store.py:75)):** Provides a class method to get/create a single instance of `S3DataStore`.
3.  **Core S3 Operations:**
    *   **Key Generation:** [`_get_s3_key()`](recursive_training/data/s3_data_store.py:166) constructs S3 object keys based on dataset name and storage format.
    *   **Download/Upload:** [`_download_from_s3()`](recursive_training/data/s3_data_store.py:229) and [`_upload_to_s3()`](recursive_training/data/s3_data_store.py:263) handle file transfers.
    *   **Metadata:** [`_get_s3_object_metadata()`](recursive_training/data/s3_data_store.py:353) fetches S3 object metadata, with a local cache for this metadata.
4.  **Caching Mechanism:**
    *   [`_get_s3_cache_path()`](recursive_training/data/s3_data_store.py:190) determines local cache paths.
    *   [`_is_in_cache()`](recursive_training/data/s3_data_store.py:204) checks cache existence and expiration.
    *   [`_ensure_dataset_in_cache()`](recursive_training/data/s3_data_store.py:402) ensures a dataset is downloaded to cache if not present or expired.
    *   [`_manage_cache_size()`](recursive_training/data/s3_data_store.py:448) prunes the cache based on size and last access time.
5.  **Data Storage ([`store_dataset_s3()`](recursive_training/data/s3_data_store.py:526)):**
    *   First, calls `super().store_dataset_optimized()` to save locally.
    *   Then, uploads the locally saved file to S3.
6.  **Data Retrieval ([`retrieve_dataset_s3()`](recursive_training/data/s3_data_store.py:566)):**
    *   Attempts direct S3 read for Parquet if `pyarrow` is available.
    *   If direct read fails or is not applicable, ensures data is in the local cache (downloading if necessary).
    *   Reads from the local cache.
    *   Applies time and column filters.
    *   Falls back to `super().retrieve_dataset_optimized()` if S3/cache methods fail.
7.  **Data Streaming ([`stream_dataset_s3()`](recursive_training/data/s3_data_store.py:707)):**
    *   Attempts direct streaming from S3 for Parquet files using `pyarrow.dataset`.
    *   If direct S3 streaming is not possible/fails, falls back to ensuring the dataset is in cache and then uses `super().stream_dataset()` on the cached file.
    *   If caching fails, falls back to `super().stream_dataset()` on the original local optimized storage.
8.  **Utility Methods:**
    *   [`list_s3_datasets()`](recursive_training/data/s3_data_store.py:698): Lists datasets in the S3 data bucket.
    *   [`copy_dataset_to_s3()`](recursive_training/data/s3_data_store.py:804), [`copy_all_datasets_to_s3()`](recursive_training/data/s3_data_store.py:839): Utilities to sync local data to S3.
9.  **Cleanup ([`close()`](recursive_training/data/s3_data_store.py:872)):** Shuts down the `s3_executor`.

**Data Flow:**
- **Write Path:** Data -> `store_dataset_s3()` -> `StreamingDataStore.store_dataset_optimized()` (local save) -> `_upload_to_s3()` (S3 save).
- **Read Path (Full):** Request -> `retrieve_dataset_s3()` -> Try direct S3 Parquet read -> If fail/not Parquet, `_ensure_dataset_in_cache()` (S3 download if needed) -> Read from local cache -> If fail, `StreamingDataStore.retrieve_dataset_optimized()` (local read).
- **Read Path (Stream):** Request -> `stream_dataset_s3()` -> Try direct S3 Parquet stream -> If fail/not Parquet, `_ensure_dataset_in_cache()` -> `StreamingDataStore.stream_dataset()` (from cache) -> If fail, `StreamingDataStore.stream_dataset()` (from local optimized).

## Naming Conventions
- **Class Name:** `S3DataStore` is clear and follows PascalCase (PEP 8).
- **Method Names:** Generally follow snake_case (PEP 8), e.g., [`_init_s3_client()`](recursive_training/data/s3_data_store.py:139), [`store_dataset_s3()`](recursive_training/data/s3_data_store.py:526).
    - Private/internal methods are correctly prefixed with a single underscore (e.g., [`_get_s3_key()`](recursive_training/data/s3_data_store.py:166)).
- **Variable Names:** Generally follow snake_case (PEP 8), e.g., [`s3_data_bucket`](recursive_training/data/s3_data_store.py:103), [`cache_path`](recursive_training/data/s3_data_store.py:416).
- **Constants:** `PYARROW_AVAILABLE`, `H5PY_AVAILABLE`, `BOTO3_AVAILABLE` are uppercase, which is conventional.
- **Consistency:** Naming seems consistent throughout the module.
- **Potential AI Assumption Errors/Deviations:**
    - No obvious AI-like naming errors (e.g., overly verbose or unidiomatic names).
    - Adherence to PEP 8 seems good.
    - The use of `PYARROW_AVAILABLE` and similar flags for optional dependencies is a common and clear pattern.
    - The mock module for `boto3` ([`MockModule`](recursive_training/data/s3_data_store.py:42)) when `boto3` is not available is a practical approach to prevent import errors and allow type checking/Pylance to function without the dependency installed.

Overall, naming conventions are well-applied and contribute to the readability of the code.