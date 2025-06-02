# Module Analysis: `iris/ingest_s3.py`

## 1. Module Intent/Purpose

The primary role of the [`iris/ingest_s3.py`](../../../iris/ingest_s3.py) module is to monitor a specified AWS S3 bucket for new data files (JSON or CSV). Upon detecting new files, it reads their content, processes them, and submits the data as tasks to a Celery worker queue for further ingestion and scoring. It also archives processed files to a separate "processed" prefix within the same S3 bucket.

## 2. Operational Status/Completeness

The module appears to be production-ready, as indicated by its docstring ("production-ready") and the implemented functionalities. It includes:
*   Configuration via environment variables.
*   Polling mechanism with a configurable interval.
*   Processing of both JSON and CSV file types.
*   Integration with Celery for asynchronous task processing.
*   Archiving of processed files.
*   Logging for operational visibility.
*   Basic error handling and graceful shutdown on `KeyboardInterrupt`.
*   Integration with Prometheus metrics.

There are no obvious TODO comments or major incomplete placeholders in the core logic.

## 3. Implementation Gaps / Unfinished Next Steps

*   **`IrisScraper` Usage:** The module imports and instantiates [`IrisScraper`](../../../iris/iris_scraper.py:10) ([`iris/ingest_s3.py:26`](../../../iris/ingest_s3.py:26)) but does not appear to use the `scraper` object. This could be dead code or an intended integration that was not completed.
*   **Robust Celery Error Handling:** While basic exception handling is present for S3 operations, error handling for Celery task submission ([`celery_app.send_task()`](../../../core/celery_app.py)) could be enhanced (e.g., retry mechanisms, dead-letter queue handling for persistent task failures).
*   **State Persistence for `seen` Files:** The `seen` set ([`iris/ingest_s3.py:27`](../../../iris/ingest_s3.py:27)) is in-memory. If the poller restarts, it will reprocess files that were already processed but not yet moved if the restart was quick, or it might miss files if it was down for a long time and many files arrived. For more robust exactly-once processing or distributed polling, a persistent tracking mechanism (e.g., database, S3 object tags, or relying solely on the existence in the processed prefix) might be considered. However, for a single poller instance, the current approach of moving files is a common and often sufficient pattern.
*   **Scalability of `list_objects_v2`:** For buckets with a very large number of objects, `list_objects_v2` might require pagination handling if more than 1000 objects match the prefix. The current implementation processes only the first page of results.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`ingestion.iris_scraper.IrisScraper`](../../../iris/iris_scraper.py:10)
*   [`core.celery_app.celery_app`](../../../core/celery_app.py)
*   [`core.metrics.start_metrics_server`](../../../core/metrics.py)

### External Library Dependencies:
*   `os` (for environment variables)
*   `time` (for polling interval)
*   `json` (for parsing JSON files)
*   `logging` (for application logging)
*   `csv` (for parsing CSV files)
*   `boto3` (AWS SDK for Python, for S3 interaction)
*   `threading` (for running metrics server in background)

### Interaction with Other Modules/Systems:
*   **AWS S3:** Reads files from a specified bucket/prefix and writes processed files to a different prefix.
*   **Celery:** Sends tasks (data from files) to a Celery queue named `"ingest_and_score_signal"` ([`iris/ingest_s3.py:41`](../../../iris/ingest_s3.py:41), [`iris/ingest_s3.py:47`](../../../iris/ingest_s3.py:47)).
*   **Prometheus:** Starts a metrics server using [`start_metrics_server()`](../../../core/metrics.py) ([`iris/ingest_s3.py:24`](../../../iris/ingest_s3.py:24)).

### Input/Output Files:
*   **Input:** `.json` and `.csv` files from the S3 bucket defined by `PULSE_S3_BUCKET` and `PULSE_S3_PREFIX`.
*   **Output:**
    *   Processed files are moved to `PULSE_S3_PROCESSED_PREFIX` in the S3 bucket.
    *   Logs are written to standard output/configured logging system.

## 5. Function and Class Example Usages

*   **[`poll_s3()`](../../../iris/ingest_s3.py:22):**
    *   This is the main function of the module.
    *   It initializes the S3 client and an [`IrisScraper`](../../../iris/iris_scraper.py:10) instance (though the scraper is not used).
    *   It starts a Prometheus metrics server in a background thread.
    *   It enters an infinite loop, polling the S3 bucket at `POLL_INTERVAL` seconds.
    *   It lists objects, reads new JSON/CSV files, sends their content to Celery, and moves them to a processed location.
    *   The script executes this function when run directly (`if __name__ == '__main__':`).
    ```python
    # This function is typically run as the main entry point of the script:
    # python iris/ingest_s3.py
    if __name__ == '__main__':
        poll_s3()
    ```

