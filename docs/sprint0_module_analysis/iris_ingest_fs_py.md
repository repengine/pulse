# Module Analysis: `iris/ingest_fs.py`

## 1. Module Intent/Purpose

The primary role of the [`iris/ingest_fs.py`](iris/ingest_fs.py) module is to monitor a specified directory on the file system for newly created JSON or CSV files. Upon detecting a new file, it reads its content and dispatches it as tasks to a Celery worker queue (task name: `"ingest_and_score_signal"`) for further processing. Successfully processed files are then moved to a designated archive directory. The module also initiates a Prometheus metrics server for monitoring.

## 2. Operational Status/Completeness

The module is described as "production-ready" in its docstring. It implements core functionalities such as file detection, parsing for supported types (JSON, CSV), task submission to Celery, file archival, and basic error logging. No obvious TODOs or placeholder code sections are apparent, suggesting a complete state for its defined scope.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Expanded File Type Support:** Currently handles only `.json` and `.csv` files. Support for other data formats (e.g., XML, Parquet, plain text) could be a future enhancement. The current handling for unsupported files ([`iris/ingest_fs.py:42-44`](iris/ingest_fs.py:42-44)) is to log a warning and skip.
*   **Granular Error Handling for CSVs:** If sending a single row from a CSV file to Celery fails, the module logs the error and continues with subsequent rows. A more robust error handling strategy might involve retries for failed rows or a mechanism to quarantine problematic files/rows.
*   **Configuration of Celery Task Name:** The Celery task name `"ingest_and_score_signal"` is hardcoded ([`iris/ingest_fs.py:34`](iris/ingest_fs.py:34), [`iris/ingest_fs.py:40`](iris/ingest_fs.py:40)). Making this configurable (e.g., via environment variables) would increase flexibility.
*   **`IrisScraper` Utility:** An [`IrisScraper`](iris/iris_scraper.py) object is instantiated ([`iris/ingest_fs.py:56`](iris/ingest_fs.py:56)) but not actively used within the `SignalFileHandler.on_created` method's logic for file processing. Its purpose in this specific module is unclear.
*   **Detailed Metrics:** While a Prometheus metrics server is started ([`iris/ingest_fs.py:55`](iris/ingest_fs.py:55) using [`core.metrics.start_metrics_server`](core/metrics.py)), the specific metrics exposed by this module (e.g., number of files processed, types of files, errors encountered, processing times) are not detailed within this module's code.

## 4. Connections & Dependencies

### Direct Project Module Imports:
*   [`iris.iris_scraper.IrisScraper`](iris/iris_scraper.py) ([`iris/ingest_fs.py:10`](iris/ingest_fs.py:10))
*   [`core.celery_app.celery_app`](core/celery_app.py) ([`iris/ingest_fs.py:13`](iris/ingest_fs.py:13))
*   [`core.metrics.start_metrics_server`](core/metrics.py) ([`iris/ingest_fs.py:14`](iris/ingest_fs.py:14))

### External Library Dependencies:
*   `os` (Python Standard Library)
*   `time` (Python Standard Library)
*   `json` (Python Standard Library)
*   `shutil` (Python Standard Library)
*   `logging` (Python Standard Library)
*   `csv` (Python Standard Library)
*   `watchdog` (for file system monitoring)
*   `threading` (Python Standard Library)

### Interactions via Shared Data:
*   **Celery Message Broker:** Sends tasks and data (file contents) to Celery workers.
*   **File System:**
    *   Reads files from `MONITOR_DIR` (env: `PULSE_FS_MONITOR_DIR`, default: `data/incoming`).
    *   Moves processed files to `ARCHIVE_DIR` (env: `PULSE_FS_ARCHIVE_DIR`, default: `data/ingested`).

### Input/Output Files:
*   **Input:** `.json` and `.csv` files arriving in `MONITOR_DIR`.
*   **Output:**
    *   Moves input files to `ARCHIVE_DIR` after processing.
    *   Generates logs via the `logging` module.

## 5. Function and Class Example Usages

*   **`SignalFileHandler(FileSystemEventHandler)` Class:**
    *   Inherits from `watchdog.events.FileSystemEventHandler`.
    *   **`__init__(self, scraper)`:** Initializes the handler, taking an `IrisScraper` instance (though `scraper` is not used in `on_created`). Ensures the `ARCHIVE_DIR` exists.
    *   **`on_created(self, event)`:** This method is triggered when a new file is created in the monitored directory.
        *   It ignores directory creation events.
        *   For `.json` files ([`iris/ingest_fs.py:31-35`](iris/ingest_fs.py:31-35)): Reads the file, parses JSON content, and sends the entire data structure as a single Celery task.
        *   For `.csv` files ([`iris/ingest_fs.py:36-41`](iris/ingest_fs.py:36-41)): Reads the CSV file row by row, treating each row as a dictionary, and sends each row as an individual Celery task.
        *   After successfully submitting tasks to Celery, it moves the source file to `ARCHIVE_DIR` ([`iris/ingest_fs.py:46-49`](iris/ingest_fs.py:46-49)).
        *   Logs errors if file processing or Celery submission fails.

