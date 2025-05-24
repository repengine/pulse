# Module Analysis: `core/feature_store.py`

## 1. Module Intent/Purpose

The [`core/feature_store.py`](core/feature_store.py:1) module implements a centralized `FeatureStore` for the Pulse project. Its primary purpose is to manage both raw data sources and engineered feature transformation pipelines. It allows for the registration of data loading functions and feature transformation functions, and provides a unified interface to retrieve these features, incorporating a caching mechanism for efficiency. The module aims to decouple feature generation and access from the components that consume these features.

## 2. Operational Status/Completeness

The module appears to be operational and provides a good baseline for feature management. Key functionalities include:
*   Dynamic registration of raw data loaders and transformation functions based on configurations in [`core.pulse_config.FEATURE_PIPELINES`](core/pulse_config.py:8).
*   Manual registration of new raw loaders via [`register_raw()`](core/feature_store.py:28).
*   Manual registration of new transforms via [`register_transform()`](core/feature_store.py:32).
*   Retrieval of features by name using [`get()`](core/feature_store.py:36), which handles computation (loading or transforming) if the feature is not in the cache.
*   Caching of computed features to avoid redundant computations.
*   Listing all available features via [`list_features()`](core/feature_store.py:58).
*   Clearing the cache via [`clear_cache()`](core/feature_store.py:62).
*   Removing registered features via [`remove_feature()`](core/feature_store.py:68).

A global instance, [`feature_store`](core/feature_store.py:77), is provided for easy access.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Error Handling:** The error handling within the [`get()`](core/feature_store.py:36) method could be more comprehensive. For instance, if a registered loader or transform function fails during execution (e.g., due to I/O errors, data inconsistencies, or bugs in the transform logic), the current implementation might raise an unhandled exception. Specific error trapping and potentially custom exceptions could improve robustness.
*   **Transform Dependency Granularity:** When a transform is computed ([`get()`](core/feature_store.py:47-52)), it concatenates *all* registered raw data sources. This could be inefficient if a transform only depends on a small subset of the raw data. A mechanism to declare specific raw data dependencies for each transform could optimize performance and reduce unnecessary data loading/processing.
*   **Feature Versioning/Staleness:** There's no explicit mechanism for feature versioning or handling stale cache entries if the underlying data or transformation logic changes. This could lead to inconsistencies if not managed externally.
*   **Complex Feature Dependencies:** The current model supports transforms on a collection of raw features. It doesn't explicitly support multi-stage transforms (i.e., features derived from other derived features) without re-registering intermediate results as "raw" features.
*   **Asynchronous Operations:** For I/O-bound raw data loaders, asynchronous operations could improve performance, especially if multiple features are fetched concurrently.
*   **Configuration Validation:** While it loads from `FEATURE_PIPELINES`, there's no explicit validation of this configuration structure at startup.

## 4. Connections & Dependencies

### Internal Pulse Modules:
*   [`core.pulse_config`](core/pulse_config.py): Specifically, it reads the `FEATURE_PIPELINES` dictionary to auto-register feature pipelines during initialization ([`__init__()`](core/feature_store.py:19)).

### External Libraries:
*   `typing` (Callable, Dict, List): Used for type hinting.
*   `pandas`: Extensively used for data manipulation, with features typically being `pd.DataFrame` or `pd.Series`.
*   `importlib`: Used for dynamically importing modules and functions specified as strings in the `FEATURE_PIPELINES` configuration ([`__init__()`](core/feature_store.py:21), [`__init__()`](core/feature_store.py:25)).

## 5. Function and Class Example Usages

