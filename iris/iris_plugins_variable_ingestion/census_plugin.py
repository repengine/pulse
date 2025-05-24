import requests
import logging
from datetime import datetime
from iris.iris_utils.ingestion_persistence import save_data_point_incremental
import os
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Census Bureau API base URL
BASE_URL = "https://api.census.gov/data/"


class CensusPlugin:
    def __init__(self):
        # Census Bureau APIs may or may not require a key depending on the dataset and usage volume.
        # It's good practice to include a key parameter if available.
        self.api_key = os.environ.get(
            "CENSUS_API_KEY"
        )  # TODO: Add CENSUS_API_KEY configuration

    def fetch_data(self, endpoint, params):
        """
        Fetch data from the Census API with pagination handling.

        Args:
            endpoint: API endpoint (e.g., '2023/eits/resretaill')
            params: Dictionary of query parameters

        Returns:
            List of observations or None on error
        """
        # Add API key to params if available
        if self.api_key:
            params["key"] = self.api_key

        url = f"{BASE_URL}{endpoint}"
        all_observations = []

        # Census pagination typically uses 'offset' or specific page parameters
        # This implementation handles both 'offset' based and 'vintage' based pagination
        offset = 0
        limit = params.get("limit", 1000)  # Default limit per request
        max_results = params.get(
            "max_results", 50000
        )  # Safety limit to prevent infinite loops

        # Create a copy of params to modify for pagination
        current_params = params.copy()

        # If a limit is specified in params, use it for pagination
        if "limit" in current_params:
            current_params["offset"] = offset

        while url and len(all_observations) < max_results:
            try:
                logging.info(
                    f"Fetching Census data from {url} with params {current_params}"
                )
                response = requests.get(url, params=current_params)
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
                data = response.json()

                # Census API typically returns a list of lists, with the first list being headers
                if data and len(data) > 1:
                    headers = data[0]
                    observations = [dict(zip(headers, row)) for row in data[1:]]
                    batch_size = len(observations)
                    all_observations.extend(observations)

                    # Log progress
                    logging.info(
                        f"Retrieved {batch_size} records, total: {len(all_observations)}"
                    )

                    # Check if we received fewer records than requested - indicates end of data
                    if batch_size < limit:
                        logging.info(
                            "Received fewer records than requested, ending pagination"
                        )
                        break

                    # Update offset for next request
                    offset += batch_size
                    if "limit" in current_params:
                        current_params["offset"] = offset
                    else:
                        # If no explicit pagination, stop after first page
                        break
                else:
                    logging.warning(
                        f"No data found for Census endpoint {endpoint} with params {current_params}."
                    )
                    break

            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching Census data from {endpoint}: {e}")
                return None  # Return None on error

        logging.info(
            f"Completed Census data retrieval with {len(all_observations)} total records"
        )
        return all_observations if all_observations else None

    def parse_date(self, date_string):
        """
        Parse a date string from the Census API using multiple format attempts.
        Supports various Census date formats including year-month, year only, and full dates.

        Args:
            date_string: Date string from Census API

        Returns:
            datetime object or None if parsing fails
        """
        # Census date formats can vary by endpoint:
        # - YYYY (annual data)
        # - YYYYMM (monthly data without separators)
        # - YYYY-MM (monthly data with separators)
        # - YYYYMMDD (daily data without separators)
        # - YYYY-MM-DD (daily data with separators)
        # - YYYY-QX (quarterly data with Q1, Q2, Q3, Q4 format)

        # Handle quarterly format separately
        if "Q" in date_string:
            try:
                # Extract year and quarter (e.g., "2023-Q1" -> year=2023, quarter=1)
                year_str, quarter_str = date_string.split("-Q")
                year = int(year_str)
                quarter = int(quarter_str)

                # Convert quarter to month (Q1->1, Q2->4, Q3->7, Q4->10)
                month = 1 + (quarter - 1) * 3

                # Create a date object for the first day of the quarter
                return datetime(year, month, 1)
            except (ValueError, IndexError):
                pass

        # Try standard formats
        for fmt in ("%Y%m", "%Y-%m", "%Y/%m", "%Y", "%Y%m%d", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue

        # If all parsing attempts fail, log and return None
        logging.warning(f"Could not parse date format for '{date_string}'")
        return None

    def ingest_retail_sales(self):
        """
        Ingest retail sales data from the U.S. Census Bureau.
        Uses the Monthly Retail Trade Survey and Annual Retail Trade Survey data.
        """
        # Census API endpoint for Monthly Retail Trade Survey
        # Using the Economic Indicators Time Series API
        endpoint = (
            "2023/eits/resretaill"  # Monthly Retail Trade Survey - U.S. Retail Sales
        )
        params = {
            "get": "BESTS2019001,UNIT,GEO_ID,TIME",  # BESTS2019001 is retail sales value
            "time": "from+2000-01+to+2023-12",  # Get historical data (adjust as needed)
            "for": "us:*",  # National level data
            "limit": 1000,  # Records per page
            "category_code": "44X72",  # Total Retail And Food Services Sales
        }
        logging.info("Ingesting Retail Sales from U.S. Census Bureau...")

        # Fetch data with pagination handling
        observations = self.fetch_data(endpoint, params)

        if observations:
            for obs in observations:
                # TODO: Adapt this based on the actual Census API response structure and date format
                # Assuming a structure with 'DATE', 'VALUE', and relevant identifiers
                timestamp_str = obs.get("DATE")
                value = obs.get("VALUE")
                # Identify other relevant identifiers (e.g., geographic level, industry code)
                # location = obs.get('state') # Example identifier

                if timestamp_str and value is not None:
                    try:
                        # Use the enhanced date parsing method
                        date_obj = self.parse_date(timestamp_str)

                        if date_obj:
                            timestamp = (
                                date_obj.isoformat()
                            )  # Convert to ISO format for consistency
                        else:
                            logging.warning(
                                f"Could not parse date format for '{timestamp_str}'. Skipping observation."
                            )
                            continue

                        # Extract additional metadata if available
                        category = obs.get("category_code", "TOTAL")
                        geo_id = obs.get("GEO_ID", "US")
                        unit = obs.get("UNIT", "Millions of Dollars")

                        # Construct a more specific variable name
                        variable_name = f"RETAIL_SALES_{category.replace('-', '_')}"

                        data_point = {
                            "variable_name": variable_name,
                            "timestamp": timestamp,
                            "value": float(value),
                            "source": "US_CENSUS_BUREAU",
                            "endpoint": endpoint,
                            "unit": unit,
                            "geo_id": geo_id,
                            "metadata": {
                                "category": category,
                                "collection_timestamp": datetime.now().isoformat(),
                            },
                            "original_obs": obs,  # Store original observation for debugging/traceability
                        }
                        save_data_point_incremental(data_point, "economic_indicators")
                        logging.debug(
                            f"Saved retail sales data point for {timestamp}: {value} {unit}"
                        )
                    except ValueError as e:
                        logging.error(
                            f"Could not convert value '{value}' to float for Retail Sales on date {timestamp_str}: {str(e)}"
                        )
                        continue
            print(
                f"Successfully ingested {len(observations)} observations for Retail Sales."
            )
        else:
            print("No data or error fetching data for Retail Sales.")

    def ingest_housing_starts_permits(self):
        """
        Ingest housing starts and building permits data from the U.S. Census Bureau.
        Uses the New Residential Construction data series.
        """
        # Census API endpoint for New Residential Construction (Housing Starts and Permits)
        # Using the Economic Indicators Time Series API
        endpoint = "2023/eits/newresconst"  # New Residential Construction

        # First, fetch housing starts data
        starts_params = {
            "get": "STARTS,UNIT,TIME",  # STARTS is housing starts value
            "time": "from+2000-01+to+2023-12",  # Get historical data (adjust as needed)
            "for": "us:*",  # National level data
            "seasonally_adj": "yes",  # Use seasonally adjusted data
            "limit": 1000,  # Records per page
        }
        logging.info("Ingesting Housing Starts from U.S. Census Bureau...")

        # Fetch housing starts data with pagination handling
        starts_observations = self.fetch_data(endpoint, starts_params)

        # Now fetch building permits data
        permits_params = {
            "get": "PERMITS,UNIT,TIME",  # PERMITS is building permits value
            "time": "from+2000-01+to+2023-12",  # Get historical data (adjust as needed)
            "for": "us:*",  # National level data
            "seasonally_adj": "yes",  # Use seasonally adjusted data
            "limit": 1000,  # Records per page
        }
        logging.info("Ingesting Building Permits from U.S. Census Bureau...")

        # Fetch building permits data with pagination handling
        permits_observations = self.fetch_data(endpoint, permits_params)

        # Process both datasets
        observations = []
        if starts_observations:
            observations.extend(starts_observations)
        if permits_observations:
            observations.extend(permits_observations)

        if observations:
            for obs in observations:
                # TODO: Adapt this based on the actual Census API response structure and date format
                # Assuming a structure with 'DATE', 'VALUE', and relevant identifiers
                timestamp_str = obs.get("DATE")
                value = obs.get("VALUE")
                # Identify other relevant identifiers (e.g., geographic level, type)
                # region = obs.get('region') # Example identifier

                if timestamp_str and value is not None:
                    try:
                        # Use the enhanced date parsing method
                        date_obj = self.parse_date(timestamp_str)

                        if date_obj:
                            timestamp = (
                                date_obj.isoformat()
                            )  # Convert to ISO format for consistency
                        else:
                            logging.warning(
                                f"Could not parse date format for '{timestamp_str}'. Skipping observation."
                            )
                            continue

                        # Determine if this is a housing start or permit based on available fields
                        data_type = "STARTS" if "STARTS" in obs else "PERMITS"

                        # Extract additional metadata if available
                        unit = obs.get("UNIT", "Thousands of Units")
                        seasonally_adj = obs.get("seasonally_adj", "yes")

                        # Construct a specific variable name
                        variable_name = f"HOUSING_{data_type}"
                        if seasonally_adj.lower() == "yes":
                            variable_name += "_SA"  # Seasonally Adjusted

                        data_point = {
                            "variable_name": variable_name,
                            "timestamp": timestamp,
                            "value": float(value),
                            "source": "US_CENSUS_BUREAU",
                            "endpoint": endpoint,
                            "unit": unit,
                            "metadata": {
                                "seasonally_adjusted": seasonally_adj.lower() == "yes",
                                "data_type": data_type,
                                "collection_timestamp": datetime.now().isoformat(),
                            },
                            "original_obs": obs,  # Store original observation for debugging/traceability
                        }
                        save_data_point_incremental(data_point, "economic_indicators")
                        logging.debug(
                            f"Saved {data_type} data point for {timestamp}: {value} {unit}"
                        )
                    except ValueError as e:
                        logging.error(
                            f"Could not convert value '{value}' to float for {data_type} on date {timestamp_str}: {str(e)}"
                        )
                        continue
            print(
                f"Successfully ingested {len(observations)} observations for Housing Starts & Building Permits."
            )
        else:
            print(
                "No data or error fetching data for Housing Starts & Building Permits."
            )

    def ingest_all(self):
        """
        Ingest all available Census Bureau data series.
        Includes rate limiting to avoid API throttling.
        """
        logging.info("Starting Census Bureau data ingestion...")

        # Ingest retail sales data
        self.ingest_retail_sales()

        # Add a short delay to avoid hitting rate limits
        time.sleep(2)

        # Ingest housing starts and permits data
        self.ingest_housing_starts_permits()

        logging.info("Census Bureau data ingestion finished.")


if __name__ == "__main__":
    # Example usage:
    # Set the CENSUS_API_KEY environment variable before running (optional)
    # os.environ["CENSUS_API_KEY"] = "YOUR_CENSUS_API_KEY"
    # census_plugin = CensusPlugin()
    # census_plugin.ingest_all()
    pass  # Prevent execution when imported
