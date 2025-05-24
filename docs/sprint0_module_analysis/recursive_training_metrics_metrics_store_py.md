# Module Analysis: `recursive_training.metrics.metrics_store`

**File Path:** [`recursive_training/metrics/metrics_store.py`](../../recursive_training/metrics/metrics_store.py)

## 1. Module Intent/Purpose

The `recursive_training.metrics.metrics_store` module provides a centralized singleton class, `MetricsStore`, responsible for storing, retrieving, and querying various metrics generated during the recursive training process. Its primary role is to act as a repository for:
*   Training iteration metrics (e.g., loss, accuracy).
*   Model performance data.
*   Associated operational costs, such as API calls and token usage, with built-in threshold warnings.

The module is designed to complement the `RecursiveDataStore` and support the overall evaluation and monitoring of the recursive training system by persisting metrics to the file system and providing query capabilities.

## 2. Operational Status/Completeness

The module appears to be largely complete and operational for its defined scope.
*   It implements core functionalities: storing metrics, indexing for efficient querying, caching, cost tracking, and data export.
*   Error handling for file operations and optional dependencies (like `PulseConfig`, `pandas`, `numpy`) is present.
*   Configuration options are available for paths, caching, and cost thresholds.
*   No "TODO", "FIXME", or obvious placeholder comments indicating unfinished critical sections were observed in the main logic.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Advanced Metric Operations:** The class docstring mentions "Support for metric aggregation and analysis" ([`recursive_training/metrics/metrics_store.py:55`](../../recursive_training/metrics/metrics_store.py:55)) and "Support for metric visualization and reporting" ([`recursive_training/metrics/metrics_store.py:58`](../../recursive_training/metrics/metrics_store.py:58)). While data can be exported (e.g., to a DataFrame), dedicated methods for performing complex aggregations, statistical analyses, or generating visualizations directly within the module are not implemented. These functionalities might be intended for external tools.
*   **Data Compression:** The module includes configuration options `use_compression` ([`recursive_training/metrics/metrics_store.py:119`](../../recursive_training/metrics/metrics_store.py:119)) and `compression_level` ([`recursive_training/metrics/metrics_store.py:120`](../../recursive_training/metrics/metrics_store.py:120)), and imports `gzip` ([`recursive_training/metrics/metrics_store.py:13`](../../recursive_training/metrics/metrics_store.py:13)). However, the core metric storage ([`store_metric()`](../../recursive_training/metrics/metrics_store.py:344)) and retrieval ([`get_metric()`](../../recursive_training/metrics/metrics_store.py:391)) methods use standard JSON operations without visible gzip compression/decompression logic for the individual metric files. This feature might be planned or handled externally. The `pickle` library ([`recursive_training/metrics/metrics_store.py:12`](../../recursive_training/metrics/metrics_store.py:12)) is also imported but not used in the provided code.
*   **Cache Eviction Strategy:** The cache eviction mechanism is described as a "simplistic approach" ([`recursive_training/metrics/metrics_store.py:380`](../../recursive_training/metrics/metrics_store.py:380)), removing the oldest items based on sorted keys. More sophisticated strategies (e.g., LRU, LFU) could be beneficial if cache performance becomes a bottleneck.
*   **Untested Methods:** The methods `get_metrics_by_filter()` ([`recursive_training/metrics/metrics_store.py:630`](../../recursive_training/metrics/metrics_store.py:630)) and `close()` ([`recursive_training/metrics/metrics_store.py:625`](../../recursive_training/metrics/metrics_store.py:625)) do not have dedicated tests in the corresponding test file. While `get_recent_metrics()` ([`recursive_training/metrics/metrics_store.py:670`](../../recursive_training/metrics/metrics_store.py:670)) is a wrapper around `query_metrics()`, `get_metrics_by_filter()` employs a different retrieval and filtering logic that would benefit from specific tests.

## 4. Connections & Dependencies

### Internal Project Dependencies:
*   [`core.pulse_config.PulseConfig`](../../core/pulse_config.py) ([`recursive_training/metrics/metrics_store.py:34`](../../recursive_training/metrics/metrics_store.py:34)): Used for loading configuration, with a fallback class defined if `PulseConfig` is unavailable.

