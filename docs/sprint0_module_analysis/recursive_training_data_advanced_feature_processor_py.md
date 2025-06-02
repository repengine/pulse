# Module Analysis: `recursive_training.data.advanced_feature_processor`

## 1. Module Intent/Purpose

The primary role of the [`recursive_training.data.advanced_feature_processor`](recursive_training/data/advanced_feature_processor.py:1) module is to serve as an integration point for applying various advanced data processing techniques to economic time series data. It orchestrates the application of time-frequency decomposition, graph-based feature extraction, and self-supervised representation learning, and then integrates these newly derived features with existing data pipelines.

## 2. Operational Status/Completeness

The module appears to be operationally complete for its defined scope.
- It includes the main class [`AdvancedFeatureProcessor`](recursive_training/data/advanced_feature_processor.py:21) for managing the processing.
- It provides functions for direct processing ([`process_with_advanced_techniques`](recursive_training/data/advanced_feature_processor.py:227)) and for integrating results into a broader pipeline ([`integrate_with_pipeline`](recursive_training/data/advanced_feature_processor.py:247)).
- Basic error handling (try-except blocks for each processing step) and logging are implemented.
- A caching mechanism for processed features is present ([`AdvancedFeatureProcessor.__init__`](recursive_training/data/advanced_feature_processor.py:52-62)).
- No explicit "TODO" comments or obvious placeholders for core functionality were observed within this module's code. The completeness of the underlying specialized processing modules (imported) would affect its overall end-to-end completeness.

## 3. Implementation Gaps / Unfinished Next Steps

- **Dependency on External Modules:** The core processing logic (time-frequency, graph, self-supervised) is delegated to imported functions ([`apply_time_frequency_decomposition`](recursive_training/data/advanced_feature_processor.py:16), [`apply_graph_based_features`](recursive_training/data/advanced_feature_processor.py:17), [`apply_self_supervised_learning`](recursive_training/data/advanced_feature_processor.py:18)). The module's functionality is thus highly dependent on the completeness and correctness of these external modules. Any gaps in those modules would translate to gaps here.
- **Integration Rigidity:** The feature integration logic within [`integrate_with_pipeline`](recursive_training/data/advanced_feature_processor.py:247) is specific about the keys and structure of features it expects from the advanced processing steps (e.g., `"spectral_entropy"`, `"degree_centrality"`). If the underlying modules evolve to produce different or additional features, this integration logic would require updates.
- **Basic Caching:** The current caching implementation saves the entire JSON output for each feature type. More granular or sophisticated caching (e.g., per data item, hash-based invalidation) could be a potential enhancement for efficiency, especially with large datasets or frequent partial updates.
- **Configuration Depth:** While configurable, the module primarily enables/disables entire processing categories. Deeper configuration passthrough to the underlying specialized modules might be limited by the current structure, potentially requiring direct modification of `self.time_frequency_config`, etc., within the `AdvancedFeatureProcessor` or more complex config handling.

## 4. Connections & Dependencies

### Direct Project Module Imports:
- [`recursive_training.data.time_frequency_decomposition.apply_time_frequency_decomposition`](recursive_training/data/time_frequency_decomposition.py:16)
- [`recursive_training.data.graph_based_features.apply_graph_based_features`](recursive_training/data/graph_based_features.py:17)
- [`recursive_training.data.self_supervised_analytics.apply_self_supervised_learning`](recursive_training/data/self_supervised_learning.py:18)

### External Library Dependencies:
- `logging`
- `numpy` (as `np`)
- `json`
- `os`
- `datetime` (from `datetime`)

### Interactions via Shared Data:
- **Input Data:**
    - `data_items` (List of Dictionaries): Expected input for processing by [`AdvancedFeatureProcessor.process()`](recursive_training/data/advanced_feature_processor.py:64).
    - `original_features` (Dictionary): Expected input for feature integration by [`integrate_with_pipeline()`](recursive_training/data/advanced_feature_processor.py:247).
- **Output Data:**
    - Returns a dictionary containing processed and integrated features.
- **Caching:**
    - Reads from and writes to JSON files within a specified cache directory (default: `"cache/advanced_features"`). Cache files include:
        - `time_frequency_features.json`
        - `graph_features.json`
        - `self_supervised_features.json`

### Input/Output Files:
- **Input:** Potentially configuration files if the `config` dictionary passed to [`AdvancedFeatureProcessor.__init__()`](recursive_training/data/advanced_feature_processor.py:32) is loaded from an external file by the calling code.
- **Output:**
    - Cache files as listed above.
    - Log messages via the `logging` module, which might be directed to console or log files depending on the logging configuration of the broader application.

## 5. Function and Class Example Usages

