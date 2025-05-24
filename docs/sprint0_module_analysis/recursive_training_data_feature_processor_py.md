# Module Analysis: `recursive_training.data.feature_processor`

## 1. Module Intent/Purpose

The primary role of the [`recursive_training/data/feature_processor.py`](recursive_training/data/feature_processor.py:) module is to extract, process, and transform features from raw data for use in a recursive training system. It handles various data manipulation tasks including:

*   Data transformation
*   Normalization of numeric features
*   Vectorization of text features
*   Encoding of categorical features
*   Basic and rule-based feature engineering
*   Advanced feature extraction (time-frequency, graph-based, self-supervised learning)
*   Caching of processed features to optimize performance
*   Preparation of data into a format suitable for model training (feature matrix `X` and target vector `y`)

The module is designed to be configurable and to work in conjunction with other components of the recursive training system, such as data ingestion and data storage modules.

## 2. Operational Status/Completeness

*   **Core Functionality:** The module appears largely complete for its core responsibilities of basic feature extraction (numeric, text, categorical) and transformation, rule-based feature extraction (dictionary-based), and caching. Classes like [`NumericNormalizer`](recursive_training/data/feature_processor.py:84), [`TextVectorizer`](recursive_training/data/feature_processor.py:227), [`CategoryEncoder`](recursive_training/data/feature_processor.py:408), and [`FeatureCache`](recursive_training/data/feature_processor.py:503) are well-defined.
*   **Advanced Features:** Methods for advanced feature extraction such as [`_apply_time_frequency_decomposition()`](recursive_training/data/feature_processor.py:692), [`_extract_graph_based_features()`](recursive_training/data/feature_processor.py:754), and [`_learn_self_supervised_representation()`](recursive_training/data/feature_processor.py:889) are implemented. However, their robustness may depend on the specific structure of input data and the availability/configuration of their respective libraries (SciPy, NetworkX, TensorFlow).
*   **Placeholders/TODOs:**
    *   The method [`_extract_object_rule_features()`](recursive_training/data/feature_processor.py:1118) is explicitly a placeholder, with a comment stating: "This is a placeholder for object-based rule feature extraction // It will be implemented as part of the hybrid rules approach."
*   **Testing Considerations:** The presence of `_mock_test_mode` in [`NumericNormalizer`](recursive_training/data/feature_processor.py:101) suggests that testing, particularly with `numpy`, might have required specific workarounds.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Object-Based Rule Features:** The [`_extract_object_rule_features()`](recursive_training/data/feature_processor.py:1118) method needs to be implemented as planned.
*   **Advanced Feature Robustness:** The advanced feature extraction methods make assumptions about input data structures (e.g., `item.get("time_series", [])` at [`recursive_training/data/feature_processor.py:720`](recursive_training/data/feature_processor.py:720)). These might require more generalized handling or clearer contracts for input data. Error handling within these methods often defaults to returning empty results, which could be improved.
*   **Feature Selection Sophistication:** The current [`_select_features()`](recursive_training/data/feature_processor.py:1161) method is basic (based on non-empty features). More advanced feature selection techniques (e.g., filter methods, wrapper methods, embedded methods) could be integrated.
*   **Configuration of Advanced Features:** While configurable, parameters for advanced methods (e.g., STFT window, graph thresholds, autoencoder architecture) might benefit from more dynamic or automated tuning mechanisms.
*   **Extensibility of Transformers:** While the base [`FeatureTransformer`](recursive_training/data/feature_processor.py:31) class exists, adding new custom transformers might require more streamlined registration or discovery within the main [`RecursiveFeatureProcessor`](recursive_training/data/feature_processor.py:568).

## 4. Connections & Dependencies

*   **Project-Internal Dependencies:**
    *   The module is "Designed to work with RecursiveDataIngestionManager and RecursiveDataStore" ([`recursive_training/data/feature_processor.py:581`](recursive_training/data/feature_processor.py:581)), implying it consumes data from an ingestion manager and its output might be used by a data store or a model training module within the `recursive_training` package.
