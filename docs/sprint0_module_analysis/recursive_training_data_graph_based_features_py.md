# Module Analysis: `recursive_training.data.graph_based_features`

## 1. Module Intent/Purpose

The primary role of the [`graph_based_features.py`](recursive_training/data/graph_based_features.py:) module is to construct co-movement graphs from time series data and subsequently extract a variety of graph-based metrics. These extracted features are intended for use in retrodiction processes. The module encapsulates functionalities for:
*   Preprocessing and cleaning input time series data.
*   Calculating correlation matrices using configurable methods (Pearson, Spearman, Kendall, or a NumPy-based fallback).
*   Building graphs where nodes represent time series and edges represent significant co-movements (correlations) above a defined threshold.
*   Extracting diverse graph metrics, including centrality measures, clustering coefficients, community structures, and overall graph-level properties.

## 2. Operational Status/Completeness

The module appears to be largely complete and operationally sound for its defined scope.
*   It incorporates robust error handling, particularly for optional dependencies like `NetworkX` and `SciPy`. If these libraries are unavailable, the module gracefully degrades its functionality (e.g., limiting feature extraction or using alternative calculation methods).
*   Comprehensive data preprocessing steps are included, such as handling `NaN` values (through interpolation or mean filling) and ensuring consistent lengths across time series.
*   There are no explicit `TODO` comments or significant placeholders indicating unfinished core functionality.
*   Certain advanced metrics (e.g., rich club coefficient, PageRank, eigenvector centrality) are wrapped in `try-except` blocks, suggesting an awareness of potential calculation issues or edge cases, with fallbacks or warnings implemented.

## 3. Implementation Gaps / Unfinished Next Steps

While functional, several areas could be enhanced or extended:

*   **Sophisticated Rolling Window Logic:** The current implementation of rolling window correlation ([`_calculate_correlation_matrix`](recursive_training/data/graph_based_features.py:231)) averages correlations across windows ([`correlation_matrix = np.nanmean(window_correlations, axis=0)`](recursive_training/data/graph_based_features.py:257)). More advanced techniques for dynamic graph construction or temporal graph analysis could be explored.
*   **Dynamic Correlation Thresholding:** The correlation threshold for edge creation is static, loaded from configuration ([`self.threshold = self.config.get("correlation_threshold", 0.7)`](recursive_training/data/graph_based_features.py:54)). Implementing dynamic or adaptive thresholding methods could improve graph relevance under varying data conditions.
*   **Expanded Community Detection Algorithms:** The module primarily uses the greedy modularity maximization algorithm ([`nx.community.greedy_modularity_communities`](recursive_training/data/graph_based_features.py:478)). Support for other community detection algorithms (e.g., Louvain, Girvan-Newman), selectable via configuration, would increase flexibility.
*   **Explicit Use of Edge Weights:** Edge weights, representing correlation strength, are stored ([`G.add_edge(i, j, weight=corr)`](recursive_training/data/graph_based_features.py:346)). However, many NetworkX functions used might not inherently utilize these weights unless explicitly instructed. A review to ensure weighted versions of metrics are used where appropriate could enhance accuracy.
*   **Broader Range of Graph Metrics:** While the current selection is comprehensive, further graph metrics (e.g., motif analysis, advanced network resilience measures, information-theoretic measures) could be added based on specific retrodiction requirements.
*   **Input Data Flexibility in `apply_graph_based_features`:** The [`apply_graph_based_features`](recursive_training/data/graph_based_features.py:631) function uses heuristics to find time series data within a list of dictionaries (checking keys like `"time_series"`, `"values"`, `"data"`). A more standardized input format or explicit configuration for data extraction paths would make this function more robust.

## 4. Connections & Dependencies

### 4.1. Direct Project Module Imports
*   None. This module is designed as a self-contained feature extractor.

### 4.2. External Library Dependencies
*   **`logging`**: Standard Python library for logging messages.
*   **`numpy` (as `np`)**: Essential for numerical computations, array manipulations, `NaN` handling, and as a fallback for correlation calculations.
*   **`networkx` (as `nx`)**: Optional but critical for graph construction, manipulation, and the calculation of most graph metrics. Availability is checked at import ([`NETWORKX_AVAILABLE`](recursive_training/data/graph_based_features.py:16)).
*   **`scipy.stats`**: Optional, used for Pearson, Spearman, and Kendall correlation coefficient calculations. Availability is checked at import ([`SCIPY_AVAILABLE`](recursive_training/data/graph_based_features.py:23)).
*   **`datetime`**: Standard Python library used for timestamping the extracted features.

