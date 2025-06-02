"""WHO Global Health Observatory API — health plugin.

Connects to the WHO GHO OData API for global health metrics.
No API key required. Access is completely free.
See: https://www.who.int/data/gho/info/gho-odata-api
"""

import datetime as dt
import logging
import time
from typing import Dict, List, Any, Optional

import requests
from ingestion.iris_plugins import IrisPluginManager

logger = logging.getLogger(__name__)


class WhoGhoPlugin(IrisPluginManager):
    plugin_name = "who_gho_plugin"
    enabled = True  # No API key required
    concurrency = 2  # Limited concurrency to be nice to the API

    # API endpoint
    BASE_URL = "https://ghoapi.azureedge.net/api"
    REQUEST_TIMEOUT = 15.0
    RETRY_WAIT = 2.0  # seconds between retries
    MAX_RETRIES = 3

    # Dictionary of indicators to track
    # Format: {pulse_variable_name: (indicator_code, description)}
    INDICATORS = {
        "life_expectancy": ("WHOSIS_000001", "Life expectancy at birth (years)"),
        "infant_mortality": (
            "MDG_0000000001",
            "Infant mortality rate (per 1000 live births)",
        ),
        "maternal_mortality": (
            "MDG_0000000004",
            "Maternal mortality ratio (per 100 000 live births)",
        ),
        "tuberculosis_incidence": (
            "MDG_0000000025",
            "Tuberculosis incidence (per 100 000 population)",
        ),
        "malaria_incidence": (
            "MALARIA_EST_CASES",
            "Malaria incidence (per 1 000 population)",
        ),
        "hiv_prevalence": (
            "HIV_0000000001",
            "HIV prevalence among adults aged 15 to 49 (%)",
        ),
        "overweight_prevalence": (
            "NCD_BMI_25A",
            "Prevalence of overweight among adults (%)",
        ),
        "obesity_prevalence": ("NCD_BMI_30A", "Prevalence of obesity among adults (%)"),
        "alcohol_consumption": (
            "SA_0000001462",
            "Total alcohol consumption per capita (liters)",
        ),
        "tobacco_prevalence": (
            "M_Est_smk_curr_std",
            "Age-standardized prevalence of tobacco smoking among persons aged 15+ years",
        ),
        "uhc_coverage_index": (
            "UHC_INDEX_REPORTED",
            "Universal health coverage (UHC) service coverage index",
        ),
        "medical_doctors_density": (
            "HWF_0001",
            "Medical doctors (per 10,000 population)",
        ),
        "hospital_beds_density": (
            "HFAC_0078",
            "Hospital bed density (per 10,000 population)",
        ),
    }

    # Key countries to monitor (ISO-3 codes)
    COUNTRIES = [
        "USA",  # United States
        "CHN",  # China
        "IND",  # India
        "DEU",  # Germany
        "BRA",  # Brazil
        "RUS",  # Russia
        "GBR",  # United Kingdom
        "JPN",  # Japan
        "KEN",  # Kenya
        "ZAF",  # South Africa
    ]

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch global health indicators from WHO GHO API."""
        signals = []

        # Get current date
        now = dt.datetime.now()

        # Rotate through indicators to avoid making too many API calls at once
        indicators_per_day = 3
        start_idx = (
            now.day % (len(self.INDICATORS) // indicators_per_day)
        ) * indicators_per_day
        indicator_items = list(self.INDICATORS.items())
        today_indicators = dict(
            indicator_items[start_idx: start_idx + indicators_per_day]
        )

        # Fetch information about selected indicators first
        for var_name, (indicator_code, _) in today_indicators.items():
            # First, we need to get metadata about the indicator
            indicator_metadata = self._fetch_indicator_metadata(indicator_code)
            if not indicator_metadata:
                continue

            # Get years available for this indicator
            latest_available_year = self._get_latest_year(indicator_metadata)
            if not latest_available_year:
                continue

            # For each country, fetch the latest available data for this indicator
            for country_code in self.COUNTRIES:
                country_data = self._fetch_indicator_data(
                    indicator_code, country_code, latest_available_year
                )
                if country_data:
                    signals.extend(country_data)

                # Be nice to the API
                time.sleep(0.5)

            # Be nice to the API between indicators
            time.sleep(1.0)

        return signals

    def _safe_get(self, url: str, params: dict = None) -> Optional[dict]:
        """Make a safe API request with retries and error handling."""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(url, params=params, timeout=self.REQUEST_TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                logger.warning(
                    f"WHO GHO API request failed ({attempt + 1}/{self.MAX_RETRIES}): {exc}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
        return None

    def _fetch_indicator_metadata(
        self, indicator_code: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch metadata for an indicator."""
        url = f"{self.BASE_URL}/Indicator/{indicator_code}"
        return self._safe_get(url)

    def _get_latest_year(self, indicator_metadata: Dict[str, Any]) -> Optional[int]:
        """Determine the latest available year for an indicator."""
        try:
            # Try to extract from metadata - this is not always reliable
            # Default to 3 years ago if not found (typical lag in WHO data)
            current_year = dt.datetime.now().year
            return current_year - 3
        except Exception:
            return dt.datetime.now().year - 3  # Default to 3 years ago

    def _fetch_indicator_data(
        self, indicator_code: str, country_code: str, year: int
    ) -> List[Dict[str, Any]]:
        """Fetch data for a specific indicator, country and year."""
        signals = []

        # Construct the URL with filters
        url = f"{self.BASE_URL}/Indicator/{indicator_code}/Country/{country_code}/Year/{year}"

        data = self._safe_get(url)
        if not data or "value" not in data:
            return signals

        indicator_data = data["value"]
        if not indicator_data:
            return signals

        for entry in indicator_data:
            # Check if there's a numeric value
            if "NumericValue" not in entry or entry["NumericValue"] is None:
                continue

            try:
                # Extract the value and metadata
                value = float(entry["NumericValue"])
                dimension_values = {}

                # Extract any dimension values (sex, age group, etc.)
                for key, val in entry.items():
                    if key.startswith("Dim") and not key.endswith("Code") and val:
                        dimension_values[key] = val

                # Create signal name, including country code and any relevant dimensions
                dimensions_str = ""
                if "Dim1" in dimension_values:  # Often this is sex
                    dim_val = dimension_values["Dim1"].lower()
                    if dim_val in ["male", "female", "both sexes"]:
                        # Abbreviate the dimension
                        if dim_val == "both sexes":
                            dimensions_str = "all"
                        else:
                            dimensions_str = dim_val[:1]  # "m" or "f"

                # Create signal name
                var_base_name = next(
                    (k for k, v in self.INDICATORS.items() if v[0] == indicator_code),
                    indicator_code.lower(),
                )
                signal_name = f"who_{country_code.lower()}_{var_base_name}"
                if dimensions_str:
                    signal_name = f"{signal_name}_{dimensions_str}"

                # Create year timestamp (middle of the year)
                timestamp = f"{year}-06-30T12:00:00Z"

                signals.append(
                    {
                        "name": signal_name,
                        "value": value,
                        "source": "who_gho",
                        "timestamp": timestamp,
                        "metadata": {
                            "country": entry.get("SpatialDim", country_code),
                            "indicator": entry.get(
                                "IndicatorName",
                                self.INDICATORS.get(
                                    var_base_name, (indicator_code, "")
                                )[1],
                            ),
                            "year": year,
                            "dimensions": dimension_values,
                        },
                    }
                )

            except (ValueError, TypeError) as e:
                logger.error(
                    f"Error processing WHO data for {indicator_code}/{country_code}: {e}")

        return signals
