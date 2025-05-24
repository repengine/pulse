# Module Analysis: `recursive_training.data.feature_processor_integration`

**File Path:** [`recursive_training/data/feature_processor_integration.py`](recursive_training/data/feature_processor_integration.py)

## 1. Module Intent/Purpose

This module serves as an integration layer, enhancing a standard feature processor by incorporating advanced data processing techniques. Its primary role is to provide an [`EnhancedFeatureProcessor`](recursive_training/data/feature_processor_integration.py:15) class that wraps the [`RecursiveFeatureProcessor`](recursive_training/data/feature_processor.py:12) and adds capabilities for time-frequency decomposition, graph-based features, and self-supervised representation learning by delegating to functions from [`recursive_training.data.advanced_feature_processor`](recursive_training/data/advanced_feature_processor.py).

## 2. Operational Status/Completeness

The module appears largely complete for its defined scope. It implements the [`EnhancedFeatureProcessor`](recursive_training/data/feature_processor_integration.py:15) with core methods for feature extraction, fitting, and transformation. It also provides a singleton accessor function [`get_enhanced_feature_processor()`](recursive_training/data/feature_processor_integration.py:170).
A minor point for potential extension is noted in the [`transform()`](recursive_training/data/feature_processor_integration.py:100) method regarding additional transformations specific to advanced features (comment on [`line 117`](recursive_training/data/feature_processor_integration.py:117)).

## 3. Implementation Gaps / Unfinished Next Steps

*   **Advanced Feature Transformations:** The comment in [`transform()`](recursive_training/data/feature_processor_integration.py:117) ("`# Add any additional transformations specific to advanced features # For now, we'll keep the advanced features as they are`") suggests that further transformations specific to the advanced features could be implemented.
*   **Fitting Advanced Processors:** The [`fit()`](recursive_training/data/feature_processor_integration.py:82) method primarily fits the `standard_processor`. While advanced processing is done via [`process_with_advanced_techniques()`](recursive_training/data/advanced_feature_processor.py:13), it's not explicitly clear if or how any stateful components within the advanced techniques are fitted through this class. This might be handled within the imported function itself.
*   **Feature Naming/Importance for Advanced Features:** The methods [`get_feature_names()`](recursive_training/data/feature_processor_integration.py:133) and [`get_feature_importance()`](recursive_training/data/feature_processor_integration.py:142) delegate solely to the `standard_processor`. If advanced features are added (especially if `integrate_features` is `False`), these methods might not accurately reflect the complete set of features or their respective importances.

## 4. Connections & Dependencies

### Project Modules:
*   [`recursive_training.data.feature_processor`](recursive_training/data/feature_processor.py): Imports [`RecursiveFeatureProcessor`](recursive_training/data/feature_processor.py:12) and [`get_feature_processor()`](recursive_training/data/feature_processor.py:12).
*   [`recursive_training.data.advanced_feature_processor`](recursive_training/data/advanced_feature_processor.py): Imports [`process_with_advanced_techniques()`](recursive_training/data/advanced_feature_processor.py:13) and [`integrate_with_pipeline()`](recursive_training/data/advanced_feature_processor.py:13).

### External Libraries:
*   `logging` (Python standard library)
*   `typing` (Python standard library: `Dict`, `List`, `Any`, `Optional`)

### Data Interactions:
*   Processes input `data_items` (expected to be `List[Dict[str, Any]]`).
*   Uses a `config` dictionary for its settings.
*   No direct file I/O observed, aside from potential logging.

## 5. Function and Class Example Usages

### [`EnhancedFeatureProcessor`](recursive_training/data/feature_processor_integration.py:15)
```python
from recursive_training.data.feature_processor_integration import EnhancedFeatureProcessor

# Example configuration
config = {
    "enable_advanced_processing": True,
    "integrate_advanced_features": True,
    "advanced_features": {
        # Configuration for advanced techniques (e.g., wavelets, graph features)
        "wavelet_config": {"enabled": True, "families": ["db1"]},
        "graph_config": {"enabled": False}
    }
    # ... other standard processor configs
}

data = [{"value": i, "timestamp": i*10} for i in range(100)] # Sample data

processor = EnhancedFeatureProcessor(config=config)
processor.fit(data)
transformed_data = processor.transform(data)
# print(transformed_data)
# feature_names = processor.get_feature_names()
# print(feature_names)
```

### [`get_enhanced_feature_processor()`](recursive_training/data/feature_processor_integration.py:170)
```python
from recursive_training.data.feature_processor_integration import get_enhanced_feature_processor

config_a = {"enable_advanced_processing": False}
processor1 = get_enhanced_feature_processor(config=config_a)

config_b = {"enable_advanced_processing": True, "advanced_features": {"wavelet_config": {"enabled": True}}}
processor2 = get_enhanced_feature_processor(config=config_b) # Updates the singleton's config

# processor1 and processor2 will be the same instance
# assert processor1 is processor2
# print(processor1.config) # Will show updated config from config_b
```

