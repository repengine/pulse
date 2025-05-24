# Module Analysis: `iris/iris_plugins_variable_ingestion/financial_news_plugin.py`

## 1. Module Intent/Purpose

The primary role of the [`financial_news_plugin.py`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py) module is to connect to external financial news APIs (specifically AlphaVantage and NewsAPI) to retrieve news articles. It then analyzes these articles to derive sentiment scores and news volume, generating "signals" related to specific companies, market sectors, financial topics, and the overall market. These signals are intended for further use within the Iris system.

## 2. Operational Status/Completeness

The module appears largely functional for its defined scope.
- It correctly handles API key retrieval from environment variables ([`ALPHAVANTAGE_API_KEY`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:85), [`NEWSAPI_KEY`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:86)) and disables itself if keys are missing.
- It implements fetching logic for various news categories (company, sector, topic, market).
- A basic, rule-based sentiment analysis function ([`_calculate_sentiment_score`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:444)) is included.
- It utilizes helper functions from [`iris.iris_utils.ingestion_persistence`](../../iris/iris_utils/ingestion_persistence.py) for saving request metadata, raw API responses, and processed signal data.
- The sentiment analysis ([`_calculate_sentiment_score`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:444)) is explicitly noted as a "simplified version" (line 447), indicating a known area for future enhancement rather than an incomplete feature for its current implementation.
- No other obvious TODOs or major placeholders are present.

## 3. Implementation Gaps / Unfinished Next Steps

-   **Advanced Sentiment Analysis:** The current sentiment calculation ([`_calculate_sentiment_score`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:444)) is basic. The module itself suggests (line 447-448) using a more sophisticated NLP model or service for improved accuracy.
-   **Configuration of Keywords/Entities:** Lists like [`TOP_COMPANIES`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:43), [`SECTORS`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:57), [`TOPICS`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:69), and various search term mappings (e.g., `company_names` in [`_fetch_company_news`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:314)) are hardcoded. Externalizing these to a configuration file would improve flexibility.
-   **Extensibility for News Providers:** While the docstring mentions supporting "other financial news providers" (line 6), the implementation is tightly coupled to AlphaVantage and NewsAPI. Adding new providers would require significant code additions.
-   **Deeper News Analysis:** The plugin currently extracts sentiment and volume. Future enhancements could include named entity recognition (NER), event detection, or finer-grained topic modeling.
-   **Robust API Response Parsing:** While network and status code errors are handled, parsing of the actual content from API responses could be more resilient to unexpected changes in the API's data structure.

## 4. Connections & Dependencies

### Direct Project Module Imports
-   [`from iris.iris_plugins import IrisPluginManager`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:17)
-   [`from iris.iris_utils.ingestion_persistence import ensure_data_directory, save_request_metadata, save_api_response, save_processed_data`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:18-23)

### External Library Dependencies
-   `datetime` (as `dt`)
-   `logging`
-   `time`
-   `os`
-   `json`
-   `re`
-   `requests`

### Interactions via Shared Data
-   **Environment Variables:** Reads `ALPHAVANTAGE_API_KEY` and `NEWSAPI_KEY`.
-   **File System:** Interacts with the file system via [`iris.iris_utils.ingestion_persistence`](../../iris/iris_utils/ingestion_persistence.py) to store:
    -   Request metadata (e.g., in `data/financial_news/requests/`)
    -   Raw API responses (e.g., in `data/financial_news/responses/`)
    -   Processed signal data (e.g., in `data/financial_news/processed/`)

### Input/Output Files
-   **Output:**
    -   JSON files for request metadata.
    -   JSON files for API responses.
    -   JSON files for processed signals.
-   **Input:** None directly from the file system; primary inputs are responses from external APIs.

## 5. Function and Class Example Usages

### `FinancialNewsPlugin` Class
The `FinancialNewsPlugin` class is designed to be managed by an Iris plugin system.
```python
# Hypothetical usage within Iris plugin management
# from iris.iris_plugins_variable_ingestion.financial_news_plugin import FinancialNewsPlugin

# financial_news_plugin_instance = FinancialNewsPlugin()

# if financial_news_plugin_instance.enabled:
#     signals = financial_news_plugin_instance.fetch_signals()
#     for signal_data in signals:
#         # Process signal_data
#         print(f"Generated signal: {signal_data['name']} - Value: {signal_data['value']}")
```
The core method is [`fetch_signals()`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:103), which orchestrates calls to various internal `_fetch_*` and `_process_*` methods.

### [`_calculate_sentiment_score(text: str)`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:444)
This internal method is used to perform basic sentiment analysis on news text when a pre-calculated score isn't provided by the API (e.g., NewsAPI).
```python
# score = self._calculate_sentiment_score("Market shows strong growth and record profits.")
# print(score) # Expected positive score
```

## 6. Hardcoding Issues

-   **API Configuration:**
    -   Base URLs: [`ALPHAVANTAGE_BASE_URL`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:36), [`NEWSAPI_BASE_URL`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:37).
    -   Request parameters: [`REQUEST_TIMEOUT`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:38), [`RETRY_WAIT`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:39), [`MAX_RETRIES`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:40).
-   **Tracked Entities & Keywords:**
    -   [`TOP_COMPANIES`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:43) (list of stock symbols).
    -   [`SECTORS`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:57) (list of sector names).
    -   [`TOPICS`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:69) (list of topic keywords).
-   **Search Term Mappings:**
    -   `company_names` dictionary in [`_fetch_company_news()`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:314).
    -   `sector_terms` dictionary in [`_fetch_sector_news()`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:347).
    -   `topic_terms` dictionary in [`_fetch_topic_news()`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:380).
    -   Market news query string in [`_fetch_market_news()`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:430).
