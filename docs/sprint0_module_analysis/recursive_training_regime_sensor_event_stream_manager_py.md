# Module Analysis: `recursive_training/regime_sensor/event_stream_manager.py`

## 1. Module Intent/Purpose

The primary role of the [`event_stream_manager.py`](recursive_training/regime_sensor/event_stream_manager.py:1) module is to provide a robust system for ingesting, processing, and managing real-time external event streams. These events, such as news headlines, corporate announcements, market movements, and economic indicators, are crucial for detecting potential regime shifts. The module is designed to handle events with varying priorities, filter them based on defined criteria, and distribute them to registered handlers for further analysis or action. It also supports persistent storage of ingested events.

## 2. Operational Status/Completeness

The module appears to be largely functional and reasonably complete for its core responsibilities. Key features implemented include:
*   Event representation ([`Event`](recursive_training/regime_sensor/event_stream_manager.py:42) class) with priority ([`EventPriority`](recursive_training/regime_sensor/event_stream_manager.py:23)) and type ([`EventType`](recursive_training/regime_sensor/event_stream_manager.py:31)) definitions.
*   A central [`EventStreamManager`](recursive_training/regime_sensor/event_stream_manager.py:138) class.
*   Priority queue for event handling.
*   Registration mechanism for event handlers and filters.
*   Asynchronous event processing using a separate thread.
*   Event serialization to JSON and storage to disk.
*   Basic mock event generation for testing ([`create_mock_news_event`](recursive_training/regime_sensor/event_stream_manager.py:372)).

One area explicitly marked as a placeholder is the entity extraction logic within [`_extract_entities_from_headline()`](recursive_training/regime_sensor/event_stream_manager.py:401), which currently uses simple regex and notes the need for more advanced NLP techniques.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Advanced Entity Extraction:** The current [`_extract_entities_from_headline()`](recursive_training/regime_sensor/event_stream_manager.py:401) method is a placeholder. A production system would require integration with a robust NLP library for accurate entity recognition.
*   **Event Source Integration:** While the module allows configuration of event sources via [`configure_source()`](recursive_training/regime_sensor/event_stream_manager.py:211), it lacks built-in mechanisms to actively fetch or listen to these sources (e.g., API clients, message queue consumers). Ingestion currently relies on external calls to [`ingest_event()`](recursive_training/regime_sensor/event_stream_manager.py:223) or [`ingest_events_batch()`](recursive_training/regime_sensor/event_stream_manager.py:249).
*   **Handler Logic:** The module provides the framework for event handling, but the actual complex logic for regime shift detection or other analyses based on events would reside in the handlers, which are external to this module.
*   **Error Handling and Resilience:** While basic logging is present, more sophisticated error handling, retry mechanisms for event processing or storage, and dead-letter queue concepts could enhance resilience.
*   **Configuration Management:** The manager takes a `config` dictionary, but how this configuration is loaded and managed externally is not defined within the module.

## 4. Connections & Dependencies

*   **Direct Project Module Imports:** None observed within this file.
*   **External Library Dependencies:**
    *   `asyncio` (imported but not explicitly used directly in the provided code, perhaps planned for future async operations beyond threading)
    *   `json` (for event serialization/deserialization)
    *   `logging` (for application logging)
    *   `os` (for file system operations, e.g., creating directories for event storage)
    *   `datetime` (from `datetime` module, for timestamps)
    *   `Enum` (from `enum` module, for `EventPriority` and `EventType`)
    *   `typing` (for type hints)
    *   `re` (for basic regex in entity extraction)
    *   `time` (for `time.sleep` in the example and `time.time` for tie-breaking in queue)
    *   `threading` (for the event processing loop)
    *   `queue` (for the `PriorityQueue`)
    *   `hashlib`, `uuid` (imported in [`create_mock_news_event()`](recursive_training/regime_sensor/event_stream_manager.py:372) for mock data generation)
*   **Interaction via Shared Data:**
    *   **File System:** Writes event data as JSON files to a configurable directory (default: [`data/event_streams/`](recursive_training/regime_sensor/event_stream_manager.py:165)). Other modules could consume these files.
    *   **Callbacks:** Interacts with other parts of the system through registered event handler functions.
*   **Input/Output Files:**
    *   **Output:** Persists events as JSON files (e.g., `data/event_streams/YYYY-MM-DD/event_type/source_name/event_id.json`).
    *   **Input:** Does not directly read files for its primary operation, but relies on an external `config` dictionary which might be sourced from a file elsewhere.

## 5. Function and Class Example Usages

