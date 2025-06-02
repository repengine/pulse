# Module Analysis: `recursive_training.data.ingestion_manager`

## 1. Module Intent/Purpose

The primary role of the [`recursive_training.data.ingestion_manager`](../../recursive_training/data/ingestion_manager.py:1) module is to manage the ingestion of data from diverse sources into the recursive training system. Its responsibilities include:

*   Collecting data from files, APIs, and databases.
*   Performing data validation and schema enforcement.
*   Handling data transformation and preprocessing (though current implementation is light on this).
*   Storing ingested data via the [`RecursiveDataStore`](../../recursive_training/data/data_store.py:20).
*   Implementing cost control mechanisms for API requests (currently placeholder).
*   Supporting the retrieval of rule-related data for training.

## 2. Operational Status/Completeness

The module appears to be substantially complete in its core data ingestion capabilities for different source types. Key observations:

*   **Core Functionality:** Defines Pydantic models for data sources ([`DataSource`](../../recursive_training/data/ingestion_manager.py:53), [`APISource`](../../recursive_training/data/ingestion_manager.py:61), [`FileSource`](../../recursive_training/data/ingestion_manager.py:70), [`DatabaseSource`](../../recursive_training/data/ingestion_manager.py:77)) and implements ingestion logic for each.
*   **Configuration:** Supports loading configuration from a JSON file or falling back to defaults ([`_load_config`](../../recursive_training/data/ingestion_manager.py:147)).
*   **Error Handling:** Includes `try-except` blocks for optional Pulse component imports (e.g., [`core.pulse_config`](../../core/pulse_config.py), [`core.bayesian_trust_tracker`](../../core/bayesian_trust_tracker.py)) and uses availability flags (e.g., `PULSE_CONFIG_AVAILABLE` on line [`PULSE_CONFIG_AVAILABLE`](../../recursive_training/data/ingestion_manager.py:23)).
*   **Placeholders:**
    *   Rate limiting ([`_check_rate_limits`](../../recursive_training/data/ingestion_manager.py:609)) and cost control ([`_check_cost_threshold`](../../recursive_training/data/ingestion_manager.py:625)) are explicitly marked as "simplified placeholder".
    *   Schema validation beyond [`ForecastRecord`](../../core/schemas.py) is noted as an area for extension ([`_process_data`](../../recursive_training/data/ingestion_manager.py:447)).
*   **Singleton Pattern:** Provides a singleton instance of [`RecursiveDataIngestionManager`](../../recursive_training/data/ingestion_manager.py:84) via [`get_ingestion_manager()`](../../recursive_training/data/ingestion_manager.py:666).

## 3. Implementation Gaps / Unfinished Next Steps

*   **Advanced Cost Control & Rate Limiting:** The methods [`_check_rate_limits()`](../../recursive_training/data/ingestion_manager.py:609) and [`_check_cost_threshold()`](../../recursive_training/data/ingestion_manager.py:625) need full implementation beyond placeholders. The `cost_tracker` is initialized but not actively updated during API calls.
*   **Token Usage Refinement:** API token usage estimation ([`_ingest_from_api`](../../recursive_training/data/ingestion_manager.py:315)) is a rough estimate and could be made more accurate.
*   **Comprehensive Schema Validation:** While `validate_schema` is a config option, detailed implementation for various data types beyond [`ForecastRecord`](../../core/schemas.py) is missing ([`_process_data`](../../recursive_training/data/ingestion_manager.py:447)).
*   **Data Transformation/Preprocessing:** The module's docstring mentions these responsibilities, but the [`_process_data()`](../../recursive_training/data/ingestion_manager.py:410) method focuses mainly on validation and storage. Explicit transformation logic is not apparent.
*   **Caching Mechanism:** Configuration options for caching exist ([`enable_cache`](../../recursive_training/data/ingestion_manager.py:179), [`cache_ttl_seconds`](../../recursive_training/data/ingestion_manager.py:180)), but caching logic within ingestion methods is not implemented.
*   **Parallel Ingestion:** Configuration for parallel ingestion ([`parallel_ingestion`](../../recursive_training/data/ingestion_manager.py:175), [`max_workers`](../../recursive_training/data/ingestion_manager.py:176)) is present, but the actual ingestion methods appear synchronous.

