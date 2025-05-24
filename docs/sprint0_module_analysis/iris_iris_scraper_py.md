# Module Analysis: `iris/iris_scraper.py`

## 1. Module Intent/Purpose

The `iris_scraper.py` module, also referred to as the "Signal Collector," serves as the main orchestrator for several key processes within the Iris system. Its primary responsibilities include:
*   Running registered ingestion plugins to gather raw signals.
*   Applying trust scoring to these signals, considering factors like recency and anomaly detection to compute a Signal Trust Index (STI).
*   Performing symbolic tagging on signals (e.g., hope, despair, rage, fatigue, neutral) using the `IrisSymbolismTagger`.
*   Exporting the processed and trusted signals to a JSONL file for downstream consumption or archival.
*   Interacting with `IrisArchive` to persist signal records.

## 2. Operational Status/Completeness

The module appears to be largely complete for its defined scope. It successfully initializes necessary components ([`IrisTrustScorer`](../../../iris/iris_trust.py:20), [`IrisSymbolismTagger`](../../../iris/iris_symbolism.py:21), [`IrisPluginManager`](../../../iris/iris_plugins.py:22), [`IrisArchive`](../../../iris/iris_archive.py:23)), ingests signals (both individually and in batch from plugins), applies the defined scoring and tagging logic, and exports the results. The presence of an `if __name__ == "__main__":` block ([`iris/iris_scraper.py:111-124`](../../../iris/iris_scraper.py:111-124)) with a dummy plugin suggests it's in a runnable state for basic testing and operation. There are no explicit "TODO" comments or obvious major placeholders for core functionality.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Plugin Ecosystem:** While the framework for plugin management exists via [`IrisPluginManager`](../../../iris/iris_plugins.py:22) and a `dummy_plugin` ([`iris/iris_scraper.py:116-120`](../../../iris/iris_scraper.py:116-120)) is used for testing, the development and integration of a comprehensive suite of real-world data ingestion plugins would be a logical next step.
*   **Error Handling:** The error handling in `batch_ingest_from_plugins` ([`iris/iris_scraper.py:70-90`](../../../iris/iris_scraper.py:70-90)) (catches general exceptions and logs errors) is functional but could be enhanced with more specific error types, retry mechanisms for transient issues, or dead-letter queueing for persistently failing signals.
*   **Log Management:** The module exports to `signals_latest.jsonl` ([`iris/iris_scraper.py:28`](../../../iris/iris_scraper.py:28)), overwriting it on each run. While [`IrisArchive`](../../../iris/iris_archive.py:23) is used, more sophisticated versioning, rotation, or management of the `signals_latest.jsonl` file itself might be beneficial depending on operational requirements.
*   **Configuration:** Key paths like `SIGNAL_LOG_DIR` ([`iris/iris_scraper.py:27`](../../../iris/iris_scraper.py:27)) are hardcoded. Externalizing such configurations (e.g., to a config file or environment variables) would improve flexibility.

## 4. Connections & Dependencies

### Internal Project Dependencies:
*   [`iris.iris_trust.IrisTrustScorer`](../../../iris/iris_trust.py:20): Used for all trust-related calculations (recency, anomaly, STI).
*   [`iris.iris_symbolism.IrisSymbolismTagger`](../../../iris/iris_symbolism.py:21): Used to infer symbolic tags for signals.
*   [`iris.iris_plugins.IrisPluginManager`](../../../iris/iris_plugins.py:22): Used to discover, load, and run ingestion plugins.
*   [`iris.iris_archive.IrisArchive`](../../../iris/iris_archive.py:23): Used to append and persist signal records.

### External Library Dependencies:
*   `os`: Standard library, used for path operations and directory creation.
*   `json`: Standard library, used for serializing signal records to JSONL.
*   `logging`: Standard library, used for application logging.
*   `datetime`: Standard library, used for timestamping signals.
*   `typing`: Standard library, used for type hinting.

### Data Interactions:
*   **Output File:** Writes processed signals to `data/iris_signals/signals_latest.jsonl` ([`iris/iris_scraper.py:28`](../../../iris/iris_scraper.py:28)). This file acts as an interface for other components that might consume these signals.
*   **Plugin Data Structure:** Expects signals from plugins to be dictionaries containing keys like `"name"`, `"value"`, and optionally `"source"` and `"timestamp"`.