*   **`monitor_directory(path=MONITOR_DIR)` Function:**
    *   The main entry point for starting the monitoring service ([`iris/ingest_fs.py:53-67`](iris/ingest_fs.py:53-67)).
    *   Starts the Prometheus metrics server in a background daemon thread.
    *   Instantiates `IrisScraper` and `SignalFileHandler`.
    *   Creates a `watchdog.observers.Observer` instance.
    *   Schedules the `SignalFileHandler` to monitor the specified `path` (non-recursively).
    *   Starts the observer.
    *   Enters an infinite loop (`while True: time.sleep(1)`), waiting for a `KeyboardInterrupt` to stop the observer and terminate.
    *   This function is called if the script is executed directly (`if __name__ == '__main__':`).

## 6. Hardcoding Issues

*   **Default Directory Paths:**
    *   `MONITOR_DIR` defaults to `"data/incoming"` ([`iris/ingest_fs.py:17`](iris/ingest_fs.py:17)).
    *   `ARCHIVE_DIR` defaults to `"data/ingested"` ([`iris/ingest_fs.py:18`](iris/ingest_fs.py:18)).
    (These are configurable via `PULSE_FS_MONITOR_DIR` and `PULSE_FS_ARCHIVE_DIR` environment variables).
*   **Celery Task Name:** The string `"ingest_and_score_signal"` is hardcoded for Celery task submission ([`iris/ingest_fs.py:34`](iris/ingest_fs.py:34), [`iris/ingest_fs.py:40`](iris/ingest_fs.py:40)).
*   **Logger Name:** The logger name `"pulse.ingest_fs"` is hardcoded ([`iris/ingest_fs.py:20`](iris/ingest_fs.py:20)).
*   **Supported File Extensions:** `".json"` and `".csv"` are hardcoded ([`iris/ingest_fs.py:31`](iris/ingest_fs.py:31), [`iris/ingest_fs.py:36`](iris/ingest_fs.py:36)).
*   **Sleep Interval:** `time.sleep(1)` in the main monitoring loop ([`iris/ingest_fs.py:64`](iris/ingest_fs.py:64)) is hardcoded.

## 7. Coupling Points

*   **`core.celery_app`:** Tightly coupled for dispatching tasks. Changes to Celery configuration or the specific task name (`"ingest_and_score_signal"`) would necessitate changes in this module.
*   **`core.metrics`:** Coupled for initiating the metrics server via `start_metrics_server`.
*   **`iris.iris_scraper`:** Loosely coupled. An instance is created and passed to `SignalFileHandler`, but its methods are not directly invoked in the file processing logic shown.
*   **File System Structure:** Relies on the existence and accessibility of `MONITOR_DIR` and `ARCHIVE_DIR`.
*   **Data Format Contract:** Implicitly expects that the data within the JSON and CSV files conforms to a structure that the downstream Celery task (`"ingest_and_score_signal"`) can process.

## 8. Existing Tests

Based on the provided file listing, there does not appear to be a dedicated test file (e.g., `tests/test_iris_ingest_fs.py` or `tests/iris/test_ingest_fs.py`) for this module. While `iris/conftest.py` exists, specific tests for `ingest_fs.py` are not evident.
*   **Assessment:** Likely no direct unit or integration tests exist for this module. Testing would typically involve mocking file system events (`watchdog`), Celery interactions (`celery_app.send_task`), file operations (`open`, `shutil.move`), and potentially the `IrisScraper` and `start_metrics_server` dependencies.

## 9. Module Architecture and Flow

1.  **Initialization:**
    *   Configure `MONITOR_DIR` and `ARCHIVE_DIR` from environment variables or defaults.
    *   Set up logging for `pulse.ingest_fs`.
    *   The `SignalFileHandler` ensures `ARCHIVE_DIR` exists upon instantiation.
2.  **Monitoring Setup (`monitor_directory`):**
    *   Start the Prometheus metrics server in a background thread.
    *   Instantiate `IrisScraper`.
    *   Instantiate `SignalFileHandler` (event handler).
    *   Instantiate `watchdog.observers.Observer`.
    *   Schedule the observer to watch `MONITOR_DIR` using `SignalFileHandler`.
    *   Start the observer thread.
3.  **Event Handling (`SignalFileHandler.on_created`):**
    *   Triggered by `watchdog` upon new file creation in `MONITOR_DIR`.
    *   Ignores directory events.
    *   Determines file type by extension:
        *   **`.json`:** Read file, parse JSON, send data to Celery task `"ingest_and_score_signal"`.
        *   **`.csv`:** Read file, parse CSV, send each row as data to Celery task `"ingest_and_score_signal"`.
        *   **Other:** Log warning and skip.
    *   If Celery submission is successful, move the processed file to `ARCHIVE_DIR`.
    *   Log any exceptions during processing.
4.  **Main Loop & Termination (`monitor_directory`):**
    *   The main thread enters a `while True: time.sleep(1)` loop to keep the program alive.
    *   A `KeyboardInterrupt` (Ctrl+C) stops the observer and allows graceful shutdown.

## 10. Naming Conventions

*   **Constants:** `MONITOR_DIR`, `ARCHIVE_DIR` use `UPPER_CASE_SNAKE_CASE` (PEP 8).
*   **Classes:** `SignalFileHandler` uses `CapWords` (PascalCase) (PEP 8).
*   **Functions/Methods:** `monitor_directory`, `on_created`, `__init__` use `lower_case_snake_case` (PEP 8).
*   **Variables:** `logger`, `scraper`, `event_handler`, `observer`, `ext`, `data`, `archive_path` use `lower_case_snake_case`.
*   **Overall:** Naming is consistent and adheres well to PEP 8 guidelines. No significant deviations or potential AI assumption errors in naming were observed.