### External Library Dependencies:
*   `json`: For serialization/deserialization of metrics, indices, and summary.
*   `logging`: For application logging.
*   `os`: For path existence checks.
*   `pickle`: Imported ([`recursive_training/metrics/metrics_store.py:12`](../../recursive_training/metrics/metrics_store.py:12)) but not visibly used.
*   `gzip`: Imported ([`recursive_training/metrics/metrics_store.py:13`](../../recursive_training/metrics/metrics_store.py:13)) for potential compression, but not visibly used in core read/write logic.
*   `hashlib`: Used for generating unique metric IDs via MD5 ([`_generate_metric_id()`](../../recursive_training/metrics/metrics_store.py:221)).
*   `datetime`: For timestamping metrics.
*   `pathlib.Path`: For path manipulations.
*   `typing`: For type hinting.
*   `collections.defaultdict`: Imported ([`recursive_training/metrics/metrics_store.py:18`](../../recursive_training/metrics/metrics_store.py:18)) but not visibly used.
*   `numpy` (optional): Checked for availability ([`recursive_training/metrics/metrics_store.py:21-24`](../../recursive_training/metrics/metrics_store.py:21-24)), but not directly used in the class methods shown.
*   `pandas` (optional): Checked for availability ([`recursive_training/metrics/metrics_store.py:27-30`](../../recursive_training/metrics/metrics_store.py:27-30)) and used in [`export_to_dataframe()`](../../recursive_training/metrics/metrics_store.py:585).

### Shared Data / File System Interactions:
*   **Input Files:**
    *   Reads configuration (implicitly via `PulseConfig` or passed dictionary).
    *   Loads `metrics_indices.json` from the `index_path` ([`recursive_training/metrics/metrics_store.py:141`](../../recursive_training/metrics/metrics_store.py:141)).
    *   Loads `metrics_summary.json` from the `meta_path` ([`recursive_training/metrics/metrics_store.py:168`](../../recursive_training/metrics/metrics_store.py:168)).
    *   Reads individual metric JSON files (e.g., `<metric_id>.json`) from subdirectories within `metrics_path`.
*   **Output Files:**
    *   Writes `metrics_indices.json` to `index_path` ([`recursive_training/metrics/metrics_store.py:159`](../../recursive_training/metrics/metrics_store.py:159)).
    *   Writes `metrics_summary.json` to `meta_path` ([`recursive_training/metrics/metrics_store.py:214`](../../recursive_training/metrics/metrics_store.py:214)).
    *   Writes individual metric JSON files to subdirectories within `metrics_path`.
*   **Logging:** Uses the standard Python `logging` module.

## 5. Function and Class Example Usages

The primary component is the `MetricsStore` class, typically used as a singleton.

```python
from recursive_training.metrics.metrics_store import get_metrics_store
from datetime import datetime, timezone

# Configuration (optional, defaults are provided)
config = {
    "metrics_path": "./my_custom_metrics_data",
    "enable_caching": True,
    "warning_cost_threshold": 15.0
}

# Get the singleton instance
metrics_store = get_metrics_store(config)

# 1. Storing a metric
training_metric_data = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "metric_type": "training_loss",
    "model": "alpha_v1",
    "epoch": 5,
    "value": 0.075,
    "tags": ["experiment_x", "run_001"]
}
metric_id = metrics_store.store_metric(training_metric_data)
print(f"Stored training metric with ID: {metric_id}")

# 2. Retrieving a metric
retrieved_metric = metrics_store.get_metric(metric_id)
if retrieved_metric:
    print(f"Retrieved metric: {retrieved_metric['metric_type']} - {retrieved_metric['value']}")

# 3. Querying metrics
queried_metrics = metrics_store.query_metrics(
    metric_types=["training_loss"],
    models=["alpha_v1"],
    tags=["experiment_x"],
    limit=5
)
print(f"Found {len(queried_metrics)} matching metrics.")
for m in queried_metrics:
    print(f" - {m['timestamp']}: {m['value']}")

# 4. Tracking costs
cost_details = metrics_store.track_cost(cost=0.25, api_calls=50, token_usage=15000)
print(f"Current total cost: ${cost_details['total_cost']:.2f}, Status: {cost_details['status']}")

# 5. Getting a summary of all metrics
summary = metrics_store.get_metrics_summary()
print(f"Total metrics stored: {summary['total_metrics']}")
print(f"Models tracked: {summary['models']}")

# 6. Exporting to pandas DataFrame (if pandas is installed)
# Ensure pandas is available or handle the None case
# df_metrics = metrics_store.export_to_dataframe(query={"tags": ["experiment_x"]})
# if df_metrics is not None:
#     print("Exported DataFrame head:")
#     print(df_metrics.head())

# 7. Get metrics by a specific filter dictionary
# cycle_metrics = metrics_store.get_metrics_by_filter({"cycle_id": "cycle_005"})

# 8. Get recent metrics
# recent_losses = metrics_store.get_recent_metrics(metric_types=["training_loss"], limit=3)

# 9. Close the store (saves pending indices/summary)
# metrics_store.close()
```

