# Module Analysis: `recursive_training.regime_sensor.retrodiction_trigger`

**File Path:** [`recursive_training/regime_sensor/retrodiction_trigger.py`](../../recursive_training/regime_sensor/retrodiction_trigger.py:1)

## 1. Module Intent/Purpose

The primary role of the `retrodiction_trigger` module is to bridge detected regime change events with the re-evaluation of retrodiction models. It achieves this by creating, managing, and processing "retrodiction snapshots." These snapshots encapsulate the necessary state and context (e.g., variables, time range, trigger cause) for a retrodiction task. Triggers can originate from various sources, including regime changes (via [`RegimeChangeEvent`](../../recursive_training/regime_sensor/regime_detector.py:1)), manual user requests, scheduled intervals, and potentially other unimplemented conditions like error thresholds or data anomalies.

## 2. Operational Status/Completeness

The module appears largely functional and complete for its core responsibilities of triggering, queuing, and dispatching retrodiction snapshots.
- It defines clear data structures: [`TriggerCause`](../../recursive_training/regime_sensor/retrodiction_trigger.py:22), [`TriggerPriority`](../../recursive_training/regime_sensor/retrodiction_trigger.py:33), and [`RetrodictionSnapshot`](../../recursive_training/regime_sensor/retrodiction_trigger.py:41).
- The main class, [`RetrodictionTrigger`](../../recursive_training/regime_sensor/retrodiction_trigger.py:173), handles snapshot creation, priority-based queuing, persistence of snapshots to disk (JSON format), and processing via registered callback handlers in a separate thread.
- An example handler, [`RetrodictionRunner`](../../recursive_training/regime_sensor/retrodiction_trigger.py:494), is provided, but it simulates the actual retrodiction work and explicitly notes that a real implementation would require integration with data loading and model evaluation systems.
- No `TODO` or `FIXME` comments indicating unfinished core logic were observed.

## 3. Implementation Gaps / Unfinished Next Steps

-   **Sophisticated Retrodiction Runner:** The current [`RetrodictionRunner`](../../recursive_training/regime_sensor/retrodiction_trigger.py:494) is a placeholder. A production-ready version would need to:
    *   Load actual data based on snapshot parameters ([`variables`](../../recursive_training/regime_sensor/retrodiction_trigger.py:75), [`time_range`](../../recursive_training/regime_sensor/retrodiction_trigger.py:76)).
    *   Integrate with and configure actual retrodiction models.
    *   Execute these models and perform comprehensive evaluation.
    *   Store detailed and structured results beyond the simulated ones.
-   **Additional Trigger Implementations:** The [`TriggerCause`](../../recursive_training/regime_sensor/retrodiction_trigger.py:22) enum includes `ERROR_THRESHOLD`, `CONFIDENCE_DROP`, `NEW_DATA`, and `ANOMALY`. However, the [`RetrodictionTrigger`](../../recursive_training/regime_sensor/retrodiction_trigger.py:173) class currently only has explicit logic for `REGIME_CHANGE`, `MANUAL`, and `SCHEDULED` triggers. Implementing automated triggers for the other causes would require additional monitoring logic (e.g., for model performance metrics).
-   **Advanced Results Management:** While snapshots and basic results are stored as JSON files, a more robust system might benefit from a database or a structured data store for easier querying and analysis of retrodiction results over time.
-   **MLOps Integration:** The module provides the triggering mechanism. Further integration into a broader MLOps pipeline for automated retraining, model deployment decisions based on retrodiction outcomes, and comprehensive monitoring would be logical extensions.
-   **Configuration for Snapshot ID Generation:** Prefixes for snapshot IDs (e.g., "manual_", "scheduled_") are hardcoded.

## 4. Connections & Dependencies

### 4.1. Internal Project Dependencies
-   [`recursive_training.regime_sensor.regime_detector`](../../recursive_training/regime_sensor/regime_detector.py:1): Imports [`RegimeType`](../../recursive_training/regime_sensor/regime_detector.py:1) and [`RegimeChangeEvent`](../../recursive_training/regime_sensor/regime_detector.py:1) ([`retrodiction_trigger.py:15`](../../recursive_training/regime_sensor/retrodiction_trigger.py:15)). The module is designed to consume `RegimeChangeEvent` objects.

