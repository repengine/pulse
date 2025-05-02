"""
Module for calculating technical indicators from high-frequency data.
"""

import pandas as pd
import numpy as np
from data.high_frequency_data_access import HighFrequencyDataAccess
from data.high_frequency_data_store import HighFrequencyDataStore

class HighFrequencyIndicators:
    def __init__(self, data_access: HighFrequencyDataAccess):
        self.data_access = data_access

    def calculate_moving_average(self, variable_name: str, symbol: str, window: int, end_time: pd.Timestamp):
        """Calculates a simple moving average."""
        # Retrieve data
        # Updated method name and arguments based on HighFrequencyDataAccess
        data_points = self.data_access.get_data_by_variable_and_time_range(variable_name, end_time - pd.Timedelta(seconds=window*2), end_time) # Fetch enough data for the window
        
        if not data_points:
            return None

        # Convert list of dicts to pandas Series for calculation
        data = pd.DataFrame(data_points)
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data = data.set_index('timestamp').sort_index()

        if data.empty or variable_name not in data.columns:
             return None

        # Calculate MA
        ma = data[variable_name].rolling(window=window).mean().iloc[-1]
        return ma

    def calculate_intraday_volume(self, symbol: str, start_time: pd.Timestamp, end_time: pd.Timestamp):
        """Calculates total volume over an intraday period."""
        # Retrieve volume data
        # Updated method name and arguments based on HighFrequencyDataAccess
        volume_data_points = self.data_access.get_data_by_variable_and_time_range("volume", start_time, end_time)
        
        if not volume_data_points:
            return 0

        # Convert list of dicts to pandas Series for calculation
        volume_data = pd.DataFrame(volume_data_points)
        volume_data['timestamp'] = pd.to_datetime(volume_data['timestamp'])
        volume_data = volume_data.set_index('timestamp').sort_index()

        if volume_data.empty or "volume" not in volume_data.columns:
            return 0

        # Calculate total volume
        total_volume = volume_data["volume"].sum()
        return total_volume

    def calculate_intraday_volatility(self, variable_name: str, symbol: str, start_time: pd.Timestamp, end_time: pd.Timestamp):
        """Calculates intraday volatility (standard deviation of price changes)."""
        # Retrieve data
        # Updated method name and arguments based on HighFrequencyDataAccess
        data_points = self.data_access.get_data_by_variable_and_time_range(variable_name, start_time, end_time)
        
        if not data_points:
            return 0

        # Convert list of dicts to pandas Series for calculation
        data = pd.DataFrame(data_points)
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data = data.set_index('timestamp').sort_index()

        if data.empty or variable_name not in data.columns:
            return 0

        # Calculate price changes and volatility
        price_changes = data[variable_name].diff().dropna()
        volatility = price_changes.std()
        return volatility

    # Add more indicator calculation methods here

    def get_latest_high_frequency_indicators(self, symbols: list[str]) -> dict:
        """
        Calculates and returns the latest values for high-frequency indicators
        for a list of symbols.
        """
        # Use the data_access instance provided during initialization
        hfda = self.data_access
        latest_indicators = {}
        
        # Define the time window for "latest" data. This should be adjusted
        # based on the actual data frequency and desired calculation window.
        # For this example, we'll use the last hour from the current time.
        end_time = pd.Timestamp.now()
        start_time = end_time - pd.Timedelta(hours=1) # Example: last hour

        for symbol in symbols:
            # Calculate hf_ma_10
            # Assuming 'close' is the variable name for price data
            ma_10 = self.calculate_moving_average("close", symbol, 10, end_time)
            latest_indicators[f"hf_ma_10_{symbol}"] = ma_10

            # Calculate hf_intraday_volume
            volume = self.calculate_intraday_volume(symbol, start_time, end_time)
            latest_indicators[f"hf_intraday_volume_{symbol}"] = volume

            # Calculate hf_intraday_volatility
            # Assuming 'close' is the variable name for price data
            volatility = self.calculate_intraday_volatility("close", symbol, start_time, end_time)
            latest_indicators[f"hf_intraday_volatility_{symbol}"] = volatility

        return latest_indicators