### 4.3. Interaction via Shared Data
*   **Input:**
    *   The [`GraphFeatureExtractor.extract_features`](recursive_training/data/graph_based_features.py:68) method expects a dictionary where keys are string identifiers for time series and values are lists of numerical data (`Dict[str, List[float]]`).
    *   The [`apply_graph_based_features`](recursive_training/data/graph_based_features.py:631) function expects a list of dictionaries (`List[Dict[str, Any]]`) and attempts to extract time series from them.
*   **Output:**
    *   Both primary functions return a dictionary containing the extracted graph-based features. This dictionary includes the correlation matrix, series names, and various calculated graph metrics.

### 4.4. Input/Output Files
*   The module does not directly perform file I/O for data persistence (e.g., reading datasets from files or saving results to files). It operates on in-memory data structures. Logging output may be directed to files depending on the logging configuration of the broader application.

## 5. Function and Class Example Usages

### 5.1. `GraphFeatureExtractor` Class

```python
from recursive_training.data.graph_based_features import GraphFeatureExtractor
import numpy as np
import logging

# Configure logging to see outputs
logging.basicConfig(level=logging.INFO)

# Sample time series data
ts_data = {
    "series_A": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "series_B": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11], # Highly correlated with A
    "series_C": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1], # Negatively correlated with A
    "series_D": list(np.random.rand(10) * 10),   # Random series
    "series_E": [None, 1, 2, np.nan, 5, 6, 7, 8, 9, 10] # Series with NaNs
}

config = {
    "correlation_method": "pearson",
    "correlation_threshold": 0.8,
    "absolute_threshold": True,
    "window_size": None,
    "include_negative": True,
    "graph_metrics": ["centrality", "clustering", "communities", "graph_level"]
}

extractor = GraphFeatureExtractor(config=config)
features = extractor.extract_features(ts_data)
# Example: Accessing a specific feature
# if "degree_centrality" in features:
#     print(features["degree_centrality"])
```

### 5.2. `apply_graph_based_features` Function

```python
from recursive_training.data.graph_based_features import apply_graph_based_features
import logging

# Configure logging to see outputs
logging.basicConfig(level=logging.INFO)

data_items_list = [
    {"id": "item1", "time_series": [1, 2, 3, 4, 5, 6, 7], "other_info": "abc"},
    {"id": "item2", "values": [7, 6, 5, 4, 3, 2, 1], "other_info": "def"},
    {"id": "item3", "data": [1, 3, 2, 4, 5, 3, 6], "other_info": "ghi"},
    {"id": "item4", "signal_X": [2, 2, 3, 3, 4, 4, 5]}
]

config_apply = {
    "correlation_threshold": 0.5,
    "graph_metrics": ["centrality", "density"]
}

graph_analysis_results = apply_graph_based_features(data_items_list, config=config_apply)
# Example: Accessing results
# if "graph_features" in graph_analysis_results and "density" in graph_analysis_results["graph_features"]:
#     print(graph_analysis_results["graph_features"]["density"])
```

## 6. Hardcoding Issues

Several parameters and strings are effectively hardcoded as defaults or constants:

*   **Default Configuration Values:** In [`GraphFeatureExtractor.__init__`](recursive_training/data/graph_based_features.py:42):
    *   `correlation_method`: Defaults to `"pearson"` ([line 53](recursive_training/data/graph_based_features.py:53)).
    *   `correlation_threshold`: Defaults to `0.7` ([line 54](recursive_training/data/graph_based_features.py:54)).
    *   `absolute_threshold`: Defaults to `True` ([line 55](recursive_training/data/graph_based_features.py:55)).
    *   `window_size`: Defaults to `None` ([line 56](recursive_training/data/graph_based_features.py:56)).
    *   `include_negative`: Defaults to `False` ([line 57](recursive_training/data/graph_based_features.py:57)).
    *   `graph_metrics`: Defaults to `["centrality", "clustering", "communities"]` ([line 58](recursive_training/data/graph_based_features.py:58)).
