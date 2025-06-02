"""ingestion.iris_utils.historical_data_verification
=============================================

A module for comprehensive verification and quality assurance of historical data.

This module builds on the basic verification capabilities in historical_data_retriever
and adds more sophisticated data quality assessment methods:

1. Time series continuity analysis (detecting gaps, irregular intervals)
2. Statistical outlier detection (z-score, IQR methods)
3. Trend break detection
4. Cross-correlation between related variables
5. Seasonal pattern verification
6. Cross-source validation
7. Comprehensive data quality scoring

Usage:
------
```python
from ingestion.iris_utils.historical_data_verification import (
    perform_quality_check,
    detect_anomalies,
    cross_validate_sources,
    analyze_gaps,
    generate_quality_report,
    visualize_data_quality
)

# Run a comprehensive quality check on a variable
quality_report = perform_quality_check("spx_close")

# Detect anomalies in a variable's data
anomalies = detect_anomalies("spx_close", method="iqr")

# Compare data from different sources for the same variable
comparison = cross_validate_sources("unemployment_rate")

# Analyze gaps in time series data
gap_report = analyze_gaps("spx_close")

# Generate a comprehensive quality report
report = generate_quality_report("spx_close")

# Visualize data quality
visualization = visualize_data_quality("spx_close")
```

The module also provides a command-line interface through cli_historical_data.py.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks

from ingestion.iris_utils.historical_data_retriever import (
    load_variable_catalog,
    get_priority_variables,
    HISTORICAL_DATA_BASE_DIR,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants for quality assessment
QUALITY_SCORE_WEIGHTS = {
    "completeness": 0.25,
    "consistency": 0.20,
    "anomaly_free": 0.20,
    "time_continuity": 0.15,
    "trend_stability": 0.10,
    "seasonality": 0.10,
}

# Expected variable ranges (to be configured for each variable type)
DEFAULT_VARIABLE_RANGES = {
    "percentage": (0, 100),
    "price": (0, float("inf")),
    "index": (0, float("inf")),
    "rate": (0, float("inf")),
    "count": (0, float("inf")),
    "temperature": (-100, 100),  # Celsius
    "raw": (float("-inf"), float("inf")),  # No specific range
}


class AnomalyDetectionMethod(Enum):
    """Methods for detecting anomalies in time series data."""

    ZSCORE = "zscore"
    IQR = "iqr"
    ISOLATION_FOREST = "isolation_forest"
    LOCAL_OUTLIER_FACTOR = "lof"
    DBSCAN = "dbscan"


class QualityDimension(Enum):
    """Dimensions of data quality assessment."""

    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    ANOMALY_FREE = "anomaly_free"
    TIME_CONTINUITY = "time_continuity"
    TREND_STABILITY = "trend_stability"
    SEASONALITY = "seasonality"


@dataclass
class DataQualityScore:
    """Quality score for a dataset along multiple dimensions."""

    variable_name: str
    completeness: float = 0.0
    consistency: float = 0.0
    anomaly_free: float = 0.0
    time_continuity: float = 0.0
    trend_stability: float = 0.0
    seasonality: float = 0.0

    @property
    def overall_score(self) -> float:
        """Calculate the weighted overall quality score."""
        return (
            self.completeness * QUALITY_SCORE_WEIGHTS["completeness"]
            + self.consistency * QUALITY_SCORE_WEIGHTS["consistency"]
            + self.anomaly_free * QUALITY_SCORE_WEIGHTS["anomaly_free"]
            + self.time_continuity * QUALITY_SCORE_WEIGHTS["time_continuity"]
            + self.trend_stability * QUALITY_SCORE_WEIGHTS["trend_stability"]
            + self.seasonality * QUALITY_SCORE_WEIGHTS["seasonality"]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the quality score to a dictionary."""
        return {
            "variable_name": self.variable_name,
            "dimensions": {
                "completeness": self.completeness,
                "consistency": self.consistency,
                "anomaly_free": self.anomaly_free,
                "time_continuity": self.time_continuity,
                "trend_stability": self.trend_stability,
                "seasonality": self.seasonality,
            },
            "overall_score": self.overall_score,
        }


@dataclass
class Anomaly:
    """Representation of an anomaly in time series data."""

    variable_name: str
    timestamp: dt.datetime
    value: float
    expected_value: Optional[float] = None
    deviation: float = 0.0
    method: str = "unknown"
    severity: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the anomaly to a dictionary."""
        return {
            "variable_name": self.variable_name,
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "expected_value": self.expected_value,
            "deviation": self.deviation,
            "method": self.method,
            "severity": self.severity,
            "context": self.context,
        }


@dataclass
class TimeSeriesGap:
    """Representation of a gap in time series data."""

    variable_name: str
    start_time: dt.datetime
    end_time: dt.datetime
    gap_duration: dt.timedelta
    expected_points: int = 0
    severity: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the gap to a dictionary."""
        return {
            "variable_name": self.variable_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "gap_duration_days": self.gap_duration.days,
            "expected_points": self.expected_points,
            "severity": self.severity,
            "context": self.context,
        }


@dataclass
class TrendBreak:
    """Representation of a break in the trend of time series data."""

    variable_name: str
    timestamp: dt.datetime
    before_trend: float
    after_trend: float
    change_magnitude: float
    severity: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the trend break to a dictionary."""
        return {
            "variable_name": self.variable_name,
            "timestamp": self.timestamp.isoformat(),
            "before_trend": self.before_trend,
            "after_trend": self.after_trend,
            "change_magnitude": self.change_magnitude,
            "severity": self.severity,
            "context": self.context,
        }


@dataclass
class QualityCheckResult:
    """Result of a comprehensive quality check."""

    variable_name: str
    quality_score: DataQualityScore
    anomalies: List[Anomaly] = field(default_factory=list)
    gaps: List[TimeSeriesGap] = field(default_factory=list)
    trend_breaks: List[TrendBreak] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the quality check result to a dictionary."""
        return {
            "variable_name": self.variable_name,
            "quality_score": self.quality_score.to_dict(),
            "anomalies": [a.to_dict() for a in self.anomalies],
            "gaps": [g.to_dict() for g in self.gaps],
            "trend_breaks": [t.to_dict() for t in self.trend_breaks],
            "statistics": self.statistics,
            "recommendations": self.recommendations,
        }