## 4. Connections & Dependencies

*   **Project Modules (Direct Imports):**
    *   [`recursive_training.data.data_store.RecursiveDataStore`](../../recursive_training/data/data_store.py:20) (Core dependency for data storage)
    *   `core.pulse_config.get_config` (Optional)
    *   `core.bayesian_trust_tracker.bayesian_trust_tracker` (Optional)
    *   `core.schemas.ForecastRecord` (Optional)
    *   `analytics.output_data_reader.OutputDataReader` (Optional)
    *   [`recursive_training.config.default_config.get_config`](../../recursive_training/config/default_config.py) (For fallback configuration)
    *   `engine.causal_rules.get_active_rules` (Optional, dynamic import)
    *   `symbolic_system.symbolic_utils.get_active_symbolic_rules` (Optional, dynamic import)
*   **External Libraries:**
    *   `json`, `logging`, `os`, `datetime`, `pathlib`, `typing`
    *   `pandas` (for CSV processing)
    *   `pydantic` (for data models)
    *   `requests` (for API ingestion)
    *   `glob` (for file pattern matching)
    *   `sqlalchemy` (for database ingestion)
    *   `importlib` (for dynamic imports)
*   **Shared Data Interactions:**
    *   Stores data via [`RecursiveDataStore`](../../recursive_training/data/data_store.py:20).
    *   Reads various Pulse output files (forecasts, logs) as default file sources.
    *   Reads rules from `simulation_engine` and `symbolic_system`.
*   **Input/Output Files:**
    *   **Input:** JSON configuration file, data files (JSON, CSV).
    *   **Output:** Logs via `logging`. Archives input files if configured. Data is primarily outputted to [`RecursiveDataStore`](../../recursive_training/data/data_store.py:20).

## 5. Function and Class Example Usages

*   **`RecursiveDataIngestionManager` Usage:**
    ```python
    from recursive_training.data.ingestion_manager import get_ingestion_manager

    # Get the singleton instance (optionally with a custom config path)
    manager = get_ingestion_manager(config_path="path/to/your_ingestion_config.json")

    # Ingest data from all enabled and prioritized sources
    ingestion_results = manager.ingest_all()
    print(f"Ingestion summary: {ingestion_results}")

    # Ingest data from a specific source
    processed_count, ingested_count = manager.ingest_from_source("my_api_data_source")
    print(f"Source 'my_api_data_source': Processed {processed_count}, Ingested {ingested_count}")

    # Retrieve rule-related data
    rule_data_list = manager.get_rule_data()
    print(f"Retrieved {len(rule_data_list)} rules.")

    # Get system metadata related to ingestion
    system_meta = manager.get_system_metadata()
    print(f"System metadata: {system_meta}")

    # Get a summary of API call costs and token usage
    cost_summary = manager.get_cost_summary()
    print(f"Cost summary: {cost_summary}")
    ```
