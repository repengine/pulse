# This module will handle high-frequency data ingestion from Alpha Vantage.
# It will interact with the AlphaVantagePlugin, handle entitlements,
# implement rate limiting, and process/store fetched data.

import time
import datetime as dt

# Import AlphaVantagePlugin and save_processed_data
from iris.iris_plugins_variable_ingestion.alpha_vantage_plugin import AlphaVantagePlugin
from data.high_frequency_data_store import HighFrequencyDataStore


class HighFrequencyIngestion:
    def __init__(
        self,
        alpha_vantage_plugin: AlphaVantagePlugin,
        entitlement: str = "delayed",
        rate_limit_per_minute: int = 150,
    ):
        """
        Initializes the HighFrequencyIngestion module.

        Args:
            alpha_vantage_plugin: An instance of AlphaVantagePlugin.
            entitlement: The data entitlement ('delayed' or 'realtime').
            rate_limit_per_minute: The maximum number of requests allowed per minute.
        """
        self.alpha_vantage_plugin = alpha_vantage_plugin
        self.entitlement = entitlement
        self.rate_limit_per_minute = rate_limit_per_minute
        self.request_timestamps = []
        self.data_store = HighFrequencyDataStore()

    def _wait_for_rate_limit(self):
        """
        Waits to ensure the API rate limit is not exceeded.
        """
        # Remove timestamps older than one minute
        current_time = time.time()
        self.request_timestamps = [
            ts for ts in self.request_timestamps if current_time - ts < 60
        ]

        # If the number of requests in the last minute exceeds the limit, wait
        if len(self.request_timestamps) >= self.rate_limit_per_minute:
            time_to_wait = 60 - (current_time - self.request_timestamps[0])
            if time_to_wait > 0:
                print(f"Rate limit reached. Waiting for {time_to_wait:.2f} seconds.")
                time.sleep(time_to_wait)

    def fetch_and_store_stock_data(self, interval: str = "1min"):
        """
        Fetches high-frequency stock data for all configured symbols and stores it.

        Args:
            interval: The data interval (e.g., '1min', '5min', '15min', '30min', '60min').
        """
        print(
            f"Fetching high-frequency stock data with entitlement: {self.entitlement}, interval: {interval}"
        )

        for var_name, symbol in self.alpha_vantage_plugin.STOCK_SYMBOLS.items():
            self._wait_for_rate_limit()
            self.request_timestamps.append(time.time())

            dataset_id = f"high_freq_stock_{symbol}_{interval}"
            params = {
                "function": "TIME_SERIES_INTRADAY",
                "symbol": symbol,
                "interval": interval,
                "outputsize": "compact",  # or "full"
                "datatype": "json",
                "entitlement": self.entitlement,  # Pass entitlement here
            }

            data = self.alpha_vantage_plugin._safe_get(params, dataset_id)

            if not data or f"Time Series ({interval})" not in data:
                print(f"Failed to fetch or invalid data for {symbol}")
                continue

            time_series_data = data[f"Time Series ({interval})"]

            # Process and store data incrementally
            processed_count = 0
            for timestamp_str, values in time_series_data.items():
                try:
                    # Convert timestamp string to ISO format
                    timestamp_dt = dt.datetime.strptime(
                        timestamp_str, "%Y-%m-%d %H:%M:%S"
                    )
                    iso_timestamp = timestamp_dt.isoformat()

                    processed_data_point = {
                        "timestamp": iso_timestamp,
                        "open": float(values["1. open"]),
                        "high": float(values["2. high"]),
                        "low": float(values["3. low"]),
                        "close": float(values["4. close"]),
                        "volume": int(values["5. volume"]),
                    }

                    # Store each metric as a separate data point
                    for metric, value in processed_data_point.items():
                        if (
                            metric != "timestamp"
                        ):  # timestamp is part of the data point, not a value to store separately
                            variable_name = f"{var_name}_{metric}"
                            self.data_store.store_data_point(
                                variable_name=variable_name,
                                timestamp=iso_timestamp,
                                value=value,
                            )
                    processed_count += 1

                except (ValueError, KeyError) as e:
                    print(
                        f"Error processing data point for {symbol} at {timestamp_str}: {e}"
                    )
                    # Optionally save error details

            print(f"Processed and stored {processed_count} data points for {symbol}")


# Example Usage (for testing)
if __name__ == "__main__":
    # Add the project root to sys.path to allow importing modules
    import sys
    import os

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Now import necessary modules after adding to path
    from iris.iris_plugins_variable_ingestion.alpha_vantage_plugin import (
        AlphaVantagePlugin,
    )
    from data.high_frequency_data_store import HighFrequencyDataStore

    # Replace with your actual API key or ensure ALPHA_VANTAGE_KEY env var is set
    # api_key = "YOUR_ALPHA_VANTAGE_API_KEY"
    # if not api_key:
    #     print("Please set the ALPHA_VANTAGE_KEY environment variable or provide it directly.")
    # else:
    #     # Create an instance of AlphaVantagePlugin
    #     av_plugin = AlphaVantagePlugin()
    #
    #     # Create an instance of HighFrequencyIngestion with the plugin and desired entitlement
    #     # Use 'realtime' for real-time data if you have the entitlement, otherwise use 'delayed'
    #     ingestion_module = HighFrequencyIngestion(alpha_vantage_plugin=av_plugin, entitlement='delayed')
    #
    #     # Fetch and store 1-minute interval data for all configured symbols
    #     ingestion_module.fetch_and_store_stock_data(interval='1min')

    print(
        "HighFrequencyIngestion module created. Add your API key/set env var and uncomment the example usage to test."
    )
    pass