### 4.2. External Library Dependencies
-   `logging`
-   `os`
-   `json`
-   `threading`
-   `time`
-   `datetime` (from `datetime`)
-   `typing` (Dict, List, Optional, Any, Callable, Set, Tuple, Union)
-   `enum` (Enum)
-   `queue`

### 4.3. Data & File Interactions
-   **Input Data:**
    *   Consumes [`RegimeChangeEvent`](../../recursive_training/regime_sensor/regime_detector.py:1) objects passed to its [`handle_regime_change`](../../recursive_training/regime_sensor/retrodiction_trigger.py:222) method.
    *   Accepts a configuration dictionary upon initialization of [`RetrodictionTrigger`](../../recursive_training/regime_sensor/retrodiction_trigger.py:173).
-   **Output Files:**
    *   **Snapshots:** Stores serialized [`RetrodictionSnapshot`](../../recursive_training/regime_sensor/retrodiction_trigger.py:41) objects as JSON files in a configurable directory (default: `data/retrodiction_snapshots/`). Path configured via `storage_path` ([`retrodiction_trigger.py:204`](../../recursive_training/regime_sensor/retrodiction_trigger.py:204)). Example: `data/retrodiction_snapshots/<snapshot_id>.json`.
    *   **Results (via example `RetrodictionRunner`):** The example [`RetrodictionRunner`](../../recursive_training/regime_sensor/retrodiction_trigger.py:494) stores its results as JSON files in a configurable directory (default: `data/retrodiction_results/`). Path configured via `results_path` ([`retrodiction_trigger.py:509`](../../recursive_training/regime_sensor/retrodiction_trigger.py:509)). Example: `data/retrodiction_results/result_<snapshot_id>.json`.
-   **Shared State (via handlers):** Passes [`RetrodictionSnapshot`](../../recursive_training/regime_sensor/retrodiction_trigger.py:41) objects to registered handler functions, which may interact with other systems or data stores.

## 5. Function and Class Example Usages

-   **`RetrodictionSnapshot(snapshot_id, timestamp, cause, priority, ...)`:**
    *   Represents a unit of work for retrodiction.
    *   Usage: `snapshot = RetrodictionSnapshot("snap1", datetime.now(), TriggerCause.MANUAL, TriggerPriority.HIGH, variables=['var1'], time_range=(start_dt, end_dt))` (see [`retrodiction_trigger.py:255`](../../recursive_training/regime_sensor/retrodiction_trigger.py:255)).
    *   Key methods: [`to_dict()`](../../recursive_training/regime_sensor/retrodiction_trigger.py:89) for serialization, [`from_dict()`](../../recursive_training/regime_sensor/retrodiction_trigger.py:113) for deserialization.

-   **`RetrodictionTrigger(config=None)`:**
    *   Manages the lifecycle of retrodiction snapshots.
    *   Usage: `trigger = RetrodictionTrigger(config={'storage_enabled': True, 'default_variables': ['var1']})` (see [`retrodiction_trigger.py:579`](../../recursive_training/regime_sensor/retrodiction_trigger.py:579)).
    *   Key methods:
        *   [`register_handler(handler_func)`](../../recursive_training/regime_sensor/retrodiction_trigger.py:212): To add a callback for processing snapshots.
        *   [`handle_regime_change(event)`](../../recursive_training/regime_sensor/retrodiction_trigger.py:222): To trigger a snapshot from a regime change.
        *   [`trigger_manual_snapshot(...)`](../../recursive_training/regime_sensor/retrodiction_trigger.py:276): To manually initiate a snapshot.
        *   [`start()`](../../recursive_training/regime_sensor/retrodiction_trigger.py:452): To begin background processing of the snapshot queue.
        *   [`stop()`](../../recursive_training/regime_sensor/retrodiction_trigger.py:463): To halt background processing.

-   **`RetrodictionRunner(config=None)` (Example Handler):**
    *   A sample implementation of a snapshot processor.
    *   Usage: `runner = RetrodictionRunner(); trigger.register_handler(runner.process_snapshot)` (see [`retrodiction_trigger.py:586-589`](../../recursive_training/regime_sensor/retrodiction_trigger.py:586)).
    *   Its [`process_snapshot(snapshot)`](../../recursive_training/regime_sensor/retrodiction_trigger.py:513) method is called by the `RetrodictionTrigger` for each snapshot.

## 6. Hardcoding Issues

