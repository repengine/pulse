import requests
from ingestion.iris_utils.ingestion_persistence import save_data_point_incremental
import os

# TODO: Add FRED API key configuration
FRED_API_KEY = os.environ.get("FRED_API_KEY")
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


class FREDPlugin:
    def __init__(self):
        if not FRED_API_KEY:
            print("FRED_API_KEY not found in environment variables.")
            # In a real scenario, you might raise an error or handle this differently
            self.api_available = False
        else:
            self.api_available = True

    def fetch_series_data(self, series_id, start_date=None, end_date=None):
        if not self.api_available:
            print(f"Skipping FRED data fetch for {series_id} due to missing API key.")
            return None

        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "observation_start": start_date,
            "observation_end": end_date,
        }

        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            return data.get("observations")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching FRED data for {series_id}: {e}")
            return None

    def ingest_interest_rates_yield_curves(self):
        # TODO: Find and add FRED series IDs for interest rates and yield curves
        series_ids = {
            "US_TREASURY_YIELD_10Y": "GS10",  # 10-Year Treasury Constant Maturity Rate
            "US_TREASURY_YIELD_3M": "DTB3",  # 3-Month Treasury Bill Secondary Market Rate
            "US_TREASURY_YIELD_2Y": "GS2",  # 2-Year Treasury Constant Maturity Rate
            "US_TREASURY_YIELD_30Y": "GS30",  # 30-Year Treasury Constant Maturity Rate
        }
        print("Ingesting Interest Rates & Yield Curves from FRED...")
        for name, series_id in series_ids.items():
            # Fetch data from a comprehensive historical range
            observations = self.fetch_series_data(series_id, start_date="1900-01-01")
            if observations:
                for obs in observations:
                    if obs["value"] != ".":  # FRED uses '.' for missing values
                        data_point = {
                            "variable_name": name,
                            "timestamp": obs["date"],
                            "value": float(obs["value"]),
                            "source": "FRED",
                            "series_id": series_id,
                        }
                        save_data_point_incremental(data_point, "economic_indicators")
                print(
                    f"Successfully ingested {len(observations)} observations for {name}"
                )
            else:
                print(f"No data or error fetching data for {name} ({series_id})")

    def ingest_industrial_production_pmi(self):
        # TODO: Find and add FRED series IDs for industrial production
        series_ids = {
            "INDUSTRIAL_PRODUCTION_INDEX": "INDPRO",  # Industrial Production Index
            "MANUFACTURING_PRODUCTION_INDEX": "IPMAN",  # Manufacturing Sector: Production Index
            "CAPACITY_UTILIZATION_RATE": "TCU",  # Capacity Utilization: Total Industry
        }
        print("Ingesting Industrial Production from FRED...")
        for name, series_id in series_ids.items():
            # Fetch data from a comprehensive historical range
            observations = self.fetch_series_data(series_id, start_date="1900-01-01")
            if observations:
                for obs in observations:
                    if obs["value"] != ".":
                        data_point = {
                            "variable_name": name,
                            "timestamp": obs["date"],
                            "value": float(obs["value"]),
                            "source": "FRED",
                            "series_id": series_id,
                        }
                        save_data_point_incremental(data_point, "economic_indicators")
                print(
                    f"Successfully ingested {len(observations)} observations for {name}"
                )
            else:
                print(f"No data or error fetching data for {name} ({series_id})")

    def ingest_unemployment_labor_force(self):
        # TODO: Find and add FRED series IDs for unemployment and labor force
        # participation
        series_ids = {
            "UNEMPLOYMENT_RATE": "UNRATE",  # Unemployment Rate
            "LABOR_FORCE_PARTICIPATION_RATE": "CIVPART",  # Labor Force Participation Rate
        }
        print("Ingesting Unemployment & Labor Force from FRED...")
        for name, series_id in series_ids.items():
            # Fetch data from a comprehensive historical range
            observations = self.fetch_series_data(series_id, start_date="1900-01-01")
            if observations:
                for obs in observations:
                    if obs["value"] != ".":
                        data_point = {
                            "variable_name": name,
                            "timestamp": obs["date"],
                            "value": float(obs["value"]),
                            "source": "FRED",
                            "series_id": series_id,
                        }
                        save_data_point_incremental(data_point, "economic_indicators")
                print(
                    f"Successfully ingested {len(observations)} observations for {name}"
                )
            else:
                print(f"No data or error fetching data for {name} ({series_id})")

    def ingest_money_supply(self):
        # TODO: Find and add FRED series IDs for money supply aggregates
        series_ids = {
            "MONEY_SUPPLY_M2": "M2SL",  # M2 Money Stock
            "MONEY_SUPPLY_M1": "M1SL",  # M1 Money Stock
        }
        print("Ingesting Money Supply from FRED...")
        for name, series_id in series_ids.items():
            # Fetch data from a comprehensive historical range
            observations = self.fetch_series_data(series_id, start_date="1900-01-01")
            if observations:
                for obs in observations:
                    if obs["value"] != ".":
                        data_point = {
                            "variable_name": name,
                            "timestamp": obs["date"],
                            "value": float(obs["value"]),
                            "source": "FRED",
                            "series_id": series_id,
                        }
                        save_data_point_incremental(data_point, "economic_indicators")
                print(
                    f"Successfully ingested {len(observations)} observations for {name}"
                )
            else:
                print(f"No data or error fetching data for {name} ({series_id})")

    def ingest_exchange_rates(self):
        # TODO: Find and add FRED series IDs for exchange rates
        series_ids = {
            "US_EURO_EXCHANGE_RATE": "DEXUSEU",  # U.S. / Euro Foreign Exchange Rate
            "US_YEN_EXCHANGE_RATE": "DEXJPUS",  # U.S. / Japanese Yen Foreign Exchange Rate
            "US_POUND_EXCHANGE_RATE": "DEXUSUK",  # U.S. / U.K. Pound Exchange Rate
        }
        print("Ingesting Exchange Rates from FRED...")
        for name, series_id in series_ids.items():
            # Fetch data from a comprehensive historical range
            observations = self.fetch_series_data(series_id, start_date="1900-01-01")
            if observations:
                for obs in observations:
                    if obs["value"] != ".":
                        data_point = {
                            "variable_name": name,
                            "timestamp": obs["date"],
                            "value": float(obs["value"]),
                            "source": "FRED",
                            "series_id": series_id,
                        }
                        save_data_point_incremental(data_point, "economic_indicators")
                print(
                    f"Successfully ingested {len(observations)} observations for {name}"
                )
            else:
                print(f"No data or error fetching data for {name} ({series_id})")

    def ingest_credit_spreads_volatility(self):
        # TODO: Find and add FRED series IDs for credit spreads and volatility indices
        series_ids = {
            "ICE_BOFA_Baa_SPREAD": "BAMLC0A4C",  # ICE BofA US Corporate BAA Option-Adjusted Spread
            # ICE BofA US High Yield Option-Adjusted Spread
            "ICE_BOFA_US_HIGH_YIELD_SPREAD": "BAMLH0A0HYM2",
        }
        print("Ingesting Credit Spreads from FRED...")
        for name, series_id in series_ids.items():
            # Fetch data from a comprehensive historical range
            observations = self.fetch_series_data(series_id, start_date="1900-01-01")
            if observations:
                for obs in observations:
                    if obs["value"] != ".":
                        data_point = {
                            "variable_name": name,
                            "timestamp": obs["date"],
                            "value": float(obs["value"]),
                            "source": "FRED",
                            "series_id": series_id,
                        }
                        save_data_point_incremental(data_point, "economic_indicators")
                print(
                    f"Successfully ingested {len(observations)} observations for {name}"
                )
            else:
                print(f"No data or error fetching data for {name} ({series_id})")

    def ingest_housing_starts_permits(self):
        # TODO: Find and add FRED series IDs for housing starts and building permits
        series_ids = {
            # Housing Starts: Total: New Privately-Owned Housing Units Started
            "HOUSING_STARTS_TOTAL": "HOUST",
            # New Privately-Owned Housing Units Authorized by Building Permits: Total
            "BUILDING_PERMITS_TOTAL": "PERMIT",
        }
        print("Ingesting Housing Starts & Building Permits from FRED...")
        for name, series_id in series_ids.items():
            # Fetch data from a comprehensive historical range
            observations = self.fetch_series_data(series_id, start_date="1900-01-01")
            if observations:
                for obs in observations:
                    if obs["value"] != ".":
                        data_point = {
                            "variable_name": name,
                            "timestamp": obs["date"],
                            "value": float(obs["value"]),
                            "source": "FRED",
                            "series_id": series_id,
                        }
                        save_data_point_incremental(data_point, "economic_indicators")
                print(
                    f"Successfully ingested {len(observations)} observations for {name}"
                )
            else:
                print(f"No data or error fetching data for {name} ({series_id})")

    def ingest_all(self):
        print("Starting FRED data ingestion...")
        self.ingest_interest_rates_yield_curves()
        self.ingest_industrial_production_pmi()
        self.ingest_unemployment_labor_force()
        self.ingest_money_supply()
        self.ingest_exchange_rates()
        self.ingest_credit_spreads_volatility()
        self.ingest_housing_starts_permits()
        print("FRED data ingestion finished.")


if __name__ == "__main__":
    # Example usage:
    # Set the FRED_API_KEY environment variable before running
    # os.environ["FRED_API_KEY"] = "YOUR_FRED_API_KEY"
    # fred_plugin = FREDPlugin()
    # fred_plugin.ingest_all()
    pass  # Prevent execution when imported
