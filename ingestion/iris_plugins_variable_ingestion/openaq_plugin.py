"""OpenAQ - air quality data ingestion plugin.

This plugin fetches air quality data from the OpenAQ API, which provides
open air quality data from around the world. The plugin retrieves data for
PM2.5, PM10, O3, NO2, SO2, and CO measurements from various monitoring
stations globally.

No API key is required for basic usage.

Example:
--------
```python
from ingestion.iris_plugins import IrisPluginManager
from ingestion.iris_plugins_variable_ingestion.openaq_plugin import OpenaqPlugin

mgr = IrisPluginManager()
mgr.register_plugin(OpenaqPlugin())
print(mgr.run_plugins())
```
"""

import datetime as dt
import logging
import time
from typing import List, Dict, Any

import requests
from ingestion.iris_plugins import IrisPluginManager
from ingestion.iris_utils.ingestion_persistence import (
    ensure_data_directory,
    save_request_metadata,
    save_api_response,
    save_processed_data,
)

logger = logging.getLogger(__name__)

# Source name for persistence
_SOURCE_NAME = "openaq"

# Base URL for the OpenAQ API
_BASE_URL = "https://api.openaq.org/v2/latest"

# List of pollutant parameters to fetch
_POLLUTANTS = ["pm25", "pm10", "o3", "no2", "so2", "co"]

# List of major cities to monitor
_CITIES = [
    "New York",
    "London",
    "Beijing",
    "Tokyo",
    "Delhi",
    "Paris",
    "Los Angeles",
    "Mexico City",
    "Cairo",
    "Mumbai",
]


class OpenaqPlugin(IrisPluginManager):
    plugin_name = "openaq_plugin"
    enabled = True  # No API key required for basic usage
    concurrency = 2  # Limit concurrent requests

    # Request configuration
    REQUEST_TIMEOUT = 15.0
    RETRY_WAIT = 2.0
    MAX_RETRIES = 2

    def __init__(self):
        """Initialize the OpenAQ plugin."""
        # Ensure data directory exists for this source
        ensure_data_directory(_SOURCE_NAME)

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch air quality data from OpenAQ API."""
        signals = []

        # Rotate between cities based on day of month to avoid too many API calls
        city_idx = dt.datetime.now().day % len(_CITIES)
        city = _CITIES[city_idx]

        logger.info(f"[openaq_plugin] Fetching air quality data for {city}")

        # Fetch data for selected city
        city_signals = self._fetch_city_data(city)
        signals.extend(city_signals)

        return signals

    def _fetch_city_data(self, city: str) -> List[Dict[str, Any]]:
        """Fetch air quality data for a specific city."""
        signals = []
        dataset_id = f"openaq_{city.replace(' ', '_').lower()}"

        # Request parameters
        params = {
            "city": city,
            "limit": 100,
            "page": 1,
            "sort": "desc",
            "order_by": "lastUpdated",
            "has_geo": "true",
        }

        # Save request metadata before making the request
        save_request_metadata(
            dataset_id, params, source_name=_SOURCE_NAME, url=_BASE_URL
        )

        # Make the API request with retries
        response_data = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = requests.get(
                    _BASE_URL, params=params, timeout=self.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                response_data = response.json()

                # Save API response
                save_api_response(
                    dataset_id,
                    response_data,
                    source_name=_SOURCE_NAME,
                    timestamp=dt.datetime.now().isoformat(),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )

                break
            except Exception as e:
                logger.warning(
                    f"[openaq_plugin] Request attempt {attempt + 1} failed: {e}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT)

        # If all attempts failed, return empty list
        if not response_data:
            logger.error(
                f"[openaq_plugin] Failed to fetch data for {city} after {self.MAX_RETRIES + 1} attempts"
            )
            return signals

        # Process the response data
        try:
            results = response_data.get("results", [])
            if not results:
                logger.warning(f"[openaq_plugin] No results found for {city}")
                return signals

            logger.info(
                f"[openaq_plugin] Found {len(results)} monitoring stations for {city}"
            )

            # Process data for each monitoring station
            for station in results:
                station_name = station.get("name", "Unknown")
                measurements = station.get("measurements", [])

                for measurement in measurements:
                    parameter = measurement.get("parameter", "").lower()
                    value = measurement.get("value")
                    unit = measurement.get("unit", "")
                    last_updated = measurement.get("lastUpdated", "")

                    if parameter and value is not None:
                        # Create signal
                        signal = {
                            "name": f"air_quality_{city.lower().replace(' ', '_')}_{parameter}",
                            "value": float(value),
                            "source": "openaq",
                            "timestamp": last_updated
                            or dt.datetime.now(dt.timezone.utc).isoformat(),
                            "metadata": {
                                "city": city,
                                "station": station_name,
                                "parameter": parameter,
                                "unit": unit,
                                "coordinates": station.get("coordinates", {}),
                                "country": station.get("country", ""),
                            },
                        }

                        # Save processed data
                        save_processed_data(
                            f"{city.replace(' ', '_').lower()}_{parameter}",
                            signal,
                            source_name=_SOURCE_NAME,
                            timestamp=signal["timestamp"],
                        )

                        signals.append(signal)

            return signals
        except Exception as e:
            logger.error(f"[openaq_plugin] Error processing data for {city}: {e}")

            # Save error information
            save_api_response(
                f"{dataset_id}_error",
                {"error": str(e), "timestamp": dt.datetime.now().isoformat()},
                source_name=_SOURCE_NAME,
            )

            return signals

    def get_pollutant_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Get WHO recommended thresholds for air pollutants.

        Used for data interpretation context.
        """
        return {
            "pm25": {
                "good": 10.0,  # Annual mean
                "moderate": 25.0,  # 24-hour mean
                "poor": 50.0,  # Exceeded WHO guidelines significantly
            },
            "pm10": {
                "good": 20.0,  # Annual mean
                "moderate": 50.0,  # 24-hour mean
                "poor": 100.0,  # Exceeded WHO guidelines significantly
            },
            "o3": {
                "good": 100.0,  # 8-hour mean
                "moderate": 160.0,  # Moderate concern
                "poor": 240.0,  # Health risk
            },
            "no2": {
                "good": 40.0,  # Annual mean
                "moderate": 100.0,  # 1-hour mean
                "poor": 200.0,  # Exceeded WHO guidelines significantly
            },
            "so2": {
                "good": 20.0,  # 24-hour mean
                "moderate": 50.0,  # Moderate concern
                "poor": 100.0,  # Health risk
            },
            "co": {
                "good": 4000.0,  # Good air quality
                "moderate": 10000.0,  # Moderate concern
                "poor": 30000.0,  # Health risk
            },
        }
