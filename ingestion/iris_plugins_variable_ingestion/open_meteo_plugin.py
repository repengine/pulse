"""Open-Meteo API — climate plugin.

Connects to Open-Meteo's free weather API that requires no API key.
Provides current weather, forecasts, and historical weather data.
See: https://open-meteo.com/
"""

import datetime as dt
import logging
import time
from typing import Dict, List, Any, Optional

import requests
from ingestion.iris_plugins import IrisPluginManager

logger = logging.getLogger(__name__)


class OpenMeteoPlugin(IrisPluginManager):
    plugin_name = "open_meteo_plugin"
    enabled = True  # No API key required
    concurrency = 4  # Higher concurrency since no rate limits

    # API endpoint
    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
    HISTORICAL_API_URL = "https://archive-api.open-meteo.com/v1/archive"
    REQUEST_TIMEOUT = 10.0
    RETRY_WAIT = 1.5  # seconds between retries
    MAX_RETRIES = 2

    # Define key global cities to monitor
    CITIES = {
        # City name: (latitude, longitude, timezone)
        "new_york": (40.71, -74.01, "America/New_York"),
        "london": (51.51, -0.13, "Europe/London"),
        "tokyo": (35.69, 139.69, "Asia/Tokyo"),
        "sydney": (-33.87, 151.21, "Australia/Sydney"),
        "beijing": (39.90, 116.41, "Asia/Shanghai"),
        "mumbai": (19.08, 72.88, "Asia/Kolkata"),
        "sao_paulo": (-23.55, -46.63, "America/Sao_Paulo"),
        "cairo": (30.04, 31.24, "Africa/Cairo"),
    }

    # Weather variables we want to track
    CURRENT_WEATHER_VARS = [
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation",
        "wind_speed_10m",
    ]

    DAILY_WEATHER_VARS = [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
    ]

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch weather data signals from Open-Meteo API."""
        signals = []

        # Get current date
        now = dt.datetime.now()

        # We'll rotate through cities - get 2 cities per day based on the day of the month
        start_idx = (now.day % 4) * 2
        today_cities = dict(list(self.CITIES.items())[start_idx : start_idx + 2])

        # Fetch current weather for selected cities
        for city_name, (lat, lon, timezone) in today_cities.items():
            current_signals = self._fetch_current_weather(city_name, lat, lon, timezone)
            signals.extend(current_signals)

            # Avoid hitting the API too quickly
            time.sleep(0.5)

            # Fetch 7-day forecast for the city
            forecast_signals = self._fetch_daily_forecast(city_name, lat, lon, timezone)
            signals.extend(forecast_signals)

            # Avoid hitting the API too quickly
            time.sleep(0.5)

            # On the 1st and 15th of the month, also fetch historical monthly data
            if now.day == 1 or now.day == 15:
                # Get previous month's data
                previous_month = now.replace(day=1) - dt.timedelta(days=1)
                year = previous_month.year
                month = previous_month.month

                historical_signals = self._fetch_historical_monthly(
                    city_name, lat, lon, timezone, year, month
                )
                signals.extend(historical_signals)

        return signals

    def _safe_get(self, url: str, params: dict) -> Optional[dict]:
        """Make a safe API request with retries and error handling."""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(url, params=params, timeout=self.REQUEST_TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                logger.warning(
                    f"Open-Meteo request failed ({attempt + 1}/{self.MAX_RETRIES}): {exc}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
        return None

    def _fetch_current_weather(
        self, city_name: str, lat: float, lon: float, timezone: str
    ) -> List[Dict[str, Any]]:
        """Fetch current weather data for a specific location."""
        signals = []

        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ",".join(self.CURRENT_WEATHER_VARS),
            "timezone": timezone,
        }

        data = self._safe_get(self.WEATHER_API_URL, params)
        if not data or "current" not in data:
            return signals

        current_data = data["current"]
        current_time = current_data.get("time")

        # Create a signal for each weather variable
        for var in self.CURRENT_WEATHER_VARS:
            if var in current_data:
                var_value = current_data[var]
                if var_value is not None:
                    signals.append(
                        {
                            "name": f"{city_name}_{var}",
                            "value": float(var_value),
                            "source": "open_meteo_current",
                            "timestamp": self._to_timestamp(current_time),
                        }
                    )

        return signals

    def _fetch_daily_forecast(
        self, city_name: str, lat: float, lon: float, timezone: str
    ) -> List[Dict[str, Any]]:
        """Fetch 7-day forecast for a location."""
        signals = []

        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join(self.DAILY_WEATHER_VARS),
            "forecast_days": 7,
            "timezone": timezone,
        }

        data = self._safe_get(self.WEATHER_API_URL, params)
        if not data or "daily" not in data:
            return signals

        daily_data = data["daily"]

        # Get the tomorrow forecast
        if len(daily_data.get("time", [])) > 1:
            tomorrow_idx = 1  # Index 1 is tomorrow
            tomorrow_date = daily_data["time"][tomorrow_idx]

            for var in self.DAILY_WEATHER_VARS:
                if var in daily_data and len(daily_data[var]) > tomorrow_idx:
                    var_value = daily_data[var][tomorrow_idx]
                    if var_value is not None:
                        signals.append(
                            {
                                "name": f"{city_name}_forecast_{var}",
                                "value": float(var_value),
                                "source": "open_meteo_forecast",
                                "timestamp": self._to_timestamp(tomorrow_date),
                            }
                        )

        return signals

    def _fetch_historical_monthly(
        self,
        city_name: str,
        lat: float,
        lon: float,
        timezone: str,
        year: int,
        month: int,
    ) -> List[Dict[str, Any]]:
        """Fetch historical monthly weather data for a location."""
        signals = []

        # Calculate start and end dates for the month
        start_date = f"{year}-{month:02d}-01"

        # Calculate the last day of the month
        if month == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month + 1

        end_date = dt.datetime(next_year, next_month, 1) - dt.timedelta(days=1)
        end_date_str = end_date.strftime("%Y-%m-%d")

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date_str,
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": timezone,
        }

        data = self._safe_get(self.HISTORICAL_API_URL, params)
        if not data or "daily" not in data:
            return signals

        daily_data = data["daily"]

        # Calculate monthly averages
        if "temperature_2m_mean" in daily_data and daily_data["temperature_2m_mean"]:
            temps = [t for t in daily_data["temperature_2m_mean"] if t is not None]
            if temps:
                avg_temp = sum(temps) / len(temps)
                signals.append(
                    {
                        "name": f"{city_name}_historical_monthly_temp",
                        "value": avg_temp,
                        "source": "open_meteo_historical",
                        "timestamp": self._to_timestamp(
                            f"{year}-{month:02d}-15"
                        ),  # Middle of month
                    }
                )

        # Calculate monthly precipitation total
        if "precipitation_sum" in daily_data and daily_data["precipitation_sum"]:
            precip = [p for p in daily_data["precipitation_sum"] if p is not None]
            if precip:
                total_precip = sum(precip)
                signals.append(
                    {
                        "name": f"{city_name}_historical_monthly_precip",
                        "value": total_precip,
                        "source": "open_meteo_historical",
                        "timestamp": self._to_timestamp(
                            f"{year}-{month:02d}-15"
                        ),  # Middle of month
                    }
                )

        return signals

    def _to_timestamp(self, date_str: str) -> str:
        """Convert date string to ISO-8601 UTC timestamp."""
        try:
            # Parse the date string to a datetime object
            if "T" in date_str:  # Already has time component
                dt_obj = dt.datetime.fromisoformat(date_str)
            else:  # Just a date, add time at noon
                dt_obj = dt.datetime.fromisoformat(f"{date_str}T12:00:00")

            # Convert to UTC timezone
            dt_obj = dt_obj.replace(tzinfo=dt.timezone.utc)
            return dt_obj.isoformat()
        except Exception:
            # Default to current time if parsing fails
            return dt.datetime.now(dt.timezone.utc).isoformat()
