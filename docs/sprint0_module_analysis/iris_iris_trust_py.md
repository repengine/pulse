# Module Analysis: `iris/iris_trust.py`

## 1. Module Intent/Purpose

The primary role of the [`iris/iris_trust.py`](../../../iris/iris_trust.py:1) module is to assess and score the trustworthiness of incoming signals. It achieves this by:
*   Calculating a **recency score** based on the signal's timestamp.
*   Performing **anomaly detection** on signal values using two methods:
    *   Isolation Forest.
    *   Z-score calculation over a sliding window.
*   Computing a composite **Signal Trust Index (STI)** that combines recency and anomaly detection results.

The module provides an [`IrisTrustScorer`](../../../iris/iris_trust.py:18) class to encapsulate this functionality.

## 2. Operational Status/Completeness

The module appears to be functionally complete for its defined scope. The [`IrisTrustScorer`](../../../iris/iris_trust.py:18) class implements all described scoring mechanisms (recency, Isolation Forest anomaly, Z-score anomaly, and STI computation). There are no explicit `TODO` comments or obvious placeholders in the code, suggesting it's considered operational for its current design.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Model Persistence & State:** The `IsolationForest` model ([`self.anomaly_model`](../../../iris/iris_trust.py:24)) is re-fitted with a small window of recent data upon each call to [`detect_anomaly_isolation()`](../../../iris/iris_trust.py:41). Similarly, the [`self.zscore_window`](../../../iris/iris_trust.py:23) is managed in memory. For long-term learning or consistent behavior across application restarts, mechanisms for persisting and loading the model state and the z-score window might be needed.
*   **Configurability of Parameters:** Several key parameters are hardcoded:
    *   `IsolationForest(contamination=0.1, random_state=42)` ([`iris_trust.py:24`](../../../iris/iris_trust.py:24)): The `contamination` rate and `random_state` could be configurable.
    *   Recency `max_age` (7 days) in [`score_recency()`](../../../iris/iris_trust.py:26).
    *   Window size for Isolation Forest fitting (last 100 from `zscore_window`) in [`detect_anomaly_isolation()`](../../../iris/iris_trust.py:52).
    *   Z-score window parameters (min 10, max 50) and threshold (3.0) in [`detect_anomaly_zscore()`](../../../iris/iris_trust.py:59).
    *   STI calculation weights (`base = 0.6`, `recency_boost = 0.3`, `anomaly_penalty = -0.2`) in [`compute_signal_trust_index()`](../../../iris/iris_trust.py:80).
    Making these configurable would offer greater flexibility.
*   **Combined Anomaly Strategy:** The module provides two anomaly detection methods but doesn't prescribe how to combine their results. The consuming code would need to decide whether one or both flags trigger an "anomalous" status for the STI calculation.
*   **Efficiency for High-Frequency Data:** Re-fitting the `IsolationForest` model on each call might be computationally intensive if signals arrive at a very high frequency. An incremental learning approach or periodic re-fitting could be considered.

## 4. Connections & Dependencies

*   **Direct Imports from other project modules:** None observed in the provided code.
*   **External Library Dependencies:**
    *   `numpy` (as `np`): Used for numerical operations, specifically for mean and standard deviation calculations in Z-score.
    *   `datetime`, `timezone` (from `datetime`): Used for handling timestamps and calculating recency.
    *   `IsolationForest` (from `sklearn.ensemble`): Used for anomaly detection.
    *   `List`, `Optional` (from `typing`): Used for type hinting.
*   **Interaction with other modules via shared data:** The module is likely used by other signal processing or decision-making modules within the Iris system. It consumes signal timestamps and values and produces trust scores. It does not appear to directly interact with files, databases, or message queues in its current form.
*   **Input/Output Files:** None directly.

## 5. Function and Class Example Usages

The core component is the [`IrisTrustScorer`](../../../iris/iris_trust.py:18) class.

