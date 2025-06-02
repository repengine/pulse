#!/usr/bin/env python3
"""
Historical Data Verification Example

This script demonstrates the enhanced data verification capabilities
by creating synthetic data with known issues (gaps, anomalies, trend breaks)
and then running the verification tools on it.
"""

from ingestion.iris_utils.historical_data_verification import (
    perform_quality_check,
    detect_anomalies,
    cross_validate_sources,
    analyze_gaps,
    visualize_data_quality,
    HISTORICAL_DATA_BASE_DIR,
)
import os
import sys
import json
import datetime as dt
import numpy as np
import pandas as pd
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the verification modules


def create_synthetic_dataset(variable_name, start_date, end_date, with_issues=True):
    """
    Create a synthetic time series dataset for demonstration purposes.

    Args:
        variable_name: Name of the variable
        start_date: Start date for the time series
        end_date: End date for the time series
        with_issues: Whether to include data quality issues

    Returns:
        pandas Series with the synthetic data
    """
    # Create a date range with daily frequency
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")

    # Create base data - sine wave + linear trend
    t = np.arange(len(date_range))
    base_data = 100 + 0.05 * t + 10 * np.sin(2 * np.pi * t / 365.25)

    # Add noise
    np.random.seed(42)  # For reproducibility
    noise = np.random.normal(0, 1, len(date_range))
    data = base_data + noise

    # Create a pandas Series
    series = pd.Series(data, index=date_range)
    series.name = variable_name

    if with_issues:
        # Add some anomalies
        # Spike anomalies
        for i in range(5):
            anomaly_idx = np.random.randint(0, len(series))
            series.iloc[anomaly_idx] += np.random.choice([1, -1]) * np.random.uniform(
                15, 30
            )

        # Add a trend break
        trend_break_idx = len(series) // 2
        series.iloc[trend_break_idx:] += 5

        # Add some gaps (remove some data points)
        gap_indices = []
        # Small gap
        gap_start = np.random.randint(30, 60)
        gap_end = gap_start + np.random.randint(3, 7)
        gap_indices.extend(range(gap_start, gap_end))

        # Larger gap
        gap_start = np.random.randint(180, 240)
        gap_end = gap_start + np.random.randint(10, 20)
        gap_indices.extend(range(gap_start, gap_end))

        # Weekend gaps pattern
        for i in range(len(series)):
            if date_range[i].dayofweek in [5, 6]:  # Saturday or Sunday
                if np.random.random() < 0.7:  # 70% chance of missing weekend data
                    gap_indices.append(i)

        # Remove the selected indices
        series = series.drop(series.index[gap_indices])

    return series


def save_variable_to_catalog(variable_name, variable_type="price", priority=1):
    """
    Add the variable to the catalog file.

    Args:
        variable_name: Name of the variable
        variable_type: Type of variable
        priority: Priority level
    """
    catalog_path = Path(HISTORICAL_DATA_BASE_DIR) / "variable_catalog.json"

    if catalog_path.exists():
        with open(catalog_path, "r") as f:
            catalog = json.load(f)
    else:
        # Create a new catalog
        catalog = {
            "version": "1.0",
            "last_updated": dt.datetime.now().isoformat(),
            "variables": [],
        }

    # Check if variable already exists
    for var in catalog["variables"]:
        if var["variable_name"] == variable_name:
            return  # Variable already in catalog

    # Add the variable
    catalog["variables"].append(
        {
            "variable_name": variable_name,
            "source": "synthetic",
            "category": "example",
            "type": variable_type,
            "priority": priority,
            "frequency": "D",
            "description": f"Synthetic {variable_name} data for verification example",
        }
    )

    # Make sure the directory exists
    catalog_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the updated catalog
    with open(catalog_path, "w") as f:
        json.dump(catalog, f, indent=2)


def save_variable_data(variable_name, series):
    """
    Save the synthetic data in the appropriate format.

    Args:
        variable_name: Name of the variable
        series: pandas Series with time series data
    """
    # Create variable directory
    variable_dir = Path(HISTORICAL_DATA_BASE_DIR) / variable_name
    variable_dir.mkdir(parents=True, exist_ok=True)

    # Format the data for saving
    data = {
        "variable_name": variable_name,
        "source": "synthetic",
        "last_updated": dt.datetime.now().isoformat(),
        "values": [],
    }

    # Add each data point
    for timestamp, value in series.items():
        data["values"].append({"date": timestamp.isoformat(), "value": float(value)})

    # Create a filename with timestamp
    timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{variable_name}_{timestamp}_processed.json"

    # Save the data
    with open(variable_dir / filename, "w") as f:
        json.dump(data, f, indent=2)

    return variable_dir / filename