*   **External Library Dependencies:**
    *   **Core:** `json`, `logging`, `hashlib`, `collections.Counter`.
    *   **Conditional (Core Processing):**
        *   `numpy` (for [`NumericNormalizer`](recursive_training/data/feature_processor.py:84), [`TextVectorizer`](recursive_training/data/feature_processor.py:227), data preparation).
        *   `pandas` (for [`to_pandas_dataframe()`](recursive_training/data/feature_processor.py:1354) and parts of graph feature extraction).
    *   **Conditional (Advanced Features):**
        *   `scipy` (specifically `scipy.signal.stft` for [`_apply_time_frequency_decomposition()`](recursive_training/data/feature_processor.py:692)).
        *   `networkx` (for [`_extract_graph_based_features()`](recursive_training/data/feature_processor.py:754)).
        *   `tensorflow` (for [`_learn_self_supervised_representation()`](recursive_training/data/feature_processor.py:889)).
    *   The availability of `numpy` and `pandas` is checked using `NUMPY_AVAILABLE` ([`recursive_training/data/feature_processor.py:20`](recursive_training/data/feature_processor.py:20)) and `PANDAS_AVAILABLE` ([`recursive_training/data/feature_processor.py:26`](recursive_training/data/feature_processor.py:26)) flags.
*   **Data Interaction:**
    *   **Input:** Consumes a list of dictionaries (`data_items`) representing raw data, and a configuration dictionary.
    *   **Output:** Produces a dictionary of transformed features, and ultimately a feature matrix (`X`) and target vector (`y`) for model training.
    *   **Logs:** Uses the `logging` module for operational messages.
    *   No direct file I/O for data processing itself, but relies on a `config` object that might be loaded from a file elsewhere.

## 5. Function and Class Example Usages

*   **[`FeatureTransformer`](recursive_training/data/feature_processor.py:31):**
    ```python
    # Base class, typically subclassed
    # transformer.fit(data)
    # transformed_data = transformer.transform(data)
    # or
    # transformed_data = transformer.fit_transform(data)
    ```

*   **[`NumericNormalizer`](recursive_training/data/feature_processor.py:84):**
    ```python
    normalizer = NumericNormalizer(config={"normalize_method": "zscore"})
    data = {"feature1": [10, 20, 30, 40, 50]}
    normalized_data = normalizer.fit_transform(data)
    # normalized_data -> {'feature1': [-1.414..., -0.707..., 0.0, 0.707..., 1.414...]}
    ```

*   **[`TextVectorizer`](recursive_training/data/feature_processor.py:227):**
    ```python
    vectorizer = TextVectorizer(config={"vectorize_method": "tfidf", "max_features": 5})
    data = {"description": ["sample text here", "another example text"]}
    vectorized_data = vectorizer.fit_transform(data)
    # vectorized_data -> {'description': [[vec1], [vec2]]} (vectors of floats)
    ```

*   **[`CategoryEncoder`](recursive_training/data/feature_processor.py:408):**
    ```python
    encoder = CategoryEncoder(config={"encode_method": "onehot"})
    data = {"category": ["A", "B", "A", "C"]}
    encoded_data = encoder.fit_transform(data)
    # encoded_data -> {'category': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], ...]} (for one-hot)
    ```

*   **[`RecursiveFeatureProcessor`](recursive_training/data/feature_processor.py:568):**
    ```python
    config = {
        "normalize_method": "minmax",
        "advanced_features": {"time_frequency_decomposition": False}
    }
    processor = RecursiveFeatureProcessor(config=config)
    data_items = [
        {"id": 1, "value": 10, "text_col": "some words", "cat_col": "X"},
        {"id": 2, "value": 20, "text_col": "more words here", "cat_col": "Y"}
    ]
    processor.fit(data_items)
    transformed_features = processor.transform(data_items)
    # Example: Access numeric features
    # numeric_transformed = transformed_features.get("numeric", {})

    # Prepare for training (assuming 'numeric:value' is the target)
    # X_train, y_train = processor.prepare_training_data(transformed_features, "numeric:value")
    ```

*   **[`get_feature_processor()`](recursive_training/data/feature_processor.py:1427):**
    ```python
    # Obtains a singleton instance of RecursiveFeatureProcessor
    fp_instance = get_feature_processor(config={"feature_cache_size": 2000})
    ```

## 6. Hardcoding Issues

