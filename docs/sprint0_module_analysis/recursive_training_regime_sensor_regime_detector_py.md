# Module Analysis: `recursive_training/regime_sensor/regime_detector.py`

**Version:** 1.0 (Assumed, based on analysis of current file)
**Date of Analysis:** 2025-05-18

## Table of Contents
1.  [Module Intent/Purpose](#1-module-intentpurpose)
2.  [Operational Status/Completeness](#2-operational-statuscompleteness)
3.  [Implementation Gaps / Unfinished Next Steps](#3-implementation-gaps--unfinished-next-steps)
4.  [Connections & Dependencies](#4-connections--dependencies)
5.  [Function and Class Example Usages](#5-function-and-class-example-usages)
6.  [Hardcoding Issues](#6-hardcoding-issues)
7.  [Coupling Points](#7-coupling-points)
8.  [Existing Tests](#8-existing-tests)
9.  [Module Architecture and Flow](#9-module-architecture-and-flow)
10. [Naming Conventions](#10-naming-conventions)

---

## 1. Module Intent/Purpose

The primary role of the [`regime_detector.py`](../../recursive_training/regime_sensor/regime_detector.py:1) module is to identify significant shifts in market or economic regimes by analyzing event streams and market data. It employs statistical methods and pattern recognition techniques to detect these changes. A key purpose is to determine when such shifts occur, as they are intended to trigger re-evaluation or adjustments in retrodiction models.

---

## 2. Operational Status/Completeness

The module provides a foundational implementation for regime detection. Key components like [`RegimeType`](../../recursive_training/regime_sensor/regime_detector.py:24), [`RegimeChangeEvent`](../../recursive_training/regime_sensor/regime_detector.py:39), and the main [`RegimeDetector`](../../recursive_training/regime_sensor/regime_detector.py:106) class are defined.

However, the actual detection logic within methods such as [`_detect_volatility_spike()`](../../recursive_training/regime_sensor/regime_detector.py:349), [`_detect_trend_reversal()`](../../recursive_training/regime_sensor/regime_detector.py:387), [`_detect_news_sentiment_shift()`](../../recursive_training/regime_sensor/regime_detector.py:445), and [`_detect_economic_indicator_shift()`](../../recursive_training/regime_sensor/regime_detector.py:533) are explicitly marked as "placeholder implementations" or "simple". Comments such as "In a production system, these would implement sophisticated algorithms" (line 347-348) indicate that the module is not yet production-ready. While there are no explicit "TODO" comments, the placeholder nature of these core detection algorithms signifies a major area of incompleteness.

---

## 3. Implementation Gaps / Unfinished Next Steps

Several areas indicate that the module is intended to be more extensive or requires further development:

*   **Sophisticated Detection Algorithms:** The current detection methods are placeholders. Future development would involve implementing advanced statistical models, machine learning techniques, or more complex rule-sets for robust regime identification.
*   **Custom Regime Detection:** While [`RegimeType.CUSTOM`](../../recursive_training/regime_sensor/regime_detector.py:36) is defined, there is no mechanism implemented to define, configure, or detect these custom regimes.
*   **Advanced Event Content Processing:** The [`_detect_news_sentiment_shift()`](../../recursive_training/regime_sensor/regime_detector.py:445) method uses basic keyword matching. A more advanced implementation would involve natural language processing (NLP) for sentiment analysis, as noted in the code (line 461-462).
*   **Granular Configuration:** The current configuration (passed to [`RegimeDetector.__init__()`](../../recursive_training/regime_sensor/regime_detector.py:112)) is basic. A more mature system would allow for detailed configuration of individual detection methods, including thresholds, parameters, and data sources.
*   **Dynamic Method Registration/Plugin System:** Detection methods are currently hardcoded during initialization. A more flexible system might allow for dynamic registration of detection methods, possibly through a plugin architecture or configuration files.
*   **Retrodiction Trigger Mechanism:** The [`RegimeChangeEvent`](../../recursive_training/regime_sensor/regime_detector.py:39) includes a `retrodiction_triggered` flag, but the actual mechanism to initiate retrodiction processes is external to this module, likely handled by registered callback handlers. Clarifying or standardizing this interaction could be a next step.

---

## 4. Connections & Dependencies

### Direct Project Module Imports
*   [`recursive_training.regime_sensor.event_stream_manager`](../../recursive_training/regime_sensor/event_stream_manager.py:1): Imports `Event`, `EventType`, `EventPriority`.

### External Library Dependencies
*   `logging`
*   `numpy` (as `np`): Imported but not directly used in the visible code; likely intended for more complex future detection algorithms.
*   `pandas` (as `pd`): Imported but not directly used in the visible code.
*   `datetime`, `timedelta` (from `datetime`)
*   `typing` (Dict, List, Optional, Any, Callable, Set, Tuple, Union)
*   `threading` (specifically `Lock`)
*   `queue`: Imported but not used in the current implementation.
*   `json`
*   `os`
*   `enum` (specifically `Enum`)

### Interaction with Other Modules/Data
*   **Event Stream:** Consumes `Event` objects, presumably produced by an `EventStreamManager` or a similar data pipeline component.
*   **Callback Handlers:** Interacts with other systems by invoking registered callback functions when a regime change is detected. These handlers receive a [`RegimeChangeEvent`](../../recursive_training/regime_sensor/regime_detector.py:39) object.
*   **Market Data:** Relies on external updates of market data through the [`update_market_data()`](../../recursive_training/regime_sensor/regime_detector.py:205) method. The structure of this data (specific dictionary keys) is implicitly defined by the detection methods.

### Input/Output Files
*   **Output:** If `storage_enabled` is true (default), detected [`RegimeChangeEvent`](../../recursive_training/regime_sensor/regime_detector.py:39) objects are serialized to JSON files. These are stored in the directory specified by `storage_path` (default: `data/regime_changes/`). Filenames are structured with the date and a unique regime change ID (e.g., `YYYY-MM-DD_regime_change_X_timestamp.json`).
*   **Input:** The module processes event data and market data provided programmatically, not by directly reading files (though the market data itself might originate from files loaded by another component).

---

## 5. Function and Class Example Usages

### `RegimeType` (Enum)
Used to define and categorize different market or economic regimes.
```python
current_condition = RegimeType.BULL_MARKET
if current_condition == RegimeType.VOLATILITY_SHOCK:
    print("Market is in a volatility shock state.")
```

### `RegimeChangeEvent` (Class)
Represents a detected regime change. Typically instantiated within the `RegimeDetector`.
```python
# Conceptual example:
# from recursive_training.regime_sensor.event_stream_manager import Event, EventType
# from datetime import datetime
#
# change_event = RegimeChangeEvent(
#     regime_change_id="rc_example_001",
#     timestamp=datetime.now(),
#     old_regime=RegimeType.EXPANSION,
#     new_regime=RegimeType.RECESSION,
#     confidence=0.75,
#     supporting_evidence=[Event(event_id="ev001", timestamp=datetime.now(), event_type=EventType.ECONOMIC_INDICATOR, source="GovStats", content="GDP declined 2%")],
#     market_indicators={'gdp_growth': -0.02, 'unemployment_rate': 0.06}
# )
# print(str(change_event))
# event_dict = change_event.to_dict()
```

### `RegimeDetector` (Class)
The main class for detecting regime changes.
```python
# from recursive_training.regime_sensor.regime_detector import RegimeDetector, RegimeChangeEvent, RegimeType
# from recursive_training.regime_sensor.event_stream_manager import Event, EventType, EventPriority
# from datetime import datetime
#
# # Initialize detector
# detector_config = {
#     'initial_regime': RegimeType.EXPANSION,
#     'min_confidence': 0.65,
#     'storage_path': 'output/regime_data'
# }
# detector = RegimeDetector(config=detector_config)
#
# # Define a handler
# def custom_regime_handler(change: RegimeChangeEvent):
#     print(f"HANDLER NOTIFIED: Regime changed from {change.old_regime} to {change.new_regime} with confidence {change.confidence:.2f}")
#     # Potentially trigger retrodiction or other actions here
#
# detector.register_change_handler(custom_regime_handler)
#
# # Simulate market data update
# market_data_update = {
#     'volatility': 45, # High volatility
#     'price': 150, 'sma_50': 145, 'sma_200': 160, # Potential death cross
#     'gdp_growth': -1.0, 'unemployment': 7.0, 'inflation': 1.5, 'interest_rates': 0.25 # Recession indicators
# }
# detector.update_market_data(market_data_update)
#
# # Simulate event processing
# news_event = Event(
#     event_id="news_panic_001",
#     timestamp=datetime.now(),
#     event_type=EventType.NEWS,
#     source="Global News Network",
#     content="Global markets in panic as new crisis emerges.",
#     priority=EventPriority.HIGH,
#     metadata={'sentiment_score': -0.9} # Assuming external sentiment scoring
# )
# detector.process_event(news_event)
#
# print(f"Final current regime: {detector.get_current_regime().value}")
# for change_event_in_history in detector.get_regime_history():
#     print(f"Historical Change: {change_event_in_history}")
```
The `if __name__ == "__main__":` block (lines 613-641) in the module itself provides a runnable basic usage example.

---

## 6. Hardcoding Issues

Several parameters, thresholds, and default values are hardcoded within the module:

*   **Configuration Defaults:**
    *   `initial_regime`: Defaults to `RegimeType.EXPANSION` ([line 120](../../recursive_training/regime_sensor/regime_detector.py:120)).
    *   `max_buffer_size`: Defaults to `1000` ([line 126](../../recursive_training/regime_sensor/regime_detector.py:126)).
    *   `min_confidence`: Defaults to `0.7` ([line 127](../../recursive_training/regime_sensor/regime_detector.py:127)).
    *   `storage_enabled`: Defaults to `True` ([line 134](../../recursive_training/regime_sensor/regime_detector.py:134)).
    *   `storage_path`: Defaults to `'data/regime_changes'` ([line 135](../../recursive_training/regime_sensor/regime_detector.py:135)).
*   **Detection Method Names:** Strings like `"volatility_spike"`, `"trend_reversal"` are used as keys for registering detection methods ([lines 146-149](../../recursive_training/regime_sensor/regime_detector.py:146-149)).
*   **`_detect_volatility_spike()`:**
    *   Volatility threshold: `volatility > 30` ([line 367](../../recursive_training/regime_sensor/regime_detector.py:367)).
    *   Confidence calculation factor: `volatility / 50.0` ([line 368](../../recursive_training/regime_sensor/regime_detector.py:368)).
    *   Event buffer lookback: `event_buffer[-20:]` ([line 372](../../recursive_training/regime_sensor/regime_detector.py:372)).
*   **`_detect_trend_reversal()`:**
    *   Confidence calculation denominator factor: `sma_200 * 0.05` ([lines 406, 426](../../recursive_training/regime_sensor/regime_detector.py:406)).
    *   Event buffer lookback: `event_buffer[-30:]` ([line 409](../../recursive_training/regime_sensor/regime_detector.py:409)).
*   **`_detect_news_sentiment_shift()`:**
    *   Keyword lists for sentiment: `crisis_keywords`, `recession_keywords`, etc. ([lines 465-469](../../recursive_training/regime_sensor/regime_detector.py:465-469)).
    *   Event count thresholds: `len(news_events) < 10` ([line 458](../../recursive_training/regime_sensor/regime_detector.py:458)), `monetary_count > 5` ([line 487](../../recursive_training/regime_sensor/regime_detector.py:487)), `count >= 5` ([line 505](../../recursive_training/regime_sensor/regime_detector.py:505)).
    *   Confidence scaling factor: `* 2` ([line 502](../../recursive_training/regime_sensor/regime_detector.py:502)).
    *   Event buffer lookback: `event_buffer[-50:]` ([line 454](../../recursive_training/regime_sensor/regime_detector.py:454)).
*   **`_detect_economic_indicator_shift()`:**
    *   Recession thresholds: `gdp_growth < 0`, `unemployment > 5.5` ([line 553](../../recursive_training/regime_sensor/regime_detector.py:553)). Confidence factors `0.2`, `0.1` ([line 554](../../recursive_training/regime_sensor/regime_detector.py:554)).
    *   Inflation threshold: `inflation > 4.0` ([line 572](../../recursive_training/regime_sensor/regime_detector.py:572)). Confidence factor `0.25` ([line 573](../../recursive_training/regime_sensor/regime_detector.py:573)).
    *   Expansion thresholds: `gdp_growth > 2.5`, `unemployment < 5.0` ([line 591](../../recursive_training/regime_sensor/regime_detector.py:591)). Confidence factors `0.2`, `0.1` ([line 592](../../recursive_training/regime_sensor/regime_detector.py:592)).
    *   Event buffer lookback: `event_buffer[-40:]` ([line 557](../../recursive_training/regime_sensor/regime_detector.py:557)).

These hardcoded values should ideally be configurable, perhaps through the main `config` object or a more detailed configuration structure for each detection method.

---

## 7. Coupling Points

*   **`EventStreamManager` Module:** Tightly coupled with the `Event`, `EventType`, and `EventPriority` enums/classes defined in [`recursive_training.regime_sensor.event_stream_manager`](../../recursive_training/regime_sensor/event_stream_manager.py:1). Changes in that module's data structures would directly impact this detector.
*   **External Callback Handlers:** The `RegimeDetector` relies on external functions (handlers) to process and act upon detected regime changes. The primary contract is the [`RegimeChangeEvent`](../../recursive_training/regime_sensor/regime_detector.py:39) object passed to these handlers.
*   **Market Data Structure:** Detection methods implicitly expect certain keys (e.g., `'volatility'`, `'price'`, `'sma_50'`, `'gdp_growth'`) to be present in the `self.market_data` dictionary. Any changes to the source or structure of this market data would necessitate updates within the detection methods.
*   **Configuration Object:** The module's behavior is partly controlled by a dictionary-based configuration passed during initialization.
*   **File System (for Storage):** If data storage is enabled, the module interacts with the file system by writing JSON files to a specified path. This creates a dependency on file system accessibility and write permissions.

---

## 8. Existing Tests

Based on the provided file list and the content of the module itself:
*   There is no dedicated test file such as `tests/recursive_training/regime_sensor/test_regime_detector.py` found in the workspace.
*   The module contains an `if __name__ == "__main__":` block ([lines 613-641](../../recursive_training/regime_sensor/regime_detector.py:613-641)). This block serves as a basic smoke test or an example of how to use the `RegimeDetector`, but it does not constitute a formal, comprehensive unit test suite. It demonstrates instantiation, handler registration, and a single market data update.

**Conclusion:** There appear to be no formal unit tests for this module. Comprehensive tests would be needed to verify the logic of individual detection methods (especially once they are more sophisticated), the regime change handling process, data storage, and edge cases.

---

## 9. Module Architecture and Flow

### Core Components
*   **`RegimeType` (Enum):** Defines a set of possible market/economic regimes (e.g., `BULL_MARKET`, `RECESSION`).
*   **`RegimeChangeEvent` (Data Class):** Encapsulates all relevant information about a detected regime change, including old/new regimes, confidence, timestamp, supporting evidence, and market indicators.
*   **`RegimeDetector` (Main Class):**
    *   Manages the current detected market regime state.
    *   Maintains an internal buffer for incoming `Event` objects and a dictionary for current `market_data`.
    *   Allows registration of various detection methods (functions that analyze data and suggest regime changes).
    *   Orchestrates the execution of these detection methods.
    *   Aggregates results from different methods, determines the most likely new regime if a change is detected with sufficient confidence.
    *   Handles the regime change by updating its internal state, notifying registered callback handlers, and optionally storing the change event to history and disk.

### Control Flow
1.  The `RegimeDetector` is initialized, setting up default configurations and registering initial (placeholder) detection methods.
2.  External systems provide data to the detector:
    *   Events are processed via [`process_event()`](../../recursive_training/regime_sensor/regime_detector.py:173) or [`process_events_batch()`](../../recursive_training/regime_sensor/regime_detector.py:189), adding them to an internal `event_buffer`.
    *   Market data is updated via [`update_market_data()`](../../recursive_training/regime_sensor/regime_detector.py:205).
3.  Following any data update, the internal [`_check_for_regime_change()`](../../recursive_training/regime_sensor/regime_detector.py:218) method is invoked.
4.  [`_check_for_regime_change()`](../../recursive_training/regime_sensor/regime_detector.py:218) iterates through all registered detection functions (e.g., [`_detect_volatility_spike()`](../../recursive_training/regime_sensor/regime_detector.py:349)).
5.  Each detection function analyzes `self.event_buffer` and `self.market_data`. If it identifies a potential regime, it returns a tuple: `(RegimeType, confidence_score, list_of_supporting_events, dict_of_market_indicators)`. Otherwise, it returns `None`.
6.  The results from all detection methods are aggregated. If multiple regimes are detected, the one with the highest confidence score is selected.
7.  If this `new_regime` is different from the `self.current_regime` and its `highest_confidence` meets the `self.min_confidence` threshold, a regime change is confirmed.
8.  The [`_handle_regime_change()`](../../recursive_training/regime_sensor/regime_detector.py:268) method is then called:
    *   It creates a [`RegimeChangeEvent`](../../recursive_training/regime_sensor/regime_detector.py:39) object.
    *   Updates `self.current_regime` to the `new_regime`.
    *   Appends the `RegimeChangeEvent` to `self.change_history`.
    *   If storage is enabled, it calls [`_store_regime_change()`](../../recursive_training/regime_sensor/regime_detector.py:317) to save the event as a JSON file.
    *   Finally, it iterates through all registered `handlers` and calls each one, passing the `RegimeChangeEvent` object.

### Data Flow
*   **Input:** `Event` objects (from `event_stream_manager`), `market_data` (Python dictionary).
*   **Internal State:** `event_buffer` (list of `Event` objects), `market_data` (dictionary), `current_regime` (`RegimeType` enum member), `change_history` (list of `RegimeChangeEvent` objects).
*   **Output:** `RegimeChangeEvent` objects are the primary output, passed to external handlers and optionally serialized to JSON files.

---

## 10. Naming Conventions

The naming conventions within the module generally adhere well to PEP 8 standards:

*   **Classes:** `RegimeType`, `RegimeChangeEvent`, `RegimeDetector` use PascalCase.
*   **Enum Members:** `BULL_MARKET`, `VOLATILITY_SHOCK`, etc., use UPPER_CASE_WITH_UNDERSCORES.
*   **Methods and Functions:** `_initialize_detection_methods`, `process_event`, `to_dict` use snake_case. Methods intended for internal use are prefixed with a single underscore (e.g., [`_check_for_regime_change()`](../../recursive_training/regime_sensor/regime_detector.py:218)).
*   **Variables:** `current_regime`, `market_data`, `supporting_evidence`, `change_id` use snake_case.
*   **Constants/Configuration Keys (as strings):** String literals used as keys (e.g., `'initial_regime'`, `'volatility'`, `'sma_50'`) are typically lowercase with underscores.
*   **File Paths:** The default storage path `data/regime_changes` is a clear, descriptive string.

Overall, the naming is consistent and clear. There are no apparent AI assumption errors or significant deviations from Python community standards. Financial terms like `vix`, `sma_50`, and `sma_200` are used appropriately.