-   **Sentiment Analysis Keywords:**
    -   `positive_terms` and `negative_terms` lists within [`_calculate_sentiment_score()`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:457,463).
-   **API Request Limits:** Hardcoded limits/page sizes in API calls (e.g., `limit: 10`, `pageSize: 10`).
-   **Internal Identifiers:**
    -   [`_SOURCE_NAME = "financial_news"`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:28) (used for data persistence).
    -   Dataset IDs for persistence are constructed with f-strings (e.g., `f"company_news_{symbol}"`).

## 7. Coupling Points

-   **`IrisPluginManager`:** Tightly coupled through inheritance.
-   **`iris.iris_utils.ingestion_persistence`:** Tightly coupled for all data storage operations (metadata, responses, processed signals).
-   **Environment Variables:** Dependent on `ALPHAVANTAGE_API_KEY` and `NEWSAPI_KEY` for operation.
-   **External APIs (AlphaVantage, NewsAPI):** Directly interacts with these services, making it susceptible to their availability, rate limits, and changes in API contracts.
-   **File System:** Implicitly coupled via `ingestion_persistence` which writes to a predefined directory structure (e.g., `data/financial_news/...`).

## 8. Existing Tests

Based on the provided file listing, there is no dedicated test file specifically for `financial_news_plugin.py` (e.g., `tests/plugins/test_financial_news_plugin.py`).
-   Files like [`iris/test_newsapi_direct.py`](../../iris/test_newsapi_direct.py) and [`iris/test_alpha_vantage.py`](../../iris/test_alpha_vantage.py) might test direct interactions with these APIs, which are used by this plugin.
-   However, specific unit tests for the plugin's logic, its scheduling mechanism ([`fetch_signals`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:103)), data processing methods (e.g., [`_process_company_news`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:483)), and sentiment calculation ([`_calculate_sentiment_score`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:444)) appear to be missing.
-   Testing would likely require mocking `requests.get` calls and the functions from `ingestion_persistence`.

## 9. Module Architecture and Flow

1.  **Initialization ([`__init__`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:82)):**
    *   Loads API keys from environment variables.
    *   Enables plugin if keys are present.
    *   Initializes data storage directory via [`ensure_data_directory`](../../iris/iris_utils/ingestion_persistence.py:19).
    *   Sets up rotation counters for distributing API calls across companies, sectors, and topics.
2.  **Signal Fetching ([`fetch_signals`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:103)):**
    *   Acts as the main entry point for the plugin.
    *   Uses a time-based mechanism (current hour) to decide which category of news to fetch (company, sector, topic, or general market). This distributes API load.
    *   Rotates through predefined lists of companies, sectors, and topics for targeted news.
    *   Calls internal `_fetch_*` methods (e.g., [`_fetch_company_news`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:296)) to get data from APIs.
    *   Calls internal `_process_*` methods (e.g., [`_process_company_news`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:483)) to transform raw data into structured signals.
    *   Returns a list of generated signal dictionaries.
3.  **Safe API Interaction ([`_safe_get_alphavantage`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:155), [`_safe_get_newsapi`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:225)):**
    *   Wrapper functions for making requests to AlphaVantage and NewsAPI respectively.
    *   Handle API key injection, parameter construction, and request metadata saving.
    *   Implement retry logic ([`MAX_RETRIES`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:40), [`RETRY_WAIT`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:39)).
    *   Perform basic error checking on responses (HTTP status, API-specific error messages, rate limits).
    *   Save raw API responses.
4.  **Specific Data Fetching (e.g., [`_fetch_company_news`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:296)):**
    *   Logic to fetch news for a specific entity (company, sector, topic).
    *   Prefers AlphaVantage if available, otherwise falls back to NewsAPI.
    *   Adapts search queries based on the API (e.g., company symbol for AlphaVantage, company name for NewsAPI).
5.  **Data Processing (e.g., [`_process_company_news`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:483)):**
    *   Transforms raw API data into a standardized list of signals.
    *   Extracts or calculates sentiment scores (using AlphaVantage's score or [`_calculate_sentiment_score`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:444) for NewsAPI).
    *   Calculates news volume (number of articles).
    *   Formats signals with `name`, `value`, `source`, `timestamp`, and `metadata`.
    *   Saves processed signals using [`save_processed_data`](../../iris/iris_utils/ingestion_persistence.py:22).
6.  **Sentiment Calculation ([`_calculate_sentiment_score`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:444)):**
    *   A simple rule-based function that counts predefined positive and negative financial terms in a given text.
    *   Returns a normalized sentiment score between -1.0 (negative) and 1.0 (positive).

## 10. Naming Conventions

-   **Class:** `FinancialNewsPlugin` (PascalCase) - Clear and appropriate.
-   **Methods:**
    -   Public: `fetch_signals` (snake_case) - Adheres to Python conventions.
    -   Internal: Prefixed with an underscore (e.g., `_safe_get_alphavantage`, `_process_company_news`) - Correctly indicates internal use.
-   **Variables:** Generally snake_case (e.g., `alphavantage_api_key`, `avg_sentiment`).
-   **Constants:** UPPER_SNAKE_CASE (e.g., [`ALPHAVANTAGE_BASE_URL`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:36), [`TOP_COMPANIES`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:43), [`_SOURCE_NAME`](../../iris/iris_plugins_variable_ingestion/financial_news_plugin.py:28)) - Standard practice.
-   **Signal Naming:** Constructed dynamically (e.g., `f"news_sentiment_{symbol.lower()}"`) providing a consistent pattern.
-   The module largely adheres to PEP 8 naming conventions. No obvious AI-generated or unconventional naming patterns were observed.