*   **Data Source Configuration (Conceptual - part of a JSON config file):**
    ```json
    {
      "data_sources": [
        {
          "source_id": "financial_news_api",
          "source_type": "api",
          "enabled": true,
          "priority": 1,
          "endpoint": "https://api.financialnews.com/v1/articles",
          "auth_type": "api_key",
          "headers": {"X-API-KEY": "YOUR_API_KEY_HERE"},
          "rate_limit": 50, // Max requests per some interval (actual interval not defined by this)
          "token_usage_tracking": true
        },
        {
          "source_id": "internal_event_logs",
          "source_type": "file",
          "enabled": true,
          "priority": 2,
          "path": "/var/log/app_events",
          "file_pattern": "events_*.json",
          "archive_after_ingestion": false
        },
        {
          "source_id": "user_activity_db",
          "source_type": "database",
          "enabled": true,
          "priority": 3,
          "connection_string": "postgresql://user:pass@host:port/dbname",
          "query": "SELECT user_id, action, timestamp FROM user_actions WHERE timestamp > :last_ingested_timestamp",
          "parameters": {"last_ingested_timestamp": "2023-01-01T00:00:00Z"} // Example parameter
        }
      ],
      "batch_size": 64,
      "parallel_ingestion": false, // Currently, parallel logic is not implemented
      "validate_schema": true,
      "daily_cost_threshold_usd": 5.00 // Placeholder for actual cost control
    }
    ```

## 6. Hardcoding Issues

*   **Default `base_data_path`:** Falls back to `"./data"` if Pulse config is unavailable ([`__init__`](../../recursive_training/data/ingestion_manager.py:113)).
*   **Default Configuration Block:** A substantial block of default settings (batch size, API limits, cost thresholds, etc.) is used if no config file is found and the project's default config module is unavailable ([`_load_config`](../../recursive_training/data/ingestion_manager.py:173-188)).
*   **Default Internal Source Paths & Patterns:** Paths for `pulse_forecasts`, `symbolic_logs`, `trust_logs` are constructed relative to `base_data_path` with fixed subdirectories and `"*.json"` pattern ([`_init_data_sources`](../../recursive_training/data/ingestion_manager.py:195-217)).
*   **API Request Timeout:** Hardcoded to `30` seconds in [`_ingest_from_api()`](../../recursive_training/data/ingestion_manager.py:299).
*   **Token Estimation Factor:** Uses `response_size / 4` as a rough estimate ([`_ingest_from_api`](../../recursive_training/data/ingestion_manager.py:315)).
*   **Archive Directory Name:** Fixed as `"archived"` within the source's directory ([`_ingest_from_file`](../../recursive_training/data/ingestion_manager.py:367)).
*   **Default Trust Score:** `0.5` is used for rules if `bayesian_trust_tracker` is unavailable ([`get_rule_data`](../../recursive_training/data/ingestion_manager.py:539)).
*   **Default Pulse Version:** `"unknown"` if Pulse config is inaccessible ([`get_system_metadata`](../../recursive_training/data/ingestion_manager.py:599)).

## 7. Coupling Points

*   **[`RecursiveDataStore`](../../recursive_training/data/data_store.py:20):** Tightly coupled for all data storage operations.
*   **Pulse Core Modules:** Significant, though often optional, coupling with `core.pulse_config`, `core.bayesian_trust_tracker`, `core.schemas.ForecastRecord`, and `analytics.output_data_reader`. Functionality degrades if these are absent.
*   **Configuration Schema:** Relies on specific structures for its own JSON configuration and the default config from [`recursive_training.config`](../../recursive_training/config).
*   **Rule Source Modules:** Depends on `engine.causal_rules` and `symbolic_system.symbolic_utils` for fetching rule data, using dynamic imports.
*   **External Libraries:** `requests`, `sqlalchemy`, `pandas` are critical for their respective data source types.

## 8. Existing Tests

*   A test file [`tests/recursive_training/test_data_ingestion.py`](../../tests/recursive_training/test_data_ingestion.py) exists, suggesting unit/integration tests are present for the data ingestion functionality.
*   The extent of test coverage for different source types, error conditions, optional dependency fallbacks, and placeholder features (cost control, rate limiting) is not ascertainable without reviewing the test file contents.
*   Given the placeholder nature of cost control and rate limiting, comprehensive tests for these features are likely missing or would test simplified logic.

## 9. Module Architecture and Flow

