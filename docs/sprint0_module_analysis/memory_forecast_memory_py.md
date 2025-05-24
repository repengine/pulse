# Module Analysis: `memory/forecast_memory.py`

## 1. Module Intent/Purpose

The primary role of the [`memory/forecast_memory.py`](../../memory/forecast_memory.py) module is to provide a robust system for storing and retrieving recent or historical forecasts generated during system simulations. It supports symbolic tagging of forecasts, facilitates replay capabilities, and integrates with the PFPA (Pulse Forecast Performance Analytics) trust scoring system. The module aims to offer a unified forecast storage solution that includes mechanisms for enforcing memory limits and pruning older or less relevant entries.

## 2. Operational Status/Completeness

The module appears largely complete and operational for its defined scope. Key functionalities such as forecast storage, retrieval, persistence, trust updates, and various pruning/retention strategies are implemented.
- It includes type validation for forecast objects and error handling for numeric fields (e.g., in the [`store()`](../../memory/forecast_memory.py:46) method).
- Fallback mechanisms are in place, for instance, for ensuring `forecast_id` presence.
- There are comments marked "PATCH" (e.g., around [`line 82`](../../memory/forecast_memory.py:82) and [`line 190`](../../memory/forecast_memory.py:190)), which might indicate areas with temporary fixes or solutions that could be refined for long-term robustness (e.g., overlay serialization).
- Some methods like [`gate_memory_retention_by_license()`](../../memory/forecast_memory.py:129) use `print` statements for logging critical information, which could potentially be replaced with the module's standard `logger` for consistency.

## 3. Implementation Gaps / Unfinished Next Steps

- **Overlay Serialization Patch:** The patch for serializing "overlays" within forecast objects ([`lines 190-201`](../../memory/forecast_memory.py:190-201)) suggests this area might benefit from a more permanent or deeply integrated solution for handling complex nested objects during persistence.
- **Logging Consistency:** Methods like [`gate_memory_retention_by_license()`](../../memory/forecast_memory.py:129) and [`retain_cluster_lineage_leaders()`](../../memory/forecast_memory.py:170) use `print()` for status messages. These could be standardized to use the existing `logger` instance for better log management and consistency.
- **Schema Versioning for Persistence:** The module persists forecast objects as JSON. There's no explicit mechanism for versioning the schema of these objects or for migrating data if the `forecast_obj` structure evolves over time. This could be a consideration for future enhancements to ensure backward compatibility.
- **Deeper License Enforcer Integration:** While [`trust_system.license_enforcer`](../../trust_system/license_enforcer.py) functions are imported, their direct application within the module's core logic (beyond the implications in `gate_memory_retention_by_license`) could be further explored or clarified if more granular license-based processing is intended.

## 4. Connections & Dependencies

### Direct Project Module Imports:
-   [`core.path_registry`](../../core/path_registry.py): For accessing `PATHS` dictionary, notably `PATHS["FORECAST_HISTORY"]` ([`line 9`](../../memory/forecast_memory.py:9)).
-   [`trust_system.license_enforcer`](../../trust_system/license_enforcer.py): Imports [`annotate_forecasts()`](../../trust_system/license_enforcer.py) and [`filter_licensed()`](../../trust_system/license_enforcer.py) ([`line 15`](../../memory/forecast_memory.py:15)).
-   [`core.pulse_learning_log`](../../core/pulse_learning_log.py): For [`log_learning_event()`](../../core/pulse_learning_log.py) ([`line 16`](../../memory/forecast_memory.py:16)).
-   [`utils.log_utils`](../../utils/log_utils.py): For [`get_logger()`](../../utils/log_utils.py) ([`line 19`](../../memory/forecast_memory.py:19)).
-   [`memory.cluster_mutation_tracker`](../../memory/cluster_mutation_tracker.py): Imports [`track_cluster_lineage()`](../../memory/cluster_mutation_tracker.py) and [`select_most_evolved()`](../../memory/cluster_mutation_tracker.py) within the [`retain_cluster_lineage_leaders()`](../../memory/forecast_memory.py:170) method.

