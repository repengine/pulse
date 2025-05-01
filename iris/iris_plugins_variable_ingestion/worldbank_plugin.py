"""World Bank Open Data API — geopolitics plugin.

Connects to the World Bank API for global development indicators.
No API key required. Access is completely free.
See: https://data.worldbank.org/
"""
import datetime as dt
import logging
import time
from typing import Dict, List, Any, Optional

import requests
from iris.iris_plugins import IrisPluginManager

logger = logging.getLogger(__name__)

class WorldBankPlugin(IrisPluginManager):
    plugin_name = "worldbank_plugin"
    enabled = True     # No API key required
    concurrency = 3     # Reasonable concurrency for the API
    
    # API endpoint
    BASE_URL = "https://api.worldbank.org/v2"
    REQUEST_TIMEOUT = 15.0
    RETRY_WAIT = 1.5  # seconds between retries
    MAX_RETRIES = 2
    
    # List of countries to monitor (ISO-2 codes)
    COUNTRIES = [
        "US",  # United States
        "CN",  # China
        "DE",  # Germany
        "JP",  # Japan
        "IN",  # India
        "BR",  # Brazil
        "RU",  # Russia
        "GB",  # United Kingdom
        "FR",  # France
        "ZA",  # South Africa
    ]
    
    # Dictionary of indicators to track
    # Format: {pulse_variable_name: (indicator_code, description)}
    INDICATORS = {
        "gdp_current_usd": ("NY.GDP.MKTP.CD", "GDP (current US$)"),
        "gdp_growth": ("NY.GDP.MKTP.KD.ZG", "GDP growth (annual %)"),
        "inflation_consumer_prices": ("FP.CPI.TOTL.ZG", "Inflation, consumer prices (annual %)"),
        "unemployment": ("SL.UEM.TOTL.ZS", "Unemployment, total (% of labor force)"),
        "population_total": ("SP.POP.TOTL", "Population, total"),
        "fdi_inflows": ("BX.KLT.DINV.WD.GD.ZS", "Foreign direct investment, net inflows (% of GDP)"),
        "govnt_debt_to_gdp": ("GC.DOD.TOTL.GD.ZS", "Central government debt, total (% of GDP)"),
        "internet_usage": ("IT.NET.USER.ZS", "Individuals using the Internet (% of population)"),
        "co2_emissions": ("EN.ATM.CO2E.PC", "CO2 emissions (metric tons per capita)"),
        "renewable_energy": ("EG.FEC.RNEW.ZS", "Renewable energy consumption (% of total final energy consumption)"),
    }

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch economic and development indicators from World Bank API."""
        signals = []
        
        # Get current date
        now = dt.datetime.now()
        
        # Rotate through countries to avoid making too many API calls at once
        # Take 3 countries per day based on the day of month
        countries_per_day = 3
        start_idx = (now.day % (len(self.COUNTRIES) // countries_per_day)) * countries_per_day
        today_countries = self.COUNTRIES[start_idx:start_idx + countries_per_day]
        
        # Rotate through indicators similarly
        indicators_per_day = 5
        start_idx = (now.day % (len(self.INDICATORS) // indicators_per_day)) * indicators_per_day
        indicator_items = list(self.INDICATORS.items())
        today_indicators = dict(indicator_items[start_idx:start_idx + indicators_per_day])
        
        # Fetch data for each country and indicator combination
        for country in today_countries:
            for var_name, (indicator_code, _) in today_indicators.items():
                indicator_data = self._fetch_indicator(country, indicator_code)
                signals.extend(indicator_data)
                
                # Be nice to the API
                time.sleep(0.5)
        
        return signals

    def _safe_get(self, url: str, params: dict) -> Optional[List[Any]]:
        """Make a safe API request with retries and error handling."""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                # Add standard parameters for JSON format and English language
                full_params = {
                    "format": "json",
                    "per_page": 10,  # Limit results
                    **params
                }
                
                resp = requests.get(url, params=full_params, timeout=self.REQUEST_TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                logger.warning(f"World Bank API request failed ({attempt+1}/{self.MAX_RETRIES}): {exc}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
        return None

    def _fetch_indicator(self, country_code: str, indicator_code: str) -> List[Dict[str, Any]]:
        """Fetch a specific indicator for a specific country."""
        signals = []
        
        url = f"{self.BASE_URL}/country/{country_code}/indicator/{indicator_code}"
        params = {
            "date": self._get_recent_years(5),  # Last 5 years
            "mrnev": 1  # Most recent non-empty value
        }
        
        data = self._safe_get(url, params)
        if not data or len(data) < 2 or not data[1]:
            logger.warning(f"No data returned for {country_code}/{indicator_code}")
            return signals
        
        # The World Bank API returns data in a peculiar format:
        # First element contains metadata, second element contains actual data points
        indicator_data = data[1]
        
        for entry in indicator_data:
            if not entry.get("value"):
                continue
                
            try:
                # Create a signal name that combines variable name and country code
                signal_name = f"{country_code.lower()}_{entry['indicator']['id'].lower()}"
                
                # Get the year and construct a timestamp (middle of the year)
                year = entry["date"]
                timestamp = f"{year}-06-30T12:00:00Z"
                
                # Add the signal
                signals.append({
                    "name": signal_name,
                    "value": float(entry["value"]),
                    "source": "worldbank",
                    "timestamp": timestamp,
                    "metadata": {
                        "country": entry["country"]["value"],
                        "indicator": entry["indicator"]["value"],
                        "year": year
                    }
                })
                break  # We only take the most recent value
                
            except (ValueError, KeyError, TypeError) as e:
                logger.error(f"Error processing World Bank data for {country_code}/{indicator_code}: {e}")
        
        return signals

    def _get_recent_years(self, num_years: int) -> str:
        """Generate a date range string for the last num_years."""
        current_year = dt.datetime.now().year
        start_year = current_year - num_years
        return f"{start_year}:{current_year}"