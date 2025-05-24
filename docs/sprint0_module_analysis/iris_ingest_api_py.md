# Module Analysis: `iris/ingest_api.py`

## 1. Module Intent/Purpose

The primary role of the [`iris/ingest_api.py`](../../iris/ingest_api.py:1) module is to provide a production-ready HTTP API endpoint for ingesting external signals (data points) into the Pulse system. It uses FastAPI for building the API and Celery for asynchronous processing of these signals.

## 2. Operational Status/Completeness

The module appears to be operationally complete for its core function of receiving signals via HTTP and dispatching them for further processing.
- It includes essential features like API key authentication ([`iris/ingest_api.py:31-35`](../../iris/ingest_api.py:31-35)).
- Health check ([`iris/ingest_api.py:37-39`](../../iris/ingest_api.py:37-39)) and Prometheus metrics ([`iris/ingest_api.py:41-48`](../../iris/ingest_api.py:41-48)) endpoints are implemented.
- Signal ingestion supports both single ([`iris/ingest_api.py:50-65`](../../iris/ingest_api.py:50-65)) and batch ([`iris/ingest_api.py:67-82`](../../iris/ingest_api.py:67-82)) submissions.
- Asynchronous processing is handled by sending tasks to Celery ([`iris/ingest_api.py:53`](../../iris/ingest_api.py:53), [`iris/ingest_api.py:72`](../../iris/ingest_api.py:72)).
- No explicit TODOs or obvious placeholders are present in the code.

## 3. Implementation Gaps / Unfinished Next Steps

- **`IrisScraper` Usage:** An instance of `IrisScraper` ([`iris/iris_scraper.py:6`](../../iris/iris_scraper.py:6)) is created ([`iris/ingest_api.py:23`](../../iris/ingest_api.py:23)) but not directly utilized within the API endpoint handlers. Its role in this module or in the downstream Celery task (`ingest_and_score_signal`) is not evident from this file alone.
- **Celery Task Details:** The module relies on a Celery task named `"ingest_and_score_signal"` ([`iris/ingest_api.py:53`](../../iris/ingest_api.py:53)). The specifics of this task (e.g., scoring logic, error handling within the task) are external to this module and represent a logical next step for understanding the full ingestion pipeline.
- **Error Handling Granularity:** Error handling for Celery task submission ([`iris/ingest_api.py:56-64`](../../iris/ingest_api.py:56-64), [`iris/ingest_api.py:74-81`](../../iris/ingest_api.py:74-81)) catches generic `Exception`. More specific exceptions could be caught for finer-grained error reporting or retry logic.
- **Configuration Management:** Some values like the Celery task name are hardcoded. These could be made configurable.

## 4. Connections & Dependencies

### Direct Project Module Imports
- [`iris.iris_scraper.IrisScraper`](../../iris/iris_scraper.py:6): For scraping functionalities (though not directly used in API handlers).
- [`core.celery_app.celery_app`](../../core/celery_app.py): The Celery application instance for task queuing.
- [`core.metrics.start_metrics_server`](../../core/metrics.py): Function to start the Prometheus metrics server.

### External Library Dependencies
- `os`: For environment variable access (e.g., `PULSE_API_KEY` ([`iris/ingest_api.py:17`](../../iris/ingest_api.py:17))).
- `logging`: For application logging.
- `fastapi`: The web framework used to build the API.
- `pydantic`: For data validation and settings management (used for `SignalIn` model ([`iris/ingest_api.py:25`](../../iris/ingest_api.py:25))).
- `typing`: For type hints.
- `uvicorn`: ASGI server for running FastAPI.
- `prometheus_client`: For generating Prometheus metrics.
- `threading`: Used to run the metrics server in a background thread.

### Interactions via Shared Data
- **Celery Task Queue:** Submits tasks (signal data) to a Celery message broker for asynchronous processing by worker nodes.
- **Prometheus:** Exposes a `/metrics` endpoint ([`iris/ingest_api.py:46-48`](../../iris/ingest_api.py:46-48)) for a Prometheus server to scrape.

### Input/Output Files
- **Logs:** Writes logs via the standard `logging` module. The logger is named `pulse.ingest_api` ([`iris/ingest_api.py:20`](../../iris/ingest_api.py:20)).
- **Environment Variables:** Reads `PULSE_API_KEY` ([`iris/ingest_api.py:17`](../../iris/ingest_api.py:17)) for API authentication.

