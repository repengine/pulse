"""iris.iris_utils.historical_data_repair
============================================

A module for repairing data quality issues in historical time series data.

This module provides multiple strategies for handling missing data, correcting
anomalies, reconciling data from different sources, and smoothing noisy data:

1. Missing data imputation strategies:
   - Forward fill and backward fill (for categorical or slowly changing data)
   - Linear interpolation (for data with linear trends)
   - Polynomial interpolation (for data with non-linear patterns)
   - Moving average imputation (for noisy data)
   - ARIMA-based imputation (for data with strong seasonal patterns)

2. Inconsistency resolution strategies:
   - Anomaly correction (for outliers and data entry errors)
   - Cross-source reconciliation (for combining data from multiple sources)
   - Smoothing methods for noisy data (rolling mean, exponential smoothing)
   - Seasonality-aware correction (for preserving seasonal patterns)

The module selects appropriate strategies based on variable characteristics,
gap size, data context, and quality assessments from historical_data_verification.

Usage:
------
```python
from iris.iris_utils.historical_data_repair import (
    repair_variable_data,
    simulate_repair,
    get_repair_report,
    repair_multiple_variables,
    revert_to_original,
    compare_versions,
    get_all_versions
)

# Repair data for a specific variable
result = repair_variable_data("spx_close")

# Simulate repairs without applying them
simulation = simulate_repair("unemployment_rate")

# Get a report of all repairs made
report = get_repair_report("gdp_quarterly")

# Compare original and repaired versions
comparison = compare_versions("inflation_rate", "original", "v20230515")
```

The module also provides a command-line interface through cli_historical_data.py.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import signal

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.nonparametric.smoothers_lowess import lowess
except ImportError:
    # statsmodels is an optional dependency
    ARIMA = None
    SARIMAX = None
    lowess = None
    import warnings

    warnings.warn(
        "statsmodels not installed. ARIMA and LOESS strategies will not be available."
    )


from iris.iris_utils.historical_data_verification import (
    load_processed_data,
    load_multi_source_data,
    detect_anomalies,
    detect_gaps,
    perform_quality_check,
    cross_validate_sources,
    detect_seasonality,
    TimeSeriesGap,
    Anomaly,
    QualityCheckResult,
    CrossValidationResult,
    HISTORICAL_DATA_BASE_DIR,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
REPAIR_VERSION_DIR = "repair_versions"

# Variable type to default repair strategy mapping
DEFAULT_REPAIR_STRATEGIES = {
    "raw": {
        "gap_strategy": "linear",
        "anomaly_strategy": "moving_average",
        "smoothing_strategy": "none",
        "cross_source_strategy": "weighted_average",
    },
    "price": {
        "gap_strategy": "linear",
        "anomaly_strategy": "median_filter",
        "smoothing_strategy": "exponential",
        "cross_source_strategy": "prioritized",
    },
    "percentage": {
        "gap_strategy": "linear_bounded",
        "anomaly_strategy": "bounded_correction",
        "smoothing_strategy": "none",
        "cross_source_strategy": "prioritized",
    },
    "rate": {
        "gap_strategy": "linear_bounded",
        "anomaly_strategy": "bounded_correction",
        "smoothing_strategy": "none",
        "cross_source_strategy": "prioritized",
    },
    "index": {
        "gap_strategy": "linear",
        "anomaly_strategy": "moving_average",
        "smoothing_strategy": "exponential",
        "cross_source_strategy": "weighted_average",
    },
    "count": {
        "gap_strategy": "interpolate_round",
        "anomaly_strategy": "moving_average_round",
        "smoothing_strategy": "none",
        "cross_source_strategy": "prioritized",
    },
    "temperature": {
        "gap_strategy": "seasonal_interpolation",
        "anomaly_strategy": "moving_average",
        "smoothing_strategy": "loess",
        "cross_source_strategy": "weighted_average",
    },
}

# Strategy selection thresholds
STRATEGY_THRESHOLDS = {
    "small_gap": 3,  # days
    "medium_gap": 14,  # days
    "large_gap": 30,  # days
    "very_large_gap": 90,  # days
    "high_correlation": 0.9,  # cross-source correlation threshold
    "medium_correlation": 0.7,  # cross-source correlation threshold
    "anomaly_severity": 0.7,  # threshold for severe anomalies
    "strong_seasonality": 0.8,  # autocorrelation threshold for strong seasonality
}


class RepairActionType(Enum):
    """Types of repair actions."""

    GAP_FILL = "gap_fill"
    ANOMALY_CORRECTION = "anomaly_correction"
    SMOOTHING = "smoothing"
    CROSS_SOURCE = "cross_source_reconciliation"
    OTHER = "other"


class RepairStrategy(Enum):
    """Available repair strategies."""

    # Gap filling strategies
    FORWARD_FILL = "forward_fill"
    BACKWARD_FILL = "backward_fill"
    LINEAR = "linear"
    LINEAR_BOUNDED = "linear_bounded"
    POLYNOMIAL = "polynomial"
    SPLINE = "spline"
    MOVING_AVERAGE = "moving_average"
    SEASONAL_INTERPOLATION = "seasonal_interpolation"
    ARIMA = "arima"
    INTERPOLATE_ROUND = "interpolate_round"

    # Anomaly correction strategies
    MEDIAN_FILTER = "median_filter"
    WINSORIZE = "winsorize"
    MOVING_AVERAGE_CORRECTION = "moving_average_correction"
    BOUNDED_CORRECTION = "bounded_correction"
    MOVING_AVERAGE_ROUND = "moving_average_round"

    # Smoothing strategies
    ROLLING_MEAN = "rolling_mean"
    EXPONENTIAL = "exponential"
    SAVITZKY_GOLAY = "savitzky_golay"
    LOESS = "loess"
    NONE = "none"

    # Cross-source reconciliation strategies
    PRIORITIZED = "prioritized"
    WEIGHTED_AVERAGE = "weighted_average"
    VOTING = "voting"


@dataclass
class RepairAction:
    """Record of a single repair action."""

    action_id: str
    variable_name: str
    action_type: RepairActionType
    strategy: RepairStrategy
    timestamp: dt.datetime
    original_value: Optional[float] = None
    new_value: Optional[float] = None
    start_time: Optional[dt.datetime] = None
    end_time: Optional[dt.datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the repair action to a dictionary."""
        result = {
            "action_id": self.action_id,
            "variable_name": self.variable_name,
            "action_type": self.action_type.value,
            "strategy": self.strategy.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

        if self.original_value is not None:
            result["original_value"] = self.original_value

        if self.new_value is not None:
            result["new_value"] = self.new_value

        if self.start_time:
            result["start_time"] = self.start_time.isoformat()

        if self.end_time:
            result["end_time"] = self.end_time.isoformat()

        if self.context:
            result["context"] = self.context

        return result


@dataclass
class RepairResult:
    """Result of a data repair operation."""

    variable_name: str
    status: str  # success, no_repairs_needed, or error
    version_id: str = ""
    timestamp: dt.datetime = field(default_factory=dt.datetime.now)
    total_repairs: int = 0
    gap_fills: int = 0
    anomaly_corrections: int = 0
    smoothing_actions: int = 0
    cross_source_actions: int = 0
    quality_improvement: float = 0.0
    before_quality: float = 0.0
    after_quality: float = 0.0
    actions: List[RepairAction] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the repair result to a dictionary."""
        return {
            "variable_name": self.variable_name,
            "status": self.status,
            "version_id": self.version_id,
            "timestamp": self.timestamp.isoformat(),
            "total_repairs": self.total_repairs,
            "gap_fills": self.gap_fills,
            "anomaly_corrections": self.anomaly_corrections,
            "smoothing_actions": self.smoothing_actions,
            "cross_source_actions": self.cross_source_actions,
            "quality_improvement": self.quality_improvement,
            "before_quality": self.before_quality,
            "after_quality": self.after_quality,
            "actions": [action.to_dict() for action in self.actions],
            "error": self.error,
        }


class AbstractRepairStrategy(ABC):
    """Abstract base class for repair strategies."""

    @abstractmethod
    def repair(
        self, series: pd.Series, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """
        Apply the repair strategy to the series.

        Args:
            series: The time series to repair
            **kwargs: Additional parameters for the strategy

        Returns:
            Tuple containing the repaired series and a list of RepairAction objects
        """
        pass


class GapFillStrategy(AbstractRepairStrategy):
    """Base class for gap filling strategies."""

    def __init__(self, strategy: RepairStrategy, variable_name: str):
        self.strategy = strategy
        self.variable_name = variable_name

    @abstractmethod
    def fill_gap(
        self, series: pd.Series, gap: TimeSeriesGap, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """
        Fill a specific gap in the series.

        Args:
            series: The time series with gaps
            gap: The gap to fill
            **kwargs: Additional parameters

        Returns:
            Tuple containing the series with the gap filled and a list of RepairAction objects
        """
        pass

    def repair(
        self, series: pd.Series, gaps: Optional[List[TimeSeriesGap]] = None, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """
        Fill all gaps in the series.

        Args:
            series: The time series to repair (pandas Series)
            gaps: Optional list of gaps to fill (if None, will detect gaps)
            **kwargs: Additional parameters

        Returns:
            Tuple containing the repaired series and a list of RepairAction objects
        """
        # Make a copy of the input series to avoid modifying the original
        repaired_series: pd.Series = series.copy()  # Use generic pd.Series type hint

        # Detect gaps if not provided
        if gaps is None:
            gaps = detect_gaps(repaired_series)

        all_actions = []

        # Apply the strategy to each gap
        for gap in gaps:
            repaired_series, actions = self.fill_gap(repaired_series, gap, **kwargs)
            all_actions.extend(actions)

        return repaired_series, all_actions


class ForwardFillStrategy(GapFillStrategy):
    """Fill gaps by propagating the last valid value forward."""

    def __init__(self, variable_name: str):
        super().__init__(RepairStrategy.FORWARD_FILL, variable_name)

    def fill_gap(
        self, series: pd.Series, gap: TimeSeriesGap, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Fill a gap by propagating the last valid value forward."""
        # Check if the gap is at the beginning of the series
        if gap.start_time <= series.index.min():
            # Can't forward fill without a prior value
            return series, []

        # Get the value just before the gap
        prior_idx = series.index[series.index < gap.start_time].max()
        fill_value = series.loc[prior_idx]

        # Create a date range for the gap
        gap_dates = pd.date_range(start=gap.start_time, end=gap.end_time, freq="D")
        gap_dates = gap_dates[~gap_dates.isin(series.index)]

        # Create repair actions
        actions = []

        # Fill the gap
        for date in gap_dates:
            # Create a repair action
            action = RepairAction(
                action_id=str(uuid.uuid4()),
                variable_name=self.variable_name,
                action_type=RepairActionType.GAP_FILL,
                strategy=self.strategy,
                timestamp=date,
                original_value=None,
                new_value=fill_value,
                start_time=gap.start_time,
                end_time=gap.end_time,
                context={
                    "method": "forward_fill",
                    "source_date": prior_idx.isoformat(),
                },
            )
            actions.append(action)

            # Add the new value to the series
            # Add the new value to the series using update
            new_data = pd.Series([float(fill_value)], index=[pd.Timestamp(date)])
            series.update(new_data)

        # Sort by index
        return series.sort_index(), actions


class BackwardFillStrategy(GapFillStrategy):
    """Fill gaps by propagating the next valid value backward."""

    def __init__(self, variable_name: str):
        super().__init__(RepairStrategy.BACKWARD_FILL, variable_name)

    def fill_gap(
        self, series: pd.Series, gap: TimeSeriesGap, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Fill a gap by propagating the next valid value backward."""
        # Check if the gap is at the end of the series
        if gap.end_time >= series.index.max():
            # Can't backward fill without a next value
            return series, []

        # Get the value just after the gap
        next_idx = series.index[series.index > gap.end_time].min()
        fill_value = series.loc[next_idx]

        # Create a date range for the gap
        gap_dates = pd.date_range(start=gap.start_time, end=gap.end_time, freq="D")
        gap_dates = gap_dates[~gap_dates.isin(series.index)]

        # Create repair actions
        actions = []

        # Fill the gap
        for date in gap_dates:
            # Create a repair action
            action = RepairAction(
                action_id=str(uuid.uuid4()),
                variable_name=self.variable_name,
                action_type=RepairActionType.GAP_FILL,
                strategy=self.strategy,
                timestamp=date,
                original_value=None,
                new_value=fill_value,
                start_time=gap.start_time,
                end_time=gap.end_time,
                context={
                    "method": "backward_fill",
                    "source_date": next_idx.isoformat(),
                },
            )
            actions.append(action)

            # Add the new value to the series
            # Add the new value to the series using update
            new_data = pd.Series([float(fill_value)], index=[pd.Timestamp(date)])
            series.update(new_data)

        # Sort by index
        return series.sort_index(), actions


class LinearInterpolationStrategy(GapFillStrategy):
    """Fill gaps using linear interpolation between the nearest valid values."""

    def __init__(
        self,
        variable_name: str,
        bounded: bool = False,
        bounds: Optional[Tuple[float, float]] = None,
    ):
        self.bounded = bounded
        self.bounds = bounds
        strategy = RepairStrategy.LINEAR_BOUNDED if bounded else RepairStrategy.LINEAR
        super().__init__(strategy, variable_name)

    def fill_gap(
        self, series: pd.Series, gap: TimeSeriesGap, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Fill a gap using linear interpolation."""
        # Check if the gap is at the beginning or end of the series
        if gap.start_time <= series.index.min():
            # Can't interpolate without values on both sides
            return series, []
        if gap.end_time >= series.index.max():
            # Can't interpolate without values on both sides
            return series, []

        # Get values just before and after the gap
        prior_idx = series.index[series.index < gap.start_time].max()
        next_idx = series.index[series.index > gap.end_time].min()

        if prior_idx is None or next_idx is None:
            # Can't interpolate without valid values on both sides
            return series, []

        prior_value = series.loc[prior_idx]
        next_value = series.loc[next_idx]

        # Create a date range for the gap
        gap_dates = pd.date_range(start=gap.start_time, end=gap.end_time, freq="D")
        gap_dates = gap_dates[~gap_dates.isin(series.index)]

        # Calculate time deltas as floats for interpolation
        prior_time = prior_idx.timestamp()
        next_time = next_idx.timestamp()
        time_delta = next_time - prior_time
        value_delta = next_value - prior_value

        # Create repair actions
        actions = []

        # Fill the gap
        for date in gap_dates:
            # Calculate the interpolated value
            date_time = date.timestamp()
            ratio = (date_time - prior_time) / time_delta
            interpolated_value = prior_value + (ratio * value_delta)

            # Apply bounds if necessary
            if self.bounded and self.bounds:
                interpolated_value = max(
                    self.bounds[0], min(self.bounds[1], interpolated_value)
                )

            # Create a repair action
            action = RepairAction(
                action_id=str(uuid.uuid4()),
                variable_name=self.variable_name,
                action_type=RepairActionType.GAP_FILL,
                strategy=self.strategy,
                timestamp=date,
                original_value=None,
                new_value=interpolated_value,
                start_time=gap.start_time,
                end_time=gap.end_time,
                context={
                    "method": "linear_interpolation",
                    "prior_date": prior_idx.isoformat(),
                    "prior_value": float(prior_value),
                    "next_date": next_idx.isoformat(),
                    "next_value": float(next_value),
                    "bounded": self.bounded,
                    "bounds": self.bounds,
                },
            )
            actions.append(action)

            # Add the new value to the series
            # Add the new value to the series using update
            new_data = pd.Series([float(interpolated_value)], index=[date])
            series.update(new_data)

        # Sort by index
        return series.sort_index(), actions


class PolynomialInterpolationStrategy(GapFillStrategy):
    """Fill gaps using polynomial interpolation based on surrounding data."""

    def __init__(self, variable_name: str, degree: int = 3, window_size: int = 10):
        self.degree = degree
        self.window_size = window_size
        super().__init__(RepairStrategy.POLYNOMIAL, variable_name)

    def fill_gap(
        self, series: pd.Series, gap: TimeSeriesGap, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Fill a gap using polynomial interpolation."""
        # Need enough surrounding points for polynomial fitting
        min_window = max(self.degree + 1, 4)  # At least 4 points or degree + 1

        # Create a date range for the gap
        gap_dates = pd.date_range(start=gap.start_time, end=gap.end_time, freq="D")
        gap_dates = gap_dates[~gap_dates.isin(series.index)]

        if len(gap_dates) == 0:
            return series, []

        # Get surrounding data points
        window_before = min(
            self.window_size, len(series[series.index < gap.start_time])
        )
        window_after = min(self.window_size, len(series[series.index > gap.end_time]))

        if window_before + window_after < min_window:
            # Not enough data for polynomial fitting
            logger.warning(
                f"Not enough data for polynomial interpolation. Gap: {gap.start_time} to {gap.end_time}"
            )
            return series, []

        # Get the reference points for fitting
        before_points = series[series.index < gap.start_time].iloc[-window_before:]
        after_points = series[series.index > gap.end_time].iloc[:window_after]

        reference_series = pd.concat([before_points, after_points])

        if len(reference_series) < min_window:
            return series, []

        # Convert timestamps to numerical values for interpolation
        # Use seconds since epoch for x values
        x_ref = np.array(
            [
                (idx - pd.Timestamp("1970-01-01")).total_seconds()
                for idx in reference_series.index
            ]
        )
        y_ref = reference_series.values

        # Convert gap timestamps to seconds
        x_gap = np.array(
            [(date - pd.Timestamp("1970-01-01")).total_seconds() for date in gap_dates]
        )

        try:
            # Fit polynomial (ensure y_ref is float type)
            coefs = np.polyfit(x_ref, y_ref.astype(float), self.degree)
            poly = np.poly1d(coefs)

            # Evaluate polynomial at gap timestamps
            y_gap = poly(x_gap)

            # Create repair actions
            actions = []

            # Fill the gap
            for i, date in enumerate(gap_dates):
                # Create a repair action
                action = RepairAction(
                    action_id=str(uuid.uuid4()),
                    variable_name=self.variable_name,
                    action_type=RepairActionType.GAP_FILL,
                    strategy=self.strategy,
                    timestamp=date,
                    original_value=None,
                    new_value=float(y_gap[i]),
                    start_time=gap.start_time,
                    end_time=gap.end_time,
                    context={
                        "method": "polynomial_interpolation",
                        "degree": self.degree,
                        "window_size": self.window_size,
                        "reference_points": len(reference_series),
                    },
                )
                actions.append(action)

                # Add the new value to the series
                # Add the new value to the series using update
                new_data = pd.Series([float(y_gap[i])], index=[date])
                series.update(new_data)

            # Sort by index
            return series.sort_index(), actions

        except Exception as e:
            logger.error(f"Error during polynomial interpolation: {e}")
            return series, []


class MovingAverageStrategy(GapFillStrategy):
    """Fill gaps using moving average of surrounding values."""

    def __init__(
        self, variable_name: str, window_size: int = 5, round_to_int: bool = False
    ):
        self.window_size = window_size
        self.round_to_int = round_to_int
        strategy = (
            RepairStrategy.INTERPOLATE_ROUND
            if round_to_int
            else RepairStrategy.MOVING_AVERAGE
        )
        super().__init__(strategy, variable_name)

    def fill_gap(
        self, series: pd.Series, gap: TimeSeriesGap, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Fill a gap using moving average imputation."""
        # Need some surrounding points for moving average
        if len(series) < self.window_size:
            return series, []

        # Create a date range for the gap
        gap_dates = pd.date_range(start=gap.start_time, end=gap.end_time, freq="D")
        gap_dates = gap_dates[~gap_dates.isin(series.index)]

        if len(gap_dates) == 0:
            return series, []

        # For each missing date, calculate the average of nearest available values
        actions = []

        for date in gap_dates:
            # Find closest dates with data
            # Filter out gap dates and sort by distance to the current date
            valid_indices = series.index[~series.index.isin(gap_dates)]
            # Ensure valid_indices is DatetimeIndex for total_seconds
            valid_datetime_indices = pd.DatetimeIndex(valid_indices)
            # Calculate time differences and sort by absolute difference
            # Calculate time differences and sort by absolute difference
            # Calculate time differences and sort by absolute difference
            # Calculate time differences and sort by absolute difference
            # Calculate time differences and sort by absolute difference
            time_diffs = np.abs(
                pd.TimedeltaIndex(
                    valid_datetime_indices - pd.Timestamp(date)
                ).total_seconds()
            )
            closest_dates = valid_indices[np.argsort(time_diffs)]

            # Use up to window_size closest dates
            closest_dates = closest_dates[: self.window_size]

            if len(closest_dates) == 0:
                continue

            # Calculate average
            avg_value = series.loc[closest_dates].mean()

            # Round to integer if requested
            if self.round_to_int:
                avg_value = round(avg_value)

            # Create repair action
            action = RepairAction(
                action_id=str(uuid.uuid4()),
                variable_name=self.variable_name,
                action_type=RepairActionType.GAP_FILL,
                strategy=self.strategy,
                timestamp=date,
                original_value=None,
                new_value=float(avg_value),
                start_time=gap.start_time,
                end_time=gap.end_time,
                context={
                    "method": "moving_average",
                    "window_size": self.window_size,
                    "actual_window": len(closest_dates),
                    "rounded": self.round_to_int,
                },
            )
            actions.append(action)

            # Add the new value to the series
            # Add the new value to the series using update
            new_data = pd.Series([float(avg_value)], index=[date])
            series.update(new_data)

        # Sort by index
        return series.sort_index(), actions


class SeasonalInterpolationStrategy(GapFillStrategy):
    """Fill gaps using seasonal patterns in the data."""

    def __init__(self, variable_name: str, seasonal_period: Optional[int] = None):
        self.seasonal_period = seasonal_period
        super().__init__(RepairStrategy.SEASONAL_INTERPOLATION, variable_name)

    def fill_gap(
        self, series: pd.Series, gap: TimeSeriesGap, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Fill a gap using seasonal interpolation."""
        # Need enough data to detect seasonality
        if len(series) < 2 * 30:  # At least 2 months of data
            return series, []

        # Create a date range for the gap
        gap_dates = pd.date_range(start=gap.start_time, end=gap.end_time, freq="D")
        gap_dates = gap_dates[~gap_dates.isin(series.index)]

        if len(gap_dates) == 0:
            return series, []

        # Determine seasonality period if not provided
        seasonal_period = self.seasonal_period
        if seasonal_period is None:
            # Try to detect seasonality
            try:
                seasonality_result = detect_seasonality(series)
                if seasonality_result["has_seasonality"]:
                    seasonal_period = seasonality_result.get("strongest_period", 7)
                else:
                    # Default to weekly seasonality
                    seasonal_period = 7
            except Exception:
                # Default to weekly seasonality
                seasonal_period = 7

        # Not enough data for the detected seasonality
        if len(series) < 2 * seasonal_period:
            return series, []

        # Use seasonal information to fill gaps
        actions = []

        for date in gap_dates:
            # Find dates with the same seasonal position
            day_of_week = date.dayofweek
            month_day = date.day
            month = date.month

            # Construct a mask for same day of week, same day of month, or same month
            dow_mask = pd.Series(
                [idx.dayofweek == day_of_week for idx in series.index],
                index=series.index,
            )

            # Try to find values from the same day of week
            seasonal_values = series[dow_mask]

            if len(seasonal_values) < 3:
                # Not enough data with same day of week, try month day
                dom_mask = pd.Series(
                    [idx.day == month_day for idx in series.index], index=series.index
                )
                seasonal_values = series[dom_mask]

                if len(seasonal_values) < 3:
                    # Not enough data with same month day, try month
                    m_mask = pd.Series(
                        [idx.month == month for idx in series.index], index=series.index
                    )
                    seasonal_values = series[m_mask]

                    if len(seasonal_values) < 3:
                        # Not enough seasonal data, skip this date
                        continue

            # Calculate the mean of seasonal values
            seasonal_mean = seasonal_values.mean()

            # Use the seasonal mean
            action = RepairAction(
                action_id=str(uuid.uuid4()),
                variable_name=self.variable_name,
                action_type=RepairActionType.GAP_FILL,
                strategy=self.strategy,
                timestamp=date,
                original_value=None,
                new_value=float(seasonal_mean),
                start_time=gap.start_time,
                end_time=gap.end_time,
                context={
                    "method": "seasonal_interpolation",
                    "seasonal_period": seasonal_period,
                    "day_of_week": day_of_week,
                    "month_day": month_day,
                    "month": month,
                    "seasonal_values_count": len(seasonal_values),
                },
            )
            actions.append(action)

            # Add the new value to the series
            # Add the new value to the series using update
            new_data = pd.Series([float(seasonal_mean)], index=[date])
            series.update(new_data)

        # Sort by index
        return series.sort_index(), actions


class ArimaImputationStrategy(GapFillStrategy):
    """Fill gaps using ARIMA model predictions."""

    def __init__(
        self,
        variable_name: str,
        order: Tuple[int, int, int] = (1, 1, 1),
        seasonal_order: Optional[Tuple[int, int, int, int]] = None,
    ):
        self.order = order
        self.seasonal_order = seasonal_order
        super().__init__(RepairStrategy.ARIMA, variable_name)

    def fill_gap(
        self, series: pd.Series, gap: TimeSeriesGap, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Fill a gap using ARIMA modeling."""
        try:
            from statsmodels.tsa.arima.model import ARIMA
            from statsmodels.tsa.statespace.sarimax import SARIMAX
        except ImportError:
            logger.error("statsmodels not installed, cannot use ARIMA imputation")
            return series, []

        # Need enough data for ARIMA modeling
        if len(series) < 30:  # Arbitrary minimum for reasonable ARIMA
            return series, []

        # Create a date range for the gap
        gap_dates = pd.date_range(start=gap.start_time, end=gap.end_time, freq="D")
        gap_dates = gap_dates[~gap_dates.isin(series.index)]

        if len(gap_dates) == 0:
            return series, []

        # Sort the series by index
        sorted_series = series.sort_index()

        try:
            # Fit ARIMA model
            if self.seasonal_order:
                # Use SARIMAX for seasonal ARIMA
                model = SARIMAX(
                    sorted_series, order=self.order, seasonal_order=self.seasonal_order
                )
            else:
                # Use regular ARIMA
                model = ARIMA(sorted_series, order=self.order)

            # Fit the model
            model_fit = model.fit()

            # Predict values for gap dates
            predictions = {}

            for date in gap_dates:
                # Check if the date is before the series start
                if date < sorted_series.index.min():
                    continue

                # Create a temporary series with the gap date missing
                temp_series = sorted_series.copy()
                if date in temp_series.index:
                    temp_series = temp_series.drop(date)

                # Re-fit model if necessary
                if len(temp_series) < 30:
                    continue

                # Predict the value for the gap date
                # First, identify the position in the index
                future_idx = len(temp_series)
                for i, idx in enumerate(sorted_series.index):
                    if idx >= date:
                        break

                # Make one-step ahead forecast
                forecast = model_fit.get_forecast(steps=1)
                predicted_value = forecast.predicted_mean.iloc[0]

                predictions[date] = predicted_value

            # Create repair actions and update series
            actions = []

            for date, predicted_value in predictions.items():
                action = RepairAction(
                    action_id=str(uuid.uuid4()),
                    variable_name=self.variable_name,
                    action_type=RepairActionType.GAP_FILL,
                    strategy=self.strategy,
                    timestamp=date,
                    original_value=None,
                    new_value=float(predicted_value),
                    start_time=gap.start_time,
                    end_time=gap.end_time,
                    context={
                        "method": "arima",
                        "order": self.order,
                        "seasonal_order": self.seasonal_order,
                    },
                )
                actions.append(action)

                # Add the new value to the series
                series.loc[date] = float(predicted_value)  # Ensure float type

            # Sort by index
            return series.sort_index(), actions

        except Exception as e:
            logger.error(f"Error during ARIMA imputation: {e}")
            return series, []


class AnomalyRepairStrategy(AbstractRepairStrategy):
    """Base class for anomaly correction strategies."""

    def __init__(self, strategy: RepairStrategy, variable_name: str):
        self.strategy = strategy
        self.variable_name = variable_name

    @abstractmethod
    def correct_anomaly(
        self, series: pd.Series, anomaly: Anomaly, **kwargs
    ) -> Tuple[pd.Series, Optional[RepairAction]]:
        """
        Correct a specific anomaly in the series.

        Args:
            series: The time series with anomalies
            anomaly: The anomaly to correct
            **kwargs: Additional parameters

        Returns:
            Tuple containing the series with the anomaly corrected and a RepairAction object
        """
        pass

    def repair(
        self, series: pd.Series, anomalies: Optional[List[Anomaly]] = None, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """
        Correct all anomalies in the series.

        Args:
            series: The time series to repair (pandas Series)
            anomalies: Optional list of anomalies to correct (if None, will detect anomalies)
            **kwargs: Additional parameters

        Returns:
            Tuple containing the repaired series and a list of RepairAction objects
        """
        # Make a copy of the input series to avoid modifying the original
        repaired_series: pd.Series = series.copy()  # Add type hint

        # Detect anomalies if not provided
        if anomalies is None:
            anomalies = detect_anomalies(repaired_series)

        all_actions = []

        # Apply the strategy to each anomaly
        for anomaly in anomalies:
            repaired_series, action = self.correct_anomaly(
                repaired_series, anomaly, **kwargs
            )
            if action:
                all_actions.append(action)

        return repaired_series, all_actions


class MedianFilterStrategy(AnomalyRepairStrategy):
    """Correct anomalies using a median filter."""

    def __init__(self, variable_name: str, window_size: int = 5):
        self.window_size = window_size
        super().__init__(RepairStrategy.MEDIAN_FILTER, variable_name)

    def correct_anomaly(
        self, series: pd.Series, anomaly: Anomaly, **kwargs
    ) -> Tuple[pd.Series, Optional[RepairAction]]:
        """Correct an anomaly using a median filter."""
        # Skip if the anomaly timestamp is not in the series
        if pd.Timestamp(anomaly.timestamp) not in series.index:
            return series, None  # Return series and None for action if skipped

        timestamp = pd.Timestamp(anomaly.timestamp)
        # Get the integer position(s) of the timestamp in the index
        # Use get_indexer to handle potential non-unique indices and ensure integer output
        idx_positions = series.index.get_indexer([timestamp])

        # If the timestamp is not found (should not happen due to prior check, but for safety)
        if len(idx_positions) == 0 or idx_positions[0] == -1:
            return (
                series,
                None,
            )  # Return series and None for action if timestamp not found

        # Use the first position if there are multiple entries for the same timestamp
        idx_position_int = int(idx_positions[0])  # Explicitly cast to int

        # Define window bounds
        start_idx = max(0, idx_position_int - self.window_size // 2)
        end_idx = min(len(series) - 1, idx_position_int + self.window_size // 2)
        start_idx = max(0, idx_position_int - self.window_size // 2)
        end_idx = min(len(series) - 1, idx_position_int + self.window_size // 2)

        # Get window values (excluding the anomaly itself)
        window_values = [
            series.iloc[i]
            for i in range(start_idx, end_idx + 1)
            if i != idx_position_int  # Use idx_position_int
        ]

        if not window_values:
            return series, None  # Return series and None for action if skipped

        # Calculate median
        median_value = np.median(window_values)

        # Create repair action
        action = RepairAction(
            action_id=str(uuid.uuid4()),
            variable_name=self.variable_name,
            action_type=RepairActionType.ANOMALY_CORRECTION,
            strategy=self.strategy,
            timestamp=anomaly.timestamp,
            original_value=float(series.loc[timestamp]),
            new_value=float(median_value),
            context={
                "method": "median_filter",
                "window_size": self.window_size,
                "actual_window": len(window_values),
                "anomaly_severity": anomaly.severity,
                "detection_method": anomaly.method,
            },
        )

        # Replace the anomaly with the median value
        series.loc[[timestamp]] = float(median_value)  # Ensure float type

        return series, action


class WinsorizeStrategy(AnomalyRepairStrategy):
    """Correct anomalies by winsorizing (capping) extreme values."""

    def __init__(self, variable_name: str, limits: Tuple[float, float] = (0.05, 0.05)):
        self.limits = limits
        super().__init__(RepairStrategy.WINSORIZE, variable_name)

    def correct_anomaly(
        self, series: pd.Series, anomaly: Anomaly, **kwargs
    ) -> Tuple[pd.Series, Optional[RepairAction]]:
        """Correct an anomaly by winsorizing."""
        # Skip if the anomaly timestamp is not in the series
        if pd.Timestamp(anomaly.timestamp) not in series.index:
            return series, None  # Return series and None for action if skipped

        timestamp = pd.Timestamp(anomaly.timestamp)
        original_value = series.loc[timestamp]

        # Calculate the percentile limits
        lower_limit = np.percentile(series, self.limits[0] * 100)
        upper_limit = np.percentile(series, 100 - self.limits[1] * 100)

        # Apply limits
        if original_value < lower_limit:
            new_value = lower_limit
        elif original_value > upper_limit:
            new_value = upper_limit
        else:
            # Value is already within limits
            return series, None  # Return series and None for action if skipped

        # Create repair action
        action = RepairAction(
            action_id=str(uuid.uuid4()),
            variable_name=self.variable_name,
            action_type=RepairActionType.ANOMALY_CORRECTION,
            strategy=self.strategy,
            timestamp=anomaly.timestamp,
            original_value=float(original_value),
            new_value=float(new_value),
            context={
                "method": "winsorize",
                "limits": self.limits,
                "lower_limit": float(lower_limit),
                "upper_limit": float(upper_limit),
                "anomaly_severity": anomaly.severity,
                "detection_method": anomaly.method,
            },
        )

        # Replace the anomaly with the capped value
        series.loc[[timestamp]] = float(new_value)  # Ensure float type

        return series, action


class MovingAverageCorrectionStrategy(AnomalyRepairStrategy):
    """Correct anomalies using a moving average."""

    def __init__(
        self, variable_name: str, window_size: int = 5, round_to_int: bool = False
    ):
        self.window_size = window_size
        self.round_to_int = round_to_int
        strategy = (
            RepairStrategy.MOVING_AVERAGE_ROUND
            if round_to_int
            else RepairStrategy.MOVING_AVERAGE_CORRECTION
        )
        super().__init__(strategy, variable_name)

    def correct_anomaly(
        self, series: pd.Series, anomaly: Anomaly, **kwargs
    ) -> Tuple[pd.Series, Optional[RepairAction]]:
        """Correct an anomaly using a moving average."""
        # Skip if the anomaly timestamp is not in the series
        if pd.Timestamp(anomaly.timestamp) not in series.index:
            return series, None  # Return series and None for action if skipped

        timestamp = pd.Timestamp(anomaly.timestamp)
        original_value = series.loc[timestamp]

        # Get the window around the anomaly
        idx_position = series.index.get_loc(pd.Timestamp(timestamp))

        # Define window bounds
        # Ensure idx_position is an integer for slicing
        idx_position_int = int(idx_position)
        start_idx = max(0, idx_position_int - self.window_size // 2)
        end_idx = min(len(series) - 1, idx_position_int + self.window_size // 2)

        # Get window values (excluding the anomaly itself)
        window_values = [
            series.iloc[i] for i in range(start_idx, end_idx + 1) if i != idx_position
        ]

        if not window_values:
            return series, None  # Return series and None for action if skipped

        # Calculate mean
        mean_value = np.mean(window_values)

        # Round to integer if requested
        if self.round_to_int:
            mean_value = round(mean_value)

        # Create repair action
        action = RepairAction(
            action_id=str(uuid.uuid4()),
            variable_name=self.variable_name,
            action_type=RepairActionType.ANOMALY_CORRECTION,
            strategy=self.strategy,
            timestamp=anomaly.timestamp,
            original_value=float(original_value),
            new_value=float(mean_value),
            context={
                "method": "moving_average_correction",
                "window_size": self.window_size,
                "actual_window": len(window_values),
                "rounded": self.round_to_int,
                "anomaly_severity": anomaly.severity,
                "detection_method": anomaly.method,
            },
        )

        # Replace the anomaly with the mean value
        series.loc[[timestamp]] = float(mean_value)  # Ensure float type

        return series, action


class BoundedCorrectionStrategy(AnomalyRepairStrategy):
    """Correct anomalies by enforcing bounds on values."""

    def __init__(
        self,
        variable_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(RepairStrategy.BOUNDED_CORRECTION, variable_name)

    def correct_anomaly(
        self, series: pd.Series, anomaly: Anomaly, **kwargs
    ) -> Tuple[pd.Series, Optional[RepairAction]]:
        """Correct an anomaly by enforcing bounds."""
        # Skip if the anomaly timestamp is not in the series
        if pd.Timestamp(anomaly.timestamp) not in series.index:
            return series, None  # Return series and None for action if skipped

        timestamp = pd.Timestamp(anomaly.timestamp)
        original_value = series.loc[timestamp]

        # Determine bounds if not provided
        min_value = self.min_value
        max_value = self.max_value

        if min_value is None:
            min_value = series.quantile(0.001)  # Very low percentile

        if max_value is None:
            max_value = series.quantile(0.999)  # Very high percentile

        # Apply bounds
        if original_value < min_value:
            new_value = min_value
        elif original_value > max_value:
            new_value = max_value
        else:
            # Value is already within limits
            return series, None  # Return series and None for action if skipped

        # Create repair action
        action = RepairAction(
            action_id=str(uuid.uuid4()),
            variable_name=self.variable_name,
            action_type=RepairActionType.ANOMALY_CORRECTION,
            strategy=self.strategy,
            timestamp=anomaly.timestamp,
            original_value=float(original_value),
            new_value=float(new_value),
            context={
                "method": "bounded_correction",
                "min_value": float(min_value),
                "max_value": float(max_value),
                "anomaly_severity": anomaly.severity,
                "detection_method": anomaly.method,
            },
        )

        # Replace the anomaly with the bounded value
        series.loc[[timestamp]] = float(new_value)  # Ensure float type

        return series, action


class SmoothingStrategy(AbstractRepairStrategy):
    """Base class for smoothing strategies."""

    def __init__(self, strategy: RepairStrategy, variable_name: str):
        self.strategy = strategy
        self.variable_name = variable_name

    def repair(
        self, series: pd.Series, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """
        Apply smoothing to the time series.

        Args:
            series: The time series to smooth
            **kwargs: Additional parameters

        Returns:
            Tuple containing the smoothed series and a list of RepairAction objects
        """
        # Default implementation returns the original series (no smoothing)
        return series, []


class RollingMeanStrategy(SmoothingStrategy):
    """Smooth data using a rolling mean."""

    def __init__(self, variable_name: str, window_size: int = 5):
        self.window_size = window_size
        super().__init__(RepairStrategy.ROLLING_MEAN, variable_name)

    def repair(
        self, series: pd.Series, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Apply rolling mean smoothing."""
        if len(series) < self.window_size:
            return series, []

        # Calculate rolling mean
        smoothed = series.rolling(window=self.window_size, center=True).mean()

        # For start and end points, use available window
        for i in range(self.window_size // 2):
            if i < len(series):
                smoothed.iloc[i] = series.iloc[: i + self.window_size // 2 + 1].mean()
                smoothed.iloc[-(i + 1)] = series.iloc[
                    -(i + self.window_size // 2 + 1) :
                ].mean()

        # Create repair actions
        actions = []

        for idx, (timestamp, original, smoothed_val) in enumerate(
            zip(series.index, series, smoothed)
        ):
            if pd.isna(smoothed_val):
                continue

            if abs(original - smoothed_val) > 1e-10:  # Avoid actions for tiny changes
                action = RepairAction(
                    action_id=str(uuid.uuid4()),
                    variable_name=self.variable_name,
                    action_type=RepairActionType.SMOOTHING,
                    strategy=self.strategy,
                    timestamp=timestamp,
                    original_value=float(original),
                    new_value=float(smoothed_val),
                    context={"method": "rolling_mean", "window_size": self.window_size},
                )
                actions.append(action)

        return smoothed, actions


class ExponentialSmoothingStrategy(SmoothingStrategy):
    """Smooth data using exponential smoothing."""

    def __init__(self, variable_name: str, alpha: float = 0.3):
        self.alpha = alpha
        super().__init__(RepairStrategy.EXPONENTIAL, variable_name)

    def repair(
        self, series: pd.Series, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Apply exponential smoothing."""
        if len(series) < 2:
            return series, []

        # Calculate exponential weighted moving average
        smoothed = series.ewm(alpha=self.alpha).mean()

        # Create repair actions
        actions = []

        for idx, (timestamp, original, smoothed_val) in enumerate(
            zip(series.index, series, smoothed)
        ):
            if pd.isna(smoothed_val):
                continue

            if abs(original - smoothed_val) > 1e-10:  # Avoid actions for tiny changes
                action = RepairAction(
                    action_id=str(uuid.uuid4()),
                    variable_name=self.variable_name,
                    action_type=RepairActionType.SMOOTHING,
                    strategy=self.strategy,
                    timestamp=timestamp,
                    original_value=float(original),
                    new_value=float(smoothed_val),
                    context={"method": "exponential_smoothing", "alpha": self.alpha},
                )
                actions.append(action)

        return smoothed, actions


class SavitzkyGolayStrategy(SmoothingStrategy):
    """Smooth data using the Savitzky-Golay filter."""

    def __init__(self, variable_name: str, window_size: int = 5, poly_order: int = 2):
        self.window_size = window_size
        self.poly_order = poly_order
        super().__init__(RepairStrategy.SAVITZKY_GOLAY, variable_name)

    def repair(
        self, series: pd.Series, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Apply Savitzky-Golay smoothing."""
        # Check if we have enough data points
        if len(series) < self.window_size:
            return series, []

        # Window size must be odd
        window_size = self.window_size
        if window_size % 2 == 0:
            window_size += 1

        # Polynomial order must be less than window size
        poly_order = min(self.poly_order, window_size - 1)

        try:
            # Apply Savitzky-Golay filter
            smoothed_values = signal.savgol_filter(
                series.values, window_size, poly_order
            )

            smoothed = pd.Series(smoothed_values, index=series.index)

            # Create repair actions
            actions = []

            for idx, (timestamp, original, smoothed_val) in enumerate(
                zip(series.index, series, smoothed)
            ):
                if pd.isna(smoothed_val):
                    continue

                if (
                    abs(original - smoothed_val) > 1e-10
                ):  # Avoid actions for tiny changes
                    action = RepairAction(
                        action_id=str(uuid.uuid4()),
                        variable_name=self.variable_name,
                        action_type=RepairActionType.SMOOTHING,
                        strategy=self.strategy,
                        timestamp=timestamp,
                        original_value=float(original),
                        new_value=float(smoothed_val),
                        context={
                            "method": "savitzky_golay",
                            "window_size": window_size,
                            "poly_order": poly_order,
                        },
                    )
                    actions.append(action)

            return smoothed, actions

        except Exception as e:
            logger.error(f"Error applying Savitzky-Golay filter: {e}")
            return series, []


class LoessStrategy(SmoothingStrategy):
    """Smooth data using LOESS (locally estimated scatterplot smoothing)."""

    def __init__(self, variable_name: str, frac: float = 0.3, it: int = 3):
        self.frac = frac
        self.it = it
        super().__init__(RepairStrategy.LOESS, variable_name)

    def repair(
        self, series: pd.Series, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Apply LOESS smoothing."""
        try:
            from statsmodels.nonparametric.smoothers_lowess import lowess
        except ImportError:
            logger.error("statsmodels not installed, cannot use LOESS smoothing")
            return series, []

        # Check if we have enough data points
        if len(series) < 10:  # Arbitrary minimum for LOESS
            return series, []

        try:
            # Generate x values (positions in the series)
            x = np.arange(len(series))
            y = series.values

            # Apply LOESS smoothing
            smoothed_array = lowess(
                y, x, frac=self.frac, it=self.it, return_sorted=False
            )

            smoothed = pd.Series(smoothed_array, index=series.index)

            # Create repair actions
            actions = []

            for idx, (timestamp, original, smoothed_val) in enumerate(
                zip(series.index, series, smoothed)
            ):
                if pd.isna(smoothed_val):
                    continue

                if (
                    abs(original - smoothed_val) > 1e-10
                ):  # Avoid actions for tiny changes
                    action = RepairAction(
                        action_id=str(uuid.uuid4()),
                        variable_name=self.variable_name,
                        action_type=RepairActionType.SMOOTHING,
                        strategy=self.strategy,
                        timestamp=timestamp,
                        original_value=float(original),
                        new_value=float(smoothed_val),
                        context={
                            "method": "loess",
                            "frac": self.frac,
                            "iterations": self.it,
                        },
                    )
                    actions.append(action)

            return smoothed, actions

        except Exception as e:
            logger.error(f"Error applying LOESS smoothing: {e}")
            return series, []


class NoSmoothingStrategy(SmoothingStrategy):
    """No-op smoothing strategy."""

    def __init__(self, variable_name: str):
        super().__init__(RepairStrategy.NONE, variable_name)

    def repair(
        self, series: pd.Series, **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """No smoothing applied."""
        return series, []


class CrossSourceStrategy(AbstractRepairStrategy):
    """Base class for cross-source reconciliation strategies."""

    def __init__(self, strategy: RepairStrategy, variable_name: str):
        self.strategy = strategy
        self.variable_name = variable_name

    @abstractmethod
    def reconcile(
        self, source_data: Dict[str, pd.Series], **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """
        Reconcile data from multiple sources.

        Args:
            source_data: Dictionary mapping source names to time series
            **kwargs: Additional parameters

        Returns:
            Tuple containing the reconciled series and a list of RepairAction objects
        """
        pass

    def repair(
        self,
        series: pd.Series,
        source_data: Optional[Dict[str, pd.Series]] = None,
        **kwargs,
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """
        Apply cross-source reconciliation.

        Args:
            series: The main time series to repair (pandas Series)
            source_data: Optional dictionary of source data (if None, will load data)
            **kwargs: Additional parameters

        Returns:
            Tuple containing the repaired series and a list of RepairAction objects
        """
        # Load source data if not provided
        if source_data is None:
            try:
                source_data = load_multi_source_data(self.variable_name)
            except Exception as e:
                logger.error(f"Error loading multi-source data: {e}")
                return series, []

        # Need at least 2 sources for reconciliation
        if len(source_data) < 2:
            return series, []

        # Apply the reconciliation strategy
        return self.reconcile(source_data, **kwargs)


class PrioritizedSourceStrategy(CrossSourceStrategy):
    """Reconcile data by prioritizing certain sources."""

    def __init__(
        self, variable_name: str, source_priorities: Optional[Dict[str, int]] = None
    ):
        self.source_priorities = source_priorities
        super().__init__(RepairStrategy.PRIORITIZED, variable_name)

    def reconcile(
        self, source_data: Dict[str, pd.Series], **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Reconcile data by prioritizing sources."""
        # Determine source priorities if not provided
        priorities = self.source_priorities
        if priorities is None:
            # Get cross-validation result to determine priorities
            try:
                cross_val = cross_validate_sources(self.variable_name)

                # Create priorities based on cross-validation correlations
                priorities = {}
                for source in source_data.keys():
                    # Calculate average correlation with other sources
                    avg_corr = 0.0
                    count = 0
                    for other_source in source_data.keys():
                        if source != other_source:
                            if (
                                source in cross_val.correlation_matrix
                                and other_source in cross_val.correlation_matrix[source]
                            ):
                                avg_corr += cross_val.correlation_matrix[source][
                                    other_source
                                ]
                                count += 1

                    # Higher average correlation = higher priority
                    if count > 0:
                        priorities[source] = avg_corr / count
                    else:
                        priorities[source] = 0.0
            except Exception as e:
                logger.error(f"Error determining source priorities: {e}")
                # Use default priorities (just use source names as keys)
                priorities = {
                    source: i for i, source in enumerate(sorted(source_data.keys()))
                }

        # Sort sources by priority (higher value = higher priority)
        sources_by_priority = [
            source
            for source, _ in sorted(
                priorities.items(), key=lambda x: x[1], reverse=True
            )
            if source in source_data
        ]

        if not sources_by_priority:
            return list(source_data.values())[0], []  # Just use the first source

        # Create a merged series based on priority
        # - For each date, use the value from the highest priority source that has data
        all_dates = set()
        for series in source_data.values():
            all_dates.update(series.index)

        all_dates = sorted(all_dates)
        result_values: Dict[pd.Timestamp, float] = {}  # Add type hint
        actions = []

        for date in all_dates:
            # Find highest priority source with data for this date
            selected_source = None
            selected_value = None

            for source in sources_by_priority:
                if date in source_data[source].index:
                    selected_source = source
                    selected_value = source_data[source].loc[date]
                    break

            if selected_source is not None:
                # Ensure the value is a float before assigning
                result_values[date] = (
                    float(selected_value) if selected_value is not None else np.nan
                )

                # Create a repair action if this date is not in the original series
                # or if the value is different
                original_series = kwargs.get(
                    "original_series", source_data.get(sources_by_priority[0])
                )

                if original_series is not None and (
                    date not in original_series.index
                    or (
                        date in original_series.index
                        and original_series.loc[date] != selected_value
                    )
                ):
                    original_value = (
                        original_series.loc[date]
                        if date in original_series.index
                        else None
                    )

                    action = RepairAction(
                        action_id=str(uuid.uuid4()),
                        variable_name=self.variable_name,
                        action_type=RepairActionType.CROSS_SOURCE,
                        strategy=self.strategy,
                        timestamp=date,
                        original_value=float(original_value)
                        if original_value is not None
                        else None,
                        new_value=float(selected_value)
                        if selected_value is not None
                        else None,  # Ensure float type, handle None
                        context={
                            "method": "prioritized_sources",
                            "selected_source": selected_source,
                            "source_priority": float(
                                priorities.get(selected_source, 0)
                            ),
                            "alternative_sources": [
                                s
                                for s in sources_by_priority
                                if s != selected_source and date in source_data[s].index
                            ],
                        },
                    )
                    actions.append(action)

        # Create the result series
        result_series = pd.Series(
            [result_values[date] for date in all_dates],
            index=all_dates,
            dtype=float,  # Ensure float dtype
        )

        return result_series, actions


class WeightedAverageStrategy(CrossSourceStrategy):
    """Reconcile data using a weighted average of multiple sources."""

    def __init__(self, variable_name: str, weights: Optional[Dict[str, float]] = None):
        self.weights = weights
        super().__init__(RepairStrategy.WEIGHTED_AVERAGE, variable_name)

    def reconcile(
        self, source_data: Dict[str, pd.Series], **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Reconcile data using a weighted average."""
        # Determine weights if not provided
        weights = self.weights
        if weights is None:
            # Get cross-validation result to determine weights
            try:
                cross_val = cross_validate_sources(self.variable_name)

                # Create weights based on cross-validation correlations
                weights = {}
                for source in source_data.keys():
                    # Calculate average correlation with other sources
                    avg_corr = 0.0
                    count = 0
                    for other_source in source_data.keys():
                        if source != other_source:
                            if (
                                source in cross_val.correlation_matrix
                                and other_source in cross_val.correlation_matrix[source]
                            ):
                                avg_corr += cross_val.correlation_matrix[source][
                                    other_source
                                ]
                                count += 1

                    # Higher average correlation = higher weight
                    if count > 0:
                        weights[source] = avg_corr / count
                    else:
                        weights[source] = 0.0

                # Normalize weights to sum to 1
                total_weight = sum(weights.values())
                if total_weight > 0:
                    weights = {
                        source: weight / total_weight
                        for source, weight in weights.items()
                    }
                else:
                    # Equal weights if no correlation information
                    weights = {
                        source: 1.0 / len(source_data) for source in source_data.keys()
                    }
            except Exception as e:
                logger.error(f"Error determining source weights: {e}")
                # Use equal weights
                weights = {
                    source: 1.0 / len(source_data) for source in source_data.keys()
                }

        # Get all dates from all sources
        all_dates = set()
        for series in source_data.values():
            all_dates.update(series.index)

        all_dates = sorted(all_dates)
        result_values: Dict[pd.Timestamp, float] = {}  # Add type hint
        actions = []

        for date in all_dates:
            # Calculate weighted average for this date
            weighted_sum = 0.0
            total_weight = 0.0
            sources_used = []

            for source, series in source_data.items():
                if date in series.index:
                    source_weight = weights.get(source, 0.0)
                    weighted_sum += series.loc[date] * source_weight
                    total_weight += source_weight
                    sources_used.append(source)

            # Only calculate if we have data
            if total_weight > 0:
                weighted_avg = weighted_sum / total_weight
                result_values[date] = weighted_avg

                # Create a repair action if this date is not in the original series
                # or if the value is different
                original_series = kwargs.get(
                    "original_series", next(iter(source_data.values()))
                )

                if original_series is not None and (
                    date not in original_series.index
                    or (
                        date in original_series.index
                        and abs(original_series.loc[date] - weighted_avg) > 1e-10
                    )
                ):
                    original_value = (
                        original_series.loc[date]
                        if date in original_series.index
                        else None
                    )

                    source_values = {
                        source: float(source_data[source].loc[date])
                        for source in sources_used
                    }
                    source_weights = {
                        source: float(weights.get(source, 0.0))
                        for source in sources_used
                    }

                    action = RepairAction(
                        action_id=str(uuid.uuid4()),
                        variable_name=self.variable_name,
                        action_type=RepairActionType.CROSS_SOURCE,
                        strategy=self.strategy,
                        timestamp=date,
                        original_value=float(original_value)
                        if original_value is not None
                        else None,
                        new_value=float(weighted_avg),
                        context={
                            "method": "weighted_average",
                            "sources_used": sources_used,
                            "source_values": source_values,
                            "source_weights": source_weights,
                            "normalized_weights": {
                                source: weight / total_weight
                                for source, weight in source_weights.items()
                            },
                        },
                    )
                    actions.append(action)

        # Create the result series
        result_series = pd.Series(
            [result_values[date] for date in all_dates],
            index=all_dates,
            dtype=float,  # Ensure float dtype
        )

        return result_series, actions


class VotingStrategy(CrossSourceStrategy):
    """Reconcile data using a voting mechanism among sources."""

    def __init__(self, variable_name: str, tolerance: float = 0.01):
        self.tolerance = tolerance
        super().__init__(RepairStrategy.VOTING, variable_name)

    def reconcile(
        self, source_data: Dict[str, pd.Series], **kwargs
    ) -> Tuple[pd.Series, List[RepairAction]]:
        """Reconcile data using voting."""
        # Get all dates from all sources
        all_dates = set()
        for series in source_data.values():
            all_dates.update(series.index)

        all_dates = sorted(all_dates)
        result_values: Dict[pd.Timestamp, float] = {}  # Add type hint
        actions = []

        for date in all_dates:
            # Collect values for this date from all sources
            date_values = []
            for source, series in source_data.items():
                if date in series.index:
                    date_values.append(series.loc[date])

            # Only proceed if we have at least 2 values
            if len(date_values) < 2:
                if date_values:
                    # If only one source has data, use that value
                    result_values[date] = float(date_values[0])
                # If no sources have data for this date, it remains missing
                continue

            # Count votes for each value (allowing for tolerance)
            value_counts: Dict[float, int] = {}  # Add type hint
            for value in date_values:
                found_match = False
                # Ensure value is float before comparison
                float_value = float(value)
                for existing_value in value_counts.keys():
                    # Check if values are close within tolerance
                    relative_diff = abs(float_value - existing_value) / max(
                        abs(existing_value), 1e-10
                    )
                    if relative_diff <= self.tolerance:
                        value_counts[existing_value] += 1
                        found_match = True
                        break

                if not found_match:
                    value_counts[float_value] = 1

            # Find the value with the most votes
            winner_value: Optional[float] = None  # Add type hint
            # Sort by votes descending, then value ascending for tie-breaking consistency
            sorted_votes = sorted(
                value_counts.items(), key=lambda item: (-item[1], item[0])
            )
            if sorted_votes:
                winner_value = sorted_votes[0][0]

            # In case of a tie, use the median
            if winner_value is None:
                winner_value = float(np.median(date_values))

            result_values[date] = float(winner_value)  # Ensure float type

            # Create a repair action if this date is not in the original series
            # or if the value is different
            # Attempt to get the original series from kwargs, otherwise use the first source's data
            original_series = kwargs.get(
                "original_series", next(iter(source_data.values()), None)
            )

            # Ensure original_series is a pandas Series before checking index
            if not isinstance(original_series, pd.Series):
                original_series = None

            if original_series is not None and (
                date not in original_series.index
                or (
                    date in original_series.index
                    and abs(float(original_series.loc[date]) - float(winner_value))
                    > 1e-10
                )  # Ensure float comparison
            ):
                original_value = (
                    original_series.loc[date] if date in original_series.index else None
                )

                action = RepairAction(
                    action_id=str(uuid.uuid4()),
                    variable_name=self.variable_name,
                    action_type=RepairActionType.CROSS_SOURCE,
                    strategy=self.strategy,
                    timestamp=date,
                    original_value=float(original_value)
                    if original_value is not None
                    else None,
                    new_value=float(winner_value)
                    if winner_value is not None
                    else None,  # Ensure float type, handle None
                    context={
                        "method": "voting",
                        "tolerance": self.tolerance,
                        "vote_counts": {
                            float(value): votes for value, votes in value_counts.items()
                        },
                        "values_considered": [float(value) for value in date_values],
                        "num_sources": len(date_values),
                    },
                )
                actions.append(action)

        # Create the result series
        result_series = pd.Series(
            [
                result_values[date] for date in all_dates if date in result_values
            ],  # Filter out dates with no result value
            index=[
                date for date in all_dates if date in result_values
            ],  # Filter index accordingly
            dtype=float,  # Ensure float dtype
        )

        return result_series, actions


def get_optimal_repair_strategy(
    variable_name: str,
    quality_result: QualityCheckResult,
    variable_type: str = "raw",
    cross_validation_result: Optional[CrossValidationResult] = None,
) -> Dict[str, Any]:
    """
    Determine the optimal repair strategies for a variable based on its quality assessment.

    Args:
        variable_name: Name of the variable
        quality_result: Quality check result from perform_quality_check
        variable_type: Type of variable (price, percentage, etc.)
        cross_validation_result: Cross-validation result (if available)

    Returns:
        Dictionary with recommended strategies for each repair type
    """
    # Default strategies based on variable type
    default_strategies = DEFAULT_REPAIR_STRATEGIES.get(
        variable_type, DEFAULT_REPAIR_STRATEGIES["raw"]
    )

    # Initialize with defaults
    strategies = {
        "gap_strategy": default_strategies["gap_strategy"],
        "anomaly_strategy": default_strategies["anomaly_strategy"],
        "smoothing_strategy": default_strategies["smoothing_strategy"],
        "cross_source_strategy": default_strategies["cross_source_strategy"],
    }

    # Adapt strategies based on quality assessment

    # 1. Gap filling strategy
    if quality_result.gaps:
        # Classify by gap size
        small_gaps = 0
        medium_gaps = 0
        large_gaps = 0
        very_large_gaps = 0

        for gap in quality_result.gaps:
            gap_days = gap.gap_duration.days

            if gap_days <= STRATEGY_THRESHOLDS["small_gap"]:
                small_gaps += 1
            elif gap_days <= STRATEGY_THRESHOLDS["medium_gap"]:
                medium_gaps += 1
            elif gap_days <= STRATEGY_THRESHOLDS["large_gap"]:
                large_gaps += 1
            else:
                very_large_gaps += 1

        # Choose strategy based on predominant gap size
        if very_large_gaps > 0:
            # For very large gaps, prefer cross-source if available
            if cross_validation_result and len(cross_validation_result.sources) > 1:
                strategies["gap_strategy"] = "weighted_average"
            else:
                # Otherwise use ARIMA for variables with seasonality
                if quality_result.quality_score.seasonality > 0.7:
                    strategies["gap_strategy"] = "seasonal_interpolation"
                else:
                    # Linear or polynomial for smoother trends
                    strategies["gap_strategy"] = "linear"
        elif large_gaps > small_gaps + medium_gaps:
            # For large gaps, prefer methods that understand trends
            if quality_result.quality_score.seasonality > 0.7:
                strategies["gap_strategy"] = "seasonal_interpolation"
            else:
                strategies["gap_strategy"] = "polynomial"
        elif medium_gaps > small_gaps:
            # For medium gaps, linear methods often work well
            strategies["gap_strategy"] = "linear"
        else:
            # For small gaps, simple methods are often sufficient
            if variable_type in ["count"]:
                strategies["gap_strategy"] = "interpolate_round"
            elif variable_type in ["percentage", "rate"]:
                strategies["gap_strategy"] = "linear_bounded"
            else:
                strategies["gap_strategy"] = "linear"

    # 2. Anomaly correction strategy
    if quality_result.anomalies:
        # Check for severe anomalies
        severe_anomalies = sum(
            1
            for a in quality_result.anomalies
            if a.severity > STRATEGY_THRESHOLDS["anomaly_severity"]
        )

        # Choose strategy based on anomaly severity and variable type
        if severe_anomalies > 0:
            if variable_type in ["count"]:
                strategies["anomaly_strategy"] = "moving_average_round"
            elif variable_type in ["percentage", "rate"]:
                strategies["anomaly_strategy"] = "bounded_correction"
            else:
                strategies["anomaly_strategy"] = "median_filter"
        else:
            # For milder anomalies, more conservative methods
            if variable_type in ["count"]:
                strategies["anomaly_strategy"] = "moving_average_round"
            elif variable_type in ["percentage", "rate"]:
                strategies["anomaly_strategy"] = "bounded_correction"
            else:
                strategies["anomaly_strategy"] = "moving_average_correction"

    # 3. Smoothing strategy
    if quality_result.quality_score.trend_stability < 0.7:
        # Unstable trend might benefit from smoothing
        if variable_type in ["price", "index"]:
            strategies["smoothing_strategy"] = "exponential"
        elif variable_type == "temperature":
            strategies["smoothing_strategy"] = "loess"
        else:
            strategies["smoothing_strategy"] = "rolling_mean"
    else:
        # Stable trend might not need smoothing
        strategies["smoothing_strategy"] = "none"

    # 4. Cross-source strategy
    if cross_validation_result and len(cross_validation_result.sources) > 1:
        # Find the best correlation from cross-validation
        best_corr = 0.0
        for source in cross_validation_result.sources:
            for other_source in cross_validation_result.sources:
                if source != other_source:
                    corr = cross_validation_result.correlation_matrix.get(
                        source, {}
                    ).get(other_source, 0.0)
                    best_corr = max(best_corr, corr)

        # Choose strategy based on correlation quality
        if best_corr > STRATEGY_THRESHOLDS["high_correlation"]:
            strategies["cross_source_strategy"] = "weighted_average"
        elif best_corr > STRATEGY_THRESHOLDS["medium_correlation"]:
            strategies["cross_source_strategy"] = "voting"
        else:
            strategies["cross_source_strategy"] = "prioritized"

    return strategies


def create_repair_strategy(
    strategy_type: str, variable_name: str, variable_type: str = "raw", **kwargs
) -> AbstractRepairStrategy:
    """
    Create a repair strategy object.

    Args:
        strategy_type: Type of strategy (e.g., "linear", "median_filter")
        variable_name: Name of the variable to repair
        variable_type: Type of variable (for bounded strategies)
        **kwargs: Additional parameters for the strategy

    Returns:
        A repair strategy object
    """
    # Get parameter defaults from variable type if needed
    var_range = None
    if variable_type == "percentage":
        var_range = (0, 100)
    elif variable_type in ["price", "rate", "index", "count"]:
        var_range = (0, float("inf"))
    elif variable_type == "temperature":
        var_range = (-100, 100)

    # Gap filling strategies
    if strategy_type == "forward_fill":
        return ForwardFillStrategy(variable_name)
    elif strategy_type == "backward_fill":
        return BackwardFillStrategy(variable_name)
    elif strategy_type == "linear":
        return LinearInterpolationStrategy(variable_name)
    elif strategy_type == "linear_bounded":
        return LinearInterpolationStrategy(
            variable_name, bounded=True, bounds=var_range
        )  # var_range can be None, handled in __init__
    elif strategy_type == "polynomial":
        degree = kwargs.get("degree", 3)
        window_size = kwargs.get("window_size", 10)
        return PolynomialInterpolationStrategy(
            variable_name, degree=degree, window_size=window_size
        )
    elif strategy_type == "moving_average":
        window_size = kwargs.get("window_size", 5)
        return MovingAverageStrategy(variable_name, window_size=window_size)
    elif strategy_type == "seasonal_interpolation":
        seasonal_period = kwargs.get("seasonal_period", None)
        return SeasonalInterpolationStrategy(
            variable_name, seasonal_period=seasonal_period
        )  # seasonal_period can be None, handled in __init__
    elif strategy_type == "arima":
        order = kwargs.get("order", (1, 1, 1))
        seasonal_order = kwargs.get("seasonal_order", None)
        return ArimaImputationStrategy(
            variable_name, order=order, seasonal_order=seasonal_order
        )  # seasonal_order can be None, handled in __init__
    elif strategy_type == "interpolate_round":
        window_size = kwargs.get("window_size", 5)
        return MovingAverageStrategy(
            variable_name, window_size=window_size, round_to_int=True
        )

    # Anomaly correction strategies
    elif strategy_type == "median_filter":
        window_size = kwargs.get("window_size", 5)
        return MedianFilterStrategy(variable_name, window_size=window_size)
    elif strategy_type == "winsorize":
        limits = kwargs.get("limits", (0.05, 0.05))
        return WinsorizeStrategy(variable_name, limits=limits)
    elif strategy_type == "moving_average_correction":
        window_size = kwargs.get("window_size", 5)
        return MovingAverageCorrectionStrategy(variable_name, window_size=window_size)
    elif strategy_type == "bounded_correction":
        min_value = kwargs.get("min_value", var_range[0] if var_range else None)
        max_value = kwargs.get("max_value", var_range[1] if var_range else None)
        return BoundedCorrectionStrategy(
            variable_name, min_value=min_value, max_value=max_value
        )
    elif strategy_type == "moving_average_round":
        window_size = kwargs.get("window_size", 5)
        return MovingAverageCorrectionStrategy(
            variable_name, window_size=window_size, round_to_int=True
        )

    # Smoothing strategies
    elif strategy_type == "rolling_mean":
        window_size = kwargs.get("window_size", 5)
        return RollingMeanStrategy(variable_name, window_size=window_size)
    elif strategy_type == "exponential":
        alpha = kwargs.get("alpha", 0.3)
        return ExponentialSmoothingStrategy(variable_name, alpha=alpha)
    elif strategy_type == "savitzky_golay":
        window_size = kwargs.get("window_size", 5)
        poly_order = kwargs.get("poly_order", 2)
        return SavitzkyGolayStrategy(
            variable_name, window_size=window_size, poly_order=poly_order
        )
    elif strategy_type == "loess":
        frac = kwargs.get("frac", 0.3)
        it = kwargs.get("it", 3)
        return LoessStrategy(variable_name, frac=frac, it=it)
    elif strategy_type == "none":
        return NoSmoothingStrategy(variable_name)

    # Cross-source strategies
    elif strategy_type == "prioritized":
        source_priorities = kwargs.get("source_priorities", None)
        return PrioritizedSourceStrategy(
            variable_name, source_priorities=source_priorities
        )  # source_priorities can be None, handled in __init__
    elif strategy_type == "weighted_average":
        weights = kwargs.get("weights", None)
        return WeightedAverageStrategy(
            variable_name, weights=weights
        )  # weights can be None, handled in __init__
    elif strategy_type == "voting":
        tolerance = kwargs.get("tolerance", 0.01)
        return VotingStrategy(variable_name, tolerance=tolerance)

    # Default
    else:
        logger.warning(
            f"Unknown strategy type: {strategy_type}. Using default linear interpolation."
        )
        return LinearInterpolationStrategy(variable_name)


def save_repair_version(
    variable_name: str,
    original_series: pd.Series,
    repaired_series: pd.Series,
    actions: List[RepairAction],
    version_type: str = "repair",
) -> str:
    """
    Save a repair version to the data store.

    Args:
        variable_name: Name of the variable
        original_series: Original time series data
        repaired_series: Repaired time series data
        actions: List of repair actions
        version_type: Type of version (repair, simulation, original)

    Returns:
        Version ID
    """
    # Create a version ID
    timestamp = dt.datetime.now()
    version_id = f"{version_type}_{timestamp.strftime('%Y%m%d%H%M%S')}"

    # Create version directory
    variable_dir = Path(HISTORICAL_DATA_BASE_DIR) / variable_name
    version_dir = variable_dir / REPAIR_VERSION_DIR
    version_dir.mkdir(parents=True, exist_ok=True)

    # Prepare version data
    version_data = {
        "variable_name": variable_name,
        "version_id": version_id,
        "version_type": version_type,
        "timestamp": timestamp.isoformat(),
        "original_data": {
            "dates": [
                pd.Timestamp(idx).isoformat() for idx in original_series.index
            ],  # Explicitly cast to Timestamp
            "values": original_series.tolist(),
        },
        "repaired_data": {
            "dates": [
                pd.Timestamp(idx).isoformat() for idx in repaired_series.index
            ],  # Explicitly cast to Timestamp
            "values": repaired_series.tolist(),
        },
        "repair_actions": [action.to_dict() for action in actions],
        "total_actions": len(actions),
        "action_types": {
            action_type.value: sum(1 for a in actions if a.action_type == action_type)
            for action_type in RepairActionType
            if sum(1 for a in actions if a.action_type == action_type) > 0
        },
        "action_strategies": {
            strategy.value: sum(1 for a in actions if a.strategy == strategy)
            for strategy in RepairStrategy
            if sum(1 for a in actions if a.strategy == strategy) > 0
        },
    }

    # Save version data
    version_path = version_dir / f"{version_id}.json"
    with open(version_path, "w") as f:
        json.dump(version_data, f, indent=2)

    # Also save data in processed format if it's a repair (not a simulation)
    if version_type == "repair":
        # Create processed data structure
        processed_data = {
            "variable_name": variable_name,
            "values": [
                {
                    "date": pd.Timestamp(idx).isoformat(),
                    "value": float(val),
                }  # Explicitly cast to Timestamp
                for idx, val in repaired_series.items()
                if pd.notna(val)  # Ensure value is not NaN
            ],
            "metadata": {
                "repair_version": version_id,
                "repair_timestamp": timestamp.isoformat(),
                "repair_actions": len(actions),
            },
        }

        # Save as processed data
        timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")
        processed_path = variable_dir / f"{timestamp_str}_processed.json"
        with open(processed_path, "w") as f:
            json.dump(processed_data, f, indent=2)

    return version_id


def repair_variable_data(
    variable_name: str,
    variable_type: str = "raw",
    skip_smoothing: bool = False,
    skip_cross_source: bool = False,
) -> RepairResult:
    """
    Repair data quality issues for a variable.

    Args:
        variable_name: Name of the variable to repair
        variable_type: Type of variable for strategy selection
        skip_smoothing: Whether to skip smoothing step
        skip_cross_source: Whether to skip cross-source reconciliation

    Returns:
        RepairResult object with repair details
    """
    try:
        # Load the data
        series: pd.Series = load_processed_data(variable_name)  # Add type hint
        original_series = series.copy()

        # Perform quality check
        quality_result = perform_quality_check(
            variable_name, variable_type=variable_type
        )
        before_quality = quality_result.quality_score.overall_score

        # No need for repair if quality is already excellent
        if (
            before_quality > 0.95
            and not quality_result.gaps
            and not quality_result.anomalies
        ):
            return RepairResult(
                variable_name=variable_name,
                status="no_repairs_needed",
                before_quality=before_quality,
                after_quality=before_quality,
            )

        # Try to get cross-validation result
        cross_validation_result = None
        if not skip_cross_source:
            try:
                cross_validation_result = cross_validate_sources(variable_name)
                if (
                    not cross_validation_result.sources
                    or len(cross_validation_result.sources) < 2
                ):
                    cross_validation_result = None
            except Exception as e:
                logger.warning(f"Error during cross-validation: {e}")

        # Get optimal repair strategies
        strategies = get_optimal_repair_strategy(
            variable_name,
            quality_result,
            variable_type,
            cross_validation_result=cross_validation_result,  # Explicitly pass as keyword argument
        )

        all_actions = []
        repaired_series: pd.Series = series.copy()  # Add type hint

        # 1. Fill gaps
        if quality_result.gaps:
            gap_strategy = create_repair_strategy(
                strategies["gap_strategy"], variable_name, variable_type
            )
            repaired_series, gap_actions = gap_strategy.repair(
                repaired_series, gaps=quality_result.gaps
            )
            all_actions.extend(gap_actions)

        # 2. Correct anomalies
        if quality_result.anomalies:
            anomaly_strategy = create_repair_strategy(
                strategies["anomaly_strategy"], variable_name, variable_type
            )
            repaired_series, anomaly_actions = anomaly_strategy.repair(
                repaired_series, anomalies=quality_result.anomalies
            )
            all_actions.extend(anomaly_actions)

        # 3. Apply smoothing if needed
        if not skip_smoothing and strategies["smoothing_strategy"] != "none":
            smoothing_strategy = create_repair_strategy(
                strategies["smoothing_strategy"], variable_name
            )
            repaired_series, smoothing_actions = smoothing_strategy.repair(
                repaired_series
            )
            all_actions.extend(smoothing_actions)

        # 4. Apply cross-source reconciliation if available
        if (
            not skip_cross_source
            and cross_validation_result
            and cross_validation_result.sources
        ):
            cross_source_strategy = create_repair_strategy(
                strategies["cross_source_strategy"], variable_name
            )
            # Extract series from cross-validation result
            source_data = cross_validation_result.aligned_datasets
            repaired_series, cross_source_actions = cross_source_strategy.repair(
                repaired_series,
                source_data=source_data,
                original_series=original_series,
            )
            all_actions.extend(cross_source_actions)

        # If no repairs were made, return early
        if not all_actions:
            return RepairResult(
                variable_name=variable_name,
                status="no_repairs_needed",
                before_quality=before_quality,
                after_quality=before_quality,
            )

        # Evaluate the repairs
        after_quality_result = perform_quality_check(
            variable_name,
            variable_type=variable_type,
            _series=repaired_series,  # Pass the repaired series for evaluation - This parameter needs to be added to historical_data_verification.py
        )
        after_quality = after_quality_result.quality_score.overall_score

        # Save the repair version
        version_id = save_repair_version(
            variable_name,
            original_series,
            repaired_series,
            all_actions,
            version_type="repair",
        )

        # Count actions by type
        gap_fills = sum(
            1 for a in all_actions if a.action_type == RepairActionType.GAP_FILL
        )
        anomaly_corrections = sum(
            1
            for a in all_actions
            if a.action_type == RepairActionType.ANOMALY_CORRECTION
        )
        smoothing_actions = sum(
            1 for a in all_actions if a.action_type == RepairActionType.SMOOTHING
        )
        cross_source_actions = sum(
            1 for a in all_actions if a.action_type == RepairActionType.CROSS_SOURCE
        )

        # Create and return the repair result
        return RepairResult(
            variable_name=variable_name,
            status="success",
            version_id=version_id,
            timestamp=dt.datetime.now(),
            total_repairs=len(all_actions),
            gap_fills=gap_fills,
            anomaly_corrections=anomaly_corrections,
            smoothing_actions=smoothing_actions,
            cross_source_actions=cross_source_actions,
            quality_improvement=after_quality - before_quality,
            before_quality=before_quality,
            after_quality=after_quality,
            actions=all_actions,
        )

    except FileNotFoundError:
        logger.error(f"No data found for variable {variable_name}")
        return RepairResult(
            variable_name=variable_name,
            status="error",
            error=f"No data found for variable {variable_name}",
        )
    except Exception as e:
        logger.error(f"Error repairing {variable_name}: {e}")
        return RepairResult(
            variable_name=variable_name,
            status="error",
            error=f"Error during repair: {str(e)}",
        )


def simulate_repair(variable_name: str, variable_type: str = "raw") -> RepairResult:
    """
    Simulate repairs for a variable without applying them.

    Args:
        variable_name: Name of the variable to simulate repairs for
        variable_type: Type of variable for strategy selection

    Returns:
        RepairResult object with simulation details
    """
    try:
        # Load the data
        series: pd.Series = load_processed_data(variable_name)  # Add type hint
        original_series = series.copy()

        # Perform quality check
        quality_result = perform_quality_check(
            variable_name, variable_type=variable_type
        )
        before_quality = quality_result.quality_score.overall_score

        # No need for repair if quality is already excellent
        if (
            before_quality > 0.95
            and not quality_result.gaps
            and not quality_result.anomalies
        ):
            return RepairResult(
                variable_name=variable_name,
                status="no_repairs_needed",
                before_quality=before_quality,
                after_quality=before_quality,
            )

        # Try to get cross-validation result
        cross_validation_result = None
        try:
            cross_validation_result = cross_validate_sources(variable_name)
            if (
                not cross_validation_result.sources
                or len(cross_validation_result.sources) < 2
            ):
                cross_validation_result = None
        except Exception as e:
            logger.warning(f"Error during cross-validation: {e}")

        # Get optimal repair strategies
        strategies = get_optimal_repair_strategy(
            variable_name,
            quality_result,
            variable_type,
            cross_validation_result=cross_validation_result,  # Explicitly pass as keyword argument
        )

        all_actions = []
        simulated_series: pd.Series = series.copy()  # Add type hint

        # 1. Fill gaps
        if quality_result.gaps:
            gap_strategy = create_repair_strategy(
                strategies["gap_strategy"], variable_name, variable_type
            )
            simulated_series, gap_actions = gap_strategy.repair(
                simulated_series, gaps=quality_result.gaps
            )
            all_actions.extend(gap_actions)

        # 2. Correct anomalies
        if quality_result.anomalies:
            anomaly_strategy = create_repair_strategy(
                strategies["anomaly_strategy"], variable_name, variable_type
            )
            simulated_series, anomaly_actions = anomaly_strategy.repair(
                simulated_series, anomalies=quality_result.anomalies
            )
            all_actions.extend(anomaly_actions)

        # 3. Apply smoothing
        if strategies["smoothing_strategy"] != "none":
            smoothing_strategy = create_repair_strategy(
                strategies["smoothing_strategy"], variable_name
            )
            simulated_series, smoothing_actions = smoothing_strategy.repair(
                simulated_series
            )
            all_actions.extend(smoothing_actions)

        # 4. Apply cross-source reconciliation if available
        if cross_validation_result and cross_validation_result.sources:
            cross_source_strategy = create_repair_strategy(
                strategies["cross_source_strategy"], variable_name
            )
            # Extract series from cross-validation result
            source_data = cross_validation_result.aligned_datasets
            simulated_series, cross_source_actions = cross_source_strategy.repair(
                simulated_series,
                source_data=source_data,
                original_series=original_series,
            )
            all_actions.extend(cross_source_actions)

        # If no repairs were simulated, return early
        if not all_actions:
            return RepairResult(
                variable_name=variable_name,
                status="no_repairs_needed",
                before_quality=before_quality,
                after_quality=before_quality,
            )

        # Evaluate the simulated repairs
        after_quality_result = perform_quality_check(
            variable_name,
            variable_type=variable_type,
            _series=simulated_series,  # Pass the simulated series for evaluation - This parameter needs to be added to historical_data_verification.py
        )
        after_quality = after_quality_result.quality_score.overall_score

        # Save the simulation version
        version_id = save_repair_version(
            variable_name,
            original_series,
            simulated_series,
            all_actions,
            version_type="simulation",
        )

        # Count actions by type
        gap_fills = sum(
            1 for a in all_actions if a.action_type == RepairActionType.GAP_FILL
        )
        anomaly_corrections = sum(
            1
            for a in all_actions
            if a.action_type == RepairActionType.ANOMALY_CORRECTION
        )
        smoothing_actions = sum(
            1 for a in all_actions if a.action_type == RepairActionType.SMOOTHING
        )
        cross_source_actions = sum(
            1 for a in all_actions if a.action_type == RepairActionType.CROSS_SOURCE
        )

        # Create and return the repair result
        return RepairResult(
            variable_name=variable_name,
            status="success",
            version_id=version_id,
            timestamp=dt.datetime.now(),
            total_repairs=len(all_actions),
            gap_fills=gap_fills,
            anomaly_corrections=anomaly_corrections,
            smoothing_actions=smoothing_actions,
            cross_source_actions=cross_source_actions,
            quality_improvement=after_quality - before_quality,
            before_quality=before_quality,
            after_quality=after_quality,
            actions=all_actions,
        )

    except FileNotFoundError:
        logger.error(f"No data found for variable {variable_name}")
        return RepairResult(
            variable_name=variable_name,
            status="error",
            error=f"No data found for variable {variable_name}",
        )
    except Exception as e:
        logger.error(f"Error simulating repairs for {variable_name}: {e}")
        return RepairResult(
            variable_name=variable_name,
            status="error",
            error=f"Error during simulation: {str(e)}",
        )


def get_repair_report(
    variable_name: str, version_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a report of repairs made for a variable.

    Args:
        variable_name: Name of the variable
        version_id: Optional Version ID (if None, gets the latest version)

    Returns:
        Dictionary with repair details
    """
    try:
        # Find the repair version file
        variable_dir = Path(HISTORICAL_DATA_BASE_DIR) / variable_name
        version_dir = variable_dir / REPAIR_VERSION_DIR

        if not version_dir.exists():
            return {
                "status": "no_versions",
                "message": f"No repair versions found for {variable_name}",
            }

        # Find the version file
        if version_id:
            version_path = version_dir / f"{version_id}.json"
            if not version_path.exists():
                return {
                    "status": "version_not_found",
                    "message": f"Version {version_id} not found for {variable_name}",
                }
        else:
            # Find the latest version
            version_files = list(version_dir.glob("repair_*.json"))
            if not version_files:
                return {
                    "status": "no_versions",
                    "message": f"No repair versions found for {variable_name}",
                }

            # Sort by modification time (newest first)
            version_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            version_path = version_files[0]

        # Load the version data
        with open(version_path, "r") as f:
            version_data = json.load(f)

        # Extract report information
        report = {
            "status": "success",
            "variable_name": variable_name,
            "version_id": version_data.get("version_id", "unknown"),
            "version_type": version_data.get("version_type", "repair"),
            "timestamp": version_data.get("timestamp", ""),
            "total_actions": version_data.get("total_actions", 0),
            "action_types": version_data.get("action_types", {}),
            "action_strategies": version_data.get("action_strategies", {}),
        }

        # Add detailed repair actions
        if "repair_actions" in version_data:
            report["actions"] = version_data["repair_actions"]

        return report

    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"No data found for variable {variable_name}",
        }
    except Exception as e:
        logger.error(f"Error getting repair report: {e}")
        return {"status": "error", "message": f"Error getting repair report: {str(e)}"}


def repair_multiple_variables(
    variable_names: List[str], variable_type: str = "raw"
) -> Dict[str, RepairResult]:
    """
    Repair multiple variables.

    Args:
        variable_names: List of variable names to repair
        variable_type: Type of variable for strategy selection

    Returns:
        Dictionary mapping variable names to RepairResult objects
    """
    results = {}

    for variable_name in variable_names:
        try:
            logger.info(f"Repairing {variable_name}")
            result = repair_variable_data(variable_name, variable_type)
            results[variable_name] = result
        except Exception as e:
            logger.error(f"Error repairing {variable_name}: {e}")
            results[variable_name] = RepairResult(
                variable_name=variable_name,
                status="error",
                error=f"Error during repair: {str(e)}",
            )

    return results


def revert_to_original(
    variable_name: str, version_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Revert a variable to its original (pre-repair) state.

    Args:
        variable_name: Name of the variable
        version_id: Optional Version ID to revert from (if None, uses the latest version)

    Returns:
        Dictionary with revert details
    """
    try:
        # Find the repair version file
        variable_dir = Path(HISTORICAL_DATA_BASE_DIR) / variable_name
        version_dir = variable_dir / REPAIR_VERSION_DIR

        if not version_dir.exists():
            return {
                "status": "no_versions",
                "message": f"No repair versions found for {variable_name}",
            }

        # Find the version file
        if version_id:
            version_path = version_dir / f"{version_id}.json"
            if not version_path.exists():
                return {
                    "status": "version_not_found",
                    "message": f"Version {version_id} not found for {variable_name}",
                }
        else:
            # Find the latest version
            version_files = list(version_dir.glob("repair_*.json"))
            if not version_files:
                return {
                    "status": "no_versions",
                    "message": f"No repair versions found for {variable_name}",
                }

            # Sort by modification time (newest first)
            version_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            version_path = version_files[0]

        # Load the version data
        with open(version_path, "r") as f:
            version_data = json.load(f)

        # Extract the original data
        if "original_data" not in version_data:
            return {
                "status": "error",
                "message": f"No original data found in version {version_data.get('version_id', 'unknown')}",
            }

        # Create a Series from the original data
        dates = [
            pd.Timestamp(date_str)
            for date_str in version_data["original_data"]["dates"]
        ]
        values = version_data["original_data"]["values"]

        original_series = pd.Series(
            values, index=dates, dtype=float
        )  # Ensure float dtype

        # Save as a new processed file
        timestamp = dt.datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")

        # Create processed data structure
        processed_data = {
            "variable_name": variable_name,
            "values": [
                {
                    "date": pd.Timestamp(idx).isoformat(),
                    "value": float(val),
                }  # Explicitly cast to Timestamp
                for idx, val in original_series.items()
                if pd.notna(val)  # Ensure value is not NaN
            ],
            "metadata": {
                "reverted_from": version_data.get("version_id", "unknown"),
                "revert_timestamp": timestamp.isoformat(),
            },
        }

        # Save as processed data
        processed_path = variable_dir / f"{timestamp_str}_processed.json"
        with open(processed_path, "w") as f:
            json.dump(processed_data, f, indent=2)

        return {
            "status": "success",
            "variable_name": variable_name,
            "version_id": version_data.get("version_id", "unknown"),
            "timestamp": timestamp.isoformat(),
            "message": f"Successfully reverted {variable_name} to original state",
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"No data found for variable {variable_name}",
        }
    except Exception as e:
        logger.error(f"Error reverting {variable_name}: {e}")
        return {"status": "error", "message": f"Error during revert: {str(e)}"}


def compare_versions(
    variable_name: str, version_id1: str, version_id2: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare two versions of a variable.

    Args:
        variable_name: Name of the variable
        version_id1: First version ID
        version_id2: Optional Second version ID (if None, uses the latest repaired version)

    Returns:
        Dictionary with comparison details
    """
    try:
        # Find the repair version directory
        variable_dir = Path(HISTORICAL_DATA_BASE_DIR) / variable_name
        version_dir = variable_dir / REPAIR_VERSION_DIR

        if not version_dir.exists():
            return {
                "status": "no_versions",
                "message": f"No repair versions found for {variable_name}",
            }

        # Find the first version file
        version1_path = version_dir / f"{version_id1}.json"
        if not version1_path.exists():
            return {
                "status": "version_not_found",
                "message": f"Version {version_id1} not found for {variable_name}",
            }

        # Find the second version file
        if version_id2:
            version2_path = version_dir / f"{version_id2}.json"
            if not version2_path.exists():
                return {
                    "status": "version_not_found",
                    "message": f"Version {version_id2} not found for {variable_name}",
                }
        else:
            # Find the latest repaired version
            version_files = list(version_dir.glob("repair_*.json"))
            if not version_files:
                return {
                    "status": "no_versions",
                    "message": f"No repair versions found for {variable_name}",
                }

            # Sort by modification time (newest first)
            version_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            version2_path = version_files[0]

        # Load the version data
        with open(version1_path, "r") as f:
            version1_data = json.load(f)

        with open(version2_path, "r") as f:
            version2_data = json.load(f)

        # Extract the data series
        dates1 = [
            pd.Timestamp(date_str)
            for date_str in version1_data["repaired_data"]["dates"]
        ]
        values1 = version1_data["repaired_data"]["values"]

        dates2 = [
            pd.Timestamp(date_str)
            for date_str in version2_data["repaired_data"]["dates"]
        ]
        values2 = version2_data["repaired_data"]["values"]

        series1: pd.Series[float] = pd.Series(
            values1, index=dates1, dtype=float
        )  # Add type hint and ensure float dtype
        series2: pd.Series[float] = pd.Series(
            values2, index=dates2, dtype=float
        )  # Add type hint and ensure float dtype

        # Compute comparison metrics
        # Ensure indices are DatetimeIndex for intersection
        common_dates = pd.DatetimeIndex(series1.index).intersection(
            pd.DatetimeIndex(series2.index)
        )

        comparison = {
            "status": "success",
            "variable_name": variable_name,
            "version_id1": version1_data.get("version_id", "unknown"),
            "version_id2": version2_data.get("version_id", "unknown"),
            "version1_type": version1_data.get("version_type", "unknown"),
            "version2_type": version2_data.get("version_type", "unknown"),
            "points_in_version1": len(series1),
            "points_in_version2": len(series2),
            "common_points": len(common_dates),
            "version1_only": len(series1) - len(common_dates),
            "version2_only": len(series2) - len(common_dates),
        }

        if len(common_dates) > 0:
            # Calculate differences for common dates
            values1_common = series1.loc[common_dates]
            values2_common = series2.loc[common_dates]

            differences = values1_common - values2_common

            # Compute difference statistics
            comparison["diff_stats"] = {
                "mean_difference": float(differences.mean()),
                "median_difference": float(differences.median()),
                "std_difference": float(differences.std()),
                "max_difference": float(differences.abs().max()),
                "min_difference": float(differences.abs().min()),
                "num_differences": int(sum(differences != 0)),
            }

        return comparison

    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"No data found for variable {variable_name}",
        }
    except Exception as e:
        logger.error(f"Error comparing versions: {e}")
        return {"status": "error", "message": f"Error during comparison: {str(e)}"}


def get_all_versions(variable_name: str) -> Dict[str, Any]:
    """
    Get a list of all repair versions for a variable.

    Args:
        variable_name: Name of the variable

    Returns:
        Dictionary with version details
    """
    try:
        # Find the repair version directory
        variable_dir = Path(HISTORICAL_DATA_BASE_DIR) / variable_name
        version_dir = variable_dir / REPAIR_VERSION_DIR

        if not version_dir.exists():
            return {
                "status": "no_versions",
                "message": f"No repair versions found for {variable_name}",
            }

        # Find all version files
        version_files = list(version_dir.glob("*.json"))
        if not version_files:
            return {
                "status": "no_versions",
                "message": f"No repair versions found for {variable_name}",
            }

        # Sort by modification time (newest first)
        version_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Extract basic info from each version
        versions = []

        for version_path in version_files:
            try:
                with open(version_path, "r") as f:
                    version_data = json.load(f)

                version_info = {
                    "version_id": version_data.get("version_id", "unknown"),
                    "version_type": version_data.get("version_type", "unknown"),
                    "timestamp": version_data.get("timestamp", ""),
                    "total_actions": version_data.get("total_actions", 0),
                    "action_types": version_data.get("action_types", {}),
                }

                versions.append(version_info)
            except Exception as e:
                logger.warning(f"Error reading version file {version_path}: {e}")

        return {
            "status": "success",
            "variable_name": variable_name,
            "versions": versions,
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"No data found for variable {variable_name}",
        }
    except Exception as e:
        logger.error(f"Error getting versions: {e}")
        return {"status": "error", "message": f"Error getting versions: {str(e)}"}


if __name__ == "__main__":
    # Simple CLI for testing
    import argparse

    parser = argparse.ArgumentParser(
        description="Test the historical data repair module"
    )
    parser.add_argument(
        "--variable", type=str, required=True, help="Variable name to repair"
    )
    parser.add_argument(
        "--action",
        type=str,
        choices=["repair", "simulate", "report", "revert", "compare", "versions"],
        default="repair",
        help="Action to perform",
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=list(DEFAULT_REPAIR_STRATEGIES.keys()),
        default="raw",
        help="Variable type for repair strategies",
    )
    parser.add_argument(
        "--version", type=str, help="Version ID for report/revert/compare"
    )
    parser.add_argument("--version2", type=str, help="Second version ID for compare")

    args = parser.parse_args()

    if args.action == "repair":
        result = repair_variable_data(args.variable, args.type)
        print(json.dumps(result.to_dict(), indent=2))
    elif args.action == "simulate":
        result = simulate_repair(args.variable, args.type)
        print(json.dumps(result.to_dict(), indent=2))
    elif args.action == "report":
        result = get_repair_report(args.variable, args.version)
        print(json.dumps(result, indent=2))
    elif args.action == "revert":
        result = revert_to_original(args.variable, args.version)
        print(json.dumps(result, indent=2))
    elif args.action == "compare":
        result = compare_versions(args.variable, args.version, args.version2)
        print(json.dumps(result, indent=2))
    elif args.action == "versions":
        result = get_all_versions(args.variable)
        print(json.dumps(result, indent=2))
