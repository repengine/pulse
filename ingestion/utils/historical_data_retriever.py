"""ingestion.iris_utils.historical_data_retriever
===========================================

A module for retrieving historical data for variables in the
historical timeline variable catalog.

This module provides functionality to:
1. Retrieve historical data for specific variables or all priority 1 variables
2. Customize the date range for data retrieval
3. Handle API rate limits with exponential backoff and retries
4. Verify data quality and completeness
5. Store retrieved data using the ingestion_persistence module

Usage:
------
```python
from ingestion.utils.historical_data_retriever import (
    retrieve_historical_data,
    retrieve_priority_variables,
    verify_retrieved_data
)

# Retrieve data for a specific variable
data = retrieve_historical_data("spx_close")

# Retrieve data for all priority 1 variables
priority_data = retrieve_priority_variables()

# Verify the completeness of retrieved data
verification_report = verify_retrieved_data(data)
```

The module also provides a command-line interface:
```
python -m ingestion.iris_utils.historical_data_retriever --variable spx_close
python -m ingestion.iris_utils.historical_data_retriever --priority 1
python -m ingestion.iris_utils.historical_data_retriever --all
```
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
import yfinance as yf
from fredapi import Fred

from ingestion.utils.ingestion_persistence import (
    ensure_data_directory,
    save_api_response,
    save_processed_data,
    save_request_metadata,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Default settings
DEFAULT_YEARS = 5
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_BASE_DELAY = 2  # seconds
DEFAULT_RATE_LIMIT_DELAY = 1  # seconds
VARIABLE_CATALOG_PATH = "data/historical_timeline/variable_catalog.json"
HISTORICAL_DATA_BASE_DIR = "data/historical_timeline/historical_data"

# Initialize FRED client
FRED_KEY = os.getenv("FRED_API_KEY", "")
_FRED = Fred(api_key=FRED_KEY) if FRED_KEY else None


@dataclass
class RetrievalStats:
    """Statistics about retrieved data."""

    variable_name: str
    source: str
    start_date: dt.datetime
    end_date: dt.datetime
    data_point_count: int
    min_value: float
    max_value: float
    mean_value: float
    median_value: float
    completeness_pct: float
    gaps: List[Tuple[dt.datetime, dt.datetime]]
    anomalies: List[Tuple[dt.datetime, float]]


def load_variable_catalog() -> Dict[str, Any]:
    """Load the variable catalog from the default location."""
    catalog_path = Path(VARIABLE_CATALOG_PATH)
    if not catalog_path.exists():
        raise FileNotFoundError(f"Variable catalog not found at {catalog_path}")

    with open(catalog_path, "r") as f:
        return json.load(f)


def get_priority_variables(priority_level: int = 1) -> List[Dict[str, Any]]:
    """Get variables with specified priority level from the catalog."""
    catalog = load_variable_catalog()
    return [
        var for var in catalog["variables"] if var.get("priority") == priority_level
    ]


def retry_with_backoff(func):
    """Decorator for retrying API calls with exponential backoff."""

    def wrapper(*args, **kwargs):
        max_attempts = kwargs.pop("max_attempts", DEFAULT_RETRY_ATTEMPTS)
        base_delay = kwargs.pop("base_delay", DEFAULT_RETRY_BASE_DELAY)

        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except (requests.RequestException, Exception) as e:
                if attempt == max_attempts:
                    logger.error(f"Max retry attempts reached. Last error: {e}")
                    raise

                # Calculate backoff delay with jitter
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                logger.warning(
                    f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f} seconds..."
                )
                time.sleep(delay)

    return wrapper


@retry_with_backoff
def fetch_fred_data(
    series_id: str, start_date: dt.datetime, end_date: dt.datetime
) -> pd.Series:
    """Fetch data from FRED with retries and backoff."""
    if _FRED is None:
        raise ValueError(
            "FRED API key not set. Set the FRED_API_KEY environment variable."
        )

    logger.info(
        f"Fetching FRED data for series {series_id} from {
            start_date.date()} to {
            end_date.date()}")
    data = _FRED.get_series(series_id, start_date, end_date)

    if data is None or data.empty:
        raise ValueError(f"No data returned for FRED series {series_id}")

    return data


@retry_with_backoff
def fetch_yahoo_finance_data(
    ticker: str, start_date: dt.datetime, end_date: dt.datetime
) -> pd.DataFrame:
    """Fetch data from Yahoo Finance with retries and backoff."""
    logger.info(
        f"Fetching Yahoo Finance data for ticker {ticker} from {
            start_date.date()} to {
            end_date.date()}")

    # yfinance download end date is exclusive, so add a day
    data = yf.download(
        ticker,
        start=start_date.strftime("%Y-%m-%d"),
        end=(end_date + dt.timedelta(days=1)).strftime("%Y-%m-%d"),
        progress=False,
    )

    if data is None or data.empty:
        raise ValueError(f"No data returned for Yahoo Finance ticker {ticker}")

    return data


def get_date_range(
    years: int = DEFAULT_YEARS, end_date: Optional[dt.datetime] = None
) -> Tuple[dt.datetime, dt.datetime]:
    """
    Calculate the date range for data retrieval.

    Args:
        years: Number of years to look back from end_date
        end_date: End date for the range (defaults to today)

    Returns:
        Tuple of (start_date, end_date)
    """
    if end_date is None:
        end_date = dt.datetime.now()

    # Ensure end_date is timezone-naive for consistent calculations
    if end_date.tzinfo is not None:
        end_date = end_date.replace(tzinfo=None)

    start_date = end_date - dt.timedelta(days=years * 365)  # Approximate years

    return start_date, end_date


def retrieve_historical_data(
    variable_info: Dict[str, Any],
    years: int = DEFAULT_YEARS,
    end_date: Optional[dt.datetime] = None,
    rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY,
) -> Dict[str, Any]:
    """
    Retrieve historical data for a specific variable.

    Args:
        variable_info: Dictionary containing variable information from the catalog
        years: Number of years to look back from end_date
        end_date: End date for data retrieval (defaults to today)
        rate_limit_delay: Delay between API calls to respect rate limits

    Returns:
        Dictionary containing:
        - variable_info: Original variable information
        - data: Retrieved data
        - stats: Statistics about the retrieved data
    """
    variable_name = variable_info["variable_name"]
    source = variable_info["source"]
    api_endpoint = variable_info["api_endpoint"]
    required_parameters = variable_info.get("required_parameters", {})

    logger.info(f"Retrieving historical data for {variable_name} from {source}")

    # Calculate date range
    start_date, end_date = get_date_range(years, end_date)

    # Create data directory for this variable
    ensure_data_directory(f"historical_timeline/{variable_name}", base_dir="data")

    # Save request metadata
    request_params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "years": years,
        **required_parameters,
    }

    save_request_metadata(
        variable_name,
        request_params,
        source_name=source,
        base_dir="data/historical_timeline",
    )

    data = None
    raw_data = None

    try:
        if source == "historical_ingestion_plugin":
            source_type = required_parameters.get("source")

            if source_type == "FRED":
                # Fetch FRED data
                raw_data = fetch_fred_data(api_endpoint, start_date, end_date)

                # Apply any transform if specified
                transform = required_parameters.get("transform")
                if transform and transform.startswith("divide by"):
                    divisor = float(transform.split("divide by ")[1])
                    data = raw_data / divisor
                else:
                    data = raw_data

                # Save the raw API response - convert to JSON-serializable format
                # For Series (FRED data is a Series, not a DataFrame)
                serializable_data = {
                    "dates": [str(date) for date in raw_data.index],
                    "values": raw_data.values.tolist(),
                }

                save_api_response(
                    f"{variable_name}_raw",
                    serializable_data,
                    source_name=source,
                    base_dir="data/historical_timeline",
                )

            elif source_type == "YahooFinance":
                # Fetch Yahoo Finance data
                raw_data = fetch_yahoo_finance_data(api_endpoint, start_date, end_date)

                # Extract close prices
                data = raw_data["Close"]

                # Save the raw API response - convert to JSON-serializable format
                # Convert pandas Series to a list of date-value pairs
                serializable_data = {
                    "dates": [str(date) for date in raw_data.index],
                    "values": raw_data.values.tolist(),
                }

                save_api_response(
                    f"{variable_name}_raw",
                    serializable_data,
                    source_name=source,
                    base_dir="data/historical_timeline",
                )

            else:
                raise ValueError(f"Unsupported source type: {source_type}")

        else:
            raise ValueError(f"Unsupported source: {source}")

        # Verify and process the data
        stats = analyze_data(variable_name, data, start_date, end_date)

        # Convert data to a more suitable format for storage
        processed_data = {
            "variable_name": variable_name,
            "source": source,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "values": [],
        }

        # Special handling for Yahoo Finance data (which is what we need for spx_close)
        if source_type == "YahooFinance":
            logger.info(
                f"Processing Yahoo Finance data with {
                    len(data)} rows for {variable_name}")

            # Convert the Series to a list of tuples for safer iteration
            data_items = [(idx, val) for idx, val in zip(data.index, data.values)]

            # Now iterate over the safe list
            for date_idx, value in data_items:
                try:
                    # Convert date to string (Yahoo Finance uses datetime index)
                    if isinstance(date_idx, (dt.datetime, pd.Timestamp)):
                        date_str = date_idx.isoformat()
                    else:
                        date_str = str(date_idx)

                    # Process the float value (Yahoo Finance Close prices are floats)
                    if pd.notna(value):  # Check for NaN
                        processed_data["values"].append(
                            {"date": date_str, "value": float(value)}
                        )
                    else:
                        logger.warning(
                            f"Skipping NaN value for {variable_name} at {date_str}"
                        )
                except Exception as e:
                    logger.warning(f"Error processing Yahoo Finance data point: {e}")

        # Handle FRED data
        elif source_type == "FRED":
            logger.info(f"Processing FRED data for {variable_name}")

            # Convert FRED Series to list of tuples for safer iteration
            if isinstance(data, pd.Series):
                data_items = [(idx, val) for idx, val in zip(data.index, data.values)]

                # Process each data point
                for date_idx, value in data_items:
                    try:
                        # Format the date
                        date_str = (
                            date_idx.isoformat()
                            if hasattr(date_idx, "isoformat")
                            else str(date_idx)
                        )

                        # Process the value
                        if pd.notna(value):
                            processed_data["values"].append(
                                {"date": date_str, "value": float(value)}
                            )
                    except Exception as e:
                        logger.warning(f"Error processing FRED data point: {e}")
            else:
                logger.warning(
                    f"FRED data for {variable_name} is not a pandas Series as expected"
                )

        # Fallback for other data types
        else:
            logger.warning(
                f"Unsupported data format for {variable_name}. No values processed."
            )

        # Save the processed data
        save_processed_data(
            variable_name,
            processed_data,
            source_name=source,
            base_dir="data/historical_timeline",
            metadata={
                "retrieval_stats": {
                    "data_point_count": stats.data_point_count,
                    "min_value": stats.min_value,
                    "max_value": stats.max_value,
                    "mean_value": stats.mean_value,
                    "median_value": stats.median_value,
                    "completeness_pct": stats.completeness_pct,
                    "gaps_count": len(stats.gaps),
                    "anomalies_count": len(stats.anomalies),
                }
            },
        )

        logger.info(f"Successfully retrieved and stored data for {variable_name}")
        logger.info(
            f"Data points: {
                stats.data_point_count}, Completeness: {
                stats.completeness_pct:.2f}%")

        if stats.gaps:
            logger.warning(f"Found {len(stats.gaps)} gaps in data for {variable_name}")

        if stats.anomalies:
            logger.warning(
                f"Found {len(stats.anomalies)} anomalies in data for {variable_name}"
            )

        # Respect rate limits
        time.sleep(rate_limit_delay)

        return {
            "variable_info": variable_info,
            "data": processed_data,
            "stats": vars(stats),
        }

    except Exception as e:
        logger.error(f"Error retrieving data for {variable_name}: {e}")
        raise


def analyze_data(
    variable_name: str, data: pd.Series, start_date: dt.datetime, end_date: dt.datetime
) -> RetrievalStats:
    """
    Analyze retrieved data to verify completeness and identify anomalies.

    Args:
        variable_name: Name of the variable
        data: Retrieved data as a pandas Series
        start_date: Start date of the requested range
        end_date: End date of the requested range

    Returns:
        RetrievalStats object with statistics about the data
    """
    # Handle timezone-aware dates for comparison
    # Try to detect if we have a DatetimeIndex with timezone info
    index_tz = None
    if hasattr(data, "index"):
        if isinstance(data.index, pd.DatetimeIndex) and hasattr(data.index, "tz"):
            index_tz = data.index.tz

    if index_tz is not None:
        start_date = start_date.replace(tzinfo=index_tz)
        end_date = end_date.replace(tzinfo=index_tz)

    # Calculate expected number of data points based on frequency
    expected_points = (end_date - start_date).days + 1

    # Get actual number of data points
    actual_points = len(data)

    # Calculate completeness percentage
    completeness = (actual_points / expected_points) * 100

    # Identify gaps (periods with missing data)
    # We'll consider a gap as 5 or more consecutive missing days
    gaps = []
    if not data.empty:
        # Sort the data by date
        data = data.sort_index()

        # Get the dates in the data
        dates = data.index

        # Identify gaps of 5 or more days
        prev_date: Optional[dt.datetime] = None
        for date_idx in dates:
            try:
                # Convert to datetime if needed
                current_date = (
                    pd.Timestamp(date_idx).to_pydatetime()
                    if not isinstance(date_idx, dt.datetime)
                    else date_idx
                )

                if prev_date is not None:
                    # Calculate gap in days
                    gap_days = (current_date - prev_date).days
                    if gap_days > 5:
                        gaps.append((prev_date, current_date))

                prev_date = current_date
            except Exception as e:
                logger.warning(f"Error calculating gap between dates: {e}")
                # Continue with next date
                continue

    # Identify anomalies (values that deviate significantly from the mean)
    anomalies = []
    if not data.empty and len(data) > 1:
        # Calculate mean and std as scalar values - proper way to handle Series
        # conversion
        mean_val = float(data.iloc[0]) if len(data) == 1 else float(data.mean())
        std_val = 0.0 if len(data) == 1 else float(data.std())

        # Values more than 3 standard deviations from the mean are considered anomalies
        threshold = 3 * std_val

        # Iterate over the Series safely
        for idx, value in data.items():
            try:
                value_float = float(value)
                if abs(value_float - mean_val) > threshold:
                    anomalies.append((idx, value_float))
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Could not process value {value} for anomaly detection: {e}"
                )

    # Create and return statistics
    return RetrievalStats(
        variable_name=variable_name,
        source=(
            str(data.name)
            if hasattr(data, "name") and data.name is not None
            else "unknown"
        ),
        start_date=start_date,
        end_date=end_date,
        data_point_count=actual_points,
        min_value=float(data.min()) if not data.empty else 0,
        max_value=float(data.max()) if not data.empty else 0,
        mean_value=(
            float(data.iloc[0])
            if not data.empty and len(data) == 1
            else float(data.mean()) if not data.empty else 0
        ),
        median_value=(
            float(data.iloc[0])
            if not data.empty and len(data) == 1
            else float(data.median()) if not data.empty else 0
        ),
        completeness_pct=completeness,
        gaps=gaps,
        anomalies=anomalies,
    )


def retrieve_priority_variables(
    priority: int = 1,
    years: int = DEFAULT_YEARS,
    end_date: Optional[dt.datetime] = None,
    rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY,
) -> Dict[str, Dict[str, Any]]:
    """
    Retrieve historical data for all variables with the specified priority.

    Args:
        priority: Priority level to filter variables by
        years: Number of years to look back from end_date
        end_date: End date for data retrieval (defaults to today)
        rate_limit_delay: Delay between API calls to respect rate limits

    Returns:
        Dictionary mapping variable names to their retrieved data
    """
    priority_vars = get_priority_variables(priority)

    if not priority_vars:
        logger.warning(f"No variables found with priority {priority}")
        return {}

    results = {}

    for var_info in priority_vars:
        try:
            var_name = var_info["variable_name"]
            result = retrieve_historical_data(
                var_info,
                years=years,
                end_date=end_date,
                rate_limit_delay=rate_limit_delay,
            )
            results[var_name] = result

        except Exception as e:
            logger.error(
                f"Failed to retrieve data for {var_info['variable_name']}: {e}"
            )

    return results


def create_verification_report(results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a verification report for the retrieved data.

    Args:
        results: Dictionary mapping variable names to their retrieved data

    Returns:
        Dictionary with verification report
    """
    report = {
        "verification_timestamp": dt.datetime.now().isoformat(),
        "variables_processed": len(results),
        "successful_retrievals": 0,
        "failed_retrievals": 0,
        "variable_reports": {},
    }

    for var_name, result in results.items():
        if "stats" in result:
            report["successful_retrievals"] += 1
            stats = result["stats"]

            # Create a variable-specific report
            report["variable_reports"][var_name] = {
                "source": result["variable_info"]["source"],
                "data_point_count": stats["data_point_count"],
                "completeness_pct": stats["completeness_pct"],
                "min_value": stats["min_value"],
                "max_value": stats["max_value"],
                "mean_value": stats["mean_value"],
                "gaps_detected": len(stats["gaps"]) > 0,
                "anomalies_detected": len(stats["anomalies"]) > 0,
            }
        else:
            report["failed_retrievals"] += 1
            report["variable_reports"][var_name] = {
                "status": "failed",
                "source": result.get("variable_info", {}).get("source", "unknown"),
            }

    # Calculate overall metrics
    if report["successful_retrievals"] > 0:
        completeness_values = [
            var_report["completeness_pct"]
            for var_name, var_report in report["variable_reports"].items()
            if "completeness_pct" in var_report
        ]

        report["overall_metrics"] = {
            "average_completeness": sum(completeness_values) / len(completeness_values),
            "variables_with_gaps": sum(
                1
                for var_report in report["variable_reports"].values()
                if var_report.get("gaps_detected", False)
            ),
            "variables_with_anomalies": sum(
                1
                for var_report in report["variable_reports"].values()
                if var_report.get("anomalies_detected", False)
            ),
        }

    return report