@dataclass
class CrossValidationResult:
    """Result of cross-validating data from multiple sources."""

    variable_name: str
    sources: List[str]
    correlation_matrix: Dict[str, Dict[str, float]]
    mean_differences: Dict[str, Dict[str, float]]
    stddev_differences: Dict[str, Dict[str, float]]
    max_differences: Dict[str, Dict[str, float]]
    aligned_datasets: Dict[str, pd.Series]
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the cross-validation result to a dictionary."""
        # Convert pandas Series to lists for JSON serialization
        aligned_data_dict = {}
        for source, series in self.aligned_datasets.items():
            aligned_data_dict[source] = {
                "dates": [d.isoformat() for d in series.index],
                "values": series.tolist(),
            }

        return {
            "variable_name": self.variable_name,
            "sources": self.sources,
            "correlation_matrix": self.correlation_matrix,
            "mean_differences": self.mean_differences,
            "stddev_differences": self.stddev_differences,
            "max_differences": self.max_differences,
            "aligned_datasets": aligned_data_dict,
            "recommendation": self.recommendation,
        }


def load_processed_data(variable_name: str) -> pd.Series:
    """
    Load processed data for a variable as a pandas Series with datetime index.

    Args:
        variable_name: Name of the variable to load

    Returns:
        pandas Series with datetime index
    """
    # Path to the processed data
    data_dir = Path(HISTORICAL_DATA_BASE_DIR) / variable_name

    if not data_dir.exists():
        raise FileNotFoundError(f"No data directory found for {variable_name}")

    # Find the most recent processed data file
    processed_files = list(data_dir.glob("*_processed.json"))

    if not processed_files:
        raise FileNotFoundError(f"No processed data found for {variable_name}")

    # Sort by modification time (newest first)
    processed_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    # Load the newest processed data
    with open(processed_files[0], "r") as f:
        data = json.load(f)

    # Convert to pandas Series
    dates = []
    values = []

    for item in data["values"]:
        try:
            # Parse the date string to datetime object
            date = pd.to_datetime(item["date"])
            value = float(item["value"])

            dates.append(date)
            values.append(value)
        except (ValueError, KeyError) as e:
            logger.warning(f"Could not parse data point: {e}")

    # Create a Series with datetime index
    series = pd.Series(values, index=dates)
    series.name = variable_name

    # Sort by date
    series = series.sort_index()

    return series


def load_multi_source_data(variable_name: str) -> Dict[str, pd.Series]:
    """
    Load data for a variable from multiple sources if available.

    Args:
        variable_name: Name of the variable to load

    Returns:
        Dictionary mapping source names to pandas Series
    """
    # Get variable info from the catalog
    catalog = load_variable_catalog()
    source_data = {}

    # Find all variable entries for this variable name (potentially from different sources)
    variable_entries = [
        var
        for var in catalog["variables"]
        if var["variable_name"] == variable_name or var.get("alias") == variable_name
    ]

    if not variable_entries:
        raise ValueError(f"Variable {variable_name} not found in the catalog")

    # Load data from each source
    for entry in variable_entries:
        source = entry.get("source", "unknown")
        var_name = entry["variable_name"]

        try:
            series = load_processed_data(var_name)
            source_data[source] = series
        except FileNotFoundError:
            logger.warning(f"No data found for {var_name} from source {source}")

    return source_data


def detect_gaps(
    series: pd.Series,
    freq: str = "D",
    min_gap_size: int = 1,
    expected_frequency: Optional[str] = None,
) -> List[TimeSeriesGap]:
    """
    Detect gaps in time series data.

    Args:
        series: Time series data
        freq: Expected frequency of the data (D=daily, B=business day, M=monthly)
        min_gap_size: Minimum number of missing points to consider a gap
        expected_frequency: Override for the expected frequency

    Returns:
        List of TimeSeriesGap objects
    """
    if len(series) < 2:
        return []

    # Determine the expected frequency if not provided
    if expected_frequency:
        freq = expected_frequency
    else:
        # Try to infer the frequency
        # Ensure we have a DatetimeIndex for frequency inference
        if isinstance(series.index, pd.DatetimeIndex):
            inferred_freq = pd.infer_freq(series.index)
        else:
            # Try to convert to DatetimeIndex
            try:
                dt_index = pd.DatetimeIndex(series.index)
                inferred_freq = pd.infer_freq(dt_index)
            except Exception:
                inferred_freq = None
        if inferred_freq:
            freq = inferred_freq
    # Create a complete date range with the expected frequency
    if freq == "auto":
        logger.info("Auto-detecting frequency")
        # Default to daily if detection fails
        freq = "D"

        try:
            # Attempt to determine frequency
            # Calculate most common interval between timestamps
            sorted_series = series.sort_index()

            # Calculate intervals between consecutive timestamps
            intervals = []
            for i in range(1, len(sorted_series.index)):
                # Convert to timestamps and calculate difference in seconds
                try:
                    t1 = pd.Timestamp(sorted_series.index[i - 1])
                    t2 = pd.Timestamp(sorted_series.index[i])
                    intervals.append((t2 - t1).total_seconds())
                except Exception as e:
                    logger.warning(f"Error calculating interval: {e}")
                    continue

            if intervals:
                # Find the most common interval
                from collections import Counter

                interval_seconds = Counter(intervals).most_common(1)[0][0]

                if (
                    abs(interval_seconds - 86400) < 60
                ):  # 1 day (with 1 minute tolerance)
                    freq = "D"
                    logger.info("Detected daily frequency")
                elif (
                    abs(interval_seconds - 86400 * 7) < 3600
                ):  # 1 week (with 1 hour tolerance)
                    freq = "W"
                    logger.info("Detected weekly frequency")
                elif 28 * 86400 <= interval_seconds <= 31 * 86400:  # ~1 month
                    freq = "M"
                    logger.info("Detected monthly frequency")
                else:
                    logger.info(
                        f"Couldn't determine standard frequency from interval {interval_seconds} seconds, using daily"
                    )
            else:
                logger.warning("No intervals detected, using daily frequency")
        except Exception as e:
            logger.warning(f"Error detecting frequency: {e}, using daily as default")

    full_date_range = pd.date_range(
        start=series.index.min(), end=series.index.max(), freq=freq
    )

    # Find missing dates
    existing_dates = set(series.index)
    missing_dates = [date for date in full_date_range if date not in existing_dates]

    if not missing_dates:
        return []

    # Group consecutive missing dates into gaps
    gaps = []
    current_gap_start = missing_dates[0]
    current_gap_dates = [current_gap_start]

    for i in range(1, len(missing_dates)):
        # Check if this date is consecutive with the previous one
        if missing_dates[i] - missing_dates[i - 1] <= pd.Timedelta(
            days=2
        ):  # Allow for some flexibility
            current_gap_dates.append(missing_dates[i])
        else:
            # End of a gap, start a new one
            if len(current_gap_dates) >= min_gap_size:
                gap = TimeSeriesGap(
                    variable_name=str(series.name)
                    if series.name is not None
                    else "unknown",
                    start_time=current_gap_dates[0],
                    end_time=current_gap_dates[-1],
                    gap_duration=current_gap_dates[-1] - current_gap_dates[0],
                    expected_points=len(current_gap_dates),
                    severity=len(current_gap_dates) / len(full_date_range),
                    context={"frequency": freq},
                )
                gaps.append(gap)

            # Start a new gap
            current_gap_start = missing_dates[i]
            current_gap_dates = [current_gap_start]

    # Don't forget the last gap
    if len(current_gap_dates) >= min_gap_size:
        gap = TimeSeriesGap(
            variable_name=str(series.name) if series.name is not None else "unknown",
            start_time=current_gap_dates[0],
            end_time=current_gap_dates[-1],
            gap_duration=current_gap_dates[-1] - current_gap_dates[0],
            expected_points=len(current_gap_dates),
            severity=len(current_gap_dates) / len(full_date_range),
            context={"frequency": freq},
        )
        gaps.append(gap)

    return gaps


def detect_anomalies(
    series: pd.Series,
    method: Union[str, AnomalyDetectionMethod] = "zscore",
    threshold: float = 3.0,
    window_size: Optional[int] = None,
    variable_type: str = "raw",
) -> List[Anomaly]:
    """
    Detect anomalies in time series data using the specified method.

    Args:
        series: Time series data
        method: Method to use for anomaly detection (zscore, iqr, isolation_forest, lof, dbscan)
        threshold: Threshold for anomaly detection
        window_size: Size of the rolling window for contextual anomaly detection
        variable_type: Type of variable for range validation

    Returns:
        List of Anomaly objects
    """
    if isinstance(method, str):
        try:
            method = AnomalyDetectionMethod(method)
        except ValueError:
            logger.warning(
                f"Unknown anomaly detection method: {method}. Using Z-score."
            )
            method = AnomalyDetectionMethod.ZSCORE

    anomalies = []
    series_values = series.values

    # Basic validation against expected ranges
    expected_range = DEFAULT_VARIABLE_RANGES.get(
        variable_type, DEFAULT_VARIABLE_RANGES["raw"]
    )
    range_min, range_max = expected_range

    for idx, (timestamp, value) in enumerate(series.items()):
        # Skip NaN values
        if pd.isna(value):
            continue

        # Check if value is outside expected range
        if value < range_min or value > range_max:
            deviation = min(abs(value - range_min), abs(value - range_max))
            severity = min(1.0, deviation / max(abs(range_min), abs(range_max)))

            anomalies.append(
                Anomaly(
                    variable_name=str(series.name)
                    if series.name is not None
                    else "unknown",
                    timestamp=pd.Timestamp(timestamp).to_pydatetime()
                    if not isinstance(timestamp, dt.datetime)
                    else timestamp,
                    value=value,
                    expected_value=None,
                    deviation=deviation,
                    method="range_check",
                    severity=severity,
                    context={"range_min": range_min, "range_max": range_max},
                )
            )

    # Apply the selected method for more sophisticated anomaly detection
    if method == AnomalyDetectionMethod.ZSCORE:
        # Z-score method (global)
        # Convert to numpy array to ensure compatibility
        values_array = np.asarray(series_values)
        mean_val = np.mean(values_array)
        std_val = np.std(values_array)

        if std_val == 0:
            logger.warning(
                "Standard deviation is zero, skipping Z-score anomaly detection"
            )
            return anomalies

        # Calculate z-scores using numpy operations
        z_scores = np.abs((values_array - mean_val) / std_val)

        for idx, (timestamp, value) in enumerate(series.items()):
            # Skip NaN values
            if pd.isna(value):
                continue

            z_score = z_scores[idx]
            if z_score > threshold:
                deviation = abs(value - mean_val)

                anomalies.append(
                    Anomaly(
                        variable_name=str(series.name)
                        if series.name is not None
                        else "unknown",
                        timestamp=pd.Timestamp(timestamp).to_pydatetime(),
                        value=value,
                        expected_value=mean_val,
                        deviation=deviation,
                        method="zscore",
                        severity=min(1.0, (z_score - threshold) / threshold),
                        context={
                            "z_score": z_score,
                            "threshold": threshold,
                            "global_mean": mean_val,
                            "global_std": std_val,
                        },
                    )
                )

    elif method == AnomalyDetectionMethod.IQR:
        # Interquartile Range method
        # Convert to numpy array for percentile calculation
        values_array = np.asarray(series_values)
        q1 = np.percentile(values_array, 25)
        q3 = np.percentile(values_array, 75)
        iqr = q3 - q1

        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr

        for idx, (timestamp, value) in enumerate(series.items()):
            # Skip NaN values
            if pd.isna(value):
                continue

            if value < lower_bound or value > upper_bound:
                deviation = min(abs(value - lower_bound), abs(value - upper_bound))

                anomalies.append(
                    Anomaly(
                        variable_name=str(series.name)
                        if series.name is not None
                        else "unknown",
                        timestamp=pd.Timestamp(timestamp).to_pydatetime(),
                        value=value,
                        expected_value=(q1 + q3) / 2,  # Median as expected value
                        deviation=deviation,
                        method="iqr",
                        severity=min(1.0, deviation / iqr),
                        context={
                            "q1": q1,
                            "q3": q3,
                            "iqr": iqr,
                            "lower_bound": lower_bound,
                            "upper_bound": upper_bound,
                        },
                    )
                )

    elif method == AnomalyDetectionMethod.ISOLATION_FOREST:
        try:
            from sklearn.ensemble import IsolationForest

            # Prepare the data
            # Convert to numpy array for reshape operation
            X = np.asarray(series_values).reshape(-1, 1)

            # Train isolation forest
            model = IsolationForest(contamination=0.05, random_state=42)
            predictions = model.fit_predict(X)
            anomaly_scores = model.decision_function(X)

            # Anomalies are marked as -1
            for idx, (timestamp, value) in enumerate(series.items()):
                # Skip NaN values
                if pd.isna(value):
                    continue

                if predictions[idx] == -1:
                    # Convert score to severity (scores close to -1 are more anomalous)
                    score = anomaly_scores[idx]
                    severity = min(1.0, abs(score))

                    anomalies.append(
                        Anomaly(
                            variable_name=str(series.name)
                            if series.name is not None
                            else "unknown",
                            timestamp=pd.Timestamp(timestamp).to_pydatetime()
                            if not isinstance(timestamp, dt.datetime)
                            else timestamp,
                            value=value,
                            expected_value=None,
                            deviation=0.0,  # Isolation Forest doesn't provide this
                            method="isolation_forest",
                            severity=severity,
                            context={"anomaly_score": score},
                        )
                    )
        except ImportError:
            logger.warning("scikit-learn not installed, falling back to Z-score method")
            return detect_anomalies(
                series, "zscore", threshold, window_size, variable_type
            )

    elif method in [
        AnomalyDetectionMethod.LOCAL_OUTLIER_FACTOR,
        AnomalyDetectionMethod.DBSCAN,
    ]:
        logger.warning(
            f"{method.value} not yet implemented, falling back to Z-score method"
        )
        return detect_anomalies(series, "zscore", threshold, window_size, variable_type)

    # Contextual anomalies (if window size provided)
    if window_size and len(series) > window_size:
        rolling_mean = series.rolling(window=window_size, center=True).mean()
        rolling_std = series.rolling(window=window_size, center=True).std()

        for idx, (timestamp, value) in enumerate(series.items()):
            # Skip NaN values or values without enough context
            if (
                pd.isna(value)
                or pd.isna(rolling_mean[idx])
                or pd.isna(rolling_std[idx])
            ):
                continue

            # If standard deviation is zero, skip this point
            if rolling_std[idx] == 0:
                continue

            # Calculate local z-score
            local_z = abs((value - rolling_mean[idx]) / rolling_std[idx])

            if local_z > threshold:
                deviation = abs(value - rolling_mean[idx])

                anomalies.append(
                    Anomaly(
                        variable_name=str(series.name)
                        if series.name is not None
                        else "unknown",
                        timestamp=pd.Timestamp(timestamp).to_pydatetime()
                        if not isinstance(timestamp, dt.datetime)
                        else timestamp,
                        value=value,
                        expected_value=rolling_mean[idx],
                        deviation=deviation,
                        method="contextual_zscore",
                        severity=min(1.0, (local_z - threshold) / threshold),
                        context={
                            "local_z_score": local_z,
                            "threshold": threshold,
                            "window_size": window_size,
                            "local_mean": rolling_mean[idx],
                            "local_std": rolling_std[idx],
                        },
                    )
                )

    # Deduplicate anomalies (same timestamp)
    unique_anomalies = {}
    for anomaly in anomalies:
        if (
            anomaly.timestamp not in unique_anomalies
            or anomaly.severity > unique_anomalies[anomaly.timestamp].severity
        ):
            unique_anomalies[anomaly.timestamp] = anomaly

    return list(unique_anomalies.values())


def detect_trend_breaks(
    series: pd.Series, window_size: int = 30, threshold: float = 2.0
) -> List[TrendBreak]:
    """
    Detect breaks in the trend of time series data.

    Args:
        series: Time series data
        window_size: Size of the window for trend calculation
        threshold: Threshold for trend break detection (z-scores)

    Returns:
        List of TrendBreak objects
    """
    if len(series) < window_size * 2:
        return []

    trend_breaks = []

    # Calculate rolling trends (slopes)
    x = np.arange(window_size)
    slopes = []

    for i in range(len(series) - window_size + 1):
        window = series.iloc[i : i + window_size].values

        # Skip if there are NaN values
        # Convert to numpy array for np.isnan
        window_array = np.asarray(window)
        if np.isnan(window_array).any():
            slopes.append(np.nan)
            continue

        # Linear regression to get slope
        slope, _, _, _, _ = stats.linregress(x, window)
        slopes.append(slope)

    # Convert to numpy array and calculate changes in slope
    slopes = np.array(slopes)
    slope_changes = np.abs(np.diff(slopes))

    # Find points where the slope changes significantly
    mean_change = np.nanmean(slope_changes)
    std_change = np.nanstd(slope_changes)

    if std_change == 0:
        return []

    # Calculate z-scores of slope changes
    z_scores = (slope_changes - mean_change) / std_change

    # Find peaks in z-scores (points where slope changes dramatically)
    peak_indices, _ = find_peaks(z_scores, height=threshold)

    # Convert peak indices to TrendBreak objects
    for idx in peak_indices:
        # The actual break point is at the end of the first window
        break_idx = idx + window_size
        if break_idx < len(series.index):
            before_trend = slopes[idx]
            after_trend = slopes[idx + 1]
            change_magnitude = abs(after_trend - before_trend)

            trend_breaks.append(
                TrendBreak(
                    variable_name=str(series.name)
                    if series.name is not None
                    else "unknown",
                    timestamp=pd.Timestamp(series.index[break_idx]).to_pydatetime()
                    if break_idx < len(series.index)
                    else dt.datetime.now(),
                    before_trend=float(before_trend),
                    after_trend=float(after_trend),
                    change_magnitude=float(change_magnitude),
                    severity=min(1.0, float(z_scores[idx] / threshold)),
                    context={
                        "z_score": z_scores[idx],
                        "threshold": threshold,
                        "window_size": window_size,
                    },
                )
            )

    return trend_breaks


def detect_seasonality(
    series: pd.Series, periods: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Detect seasonal patterns in time series data.

    Args:
        series: Time series data
        periods: List of periods to check for seasonality (e.g., [7, 30, 365] for daily, monthly, yearly)

    Returns:
        Dictionary with seasonality metrics
    """
    if len(series) < 4:  # Need at least a few data points
        return {"has_seasonality": False}

    # If no periods specified, try to determine from the data
    if periods is None:
        # Infer frequency
        # Convert index to DatetimeIndex if necessary
        if isinstance(series.index, pd.DatetimeIndex):
            inferred_freq = pd.infer_freq(series.index)
        else:
            try:
                dt_index = pd.DatetimeIndex(series.index)
                inferred_freq = pd.infer_freq(dt_index)
            except Exception:
                inferred_freq = None

        if inferred_freq == "D":  # Daily data
            periods = [7, 30, 90, 365]  # Day of week, monthly, quarterly, yearly
        elif inferred_freq == "B":  # Business daily data
            periods = [5, 21, 63, 252]  # Week, month, quarter, year in business days
        elif inferred_freq == "M" or inferred_freq == "MS":  # Monthly data
            periods = [3, 6, 12]  # Quarterly, biannual, yearly
        else:
            # Default periods to check
            periods = [7, 30, 90, 365]

    results = {"has_seasonality": False}

    # Handle special case where data is constant
    # Convert to numpy array for np.std
    values_array = np.asarray(series.values)
    if np.std(values_array) == 0:
        return results

    # Test each period for seasonality
    for period in periods:
        if len(series) < period * 2:
            continue  # Not enough data for this period

        # Calculate autocorrelation at the specified lag
        acf = calculate_autocorrelation(series, period)

        # Calculate partial autocorrelation
        pacf = calculate_partial_autocorrelation(series, period)

        # Determine if there's significant seasonality
        # A high positive ACF at the seasonal lag indicates seasonality
        is_seasonal = acf > 0.3  # Arbitrary threshold

        # Create a nested dictionary for period results
        period_key = f"period_{period}"
        results[period_key] = {
            "autocorrelation": acf,
            "partial_autocorrelation": pacf,
            "is_seasonal": is_seasonal,
        }

        if is_seasonal:
            results["has_seasonality"] = True
            # Update strongest_period based on autocorrelation strength
            if (
                "strongest_period" not in results
                or not results.get("strongest_period")
                or (
                    period_key in results
                    and "strongest_period" in results
                    and acf
                    > results[f"period_{results['strongest_period']}"][
                        "autocorrelation"
                    ]
                )
            ):
                results["strongest_period"] = period

    return results