*   **Logger Names:**
    *   `"GraphFeatureExtractor"` ([line 49](recursive_training/data/graph_based_features.py:49)).
    *   `"GraphFeatureProcessor"` ([line 645](recursive_training/data/graph_based_features.py:645)).
*   **NaN Handling Threshold:** In [`_preprocess_time_series`](recursive_training/data/graph_based_features.py:133), a series is skipped if its NaN ratio exceeds `0.3` ([line 168](recursive_training/data/graph_based_features.py:168)). This threshold could be made configurable.
*   **Eigenvector Centrality Parameter:** `max_iter` is set to `1000` for [`nx.eigenvector_centrality`](recursive_training/data/graph_based_features.py:391).
*   **Resilience Metric Node Percentage:** In [`_calculate_graph_level_metrics`](recursive_training/data/graph_based_features.py:526), the top `0.1` (10%) of nodes by degree are considered for removal in a resilience approximation ([line 601](recursive_training/data/graph_based_features.py:601)). This percentage could be configurable.
*   **Input Data Keys in `apply_graph_based_features`:** The keys `"time_series"`, `"values"`, and `"data"` are hardcoded strings used to heuristically locate time series data within input items ([lines 655-660](recursive_training/data/graph_based_features.py:655-660)).

## 7. Coupling Points

*   **Configuration Dictionary:** The [`GraphFeatureExtractor`](recursive_training/data/graph_based_features.py:28) class is tightly coupled to the structure and specific keys expected within the `config` dictionary provided during initialization.
*   **Input Data Structure:**
    *   [`GraphFeatureExtractor.extract_features`](recursive_training/data/graph_based_features.py:68) expects input `time_series_data` as `Dict[str, List[float]]`.
    *   [`apply_graph_based_features`](recursive_training/data/graph_based_features.py:631) expects `data_items` as `List[Dict[str, Any]]` and relies on specific internal keys to find time series.
*   **External Library APIs:**
    *   **NetworkX:** The module is heavily dependent on the NetworkX API for all graph-related operations. Significant changes in the NetworkX API could necessitate updates to this module.
    *   **SciPy:** Dependency on `scipy.stats` for specific correlation calculation methods.
    *   **NumPy:** Extensive use of NumPy for data structures and numerical calculations creates a strong coupling.

## 8. Existing Tests

*   Based on the provided workspace file list, there is no dedicated test file specifically named `test_graph_based_features.py` within the `tests/recursive_training/data/` directory.
*   It is possible that functionalities of this module are covered by integration tests within other files, such as `tests/recursive_training/test_feature_processor.py` or `tests/recursive_training/test_feature_processor_integration.py`. However, without inspecting those files, the extent of dedicated unit testing for `graph_based_features.py` is unclear.
*   **Potential Gap:** A lack of specific unit tests for the `GraphFeatureExtractor` class and its methods, covering various configurations, data inputs (including edge cases like empty data, all NaN series, disconnected graphs), and optional dependency scenarios, appears to be a potential gap.

## 9. Module Architecture and Flow

The module's architecture revolves around the `GraphFeatureExtractor` class and a utility function `apply_graph_based_features`.