### `AdvancedFeatureProcessor` Class Usage:
```python
from recursive_training.data.advanced_feature_processor import AdvancedFeatureProcessor
import numpy as np
import json

# Example configuration
config = {
    "enable_time_frequency": True,
    "enable_graph_features": True,
    "enable_self_supervised": False, # Disable self-supervised learning
    "cache_dir": "output/my_advanced_feature_cache",
    "use_cache": True,
    "time_frequency": {"method": "wavelet", "wavelet": "db4"},
    "graph_features": {"method": "correlation", "threshold": 0.7}
}

# Dummy data items
data_items = [
    {"id": "series_A", "values": np.random.rand(100).tolist()},
    {"id": "series_B", "values": np.random.rand(100).tolist()}
]

# Initialize processor
processor = AdvancedFeatureProcessor(config=config)

# Process data
advanced_features_output = processor.process(data_items)
print(json.dumps(advanced_features_output, indent=2))
```

### `process_with_advanced_techniques` Function Usage:
```python
from recursive_training.data.advanced_feature_processor import process_with_advanced_techniques
import numpy as np
import json

# Dummy data items
data_items = [
    {"id": "series_C", "values": np.random.rand(50).tolist()},
    {"id": "series_D", "values": np.random.rand(50).tolist()}
]

# Process using the convenience function (uses default or provided config)
all_advanced_features = process_with_advanced_techniques(data_items)
print(json.dumps(all_advanced_features, indent=2))
```

### `integrate_with_pipeline` Function Usage:
```python
from recursive_training.data.advanced_feature_processor import integrate_with_pipeline
import json

# For a self-contained example, let's mock advanced_features_output
advanced_features_output = {
    "time_frequency": {
        "item_0": {"spectral_entropy": 0.5, "regime_shifts": [10, 20]},
        "item_1": {"spectral_entropy": 0.6}
    },
    "graph_features": {
        "degree_centrality": {"series_A": 5, "series_B": 3},
        "node_communities": {"series_A": 0, "series_B": 0},
        "density": 0.4
    },
    "self_supervised": {
        "representations": {
            "series_A": {"latent_vector": [0.1, 0.2], "reconstruction_error": 0.01},
            "series_B": {"latent_vector": [0.3, 0.4]}
        }
    },
    "metadata": {} # Simplified for example
}

# Dummy original features from a hypothetical standard pipeline
original_pipeline_features = {
    "items": [
        {"name": "series_A", "original_value": 150, "metadata": {}},
        {"name": "series_B", "original_value": 250, "metadata": {}}
    ],
    "global_info": "some_info"
}

# Integrate
integrated_data = integrate_with_pipeline(original_pipeline_features, advanced_features_output)
print(json.dumps(integrated_data, indent=2))
```

## 6. Hardcoding Issues

- **Default Cache Directory:** The default path for caching is hardcoded to `"cache/advanced_features"` ([`AdvancedFeatureProcessor.__init__`](recursive_training/data/advanced_feature_processor.py:53)). While configurable via the `config` dictionary, this default string is embedded.
- **Cache Filenames:** The names of the cache files are hardcoded:
    - `"time_frequency_features.json"` ([`_apply_time_frequency`](recursive_training/data/advanced_feature_processor.py:135))
    - `"graph_features.json"` ([`_apply_graph_features`](recursive_training/data/advanced_feature_processor.py:169))
    - `"self_supervised_features.json"` ([`_apply_self_supervised`](recursive_training/data/advanced_feature_processor.py:204))
- **Feature Keys for Integration:** The [`integrate_with_pipeline`](recursive_training/data/advanced_feature_processor.py:247) function uses numerous hardcoded string keys to access and assign features. Examples include:
    - Time-frequency: `"spectral_entropy"`, `"regime_shifts"`, `"dominant_frequencies"` (lines 287-296).
    - Graph features: `"degree_centrality"`, `"node_communities"`, `"community"`, `"density"`, `"average_clustering"`, `"modularity"`, `"community_count"` (lines 307-328).
    - Self-supervised: `"latent_representation"`, `"reconstruction_error"` (lines 334-345).
    This creates a tight coupling with the expected output structure of the specialized processing modules.
- **Item Key Parsing:** The logic to parse item keys in [`integrate_with_pipeline`](recursive_training/data/advanced_feature_processor.py:278) (`item_key.split("_")[1]`) assumes a specific format like `"item_X"`. If the key format changes, this logic will break.
- **Metadata Keys:** Keys like `"metadata"`, `"timestamp"`, `"num_items_processed"`, `"techniques_applied"`, `"advanced_processing"`, `"techniques"` are hardcoded when adding metadata (lines 111-119, 348-354).

## 7. Coupling Points

- **External Processing Modules:** The module is tightly coupled to the function signatures and, more importantly, the *output data structures* of the imported processing functions:
    - [`apply_time_frequency_decomposition`](recursive_training/data/time_frequency_decomposition.py:)
    - [`apply_graph_based_features`](recursive_training/data/graph_based_features.py:)
    - [`apply_self_supervised_learning`](recursive_training/data/self_supervised_learning.py:)
    Changes in these external modules, especially their return formats, would necessitate changes in this processor, particularly in [`integrate_with_pipeline`](recursive_training/data/advanced_feature_processor.py:247).
