# Analysis Report: `forecast_output.forecast_compressor`

**Version:** As of `forecast_output/forecast_compressor.py` (Pulse Version: v0.21.2)
**Patch Note:** "Auto-calls forecast_summary_synthesizer after compressing clusters"

## Table of Contents
1.  [Module Intent/Purpose](#1-module-intentpurpose)
2.  [Operational Status/Completeness](#2-operational-statuscompleteness)
3.  [Implementation Gaps / Unfinished Next Steps](#3-implementation-gaps--unfinished-next-steps)
4.  [Connections & Dependencies](#4-connections--dependencies)
    *   [Direct Project Imports](#41-direct-project-imports)
    *   [External Library Dependencies](#42-external-library-dependencies)
    *   [Data Interactions](#43-data-interactions)
    *   [Input/Output Files](#44-inputoutput-files)
5.  [Function and Class Example Usages](#5-function-and-class-example-usages)
    *   [`compress_mc_samples`](#51-compress_mc_samplesmc_samples-alpha09)
    *   [`flag_drift_sensitive_forecasts`](#52-flag_drift_sensitive_forecastsforecasts-drift_report-threshold02)
    *   [`compress_forecasts`](#53-compress_forecastsforecasts-cluster_key-top_n-summarize-arc_drift-drift_report)
6.  [Hardcoding Issues](#6-hardcoding-issues)
7.  [Coupling Points](#7-coupling-points)
8.  [Existing Tests](#8-existing-tests)
9.  [Module Architecture and Flow](#9-module-architecture-and-flow)
10. [Naming Conventions](#10-naming-conventions)

---

## 1. Module Intent/Purpose

The primary role of the [`forecast_output.forecast_compressor`](forecast_output/forecast_compressor.py:0) module is to process and condense forecast data. This involves:
*   Compressing Monte Carlo (MC) forecast samples into statistical summaries (mean, prediction intervals).
*   Clustering a list of forecasts based on a specified key (e.g., `symbolic_tag`).
*   Calculating aggregate metrics for these clusters (e.g., average confidence, top drivers).
*   Flagging forecasts that might be sensitive to drift based on an external `drift_report`.
*   Calculating an `attention_score` for clusters based on `arc_drift` data.
*   Persisting the compressed forecast clusters to a JSON file.
*   Triggering a downstream summarization step by calling [`summarize_forecasts`](forecast_output/forecast_summary_synthesizer.py:0) from the [`forecast_output.forecast_summary_synthesizer`](forecast_output/forecast_summary_synthesizer.py:0) module.

## 2. Operational Status/Completeness

The module appears largely complete and operational for its defined tasks.
*   It contains well-defined functions with docstrings.
*   Error handling is present for various scenarios (e.g., invalid inputs, file I/O issues).
*   Logging is implemented using [`utils.log_utils.get_logger`](utils/log_utils.py:0).
*   A patch note at the beginning of the file indicates active maintenance or recent updates.
*   An `if __name__ == "__main__":` block provides a basic example usage, suggesting it can be run for simple testing or demonstration.
*   No explicit `TODO` comments or obvious major placeholders are visible in the code.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Drift Report Dependency:** The [`flag_drift_sensitive_forecasts`](forecast_output/forecast_compressor.py:52) function relies on a `drift_report` dictionary with an expected structure (keys like `rule_trigger_delta`, `overlay_drift`, `arc_stability`). The module does not define or validate this structure comprehensively, making it sensitive to changes in the format or availability of this external report.
*   **Externalized Logic for Scoring:** The computation of `compute_symbolic_attention_score` is handled by the external [`trust_system.trust_engine`](trust_system/trust_engine.py:0) module. The specifics of this scoring mechanism and the `arc_drift` data it uses are not detailed within this module.
*   **Summarization Chain:** The module's effectiveness is partly dependent on the downstream [`summarize_forecasts`](forecast_output/forecast_summary_synthesizer.py:0) function. The comment "Always call summarize_forecasts after compression for downstream integration" highlights this critical link.
*   **Configuration of Thresholds:**
    *   The `threshold` (default 0.2) in [`flag_drift_sensitive_forecasts`](forecast_output/forecast_compressor.py:52) and the multiplier `10` used with `rule_trigger_delta` (line 79) are effectively magic numbers. These might be better managed via a centralized configuration system for easier tuning.
    *   The `alpha` value (default 0.9) in [`compress_mc_samples`](forecast_output/forecast_compressor.py:16) for prediction intervals could also be a configurable parameter.
*   **Error Handling Specificity:** While `try-except` blocks are used, some error handling is generic (e.g., logging an error and setting default values or returning). Depending on the system's requirements, more specific error handling or propagation strategies might be beneficial.

## 4. Connections & Dependencies

### 4.1. Direct Project Imports
*   [`from forecast_output.forecast_summary_synthesizer import summarize_forecasts`](forecast_output/forecast_summary_synthesizer.py:0)
*   [`from utils.log_utils import get_logger`](utils/log_utils.py:0)
*   [`from core.path_registry import PATHS`](core/path_registry.py:0)
*   [`from trust_system.trust_engine import compute_symbolic_attention_score`](trust_system/trust_engine.py:0)

### 4.2. External Library Dependencies
*   `json`
*   `os` (implicitly, for path operations)
*   `typing` (List, Dict, Optional)
*   `numpy` (as `np`)
*   `collections.defaultdict`, `collections.Counter` (imported locally within [`compress_forecasts`](forecast_output/forecast_compressor.py:121))

### 4.3. Data Interactions
*   **Inputs:**
    *   `forecasts`: A list of dictionaries, where each dictionary represents a single forecast with various attributes (e.g., `symbolic_tag`, `confidence`, `drivers`, `arc_label`).
    *   `mc_samples`: A list of dictionaries for Monte Carlo samples, where each maps field names to NumPy arrays.
    *   `drift_report`: A dictionary containing analysis of rule and overlay drift.
    *   `arc_drift`: A dictionary containing arc drift deltas.
*   **Outputs:**
    *   Returns a list of compressed cluster dictionaries.
    *   The structure of these dictionaries is a key contract for consumers.
*   **Shared Data via Files:**
    *   Writes compressed forecast data to a JSON file specified by `PATHS["FORECAST_COMPRESSED"]` from [`core.path_registry`](core/path_registry.py:0). This file serves as an integration point for other parts of the system.
*   **Downstream Calls:**
    *   Calls [`summarize_forecasts`](forecast_output/forecast_summary_synthesizer.py:0), passing the compressed data to it, indicating that the [`forecast_output.forecast_summary_synthesizer`](forecast_output/forecast_summary_synthesizer.py:0) module consumes this output.

### 4.4. Input/Output Files
*   **Output File:** The primary output file is defined by `PATHS["FORECAST_COMPRESSED"]`. This is a JSON file containing the list of compressed forecast clusters.
*   **Log Files:** The module uses [`get_logger`](utils/log_utils.py:0), so log messages will be written to files as configured by the project's logging setup.

## 5. Function and Class Example Usages

### 5.1. `compress_mc_samples(mc_samples, alpha=0.9)`
*   **Purpose:** Compresses multiple Monte Carlo forecast samples into a mean forecast and a prediction interval.
*   **Usage:**
    ```python
    import numpy as np
    # from forecast_output.forecast_compressor import compress_mc_samples # Assuming import

    mc_samples_data = [
        {"price": np.array([100, 102, 101]), "volume": np.array([1000, 1100, 1050])},
        {"price": np.array([98, 103, 100]), "volume": np.array([950, 1150, 1020])},
        {"price": np.array([101, 101, 102]), "volume": np.array([1020, 1080, 1080])}
    ]
    compressed_data = compress_mc_samples(mc_samples_data, alpha=0.95)
    # compressed_data will be like:
    # {
    #     "price": {"mean": array([...]), "lower": array([...]), "upper": array([...])},
    #     "volume": {"mean": array([...]), "lower": array([...]), "upper": array([...])}
    # }
    ```

### 5.2. `flag_drift_sensitive_forecasts(forecasts, drift_report, threshold=0.2)`
*   **Purpose:** Adds a `drift_flag` to each forecast dictionary based on instability indicators in the `drift_report`.
*   **Usage:**
    ```python
    # from forecast_output.forecast_compressor import flag_drift_sensitive_forecasts # Assuming import

    forecast_list = [
        {"arc_label": "stable_growth", "fired_rules": ["rule_A"], "forecast": {"symbolic_change": {"overlay1": 0.1}}},
        {"arc_label": "collapse_risk", "fired_rules": ["rule_B"], "forecast": {"symbolic_change": {"overlay2": 0.3}}}
    ]
    drift_report_data = {
        "rule_trigger_delta": {"rule_B": 3.0}, # rule_B is volatile (3.0 > 0.2 * 10)
        "overlay_drift": {"overlay1": 0.15, "overlay2": 0.25}, # overlay2 is unstable (0.25 > 0.2)
        "arc_stability": {"collapse": 0.3} # collapse arc is unstable (0.3 > 0.2)
    }
    flagged_forecasts = flag_drift_sensitive_forecasts(forecast_list, drift_report_data)
    # Each forecast in flagged_forecasts will now have a "drift_flag" key, e.g.:
    # fc1: "✅ Stable" (assuming rule_A and overlay1 are stable)
    # fc2: "⚠️ Rule Instability" (due to rule_B) or "⚠️ Overlay Volatility" or "⚠️ Arc Volatility"
    ```

### 5.3. `compress_forecasts(forecasts, cluster_key="symbolic_tag", top_n=None, summarize=True, arc_drift=None, drift_report=None)`
*   **Purpose:** The main function to cluster, summarize, and compress a list of forecasts.
*   **Usage:** (Derived from the `if __name__ == "__main__":` block)
    ```python
    import json
    # from forecast_output.forecast_compressor import compress_forecasts # Assuming import

    sample_forecasts = [
        {"symbolic_tag": "hope", "confidence": 0.62, "drivers": ["NVDA earnings", "AI sentiment"], "arc_label": "tech_rally"},
        {"symbolic_tag": "hope", "confidence": 0.68, "drivers": ["FED stance"], "arc_label": "tech_rally"},
        {"symbolic_tag": "fatigue", "confidence": 0.43, "drivers": ["news overload"], "arc_label": "market_correction"}
    ]
    # Assuming PATHS is configured and forecast_summary_synthesizer.summarize_forecasts exists
    # and trust_system.trust_engine.compute_symbolic_attention_score exists.
    
    # Example with drift report and arc drift
    drift_report_data = {"rule_trigger_delta": {}, "overlay_drift": {}} # Simplified
    arc_drift_data = {"tech_rally": 5, "market_correction": -2} # Simplified

    compressed_result = compress_forecasts(
        sample_forecasts,
        cluster_key="symbolic_tag",
        top_n=5,
        summarize=True, # This will call summarize_forecasts
        arc_drift=arc_drift_data,
        drift_report=drift_report_data
    )
    print(json.dumps(compressed_result, indent=2))
    # This will print the compressed clusters and also write to PATHS["FORECAST_COMPRESSED"]
    # and call summarize_forecasts(compressed_result)
    ```

## 6. Hardcoding Issues

*   **`alpha = 0.9`**: Default confidence level in [`compress_mc_samples`](forecast_output/forecast_compressor.py:18).
*   **`threshold = 0.2`**: Default drift sensitivity threshold in [`flag_drift_sensitive_forecasts`](forecast_output/forecast_compressor.py:52).
*   **`threshold * 10`**: Magic number multiplier for `rule_trigger_delta` sensitivity in [`flag_drift_sensitive_forecasts`](forecast_output/forecast_compressor.py:79).
*   **`cluster_key = "symbolic_tag"`**: Default key for clustering in [`compress_forecasts`](forecast_output/forecast_compressor.py:123).
*   **`"unknown"` string literal**: Used as a default for `arc_label` (lines 94, 177) and `cluster_key` default value if missing (line 157).
*   **Drift Flag Strings**: e.g., `"⚠️ Rule Instability"`, `"✅ Stable"`. These are hardcoded (lines 103, 106, 109, 113, 117). If these need to be machine-parsed or frequently changed, constants would be better.
*   **Top N Counts**:
    *   Number of top drivers extracted is hardcoded to `3` (line 173).
    *   Number of example forecasts kept per cluster is hardcoded to `2` (line 188).
*   **File Path Key**: `PATHS["FORECAST_COMPRESSED"]` (line 48) uses the string literal `"FORECAST_COMPRESSED"` as a key. This is standard for path registries but still a hardcoded key.

## 7. Coupling Points

*   **[`forecast_output.forecast_summary_synthesizer`](forecast_output/forecast_summary_synthesizer.py:0)**: Tightly coupled due to the direct call to [`summarize_forecasts`](forecast_output/forecast_summary_synthesizer.py:0). The `summarize=True` default and the patch note emphasize this dependency for downstream processing.
*   **[`core.path_registry.PATHS`](core/path_registry.py:0)**: Dependency for obtaining the output file path. Changes to the `PATHS` dictionary structure or the specific key `"FORECAST_COMPRESSED"` would break file output.
*   **[`trust_system.trust_engine.compute_symbolic_attention_score`](trust_system/trust_engine.py:0)**: External dependency for calculating attention scores.
*   **Input Data Structures:** The module heavily relies on the specific structure and keys within the input `forecasts` dictionaries, the `drift_report`, and `arc_drift` data. Any changes to these external data structures would necessitate updates in this module.
*   **Output Data Structure:** The structure of the JSON data written to `COMPRESSED_OUTPUT` and the list of dictionaries passed to [`summarize_forecasts`](forecast_output/forecast_summary_synthesizer.py:0) forms a contract with any consuming modules or processes.

## 8. Existing Tests

*   **No Dedicated Test File:** Based on the provided file listing, there does not appear to be a dedicated test file (e.g., `tests/forecast_output/test_forecast_compressor.py` or `tests/test_forecast_compressor.py`).
*   **Inline Example/Test:** The `if __name__ == "__main__":` block (lines 208-216) in [`forecast_output/forecast_compressor.py`](forecast_output/forecast_compressor.py:208) serves as a basic smoke test or example usage for the [`compress_forecasts`](forecast_output/forecast_compressor.py:121) function.
*   **Runtime Assertion:** An `assert isinstance(PATHS, dict)` (line 46) exists, providing a minimal runtime check for the `PATHS` import.
*   **Gaps:**
    *   No apparent unit tests for [`compress_mc_samples`](forecast_output/forecast_compressor.py:16) or [`flag_drift_sensitive_forecasts`](forecast_output/forecast_compressor.py:52).
    *   The existing inline example does not cover various edge cases, error conditions (e.g., malformed inputs, I/O errors beyond basic handling), or different combinations of optional parameters for [`compress_forecasts`](forecast_output/forecast_compressor.py:121).
    *   The interaction with `drift_report` and `arc_drift` is not tested in the inline example.

## 9. Module Architecture and Flow

The module's logic flows through three main functions:

1.  **[`compress_mc_samples(mc_samples, alpha)`](forecast_output/forecast_compressor.py:16)**:
    *   **Input:** A list of Monte Carlo sample dictionaries.
    *   **Process:** Iterates through each field name present in the samples. For each field, it stacks the data from all samples and calculates the mean and specified percentiles (lower/upper bounds based on `alpha`) across the samples.
    *   **Output:** A dictionary where keys are field names, and values are dictionaries containing 'mean', 'lower', and 'upper' NumPy arrays.

2.  **[`flag_drift_sensitive_forecasts(forecasts, drift_report, threshold)`](forecast_output/forecast_compressor.py:52)**:
    *   **Input:** A list of forecast dictionaries, a `drift_report` dictionary, and a `threshold` value.
    *   **Process:**
        *   Performs input validation.
        *   Extracts sets of `volatile_rules` and `unstable_overlays` from the `drift_report` based on the `threshold`.
        *   Iterates through each forecast:
            *   Checks if any of its `fired_rules` are in `volatile_rules`.
            *   Checks if any of its `symbolic_change` keys (overlays) are in `unstable_overlays`.
            *   Checks if the forecast's `arc_label` (if "collapse") indicates instability based on `drift_report["arc_stability"]`.
            *   Assigns a corresponding `drift_flag` string to the forecast dictionary.
    *   **Output:** The input list of forecasts, with each forecast dictionary augmented with a `drift_flag`.

3.  **[`compress_forecasts(forecasts, cluster_key, top_n, summarize, arc_drift, drift_report)`](forecast_output/forecast_compressor.py:121)**:
    *   **Input:** A list of forecast dictionaries and several optional parameters controlling clustering, filtering, and summarization.
    *   **Process:**
        *   If `drift_report` is provided, it calls [`flag_drift_sensitive_forecasts`](forecast_output/forecast_compressor.py:52) to flag forecasts.
        *   Filters out forecasts that were flagged for "Rule Instability" or "Overlay Volatility".
        *   Groups the remaining forecasts into clusters based on the `cluster_key` (e.g., "symbolic_tag").
        *   If `top_n` is specified, it sorts clusters by size (number of forecasts) and keeps only the top N.
        *   For each selected cluster:
            *   Calculates the average confidence.
            *   Identifies the top N most common drivers.
            *   If `arc_drift` data is available, it computes an `attention_score` using the imported [`compute_symbolic_attention_score`](trust_system/trust_engine.py:0) function.
            *   Collects a small number of example forecasts from the group.
            *   Compiles this information into a dictionary representing the compressed cluster.
        *   Writes the list of compressed cluster dictionaries to a JSON file (path from `COMPRESSED_OUTPUT`).
        *   If `summarize` is `True` (default), it calls the external [`summarize_forecasts`](forecast_output/forecast_summary_synthesizer.py:0) function, passing the list of compressed clusters.
    *   **Output:** The list of compressed cluster dictionaries.

## 10. Naming Conventions

*   **Functions:** Adhere to PEP 8 (e.g., [`compress_mc_samples`](forecast_output/forecast_compressor.py:16), [`flag_drift_sensitive_forecasts`](forecast_output/forecast_compressor.py:52)). Names are descriptive.
*   **Variables:** Mostly snake_case (e.g., `mc_samples`, `cluster_key`, `avg_conf`, `volatile_rules`). Short-form variables like `fc` (forecast) and `ds` (drivers) are used in tight loops and are generally understandable in context.
*   **Constants:** `COMPRESSED_OUTPUT` and `PATHS` (imported) are in uppercase, following Python conventions.
*   **Parameters:** Names are clear and indicative of their purpose (e.g., `alpha`, `threshold`, `arc_label`, `drift_report`).
*   **Clarity & Consistency:** Overall, naming is clear and consistent within the module.
*   **Potential AI/Deviations:**
    *   The use of emoji characters (⚠️, ✅) in string literals for `drift_flag` values is a notable stylistic choice. While visually informative, it might be less conventional if these flags were intended for robust programmatic parsing elsewhere, though likely intended for human-readable reports or UI elements.
    *   No other significant deviations from standard Python naming conventions or obvious AI-generated naming patterns were observed. The module name [`forecast_compressor.py`](forecast_output/forecast_compressor.py:0) accurately reflects its content.