1.  **`GraphFeatureExtractor` Class:**
    *   **Initialization (`__init__`)**:
        *   Sets up logging.
        *   Loads configuration parameters from an optional dictionary, applying defaults if parameters are missing. Key configurations include correlation method, threshold, window size, and the list of graph metrics to compute.
        *   Checks for the availability of `NetworkX` and `SciPy`, logging warnings and adjusting behavior (e.g., falling back to NumPy correlation) if they are not found.
    *   **Core Logic (`extract_features`)**: This is the main method for feature extraction.
        1.  **Input Validation**: Checks if there's enough data to proceed.
        2.  **Preprocessing (`_preprocess_time_series`)**:
            *   Converts input dictionary of time series lists into a 2D NumPy array.
            *   Handles string-formatted numbers.
            *   Filters out series with a high percentage of `NaN`s (default > 30%).
            *   Aligns series lengths by truncating to the minimum common length.
            *   Imputes remaining `NaN` values using linear interpolation or filling with the nearest valid value.
        3.  **Correlation Matrix Calculation (`_calculate_correlation_matrix` -> `_compute_single_correlation_matrix`)**:
            *   If a `window_size` is configured, it computes correlations for rolling windows and then averages these correlation matrices.
            *   Otherwise, it computes a single correlation matrix for the entire length of the series.
            *   Supports "pearson", "spearman", "kendall" (if SciPy is available) or falls back to `np.corrcoef`.
            *   Converts any resulting `NaN`s in the correlation matrix to `0.0`.
        4.  **Graph Construction (`_build_graph`)**:
            *   Requires `NetworkX`. If unavailable, feature extraction beyond the correlation matrix stops.
            *   Creates an `nx.Graph`. Nodes correspond to the input time series.
            *   Edges are added between nodes if their correlation value meets the configured `threshold`. The `absolute_threshold` and `include_negative` configurations determine how the threshold is applied. Edge `weight` is set to the correlation value.
        5.  **Graph Metric Extraction**: Iterates through the metrics specified in `self.graph_metrics` and calls dedicated internal methods:
            *   [`_calculate_centrality_metrics`](recursive_training/data/graph_based_features.py:350): Computes degree, closeness (handling disconnected graphs by focusing on the largest connected component), betweenness, and eigenvector centrality (with a convergence fallback), and PageRank. Identifies the most central node for each metric.
            *   [`_calculate_clustering_metrics`](recursive_training/data/graph_based_features.py:421): Computes node-local clustering coefficients, graph average clustering coefficient, and transitivity. Attempts to compute rich club coefficient.
            *   [`_detect_communities`](recursive_training/data/graph_based_features.py:460): Uses NetworkX's greedy modularity maximization to find communities. Reports community members, count, and attempts to calculate the modularity score.
            *   [`_calculate_graph_level_metrics`](recursive_training/data/graph_based_features.py:526): Computes density, average degree. For connected graphs (or the largest component of disconnected ones): average shortest path length, diameter, eccentricity, radius, periphery, and center. Also calculates degree assortativity, global efficiency, and a basic connectivity resilience metric (by simulating removal of top 10% degree-central nodes).
        6.  **Output**: Returns a dictionary containing all computed features, including the correlation matrix, series names, basic graph properties (node/edge counts, density), and a timestamp.

2.  **`apply_graph_based_features` Function:**
    *   A wrapper function designed to apply the `GraphFeatureExtractor` to a list of data items (dictionaries).
    *   It iterates through the `data_items`, heuristically attempting to find lists of numerical data under common keys (`"time_series"`, `"values"`, `"data"`) or any top-level key holding a list of numbers. These are aggregated into a single `time_series_dict`.
    *   Instantiates `GraphFeatureExtractor` with the provided or default configuration.
    *   Calls `extractor.extract_features` with the aggregated time series.
    *   Returns the resulting graph features dictionary, nested under a `"graph_features"` key.

## 10. Naming Conventions

*   **Classes:** `GraphFeatureExtractor` follows PascalCase, which is standard.
*   **Methods and Functions:** Primarily use snake_case (e.g., [`extract_features`](recursive_training/data/graph_based_features.py:68), [`_calculate_correlation_matrix`](recursive_training/data/graph_based_features.py:231), [`apply_graph_based_features`](recursive_training/data/graph_based_features.py:631)), adhering to PEP 8. Internal helper methods are correctly prefixed with a single underscore (e.g., [`_preprocess_time_series`](recursive_training/data/graph_based_features.py:133)).
*   **Variables:** Generally use snake_case (e.g., `correlation_matrix`, `time_series_data`, `graph_features`, `num_series`).
*   **Constants:** Global constants like `NETWORKX_AVAILABLE` and `SCIPY_AVAILABLE` use UPPER_SNAKE_CASE, which is appropriate.
*   **Clarity:** Most names are descriptive and clearly convey their purpose (e.g., `degree_centrality`, `average_shortest_path_length`).
*   **Consistency:** Naming is consistent throughout the module.
*   **AI Assumption Errors/Deviations:** No obvious errors or unconventional naming choices that would suggest problematic AI generation or significant deviation from common Python practices. The use of `G` as a variable name for a NetworkX graph object is a widely accepted convention. `H` is used for a modified graph copy, acceptable in its local scope.

Overall, the naming conventions are clear, consistent, and align well with Python community standards (PEP 8).