*   **[`Event`](recursive_training/regime_sensor/event_stream_manager.py:42) Class:**
    ```python
    from datetime import datetime
    from recursive_training.regime_sensor.event_stream_manager import Event, EventType, EventPriority

    event = Event(
        event_id="news_001",
        source="Reuters",
        event_type=EventType.NEWS,
        timestamp=datetime.now(),
        content="Major tech company announces breakthrough.",
        entities=["TechCompanyA"],
        priority=EventPriority.HIGH
    )
    print(event.to_dict())
    ```
*   **[`EventStreamManager`](recursive_training/regime_sensor/event_stream_manager.py:138) Class:**
    The `if __name__ == "__main__":` block (lines [`423-451`](recursive_training/regime_sensor/event_stream_manager.py:423)) provides a good usage example:
    ```python
    from recursive_training.regime_sensor.event_stream_manager import EventStreamManager, EventType, Event
    import time

    manager = EventStreamManager(config={'storage_path': 'temp_event_data'})

    def custom_news_handler(event: Event):
        print(f"Handler received NEWS: {event.content[:30]}...")

    manager.register_event_handler(EventType.NEWS, custom_news_handler)
    manager.start()

    mock_event = manager.create_mock_news_event("Global markets react to policy changes.")
    manager.ingest_event(mock_event)

    time.sleep(0.5) # Allow time for processing
    manager.stop()
    ```
*   **Registering a Handler:**
    ```python
    manager.register_event_handler(EventType.ECONOMIC_INDICATOR, my_econ_handler_func)
    ```
*   **Ingesting an Event:**
    ```python
    new_event = Event(...)
    manager.ingest_event(new_event)
    ```

## 6. Hardcoding Issues

*   **Default Storage Path:** [`self.storage_path = self.config.get('storage_path', 'data/event_streams')`](recursive_training/regime_sensor/event_stream_manager.py:165). While configurable, the default is hardcoded.
*   **Default Max Queue Size:** [`self.max_queue_size = self.config.get('max_queue_size', 10000)`](recursive_training/regime_sensor/event_stream_manager.py:159). Default is hardcoded.
*   **Timestamp 'Z' Replacement:** [`timestamp.replace('Z', '+00:00')`](recursive_training/regime_sensor/event_stream_manager.py:78) in [`Event.__init__()`](recursive_training/regime_sensor/event_stream_manager.py:47) assumes 'Z' always signifies UTC and requires this specific replacement for `fromisoformat`.
*   **Mock Source Name:** [`source: str = "mock_source"`](recursive_training/regime_sensor/event_stream_manager.py:372) in [`create_mock_news_event()`](recursive_training/regime_sensor/event_stream_manager.py:372).
*   **Common Words for Entity Filtering:** The set [`common_words`](recursive_training/regime_sensor/event_stream_manager.py:416) in [`_extract_entities_from_headline()`](recursive_training/regime_sensor/event_stream_manager.py:401) is hardcoded and limited.
*   **Timeout in `_event_processor_loop`:** `self.event_queue.get(timeout=0.1)` ([line 328](recursive_training/regime_sensor/event_stream_manager.py:328)) and `self.processing_thread.join(timeout=5.0)` ([line 356](recursive_training/regime_sensor/event_stream_manager.py:356)) use hardcoded timeout values.

## 7. Coupling Points

*   **Event Handlers:** The manager is coupled to the signature of event handler functions (`Callable[[Event], None]`). The effectiveness of the system heavily relies on externally provided handlers.
*   **`Event` Object Structure:** Any module creating or handling events must conform to the [`Event`](recursive_training/regime_sensor/event_stream_manager.py:42) class structure.
*   **Storage Format:** The JSON serialization format and directory structure ([`_store_event()`](recursive_training/regime_sensor/event_stream_manager.py:261)) create a coupling point for any external system that might read this stored event data.
*   **Configuration Dictionary:** The manager's behavior (e.g., `max_queue_size`, `storage_path`) is dependent on the structure and keys within the `config` dictionary passed during initialization.

## 8. Existing Tests

*   **Formal Tests:** No separate test file (e.g., `tests/recursive_training/regime_sensor/test_event_stream_manager.py`) is indicated in the provided project structure.
*   **Inline Example/Test:** The `if __name__ == "__main__":` block (lines [`423-451`](recursive_training/regime_sensor/event_stream_manager.py:423)) serves as a basic functional test and usage demonstration. It covers handler registration, event creation, ingestion, and the start/stop lifecycle of the manager. This is useful for basic validation but not a comprehensive test suite.

## 9. Module Architecture and Flow