def calculate_autocorrelation(series: pd.Series, lag: int) -> float:
    """
    Calculate autocorrelation at a specific lag.

    Args:
        series: Time series data
        lag: Lag for autocorrelation

    Returns:
        Autocorrelation value
    """
    # Remove NaN values
    clean_series = series.dropna()

    if len(clean_series) <= lag:
        return 0.0

    # Calculate autocorrelation
    n = len(clean_series)
    data = clean_series.values

    # Convert data to float
    data = data.astype(float)

    # Calculate mean and variance
    mean = np.mean(data)
    var = np.var(data)

    if var == 0:
        return 0.0

    # Calculate autocorrelation
    acf = 0
    for i in range(n - lag):
        acf += (data[i] - mean) * (data[i + lag] - mean)

    acf /= (n - lag) * var

    return float(acf)


def calculate_partial_autocorrelation(series: pd.Series, lag: int) -> float:
    """
    Calculate partial autocorrelation at a specific lag.

    Args:
        series: Time series data
        lag: Lag for partial autocorrelation

    Returns:
        Partial autocorrelation value
    """
    try:
        from statsmodels.tsa.stattools import pacf

        # Remove NaN values
        clean_series = series.dropna()

        if len(clean_series) <= lag:
            return 0.0

        # Calculate partial autocorrelation
        pacf_values = pacf(clean_series.values, nlags=lag, method="ols")

        return pacf_values[-1]  # Return the PACF at the specified lag

    except ImportError:
        logger.warning("statsmodels not installed, using simplified PACF calculation")

        # Simplified PACF calculation through correlation adjustments
        if lag <= 1:
            return calculate_autocorrelation(series, lag)

        # For lag > 1, use recursive calculation (Durbin-Levinson)
        clean_series = series.dropna()

        if len(clean_series) <= lag:
            return 0.0

        # Base case
        phi = np.zeros(lag + 1)
        phi[1] = calculate_autocorrelation(clean_series, 1)

        # Recursion
        for k in range(2, lag + 1):
            # Calculate ACF at lag k
            r_k = calculate_autocorrelation(clean_series, k)

            # Calculate the numerator
            num = r_k
            for j in range(1, k):
                num -= phi[j] * calculate_autocorrelation(clean_series, k - j)

            # Calculate the denominator
            den = 1
            for j in range(1, k):
                den -= phi[j] * calculate_autocorrelation(clean_series, j)

            # Calculate new phi
            phi[k] = num / den if den != 0 else 0

            # Update previous phi values
            for j in range(1, k):
                phi[j] = phi[j] - phi[k] * phi[k - j]

        return phi[lag]