## 6. Hardcoding Issues

*   **`S3_BUCKET` Default Value:** The environment variable `PULSE_S3_BUCKET` defaults to `"your-bucket-name"` ([`iris/ingest_s3.py:15`](../../../iris/ingest_s3.py:15)). This is a placeholder and requires proper configuration via the environment variable for the module to function correctly.
*   **Celery Task Name:** The Celery task name `"ingest_and_score_signal"` is hardcoded ([`iris/ingest_s3.py:41`](../../../iris/ingest_s3.py:41), [`iris/ingest_s3.py:47`](../../../iris/ingest_s3.py:47)). While common, making this configurable (e.g., via an environment variable) could offer more flexibility if the target task name changes.
*   **Default Prefixes and Poll Interval:** `S3_PREFIX` (defaults to `""`), `S3_PROCESSED_PREFIX` (defaults to `"processed/"`), and `POLL_INTERVAL` (defaults to `"60"`) are configurable via environment variables, which is good. Their default values are generally reasonable but should be reviewed for specific deployments.

## 7. Coupling Points

*   **AWS S3:** The module is tightly coupled to AWS S3 services, using `boto3` for all S3 interactions (listing, reading, copying, deleting objects).
*   **Celery:** It's dependent on a running Celery infrastructure and a worker that can process tasks named `"ingest_and_score_signal"`. The specific Celery application is imported from [`core.celery_app`](../../../core/celery_app.py).
*   **Prometheus Metrics:** Relies on [`core.metrics.start_metrics_server()`](../../../core/metrics.py) for exposing metrics.
*   **Environment Variables:** Configuration is heavily reliant on environment variables (e.g., `PULSE_S3_BUCKET`, `PULSE_S3_PREFIX`, `PULSE_S3_PROCESSED_PREFIX`, `PULSE_S3_POLL_INTERVAL`).

## 8. Existing Tests

Based on the provided file list, there is no immediately visible dedicated test file for this module, such as `tests/iris/test_ingest_s3.py` or `tests/test_ingest_s3.py`. The actual state of tests would require inspecting the `tests/` directory more thoroughly or looking for integration tests that cover S3 ingestion.

## 9. Module Architecture and Flow

1.  **Initialization:**
    *   Load configuration from environment variables (S3 bucket, prefixes, poll interval).
    *   Set up logging.
    *   Instantiate `boto3.client('s3')`.
    *   Instantiate [`IrisScraper()`](../../../iris/iris_scraper.py:10) (currently unused).
    *   Initialize an empty set `seen` to track processed file keys.
    *   Start the Prometheus metrics server in a separate daemon thread.
2.  **Polling Loop:**
    *   The module enters an infinite `while True` loop.
    *   **List Objects:** Call `s3.list_objects_v2()` to get objects from `S3_BUCKET` with `S3_PREFIX`.
    *   **Iterate Objects:** For each object in the response:
        *   Skip if the object key is already in `seen` or if the file is not `.json` or `.csv`.
        *   **Process File:**
            *   Get the file object from S3 using `s3.get_object()`.
            *   Read and decode the file body.
            *   If JSON: Parse using `json.loads()`, send the resulting data to Celery task `"ingest_and_score_signal"`.
            *   If CSV: Parse using `csv.DictReader()`, iterate through rows, and send each row to Celery task `"ingest_and_score_signal"`.
            *   **Archive File:** Copy the object to the `S3_PROCESSED_PREFIX` and then delete the original object.
            *   Log the archival and add the key to the `seen` set.
        *   Catch and log exceptions during individual file processing.
    *   **Sleep:** Wait for `POLL_INTERVAL` seconds.
    *   **Error Handling:** Catch `KeyboardInterrupt` to stop polling gracefully. Catch other broad exceptions in the main loop, log them, and continue polling after a delay.

## 10. Naming Conventions

*   **Constants:** Uppercase with underscores (e.g., `S3_BUCKET`, `POLL_INTERVAL`) are used for module-level configurations loaded from environment variables, adhering to PEP 8.
*   **Functions:** Lowercase with underscores (e.g., [`poll_s3()`](../../../iris/ingest_s3.py:22)), adhering to PEP 8.
*   **Variables:** Generally lowercase with underscores (e.g., `file_obj`, `dest_key`). `obj` is used for S3 object summaries, which is common but could be more descriptive like `s3_object_summary`. `key` for S3 object key is standard.
*   **Logger Name:** The logger is named `"pulse.ingest_s3"` ([`iris/ingest_s3.py:20`](../../../iris/ingest_s3.py:20)), which provides good namespacing.
*   **Overall:** Naming conventions are largely consistent and follow Python community standards (PEP 8). No obvious AI assumption errors or significant deviations were noted.