## 6. Hardcoding Issues

*   **Configuration Defaults:**
    *   `enable_advanced_processing`: Defaults to `True` ([`line 40`](recursive_training/data/feature_processor_integration.py:40)).
    *   `integrate_advanced_features`: Defaults to `True` ([`line 44`](recursive_training/data/feature_processor_integration.py:44)).
*   **Logger Name:** The logger is named `"EnhancedFeatureProcessor"` ([`line 33`](recursive_training/data/feature_processor_integration.py:33)).
*   **Dictionary Key:** If advanced features are not integrated, they are stored under the key `"advanced"` in the results dictionary ([`line 75`](recursive_training/data/feature_processor_integration.py:75)).

## 7. Coupling Points

*   **High Coupling:** Tightly coupled with:
    *   [`RecursiveFeatureProcessor`](recursive_training/data/feature_processor.py:12) and its factory [`get_feature_processor()`](recursive_training/data/feature_processor.py:12) from [`recursive_training.data.feature_processor`](recursive_training/data/feature_processor.py).
    *   Functions [`process_with_advanced_techniques()`](recursive_training/data/advanced_feature_processor.py:13) and [`integrate_with_pipeline()`](recursive_training/data/advanced_feature_processor.py:13) from [`recursive_training.data.advanced_feature_processor`](recursive_training/data/advanced_feature_processor.py).
*   **Configuration Structure:** Relies on a specific structure and keys within the `config` dictionary (e.g., `"enable_advanced_processing"`, `"advanced_features"`, `"integrate_advanced_features"`).
*   **Data Format:** Implicitly coupled to the expected format of `data_items` (`List[Dict[str, Any]]`).

## 8. Existing Tests

*   A corresponding test file exists at [`tests/recursive_training/test_feature_processor_integration.py`](tests/recursive_training/test_feature_processor_integration.py).
*   The code includes comments such as "Use the imported function directly for better testability" ([`line 63`](recursive_training/data/feature_processor_integration.py:63), [`line 69`](recursive_training/data/feature_processor_integration.py:69)), indicating that testability was a design consideration.
*   The actual coverage and nature of these tests are not assessed here.

## 9. Module Architecture and Flow

*   **Wrapper Design:** The [`EnhancedFeatureProcessor`](recursive_training/data/feature_processor_integration.py:15) class acts as a wrapper around a `standard_processor` (an instance of [`RecursiveFeatureProcessor`](recursive_training/data/feature_processor.py:12)).
*   **Conditional Advanced Processing:** It conditionally applies advanced feature processing based on the `enable_advanced` flag in its configuration.
*   **Delegation:** Advanced processing and integration are delegated to imported functions ([`process_with_advanced_techniques()`](recursive_training/data/advanced_feature_processor.py:13) and [`integrate_with_pipeline()`](recursive_training/data/advanced_feature_processor.py:13)).
*   **Configuration-Driven:** Behavior is largely driven by the `config` dictionary.
*   **Singleton Access:** Provides a singleton instance via [`get_enhanced_feature_processor()`](recursive_training/data/feature_processor_integration.py:170), which allows for a globally accessible, configurable instance.
*   **Data Flow:**
    1.  Input `data_items`.
    2.  Standard features extracted via `self.standard_processor.extract_features()`.
    3.  If `enable_advanced` is true, advanced features are generated by [`process_with_advanced_techniques()`](recursive_training/data/advanced_feature_processor.py:13).
    4.  If `integrate_features` is true, standard and advanced features are combined by [`integrate_with_pipeline()`](recursive_training/data/advanced_feature_processor.py:13); otherwise, advanced features are added under a separate key.
    5.  The `fit()` and `transform()` methods utilize these extracted features, with transformations primarily handled by the `standard_processor`.

## 10. Naming Conventions

*   **Class Names:** [`EnhancedFeatureProcessor`](recursive_training/data/feature_processor_integration.py:15) (PascalCase) - Adheres to PEP 8.
*   **Function/Method Names:** [`extract_features()`](recursive_training/data/feature_processor_integration.py:46), [`fit()`](recursive_training/data/feature_processor_integration.py:82), [`get_enhanced_feature_processor()`](recursive_training/data/feature_processor_integration.py:170) (snake_case) - Adheres to PEP 8.
*   **Variable Names:** `standard_processor`, `advanced_config`, `_enhanced_instance` (snake_case, with leading underscore for internal singleton) - Adheres to PEP 8.
*   **Consistency:** Naming is generally consistent and descriptive.
*   **No Obvious AI Errors:** Naming conventions appear standard and human-generated.