def perform_quality_check(
    variable_name: str,
    anomaly_method: str = "zscore",
    gap_min_size: int = 1,
    trend_window_size: int = 30,
    seasonality_periods: Optional[List[int]] = None,
    variable_type: str = "raw",
    _series: Optional[
        pd.Series
    ] = None,  # Add optional parameter to pass series directly
) -> QualityCheckResult:
    """
    Perform a comprehensive quality check on the data for a variable.

    Args:
        variable_name: Name of the variable to check
        anomaly_method: Method to use for anomaly detection
        gap_min_size: Minimum size of gaps to detect
        trend_window_size: Window size for trend break detection
        seasonality_periods: Periods to check for seasonality
        variable_type: Type of variable for range validation

    Returns:
        QualityCheckResult object with all quality metrics
    """
    try:
        # Load the data if not provided
        if _series is not None:
            series = _series
        else:
            series = load_processed_data(variable_name)

        # Initialize quality score
        quality_score = DataQualityScore(variable_name=variable_name)

        # Calculate basic statistics
        statistics = {
            "count": len(series),
            "min": series.min(),
            "max": series.max(),
            "mean": series.mean(),
            "median": series.median(),
            "std": series.std(),
            "start_date": series.index.min().isoformat(),
            "end_date": series.index.max().isoformat(),
            "date_range_days": (series.index.max() - series.index.min()).days,
        }

        # 1. Detect gaps
        gaps = detect_gaps(series, min_gap_size=gap_min_size)

        # Calculate completeness score
        if statistics["date_range_days"] > 0:
            total_gap_days = sum(gap.gap_duration.days for gap in gaps)
            completeness = 1.0 - (total_gap_days / statistics["date_range_days"])
            quality_score.completeness = max(0.0, min(1.0, completeness))
        else:
            quality_score.completeness = 1.0

        # 2. Detect anomalies
        anomalies = detect_anomalies(
            series, method=anomaly_method, variable_type=variable_type
        )

        # Calculate anomaly_free score
        if len(series) > 0:
            anomaly_free = 1.0 - (len(anomalies) / len(series))
            quality_score.anomaly_free = max(0.0, min(1.0, anomaly_free))
        else:
            quality_score.anomaly_free = 1.0

        # 3. Detect trend breaks
        trend_breaks = detect_trend_breaks(series, window_size=trend_window_size)

        # Calculate trend_stability score
        # A lower score if more trend breaks or high severity breaks are found
        if len(series) > trend_window_size * 2:
            max_expected_breaks = (
                len(series) / trend_window_size
            ) / 4  # Rough estimate of maximum expected breaks
            trend_break_count = len(trend_breaks)

            if max_expected_breaks > 0:
                trend_stability = 1.0 - min(
                    1.0, trend_break_count / max_expected_breaks
                )

                # Adjust for severity
                if trend_breaks:
                    avg_severity = sum(tb.severity for tb in trend_breaks) / len(
                        trend_breaks
                    )
                    trend_stability *= 1 - avg_severity * 0.5

                quality_score.trend_stability = max(0.0, min(1.0, trend_stability))
            else:
                quality_score.trend_stability = 1.0
        else:
            quality_score.trend_stability = (
                0.5  # Not enough data for reliable trend analysis
            )

        # 4. Detect seasonality
        seasonality_results = detect_seasonality(series, periods=seasonality_periods)

        # Calculate seasonality score
        # Higher score if seasonality is detected and consistent
        if seasonality_results["has_seasonality"]:
            strongest_period = seasonality_results.get("strongest_period")
            if strongest_period:
                # Higher autocorrelation means more consistent seasonality
                autocorr = seasonality_results[f"period_{strongest_period}"][
                    "autocorrelation"
                ]
                quality_score.seasonality = min(
                    1.0, autocorr * 2
                )  # Scale up, max at 1.0
            else:
                quality_score.seasonality = 0.5
        else:
            # No seasonality might be correct for the data, so use a neutral score
            quality_score.seasonality = 0.5

        # 5. Calculate consistency score
        # Check if values are within expected ranges and have consistent patterns

        # Get the expected range for this variable type
        expected_range = DEFAULT_VARIABLE_RANGES.get(
            variable_type, DEFAULT_VARIABLE_RANGES["raw"]
        )
        range_min, range_max = expected_range

        # Calculate what percentage of values are within the expected range
        if range_min != float("-inf") and range_max != float("inf"):
            in_range_count = ((series >= range_min) & (series <= range_max)).sum()
            consistency = in_range_count / len(series) if len(series) > 0 else 1.0
            quality_score.consistency = max(0.0, min(1.0, consistency))
        else:
            # If no specific range, use other metrics to estimate consistency

            # Calculate coefficient of variation
            cv = series.std() / series.mean() if series.mean() != 0 else float("inf")

            if np.isfinite(cv):
                # Lower CV indicates more consistent data
                # Scale so that CV=0 gives 1.0 and CV>=2 gives 0.0
                consistency = max(0.0, min(1.0, 1.0 - cv / 2))
            else:
                consistency = 0.5  # Default if can't calculate

            quality_score.consistency = consistency

        # 6. Calculate time continuity score
        # Based on the regularity of the time intervals

        if len(series) > 1:
            # Calculate intervals between timestamps
            intervals = series.index[1:] - series.index[:-1]
            # Convert interval index to appropriate type for calculating seconds
            interval_seconds = np.array(
                [
                    (
                        interval.total_seconds()
                        if hasattr(interval, "total_seconds")
                        else pd.Timedelta(interval).total_seconds()
                    )
                    for interval in intervals
                ]
            )

            # Check if intervals are consistent
            if len(interval_seconds) > 0:
                mean_interval = np.mean(interval_seconds)
                std_interval = np.std(interval_seconds)

                if mean_interval > 0:
                    # Calculate coefficient of variation of intervals
                    cv_interval = std_interval / mean_interval

                    # Lower CV indicates more consistent intervals
                    time_continuity = max(0.0, min(1.0, float(1.0 - cv_interval / 2)))
                else:
                    time_continuity = 0.0
            else:
                time_continuity = 1.0  # Only one data point
        else:
            time_continuity = 0.0  # Not enough data

        quality_score.time_continuity = time_continuity

        # Generate recommendations based on issues found
        recommendations = []

        if quality_score.completeness < 0.9:
            recommendations.append(
                f"Data has significant gaps ({(1 - quality_score.completeness) * 100:.1f}% missing). Consider using interpolation methods to fill gaps."
            )

        if quality_score.anomaly_free < 0.95:
            recommendations.append(
                f"Data contains {len(anomalies)} potential anomalies. Review and consider whether they are valid data points or errors."
            )

        if quality_score.consistency < 0.9:
            recommendations.append(
                "Data shows inconsistent value ranges. Validate that all values are in expected units and ranges."
            )

        if quality_score.time_continuity < 0.9:
            recommendations.append(
                "Data has irregular time intervals. Consider resampling to a consistent frequency."
            )

        if quality_score.trend_stability < 0.7:
            recommendations.append(
                f"Data shows {len(trend_breaks)} significant trend breaks. These might indicate structural changes or data quality issues."
            )

        if quality_score.overall_score < 0.7:
            recommendations.append(
                "Overall data quality is low. Consider acquiring higher quality data or applying extensive preprocessing."
            )

        # Create and return the quality check result
        return QualityCheckResult(
            variable_name=variable_name,
            quality_score=quality_score,
            anomalies=anomalies,
            gaps=gaps,
            trend_breaks=trend_breaks,
            statistics=statistics,
            recommendations=recommendations,
        )

    except FileNotFoundError:
        # Handle the case where data is not available
        logger.error(f"No data found for variable {variable_name}")

        # Return an empty result with error indication
        quality_score = DataQualityScore(variable_name=variable_name)

        return QualityCheckResult(
            variable_name=variable_name,
            quality_score=quality_score,
            statistics={"error": f"No data found for variable {variable_name}"},
            recommendations=[
                "Ensure the variable exists and data has been retrieved and processed."
            ],
        )
    except Exception as e:
        logger.error(f"Error performing quality check for {variable_name}: {e}")

        # Return an error result
        quality_score = DataQualityScore(variable_name=variable_name)

        return QualityCheckResult(
            variable_name=variable_name,
            quality_score=quality_score,
            statistics={"error": f"Error during quality check: {str(e)}"},
            recommendations=[
                "Review the error and ensure the data is in the expected format."
            ],
        )