### External Library Dependencies:
-   `typing`: For type hints (`List`, `Dict`, `Optional`) ([`line 12`](../../memory/forecast_memory.py:12)).
-   `datetime`: For timestamping in [`log_learning_event()`](../../memory/forecast_memory.py:96) ([`line 17`](../../memory/forecast_memory.py:17)).
-   `re`: Used for UUID-like string matching in [`store()`](../../memory/forecast_memory.py:46).
-   `uuid`: Potentially used for generating fallback IDs (imported in [`store()`](../../memory/forecast_memory.py:46), though direct usage for generation isn't explicit).
-   `os`: For path operations and directory creation (e.g., in [`_persist_to_file()`](../../memory/forecast_memory.py:186), [`_load_from_files()`](../../memory/forecast_memory.py:209)).
-   `json`: For serializing/deserializing forecast objects to/from files (e.g., in [`gate_memory_retention_by_license()`](../../memory/forecast_memory.py:129), [`_persist_to_file()`](../../memory/forecast_memory.py:186), [`_load_from_files()`](../../memory/forecast_memory.py:209)).

### Interaction via Shared Data:
-   **File System (Forecast History):** Reads from and writes to a persistence directory, typically defined by `PATHS["FORECAST_HISTORY"]`. Forecasts are stored as individual JSON files.
-   **File System (Blocked Memory Log):** Appends discarded forecast entries to [`logs/blocked_memory_log.jsonl`](../../logs/blocked_memory_log.jsonl) if memory retention is blocked due to license instability.

### Input/Output Files:
-   **Input:**
    -   `.json` files from the `persist_dir` (e.g., `PATHS["FORECAST_HISTORY"]`) are loaded during initialization.
-   **Output:**
    -   Individual forecast objects are written as `.json` files (e.g., `<forecast_id>.json`) in the `persist_dir`.
    -   Log entries are appended to [`logs/blocked_memory_log.jsonl`](../../logs/blocked_memory_log.jsonl).

## 5. Function and Class Example Usages

```python
from memory.forecast_memory import ForecastMemory

# Initialize ForecastMemory, optionally specifying persistence directory and max entries
# Assumes PATHS is configured, e.g., PATHS = {"FORECAST_HISTORY": "data/forecast_history"}
# from core.path_registry import PATHS # Ensure PATHS is available

# Example initialization (if PATHS["FORECAST_HISTORY"] is set)
# memory_store = ForecastMemory()

# Or with explicit path and max_entries
memory_store = ForecastMemory(persist_dir="custom_forecast_data", max_entries=500)

# Example forecast object
new_forecast = {
    "forecast_id": "some_unique_id_string_123",
    "trace_id": "trace_abc_789",
    "domain": "finance",
    "confidence": 0.85,
    "fragility": 0.1,
    "priority": 1.0,
    "retrodiction_score": 0.9,
    "target_variable": "stock_price_xyz",
    "prediction": {"value": 150.75, "timestamp": "2025-05-18T10:00:00Z"},
    "certified": False,
    "unstable_symbolic_path": False,
    "trust_label": "🟢 Stable"
}

# Store a forecast
memory_store.store(new_forecast)

# Retrieve the 5 most recent forecasts for the 'finance' domain
recent_finance_forecasts = memory_store.get_recent(n=5, domain="finance")
# for fc in recent_finance_forecasts:
#     print(fc.get("forecast_id"))

# Update trust information for a forecast
trust_update_data = {"trust_score": 0.92, "certified": True, "license": True}
memory_store.update_trust(forecast_id="some_unique_id_string_123", trust_data=trust_update_data)

# Prune forecasts with confidence below 0.6
pruned_count = memory_store.prune(min_confidence=0.6)
# print(f"Pruned {pruned_count} forecasts.")

# Find a forecast by its trace_id
found_forecast = memory_store.find_by_trace_id("trace_abc_789")
# if found_forecast:
#     print(f"Found forecast: {found_forecast.get('forecast_id')}")

# Example of retaining only certified forecasts
memory_store.retain_certified_forecasts()

# Example of gating memory by license loss (simulating high loss)
# memory_store.gate_memory_retention_by_license(license_loss_percent=50.0)
```

## 6. Hardcoding Issues

-   **`MAX_MEMORY_ENTRIES: int = 1000`** ([`line 29`](../../memory/forecast_memory.py:29)): Default maximum number of forecasts. While this is a class attribute, it's configurable during instantiation, mitigating the "hardcoding" aspect for instances.
-   **`BLOCKED_MEMORY_LOG = "logs/blocked_memory_log.jsonl"`** ([`line 22`](../../memory/forecast_memory.py:22)): The file path for logging memory entries that were blocked from retention. This could be made configurable if different logging locations are needed.
-   **Numeric Field Names in `store()`**: The list `['confidence', 'fragility', 'priority', 'retrodiction_score']` ([`line 61`](../../memory/forecast_memory.py:61)) used for type conversion is hardcoded.
-   **Default `forecast_id` Fallback**: In [`store()`](../../memory/forecast_memory.py:79), if `forecast_id` is missing, it falls back to `str(forecast_obj.get("trace_id", "unknown"))`. The string `"unknown"` is hardcoded.
-   **`trust_label` Value for Drift**: The specific string `"🔴 Drift-Prone"` is checked in [`store()`](../../memory/forecast_memory.py:83).
-   **`memory_flag` Values**: Strings like `"review_only"` ([`line 84`](../../memory/forecast_memory.py:84)) and `"uncertified_discard"` ([`line 168`](../../memory/forecast_memory.py:168)) are hardcoded.
-   **License Loss Threshold**: The `threshold` parameter in [`gate_memory_retention_by_license()`](../../memory/forecast_memory.py:129) defaults to `40.0`.

## 7. Coupling Points

-   **`core.path_registry`**: Tightly coupled for the default persistence directory (`PATHS["FORECAST_HISTORY"]`). Changes to how paths are managed could impact this module.
-   **Forecast Object Structure**: The module heavily relies on the internal structure (expected keys and data types) of the `forecast_obj` dictionaries. Changes to this structure elsewhere in the system would require updates here. Examples include keys like `forecast_id`, `confidence`, `domain`, `overlays`, `certified`, `unstable_symbolic_path`, `trust_label`, `license`.
-   **`trust_system.license_enforcer`**: Imports suggest a functional dependency, particularly for license-related processing, even if not all imported functions are directly called in the visible code.
-   **`memory.cluster_mutation_tracker`**: Dependency for the `retain_cluster_lineage_leaders` functionality.
-   **File System & JSON Format**: Interaction with the file system for persistence (reading/writing JSON files) creates coupling. Changes in storage format or strategy would affect [`_persist_to_file()`](../../memory/forecast_memory.py:186) and [`_load_from_files()`](../../memory/forecast_memory.py:209).
-   **`core.pulse_learning_log`**: Coupled for logging learning events related to memory updates.

## 8. Existing Tests

-   A corresponding test file, [`tests/test_forecast_memory.py`](../../tests/test_forecast_memory.py), exists in the project structure.
-   The specific state, coverage, and nature of these tests (e.g., unit, integration, specific scenarios covered) are not ascertainable from the provided file content alone but its presence indicates that testing infrastructure for this module is in place.

## 9. Module Architecture and Flow

The `ForecastMemory` class is the central component of this module.

-   **Initialization (`__init__`)**:
    -   Sets the persistence directory (defaulting to `PATHS["FORECAST_HISTORY"]`) and the maximum number of memory entries.
    -   If a persistence directory is configured, it calls [`_load_from_files()`](../../memory/forecast_memory.py:209) to populate the in-memory store (`self._memory`) with existing forecasts.
    -   Calls [`_enforce_memory_limit()`](../../memory/forecast_memory.py:181) to ensure the loaded memory conforms to size constraints.
-   **Storage (`store`)**:
    -   Validates that the input `forecast_obj` is a dictionary.
    -   Performs type conversion and validation for specific numeric fields (e.g., `confidence`, `fragility`).
    -   Ensures `forecast_id` is present and is a string, using `trace_id` or "unknown" as fallbacks.
    -   Applies a "PATCH" to tag "🔴 Drift-Prone" forecasts as `review_only` and `license=False`.
    -   Appends the processed `forecast_obj` to the `self._memory` list.
    -   Calls [`_enforce_memory_limit()`](../../memory/forecast_memory.py:181).
    -   If persistence is enabled, calls [`_persist_to_file()`](../../memory/forecast_memory.py:186) to save the forecast.
    -   Logs a "memory_update" event via [`log_learning_event()`](../../core/pulse_learning_log.py).
-   **Retrieval**:
    -   [`get_recent()`](../../memory/forecast_memory.py:102): Returns the last `n` forecasts, optionally filtered by `domain`.
    -   [`find_by_trace_id()`](../../memory/forecast_memory.py:221): Searches `self._memory` for a forecast matching the given `trace_id` or `forecast_id`.
-   **Update (`update_trust`)**:
    -   Locates a forecast by `forecast_id` in `self._memory`.
    -   Updates its dictionary with the provided `trust_data`.
    -   If persistence is enabled, re-persists the updated forecast using [`_persist_to_file()`](../../memory/forecast_memory.py:186).
-   **Pruning and Retention Strategies**:
    -   [`prune()`](../../memory/forecast_memory.py:118): Removes entries below a `min_confidence` and then calls [`_enforce_memory_limit()`](../../memory/forecast_memory.py:181).
    -   [`gate_memory_retention_by_license()`](../../memory/forecast_memory.py:129): If `license_loss_percent` exceeds a `threshold`, logs current memory to `BLOCKED_MEMORY_LOG` and clears `self._memory`.
    -   [`retain_only_stable_forecasts()`](../../memory/forecast_memory.py:151): Filters `self._memory` to keep only forecasts not marked with `unstable_symbolic_path`.
    -   [`retain_certified_forecasts()`](../../memory/forecast_memory.py:159): Filters `self._memory` to keep only forecasts where `certified` is `True`.
    -   [`tag_uncertified_for_review()`](../../memory/forecast_memory.py:164): Sets `memory_flag` to `"uncertified_discard"` for non-certified forecasts.
    -   [`retain_cluster_lineage_leaders()`](../../memory/forecast_memory.py:170): Uses [`memory.cluster_mutation_tracker`](../../memory/cluster_mutation_tracker.py) to keep only the most evolved forecast per narrative cluster.
-   **Internal Persistence Logic**:
    -   [`_enforce_memory_limit()`](../../memory/forecast_memory.py:181): If `len(self._memory)` exceeds `self.max_entries`, truncates the list to keep only the most recent `self.max_entries`.
    -   [`_persist_to_file()`](../../memory/forecast_memory.py:186): Saves a single `forecast_obj` to a JSON file named `<forecast_id>.json` in `self.persist_dir`. Includes a "PATCH" to handle serialization of `overlays`.
    -   [`_load_from_files()`](../../memory/forecast_memory.py:209): Lists `.json` files in `self.persist_dir`, loads each, and appends to `self._memory`. Includes error handling for corrupted files.

## 10. Naming Conventions

-   **Class Names**: `ForecastMemory` follows PascalCase, which is standard (e.g., [`ForecastMemory`](../../memory/forecast_memory.py:24)).
-   **Method Names**: Generally use snake_case and are descriptive (e.g., [`store()`](../../memory/forecast_memory.py:46), [`get_recent()`](../../memory/forecast_memory.py:102), [`_persist_to_file()`](../../memory/forecast_memory.py:186)).
-   **Constants**: `MAX_MEMORY_ENTRIES` ([`line 29`](../../memory/forecast_memory.py:29)) and `BLOCKED_MEMORY_LOG` ([`line 22`](../../memory/forecast_memory.py:22)) are in `UPPER_SNAKE_CASE`, adhering to PEP 8.
-   **Variables**: Local variables mostly use snake_case (e.g., `forecast_obj`, `persist_dir`, `numeric_field`, `fname`).
    -   The variable `pd` ([`line 38`](../../memory/forecast_memory.py:38)) as an abbreviation for `persist_dir` is short but its scope is very limited, making it acceptable.
-   **Overall Consistency**: Naming conventions appear consistent throughout the module and largely adhere to PEP 8 guidelines. There are no obvious AI assumption errors or significant deviations from common Python styling.