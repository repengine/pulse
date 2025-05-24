# Module Analysis: `data/ground_truth_generator.py`

## 1. Module Intent/Purpose

The primary purpose of the [`data/ground_truth_generator.py`](data/ground_truth_generator.py:1) module is to create and maintain a comprehensive ground truth financial dataset. This dataset is intended for use in training and backtesting AI models within the Pulse project. It achieves this by fetching data from various external financial APIs, processing it, and storing it in a structured format.

## 2. Key Functionalities

*   **Data Aggregation:** Fetches economic indicators and market data from multiple sources:
    *   FRED (Federal Reserve Economic Data)
    *   World Bank
    *   Alpha Vantage (stocks, cryptocurrencies)
    *   Finnhub (stocks)
    *   NASDAQ (placeholder, intended for market data)
*   **Variable Mapping:** Dynamically maps variables defined in Pulse's `VARIABLE_REGISTRY` (or a fallback internal registry if the main one is unavailable) to specific API endpoints and series/symbol identifiers.
*   **API Management:**
    *   Handles API key retrieval from environment variables.
    *   Implements rate limiting to avoid exceeding API call quotas.
    *   Tracks estimated API call costs against a configurable budget.
*   **Data Processing & Storage:**
    *   Processes fetched data into a standardized format.
    *   Saves economic indicators to [`data/ground_truth_dataset/economic_indicators.csv`](data/ground_truth_dataset/economic_indicators.csv).
    *   Saves market data to [`data/ground_truth_dataset/market_data.csv`](data/ground_truth_dataset/market_data.csv).
*   **Documentation & Metadata:**
    *   Generates a [`data/ground_truth_dataset/metadata.json`](data/ground_truth_dataset/metadata.json) file detailing dataset fields, sources, update frequencies, API key status, variable coverage, and cost tracking.
    *   Generates a [`data/ground_truth_dataset/README.md`](data/ground_truth_dataset/README.md) file explaining the dataset's content, usage, and update instructions.
*   **Command-Line Interface (CLI):** Provides options to:
    *   Specify data sources to use.
    *   Define the historical date range for data fetching.
    *   Set a maximum budget for API calls.
    *   Select specific variable types (economic, market) to include.
*   **Scheduling:** Optionally supports scheduled updates (daily/weekly) using the `apscheduler` library if available.
*   **Logging:** Implements logging to [`data/ground_truth_dataset/ground_truth_generator.log`](data/ground_truth_dataset/ground_truth_generator.log) for tracking the data generation process and errors.

## 3. Role Within `data/` Directory

This module serves as the central script for populating and maintaining the `data/ground_truth_dataset/` subdirectory. It is responsible for external data acquisition and structuring it into a usable format for other parts of the Pulse system that rely on historical financial data.

## 4. Dependencies

### External Libraries:
*   `os`
*   `sys`
*   `json`
*   `time`
*   `logging`
*   `argparse`
*   `requests`
*   `pandas`
*   `datetime` (from `datetime` module)
*   `Path` (from `pathlib` module)
*   `typing` (Dict, List, Any, Optional, Set, Tuple, Union, cast)
*   `apscheduler` (optional, for scheduling updates)

### Internal Pulse Modules:
*   [`core.variable_registry`](core/variable_registry.py:0) (optional): The script attempts to import `VARIABLE_REGISTRY` from this module. If unavailable, it uses a hardcoded fallback registry.

## 5. SPARC Principles Adherence

*   **Module Intent/Purpose:**
    *   **Clarity:** The intent is very clear: generate a ground truth financial dataset.
    *   **Adherence:** High. The module is focused solely on this task.

*   **Operational Status/Completeness:**
    *   **Status:** Largely operational and complete.
    *   **Details:** It successfully fetches data from most intended sources, processes it, handles API interactions, and generates output files. Scheduling is a functional optional feature.