While many parameters are configurable via the `config` dictionary, some defaults and internal values are hardcoded:
-   **Default Storage Paths:**
    *   Snapshot storage: `'data/retrodiction_snapshots'` ([`retrodiction_trigger.py:204`](../../recursive_training/regime_sensor/retrodiction_trigger.py:204)).
    *   Results storage (in example runner): `'data/retrodiction_results'` ([`retrodiction_trigger.py:509`](../../recursive_training/regime_sensor/retrodiction_trigger.py:509)).
-   **Default Configuration Values:**
    *   `default_time_window_days`: `365` ([`retrodiction_trigger.py:197`](../../recursive_training/regime_sensor/retrodiction_trigger.py:197)).
    *   `default_variables`: `[]` (empty list) ([`retrodiction_trigger.py:198`](../../recursive_training/regime_sensor/retrodiction_trigger.py:198)).
    *   `schedule_interval_hours`: `24` ([`retrodiction_trigger.py:199`](../../recursive_training/regime_sensor/retrodiction_trigger.py:199)).
-   **Snapshot ID Prefixes:** "snapshot_", "manual_", "scheduled_" are used in [`RetrodictionTrigger`](../../recursive_training/regime_sensor/retrodiction_trigger.py:173) when generating `snapshot_id` values (e.g., [`retrodiction_trigger.py:254`](../../recursive_training/regime_sensor/retrodiction_trigger.py:254)).
-   **Default Time Range Logic:** The specific calculation for the default `start_time` (e.g., setting day and month to 1) is hardcoded within methods like [`handle_regime_change`](../../recursive_training/regime_sensor/retrodiction_trigger.py:247-251).
-   **Example Runner Simulation:** The [`RetrodictionRunner`](../../recursive_training/regime_sensor/retrodiction_trigger.py:494) uses a hardcoded sleep time (`time.sleep(1)`) ([`retrodiction_trigger.py:529`](../../recursive_training/regime_sensor/retrodiction_trigger.py:529)) and simulated metrics ([`retrodiction_trigger.py:532-542`](../../recursive_training/regime_sensor/retrodiction_trigger.py:532-542)), which is acceptable for an example.

## 7. Coupling Points

-   **`recursive_training.regime_sensor.regime_detector`:** Tightly coupled, as it consumes [`RegimeChangeEvent`](../../recursive_training/regime_sensor/regime_detector.py:1) and uses [`RegimeType`](../../recursive_training/regime_sensor/regime_detector.py:1) from this module.
-   **Snapshot Handlers:** The [`RetrodictionTrigger`](../../recursive_training/regime_sensor/retrodiction_trigger.py:173) is coupled to its registered handlers via a callback mechanism. The contract is that handlers accept a [`RetrodictionSnapshot`](../../recursive_training/regime_sensor/retrodiction_trigger.py:41) object.
-   **Configuration Dictionary:** The behavior of [`RetrodictionTrigger`](../../recursive_training/regime_sensor/retrodiction_trigger.py:173) is significantly dependent on the structure and values within the configuration dictionary provided at initialization.
-   **File System:** If `storage_enabled` is true, the module interacts with the file system for storing and updating snapshot (and example results) JSON files, creating a dependency on file system access and structure.

## 8. Existing Tests

-   **Inline Example/Basic Test:** The module includes an `if __name__ == "__main__":` block ([`retrodiction_trigger.py:577`](../../recursive_training/regime_sensor/retrodiction_trigger.py:577)) that demonstrates basic instantiation, handler registration, triggering via regime change and manual call, and processing. This serves as a rudimentary integration test.
-   **Formal Unit Tests:** No dedicated unit test files (e.g., in a `tests/` directory corresponding to this module) were identified in the provided file listing.
-   **Testing Gaps:**
    *   Lack of unit tests for methods within [`RetrodictionSnapshot`](../../recursive_training/regime_sensor/retrodiction_trigger.py:41) (e.g., robust testing of [`from_dict`](../../recursive_training/regime_sensor/retrodiction_trigger.py:113) with various valid/invalid date formats and missing fields).
    *   Lack of unit tests for [`RetrodictionTrigger`](../../recursive_training/regime_sensor/retrodiction_trigger.py:173) methods covering different configurations, priority handling in the queue, thread safety (though locks are used), error conditions, and behavior of different trigger paths in isolation.

## 9. Module Architecture and Flow