def cross_validate_sources(variable_name: str) -> CrossValidationResult:
    """
    Compare data for the same variable from different sources.

    Args:
        variable_name: Name of the variable to validate

    Returns:
        CrossValidationResult object with comparison metrics
    """
    try:
        # Load data from all available sources
        source_data = load_multi_source_data(variable_name)

        if len(source_data) < 2:
            raise ValueError(
                f"Not enough sources available for cross-validation. Found {len(source_data)} sources."
            )

        sources = list(source_data.keys())

        # Create empty matrices for correlations and differences
        correlation_matrix = {
            source: {other_source: 0.0 for other_source in sources}
            for source in sources
        }
        mean_diff_matrix = {
            source: {other_source: 0.0 for other_source in sources}
            for source in sources
        }
        stddev_diff_matrix = {
            source: {other_source: 0.0 for other_source in sources}
            for source in sources
        }
        max_diff_matrix = {
            source: {other_source: 0.0 for other_source in sources}
            for source in sources
        }

        # Align all series to a common date range
        aligned_data = {}
        all_dates = set()

        # Collect all dates from all series
        for source, series in source_data.items():
            all_dates.update(series.index)

        # Create a union of all dates
        common_index = pd.DatetimeIndex(sorted(all_dates))

        # Reindex all series to the common date range, filling NaN values
        for source, series in source_data.items():
            aligned_series = series.reindex(common_index)
            aligned_data[source] = aligned_series

        # Calculate comparison metrics for each pair of sources
        for i, source1 in enumerate(sources):
            for j, source2 in enumerate(sources):
                if i >= j:  # Skip duplicate comparisons
                    continue

                series1 = aligned_data[source1]
                series2 = aligned_data[source2]

                # Drop dates where either series has NaN
                common_data = pd.DataFrame(
                    {source1: series1, source2: series2}
                ).dropna()

                if len(common_data) > 1:
                    # Calculate correlation
                    correlation = common_data[source1].corr(common_data[source2])
                    correlation_matrix[source1][source2] = correlation
                    correlation_matrix[source2][source1] = correlation

                    # Calculate differences
                    diffs = common_data[source1] - common_data[source2]
                    mean_diff = diffs.mean()
                    stddev_diff = diffs.std()
                    max_diff = diffs.abs().max()

                    mean_diff_matrix[source1][source2] = mean_diff
                    mean_diff_matrix[source2][source1] = -mean_diff

                    stddev_diff_matrix[source1][source2] = stddev_diff
                    stddev_diff_matrix[source2][source1] = stddev_diff

                    max_diff_matrix[source1][source2] = max_diff
                    max_diff_matrix[source2][source1] = max_diff
                else:
                    logger.warning(
                        f"No overlapping dates for sources {source1} and {source2}"
                    )

        # Determine the most reliable source based on correlations and differences
        avg_correlations = {source: 0.0 for source in sources}
        for source in sources:
            total_corr = 0.0
            count = 0
            for other_source in sources:
                if (
                    source != other_source
                    and correlation_matrix[source][other_source] != 0.0
                ):
                    total_corr += correlation_matrix[source][other_source]
                    count += 1

            avg_correlations[source] = total_corr / count if count > 0 else 0.0

        # Find source with highest average correlation
        best_source = max(avg_correlations.items(), key=lambda x: x[1])

        # Generate recommendation
        if best_source[1] > 0.9:
            recommendation = f"Source '{best_source[0]}' shows high correlation with other sources (avg: {best_source[1]:.2f}). It is recommended as the primary source for this variable."
        elif best_source[1] > 0.7:
            recommendation = f"Source '{best_source[0]}' shows good correlation with other sources (avg: {best_source[1]:.2f}). Consider using this source but validate with other sources when possible."
        else:
            recommendation = f"All sources show low correlation with each other (best: {best_source[0]}, avg: {best_source[1]:.2f}). Data should be used with caution and additional validation is recommended."

        return CrossValidationResult(
            variable_name=variable_name,
            sources=sources,
            correlation_matrix=correlation_matrix,
            mean_differences=mean_diff_matrix,
            stddev_differences=stddev_diff_matrix,
            max_differences=max_diff_matrix,
            aligned_datasets=aligned_data,
            recommendation=recommendation,
        )

    except ValueError as e:
        logger.error(f"Error in cross-validation for {variable_name}: {e}")

        # Return a result indicating the error
        return CrossValidationResult(
            variable_name=variable_name,
            sources=[],
            correlation_matrix={},
            mean_differences={},
            stddev_differences={},
            max_differences={},
            aligned_datasets={},
            recommendation=f"Error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error in cross-validation for {variable_name}: {e}")

        # Return a result indicating the error
        return CrossValidationResult(
            variable_name=variable_name,
            sources=[],
            correlation_matrix={},
            mean_differences={},
            stddev_differences={},
            max_differences={},
            aligned_datasets={},
            recommendation=f"Unexpected error: {str(e)}",
        )


