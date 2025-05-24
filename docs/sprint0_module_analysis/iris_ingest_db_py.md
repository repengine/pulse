# Module Analysis: `iris/ingest_db.py`

## 1. Module Intent/Purpose

The primary role of the [`iris/ingest_db.py`](iris/ingest_db.py:) module is to periodically poll a configured database for new signal records. Upon finding new, unprocessed signals, it submits them to a Celery task queue for further processing (specifically, a task named `"ingest_and_score_signal"`) and then marks the records as processed in the database. The module is described as "production-ready."

## 2. Operational Status/Completeness

The module appears to be functionally complete for its defined purpose of polling and submitting tasks. It includes:
*   Configuration via environment variables with sensible defaults.
*   Database connection and querying using SQLAlchemy.
*   Submission of tasks to Celery.
*   Error handling for database operations and task submission.
*   Logging of significant events and errors.
*   Integration with Prometheus for metrics via [`core.metrics.start_metrics_server()`](core/metrics.py:).

No explicit "TODO" comments or obvious placeholders for core functionality are present in the provided code. However, an instance of [`IrisScraper`](iris/iris_scraper.py:) is created ([`iris/ingest_db.py:32`](iris/ingest_db.py:32)) but not used within the [`poll_database()`](iris/ingest_db.py:29) function, which might indicate incomplete integration or leftover code. Similarly, a variable `last_id` is initialized ([`iris/ingest_db.py:34`](iris/ingest_db.py:34)) but not subsequently used, potentially hinting at an abandoned or alternative polling strategy.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Unused `IrisScraper` and `last_id`:** The instantiation of [`IrisScraper`](iris/iris_scraper.py:) ([`iris/ingest_db.py:32`](iris/ingest_db.py:32)) without any apparent use and the initialized but unused `last_id` variable ([`iris/ingest_db.py:34`](iris/ingest_db.py:34)) suggest that the module might have had a slightly different or more extensive design initially. The `last_id` could have been part of a polling strategy to fetch records incrementally, though the current `WHERE processed=0` clause handles this differently.
*   **Limited Error Recovery:** While errors are logged, the recovery mechanism is generally to wait for the next `POLL_INTERVAL` ([`iris/ingest_db.py:55`](iris/ingest_db.py:55), [`iris/ingest_db.py:58`](iris/ingest_db.py:58), [`iris/ingest_db.py:64`](iris/ingest_db.py:64)). More sophisticated retry logic, backoff strategies, or dead-letter queuing for persistently failing signals are not implemented.
*   **Backpressure Handling:** There's no explicit mechanism to handle backpressure if the Celery queue is overwhelmed or if downstream processing is slow. The module will continue to poll and submit tasks at the defined interval.
*   **Scalability of Polling:** For very high-volume signal databases, a simple polling mechanism might become a bottleneck or inefficient. Event-driven mechanisms (e.g., database triggers, message queues populated by the DB) could be more scalable alternatives, though this would be a significant architectural change.
*   **Dynamic Configuration:** Configuration is loaded at startup. There's no mechanism for dynamic reconfiguration (e.g., changing `POLL_INTERVAL` or `SIGNAL_QUERY`) without restarting the poller.

## 4. Connections & Dependencies

*   **Direct Imports from Other Project Modules:**
    *   [`iris.iris_scraper.IrisScraper`](iris/iris_scraper.py:) (instantiated but unused in `poll_database`)
    *   [`core.celery_app.celery_app`](core/celery_app.py:) (used to send tasks)
    *   [`core.metrics.start_metrics_server`](core/metrics.py:) (used to start Prometheus metrics endpoint)
*   **External Library Dependencies:**
    *   `os` (for environment variables)
    *   `time` (for `sleep`)
    *   `logging` (for application logging)
    *   `sqlalchemy` (for database interaction: [`create_engine`](iris/ingest_db.py:8), [`text`](iris/ingest_db.py:8), [`SQLAlchemyError`](iris/ingest_db.py:9))
    *   `threading` (to run metrics server in a background thread)
*   **Interaction with Other Modules via Shared Data:**
    *   **Database:** Reads from and writes to a SQL database (table `signals`, columns `id`, `name`, `value`, `source`, `timestamp`, `processed`). The database URL is configured by `PULSE_DB_URL` ([`iris/ingest_db.py:15`](iris/ingest_db.py:15)).
    *   **Celery Message Queue:** Submits tasks to a Celery worker via the `ingest_and_score_signal` task name ([`iris/ingest_db.py:50`](iris/ingest_db.py:50)).
*   **Input/Output Files:**
    *   **Input:** Data rows from the `signals` table in the configured database.
    *   **Output:**
        *   Log messages (standard output/error or configured logging system).
        *   Tasks sent to the Celery message broker.
        *   Metrics exposed via a Prometheus endpoint.

## 5. Function and Class Example Usages

The module primarily defines one function:

*   **[`poll_database()`](iris/ingest_db.py:29):**
    This function is the core of the module. It initializes a database connection and enters an infinite loop to:
    1.  Query the database for unprocessed signals using `SIGNAL_QUERY`.
    2.  For each retrieved signal, format it into a dictionary.
    3.  Send this dictionary as an argument to the Celery task `"ingest_and_score_signal"`.
    4.  Mark the signal as processed in the database using `MARK_PROCESSED_QUERY`.
    5.  Sleep for `POLL_INTERVAL` seconds before repeating.
    It also starts a Prometheus metrics server in a background thread.

    **Usage (as a standalone script):**
    ```bash
    python iris/ingest_db.py
    ```
    Environment variables like `PULSE_DB_URL`, `PULSE_DB_POLL_INTERVAL`, `PULSE_DB_QUERY`, and `PULSE_DB_MARK_PROCESSED` can be set to customize its behavior.