```python
from ingestion.iris_trust import IrisTrustScorer
from datetime import datetime, timedelta, timezone

# Initialize the scorer
scorer = IrisTrustScorer()

# Simulate some historical data for the z-score window
for i in range(30):
    scorer.zscore_window.append(100.0 + (i % 7 - 3) * 0.5) # Some fluctuating normal data

# Example signal
signal_time = datetime.now(timezone.utc) - timedelta(hours=5)
signal_value = 115.0 # A potentially anomalous value

# 1. Score recency
recency = scorer.score_recency(signal_time)
print(f"Recency Score: {recency:.3f}")

# 2. Detect anomaly using Isolation Forest
# Note: detect_anomaly_isolation uses the current zscore_window (last 100) + new value
is_anomaly_iso = scorer.detect_anomaly_isolation(signal_value)
print(f"Anomaly (Isolation Forest): {is_anomaly_iso}")

# 3. Detect anomaly using Z-score
# Note: detect_anomaly_zscore appends the value to its window
is_anomaly_z = scorer.detect_anomaly_zscore(signal_value)
print(f"Anomaly (Z-score): {is_anomaly_z}")

# 4. Compute Signal Trust Index (STI)
# Assuming an anomaly if either method flags it
anomaly_detected = is_anomaly_iso or is_anomaly_z
sti = scorer.compute_signal_trust_index(recency, anomaly_detected)
print(f"Signal Trust Index (STI): {sti:.3f}")

# Example with a fresh, non-anomalous signal
fresh_signal_time = datetime.now(timezone.utc) - timedelta(minutes=10)
fresh_signal_value = 101.0

recency_fresh = scorer.score_recency(fresh_signal_time)
is_anomaly_iso_fresh = scorer.detect_anomaly_isolation(fresh_signal_value)
is_anomaly_z_fresh = scorer.detect_anomaly_zscore(fresh_signal_value)
anomaly_fresh = is_anomaly_iso_fresh or is_anomaly_z_fresh
sti_fresh = scorer.compute_signal_trust_index(recency_fresh, anomaly_fresh)
print(f"\nFresh Signal STI: {sti_fresh:.3f} (Recency: {recency_fresh:.3f}, Anomaly: {anomaly_fresh})")
```

## 6. Hardcoding Issues

Several parameters and thresholds are hardcoded within the module:

*   **[`IrisTrustScorer.__init__()`](../../../iris/iris_trust.py:19):**
    *   `contamination=0.1` for `IsolationForest` ([`iris_trust.py:24`](../../../iris/iris_trust.py:24)).
    *   `random_state=42` for `IsolationForest` ([`iris_trust.py:24`](../../../iris/iris_trust.py:24)).
*   **[`score_recency()`](../../../iris/iris_trust.py:26):**
    *   `max_age = 7 * 24 * 3600` (7 days in seconds) ([`iris_trust.py:38`](../../../iris/iris_trust.py:38)).
*   **[`detect_anomaly_isolation()`](../../../iris/iris_trust.py:41):**
    *   Uses the last 100 values from `self.zscore_window` for fitting: `self.zscore_window[-100:]` ([`iris_trust.py:52`](../../../iris/iris_trust.py:52)).
*   **[`detect_anomaly_zscore()`](../../../iris/iris_trust.py:59):**
    *   Minimum window size: `len(self.zscore_window) < 10` ([`iris_trust.py:70`](../../../iris/iris_trust.py:70)).
    *   Maximum window size / slice point: `len(self.zscore_window) > 50`, `self.zscore_window[-50:]` ([`iris_trust.py:72-73`](../../../iris/iris_trust.py:72-73)).
    *   Z-score threshold: `abs(z) > 3.0` ([`iris_trust.py:78`](../../../iris/iris_trust.py:78)).
    *   Epsilon for std calculation: `1e-6` ([`iris_trust.py:76`](../../../iris/iris_trust.py:76)).
*   **[`compute_signal_trust_index()`](../../../iris/iris_trust.py:80):**
    *   `base = 0.6` (base trust score) ([`iris_trust.py:91`](../../../iris/iris_trust.py:91)).
    *   `recency_boost = 0.3` (weight for recency score contribution) ([`iris_trust.py:92`](../../../iris/iris_trust.py:92)).
    *   `anomaly_penalty = -0.2` (penalty for anomalous signal) ([`iris_trust.py:93`](../../../iris/iris_trust.py:93)).

## 7. Coupling Points

*   The [`IrisTrustScorer`](../../../iris/iris_trust.py:18) class is the primary interface. Other modules will depend on this class and its public methods: [`score_recency()`](../../../iris/iris_trust.py:26), [`detect_anomaly_isolation()`](../../../iris/iris_trust.py:41), [`detect_anomaly_zscore()`](../../../iris/iris_trust.py:59), and [`compute_signal_trust_index()`](../../../iris/iris_trust.py:80).
*   The module expects `datetime` objects for timestamps and `float` values for signals.
*   The output STI is a `float`, which consuming modules will use for decision-making.

