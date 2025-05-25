"""iris.iris_plugins_variable_ingestion.nasdaq_plugin
================================================================
Nasdaq Data Link (Quandl) ingestion plugin for Pulse IRIS.

* Expects `NASDAQ_API_KEY` in environment.
* Optional `NASDAQ_DL_DATASETS` env‑var (comma‑separated, default
  "LBMA/GOLD").
* Returns a list of *signal dictionaries* matching Iris schema so it
  can be registered with `IrisPluginManager` just like
  `finance_plugins()`.

Available datasets include:
- "LBMA/GOLD" for London Bullion Market gold prices (free tier)
- "FRED/GDP" for economic data from Federal Reserve (free tier)
- "ODA/PALUM_USD" for Aluminum Price (free tier)
- "OPEC/ORB" for OPEC Reference Basket Price (free tier)
- "WORLDBANK/WLD_SP_POP_TOTL" for World Population (free tier)
- "EOD/AAPL" for End of Day data (premium, may require subscription)
- "MULTPL/SHILLER_PE_RATIO_MONTH" for S&P 500 Shiller PE Ratio (premium)

NOTE: Access to specific datasets is governed by your API key's subscription level.
The plugin will try to use available datasets with proper error handling.

Example
-------
```python
from iris.iris_plugins import IrisPluginManager
from iris.iris_plugins_variable_ingestion.nasdaq_plugin import nasdaq_plugin

mgr = IrisPluginManager()
mgr.register_plugin(nasdaq_plugin)
print(mgr.run_plugins())
```
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import random
from typing import List, Dict, Any, Optional

import requests  # lightweight fallback instead of nasdaq‑data‑link SDK

from iris.iris_utils.ingestion_persistence import (
    ensure_data_directory,
    save_request_metadata,
    save_api_response,
    save_processed_data,
    save_data_point_incremental,
)

logger = logging.getLogger(__name__)

# Check both key naming conventions
_API_KEY: Optional[str] = os.getenv("NASDAQ_API_KEY") or os.getenv("NASDAQ_KEY")
# Use LBMA/GOLD as default dataset (more likely to be accessible on free tier)
_DEFAULT_DATASETS = ""

# Fallback datasets - if the user's preferred datasets are inaccessible
_FALLBACK_DATASETS = []

# Mock symbols for generating sample data when API access fails
_MOCK_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]

_BASE_URL = "https://data.nasdaq.com/api/v3/datasets/{code}.json"

# Source name for persistence
_SOURCE_NAME = "nasdaq"


def nasdaq_plugin() -> List[Dict[str, Any]]:
    """Entry point expected by *IrisPluginManager* (no args → List[Dict])."""
    if not _API_KEY:
        logger.warning("[nasdaq_plugin] NASDAQ_API_KEY not set — skipping fetch")
        return []

    # Ensure data directory exists for this source
    ensure_data_directory(_SOURCE_NAME)

    # Reload dataset list from environment every time to allow runtime changes
    user_datasets = os.getenv("NASDAQ_DL_DATASETS", _DEFAULT_DATASETS)
    dataset_list = [code.strip() for code in user_datasets.split(",") if code]
    logger.info("[nasdaq_plugin] Attempting to process datasets: %s", dataset_list)

    signals: List[Dict[str, Any]] = []
    accessible_datasets = []

    # First try user-specified datasets
    for code in dataset_list:
        if sig := _fetch_latest(code):
            signals.append(sig)
            accessible_datasets.append(code)

    # If no datasets were accessible, try fallbacks
    if not signals and "WIKI/" not in "".join(
        dataset_list
    ):  # Don't fallback if using old WIKI datasets
        logger.warning(
            "[nasdaq_plugin] No data retrieved from specified datasets. Trying fallback datasets."
        )
        for code in _FALLBACK_DATASETS:
            if code not in dataset_list:  # Don't retry datasets we already tried
                if sig := _fetch_latest(code):
                    signals.append(sig)
                    accessible_datasets.append(code)
                    break  # One successful fallback is enough

    if accessible_datasets:
        logger.info(
            "[nasdaq_plugin] Successfully accessed datasets: %s", accessible_datasets
        )
    else:
        logger.error(
            "[nasdaq_plugin] Could not access any datasets. Check API key permissions."
        )
        logger.warning(
            "[nasdaq_plugin] Falling back to mock data for demonstration purposes."
        )
        mock_signals = _generate_mock_data()
        signals.extend(mock_signals)

    return signals


def _generate_mock_data() -> List[Dict[str, Any]]:
    """Generate mock stock data when API access fails.

    This allows the system to continue functioning with sample data
    when the NASDAQ Data Link API is inaccessible due to API key limitations.
    """
    logger.info("[nasdaq_plugin] Generating mock data for demonstration")

    mock_signals = []

    # Current date for timestamp
    today = _dt.datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)

    # Generate mock data for a few sample symbols
    for symbol in _MOCK_SYMBOLS:
        # Base price depends on the symbol
        base_price = {
            "AAPL": 175.0,
            "MSFT": 350.0,
            "GOOGL": 145.0,
            "AMZN": 130.0,
            "META": 450.0,
            "TSLA": 230.0,
        }.get(symbol, 100.0)

        # Add small random variations
        close_price = base_price * (1 + random.uniform(-0.02, 0.02))
        open_price = close_price * (1 + random.uniform(-0.01, 0.01))
        high_price = max(close_price, open_price) * (1 + random.uniform(0.001, 0.02))
        low_price = min(close_price, open_price) * (1 - random.uniform(0.001, 0.02))
        volume = random.randint(1000000, 10000000)

        # Create a signal with mock data
        signal = {
            "source": "nasdaq_dl_mock",  # Mark as mock data
            "symbol": symbol,
            "timestamp": today.isoformat(),
            "value": round(close_price, 2),
            "dataset_id": f"MOCK/{symbol}",
            "meta": {
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "volume": volume,
                "mock_data": True,  # Explicitly flag as mock data
            },
        }

        # Save data point incrementally as soon as it's processed
        save_data_point_incremental(
            f"MOCK/{symbol}",
            signal["timestamp"],
            signal["value"],
            variable_name=symbol.lower() + "_price",
            source_name=_SOURCE_NAME,
            metadata=signal["meta"],
        )

        # Also save processed data (for backward compatibility)
        save_processed_data(
            f"MOCK/{symbol}",
            signal,
            source_name=_SOURCE_NAME,
            timestamp=signal["timestamp"],
        )

        mock_signals.append(signal)

    return mock_signals


def _fetch_latest(code: str) -> Optional[Dict[str, Any]]:
    """Return the latest observation for *dataset* `code`.

    Handles multiple dataset formats:
    - EOD datasets: [date, open, high, low, close, volume, ...]
    - Other datasets: [date, value, ...] or custom structures

    The function attempts to extract consistent data regardless of source format.
    Also writes the fetched data to a file in the data directory.
    """
    url = _BASE_URL.format(code=code)
    params = {"api_key": _API_KEY, "rows": 1}

    # Save request metadata BEFORE making the API call using the persistence module
    save_request_metadata(code, params, source_name=_SOURCE_NAME, url=url)

    try:
        resp = requests.get(url, params=params, timeout=10)

        # Handle specific API errors
        if resp.status_code == 410:
            logger.error(
                "[nasdaq_plugin] %s endpoint is no longer available (410 Gone). "
                "This dataset has been deprecated. Try using an alternative dataset.",
                code,
            )
            return None
        elif resp.status_code == 403:
            logger.error(
                "[nasdaq_plugin] %s endpoint returned 403 Forbidden. "
                "Your API key may not have access to this dataset.",
                code,
            )
            return None
        elif resp.status_code == 404:
            logger.error(
                "[nasdaq_plugin] %s endpoint returned 404 Not Found. "
                "This dataset may not exist or has been renamed.",
                code,
            )
            return None

        # Handle other HTTP errors
        resp.raise_for_status()

        # Get the raw API response data
        response_data = resp.json()

        # Save the raw API response data using the persistence module
        current_time = _dt.datetime.now().isoformat()
        save_api_response(
            code,
            response_data,
            source_name=_SOURCE_NAME,
            timestamp=current_time,
            status_code=resp.status_code,
            headers=dict(resp.headers),
        )

        # Create an incremental ingestion directory to track the progress
        ingest_dir = os.path.join(f"data/{_SOURCE_NAME}", f"{code}_ingest_progress")
        os.makedirs(ingest_dir, exist_ok=True)

        # Save the parser progress before starting to parse
        progress_file = os.path.join(
            ingest_dir,
            f"{code}_progress_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_start.json",
        )
        with open(progress_file, "w") as f:
            json.dump(
                {
                    "stage": "parsing_start",
                    "timestamp": _dt.datetime.now().isoformat(),
                    "code": code,
                    "status": "starting payload extraction",
                },
                f,
                indent=2,
            )

        payload = response_data["dataset"]
        latest = payload["data"][0]

        # Save the parser progress after extracting payload data
        progress_file = os.path.join(
            ingest_dir,
            f"{code}_progress_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_raw_extracted.json",
        )
        with open(progress_file, "w") as f:
            json.dump(
                {
                    "stage": "raw_data_extracted",
                    "timestamp": _dt.datetime.now().isoformat(),
                    "code": code,
                    "dataset_info": {
                        "name": payload.get("name", ""),
                        "dataset_code": payload.get("dataset_code", ""),
                        "data_points": len(payload.get("data", [])),
                        "latest_date": latest[0]
                        if latest and len(latest) > 0
                        else None,
                    },
                },
                f,
                indent=2,
            )

        # Get dataset type and code to determine structure
        dataset_type = code.split("/")[0].upper() if "/" in code else ""
        dataset_code = (
            code.split("/")[1] if "/" in code and len(code.split("/")) > 1 else ""
        )

        # Basic fields every signal should have
        signal = {
            "source": "nasdaq_dl",
            "symbol": payload.get("dataset_code", dataset_code),
            "timestamp": _dt.datetime.strptime(latest[0], "%Y-%m-%d").isoformat(),
            "dataset_id": code,  # Store original dataset ID for reference
        }

        # Save incremental progress after basic signal creation
        progress_file = os.path.join(
            ingest_dir,
            f"{code}_progress_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_basic_fields.json",
        )
        with open(progress_file, "w") as f:
            json.dump(
                {
                    "stage": "basic_fields_created",
                    "timestamp": _dt.datetime.now().isoformat(),
                    "code": code,
                    "signal_basic": signal,
                },
                f,
                indent=2,
            )

        # Handle different dataset structures
        if dataset_type == "EOD" or dataset_type == "WIKI":
            # Standard OHLCV format
            if len(latest) >= 6:
                # Save progress before processing OHLCV data
                progress_file = os.path.join(
                    ingest_dir,
                    f"{code}_progress_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_parse_ohlcv_start.json",
                )
                with open(progress_file, "w") as f:
                    json.dump(
                        {
                            "stage": "processing_ohlcv",
                            "timestamp": _dt.datetime.now().isoformat(),
                            "code": code,
                            "data_point_count": len(latest),
                        },
                        f,
                        indent=2,
                    )

                signal["value"] = float(latest[4])  # close price
                signal["meta"] = {
                    "open": float(latest[1]) if latest[1] is not None else None,
                    "high": float(latest[2]) if latest[2] is not None else None,
                    "low": float(latest[3]) if latest[3] is not None else None,
                    "volume": float(latest[5])
                    if latest[5] is not None and len(latest) > 5
                    else None,
                }

                # Save progress after processing OHLCV data
                progress_file = os.path.join(
                    ingest_dir,
                    f"{code}_progress_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_parse_ohlcv_complete.json",
                )
                with open(progress_file, "w") as f:
                    json.dump(
                        {
                            "stage": "ohlcv_processed",
                            "timestamp": _dt.datetime.now().isoformat(),
                            "code": code,
                            "signal_value": signal["value"],
                            "signal_meta": signal["meta"],
                        },
                        f,
                        indent=2,
                    )
            else:
                # Shorter data format
                progress_file = os.path.join(
                    ingest_dir,
                    f"{code}_progress_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_parse_short_start.json",
                )
                with open(progress_file, "w") as f:
                    json.dump(
                        {
                            "stage": "processing_short_format",
                            "timestamp": _dt.datetime.now().isoformat(),
                            "code": code,
                            "data_point_count": len(latest),
                        },
                        f,
                        indent=2,
                    )

                signal["value"] = float(latest[1]) if len(latest) > 1 else 0.0
                signal["meta"] = {"raw_data": latest}

                progress_file = os.path.join(
                    ingest_dir,
                    f"{code}_progress_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_parse_short_complete.json",
                )
                with open(progress_file, "w") as f:
                    json.dump(
                        {
                            "stage": "short_format_processed",
                            "timestamp": _dt.datetime.now().isoformat(),
                            "code": code,
                            "signal_value": signal["value"],
                        },
                        f,
                        indent=2,
                    )
        else:
            # Generic format - assume second column is the main value if available
            progress_file = os.path.join(
                ingest_dir,
                f"{code}_progress_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_parse_generic_start.json",
            )
            with open(progress_file, "w") as f:
                json.dump(
                    {
                        "stage": "processing_generic_format",
                        "timestamp": _dt.datetime.now().isoformat(),
                        "code": code,
                        "data_point_count": len(latest),
                    },
                    f,
                    indent=2,
                )

            signal["value"] = float(latest[1]) if len(latest) > 1 else 0.0
            # Include all available data in metadata for other components to use if needed
            signal["meta"] = {
                f"column_{i}": float(val)
                if val is not None and isinstance(val, (int, float, str)) and val != ""
                else val
                for i, val in enumerate(latest[1:], 1)
                if i < len(latest)
            }

            progress_file = os.path.join(
                ingest_dir,
                f"{code}_progress_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_parse_generic_complete.json",
            )
            with open(progress_file, "w") as f:
                json.dump(
                    {
                        "stage": "generic_format_processed",
                        "timestamp": _dt.datetime.now().isoformat(),
                        "code": code,
                        "signal_value": signal["value"],
                        "column_count": len(signal["meta"]),
                    },
                    f,
                    indent=2,
                )

        # Save final progress before persisting to regular storage
        progress_file = os.path.join(
            ingest_dir,
            f"{code}_progress_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_processing_complete.json",
        )
        with open(progress_file, "w") as f:
            json.dump(
                {
                    "stage": "processing_complete",
                    "timestamp": _dt.datetime.now().isoformat(),
                    "code": code,
                    "final_signal": signal,
                },
                f,
                indent=2,
            )

        # Save data point incrementally as soon as it's processed
        save_data_point_incremental(
            code,
            signal["timestamp"],
            signal["value"],
            variable_name=signal["symbol"].lower() + "_price",
            source_name=_SOURCE_NAME,
            metadata=signal.get("meta", {}),
        )

        # Also save processed data (for backward compatibility)
        save_processed_data(
            code, signal, source_name=_SOURCE_NAME, timestamp=signal["timestamp"]
        )

        # Save final completion marker
        progress_file = os.path.join(
            ingest_dir,
            f"{code}_progress_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_final.json",
        )
        with open(progress_file, "w") as f:
            json.dump(
                {
                    "stage": "persistence_complete",
                    "timestamp": _dt.datetime.now().isoformat(),
                    "code": code,
                    "status": "success",
                    "saved_to": f"{_SOURCE_NAME}/{code}",
                },
                f,
                indent=2,
            )

        return signal

    except Exception as exc:  # noqa: E722 — network/API errors are mapped to log + skip
        logger.error("[nasdaq_plugin] %s fetch failed: %s", code, exc)

        # Create error tracking directory to record each step of error handling
        error_dir = os.path.join(f"data/{_SOURCE_NAME}", f"{code}_errors")
        os.makedirs(error_dir, exist_ok=True)

        # Save detailed error information as it happens
        error_file = os.path.join(
            error_dir,
            f"{code}_error_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
        with open(error_file, "w") as f:
            error_info = {
                "error": str(exc),
                "timestamp": _dt.datetime.now().isoformat(),
                "code": code,
                "error_type": type(exc).__name__,
                "stage": "api_fetch",
            }
            json.dump(error_info, f, indent=2)

        # Determine the error type
        if "Wiki" in str(exc) or "WIKI" in str(exc):
            error_type = "deprecated_dataset"
            logger.warning(
                "[nasdaq_plugin] WIKI dataset is deprecated. Try using alternative datasets like LBMA/GOLD or FRED/GDP."
            )
        elif "403" in str(exc) or "Forbidden" in str(exc):
            error_type = "access_forbidden"
            logger.warning(
                "[nasdaq_plugin] Access forbidden to %s. Your subscription may not include this dataset.",
                code,
            )
        elif "404" in str(exc) or "Not Found" in str(exc):
            error_type = "not_found"
            logger.warning(
                "[nasdaq_plugin] Dataset %s not found. It may have been renamed or removed.",
                code,
            )
        else:
            error_type = "general_error"

        # Save categorized error information
        error_summary_file = os.path.join(
            error_dir,
            f"{code}_error_summary_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
        with open(error_summary_file, "w") as f:
            json.dump(
                {
                    "error": str(exc),
                    "timestamp": _dt.datetime.now().isoformat(),
                    "code": code,
                    "error_type": error_type,
                    "recommendations": {
                        "deprecated_dataset": "Try using alternative datasets like LBMA/GOLD or FRED/GDP",
                        "access_forbidden": "Check your API key permissions",
                        "not_found": "Verify the dataset code or try an alternative dataset",
                        "general_error": "Check network connectivity and try again",
                    }.get(error_type, "Unknown error"),
                },
                f,
                indent=2,
            )

        # Save error information to a file using the standard persistence module too
        save_api_response(
            f"{code}_error",
            {"error": str(exc), "timestamp": _dt.datetime.now().isoformat()},
            source_name=_SOURCE_NAME,
        )

        return None