*   **Core Components:**
    *   [`EventPriority`](recursive_training/regime_sensor/event_stream_manager.py:23) (Enum): Defines event priority levels (LOW, MEDIUM, HIGH, CRITICAL).
    *   [`EventType`](recursive_training/regime_sensor/event_stream_manager.py:31) (Enum): Defines types of events (NEWS, CORPORATE_ANNOUNCEMENT, etc.).
    *   [`Event`](recursive_training/regime_sensor/event_stream_manager.py:42) (Class): Represents a single event with attributes like ID, source, type, timestamp, content, entities, metadata, and priority. Includes methods for dictionary conversion.
    *   [`EventStreamManager`](recursive_training/regime_sensor/event_stream_manager.py:138) (Class): The central orchestrator.
        *   Manages an internal `queue.PriorityQueue` for events, prioritizing by event priority and then by timestamp.
        *   Stores registered event handlers in a dictionary (`event_handlers`).
        *   Manages event filters (`filters`).
        *   Maintains a history of processed events (`event_history`).
        *   Uses a `threading.Thread` ([`processing_thread`](recursive_training/regime_sensor/event_stream_manager.py:158)) to run the [`_event_processor_loop()`](recursive_training/regime_sensor/event_stream_manager.py:320) asynchronously.
        *   Handles event storage to disk if enabled.
*   **Primary Data/Control Flow:**
    1.  Initialize [`EventStreamManager`](recursive_training/regime_sensor/event_stream_manager.py:138), optionally with a configuration dictionary.
    2.  Register custom event handlers for specific [`EventType`](recursive_training/regime_sensor/event_stream_manager.py:31)s using [`register_event_handler()`](recursive_training/regime_sensor/event_stream_manager.py:173).
    3.  Optionally, add custom filter functions using [`add_filter()`](recursive_training/regime_sensor/event_stream_manager.py:187).
    4.  Start the manager using [`start()`](recursive_training/regime_sensor/event_stream_manager.py:339), which launches the background processing thread.
    5.  Events are submitted to the manager via [`ingest_event()`](recursive_training/regime_sensor/event_stream_manager.py:223) or [`ingest_events_batch()`](recursive_training/regime_sensor/event_stream_manager.py:249).
    6.  Each ingested event is first checked against all registered filters.
    7.  If an event passes all filters, it's put onto the `PriorityQueue`. The priority is `(-event.priority.value, time.time(), event)` to ensure higher numerical priority values are processed first, with `time.time()` as a tie-breaker.
    8.  If storage is enabled, the event is serialized to JSON and saved to disk via [`_store_event()`](recursive_training/regime_sensor/event_stream_manager.py:261).
    9.  The [`_event_processor_loop()`](recursive_training/regime_sensor/event_stream_manager.py:320) in the background thread continuously attempts to get events from the queue.
    10. When an event is retrieved, [`_process_event()`](recursive_training/regime_sensor/event_stream_manager.py:284) is called. This method finds all relevant handlers (for the specific event type and general `EventType.CUSTOM` handlers) and executes them with the event as an argument.
    11. The event's `processed` flag is set to `True`, and processing information is added to its `processing_history`. The event is also added to the in-memory `event_history`.
    12. The manager can be stopped using [`stop()`](recursive_training/regime_sensor/event_stream_manager.py:350), which signals the processing thread to terminate and waits for it to join.

## 10. Naming Conventions

*   **Overall:** The module generally adheres to PEP 8 naming conventions.
*   **Classes:** `PascalCase` is used for class names (e.g., [`EventPriority`](recursive_training/regime_sensor/event_stream_manager.py:23), [`EventType`](recursive_training/regime_sensor/event_stream_manager.py:31), [`Event`](recursive_training/regime_sensor/event_stream_manager.py:42), [`EventStreamManager`](recursive_training/regime_sensor/event_stream_manager.py:138)).
*   **Enums:** Enum members are `UPPER_CASE` (e.g., `EventPriority.HIGH`, `EventType.NEWS`).
*   **Functions and Methods:** `snake_case` is used (e.g., [`register_event_handler`](recursive_training/regime_sensor/event_stream_manager.py:173), [`_store_event`](recursive_training/regime_sensor/event_stream_manager.py:261)).
*   **Variables:** `snake_case` is used (e.g., `event_queue`, `max_queue_size`).
*   **Private/Internal Methods:** Prefixed with a single underscore (e.g., [`_process_event`](recursive_training/regime_sensor/event_stream_manager.py:284)), which is a standard Python convention.
*   **Clarity:** Names are generally descriptive and easy to understand (e.g., `event_id`, `timestamp`, `processing_history`).
*   **Potential AI Assumption Errors/Deviations:** No obvious errors or significant deviations from standard Python conventions were noted. The naming is consistent and follows common practices.