The module is architected around a few key components:
-   **Enums (`TriggerCause`, `TriggerPriority`):** Define types of triggers and their importance.
-   **`RetrodictionSnapshot` (Data Class):** Encapsulates all information for a single retrodiction task. It handles its own JSON serialization and deserialization.
-   **`RetrodictionTrigger` (Orchestrator):**
    *   Manages a `PriorityQueue` ([`snapshot_queue`](../../recursive_training/regime_sensor/retrodiction_trigger.py:187)) for [`RetrodictionSnapshot`](../../recursive_training/regime_sensor/retrodiction_trigger.py:41) objects, ensuring higher priority snapshots are processed first.
    *   Maintains a list of historical snapshots ([`snapshot_history`](../../recursive_training/regime_sensor/retrodiction_trigger.py:188)).
    *   Uses a list of registered [`handlers`](../../recursive_training/regime_sensor/retrodiction_trigger.py:189) (callback functions) to delegate the actual processing of snapshots.
    *   Operates a background `threading.Thread` ([`processing_thread`](../../recursive_training/regime_sensor/retrodiction_trigger.py:191)) that continuously polls the queue and dispatches snapshots to handlers.
    *   Provides methods to trigger snapshots due to regime changes ([`handle_regime_change`](../../recursive_training/regime_sensor/retrodiction_trigger.py:222)), manual intervention ([`trigger_manual_snapshot`](../../recursive_training/regime_sensor/retrodiction_trigger.py:276)), or on a schedule ([`_check_scheduled_snapshot`](../../recursive_training/regime_sensor/retrodiction_trigger.py:415)).
    *   Includes logic for persisting snapshots to the file system if enabled ([`_store_snapshot`](../../recursive_training/regime_sensor/retrodiction_trigger.py:343)).
-   **`RetrodictionRunner` (Example Handler Class):** Demonstrates a simple handler that simulates processing a snapshot and storing results.

**Primary Data/Control Flow:**
1.  `RetrodictionTrigger` is initialized and its [`start()`](../../recursive_training/regime_sensor/retrodiction_trigger.py:452) method is called, launching the `_snapshot_processor_loop`.
2.  External systems or internal logic call methods like [`handle_regime_change()`](../../recursive_training/regime_sensor/retrodiction_trigger.py:222) or [`trigger_manual_snapshot()`](../../recursive_training/regime_sensor/retrodiction_trigger.py:276). Scheduled triggers are checked internally by the processor loop.
3.  A [`RetrodictionSnapshot`](../../recursive_training/regime_sensor/retrodiction_trigger.py:41) object is created with relevant details and cause/priority.
4.  The snapshot is added to the `PriorityQueue` ([`_enqueue_snapshot`](../../recursive_training/regime_sensor/retrodiction_trigger.py:323)) and optionally saved to disk.
5.  The `_snapshot_processor_loop` dequeues the highest priority snapshot.
6.  The snapshot is passed to each registered handler function ([\`_process_snapshot\`](../../recursive_training/regime_sensor/retrodiction_trigger.py:363)).
7.  Handlers perform their specific retrodiction tasks (simulated by [`RetrodictionRunner`](../../recursive_training/regime_sensor/retrodiction_trigger.py:494)), update the snapshot's `results` and `processed` status.
8.  The updated snapshot is saved to disk again if storage is enabled.

## 10. Naming Conventions

-   **Classes:** PascalCase (e.g., [`RetrodictionSnapshot`](../../recursive_training/regime_sensor/retrodiction_trigger.py:41), [`RetrodictionTrigger`](../../recursive_training/regime_sensor/retrodiction_trigger.py:173)).
-   **Enum Members:** UPPER_CASE (e.g., `REGIME_CHANGE`, `CRITICAL`).
-   **Methods & Functions:** snake_case (e.g., [`handle_regime_change`](../../recursive_training/regime_sensor/retrodiction_trigger.py:222), [`_store_snapshot`](../../recursive_training/regime_sensor/retrodiction_trigger.py:343)). Single leading underscore for "protected" methods.
-   **Variables & Parameters:** snake_case (e.g., `snapshot_id`, `default_time_window`).
-   **Module Name:** `retrodiction_trigger.py` (snake_case).
-   **Overall:** The naming conventions are consistent, descriptive, and adhere well to PEP 8 guidelines. No significant deviations or potential AI assumption errors in naming were noted.