## 6. Hardcoding Issues

*   **Default Storage Path:** The `base_path` for metrics defaults to `"./data/recursive_training/metrics"` ([`recursive_training/metrics/metrics_store.py:103`](../../recursive_training/metrics/metrics_store.py:103)) if not specified in the configuration.
*   **File Names:** Index file (`metrics_indices.json` - [`recursive_training/metrics/metrics_store.py:141`](../../recursive_training/metrics/metrics_store.py:141)) and summary file (`metrics_summary.json` - [`recursive_training/metrics/metrics_store.py:168`](../../recursive_training/metrics/metrics_store.py:168)) names are hardcoded.
*   **Default Configuration Values:** Several parameters have hardcoded defaults within the `__init__` method if not provided via the `config` dictionary (e.g., `use_compression: True`, `max_cache_size: 1000`, cost thresholds like `warning_cost_threshold: 10.0`). See lines [`recursive_training/metrics/metrics_store.py:119-129`](../../recursive_training/metrics/metrics_store.py:119-129).
*   **Metric ID Subdirectory Prefix:** The subdirectory structure for storing individual metric files uses the first two characters of the metric ID (`metric_id[:2]`), as seen in [`_get_metric_path()`](../../recursive_training/metrics/metrics_store.py:253).
*   **Default "unknown" Values:** If `metric_type` or `model` are missing from metric data, they default to `"unknown"` during ID generation ([`recursive_training/metrics/metrics_store.py:233-234`](../../recursive_training/metrics/metrics_store.py:233-234)) and index updates ([`recursive_training/metrics/metrics_store.py:267,274`](../../recursive_training/metrics/metrics_store.py:267)).
*   **Cost Tracking Tag:** The `track_cost` method hardcodes the tag `["cost_tracking"]` for cost-related metrics ([`recursive_training/metrics/metrics_store.py:557`](../../recursive_training/metrics/metrics_store.py:557)).

## 7. Coupling Points

*   **`core.pulse_config.PulseConfig`:** The module is designed to integrate with `PulseConfig` for its configuration, creating a coupling point. However, it provides a fallback mechanism if `PulseConfig` is not available.
*   **File System Structure:** The store is tightly coupled to a specific directory structure (`data/`, `indices/`, `metadata/`) under its `base_path`. Changes to this organization would require code modifications.
*   **Data Serialization Format (JSON):** The choice of JSON for storing metrics, indices, and the summary file creates a dependency on this format. Migrating to another format would involve significant changes.
*   **Pandas (Optional):** The [`export_to_dataframe()`](../../recursive_training/metrics/metrics_store.py:585) method introduces an optional coupling with the pandas library.
*   **Metric Data Schema:** The internal logic (e.g., for indexing, summary updates, ID generation) implicitly expects certain keys in the `metric_data` dictionary (e.g., `timestamp`, `metric_type`, `model`, `tags`, `cost`).

## 8. Existing Tests

Test File: [`tests/recursive_training/test_metrics_store.py`](../../tests/recursive_training/test_metrics_store.py)

*   **Framework:** Uses `pytest` and `unittest.mock`.
*   **Coverage Overview:** The tests cover a significant portion of the `MetricsStore`'s functionality:
    *   Initialization ([`test_initialization()`](../../tests/recursive_training/test_metrics_store.py:88))
    *   Singleton pattern ([`test_singleton_pattern()`](../../tests/recursive_training/test_metrics_store.py:110))
    *   Metric ID generation ([`test_generate_metric_id()`](../../tests/recursive_training/test_metrics_store.py:148))
    *   Storing metrics ([`test_store_metric()`](../../tests/recursive_training/test_metrics_store.py:172))
    *   Retrieving metrics ([`test_get_metric()`](../../tests/recursive_training/test_metrics_store.py:194)) (cache and disk)
    *   Index updates ([`test_update_indices()`](../../tests/recursive_training/test_metrics_store.py:220))
    *   Summary updates ([`test_update_summary()`](../../tests/recursive_training/test_metrics_store.py:242)) (including cost tracking)
    *   Querying metrics ([`test_query_metrics()`](../../tests/recursive_training/test_metrics_store.py:288))
    *   Cost tracking and threshold checks ([`test_track_cost()`](../../tests/recursive_training/test_metrics_store.py:345))
    *   Getting metrics summary ([`test_get_metrics_summary()`](../../tests/recursive_training/test_metrics_store.py:417))
    *   Exporting to DataFrame ([`test_export_to_dataframe()`](../../tests/recursive_training/test_metrics_store.py:446))
