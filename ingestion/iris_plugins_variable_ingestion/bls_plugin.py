import pandas as pd
import requests
import json
from datetime import datetime
from ingestion.iris_utils.ingestion_persistence import save_data_point_incremental
import os

# BLS API requires a registration key for higher volume, but allows some access without one.
# It's good practice to use a key if available.
BLS_API_KEY = os.environ.get("BLS_API_KEY")
BASE_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"


class BLSPlugin:
    def __init__(self):
        # API key is optional for basic usage, so we don't strictly require it.
        self.api_key = BLS_API_KEY

    def fetch_series_data(self, series_id, start_year=None, end_year=None):
        headers = {"Content-type": "application/json"}
        data = {
            "seriesid": [series_id],
            "startyear": str(start_year) if start_year else None,
            "endyear": str(end_year) if end_year else None,
            "catalog": False,
            "calculations": False,
            "annualaverage": False,
            "aspects": False,
            "datatype": "json",
        }
        if self.api_key:
            data["registrationkey"] = self.api_key

        # Remove None values from data
        data = {k: v for k, v in data.items() if v is not None}

        try:
            response = requests.post(BASE_URL, headers=headers, data=json.dumps(data))
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            result = response.json()

            if result and result["status"] == "REQUEST_SUCCEEDED":
                # BLS API returns a list of series, even if only one is requested
                if result["Results"]["series"]:
                    return result["Results"]["series"][0].get("data")
                else:
                    print(f"No data found for BLS series {series_id}.")
                    return None
            else:
                print(
                    f"BLS API request failed for {series_id}: {result.get('message', 'Unknown error')}"
                )
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching BLS data for {series_id}: {e}")
            return None

    def ingest_inflation_measures(self):
        # TODO: Find and add BLS series IDs for inflation measures (e.g., CPI)
        series_ids = {
            "CONSUMER_PRICE_INDEX_ALL_URBAN": "CUUR0000SA0",  # Example: CPI for All Urban Consumers, All Items
            # Add other relevant series IDs here (e.g., PPI)
        }
        print("Ingesting Inflation Measures from BLS...")
        for name, series_id in series_ids.items():
            # BLS API typically requires specifying year ranges
            # For simplicity, fetching data for a recent range.
            # TODO: Implement logic to fetch data for a comprehensive historical range.
            # Implement logic to fetch data for a comprehensive historical range.
            # BLS API allows fetching data up to 20 years at a time without a key.
            # For comprehensive history, we would need to make multiple calls or use a key.
            # For now, fetching from a fixed early year.
            observations = self.fetch_series_data(
                series_id, start_year=1900, end_year=datetime.now().year
            )

            if observations:
                for obs in observations:
                    # BLS date format is YYYY[M/Q]period (e.g., 2023M13 for annual, 2023Q4, 2023M12)
                    # Need to parse this into a standard date format.
                    year = int(obs["year"])
                    period = obs["period"]
                    periodicity = obs[
                        "periodicity"
                    ]  # 'M' for monthly, 'Q' for quarterly, 'A' for annual

                    if periodicity == "M":
                        month = int(period[1:])
                        # Use the last day of the month for monthly data timestamp
                        day = pd.Period(f"{year}-{month}").days_in_month
                        date_str = f"{year}-{month:02d}-{day:02d}"
                    elif periodicity == "Q":
                        quarter = int(period[1:])
                        # Use the last day of the last month of the quarter
                        month = quarter * 3
                        day = pd.Period(f"{year}-{month}").days_in_month
                        date_str = f"{year}-{month:02d}-{day:02d}"
                    elif periodicity == "A":
                        # Use the last day of the year for annual data timestamp
                        date_str = f"{year}-12-31"
                    else:
                        print(
                            f"Unknown periodicity {periodicity} for series {series_id}. Skipping observation."
                        )
                        continue

                    try:
                        value = float(obs["value"])
                        save_data_point_incremental(
                            name,
                            date_str,
                            value,
                            source_name="BLS",
                            metadata={"series_id": series_id},
                        )
                    except ValueError:
                        print(
                            f"Could not convert value '{obs['value']}' to float for series {series_id} on date {date_str}. Skipping observation."
                        )
                        continue

                print(
                    f"Successfully ingested {len(observations)} observations for {name}"
                )
            else:
                print(f"No data or error fetching data for {name} ({series_id})")

    def ingest_unemployment_labor_force(self):
        # TODO: Find and add BLS series IDs for unemployment and labor force participation
        series_ids = {
            "BLS_UNEMPLOYMENT_RATE_CIVILIAN": "LNS14000000",  # Example: Unemployment Rate - 16 Years & Over
            # Add other relevant series IDs here (e.g., Labor Force Participation Rate)
        }
        print("Ingesting Unemployment & Labor Force from BLS...")
        for name, series_id in series_ids.items():
            # BLS API typically requires specifying year ranges
            # For simplicity, fetching data for a recent range.
            # TODO: Implement logic to fetch data for a comprehensive historical range.
            # Implement logic to fetch data for a comprehensive historical range.
            # BLS API allows fetching data up to 20 years at a time without a key.
            # For comprehensive history, we would need to make multiple calls or use a key.
            # For now, fetching from a fixed early year.
            observations = self.fetch_series_data(
                series_id, start_year=1900, end_year=datetime.now().year
            )

            if observations:
                for obs in observations:
                    year = int(obs["year"])
                    period = obs["period"]
                    periodicity = obs["periodicity"]

                    if periodicity == "M":
                        month = int(period[1:])
                        day = pd.Period(f"{year}-{month}").days_in_month
                        date_str = f"{year}-{month:02d}-{day:02d}"
                    elif periodicity == "Q":
                        quarter = int(period[1:])
                        month = quarter * 3
                        day = pd.Period(f"{year}-{month}").days_in_month
                        date_str = f"{year}-{month:02d}-{day:02d}"
                    elif periodicity == "A":
                        date_str = f"{year}-12-31"
                    else:
                        print(
                            f"Unknown periodicity {periodicity} for series {series_id}. Skipping observation."
                        )
                        continue

                    try:
                        value = float(obs["value"])
                        save_data_point_incremental(
                            name,
                            date_str,
                            value,
                            source_name="BLS",
                            metadata={"series_id": series_id},
                        )
                    except ValueError:
                        print(
                            f"Could not convert value '{obs['value']}' to float for series {series_id} on date {date_str}. Skipping observation."
                        )
                        continue

                print(
                    f"Successfully ingested {len(observations)} observations for {name}"
                )
            else:
                print(f"No data or error fetching data for {name} ({series_id})")

    def ingest_all(self):
        print("Starting BLS data ingestion...")
        self.ingest_inflation_measures()
        self.ingest_unemployment_labor_force()
        print("BLS data ingestion finished.")


if __name__ == "__main__":
    # Example usage:
    # Set the BLS_API_KEY environment variable before running (optional for basic usage)
    # os.environ["BLS_API_KEY"] = "YOUR_BLS_API_KEY"
    # bls_plugin = BLSPlugin()
    # bls_plugin.ingest_all()
    pass  # Prevent execution when imported
