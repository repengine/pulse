"""OpenFDA - healthcare and pharmaceutical data ingestion plugin.

This plugin fetches data from the FDA's OpenFDA API, which provides access to
various datasets including drug adverse events, drug recalls, medical device reports,
and more. The plugin processes this data into signals that can be used for healthcare
sector analysis and pharmaceutical market forecasting.

An API key is optional for basic usage (up to 240 requests per minute), but recommended
for higher rate limits. Get a free API key at: https://open.fda.gov/apis/authentication/

Example:
--------
```python
from ingestion.iris_plugins import IrisPluginManager
from ingestion.iris_plugins_variable_ingestion.openfda_plugin import OpenfdaPlugin

mgr = IrisPluginManager()
mgr.register_plugin(OpenfdaPlugin())
print(mgr.run_plugins())
```
"""

import datetime as dt
import logging
import os
import time
from typing import List, Dict, Any
import re
from collections import Counter

import requests
from ingestion.iris_plugins import IrisPluginManager
from ingestion.utils.ingestion_persistence import (
    ensure_data_directory,
    save_request_metadata,
    save_api_response,
    save_processed_data,
)

logger = logging.getLogger(__name__)

# Source name for persistence
_SOURCE_NAME = "openfda"

# Base URL for the OpenFDA API
_BASE_URL = "https://api.fda.gov"

# Check both key naming conventions
_API_KEY = os.getenv("OPENFDA_API_KEY") or os.getenv("OPENFDA_KEY")

# Define endpoints of interest
_ENDPOINTS = {
    "drug_events": "/drug/event.json",
    "drug_recalls": "/drug/enforcement.json",
    "drug_ndc": "/drug/ndc.json",
    "device_events": "/device/event.json",
    "device_recalls": "/device/enforcement.json",
    "food_enforcement": "/food/enforcement.json",
}

# Time windows to analyze (recent vs historical)
_TIME_WINDOWS = {
    "recent": 30,  # Last 30 days
    "medium": 90,  # Last 90 days
    "annual": 365,  # Last year
}