*   **Default Configuration Values:** Many parameters within transformers and the main processor have hardcoded default values if not specified in the configuration. Examples:
    *   `NumericNormalizer(config).normalize_method`: "minmax" ([`recursive_training/data/feature_processor.py:99`](recursive_training/data/feature_processor.py:99))
    *   `TextVectorizer(config).vectorize_method`: "tfidf" ([`recursive_training/data/feature_processor.py:240`](recursive_training/data/feature_processor.py:240))
    *   `TextVectorizer(config).max_features`: 1000 ([`recursive_training/data/feature_processor.py:241`](recursive_training/data/feature_processor.py:241))
    *   `CategoryEncoder(config).encode_method`: "onehot" ([`recursive_training/data/feature_processor.py:420`](recursive_training/data/feature_processor.py:420))
    *   `CategoryEncoder(config).unknown_value`: -1 ([`recursive_training/data/feature_processor.py:421`](recursive_training/data/feature_processor.py:421))
    *   `RecursiveFeatureProcessor(config).feature_cache_size`: 1000 ([`recursive_training/data/feature_processor.py:600`](recursive_training/data/feature_processor.py:600))
    *   `RecursiveFeatureProcessor(config).feature_extraction_methods`: `["basic", "dict_rules", "object_rules"]` ([`recursive_training/data/feature_processor.py:611-614`](recursive_training/data/feature_processor.py:611-614))
    *   Advanced feature parameters (e.g., `graph_correlation_threshold` at [`recursive_training/data/feature_processor.py:827`](recursive_training/data/feature_processor.py:827), autoencoder defaults at [`recursive_training/data/feature_processor.py:958-978`](recursive_training/data/feature_processor.py:958-978)).
*   **Cache Key Hashing Algorithm:** Uses `hashlib.md5` ([`recursive_training/data/feature_processor.py:637`](recursive_training/data/feature_processor.py:637)).
*   **Feature Names in Rule Extraction:** Specific keys like `"condition_count"`, `"action_count"` are used in [`_extract_dict_rule_features()`](recursive_training/data/feature_processor.py:1052).
*   **Mock Values for Testing:** [`NumericNormalizer`](recursive_training/data/feature_processor.py:84) contains hardcoded mock values ([`recursive_training/data/feature_processor.py:133-136`](recursive_training/data/feature_processor.py:133-136)) when `_mock_test_mode` is active.
*   **STFT Parameters:** Default segment lengths for STFT in [`_apply_time_frequency_decomposition()`](recursive_training/data/feature_processor.py:732-733).
*   **Padding Value:** `0.0` is used for padding in [`prepare_training_data()`](recursive_training/data/feature_processor.py:1350).
*   **Logger Name:** `"RecursiveFeatureProcessor"` ([`recursive_training/data/feature_processor.py:591`](recursive_training/data/feature_processor.py:591)).

## 7. Coupling Points

*   **Configuration Object:** The module is heavily dependent on the structure and keys within the `config` dictionary. Changes to expected configuration keys would impact behavior.
*   **Input Data Structure:** Methods like [`extract_features()`](recursive_training/data/feature_processor.py:640) and its sub-methods (e.g., [`_extract_basic_features()`](recursive_training/data/feature_processor.py:1011), [`_extract_dict_rule_features()`](recursive_training/data/feature_processor.py:1052)) make assumptions about the format of `data_items` (e.g., presence of `"rule_definition"` key). Advanced features also assume specific keys like `"time_series"`.
*   **External Libraries:** The module's functionality, especially advanced features, is coupled with `numpy`, `pandas`, `scipy`, `networkx`, and `tensorflow`. API changes or absence of these libraries can lead to errors or reduced functionality.
*   **Singleton Pattern:** The [`get_feature_processor()`](recursive_training/data/feature_processor.py:1427) function creates a global singleton instance. While it allows config updates, shared global state can complicate testing and lead to unexpected interactions if different parts of an application attempt to reconfigure it.
*   **Feature Naming Convention:** The `prepare_training_data()` method relies on features being named `"{feature_type}:{feature_name}"` ([`recursive_training/data/feature_processor.py:1299`](recursive_training/data/feature_processor.py:1299)).

## 8. Existing Tests

*   The file system indicates the presence of test files:
    *   `tests/recursive_training/test_feature_processor.py`
    *   `tests/recursive_training/test_feature_processor_integration.py`
*   This suggests that both unit tests and integration tests exist for this module.
*   The code contains specific provisions for testing:
    *   `_mock_test_mode` in [`NumericNormalizer`](recursive_training/data/feature_processor.py:101) to bypass actual `numpy` computations and use predictable mock values.
    *   [`FeatureCache`](recursive_training/data/feature_processor.py:503) uses insertion order for eviction during testing to ensure predictability ([`recursive_training/data/feature_processor.py:543-544`](recursive_training/data/feature_processor.py:543-544)).
*   The extent of test coverage, particularly for the advanced feature extraction methods and various configurations, cannot be determined without inspecting the test files themselves. The placeholder method [`_extract_object_rule_features()`](recursive_training/data/feature_processor.py:1118) would likely lack meaningful tests.

## 9. Module Architecture and Flow