*   **Nature of Tests:** Primarily unit tests that mock file system interactions (`os.path.exists`, `Path.mkdir`, `open`) and some internal methods to isolate the logic of the method under test.
*   **Potential Gaps or Problematic Tests:**
    *   **File System Integration:** Due to heavy mocking of file operations, dedicated integration tests ensuring the end-to-end file system interactions (directory creation, file persistence, loading from persisted state) might be beneficial.
    *   **Compression Feature:** The `use_compression` config option and `gzip` import suggest a compression feature, but its implementation and corresponding tests are not apparent.
    *   **Untested Methods:** As noted in "Implementation Gaps", `get_metrics_by_filter()` and `close()` lack dedicated tests.
    *   **Cache Eviction Logic:** The simplistic cache eviction logic is tested implicitly by checking cache presence after operations but not explicitly for its eviction behavior under load.

## 9. Module Architecture and Flow

*   **Singleton Design:** `MetricsStore` uses the singleton pattern, accessible via `MetricsStore.get_instance()` or `get_metrics_store()`, ensuring one central point for metric management.
*   **Configuration:** Initialization is driven by a configuration dictionary, falling back to `PulseConfig` if available, and providing defaults for many settings.
*   **Storage Mechanism:**
    *   Individual metrics are serialized as JSON and stored in separate files. These files are organized into a shallow directory structure based on the first two characters of their MD5 hash ID to avoid having too many files in a single directory.
    *   **Indices:** To facilitate efficient querying, several indices (`by_type`, `by_model`, `by_date`, `by_tag`) are maintained in a central `metrics_indices.json` file. These map criteria values to lists of metric IDs.
    *   **Summary:** A `metrics_summary.json` file keeps track of aggregate statistics like total metrics, counts per type, overall time range, unique models/tags, and cumulative costs.
*   **Caching:** An optional in-memory dictionary (`metrics_cache`) stores recently stored or retrieved metrics to reduce disk I/O.
*   **Core Data Flow:**
    1.  **Ingestion ([`store_metric()`](../../recursive_training/metrics/metrics_store.py:344), [`track_cost()`](../../recursive_training/metrics/metrics_store.py:538)):
        *   A metric dictionary is received.
        *   A unique ID is generated (if not provided).
        *   The metric is written to its dedicated JSON file.
        *   Relevant indices in `metrics_indices.json` are updated.
        *   `metrics_summary.json` is updated.
        *   The metric is added to the in-memory cache (if enabled).
    2.  **Retrieval ([`get_metric()`](../../recursive_training/metrics/metrics_store.py:391)):**
        *   Checks the cache first.
        *   If not in cache, loads from the corresponding JSON file on disk and populates the cache.
    3.  **Querying ([`query_metrics()`](../../recursive_training/metrics/metrics_store.py:424), [`get_metrics_by_filter()`](../../recursive_training/metrics/metrics_store.py:630)):
        *   `query_metrics` utilizes the loaded indices to find sets of matching metric IDs based on the provided criteria (type, model, tags, date). It then intersects these sets and retrieves the full data for the final list of IDs.
        *   `get_metrics_by_filter` retrieves all metrics and then filters them in memory.
    4.  **Export ([`export_to_dataframe()`](../../recursive_training/metrics/metrics_store.py:585)):**
        *   Uses `query_metrics` to fetch data, then converts it into a pandas DataFrame.

## 10. Naming Conventions

*   **Overall:** The module generally adheres to PEP 8 naming conventions.
*   **Classes:** `MetricsStore`, `PulseConfig` (PascalCase).
*   **Methods & Functions:** `store_metric`, `_load_indices`, `get_metrics_store` (snake_case, with `_` prefix for internal/protected methods).
*   **Variables:** `metric_data`, `base_path` (snake_case for local variables).
*   **Constants/Globals:** `NUMPY_AVAILABLE`, `PANDAS_AVAILABLE` (UPPER_SNAKE_CASE for module-level flags indicating dependency availability).
*   **Configuration Keys & File Names:** `metrics_path`, `metrics_indices.json` (snake_case).
*   **Clarity:** Names are generally descriptive and understandable. No significant deviations or potential AI assumption errors in naming were noted.