## 5. Function and Class Example Usages

### Class: `IrisScraper` ([`iris/iris_scraper.py:31`](../../../iris/iris_scraper.py:31))

**Initialization:**
```python
iris_scraper = IrisScraper()
```

**Ingesting a single signal:**
```python
from datetime import datetime, timezone
signal_data = iris_scraper.ingest_signal(
    name="temperature_reading",
    value=25.5,
    source="manual_input",
    timestamp=datetime.now(timezone.utc)
)
```

**Batch ingesting signals from plugins:**
```python
# Assumes plugins are discoverable by IrisPluginManager
iris_scraper.plugin_manager.autoload() # Important to load plugins first
iris_scraper.batch_ingest_from_plugins()
```

**Exporting collected signals:**
```python
exported_file_path = iris_scraper.export_signal_log()
print(f"Signals exported to: {exported_file_path}")
```

**Resetting the in-memory signal log:**
```python
iris_scraper.reset_signal_log()
```
The `if __name__ == "__main__":` block in [`iris/iris_scraper.py:111-124`](../../../iris/iris_scraper.py:111-124) provides a practical example of initializing the scraper, loading plugins (implicitly via `autoload`), running batch ingestion, and could be extended to show export.

## 6. Hardcoding Issues

*   **Signal Log Directory:** `SIGNAL_LOG_DIR = "data/iris_signals"` ([`iris/iris_scraper.py:27`](../../../iris/iris_scraper.py:27)). This path is hardcoded.
*   **Signal Log File:** `SIGNAL_LOG_FILE = os.path.join(SIGNAL_LOG_DIR, "signals_latest.jsonl")` ([`iris/iris_scraper.py:28`](../../../iris/iris_scraper.py:28)). The filename `signals_latest.jsonl` is hardcoded.
*   **Default Signal Source:** In the `batch_ingest_from_plugins` method ([`iris/iris_scraper.py:70`](../../../iris/iris_scraper.py:70)), if a signal from a plugin does not specify a source, it defaults to `"plugin"` ([`iris/iris_scraper.py:85`](../../../iris/iris_scraper.py:85)). This is a minor hardcoding but worth noting.

## 7. Coupling Points

*   **Internal Components:** The `IrisScraper` class ([`iris/iris_scraper.py:31`](../../../iris/iris_scraper.py:31)) is tightly coupled to `IrisTrustScorer` ([`iris/iris_trust.py:20`](../../../iris/iris_trust.py:20)), `IrisSymbolismTagger` ([`iris/iris_symbolism.py:21`](../../../iris/iris_symbolism.py:21)), `IrisPluginManager` ([`iris/iris_plugins.py:22`](../../../iris/iris_plugins.py:22)), and `IrisArchive` ([`iris/iris_archive.py:23`](../../../iris/iris_archive.py:23)) as it directly instantiates and calls their methods. Changes to the APIs of these components would directly impact `IrisScraper`.
*   **Plugin Contract:** The scraper expects a specific dictionary structure (with `name`, `value` keys being mandatory) for signals returned by plugins. Changes to this implicit contract would break ingestion.
*   **Output File Format:** The structure of the JSON objects written to `signals_latest.jsonl` ([`iris/iris_scraper.py:28`](../../../iris/iris_scraper.py:28)) creates a coupling point for any downstream consumers of this file.

## 8. Existing Tests

*   The module does not appear to have a dedicated test file (e.g., `tests/iris/test_iris_scraper.py`) in the provided file listing.
*   A basic inline testing or demonstration capability is provided within the `if __name__ == "__main__":` block ([`iris/iris_scraper.py:111-124`](../../../iris/iris_scraper.py:111-124)). This block initializes the scraper, defines and uses a `dummy_plugin` ([`iris/iris_scraper.py:116-120`](../../../iris/iris_scraper.py:116-120)), loads plugins via `autoload()` ([`iris/iris_scraper.py:123`](../../../iris/iris_scraper.py:123)), and runs `batch_ingest_from_plugins()` ([`iris/iris_scraper.py:124`](../../../iris/iris_scraper.py:124)).
*   This suggests that formal, isolated unit tests might be limited or missing for this specific module.

## 9. Module Architecture and Flow