*   **Implementation Gaps / Unfinished Next Steps:**
    *   **NASDAQ API Integration:** Explicitly marked as "TODO" ([`data/ground_truth_generator.py:720`](data/ground_truth_generator.py:720)). Currently, it falls back to Alpha Vantage if the NASDAQ key is not set or uses a placeholder.
    *   **Granular Error Handling:** While general error handling for API requests exists, it could be more specific for different HTTP status codes or API-specific error messages.
    *   **Fallback Registry Scope:** The fallback `VARIABLE_REGISTRY` is minimal. The module's comprehensiveness heavily relies on the actual `core.variable_registry`.
    *   **Configuration for API Costs/Limits:** `API_COSTS` and `API_LIMITS` are hardcoded; making them configurable (e.g., via a config file) could improve flexibility.

*   **Connections & Dependencies:**
    *   **External APIs:** Connects to FRED, World Bank, Alpha Vantage, Finnhub. Intends to connect to NASDAQ.
    *   **Environment Variables:** Relies on `ALPHA_VANTAGE_KEY`, `FINNHUB_KEY`, `FRED_KEY`, `NASDAQ_KEY` for API access.
    *   **File System:** Reads no specific input configuration files (beyond Python imports). Writes output CSVs, JSON metadata, README, and a log file to the `data/ground_truth_dataset/` directory.
    *   **Internal Modules:** Optionally depends on [`core.variable_registry`](core/variable_registry.py:0).

*   **Function and Class Example Usages:**
    *   The script is primarily procedural.
    *   **Data Fetching:** Functions like [`fetch_fred(var_name, series_id, start_date, end_date)`](data/ground_truth_generator.py:392), [`fetch_alpha_vantage(var_name, symbol, start_date, end_date)`](data/ground_truth_generator.py:525).
    *   **Orchestration:** The [`main()`](data/ground_truth_generator.py:955) function parses arguments and calls generator functions like [`generate_economic_indicators(...)`](data/ground_truth_generator.py:728) and [`generate_market_data(...)`](data/ground_truth_generator.py:773).
    *   **Utility:** [`safe_get(url, params, api)`](data/ground_truth_generator.py:331) for robust API calls.

*   **Hardcoding Issues:**
    *   `API_COSTS`: ([`data/ground_truth_generator.py:98`](data/ground_truth_generator.py:98)) Estimated costs per API call.
    *   `API_LIMITS`: ([`data/ground_truth_generator.py:110`](data/ground_truth_generator.py:110)) Rate limits per API.
    *   `TOTAL_BUDGET`: ([`data/ground_truth_generator.py:106`](data/ground_truth_generator.py:106)) Default budget, though overridable via CLI.
    *   Fallback `VARIABLE_REGISTRY`: ([`data/ground_truth_generator.py:38`](data/ground_truth_generator.py:38)) Used if `core.variable_registry` import fails.
    *   `DATASET_DIR`: ([`data/ground_truth_generator.py:68`](data/ground_truth_generator.py:68)) Path to the output directory.
    *   Manual Mappings in [`map_registry_to_sources()`](data/ground_truth_generator.py:122): ([`data/ground_truth_generator.py:181`](data/ground_truth_generator.py:181)) Specific variable-to-source mappings. This is somewhat necessary for ensuring critical variables are correctly sourced.
    *   Log file path: ([`data/ground_truth_generator.py:18`](data/ground_truth_generator.py:18)).

*   **Coupling Points:**
    *   **`VARIABLE_REGISTRY` Structure:** Tightly coupled to the expected dictionary structure of `VARIABLE_REGISTRY` (or its fallback).
    *   **External API Formats:** Directly parses JSON responses from external APIs. Changes in these API response structures would break the respective fetcher functions.
    *   **Output File Structure:** The schema of the output CSV files is implicitly defined by the data processing logic.

*   **Existing Tests:**
    *   No unit tests or integration tests are present within this module or explicitly referenced.
    *   Testing would typically involve mocking `requests.get` calls, simulating different API responses (success, errors, rate limits), and verifying the content and structure of the generated CSV and JSON files.