## 6. Hardcoding Issues

*   **Default Configuration Values:**
    *   `DB_URL`: Defaults to `"sqlite:///pulse_signals.db"` ([`iris/ingest_db.py:15`](iris/ingest_db.py:15)).
    *   `POLL_INTERVAL`: Defaults to `60` seconds ([`iris/ingest_db.py:16`](iris/ingest_db.py:16)).
    *   `SIGNAL_QUERY`: Defaults to `"SELECT id, name, value, source, timestamp FROM signals WHERE processed=0 ORDER BY id ASC"` ([`iris/ingest_db.py:17-20`](iris/ingest_db.py:17-20)). This query hardcodes the table name (`signals`) and column names.
    *   `MARK_PROCESSED_QUERY`: Defaults to `"UPDATE signals SET processed=1 WHERE id=:id"` ([`iris/ingest_db.py:21-24`](iris/ingest_db.py:21-24)). This also hardcodes the table name and column names.
*   **Celery Task Name:** The task name `"ingest_and_score_signal"` is hardcoded ([`iris/ingest_db.py:50`](iris/ingest_db.py:50)).
*   **Logger Name:** The logger name `"pulse.ingest_db"` is hardcoded ([`iris/ingest_db.py:27`](iris/ingest_db.py:27)).
*   **Signal Data Keys:** The keys used in `signal_data` dictionary (`"name"`, `"value"`, `"source"`, `"timestamp"`) are derived from the database query structure but are effectively hardcoded expectations for the Celery task ([`iris/ingest_db.py:44-49`](iris/ingest_db.py:44-49)).

While most of these are configurable via environment variables, the default SQL queries embed schema details (table and column names) directly.

## 7. Coupling Points

*   **Database Schema:** Tightly coupled to the `signals` table schema (name, existence of columns `id`, `name`, `value`, `source`, `timestamp`, `processed`, and their types). Changes here would break the default queries.
*   **Celery Task Contract:** Tightly coupled to the Celery task named `"ingest_and_score_signal"` and its expected input argument structure (a dictionary with keys `name`, `value`, `source`, `timestamp`).
*   **`core.celery_app`:** Relies on the availability and correct configuration of the Celery application instance.
*   **`core.metrics`:** Depends on the [`start_metrics_server()`](core/metrics.py:) function from this module.

## 8. Existing Tests

*   Based on the provided file list, there does not appear to be a dedicated test file for [`iris/ingest_db.py`](iris/ingest_db.py:) (e.g., `tests/iris/test_ingest_db.py`).
*   While general test infrastructure like [`tests/conftest.py`](tests/conftest.py:) and [`iris/conftest.py`](iris/conftest.py:) exists, specific tests for this module's logic (database polling, task submission, error handling) are not evident.
*   **Assessment:** The module likely has limited or no direct unit or integration tests. Testing would require mocking database interactions (SQLAlchemy engine, connection, result proxy), Celery's `send_task` method, and potentially the metrics server startup.

## 9. Module Architecture and Flow

1.  **Configuration:**
    *   Environment variables `PULSE_DB_URL`, `PULSE_DB_POLL_INTERVAL`, `PULSE_DB_QUERY`, `PULSE_DB_MARK_PROCESSED` are read, with defaults provided.
2.  **Initialization (within `poll_database`):**
    *   A Prometheus metrics server is started in a background thread using [`threading.Thread()`](iris/ingest_db.py:12) and [`core.metrics.start_metrics_server()`](core/metrics.py:).
    *   An [`IrisScraper`](iris/iris_scraper.py:) instance is created (currently unused).
    *   A SQLAlchemy engine is created using `DB_URL`.
    *   Logging is configured.
3.  **Main Polling Loop:**
    *   The function enters an infinite `while True` loop.
    *   **Database Interaction:**
        *   A connection is established to the database.
        *   The `SIGNAL_QUERY` is executed to fetch unprocessed rows.
        *   For each `row` retrieved:
            *   A `signal_data` dictionary is constructed from row elements.
            *   The `signal_data` is sent to the Celery task `"ingest_and_score_signal"` via [`celery_app.send_task()`](core/celery_app.py:).
            *   A log message confirms the submission.
            *   The `MARK_PROCESSED_QUERY` is executed to update the `processed` status of the row in the database, using the row's ID.
            *   Exceptions during this inner loop (e.g., Celery submission failure) are caught, logged, but do not stop processing of other rows or the main loop.
    *   **Sleep:** The loop pauses for `POLL_INTERVAL` seconds.
    *   **Error Handling (Outer Loop):**
        *   `SQLAlchemyError` exceptions are caught, logged, and the loop continues after sleeping.
        *   `KeyboardInterrupt` allows graceful shutdown.
        *   Any other `Exception` is caught, logged, and the loop continues after sleeping.
4.  **Script Execution:**
    *   If the module is run as `__main__`, the [`poll_database()`](iris/ingest_db.py:29) function is called.

## 10. Naming Conventions

*   **Constants:** Uppercase with underscores (e.g., `DB_URL`, `POLL_INTERVAL`, `SIGNAL_QUERY`), following PEP 8.
*   **Functions:** Lowercase with underscores (e.g., [`poll_database`](iris/ingest_db.py:29)), following PEP 8.
*   **Variables:** Lowercase with underscores (e.g., `engine`, `scraper`, `signal_data`), following PEP 8.
*   **Logger Name:** `"pulse.ingest_db"` is descriptive and uses dot notation common for hierarchical loggers.
*   **Celery Task Name:** `"ingest_and_score_signal"` is descriptive.
*   The naming is generally consistent and adheres to Python conventions (PEP 8). No significant deviations or potential AI assumption errors in naming are apparent.