## 5. Function and Class Example Usages

### `SignalIn(BaseModel)` ([`iris/ingest_api.py:25-29`](../../iris/ingest_api.py:25-29))
Defines the data structure for an incoming signal.
```python
class SignalIn(BaseModel):
    name: str
    value: float
    source: Optional[str] = "api"
    timestamp: Optional[str] = None
```
**Example JSON payload for `/ingest`:**
```json
{
  "name": "temperature_sensor_1",
  "value": 23.5,
  "source": "iot_device_cluster_A",
  "timestamp": "2024-05-16T10:00:00Z"
}
```

### API Endpoints
- **`GET /health` ([`iris/ingest_api.py:37-39`](../../iris/ingest_api.py:37-39)):**
  - Purpose: Check the health status of the API.
  - Usage: `curl http://localhost:8000/health`
  - Response: `{"status": "ok"}`

- **`GET /metrics` ([`iris/ingest_api.py:46-48`](../../iris/ingest_api.py:46-48)):**
  - Purpose: Expose Prometheus metrics.
  - Usage: `curl http://localhost:8000/metrics`
  - Response: Prometheus metrics data.

- **`POST /ingest` ([`iris/ingest_api.py:50-65`](../../iris/ingest_api.py:50-65)):**
  - Purpose: Ingest a single signal.
  - Headers: `x-api-key: <your_api_key>`
  - Body: JSON object matching the `SignalIn` model.
  - Usage:
    ```bash
    curl -X POST http://localhost:8000/ingest \
    -H "Content-Type: application/json" \
    -H "x-api-key: changeme" \
    -d '{"name": "signal_x", "value": 123.45}'
    ```
  - Response: `{"status": "submitted"}` or error details.

- **`POST /ingest_batch` ([`iris/ingest_api.py:67-82`](../../iris/ingest_api.py:67-82)):**
  - Purpose: Ingest a batch of signals.
  - Headers: `x-api-key: <your_api_key>`
  - Body: JSON array of objects, each matching the `SignalIn` model.
  - Usage:
    ```bash
    curl -X POST http://localhost:8000/ingest_batch \
    -H "Content-Type: application/json" \
    -H "x-api-key: changeme" \
    -d '[{"name": "signal_y", "value": 0.88}, {"name": "signal_z", "value": -10.2}]'
    ```
  - Response: `{"results": [{"name": "signal_y", "status": "submitted"}, ...]}`

## 6. Hardcoding Issues

- **Default API Key:** `API_KEY = os.getenv("PULSE_API_KEY", "changeme")` ([`iris/ingest_api.py:17`](../../iris/ingest_api.py:17)). The default value `"changeme"` is insecure and intended for development; it must be overridden by the environment variable in production.
- **Celery Task Name:** The string `"ingest_and_score_signal"` ([`iris/ingest_api.py:53`](../../iris/ingest_api.py:53), [`iris/ingest_api.py:72`](../../iris/ingest_api.py:72)) is hardcoded. This could be sourced from configuration for flexibility.
- **Default Signal Source:** In the `SignalIn` model, `source` defaults to `"api"` ([`iris/ingest_api.py:28`](../../iris/ingest_api.py:28)). While reasonable, this is a hardcoded default.
- **Uvicorn Host/Port (Development):** In the `if __name__ == "__main__":` block ([`iris/ingest_api.py:84-85`](../../iris/ingest_api.py:84-85)), `host="0.0.0.0"` and `port=8000` are hardcoded. This is standard for direct script execution during development but would typically be managed by a process manager or container configuration in production.

## 7. Coupling Points

- **Celery ([`core/celery_app.py`](../../core/celery_app.py)):** Tightly coupled for asynchronous task dispatch. The API's primary function of signal processing relies on Celery workers.
- **Metrics ([`core/metrics.py`](../../core/metrics.py)):** Depends on this module to start the Prometheus metrics server.
- **`IrisScraper` ([`iris/iris_scraper.py`](../../iris/iris_scraper.py)):** An instance is created, implying a dependency, though its direct use in API handlers is not shown. The coupling might exist within the downstream Celery task.
- **FastAPI Framework:** The entire module structure and operation are built upon FastAPI.
- **Pydantic:** Used for request body validation, tightly integrating data structure definitions.