## 8. Existing Tests

Based on the file listing and the content of [`tests/test_trust_engine_risk.py`](../../../tests/test_trust_engine_risk.py:1), there do not appear to be dedicated unit tests specifically for the [`ingestion.iris_trust`](../../../iris/iris_trust.py:1) module or the [`IrisTrustScorer`](../../../iris/iris_trust.py:18) class. The existing test file seems to target a different `TrustEngine` in the `trust_system` package.

This indicates a gap in test coverage for this specific module.

## 9. Module Architecture and Flow

The module's architecture is centered around the [`IrisTrustScorer`](../../../iris/iris_trust.py:18) class.

**Control Flow:**
1.  An instance of [`IrisTrustScorer`](../../../iris/iris_trust.py:18) is created. This initializes an empty list [`self.zscore_window`](../../../iris/iris_trust.py:23) and an `IsolationForest` model [`self.anomaly_model`](../../../iris/iris_trust.py:24).
2.  When a new signal (timestamp and value) needs to be evaluated:
    a.  The signal's `timestamp` is passed to [`score_recency()`](../../../iris/iris_trust.py:26), which calculates a recency score between 0.0 and 1.0.
    b.  The signal's `value` is passed to [`detect_anomaly_isolation()`](../../../iris/iris_trust.py:41). This method takes the last 100 values from `self.zscore_window`, adds the new value, fits the `IsolationForest` model on this temporary window, and predicts if the new value is an anomaly (-1 for anomaly).
    c.  The signal's `value` is passed to [`detect_anomaly_zscore()`](../../../iris/iris_trust.py:59). This method appends the value to `self.zscore_window` (maintaining a max size of 50). If the window is large enough (>=10), it calculates the Z-score for the new value and flags it as an anomaly if `abs(z) > 3.0`.
    d.  The `recency_score` and a boolean `anomaly_flag` (derived from the outputs of the anomaly detection methods) are passed to [`compute_signal_trust_index()`](../../../iris/iris_trust.py:80).
    e.  This method calculates the STI based on a formula involving a base score, a boost from recency, and a penalty if anomalous. The result is clamped between 0.0 and 1.0 and rounded.
3.  The calculated STI is returned to the caller.

**Data Flow:**
*   **Inputs:** `timestamp` (`datetime`), `value` (`float`).
*   **Internal State:** `self.zscore_window` (list of `float`), `self.anomaly_model` (`IsolationForest` instance).
*   **Outputs:** `recency_score` (`float`), `anomaly_flag` (`bool` from detection methods), `sti` (`float`).

## 10. Naming Conventions

*   **Module Name:** `iris_trust.py` - Clear and indicative of its purpose within an "iris" system.
*   **Class Name:** [`IrisTrustScorer`](../../../iris/iris_trust.py:18) - PascalCase, clear, and descriptive.
*   **Method Names:**
    *   [`__init__()`](../../../iris/iris_trust.py:19)
    *   [`score_recency()`](../../../iris/iris_trust.py:26)
    *   [`detect_anomaly_isolation()`](../../../iris/iris_trust.py:41)
    *   [`detect_anomaly_zscore()`](../../../iris/iris_trust.py:59)
    *   [`compute_signal_trust_index()`](../../../iris/iris_trust.py:80)
    All use snake_case and are descriptive of their actions.
*   **Variable Names:** `now`, `delta_seconds`, `max_age`, `zscore_window`, `anomaly_model`, `window`, `prediction`, `mean`, `std`, `z`, `recency_score`, `anomaly_flag`, `base`, `recency_boost`, `anomaly_penalty`, `sti`. All use snake_case and are generally clear.
*   **Constants:** Some values are assigned to variables (e.g., `max_age`), while others are used as magic numbers/strings directly in the code (e.g., `0.1` for contamination, `42` for `random_state`, window size limits `10`, `50`, `100`, Z-score threshold `3.0`, STI calculation weights `0.6`, `0.3`, `-0.2`).
*   **Docstrings:** The module and class have docstrings. Methods also have docstrings explaining their purpose, arguments, and return values.

Overall, naming conventions are consistent and largely adhere to PEP 8. There are no obvious AI assumption errors in naming. The main area for improvement would be to replace magic numbers with named constants for better readability and maintainability.