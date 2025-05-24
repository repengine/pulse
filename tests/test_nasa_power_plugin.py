"""Test for NASA POWER plugin functionality.

This test suite verifies:
1. Basic plugin initialization
2. API data fetching and error handling
3. Data persistence functionality
4. Output signal format correctness
"""

import unittest
import os
import sys
from unittest.mock import patch

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from iris.iris_plugins_variable_ingestion.nasa_power_plugin import NasaPowerPlugin


class MockResponse:
    """Mock HTTP response object for testing."""

    def __init__(self, json_data, status_code=200, headers=None):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception(f"HTTP Error: {self.status_code}")


class TestNasaPowerPlugin(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        # Create a NASA POWER plugin instance
        self.plugin = NasaPowerPlugin()

        # Sample mock data for NASA POWER API
        self.mock_nasa_data = {
            "properties": {
                "parameter": {
                    "T2M": {"20250430": 22.5, "20250501": 23.2},
                    "T2M_MAX": {"20250430": 28.3, "20250501": 29.1},
                    "T2M_MIN": {"20250430": 17.2, "20250501": 18.5},
                    "PRECTOT": {"20250430": 2.3, "20250501": 0.0},
                    "RH2M": {"20250430": 68.5, "20250501": 65.2},
                    "WS10M": {"20250430": 3.2, "20250501": 4.1},
                    "ALLSKY_SFC_SW_DWN": {"20250430": 245.6, "20250501": 267.3},
                    "ALLSKY_SFC_LW_DWN": {"20250430": 378.2, "20250501": 385.1},
                }
            }
        }

    @patch(
        "iris.iris_plugins_variable_ingestion.nasa_power_plugin.ensure_data_directory"
    )
    def test_plugin_init(self, mock_ensure_dir):
        """Test plugin initialization."""
        plugin = NasaPowerPlugin()
        self.assertEqual(plugin.plugin_name, "nasa_power_plugin")
        self.assertTrue(plugin.enabled)
        self.assertEqual(plugin.concurrency, 2)
        mock_ensure_dir.assert_called_once_with("nasa_power")

    @patch("iris.iris_plugins_variable_ingestion.nasa_power_plugin.requests.get")
    @patch(
        "iris.iris_plugins_variable_ingestion.nasa_power_plugin.save_request_metadata"
    )
    @patch("iris.iris_plugins_variable_ingestion.nasa_power_plugin.save_api_response")
    @patch("iris.iris_plugins_variable_ingestion.nasa_power_plugin.save_processed_data")
    def test_fetch_signals(
        self, mock_save_processed, mock_save_response, mock_save_metadata, mock_get
    ):
        """Test fetching signals from NASA POWER API."""
        # Mock the API response
        mock_get.return_value = MockResponse(
            self.mock_nasa_data, 200, {"Content-Type": "application/json"}
        )

        # Call the fetch_signals method
        signals = self.plugin.fetch_signals()

        # Verify API was called correctly
        self.assertTrue(mock_get.called)
        self.assertTrue(mock_save_metadata.called)
        self.assertTrue(mock_save_response.called)

        # Check that we got the expected number of signals (8 parameters)
        self.assertEqual(len(signals), 8)

        # Check that signals have required fields and correct structure
        for signal in signals:
            self.assertIn("name", signal)
            self.assertIn("value", signal)
            self.assertIn("source", signal)
            self.assertIn("timestamp", signal)
            self.assertIn("metadata", signal)
            self.assertEqual(signal["source"], "nasa_power")

            # Check metadata structure
            self.assertIn("location", signal["metadata"])
            self.assertIn("lat", signal["metadata"])
            self.assertIn("lon", signal["metadata"])
            self.assertIn("parameter", signal["metadata"])

        # Check that processed data was saved (8 calls, one per parameter)
        self.assertEqual(mock_save_processed.call_count, 8)

    @patch("iris.iris_plugins_variable_ingestion.nasa_power_plugin.requests.get")
    @patch(
        "iris.iris_plugins_variable_ingestion.nasa_power_plugin.save_request_metadata"
    )
    @patch("iris.iris_plugins_variable_ingestion.nasa_power_plugin.save_api_response")
    def test_failed_api_call(self, mock_save_response, mock_save_metadata, mock_get):
        """Test error handling for failed API calls."""
        # Mock a failed API response
        mock_get.side_effect = Exception("API connection error")

        # Call the fetch_signals method
        signals = self.plugin.fetch_signals()

        # Check that we got no signals
        self.assertEqual(len(signals), 0)

        # Verify that error handling occurred
        self.assertTrue(mock_save_metadata.called)
        self.assertEqual(mock_save_response.call_count, 0)  # No valid response to save

    def test_get_most_recent_date_with_data(self):
        """Test logic to find the most recent date with valid data."""
        param_data = {
            "T2M": {"20250430": 22.5, "20250501": 23.2},
            "PRECTOT": {
                "20250430": 2.3,
                "20250501": -999,  # Missing data
            },
        }

        # Should find most recent valid date
        most_recent = self.plugin._get_most_recent_date_with_data(param_data)
        self.assertEqual(most_recent, "20250501")  # Has valid temperature

        # Test with all invalid data on the most recent date
        param_data = {
            "T2M": {"20250430": 22.5, "20250501": -999},
            "PRECTOT": {"20250430": 2.3, "20250501": -999},
        }

        most_recent = self.plugin._get_most_recent_date_with_data(param_data)
        self.assertEqual(
            most_recent, "20250430"
        )  # Falls back to earlier date with valid data

    def test_parameter_info(self):
        """Test that parameter information is provided correctly."""
        info = self.plugin.get_climate_parameter_info()

        # Check that all parameters have information
        self.assertGreaterEqual(len(info), 8)

        # Check that each parameter has the required fields
        for param, param_info in info.items():
            self.assertIn("unit", param_info)
            self.assertIn("description", param_info)
            self.assertIn("significance", param_info)


if __name__ == "__main__":
    unittest.main()