*   **Module Architecture and Flow:**
    1.  **Initialization:** Sets up logging, loads API keys, defines constants (costs, limits, directories).
    2.  **Variable Mapping:** The [`map_registry_to_sources()`](data/ground_truth_generator.py:122) function attempts to parse `VARIABLE_REGISTRY` or uses manual/fallback mappings to link Pulse variables to API-specific identifiers. This populates `ECON_INDICATORS` and `MARKET_SYMBOLS`.
    3.  **Helper Functions:** Provides utilities for rate limiting ([`rate_limit()`](data/ground_truth_generator.py:308)), cost tracking ([`track_cost()`](data/ground_truth_generator.py:323)), and safe API GET requests ([`safe_get()`](data/ground_truth_generator.py:331)).
    4.  **Fetcher Functions:** Dedicated functions for each API source (e.g., [`fetch_fred()`](data/ground_truth_generator.py:392), [`fetch_world_bank()`](data/ground_truth_generator.py:445), etc.) handle the specifics of querying and parsing data.
    5.  **Data Generation Functions:** [`generate_economic_indicators()`](data/ground_truth_generator.py:728) and [`generate_market_data()`](data/ground_truth_generator.py:773) orchestrate calls to the fetcher functions based on selected sources and variable types, then compile results into pandas DataFrames and save them to CSV.
    6.  **Documentation Generation:** [`write_metadata()`](data/ground_truth_generator.py:819) and [`write_readme()`](data/ground_truth_generator.py:890) create supporting documentation files.
    7.  **CLI and Main Logic:** The [`main()`](data/ground_truth_generator.py:955) function handles argument parsing, sets up the overall process, and can optionally schedule recurring runs via `apscheduler`.
    *   The flow is logical: configuration -> mapping -> fetching -> processing -> saving -> documenting.

*   **Naming Conventions:**
    *   Generally adheres to Python PEP 8 standards.
    *   Functions and local variables use `snake_case` (e.g., [`fetch_fred()`](data/ground_truth_generator.py:392), `series_id`).
    *   Constants use `UPPER_SNAKE_CASE` (e.g., `ALPHA_VANTAGE_KEY`, `DATASET_DIR`).
    *   Class names (though none are defined in this script, `Path` and `datetime` are used) would be `CapWords`.

## 6. Overall Assessment

*   **Completeness:** High. The module is quite comprehensive in its goal of generating a financial dataset. It handles multiple data sources, API complexities (keys, rates, costs), data storage, and basic documentation. The main identified gap is the full implementation of the NASDAQ API.
*   **Quality:** Good.
    *   **Strengths:**
        *   Modular design with separate functions for different concerns (fetching, processing, API interaction).
        *   Good use of logging for traceability.
        *   Error handling for API requests and data parsing is present.
        *   Attempts to integrate with a central `VARIABLE_REGISTRY`, promoting consistency.
        *   Includes practical features like cost tracking and rate limiting.
        *   CLI provides useful flexibility.
        *   Use of `pathlib` for path management and `typing` for type hints improves code clarity and maintainability.
    *   **Areas for Improvement:**
        *   Complete NASDAQ API integration.
        *   Consider making `API_COSTS`, `API_LIMITS`, and `DATASET_DIR` configurable rather than hardcoded.
        *   More robust error handling for specific API error codes.
        *   Addition of unit and integration tests would significantly improve reliability.

## 7. Summary Note for Main Report

The [`data/ground_truth_generator.py`](data/ground_truth_generator.py:1) module is a well-structured and largely complete script for creating a financial ground truth dataset by fetching data from multiple APIs (FRED, World Bank, Alpha Vantage, Finnhub), managing API keys, costs, and rate limits, and generating CSVs with metadata. While robust, full NASDAQ API integration is a pending task, and certain configurations like API costs are currently hardcoded.