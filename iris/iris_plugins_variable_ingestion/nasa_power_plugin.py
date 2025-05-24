"""NASA POWER - climate data ingestion plugin.

This plugin fetches climate data from the NASA POWER API (Prediction of Worldwide Energy Resource),
which provides meteorological and solar energy parameters derived from satellite observations
and model assimilation.

The API provides:
- Temperature data (min, max, and average)
- Precipitation data
- Solar radiation data
- Wind speed and direction
- Relative humidity
- Earth's radiation components

No API key is required for basic usage.

Example:
--------
```python
from iris.iris_plugins import IrisPluginManager
from iris.iris_plugins_variable_ingestion.nasa_power_plugin import NasaPowerPlugin

mgr = IrisPluginManager()
mgr.register_plugin(NasaPowerPlugin())
print(mgr.run_plugins())
```
"""

import datetime as dt
import logging
import time
from typing import List, Dict, Any, Optional

import requests
from iris.iris_plugins import IrisPluginManager
from iris.iris_utils.ingestion_persistence import (
    ensure_data_directory,
    save_request_metadata,
    save_api_response,
    save_processed_data,
)

logger = logging.getLogger(__name__)

# Source name for persistence
_SOURCE_NAME = "nasa_power"

# Base URL for the NASA POWER API
_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Parameters to fetch (documentation: https://power.larc.nasa.gov/docs/services/api/)
_PARAMETERS = {
    "T2M": "temperature_2m",  # Temperature at 2 Meters (°C)
    "T2M_MAX": "temperature_2m_max",  # Maximum Temperature at 2 Meters (°C)
    "T2M_MIN": "temperature_2m_min",  # Minimum Temperature at 2 Meters (°C)
    "PRECTOT": "precipitation",  # Precipitation (mm/day)
    "RH2M": "relative_humidity_2m",  # Relative Humidity at 2 Meters (%)
    "WS10M": "wind_speed_10m",  # Wind Speed at 10 Meters (m/s)
    "ALLSKY_SFC_SW_DWN": "solar_radiation_downward",  # All Sky Surface Shortwave Downward Irradiance (W/m^2)
    "ALLSKY_SFC_LW_DWN": "longwave_radiation_downward",  # All Sky Surface Longwave Downward Irradiance (W/m^2)
}

# List of major cities to monitor with lat/lon coordinates
_LOCATIONS = {
    "New_York": {"lat": 40.71, "lon": -74.01},
    "London": {"lat": 51.51, "lon": -0.13},
    "Tokyo": {"lat": 35.68, "lon": 139.77},
    "Beijing": {"lat": 39.91, "lon": 116.40},
    "Sydney": {"lat": -33.87, "lon": 151.21},
    "Mumbai": {"lat": 19.08, "lon": 72.88},
    "Rio_de_Janeiro": {"lat": -22.91, "lon": -43.18},
    "Cairo": {"lat": 30.05, "lon": 31.24},
    "Moscow": {"lat": 55.75, "lon": 37.62},
    "Lagos": {"lat": 6.46, "lon": 3.38},
}


class NasaPowerPlugin(IrisPluginManager):
    plugin_name = "nasa_power_plugin"
    enabled = True  # No API key required for basic usage
    concurrency = 2  # Limit concurrent requests

    # Request configuration
    REQUEST_TIMEOUT = 20.0  # NASA POWER can be slow, so longer timeout
    RETRY_WAIT = 2.0
    MAX_RETRIES = 3

    def __init__(self):
        """Initialize the NASA POWER plugin."""
        # Ensure data directory exists for this source
        ensure_data_directory(_SOURCE_NAME)

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch climate data from NASA POWER API."""
        signals = []

        # Rotate between locations based on day of month to avoid too many API calls
        day_of_month = dt.datetime.now().day
        location_idx = day_of_month % len(_LOCATIONS)
        location_name = list(_LOCATIONS.keys())[location_idx]
        location = _LOCATIONS[location_name]

        logger.info(f"[nasa_power_plugin] Fetching climate data for {location_name}")

        # Fetch data for selected location
        location_signals = self._fetch_location_data(
            location_name, location["lat"], location["lon"]
        )
        signals.extend(location_signals)

        return signals

    def _fetch_location_data(
        self, location_name: str, lat: float, lon: float
    ) -> List[Dict[str, Any]]:
        """Fetch climate data for a specific location.

        Args:
            location_name: Name of the location
            lat: Latitude
            lon: Longitude

        Returns:
            List of signal dictionaries containing climate data
        """
        signals = []
        dataset_id = f"nasa_power_{location_name.lower()}"

        # Calculate date range (last 7 days)
        end_date = dt.datetime.now() - dt.timedelta(
            days=1
        )  # Yesterday (NASA data has a delay)
        start_date = end_date - dt.timedelta(days=7)  # 7 days before that

        # Format dates for API
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")

        # Request parameters
        params = {
            "start": start_date_str,
            "end": end_date_str,
            "lat": lat,
            "lon": lon,
            "parameters": ",".join(_PARAMETERS.keys()),
            "community": "RE",  # Renewable Energy community
            "format": "JSON",
            "header": "false",  # Disable CSV header
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
                    f"[nasa_power_plugin] Request attempt {attempt + 1} failed: {e}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT)

        # If all attempts failed, return empty list
        if not response_data:
            logger.error(
                f"[nasa_power_plugin] Failed to fetch data for {location_name} after {self.MAX_RETRIES + 1} attempts"
            )
            return signals

        # Process the response data
        try:
            # NASA POWER API returns data in a specific structure
            properties = response_data.get("properties", {})
            parameter_data = properties.get("parameter", {})

            if not parameter_data:
                logger.warning(f"[nasa_power_plugin] No data found for {location_name}")
                return signals

            logger.info(
                f"[nasa_power_plugin] Successfully received data for {location_name}"
            )

            # The API returns data for each day, process the most recent day
            # Find the most recent date with data
            most_recent = self._get_most_recent_date_with_data(parameter_data)

            if not most_recent:
                logger.warning(
                    f"[nasa_power_plugin] No valid data found for {location_name}"
                )
                return signals

            # Generate signals for each parameter
            for nasa_param, param_name in _PARAMETERS.items():
                if (
                    nasa_param in parameter_data
                    and most_recent in parameter_data[nasa_param]
                ):
                    value = parameter_data[nasa_param][most_recent]

                    # Skip if value is missing (-999 is NASA's missing data indicator)
                    if value == -999:
                        continue

                    # Create signal
                    signal = {
                        "name": f"climate_{location_name.lower()}_{param_name}",
                        "value": float(value),
                        "source": "nasa_power",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "location": location_name,
                            "lat": lat,
                            "lon": lon,
                            "date": most_recent,
                            "parameter": nasa_param,
                            "source": "NASA POWER",
                        },
                    }

                    # Save processed data
                    save_processed_data(
                        f"{location_name.lower()}_{param_name}",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"],
                    )

                    signals.append(signal)

            return signals
        except Exception as e:
            logger.error(
                f"[nasa_power_plugin] Error processing data for {location_name}: {e}"
            )

            # Save error information
            save_api_response(
                f"{dataset_id}_error",
                {"error": str(e), "timestamp": dt.datetime.now().isoformat()},
                source_name=_SOURCE_NAME,
            )

            return signals

    def _get_most_recent_date_with_data(
        self, parameter_data: Dict[str, Dict[str, float]]
    ) -> Optional[str]:
        """Get the most recent date that has valid data for any parameter.

        Args:
            parameter_data: Dictionary of parameters with date values

        Returns:
            Date string in YYYYMMDD format, or None if no valid dates found
        """
        # Get all dates from the first parameter (assumes all parameters have same dates)
        if not parameter_data or not next(iter(parameter_data.values()), {}):
            return None

        # Get sample parameter and its dates
        sample_param = next(iter(parameter_data.keys()))
        dates = list(parameter_data[sample_param].keys())

        # Sort in descending order (most recent first)
        dates.sort(reverse=True)

        # Find first date with valid data for major parameters
        for date in dates:
            # Check temperature and precipitation (most important parameters)
            temp_valid = parameter_data.get("T2M", {}).get(date, -999) != -999
            precip_valid = parameter_data.get("PRECTOT", {}).get(date, -999) != -999

            if temp_valid or precip_valid:
                return date

        # If no valid data found, return the most recent date anyway
        return dates[0] if dates else None

    def get_climate_parameter_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about climate parameters for data interpretation context."""
        return {
            "temperature_2m": {
                "unit": "°C",
                "description": "Daily average temperature at 2 meters above the surface",
                "significance": "Key indicator for economic activity, energy usage, and agricultural planning",
            },
            "temperature_2m_max": {
                "unit": "°C",
                "description": "Daily maximum temperature at 2 meters above the surface",
                "significance": "Important for energy demand forecasting and extreme weather analysis",
            },
            "temperature_2m_min": {
                "unit": "°C",
                "description": "Daily minimum temperature at 2 meters above the surface",
                "significance": "Critical for agriculture (frost risk) and energy use forecasting",
            },
            "precipitation": {
                "unit": "mm/day",
                "description": "Total daily precipitation",
                "significance": "Essential for agricultural yields, water resource management, and flood risk",
            },
            "relative_humidity_2m": {
                "unit": "%",
                "description": "Daily average relative humidity at 2 meters above the surface",
                "significance": "Affects human comfort, energy consumption, and agricultural conditions",
            },
            "wind_speed_10m": {
                "unit": "m/s",
                "description": "Daily average wind speed at 10 meters above the surface",
                "significance": "Important for renewable energy forecasting and transportation planning",
            },
            "solar_radiation_downward": {
                "unit": "W/m²",
                "description": "Daily average solar radiation reaching the Earth's surface",
                "significance": "Critical for solar energy production forecasting and agricultural modeling",
            },
            "longwave_radiation_downward": {
                "unit": "W/m²",
                "description": "Daily average longwave radiation reaching the Earth's surface",
                "significance": "Important component of Earth's energy budget affecting climate",
            },
        }