- **Input Data Structure:** The module expects `data_items` to be a list of dictionaries and `original_features` to be a dictionary with an "items" list, where items are dictionaries that may contain "name" or "id" keys for matching.
- **Configuration Contract:** The configuration dictionary (`config`) establishes an implicit contract. Keys like `"enable_time_frequency"`, `"time_frequency"`, `"cache_dir"`, etc., are expected by the processor.
- **Integration Logic:** The [`integrate_with_pipeline`](recursive_training/data/advanced_feature_processor.py:247) function is a significant coupling point, as it makes strong assumptions about where to find specific features within the `advanced_features` dictionary and how to merge them into the `original_features` structure.

## 8. Existing Tests

A test file [`tests/recursive_training/test_advanced_feature_processor.py`](tests/recursive_training/test_advanced_feature_processor.py) exists in the project structure. This suggests that unit tests are in place for this module. Without examining the test file's content, the exact coverage, nature of tests (e.g., unit, integration), and any potential gaps cannot be determined. However, its presence is a positive indicator for maintainability and reliability.

## 9. Module Architecture and Flow

The module's architecture revolves around the [`AdvancedFeatureProcessor`](recursive_training/data/advanced_feature_processor.py:21) class, which acts as an orchestrator.

**Key Components:**
- **`AdvancedFeatureProcessor` Class:**
    - **`__init__(config)`:** Initializes the processor, sets up configuration flags (enabling/disabling features like time-frequency, graph, self-supervised), configures caching, and stores technique-specific configurations.
    - **`process(data_items)`:** The main public method. It takes a list of data items and, based on the configuration, calls internal private methods to apply the enabled advanced processing techniques. It aggregates results and adds metadata.
    - **`_apply_time_frequency(data_items)`:** Internal method to apply time-frequency decomposition. Handles caching (load if exists, save if computed). Calls the external [`apply_time_frequency_decomposition`](recursive_training/data/time_frequency_decomposition.py:) function.
    - **`_apply_graph_features(data_items)`:** Internal method for graph-based features. Handles caching. Calls [`apply_graph_based_features`](recursive_training/data/graph_based_features.py:).
    - **`_apply_self_supervised(data_items)`:** Internal method for self-supervised learning. Handles caching. Calls [`apply_self_supervised_learning`](recursive_training/data/self_supervised_learning.py:).
- **`process_with_advanced_techniques(data_items, config)` Function:** A standalone utility function that instantiates `AdvancedFeatureProcessor` and calls its `process` method. Serves as a simplified entry point.
- **`integrate_with_pipeline(original_features, advanced_features, config)` Function:** Takes the output from this module (`advanced_features`) and merges it with features from a pre-existing pipeline (`original_features`). This function contains specific logic for how different types of advanced features (time-frequency, graph, self-supervised) are added or combined with the original data items.

**Primary Data/Control Flows:**
1.  **Feature Generation Flow:**
    `data_items` -> [`AdvancedFeatureProcessor.process()`](recursive_training/data/advanced_feature_processor.py:64) (or [`process_with_advanced_techniques()`](recursive_training/data/advanced_feature_processor.py:227))
    -> Conditional calls to `_apply_...` methods based on `enable_...` flags
    -> Each `_apply_...` method checks cache, then calls respective external `apply_...` function
    -> Results from `apply_...` functions are cached and returned
    -> `process()` aggregates results and adds metadata -> `advanced_features_output` (dictionary).
2.  **Feature Integration Flow:**
    `original_features`, `advanced_features_output` -> [`integrate_with_pipeline()`](recursive_training/data/advanced_feature_processor.py:247)
    -> Iterates through `advanced_features_output` (e.g., "time_frequency", "graph_features")
    -> Extracts specific sub-features based on hardcoded keys
    -> Modifies a copy of `original_features` by adding these new features to corresponding items or global sections
    -> Adds integration metadata -> `integrated_features` (dictionary).

## 10. Naming Conventions

- **Class Names:** `AdvancedFeatureProcessor` follows `PascalCase`, which is standard (PEP 8).
- **Function and Method Names:** `process_with_advanced_techniques`, `integrate_with_pipeline`, `_apply_time_frequency` use `snake_case`, adhering to PEP 8. Private methods are correctly prefixed with a single underscore.
- **Variable Names:** `data_items`, `config`, `enable_time_frequency`, `time_frequency_config`, `cache_dir`, `integrated_features` are descriptive and use `snake_case`.
- **Constants/Configuration Keys (Strings):** Strings like `"enable_time_frequency"`, `"spectral_entropy"`, `"cache/advanced_features"` are used. While not strictly constants in the `UPPER_SNAKE_CASE` sense, their usage as keys is clear.
- **Overall Consistency:** The naming conventions appear consistent throughout the module and align well with Python community standards (PEP 8). No obvious deviations or potential AI assumption errors in naming were noted from the module's code itself.