```python
from core.feature_store import feature_store
import pandas as pd

# --- Assuming FEATURE_PIPELINES in core.pulse_config.py is set up ---
# Example:
# FEATURE_PIPELINES = {
#     "raw_price": {
#         "raw_loader": "my_data_loaders.load_price_data", # my_data_loaders.py needs load_price_data()
#     },
#     "price_sma_10": {
#         "raw_loader": "my_data_loaders.load_price_data", # Assumes transform needs the same raw data
#         "transform": "my_transforms.calculate_sma_10" # my_transforms.py needs calculate_sma_10(df)
#     }
# }

# --- Retrieving a pre-registered feature (auto-loaded from config) ---
# try:
#     price_series = feature_store.get("raw_price")
#     sma_feature = feature_store.get("price_sma_10")
#     print("SMA Feature:\n", sma_feature.head())
# except KeyError as e:
#     print(e)

# --- Manually registering a new raw data loader ---
# def custom_volume_loader() -> pd.DataFrame:
#     # In a real scenario, this would load data from a file, DB, API, etc.
#     return pd.DataFrame({'volume': [100, 150, 120, 180, 200]},
#                         index=pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']))

# feature_store.register_raw("custom_volume", custom_volume_loader)
# volume_data = feature_store.get("custom_volume") # Retrieves the 'volume' series
# print("\nCustom Volume Data:\n", volume_data.head())


# --- Manually registering a new transformation function ---
# def volume_change_transform(df: pd.DataFrame) -> pd.Series:
#     # Expects 'custom_volume' to be available via a raw loader that returns a DataFrame
#     # where one of the columns is named 'custom_volume' or it's the first column.
#     # For this example, let's assume 'custom_volume' is loaded and available.
#     if "custom_volume" in df.columns:
#         return df["custom_volume"].pct_change().rename("volume_change")
#     # Fallback if the raw loader for 'custom_volume' returned a Series directly
#     # or a DataFrame where 'custom_volume' was the first column and got picked.
#     # This part is a bit tricky due to how get() handles raw features.
#     # A more robust transform would ensure its input needs are met.
#     elif isinstance(df, pd.Series) and df.name == "custom_volume":
#          return df.pct_change().rename("volume_change")
#     # A more robust way: ensure the transform knows what raw features it needs
#     # and accesses them explicitly from the input DataFrame 'df' which is a concat of all raw features.
#     # For example, if custom_volume_loader was registered as 'vol_data_source':
#     # return df[('vol_data_source', 'volume')].pct_change().rename("volume_change")
#     # The current implementation of get() for transforms concatenates all raw_loaders
#     # with keys, so df.columns would be a MultiIndex.
#     # Example: if 'raw_price' and 'custom_volume' are registered raw loaders
#     # df.columns might be [('raw_price', 'price_col_name'), ('custom_volume', 'volume')]
#     # So the transform should expect this structure.
#     # Let's assume 'custom_volume' loader returns a DataFrame with a 'volume' column
#     # and was registered with the key 'custom_volume_source_key'.
#     if ('custom_volume_source_key', 'volume') in df.columns: # Adjust key based on actual registration
#         return df[('custom_volume_source_key', 'volume')].pct_change().rename("volume_change")
#     raise ValueError("Required 'custom_volume' data not found in expected format for transform.")


# feature_store.register_transform("volume_percentage_change", volume_change_transform)
# try:
#     volume_change = feature_store.get("volume_percentage_change")
#     print("\nVolume Percentage Change:\n", volume_change.head())
# except (KeyError, ValueError) as e:
#     print(f"Error getting transformed feature: {e}")


# --- Listing all features ---
# print("\nAvailable features:", feature_store.list_features())

# --- Clearing the cache ---
# feature_store.clear_cache()
# print("\nCache cleared.")

# --- Removing a feature ---
# feature_store.remove_feature("custom_volume")
# print("\n'custom_volume' feature removed.")
# print("Available features after removal:", feature_store.list_features())

```

## 6. Hardcoding Issues

*   **Configuration Path:** The module relies on `FEATURE_PIPELINES` being defined in [`core.pulse_config`](core/pulse_config.py:8). While this centralizes configuration, the path itself is hardcoded.
*   **Raw Feature Column Selection:** In [`get()`](core/feature_store.py:45), when a raw loader returns a `pd.DataFrame`, it tries to select a series by `df[name]` (where `name` is the registration key) or falls back to `df.iloc[:, 0]`. This assumption might not always hold if the desired series has a different name or is not the first column, and the registration key doesn't match a column name. This could lead to unexpected behavior or errors.
*   **Transform Input Structure:** Transforms receive a DataFrame ([`get()`](core/feature_store.py:48-52)) that is a concatenation of *all* registered raw features. The column names in this concatenated DataFrame will be a `MultiIndex` if the raw loaders return DataFrames (e.g., `(loader_key, original_column_name)`). Transform functions must be written with awareness of this structure, which isn't explicitly documented in the `FeatureStore` itself.

## 7. Coupling Points

*   **[`core.pulse_config`](core/pulse_config.py):** Tightly coupled to the existence and structure of the `FEATURE_PIPELINES` dictionary in this configuration module. Changes to the config structure could break the feature store's initialization.
*   **`pandas` API:** Heavily reliant on `pandas` DataFrames and Series. Changes in the `pandas` API could impact the module.
*   **Dynamic Import Paths:** The string paths for loader and transform functions in `FEATURE_PIPELINES` create a coupling. If these modules or functions are renamed or moved, the configuration must be updated, otherwise, `importlib` will fail.

## 8. Existing Tests