def save_verification_report(report: Dict[str, Any]) -> Path:
    """Save the verification report to a file."""
    report_dir = Path("data/historical_timeline")
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / "verification_report.json"

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved verification report to {report_path}")

    return report_path


def main():
    """Command-line interface for historical data retrieval."""
    parser = argparse.ArgumentParser(
        description="Retrieve historical data for variables in the catalog"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--variable", type=str, help="Name of a specific variable to retrieve data for"
    )
    group.add_argument(
        "--priority",
        type=int,
        help="Retrieve data for all variables with this priority level",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Retrieve data for all variables in the catalog",
    )

    parser.add_argument(
        "--years",
        type=int,
        default=DEFAULT_YEARS,
        help=f"Number of years to look back (default: {DEFAULT_YEARS})",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_RATE_LIMIT_DELAY,
        help=f"Delay between API calls in seconds (default: {DEFAULT_RATE_LIMIT_DELAY})",
    )

    parser.add_argument(
        "--end-date", type=str, help="End date for data retrieval (format: YYYY-MM-DD)"
    )

    args = parser.parse_args()

    # Parse end date if provided
    end_date = None
    if args.end_date:
        try:
            end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            logger.error("Invalid end date format. Use YYYY-MM-DD.")
            return 1

    try:
        results = {}

        if args.variable:
            # Retrieve data for a specific variable
            catalog = load_variable_catalog()
            var_info = next(
                (
                    var
                    for var in catalog["variables"]
                    if var["variable_name"] == args.variable
                ),
                None,
            )

            if var_info is None:
                logger.error(f"Variable {args.variable} not found in the catalog")
                return 1

            result = retrieve_historical_data(
                var_info,
                years=args.years,
                end_date=end_date,
                rate_limit_delay=args.delay,
            )

            results[args.variable] = result

        elif args.priority:
            # Retrieve data for all variables with the specified priority
            results = retrieve_priority_variables(
                priority=args.priority,
                years=args.years,
                end_date=end_date,
                rate_limit_delay=args.delay,
            )

        elif args.all:
            # Retrieve data for all variables in the catalog
            catalog = load_variable_catalog()

            for var_info in catalog["variables"]:
                try:
                    var_name = var_info["variable_name"]
                    result = retrieve_historical_data(
                        var_info,
                        years=args.years,
                        end_date=end_date,
                        rate_limit_delay=args.delay,
                    )
                    results[var_name] = result

                except Exception as e:
                    logger.error(
                        f"Failed to retrieve data for {var_info['variable_name']}: {e}"
                    )

        # Create and save verification report
        report = create_verification_report(results)
        save_verification_report(report)

        logger.info(f"Processed {len(results)} variables:")
        logger.info(f"  - Successful: {report['successful_retrievals']}")
        logger.info(f"  - Failed: {report['failed_retrievals']}")

        if "overall_metrics" in report:
            logger.info(
                f"Average completeness: {
                    report['overall_metrics']['average_completeness']:.2f}%")
            logger.info(
                f"Variables with gaps: {
                    report['overall_metrics']['variables_with_gaps']}")
            logger.info(
                f"Variables with anomalies: {
                    report['overall_metrics']['variables_with_anomalies']}")

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