class OpenfdaPlugin(IrisPluginManager):
    plugin_name = "openfda_plugin"
    enabled = True  # No API key required for basic usage
    concurrency = 2  # Limit concurrent requests

    # Request configuration
    REQUEST_TIMEOUT = 15.0
    RETRY_WAIT = 2.0
    MAX_RETRIES = 2

    def __init__(self):
        """Initialize the OpenFDA plugin."""
        # Ensure data directory exists for this source
        ensure_data_directory(_SOURCE_NAME)

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch healthcare and pharmaceutical data from OpenFDA API."""
        signals = []

        # Rotate between endpoints based on day of month to distribute API calls
        day_of_month = dt.datetime.now().day
        endpoint_idx = day_of_month % len(_ENDPOINTS)
        endpoint_name = list(_ENDPOINTS.keys())[endpoint_idx]
        endpoint_path = _ENDPOINTS[endpoint_name]

        logger.info(f"[openfda_plugin] Fetching data for {endpoint_name}")

        # For current endpoint, fetch recent data
        time_window = "recent"  # Default to recent window

        # Fetch data for selected endpoint and time window
        endpoint_signals = self._fetch_endpoint_data(
            endpoint_name, endpoint_path, time_window
        )
        signals.extend(endpoint_signals)

        return signals

    def _fetch_endpoint_data(
        self, endpoint_name: str, endpoint_path: str, time_window: str
    ) -> List[Dict[str, Any]]:
        """Fetch data for a specific OpenFDA endpoint and time window.

        Args:
            endpoint_name: Name of the endpoint (e.g., 'drug_events')
            endpoint_path: API path for the endpoint
            time_window: Time window to analyze ('recent', 'medium', 'annual')

        Returns:
            List of signal dictionaries containing OpenFDA data
        """
        signals = []
        dataset_id = f"openfda_{endpoint_name}_{time_window}"

        # Calculate date range based on time window
        days = _TIME_WINDOWS.get(time_window, 30)  # Default to 30 days
        end_date = dt.datetime.now()
        start_date = end_date - dt.timedelta(days=days)

        # Format dates for API (YYYYMMDD format)
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")

        # Construct search query based on endpoint type
        search_query = self._get_search_query(
            endpoint_name, start_date_str, end_date_str
        )

        # Request parameters
        params = {
            "search": search_query,
            "limit": 100,  # Max results per request
            "skip": 0,  # Starting offset
        }

        # Add API key if available
        if _API_KEY:
            params["api_key"] = _API_KEY

        # Add count parameters (get aggregated data)
        count_field = self._get_count_field(endpoint_name)
        if count_field:
            params["count"] = count_field
            params["limit"] = 10  # Limit to top 10 categories

        # Save request metadata before making the request
        url = f"{_BASE_URL}{endpoint_path}"
        save_request_metadata(
            dataset_id,
            params,
            source_name=_SOURCE_NAME,
            url=url,
            sensitive_params={"api_key"},  # Mask API key in logs
        )

        # Make the API request with retries
        response_data = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = requests.get(
                    url, params=params, timeout=self.REQUEST_TIMEOUT
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
                    f"[openfda_plugin] Request attempt {attempt + 1} failed: {e}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT)

        # If all attempts failed, return empty list
        if not response_data:
            logger.error(
                f"[openfda_plugin] Failed to fetch data for {endpoint_name} after {self.MAX_RETRIES + 1} attempts"
            )
            return signals

        # Process the response data based on endpoint type
        try:
            if "results" in response_data:
                # For count queries
                if count_field and "count" in response_data:
                    count_results = response_data.get("count", [])
                    signals.extend(
                        self._process_count_data(
                            endpoint_name, count_field, count_results, time_window
                        )
                    )
                # For regular queries
                elif "results" in response_data:
                    results = response_data.get("results", [])
                    signals.extend(
                        self._process_regular_data(endpoint_name, results, time_window)
                    )

                logger.info(
                    f"[openfda_plugin] Successfully processed {len(signals)} signals for {endpoint_name}"
                )
            else:
                logger.warning(f"[openfda_plugin] No results found for {endpoint_name}")

            # Get any metadata about the query
            meta = response_data.get("meta", {})
            if meta:
                # Create a signal for the total count
                if "results" in meta:
                    total_count = meta.get("results", {}).get("total", 0)
                    signal = {
                        "name": f"fda_{endpoint_name}_{time_window}_total_count",
                        "value": float(total_count),
                        "source": "openfda",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "endpoint": endpoint_name,
                            "time_window": time_window,
                            "days": days,
                        },
                    }

                    # Save processed data
                    save_processed_data(
                        f"{endpoint_name}_{time_window}_total",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"],
                    )

                    signals.append(signal)

            return signals
        except Exception as e:
            logger.error(
                f"[openfda_plugin] Error processing data for {endpoint_name}: {e}"
            )

            # Save error information
            save_api_response(
                f"{dataset_id}_error",
                {"error": str(e), "timestamp": dt.datetime.now().isoformat()},
                source_name=_SOURCE_NAME,
            )

            return signals

    def _get_search_query(
        self, endpoint_name: str, start_date: str, end_date: str
    ) -> str:
        """Get the appropriate search query for the endpoint.

        Args:
            endpoint_name: Name of the endpoint
            start_date: Start date in YYYYMMDD format
            end_date: End date in YYYYMMDD format

        Returns:
            Search query string for the API
        """
        if "event" in endpoint_name:
            return f"receivedate:[{start_date} TO {end_date}]"
        elif "enforcement" in endpoint_name or "recall" in endpoint_name:
            return f"report_date:[{start_date} TO {end_date}]"
        elif "ndc" in endpoint_name:
            return ""  # No date filtering for drug NDC database
        else:
            return f"report_date:[{start_date} TO {end_date}]"

    def _get_count_field(self, endpoint_name: str) -> str:
        """Get the appropriate count field for the endpoint.

        Args:
            endpoint_name: Name of the endpoint

        Returns:
            Field to count/aggregate by
        """
        if endpoint_name == "drug_events":
            return "patient.reaction.reactionmeddrapt.exact"  # Count by reaction type
        elif endpoint_name == "drug_recalls":
            return "openfda.pharm_class_epc.exact"  # Count by pharmaceutical class
        elif endpoint_name == "drug_ndc":
            return "openfda.route.exact"  # Count by administration route
        elif endpoint_name == "device_events":
            return "device.device_report_product_code.exact"  # Count by product code
        elif endpoint_name == "device_recalls":
            return "product_code.exact"  # Count by product code
        elif endpoint_name == "food_enforcement":
            return "classification.exact"  # Count by classification
        else:
            return ""

    def _process_count_data(
        self,
        endpoint_name: str,
        count_field: str,
        count_results: List[Dict],
        time_window: str,
    ) -> List[Dict[str, Any]]:
        """Process count/aggregation data from OpenFDA API.

        Args:
            endpoint_name: Name of the endpoint
            count_field: Field that was counted
            count_results: Count results from the API
            time_window: Time window being analyzed

        Returns:
            List of signal dictionaries
        """
        signals = []

        # Process top categories
        for i, count_item in enumerate(count_results[:10]):  # Take top 10
            if "term" in count_item and "count" in count_item:
                term = count_item["term"]
                count = count_item["count"]

                # Clean up term for signal name
                clean_term = re.sub(r"[^a-zA-Z0-9]", "_", term.lower())
                clean_term = re.sub(r"_+", "_", clean_term).strip("_")

                # Create signal
                signal = {
                    "name": f"fda_{endpoint_name}_{time_window}_{clean_term}",
                    "value": float(count),
                    "source": "openfda",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "metadata": {
                        "endpoint": endpoint_name,
                        "time_window": time_window,
                        "field": count_field,
                        "term": term,
                        "rank": i + 1,  # 1-based rank
                    },
                }

                # Save processed data
                save_processed_data(
                    f"{endpoint_name}_{time_window}_{clean_term}",
                    signal,
                    source_name=_SOURCE_NAME,
                    timestamp=signal["timestamp"],
                )

                signals.append(signal)

        return signals

    def _process_regular_data(
        self, endpoint_name: str, results: List[Dict], time_window: str
    ) -> List[Dict[str, Any]]:
        """Process regular data from OpenFDA API.

        Args:
            endpoint_name: Name of the endpoint
            results: Results from the API
            time_window: Time window being analyzed

        Returns:
            List of signal dictionaries
        """
        signals = []

        # For non-count queries, analyze the data and extract metrics
        if endpoint_name == "drug_events":
            # Count serious vs. non-serious outcomes
            serious_count = 0
            death_count = 0

            for event in results:
                # Check if patient outcomes include serious conditions
                patient = event.get("patient", {})
                if "reaction" in patient:
                    for reaction in patient.get("reaction", []):
                        if reaction.get("reactionoutcome") in [
                            "1",
                            "2",
                            "3",
                        ]:  # Serious outcomes
                            serious_count += 1

                # Check specifically for death outcomes
                if "seriousnessdeath" in event and event["seriousnessdeath"] == "1":
                    death_count += 1

            # Create signals
            if results:
                serious_signal = {
                    "name": f"fda_{endpoint_name}_{time_window}_serious_pct",
                    "value": float(serious_count) / len(results) * 100
                    if results
                    else 0,
                    "source": "openfda",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "metadata": {
                        "endpoint": endpoint_name,
                        "time_window": time_window,
                        "metric": "serious_outcomes_percentage",
                    },
                }

                death_signal = {
                    "name": f"fda_{endpoint_name}_{time_window}_death_pct",
                    "value": float(death_count) / len(results) * 100 if results else 0,
                    "source": "openfda",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "metadata": {
                        "endpoint": endpoint_name,
                        "time_window": time_window,
                        "metric": "death_outcomes_percentage",
                    },
                }

                # Save processed data
                save_processed_data(
                    f"{endpoint_name}_{time_window}_serious_pct",
                    serious_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=serious_signal["timestamp"],
                )

                save_processed_data(
                    f"{endpoint_name}_{time_window}_death_pct",
                    death_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=death_signal["timestamp"],
                )

                signals.append(serious_signal)
                signals.append(death_signal)

        elif "recalls" in endpoint_name or "enforcement" in endpoint_name:
            # Count by classification (I = most serious, III = least serious)
            classifications = Counter()
            voluntary_count = 0

            for recall in results:
                classification = recall.get("classification", "")
                classifications[classification] += 1

                # Count voluntary recalls
                if "voluntary" in recall.get("voluntary_mandated", "").lower():
                    voluntary_count += 1

            # Create signals for each classification
            for classification, count in classifications.items():
                classification_signal = {
                    "name": f"fda_{endpoint_name}_{time_window}_class_{classification}",
                    "value": float(count),
                    "source": "openfda",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "metadata": {
                        "endpoint": endpoint_name,
                        "time_window": time_window,
                        "classification": classification,
                    },
                }

                # Save processed data
                save_processed_data(
                    f"{endpoint_name}_{time_window}_class_{classification}",
                    classification_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=classification_signal["timestamp"],
                )

                signals.append(classification_signal)

            # Create signal for voluntary recalls percentage
            if results:
                voluntary_signal = {
                    "name": f"fda_{endpoint_name}_{time_window}_voluntary_pct",
                    "value": float(voluntary_count) / len(results) * 100
                    if results
                    else 0,
                    "source": "openfda",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "metadata": {
                        "endpoint": endpoint_name,
                        "time_window": time_window,
                        "metric": "voluntary_recalls_percentage",
                    },
                }

                # Save processed data
                save_processed_data(
                    f"{endpoint_name}_{time_window}_voluntary_pct",
                    voluntary_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=voluntary_signal["timestamp"],
                )

                signals.append(voluntary_signal)

        return signals

    def get_healthcare_metrics_info(self) -> Dict[str, Dict[str, Any]]:
        """Get explanatory information about healthcare metrics for data interpretation context."""
        return {
            "serious_outcomes_percentage": {
                "description": "Percentage of drug adverse events with serious outcomes",
                "significance": "Higher percentages may indicate increased safety concerns in pharmaceutical market",
            },
            "death_outcomes_percentage": {
                "description": "Percentage of drug adverse events resulting in death",
                "significance": "Critical safety indicator for pharmaceutical products",
            },
            "class_I": {
                "description": "Class I recalls - reasonable probability of serious adverse health consequences or death",
                "significance": "Most serious recall classification, may indicate significant market disruption",
            },
            "class_II": {
                "description": "Class II recalls - may cause temporary or medically reversible adverse health consequences",
                "significance": "Moderate severity recall classification",
            },
            "class_III": {
                "description": "Class III recalls - not likely to cause adverse health consequences",
                "significance": "Least severe recall classification",
            },
            "voluntary_recalls_percentage": {
                "description": "Percentage of recalls that were voluntary (vs. mandated by FDA)",
                "significance": "Indicator of industry self-regulation and compliance",
            },
        }