def analyze_gaps(
    variable_name: str, freq: str = "auto", min_gap_size: int = 1
) -> Dict[str, Any]:
    """
    Analyze gaps in the time series data for a variable.

    Args:
        variable_name: Name of the variable to analyze
        freq: Expected frequency of the data
        min_gap_size: Minimum number of missing points to consider a gap

    Returns:
        Dictionary with gap analysis results
    """
    try:
        # Load the data
        series = load_processed_data(variable_name)

        # Detect gaps
        gaps = detect_gaps(series, freq=freq, min_gap_size=min_gap_size)

        # Calculate gap statistics
        total_gap_days = sum(gap.gap_duration.days for gap in gaps)

        date_range_days = (
            (series.index.max() - series.index.min()).days if len(series) > 1 else 0
        )
        completeness = (
            1.0 - (total_gap_days / date_range_days) if date_range_days > 0 else 1.0
        )

        # Analyze gap patterns
        gap_lengths = [gap.gap_duration.days for gap in gaps]

        # Create summary statistics for gaps
        if gaps:
            avg_gap_length = sum(gap_lengths) / len(gaps)
            max_gap_length = max(gap_lengths)
            min_gap_length = min(gap_lengths)

            # Find the most common gap length (mode)
            from collections import Counter

            length_counts = Counter(gap_lengths)
            most_common_length = length_counts.most_common(1)[0][0]

            # Check for any patterns in gap timing
            weekday_gaps = 0
            weekend_gaps = 0
            month_end_gaps = 0

            for gap in gaps:
                if gap.start_time.weekday() < 5:  # Monday to Friday
                    weekday_gaps += 1
                else:
                    weekend_gaps += 1

                # Check if gap starts at month end
                if (
                    gap.start_time.day
                    == (gap.start_time.replace(day=28) + dt.timedelta(days=4))
                    .replace(day=1)
                    .day
                    - 1
                ):
                    month_end_gaps += 1

            gap_patterns = {
                "weekday_gaps": weekday_gaps,
                "weekend_gaps": weekend_gaps,
                "month_end_gaps": month_end_gaps,
                "possible_pattern": "weekend"
                if weekend_gaps > weekday_gaps * 2
                else "month_end"
                if month_end_gaps > len(gaps) * 0.4
                else "random",
            }

            # Generate recommendations based on gap analysis
            if completeness < 0.8:
                severity = "severe"
            elif completeness < 0.9:
                severity = "moderate"
            elif completeness < 0.95:
                severity = "minor"
            else:
                severity = "negligible"

            recommendation = (
                f"Data completeness is {completeness:.2%} ({severity} gaps). "
            )

            if gap_patterns["possible_pattern"] == "weekend":
                recommendation += "Gaps appear to be concentrated on weekends. Consider using a business day frequency for analysis."
            elif gap_patterns["possible_pattern"] == "month_end":
                recommendation += "Gaps appear to be concentrated at month ends. This may indicate reporting delays."
            else:
                recommendation += f"Gaps appear to be randomly distributed. Consider interpolation methods to fill gaps (average length: {avg_gap_length:.1f} days)."
        else:
            avg_gap_length = 0
            max_gap_length = 0
            min_gap_length = 0
            most_common_length = 0
            gap_patterns = {
                "weekday_gaps": 0,
                "weekend_gaps": 0,
                "month_end_gaps": 0,
                "possible_pattern": "none",
            }
            recommendation = "No significant gaps detected in the data."

        # Prepare the results
        results = {
            "variable_name": variable_name,
            "total_gaps": len(gaps),
            "total_gap_days": total_gap_days,
            "data_range_days": date_range_days,
            "completeness": completeness,
            "gaps": [gap.to_dict() for gap in gaps],
            "gap_statistics": {
                "average_length": avg_gap_length,
                "max_length": max_gap_length,
                "min_length": min_gap_length,
                "most_common_length": most_common_length,
            },
            "gap_patterns": gap_patterns,
            "recommendation": recommendation,
        }

        return results

    except FileNotFoundError:
        logger.error(f"No data found for variable {variable_name}")

        return {
            "variable_name": variable_name,
            "error": f"No data found for variable {variable_name}",
            "recommendation": "Ensure the variable exists and data has been retrieved and processed.",
        }
    except ValueError as e:
        logger.error(f"Invalid frequency parameter for {variable_name}: {e}")

        return {
            "variable_name": variable_name,
            "error": f"Invalid frequency parameter: {str(e)}",
            "recommendation": "Try a different frequency value (D, B, W, M) or adjust the data.",
        }
    except Exception as e:
        logger.error(f"Error analyzing gaps for {variable_name}: {e}")

        return {
            "variable_name": variable_name,
            "error": f"Error during gap analysis: {str(e)}",
            "recommendation": "Review the error and ensure the data is in the expected format.",
        }