## 8. Existing Tests

- A specific test file for this module (e.g., `tests/iris/test_ingest_api.py`) is not immediately visible in the provided file listing.
- The directory [`tests/api/`](../../tests/api/) exists and contains [`conftest.py`](../../tests/api/conftest.py:None), suggesting API tests are present in the project.
- Without access to the specific test files, it's not possible to assess coverage or the nature of existing tests for `iris/ingest_api.py`.
- Typical tests would involve:
    - Using FastAPI's `TestClient`.
    - Mocking `celery_app.send_task` to verify it's called with correct arguments.
    - Testing authentication (valid and invalid API keys).
    - Testing request validation for `SignalIn` (correct and malformed payloads).
    - Testing `/health` and `/metrics` endpoints.

## 9. Module Architecture and Flow

1.  **Initialization:**
    -   Imports necessary libraries and project modules.
    -   Sets up logging.
    -   Retrieves `PULSE_API_KEY` from environment or uses a default.
    -   Creates a FastAPI `app` instance.
    -   Instantiates `IrisScraper` (though not directly used in handlers).
2.  **Pydantic Model:**
    -   `SignalIn` ([`iris/ingest_api.py:25-29`](../../iris/ingest_api.py:25-29)) defines the expected JSON structure for incoming signals.
3.  **API Key Authentication:**
    -   `get_api_key` ([`iris/ingest_api.py:31-35`](../../iris/ingest_api.py:31-35)) function, used as a dependency, validates the `x-api-key` header.
4.  **Startup Event:**
    -   `@app.on_event("startup")` ([`iris/ingest_api.py:41-44`](../../iris/ingest_api.py:41-44)): Starts the Prometheus metrics server ([`core.metrics.start_metrics_server`](../../core/metrics.py)) in a background thread.
5.  **API Endpoints:**
    -   `GET /health` ([`iris/ingest_api.py:37-39`](../../iris/ingest_api.py:37-39)): Returns a static "ok" status.
    -   `GET /metrics` ([`iris/ingest_api.py:46-48`](../../iris/ingest_api.py:46-48)): Returns Prometheus metrics.
    -   `POST /ingest` ([`iris/ingest_api.py:50-65`](../../iris/ingest_api.py:50-65)):
        -   Requires API key.
        -   Accepts a single `SignalIn` object.
        -   Sends the signal data to the Celery task `"ingest_and_score_signal"`.
        -   Returns a submission status.
    -   `POST /ingest_batch` ([`iris/ingest_api.py:67-82`](../../iris/ingest_api.py:67-82)):
        -   Requires API key.
        -   Accepts a list of `SignalIn` objects.
        -   Iterates through signals, sending each to the Celery task.
        -   Returns a list of submission statuses.
6.  **Main Execution Block:**
    -   `if __name__ == "__main__":` ([`iris/ingest_api.py:84-85`](../../iris/ingest_api.py:84-85)): Runs the FastAPI application using Uvicorn, typically for development.

**Data Flow:**
External Client -> HTTP POST Request (`/ingest` or `/ingest_batch` with JSON payload and API key) -> FastAPI App -> API Key Auth -> Pydantic Validation -> Celery Task Submission (`ingest_and_score_signal`) -> Celery Worker (external processing) -> HTTP Response (submission status).

## 10. Naming Conventions

- **Overall:** The module generally adheres to Python's PEP 8 naming conventions.
- **Variables:** `snake_case` (e.g., `api_key`, `celery_app`, `signal_data`).
- **Functions/Methods:** `snake_case` (e.g., [`get_api_key()`](../../iris/ingest_api.py:31), [`ingest_signal()`](../../iris/ingest_api.py:51)).
- **Classes:** `PascalCase` (e.g., [`SignalIn`](../../iris/ingest_api.py:25)).
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `API_KEY` ([`iris/ingest_api.py:17`](../../iris/ingest_api.py:17))).
- **Clarity:** Names are generally descriptive and understandable (e.g., `app`, `logger`, `scraper`).
- **No major deviations or AI assumption errors in naming were observed.**