1.  **Initialization (`__init__`)** ([`iris/iris_scraper.py:32`](../../../iris/iris_scraper.py:32)):
    *   Instances of `IrisTrustScorer`, `IrisSymbolismTagger`, `IrisPluginManager`, and `IrisArchive` are created and stored as instance variables.
    *   An empty list `self.signal_log` is initialized to store signals in memory during a run.
    *   The `SIGNAL_LOG_DIR` (e.g., `data/iris_signals/`) is created if it doesn't exist ([`iris/iris_scraper.py:41`](../../../iris/iris_scraper.py:41)).
2.  **Signal Ingestion**:
    *   **Single Signal (`ingest_signal`)** ([`iris/iris_scraper.py:43`](../../../iris/iris_scraper.py:43)):
        *   Takes signal `name`, `value`, `source`, and an optional `timestamp`.
        *   If `timestamp` is not provided, it defaults to `datetime.now(timezone.utc)`.
        *   Calls `self.trust_engine` to get `recency_score`, `anomaly_flag`, and `sti`.
        *   Calls `self.symbolism_engine` to get `symbolic_tag`.
        *   Constructs a `signal_record` dictionary containing all this information.
        *   Appends the `signal_record` to `self.signal_log` and `self.archive` ([`iris/iris_scraper.py:67`](../../../iris/iris_scraper.py:67)).
        *   Returns the `signal_record`.
    *   **Batch Ingestion (`batch_ingest_from_plugins`)** ([`iris/iris_scraper.py:70`](../../../iris/iris_scraper.py:70)):
        *   Calls `self.plugin_manager.run_plugins()` to retrieve a list of signals from all registered and active plugins.
        *   Iterates through each signal from the plugins.
        *   Validates that the signal has `name` and `value`. Logs an error and skips if not.
        *   Calls `self.ingest_signal()` for each valid plugin signal.
        *   Logs errors if `ingest_signal` fails for any plugin signal.
3.  **Signal Export (`export_signal_log`)** ([`iris/iris_scraper.py:91`](../../../iris/iris_scraper.py:91)):
    *   Opens `SIGNAL_LOG_FILE` (e.g., `data/iris_signals/signals_latest.jsonl`) in write mode.
    *   Iterates through `self.signal_log` (all signals collected in the current run).
    *   Writes each `signal_record` as a JSON string followed by a newline (JSONL format).
    *   Logs the export action and returns the path to the log file.
4.  **Log Reset (`reset_signal_log`)** ([`iris/iris_scraper.py:104`](../../../iris/iris_scraper.py:104)):
    *   Clears the in-memory `self.signal_log` by reassigning it to an empty list. This prepares the scraper for a new batch of signals without carrying over old ones in memory (though they are in `IrisArchive` and potentially the last `signals_latest.jsonl`).

## 10. Naming Conventions

*   **Class Names:** `IrisScraper` ([`iris/iris_scraper.py:31`](../../../iris/iris_scraper.py:31)) follows PascalCase, which is standard for Python classes (PEP 8).
*   **Method Names:** Methods like `ingest_signal` ([`iris/iris_scraper.py:43`](../../../iris/iris_scraper.py:43)), `batch_ingest_from_plugins` ([`iris/iris_scraper.py:70`](../../../iris/iris_scraper.py:70)), `export_signal_log` ([`iris/iris_scraper.py:91`](../../../iris/iris_scraper.py:91)), and `reset_signal_log` ([`iris/iris_scraper.py:104`](../../../iris/iris_scraper.py:104)) use snake_case, adhering to PEP 8.
*   **Variable Names:** Local variables (`signal_record`, `recency_score`) and instance variables (`self.trust_engine`, `self.signal_log`) consistently use snake_case.
*   **Constants:** Module-level constants `SIGNAL_LOG_DIR` ([`iris/iris_scraper.py:27`](../../../iris/iris_scraper.py:27)) and `SIGNAL_LOG_FILE` ([`iris/iris_scraper.py:28`](../../../iris/iris_scraper.py:28)) use UPPER_SNAKE_CASE, which is the correct convention.
*   **Docstrings:** The module, class, and all public methods have docstrings explaining their purpose, arguments, and return values where applicable.
*   **Type Hinting:** Type hints are used for function arguments and return types (e.g., `Optional[Dict[str, Any]]`, `str`), improving code readability and maintainability.

Overall, the naming conventions are consistent, follow Python community best practices (PEP 8), and contribute to the module's clarity. There are no apparent AI assumption errors or significant deviations from standards.