def generate_quality_report(
    variable_names: Optional[List[str]] = None, priority: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive quality report for multiple variables.

    Args:
        variable_names: List of variable names to include in the report
        priority: Priority level to filter variables by

    Returns:
        Dictionary with the quality report
    """
    # Determine which variables to include
    if variable_names is None:
        if priority is not None:
            # Get variables with the specified priority
            priority_vars = get_priority_variables(priority)
            variable_names = [var["variable_name"] for var in priority_vars]
        else:
            # Get all variables from the catalog
            catalog = load_variable_catalog()
            variable_names = [var["variable_name"] for var in catalog["variables"]]

    results = []
    overall_scores = []
    completeness_scores = []
    consistency_scores = []
    anomaly_free_scores = []
    variables_with_gaps = 0
    variables_with_anomalies = 0
    variables_with_trend_breaks = 0

    # Perform quality check for each variable
    for var_name in variable_names:
        try:
            logger.info(f"Generating quality report for {var_name}")
            result = perform_quality_check(var_name)

            results.append(result.to_dict())

            # Collect metrics for overall statistics
            overall_scores.append(result.quality_score.overall_score)
            completeness_scores.append(result.quality_score.completeness)
            consistency_scores.append(result.quality_score.consistency)
            anomaly_free_scores.append(result.quality_score.anomaly_free)

            if result.gaps:
                variables_with_gaps += 1

            if result.anomalies:
                variables_with_anomalies += 1

            if result.trend_breaks:
                variables_with_trend_breaks += 1

        except Exception as e:
            logger.error(f"Error generating quality report for {var_name}: {e}")

            # Add an error entry
            results.append({"variable_name": var_name, "error": str(e)})

    # Calculate overall statistics
    if overall_scores:
        avg_overall_score = sum(overall_scores) / len(overall_scores)
        avg_completeness = sum(completeness_scores) / len(completeness_scores)
        avg_consistency = sum(consistency_scores) / len(consistency_scores)
        avg_anomaly_free = sum(anomaly_free_scores) / len(anomaly_free_scores)

        # Count variables in different quality levels
        excellent_quality = sum(1 for score in overall_scores if score >= 0.9)
        good_quality = sum(1 for score in overall_scores if 0.8 <= score < 0.9)
        fair_quality = sum(1 for score in overall_scores if 0.7 <= score < 0.8)
        poor_quality = sum(1 for score in overall_scores if score < 0.7)

        # Generate overall recommendations
        recommendations = []

        if variables_with_gaps > 0:
            recommendations.append(
                f"{variables_with_gaps} variables have gaps. Consider using imputation methods to fill these gaps."
            )

        if variables_with_anomalies > 0:
            recommendations.append(
                f"{variables_with_anomalies} variables have potential anomalies. Review and address these for improved data quality."
            )

        if variables_with_trend_breaks > 0:
            recommendations.append(
                f"{variables_with_trend_breaks} variables have significant trend breaks. This might indicate structural changes or data issues."
            )

        if poor_quality > 0:
            recommendations.append(
                f"{poor_quality} variables have poor quality scores (<0.7). Prioritize these for data quality improvement."
            )

        # Create the final report
        report = {
            "timestamp": dt.datetime.now().isoformat(),
            "variables_analyzed": len(variable_names),
            "successful_analyses": len(overall_scores),
            "failed_analyses": len(variable_names) - len(overall_scores),
            "overall_statistics": {
                "average_overall_score": avg_overall_score,
                "average_completeness": avg_completeness,
                "average_consistency": avg_consistency,
                "average_anomaly_free": avg_anomaly_free,
                "variables_with_gaps": variables_with_gaps,
                "variables_with_anomalies": variables_with_anomalies,
                "variables_with_trend_breaks": variables_with_trend_breaks,
                "quality_distribution": {
                    "excellent": excellent_quality,
                    "good": good_quality,
                    "fair": fair_quality,
                    "poor": poor_quality,
                },
            },
            "overall_recommendations": recommendations,
            "variable_results": results,
        }
    else:
        # No successful analyses
        report = {
            "timestamp": dt.datetime.now().isoformat(),
            "variables_analyzed": len(variable_names),
            "successful_analyses": 0,
            "failed_analyses": len(variable_names),
            "error": "No successful quality analyses were completed.",
            "variable_results": results,
        }

    # Save the report to a file
    report_dir = Path(HISTORICAL_DATA_BASE_DIR) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    report_file = report_dir / f"quality_report_{timestamp}.json"

    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved quality report to {report_file}")

    return report


def visualize_data_quality(
    variable_name: str,
    output_dir: Optional[str] = None,
    show_anomalies: bool = True,
    show_gaps: bool = True,
    show_trend_breaks: bool = True,
    save_format: str = "png",
) -> Dict[str, str]:
    """
    Generate visualizations of data quality for a variable.

    Args:
        variable_name: Name of the variable to visualize
        output_dir: Directory to save visualizations to
        show_anomalies: Whether to highlight anomalies in the visualization
        show_gaps: Whether to highlight gaps in the visualization
        show_trend_breaks: Whether to highlight trend breaks in the visualization
        save_format: Format to save visualizations in (png, pdf, svg)

    Returns:
        Dictionary mapping visualization types to their file paths
    """
    try:
        # Load the data
        series = load_processed_data(variable_name)

        # Create output directory if specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            # Default output directory
            output_path = (
                Path(HISTORICAL_DATA_BASE_DIR) / "visualizations" / variable_name
            )
            output_path.mkdir(parents=True, exist_ok=True)

        # Perform quality check (this includes detecting anomalies, gaps, and trend breaks)
        quality_result = perform_quality_check(variable_name)

        # Track generated visualizations
        visualization_paths = {}

        # 1. Time series plot with anomalies, gaps, and trend breaks
        plt.figure(figsize=(12, 6))

        # Plot the raw data
        # Convert to numpy arrays for matplotlib
        dates = pd.to_datetime(series.index)
        values = np.asarray(series.values)
        plt.plot(dates, values, "b-", label=variable_name)

        # Mark anomalies if requested
        if show_anomalies and quality_result.anomalies:
            anomaly_dates = [a.timestamp for a in quality_result.anomalies]
            anomaly_values = [a.value for a in quality_result.anomalies]

            # Convert datetime objects to matplotlib dates
            import matplotlib.dates as mdates

            anomaly_dates_num = mdates.date2num(anomaly_dates)
            plt.scatter(
                anomaly_dates_num, anomaly_values, color="r", s=50, label="Anomalies"
            )

        # Mark trend breaks if requested
        if show_trend_breaks and quality_result.trend_breaks:
            trend_break_dates = [tb.timestamp for tb in quality_result.trend_breaks]
            trend_break_values = [
                series.loc[tb.timestamp] if tb.timestamp in series.index else None
                for tb in quality_result.trend_breaks
            ]
            # Filter out None values
            valid_dates = []
            valid_values = []
            for date, value in zip(trend_break_dates, trend_break_values):
                if value is not None:
                    valid_dates.append(date)
                    valid_values.append(value)

            if valid_dates:
                plt.scatter(
                    valid_dates,
                    valid_values,
                    color="g",
                    s=80,
                    marker="^",
                    label="Trend Breaks",
                )

                # Add vertical lines at trend breaks
                for date in valid_dates:
                    plt.axvline(x=date, color="g", linestyle="--", alpha=0.3)

        # Mark gaps if requested
        if show_gaps and quality_result.gaps:
            for gap in quality_result.gaps:
                # Convert datetimes to matplotlib date format
                # Convert datetimes to matplotlib dates for axvspan
                import matplotlib.dates as mdates

                start = mdates.date2num(gap.start_time)
                end = mdates.date2num(gap.end_time)
                plt.axvspan(start, end, color="y", alpha=0.3)

            # Add a custom patch for the legend
            import matplotlib.patches as mpatches

            gap_patch = mpatches.Patch(color="y", alpha=0.3, label="Gaps")
            handles, labels = plt.gca().get_legend_handles_labels()
            handles.append(gap_patch)
            plt.legend(handles=handles)
        else:
            plt.legend()

        plt.title(f"Time Series Quality Analysis: {variable_name}")
        plt.xlabel("Date")
        plt.ylabel("Value")
        plt.grid(True)

        # Add a text box with quality scores
        quality_text = (
            f"Overall Quality: {quality_result.quality_score.overall_score:.2f}\n"
            f"Completeness: {quality_result.quality_score.completeness:.2f}\n"
            f"Consistency: {quality_result.quality_score.consistency:.2f}\n"
            f"Anomaly-Free: {quality_result.quality_score.anomaly_free:.2f}\n"
            f"Time Continuity: {quality_result.quality_score.time_continuity:.2f}\n"
            f"Trend Stability: {quality_result.quality_score.trend_stability:.2f}\n"
            f"Seasonality: {quality_result.quality_score.seasonality:.2f}"
        )

        plt.figtext(
            0.02,
            0.02,
            quality_text,
            fontsize=9,
            bbox={"facecolor": "white", "alpha": 0.8, "pad": 5},
        )

        # Save the plot
        time_series_path = (
            output_path / f"{variable_name}_time_series_quality.{save_format}"
        )
        plt.savefig(time_series_path)
        plt.close()

        visualization_paths["time_series"] = str(time_series_path)

        # 2. Quality score radar chart
        try:
            plt.figure(figsize=(8, 8))

            # Categories for the radar chart
            categories = [
                "Completeness",
                "Consistency",
                "Anomaly-Free",
                "Time Continuity",
                "Trend Stability",
                "Seasonality",
            ]

            # Values for the radar chart
            values = [
                quality_result.quality_score.completeness,
                quality_result.quality_score.consistency,
                quality_result.quality_score.anomaly_free,
                quality_result.quality_score.time_continuity,
                quality_result.quality_score.trend_stability,
                quality_result.quality_score.seasonality,
            ]

            # Number of categories
            N = len(categories)

            # Create angles for each category
            angles = [n / float(N) * 2 * np.pi for n in range(N)]
            angles += angles[:1]  # Close the loop

            # Add the values for the last point to close the loop
            values += values[:1]

            # Create the plot
            ax = plt.subplot(111, polar=True)

            # Draw the chart
            ax.plot(angles, values, "o-", linewidth=2)
            ax.fill(angles, values, alpha=0.25)

            # Set the labels
            # For polar coordinates in matplotlib
            plt.xticks(angles[:-1], categories)

            # Set y-limits
            ax.set_ylim(0, 1)

            # Add grid lines and labels
            # Set y-ticks for radar chart (works in all matplotlib versions)
            plt.yticks(
                [0.2, 0.4, 0.6, 0.8], ["0.2", "0.4", "0.6", "0.8"], color="grey", size=8
            )
            plt.yticks(
                [0.2, 0.4, 0.6, 0.8], ["0.2", "0.4", "0.6", "0.8"], color="grey", size=8
            )
            plt.ylim(0, 1)

            plt.title(f"Quality Score Dimensions: {variable_name}")

            # Add overall score
            plt.figtext(
                0.5,
                0.02,
                f"Overall Quality Score: {quality_result.quality_score.overall_score:.2f}",
                ha="center",
                fontsize=12,
                bbox={"facecolor": "white", "alpha": 0.8, "pad": 5},
            )

            # Save the plot
            radar_path = output_path / f"{variable_name}_quality_radar.{save_format}"
            plt.savefig(radar_path)
            plt.close()

            visualization_paths["radar_chart"] = str(radar_path)

        except Exception as e:
            logger.error(f"Error creating radar chart: {e}")

        # 3. Data Completeness Calendar Heatmap (if matplotlib-extras available)
        try:
            # This is a placeholder - in a real implementation, we might use
            # calmap, seaborn, or another library for calendar heatmaps.
            # For now, we'll create a simple visualization of data completeness.

            plt.figure(figsize=(12, 6))

            # Create a daily indicator of data presence (1) or absence (0)
            date_range = pd.date_range(
                start=series.index.min(), end=series.index.max(), freq="D"
            )

            # Create a Series with 0s for all dates in the range
            completeness = pd.Series(0, index=date_range)

            # Mark dates with data as 1
            for idx in series.index:
                if idx in completeness.index:
                    completeness[idx] = 1

            # Plot the data completeness
            # Convert to numpy arrays for matplotlib
            dates = pd.to_datetime(completeness.index)
            values = np.asarray(completeness.values)
            plt.bar(dates, values, width=1, color="blue", alpha=0.7)

            plt.title(f"Data Completeness: {variable_name}")
            plt.xlabel("Date")
            plt.ylabel("Data Present (1) or Absent (0)")

            # Add completeness percentage
            complete_pct = completeness.mean() * 100
            plt.figtext(
                0.5,
                0.02,
                f"Overall Completeness: {complete_pct:.1f}%",
                ha="center",
                fontsize=12,
                bbox={"facecolor": "white", "alpha": 0.8, "pad": 5},
            )

            # Save the plot
            completeness_path = (
                output_path / f"{variable_name}_completeness.{save_format}"
            )
            plt.savefig(completeness_path)
            plt.close()

            visualization_paths["completeness"] = str(completeness_path)

        except Exception as e:
            logger.error(f"Error creating completeness visualization: {e}")

        # 4. If multiple sources are available, create a cross-source comparison chart
        try:
            source_data = load_multi_source_data(variable_name)

            if len(source_data) > 1:
                plt.figure(figsize=(12, 6))

                # Plot data from each source
                for source, data in source_data.items():
                    # Convert to numpy arrays for matplotlib
                    dates = pd.to_datetime(data.index)
                    values = np.asarray(data.values)
                    plt.plot(dates, values, label=source)

                plt.title(f"Cross-Source Comparison: {variable_name}")
                plt.xlabel("Date")
                plt.ylabel("Value")
                plt.legend()
                plt.grid(True)

                # Save the plot
                comparison_path = (
                    output_path / f"{variable_name}_cross_source.{save_format}"
                )
                plt.savefig(comparison_path)
                plt.close()

                visualization_paths["cross_source"] = str(comparison_path)

                # Also create a scatter plot comparing sources
                if len(source_data) == 2:
                    sources = list(source_data.keys())

                    # Create a DataFrame with aligned data
                    combined = pd.DataFrame(
                        {
                            sources[0]: source_data[sources[0]],
                            sources[1]: source_data[sources[1]],
                        }
                    )

                    # Drop rows with missing values
                    combined = combined.dropna()

                    if len(combined) > 0:
                        plt.figure(figsize=(8, 8))

                        plt.scatter(
                            combined[sources[0]], combined[sources[1]], alpha=0.7
                        )

                        # Draw a perfect correlation line
                        min_val = min(
                            combined[sources[0]].min(), combined[sources[1]].min()
                        )
                        max_val = max(
                            combined[sources[0]].max(), combined[sources[1]].max()
                        )
                        plt.plot([min_val, max_val], [min_val, max_val], "r--")

                        plt.title(f"Source Correlation: {variable_name}")
                        plt.xlabel(sources[0])
                        plt.ylabel(sources[1])
                        plt.grid(True)

                        # Add correlation coefficient
                        corr = combined[sources[0]].corr(combined[sources[1]])
                        plt.figtext(
                            0.5,
                            0.02,
                            f"Correlation: {corr:.3f}",
                            ha="center",
                            fontsize=12,
                            bbox={"facecolor": "white", "alpha": 0.8, "pad": 5},
                        )

                        # Save the plot
                        correlation_path = (
                            output_path
                            / f"{variable_name}_source_correlation.{save_format}"
                        )
                        plt.savefig(correlation_path)
                        plt.close()

                        visualization_paths["source_correlation"] = str(
                            correlation_path
                        )
        except Exception as e:
            logger.error(f"Error creating cross-source visualizations: {e}")

        return visualization_paths

    except FileNotFoundError:
        logger.error(f"No data found for variable {variable_name}")
        return {"error": f"No data found for variable {variable_name}"}
    except Exception as e:
        logger.error(f"Error visualizing data quality for {variable_name}: {e}")
        return {"error": f"Error during visualization: {str(e)}"}


if __name__ == "__main__":
    # Simple CLI for testing
    import argparse

    parser = argparse.ArgumentParser(
        description="Test the historical data verification module"
    )
    parser.add_argument(
        "--variable", type=str, required=True, help="Variable name to verify"
    )
    parser.add_argument(
        "--action",
        type=str,
        choices=["quality", "anomalies", "gaps", "cross", "visualize"],
        default="quality",
        help="Action to perform",
    )

    args = parser.parse_args()

    if args.action == "quality":
        result = perform_quality_check(args.variable)
        print(json.dumps(result.to_dict(), indent=2))
    elif args.action == "anomalies":
        series = load_processed_data(args.variable)
        anomalies = detect_anomalies(series)
        print(json.dumps([a.to_dict() for a in anomalies], indent=2))
    elif args.action == "gaps":
        result = analyze_gaps(args.variable)
        print(json.dumps(result, indent=2))
    elif args.action == "cross":
        result = cross_validate_sources(args.variable)
        print(json.dumps(result.to_dict(), indent=2))
    elif args.action == "visualize":
        paths = visualize_data_quality(args.variable)
        print(json.dumps(paths, indent=2))