The module is architected around a central [`RecursiveFeatureProcessor`](recursive_training/data/feature_processor.py:568) class that orchestrates several specialized transformer classes and a caching mechanism.

*   **Transformer Classes:**
    *   [`FeatureTransformer`](recursive_training/data/feature_processor.py:31): Abstract base class defining the `fit`/`transform` interface.
    *   [`NumericNormalizer`](recursive_training/data/feature_processor.py:84): Handles normalization of numerical data (min-max, z-score).
    *   [`TextVectorizer`](recursive_training/data/feature_processor.py:227): Converts text data into numerical vectors (TF-IDF, count, binary).
    *   [`CategoryEncoder`](recursive_training/data/feature_processor.py:408): Encodes categorical data (ordinal, one-hot).
*   **Caching:**
    *   [`FeatureCache`](recursive_training/data/feature_processor.py:503): Stores results of feature extraction and transformation to avoid redundant computations, using MD5 hashing of input data for cache keys.
*   **Main Processor (`RecursiveFeatureProcessor`):**
    1.  **Initialization:** Sets up transformers, cache, and configuration.
    2.  **Feature Extraction (`extract_features()`):**
        *   Processes input `data_items`.
        *   Categorizes data into numeric, text, and categorical types via [`_extract_basic_features()`](recursive_training/data/feature_processor.py:1011).
        *   Extracts features from dictionary-based rules via [`_extract_dict_rule_features()`](recursive_training/data/feature_processor.py:1052).
        *   (Placeholder for object-based rules: [`_extract_object_rule_features()`](recursive_training/data/feature_processor.py:1118)).
        *   Optionally applies advanced feature extraction: [`_apply_time_frequency_decomposition()`](recursive_training/data/feature_processor.py:692), [`_extract_graph_based_features()`](recursive_training/data/feature_processor.py:754), [`_learn_self_supervised_representation()`](recursive_training/data/feature_processor.py:889).
        *   Results are cached.
    3.  **Fitting (`fit()`):**
        *   Calls `extract_features()`.
        *   Fits each transformer (normalizer, vectorizer, encoder) on the relevant extracted features.
        *   Performs basic feature selection via [`_select_features()`](recursive_training/data/feature_processor.py:1161).
    4.  **Transformation (`transform()`):**
        *   Calls `extract_features()`.
        *   Uses the fitted transformers to process the features.
        *   Results are cached.
    5.  **Data Preparation (`prepare_training_data()`):**
        *   Takes transformed features and a target feature name.
        *   Flattens selected features into a numerical matrix `X` and extracts the target vector `y`.
*   **Singleton Access:**
    *   [`get_feature_processor()`](recursive_training/data/feature_processor.py:1427): Provides a global singleton instance, allowing shared access and configuration.

**Data Flow Summary:**
`List[Dict]` (raw data) -> `extract_features()` -> `Dict` (categorized & rule features) -> `fit()` (fits transformers) / `transform()` (applies transformers) -> `Dict` (transformed features) -> `prepare_training_data()` -> `Tuple[List[List[float]], List[float]]` (X, y for ML).

## 10. Naming Conventions

*   **Overall:** The module generally adheres to PEP 8 naming conventions (PascalCase for classes, snake_case for functions, methods, and variables).
*   **Clarity:** Class and method names are descriptive and clearly indicate their purpose (e.g., [`RecursiveFeatureProcessor`](recursive_training/data/feature_processor.py:568), [`NumericNormalizer`](recursive_training/data/feature_processor.py:84), [`extract_features`](recursive_training/data/feature_processor.py:640), [`prepare_training_data`](recursive_training/data/feature_processor.py:1254)).
*   **Internal/Private Methods:** Prefixed with a single underscore (e.g., [`_extract_basic_features()`](recursive_training/data/feature_processor.py:1011), [`_generate_cache_key()`](recursive_training/data/feature_processor.py:619)).
*   **Constants/Flags:** Uppercase for availability flags like `NUMPY_AVAILABLE` ([`recursive_training/data/feature_processor.py:20`](recursive_training/data/feature_processor.py:20)).
*   **Test-Specific Naming:** `_mock_test_mode` ([`recursive_training/data/feature_processor.py:101`](recursive_training/data/feature_processor.py:101)) is specific but its intent is clear from the name.
*   **Generated Feature Names:** Feature names are systematically generated (e.g., `f"{feature_type}:{feature_name}"`, `f"ssl_encoded_dim_{i}"`).
*   No significant deviations from standard Python naming practices or potential AI assumption errors were noted. The naming is consistent and contributes to the readability of the code.