The provided file [`core/feature_store.py`](core/feature_store.py:1) does not contain unit tests. Comprehensive tests would be needed to cover:
*   Successful registration and retrieval of raw features.
*   Successful registration and retrieval of transformed features.
*   Correct operation of the caching mechanism (cache hits, cache misses).
*   Cache clearing functionality.
*   Feature removal functionality.
*   Handling of `KeyError` for non-existent features.
*   Correct dynamic loading of modules/functions from configuration.
*   Behavior with empty `FEATURE_PIPELINES`.
*   Edge cases for raw feature column selection (e.g., multi-column DataFrames from raw loaders).
*   Correct concatenation of raw data for transforms and ensuring transforms can access the data.

## 9. Module Architecture and Flow

The `FeatureStore` is implemented as a class, and a global instance ([`feature_store`](core/feature_store.py:77)) is created for easy access throughout the application.

**Initialization ([`__init__()`](core/feature_store.py:14)):**
1.  Initializes internal dictionaries: `_raw_loaders`, `_transforms`, and `_cache`.
2.  Iterates through `FEATURE_PIPELINES` from [`core.pulse_config`](core/pulse_config.py:8).
3.  For each feature specification:
    *   Dynamically imports the raw loader function using `importlib`.
    *   Registers the raw loader using [`register_raw()`](core/feature_store.py:28).
    *   If a transform is specified, dynamically imports the transform function.
    *   Registers the transform function using [`register_transform()`](core/feature_store.py:32).

**Feature Retrieval ([`get(name)`](core/feature_store.py:36)):**
1.  Checks if the feature `name` is in the `_cache`. If yes, returns the cached `pd.Series`.
2.  If not cached:
    *   Determines if `name` corresponds to a registered raw loader ([`_raw_loaders`](core/feature_store.py:15)).
        *   If yes, calls the loader function to get a `pd.DataFrame`.
        *   Extracts a `pd.Series` from the DataFrame (either by `name` as column or the first column).
    *   Else, determines if `name` corresponds to a registered transform ([`_transforms`](core/feature_store.py:16)).
        *   If yes, it first prepares the input DataFrame for the transform by:
            *   Loading *all* raw DataFrames from `_raw_loaders`.
            *   Concatenating them column-wise using `pd.concat`, with keys from `_raw_loaders` potentially forming a `MultiIndex` on columns.
        *   Calls the transform function with this concatenated DataFrame. The transform is expected to return a `pd.Series`.
    *   If `name` is not found in either `_raw_loaders` or `_transforms`, raises a `KeyError`.
3.  Stores the computed `pd.Series` in the `_cache`.
4.  Returns the `pd.Series`.

Other methods like [`list_features()`](core/feature_store.py:58), [`clear_cache()`](core/feature_store.py:62), and [`remove_feature()`](core/feature_store.py:68) provide straightforward management utilities.

## 10. Naming Conventions

*   Class name `FeatureStore` is clear and follows PascalCase.
*   Method names like [`register_raw()`](core/feature_store.py:28), [`get()`](core/feature_store.py:36), [`clear_cache()`](core/feature_store.py:62) are descriptive and use snake_case.
*   Internal attributes like `_raw_loaders`, `_transforms`, `_cache` use a leading underscore, indicating they are intended for internal use.
*   Variable names (e.g., `module_name`, `fn_name`, `spec`) are generally clear.
*   The global instance `feature_store` is lowercase snake_case.

The conventions are consistent with Python (PEP 8) guidelines.

## 11. Overall Assessment of Completeness and Quality

**Completeness:**
The module provides a solid foundation for feature management within Pulse. It covers the essential aspects of registering, retrieving, and caching features, with a flexible configuration-driven approach for initial setup. However, as noted in "Implementation Gaps," areas like advanced error handling, granular dependency management for transforms, and feature versioning could enhance its completeness for more complex scenarios.

**Quality:**
*   **Readability:** The code is generally well-written, with clear docstrings for the module, class, and public methods.
*   **Maintainability:** The use of dynamic imports and configuration-driven setup makes it relatively easy to add new features without modifying the `FeatureStore` code itself. The separation of concerns (loading, transforming, caching) is good.
*   **Type Hinting:** Good use of type hints improves code clarity and helps with static analysis.
*   **Efficiency:** Caching is a key feature for efficiency. The concatenation of all raw data for every transform ([`get()`](core/feature_store.py:48-51)) is a potential performance bottleneck if many raw features exist and transforms only need a few.
*   **Robustness:** Could be improved with more explicit error handling and validation, as mentioned. The assumption about raw feature column selection could also lead to subtle bugs.
*   **Testability:** The global instance `feature_store` can make unit testing slightly more challenging, as tests might need to manage its state (e.g., clearing features/cache between test cases). Dependency injection for the configuration source could improve this, but the current approach is common for such utility modules.

Overall, [`core/feature_store.py`](core/feature_store.py:1) is a good quality, functional module that serves its core purpose effectively. It's a valuable component for managing data pipelines in the `core/` directory.