"""World Bank API — economic and development data plugin.

Connects to the World Bank Indicators API to fetch economic and development data
for countries around the world. This data includes GDP, population statistics,
poverty metrics, education indicators, health statistics, and more.

No API key required. The World Bank API is public and freely accessible.
Documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-api-documentation
"""

import datetime as dt
import logging
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode
import json

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
_SOURCE_NAME = "worldbank"


class WorldBankPlugin(IrisPluginManager):
    plugin_name = "world_bank_plugin"
    enabled = True  # No API key required
    concurrency = 2  # Limit concurrent requests to avoid overloading API

    # World Bank API configuration
    BASE_URL = "https://api.worldbank.org/v2"
    REQUEST_TIMEOUT = 20.0
    RETRY_WAIT = 2.0  # seconds between retries
    MAX_RETRIES = 3

    # Selected indicators to track (based on relevance to forecasting and
    # update frequency)
    INDICATORS = {
        # Economic indicators
        "NY.GDP.MKTP.CD": "gdp",  # GDP (current US$)
        "NY.GDP.MKTP.KD.ZG": "gdp_growth",  # GDP growth (annual %)
        "FP.CPI.TOTL.ZG": "inflation",  # Inflation, consumer prices (annual %)
        "SL.UEM.TOTL.ZS": "unemployment",  # Unemployment, total (% of labor force)
        "NE.EXP.GNFS.ZS": "exports",  # Exports of goods and services (% of GDP)
        "BX.KLT.DINV.WD.GD.ZS": "fdi",  # Foreign direct investment (% of GDP)
        # Development indicators
        "SP.POP.TOTL": "population",  # Population, total
        "SP.DYN.LE00.IN": "life_expectancy",  # Life expectancy at birth, total (years)
        # Government expenditure on education (% of GDP)
        "SE.XPD.TOTL.GD.ZS": "education",
        "SH.XPD.CHEX.GD.ZS": "healthcare",  # Current health expenditure (% of GDP)
        # Electric power consumption (kWh per capita)
        "EG.USE.ELEC.KH.PC": "electricity",
        # Individuals using the Internet (% of population)
        "IT.NET.USER.ZS": "internet",
    }

    # Countries to track by region
    COUNTRIES = {
        "north_america": ["US", "CA", "MX"],  # USA, Canada, Mexico
        "south_america": ["BR", "AR", "CO", "CL"],  # Brazil, Argentina, Colombia, Chile
        "europe": ["DE", "FR", "GB", "IT", "ES"],  # Germany, France, UK, Italy, Spain
        "east_asia": ["CN", "JP", "KR", "ID"],  # China, Japan, South Korea, Indonesia
        "south_asia": ["IN", "PK", "BD"],  # India, Pakistan, Bangladesh
        "africa": [
            "ZA",
            "NG",
            "EG",
            "ET",
            "KE",
        ],  # South Africa, Nigeria, Egypt, Ethiopia, Kenya
        "middle_east": [
            "SA",
            "AE",
            "IR",
            "IL",
            "TR",
        ],  # Saudi Arabia, UAE, Iran, Israel, Turkey
        "oceania": ["AU", "NZ"],  # Australia, New Zealand
    }

    # Map for more readable indicator names in signals
    INDICATOR_NAMES = {
        "gdp": "Gross Domestic Product",
        "gdp_growth": "GDP Growth Rate",
        "inflation": "Inflation Rate",
        "unemployment": "Unemployment Rate",
        "exports": "Exports (% of GDP)",
        "fdi": "Foreign Direct Investment",
        "population": "Total Population",
        "life_expectancy": "Life Expectancy",
        "education": "Education Expenditure",
        "healthcare": "Healthcare Expenditure",
        "electricity": "Electricity Consumption",
        "internet": "Internet Penetration",
    }

    def __init__(self):
        """Initialize the World Bank plugin."""
        # Ensure data directory exists for this source
        ensure_data_directory(_SOURCE_NAME)

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch economic and development signals from World Bank API."""
        signals = []

        # Current timestamp
        now = dt.datetime.now(dt.timezone.utc)

        # Rotate through regions and indicators to limit the number of API calls
        # and avoid overloading the API
        region_key = self._get_rotation_region()
        indicator_key = self._get_rotation_indicator()

        # Get country codes for the selected region
        country_codes = self.COUNTRIES.get(region_key, [])
        if not country_codes:
            logger.warning(f"No country codes defined for region: {region_key}")
            return signals

        # Get indicator code
        indicator_code = self._get_indicator_code(indicator_key)
        if not indicator_code:
            logger.warning(f"Invalid indicator key: {indicator_key}")
            return signals

        # Fetch data for the selected countries and indicator
        indicator_data = self._fetch_indicator_data(country_codes, indicator_code)
        if not indicator_data:
            logger.warning(
                f"No data found for indicator {indicator_key} in region {region_key}"
            )
            return signals

        # Process data into signals
        signals.extend(
            self._process_indicator_data(indicator_data, indicator_key, region_key, now)
        )

        return signals

    def _get_rotation_region(self) -> str:
        """Get region to use based on daily rotation."""
        day_of_month = dt.datetime.now().day
        regions = list(self.COUNTRIES.keys())
        return regions[day_of_month % len(regions)]

    def _get_rotation_indicator(self) -> str:
        """Get indicator to use based on daily rotation."""
        day_of_month = dt.datetime.now().day
        indicators = list(self.INDICATORS.values())
        return indicators[(day_of_month // len(self.COUNTRIES)) % len(indicators)]

    def _get_indicator_code(self, indicator_key: str) -> Optional[str]:
        """Get indicator code from key."""
        for code, key in self.INDICATORS.items():
            if key == indicator_key:
                return code
        return None

    def _safe_get(self, url: str, params: dict, dataset_id: str) -> Optional[dict]:
        """Make a safe API request with retries and error handling."""
        # Save request metadata
        save_request_metadata(dataset_id, params, source_name=_SOURCE_NAME, url=url)

        # Create request URL
        full_url = f"{url}?{urlencode(params)}"

        # Make request with retries
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(full_url, timeout=self.REQUEST_TIMEOUT)
                resp.raise_for_status()

                # Parse JSON response
                data = resp.json()

                # Save successful response
                save_api_response(
                    dataset_id,
                    {"response_json": json.dumps(data)},
                    source_name=_SOURCE_NAME,
                    status_code=resp.status_code,
                    headers=dict(resp.headers),
                )

                return data
            except requests.exceptions.RequestException as exc:
                logger.warning(
                    f"World Bank request failed ({attempt + 1}/{self.MAX_RETRIES}): {exc}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
            except json.JSONDecodeError:
                logger.error("Failed to parse World Bank API response")
                break

        # If all attempts failed, log the error
        logger.error(
            f"Failed to fetch data from World Bank after {self.MAX_RETRIES} attempts"
        )
        return None

    def _fetch_indicator_data(
        self, country_codes: List[str], indicator_code: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch indicator data for specified countries.

        Args:
            country_codes: List of country codes to fetch data for
            indicator_code: World Bank indicator code

        Returns:
            Dictionary with country code as key and indicator value as value
        """
        # Use ISO3 country codes joined by semicolons
        countries_str = ";".join(country_codes)

        # Build request parameters
        # The World Bank API returns the most recent available data by default
        params = {
            "format": "json",
            "per_page": 100,  # Maximum allowed by the API
            "date": "last5",  # Last 5 years of data (we'll use the most recent)
        }

        # Create endpoint URL
        endpoint = f"{self.BASE_URL}/country/{countries_str}/indicator/{indicator_code}"

        # Create dataset ID for persistence
        dataset_id = f"{indicator_code}_{len(country_codes)}_countries"

        # Make request
        response_data = self._safe_get(endpoint, params, dataset_id)
        if (
            not response_data
            or not isinstance(response_data, list)
            or len(response_data) < 2
        ):
            logger.error(
                f"Invalid response format from World Bank API for indicator {indicator_code}")
            return None

        # Extract data
        # The World Bank API returns a list where the first element is metadata
        # and the second element is the actual data
        results = {}
        try:
            data_points = response_data[1]

            # Group data by country
            country_data = {}
            for point in data_points:
                if not all(
                    k in point for k in ["country", "countryiso3code", "value", "date"]
                ):
                    continue

                country_code = point["countryiso3code"]
                value = point["value"]
                date = point["date"]

                # Skip entries with null values
                if value is None:
                    continue

                # If this is the first or a more recent data point for this country
                if (
                    country_code not in country_data
                    or date > country_data[country_code]["date"]
                ):
                    country_data[country_code] = {"value": value, "date": date}

            # Extract just the values for the results
            for country_code, data in country_data.items():
                results[country_code] = data["value"]

            return results
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"Error processing World Bank data: {e}")
            return None

    def _process_indicator_data(
        self,
        indicator_data: Dict[str, Any],
        indicator_key: str,
        region_key: str,
        timestamp: dt.datetime,
    ) -> List[Dict[str, Any]]:
        """Process indicator data into signals.

        Args:
            indicator_data: Dictionary with country code as key and indicator value as value
            indicator_key: Key for the indicator
            region_key: Key for the region
            timestamp: Timestamp for the signals

        Returns:
            List of signals derived from indicator data
        """
        signals = []

        # Get descriptive name for the indicator
        indicator_name = self.INDICATOR_NAMES.get(indicator_key, indicator_key)

        # Create a signal for each country
        iso_timestamp = timestamp.isoformat()

        for country_code, value in indicator_data.items():
            # Create signal
            signal = {
                "name": f"worldbank_{country_code.lower()}_{indicator_key}",
                "value": value,
                "source": "worldbank",
                "timestamp": iso_timestamp,
                "metadata": {
                    "country": country_code,
                    "region": region_key,
                    "indicator": indicator_key,
                    "indicator_name": indicator_name,
                },
            }

            # Save the processed signal
            save_processed_data(
                f"{country_code}_{indicator_key}",
                signal,
                source_name=_SOURCE_NAME,
                timestamp=iso_timestamp,
            )

            signals.append(signal)

        # If we have data for multiple countries, create a regional average
        if len(indicator_data) > 1:
            # Calculate average
            values = list(indicator_data.values())
            avg_value = sum(values) / len(values)

            # Create signal for regional average
            region_signal = {
                "name": f"worldbank_{region_key}_{indicator_key}_avg",
                "value": avg_value,
                "source": "worldbank",
                "timestamp": iso_timestamp,
                "metadata": {
                    "region": region_key,
                    "indicator": indicator_key,
                    "indicator_name": indicator_name,
                    "countries": len(indicator_data),
                    "calculation": "average",
                },
            }

            # Save the processed signal
            save_processed_data(
                f"{region_key}_{indicator_key}_avg",
                region_signal,
                source_name=_SOURCE_NAME,
                timestamp=iso_timestamp,
            )

            signals.append(region_signal)

        return signals