def create_multiple_sources(variable_name, base_series):
    """
    Create multiple data sources for the same variable with slight differences.

    Args:
        variable_name: Base name of the variable
        base_series: Base time series data

    Returns:
        Dictionary mapping source names to time series
    """
    sources = {}

    # Source 1: Base data with some missing points
    source1_name = f"{variable_name}_source1"
    source1_data = base_series.copy()
    drop_indices = np.random.choice(
        range(len(source1_data)), size=len(source1_data) // 10, replace=False
    )
    source1_data = source1_data.drop(source1_data.index[drop_indices])
    source1_data.name = source1_name
    sources[source1_name] = source1_data

    # Source 2: Slightly different values (systematic difference)
    source2_name = f"{variable_name}_source2"
    source2_data = base_series * 1.02  # 2% higher
    source2_data.name = source2_name
    sources[source2_name] = source2_data

    # Source 3: More noise
    source3_name = f"{variable_name}_source3"
    source3_data = base_series + np.random.normal(0, 2, len(base_series))
    source3_data.name = source3_name
    sources[source3_name] = source3_data

    return sources


def run_verification_demo():
    """Run the complete verification demonstration."""
    print("Historical Data Verification Demo")
    print("=================================")

    # 1. Create synthetic data
    print("\n1. Creating synthetic data...")
    variable_name = "demo_stock_price"
    start_date = "2020-01-01"
    end_date = "2022-12-31"

    series = create_synthetic_dataset(variable_name, start_date, end_date)

    # 2. Save the variable to the catalog
    print("\n2. Adding variable to catalog...")
    save_variable_to_catalog(variable_name, variable_type="price", priority=1)

    # 3. Save the processed data
    print("\n3. Saving processed data...")
    data_file = save_variable_data(variable_name, series)
    print(f"   Data saved to: {data_file}")

    # 4. Create multiple sources for cross-validation
    print("\n4. Creating multiple data sources for cross-validation...")
    sources = create_multiple_sources("cross_demo", series)

    for source_name, source_data in sources.items():
        save_variable_to_catalog(source_name, variable_type="price", priority=2)
        source_file = save_variable_data(source_name, source_data)
        print(f"   {source_name} saved to: {source_file}")

    # 5. Run quality check
    print("\n5. Running quality check...")
    quality_result = perform_quality_check(variable_name)

    print(f"\nQuality Check Results for {variable_name}:")
    print(f"Overall quality score: {quality_result.quality_score.overall_score:.2f}")
    print(f"Completeness: {quality_result.quality_score.completeness:.2f}")
    print(f"Consistency: {quality_result.quality_score.consistency:.2f}")
    print(f"Anomaly-free: {quality_result.quality_score.anomaly_free:.2f}")
    print(f"Time continuity: {quality_result.quality_score.time_continuity:.2f}")
    print(f"Trend stability: {quality_result.quality_score.trend_stability:.2f}")
    print(f"Seasonality: {quality_result.quality_score.seasonality:.2f}")

    if quality_result.anomalies:
        print(f"\nDetected {len(quality_result.anomalies)} anomalies:")
        for i, anomaly in enumerate(quality_result.anomalies[:5]):  # Show first 5
            print(
                f"  {i + 1}. {anomaly.timestamp.date()}: value={anomaly.value:.2f}, "
                + f"severity={anomaly.severity:.2f}, method={anomaly.method}"
            )

    if quality_result.gaps:
        print(f"\nDetected {len(quality_result.gaps)} gaps:")
        for i, gap in enumerate(quality_result.gaps[:5]):  # Show first 5
            print(
                f"  {i + 1}. {gap.start_time.date()} to {gap.end_time.date()}: "
                + f"{gap.gap_duration.days} days, {gap.expected_points} points"
            )

    if quality_result.trend_breaks:
        print(f"\nDetected {len(quality_result.trend_breaks)} trend breaks:")
        for i, break_ in enumerate(quality_result.trend_breaks):
            print(
                f"  {
                    i +
                    1}. {
                    break_.timestamp.date()}: Before={
                    break_.before_trend:.2f}, " +
                f"After={
                    break_.after_trend:.2f}, Magnitude={
                        break_.change_magnitude:.2f}")

    # 6. Run anomaly detection with different methods
    print("\n6. Running anomaly detection with different methods...")
    methods = ["zscore", "iqr", "isolation_forest"]

    for method in methods:
        try:
            anomalies = detect_anomalies(series, method=method)
            print(f"\n{method.upper()} method detected {len(anomalies)} anomalies:")
            for i, anomaly in enumerate(
                sorted(anomalies, key=lambda a: a.severity, reverse=True)[:3]
            ):
                print(
                    f"  {
                        i +
                        1}. {
                        anomaly.timestamp.date()}: value={
                        anomaly.value:.2f}, " +
                    f"severity={
                        anomaly.severity:.2f}")
        except Exception as e:
            print(f"Error with {method} method: {e}")

    # 7. Run gap analysis
    print("\n7. Running gap analysis...")
    try:
        gap_result = analyze_gaps(
            variable_name, freq="D"
        )  # Explicitly use 'D' for daily frequency

        print("Gap analysis results:")
        if "error" not in gap_result:
            print(f"Total gaps: {gap_result.get('total_gaps', 0)}")
            print(f"Total gap days: {gap_result.get('total_gap_days', 0)}")
            print(f"Data completeness: {gap_result.get('completeness', 0):.2%}")
            if (
                "gap_patterns" in gap_result
                and "possible_pattern" in gap_result["gap_patterns"]
            ):
                print(f"Gap pattern: {gap_result['gap_patterns']['possible_pattern']}")
            else:
                print("Gap pattern: Unknown")
        else:
            print(f"Error: {gap_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"Error in gap analysis: {e}")

    # 8. Run cross-source validation
    print("\n8. Running cross-source validation...")
    try:
        # For this to work, we need to add an alias to one of the sources in the catalog
        # Quick hack: add the original variable as an alias to one of the sources
        update_catalog_for_cross_validation("cross_demo_source1", "cross_demo")

        cross_result = cross_validate_sources("cross_demo")

        print("Cross-validation results:")
        print(f"Sources: {', '.join(cross_result.sources)}")

        print("Correlation matrix:")
        for source1 in cross_result.sources:
            for source2 in cross_result.sources:
                if source1 != source2:
                    corr = cross_result.correlation_matrix[source1][source2]
                    print(f"  {source1} vs {source2}: {corr:.3f}")

        print(f"Recommendation: {cross_result.recommendation}")
    except Exception as e:
        print(f"Error in cross-validation: {e}")

    # 9. Generate visualizations
    print("\n9. Generating visualizations...")
    vis_paths = visualize_data_quality(variable_name)

    print("Visualizations saved to:")
    for vis_type, path in vis_paths.items():
        print(f"  {vis_type}: {path}")

    print("\nDemo complete!")
    return quality_result


def update_catalog_for_cross_validation(source_name, alias):
    """Update the catalog to add an alias to a source for cross-validation demo."""
    catalog_path = Path(HISTORICAL_DATA_BASE_DIR) / "variable_catalog.json"

    if catalog_path.exists():
        with open(catalog_path, "r") as f:
            catalog = json.load(f)

        # Find the source and add the alias
        for var in catalog["variables"]:
            if var["variable_name"] == source_name:
                var["alias"] = alias
                break

        # Save the updated catalog
        with open(catalog_path, "w") as f:
            json.dump(catalog, f, indent=2)


if __name__ == "__main__":
    try:
        # Run the demo
        result = run_verification_demo()

        # Open the visualizations if available
        try:
            vis_paths = visualize_data_quality(result.variable_name)
            if "time_series" in vis_paths:
                # Try to display the image if running in a notebook or with a GUI
                try:
                    # Use PIL instead of IPython for broader compatibility
                    import os

                    print(f"\nVisualization saved to: {vis_paths['time_series']}")
                    if os.name == "nt":
                        os.system(f"start {vis_paths['time_series']}")
                    else:
                        os.system(f"open {vis_paths['time_series']}")
                except Exception as e:
                    print(f"Could not open visualization: {e}")
        except Exception as e:
            print(f"Error generating visualizations: {e}")
    except Exception as e:
        print(f"Error in demo: {e}")