1.  **Initialization ([`__init__`](../../recursive_training/data/ingestion_manager.py:99)):**
    *   Sets up logging and determines `base_data_path` (from Pulse config or default).
    *   Loads its own configuration ([`_load_config`](../../recursive_training/data/ingestion_manager.py:147)), with fallbacks.
    *   Initializes data sources ([`_init_data_sources`](../../recursive_training/data/ingestion_manager.py:190)) from the configuration, including default Pulse output file sources.
    *   Sets up tracking for API calls, token usage, and costs.
    *   Optionally initializes [`OutputDataReader`](../../learning/output_data_reader.py).
    *   Prepares a set for deduplicating processed data.
2.  **Ingestion Triggering:**
    *   [`ingest_all()`](../../recursive_training/data/ingestion_manager.py:476): Iterates through enabled and prioritized sources.
    *   [`ingest_from_source()`](../../recursive_training/data/ingestion_manager.py:240): Handles a single specified source.
    *   [`ingest_pulse_outputs()`](../../recursive_training/data/ingestion_manager.py:503): Specifically targets default Pulse output sources.
3.  **Source-Specific Ingestion:**
    *   [`_ingest_from_api()`](../../recursive_training/data/ingestion_manager.py:272): Makes HTTP GET requests, tracks calls/tokens (rudimentary cost/rate checks).
    *   [`_ingest_from_file()`](../../recursive_training/data/ingestion_manager.py:325): Uses `glob` to find files (JSON, CSV), reads them, and optionally archives.
    *   [`_ingest_from_database()`](../../recursive_training/data/ingestion_manager.py:378): Uses `sqlalchemy` to connect and execute SQL queries.
4.  **Data Processing ([`_process_data`](../../recursive_training/data/ingestion_manager.py:410)):**
    *   Ensures data is a list of records.
    *   For each record:
        *   Checks against `processed_data_hashes` to prevent duplicates.
        *   If `validate_schema` is true, attempts validation (e.g., using [`ForecastRecord`](../../core/schemas.py) for `pulse_forecasts` source).
        *   Stores valid, new records in [`RecursiveDataStore`](../../recursive_training/data/data_store.py:20) along with metadata (source ID, timestamp, type).
        *   Adds record hash to `processed_data_hashes`.
5.  **Auxiliary Data Retrieval:**
    *   [`get_rule_data()`](../../recursive_training/data/ingestion_manager.py:520): Dynamically imports and calls functions from `simulation_engine` and `symbolic_system` to fetch causal and symbolic rules, adding trust scores if available.
    *   [`get_system_metadata()`](../../recursive_training/data/ingestion_manager.py:579): Compiles metadata about active sources, rule counts, token usage, and Pulse version.
    *   [`get_cost_summary()`](../../recursive_training/data/ingestion_manager.py:641): Returns a summary of tracked costs and usage.
6.  **Singleton Access:** The [`get_ingestion_manager()`](../../recursive_training/data/ingestion_manager.py:666) function ensures only one instance of the manager is used throughout the application.

## 10. Naming Conventions

*   **Overall:** Adheres well to PEP 8 standards.
*   **Classes:** PascalCase (e.g., [`RecursiveDataIngestionManager`](../../recursive_training/data/ingestion_manager.py:84)).
*   **Methods & Functions:** snake_case (e.g., [`ingest_from_source`](../../recursive_training/data/ingestion_manager.py:240), [`_load_config`](../../recursive_training/data/ingestion_manager.py:147)). Private/internal methods are prefixed with a single underscore.
*   **Variables & Parameters:** snake_case (e.g., `config_path`, `source_id`).
*   **Constants/Flags:** `UPPER_CASE_WITH_UNDERSCORES` (e.g., `PULSE_CONFIG_AVAILABLE`).
*   **Clarity:** Names are generally descriptive and understandable.
*   **Consistency:** Maintained throughout the module. No significant deviations or potential AI assumption errors in naming were noted beyond minor leftover comments from refactoring (e.g., around line [`# Use global import`](../../recursive_training/data/ingestion_manager.py:433)).