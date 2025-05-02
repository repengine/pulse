"""Test for OpenFDA plugin functionality.

This test suite verifies:
1. Basic plugin initialization
2. API data fetching and error handling
3. Data persistence functionality
4. Output signal format correctness
"""
import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock
import datetime as dt

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from iris.iris_plugins_variable_ingestion.openfda_plugin import OpenfdaPlugin


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


class TestOpenFdaPlugin(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        # Create an OpenFDA plugin instance
        self.plugin = OpenfdaPlugin()
        
        # Sample mock data for OpenFDA API count results
        self.mock_count_data = {
            "meta": {
                "disclaimer": "API disclaimer text",
                "terms": "API terms of service",
                "license": "API license text",
                "last_updated": "2025-05-01",
                "results": {
                    "skip": 0,
                    "limit": 10,
                    "total": 125
                }
            },
            "results": [{"term": "Term 1", "count": 50}, {"term": "Term 2", "count": 40}],
            "count": [
                {"term": "Headache", "count": 50},
                {"term": "Nausea", "count": 40},
                {"term": "Dizziness", "count": 30},
                {"term": "Fatigue", "count": 25},
                {"term": "Vomiting", "count": 20}
            ]
        }
        
        # Sample mock data for OpenFDA API regular results (drug events)
        self.mock_drug_events_data = {
            "meta": {
                "disclaimer": "API disclaimer text",
                "terms": "API terms of service",
                "license": "API license text",
                "last_updated": "2025-05-01",
                "results": {
                    "skip": 0,
                    "limit": 10,
                    "total": 100
                }
            },
            "results": [
                {
                    "receivedate": "20250430",
                    "seriousnessdeath": "1",
                    "patient": {
                        "reaction": [
                            {"reactionoutcome": "1", "reactionmeddrapt": "Cardiac arrest"}
                        ]
                    }
                },
                {
                    "receivedate": "20250429",
                    "seriousnessdeath": "0",
                    "patient": {
                        "reaction": [
                            {"reactionoutcome": "2", "reactionmeddrapt": "Nausea"}
                        ]
                    }
                },
                {
                    "receivedate": "20250428",
                    "seriousnessdeath": "0",
                    "patient": {
                        "reaction": [
                            {"reactionoutcome": "0", "reactionmeddrapt": "Headache"}
                        ]
                    }
                }
            ]
        }
        
        # Sample mock data for OpenFDA API regular results (recalls)
        self.mock_recalls_data = {
            "meta": {
                "disclaimer": "API disclaimer text",
                "terms": "API terms of service",
                "license": "API license text",
                "last_updated": "2025-05-01",
                "results": {
                    "skip": 0,
                    "limit": 10,
                    "total": 50
                }
            },
            "results": [
                {
                    "report_date": "20250430",
                    "classification": "Class I",
                    "voluntary_mandated": "Voluntary"
                },
                {
                    "report_date": "20250429",
                    "classification": "Class II",
                    "voluntary_mandated": "FDA Mandated"
                },
                {
                    "report_date": "20250428",
                    "classification": "Class I",
                    "voluntary_mandated": "Voluntary"
                },
                {
                    "report_date": "20250427",
                    "classification": "Class III",
                    "voluntary_mandated": "Voluntary"
                }
            ]
        }
    
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.ensure_data_directory')
    def test_plugin_init(self, mock_ensure_dir):
        """Test plugin initialization."""
        plugin = OpenfdaPlugin()
        self.assertEqual(plugin.plugin_name, "openfda_plugin")
        self.assertTrue(plugin.enabled)
        self.assertEqual(plugin.concurrency, 2)
        mock_ensure_dir.assert_called_once_with("openfda")
    
    def test_get_search_query(self):
        """Test search query generation based on endpoint type."""
        # Test drug events endpoint
        query = self.plugin._get_search_query("drug_events", "20250401", "20250430")
        self.assertEqual(query, "receivedate:[20250401 TO 20250430]")
        
        # Test recalls endpoint
        query = self.plugin._get_search_query("drug_recalls", "20250401", "20250430")
        self.assertEqual(query, "report_date:[20250401 TO 20250430]")
        
        # Test NDC endpoint
        query = self.plugin._get_search_query("drug_ndc", "20250401", "20250430")
        self.assertEqual(query, "")  # No date filtering for NDC database
    
    def test_get_count_field(self):
        """Test count field selection based on endpoint type."""
        # Test drug events endpoint
        field = self.plugin._get_count_field("drug_events")
        self.assertEqual(field, "patient.reaction.reactionmeddrapt.exact")
        
        # Test drug recalls endpoint
        field = self.plugin._get_count_field("drug_recalls")
        self.assertEqual(field, "openfda.pharm_class_epc.exact")
    
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.requests.get')
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.save_request_metadata')
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.save_api_response')
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.save_processed_data')
    def test_process_count_data(self, mock_save_processed, mock_save_response, mock_save_metadata, mock_get):
        """Test processing of count/aggregation data."""
        # Mock the API response
        mock_get.return_value = MockResponse(self.mock_count_data, 200, {"Content-Type": "application/json"})
        
        # Process count data directly
        count_results = self.mock_count_data.get("count", [])
        signals = self.plugin._process_count_data("drug_events", "patient.reaction.reactionmeddrapt.exact", count_results, "recent")
        
        # Check that we got 5 signals (one for each reaction term)
        self.assertEqual(len(signals), 5)
        
        # Check signal structure for the first count item
        signal = signals[0]
        self.assertEqual(signal["name"], "fda_drug_events_recent_headache")
        self.assertEqual(signal["value"], 50.0)
        self.assertEqual(signal["source"], "openfda")
        self.assertIn("timestamp", signal)
        self.assertIn("metadata", signal)
        
        # Check that the metadata has the expected fields
        metadata = signal["metadata"]
        self.assertEqual(metadata["endpoint"], "drug_events")
        self.assertEqual(metadata["time_window"], "recent")
        self.assertEqual(metadata["term"], "Headache")
        self.assertEqual(metadata["rank"], 1)
    
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.requests.get')
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.save_request_metadata')
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.save_api_response')
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.save_processed_data')
    def test_process_drug_events_data(self, mock_save_processed, mock_save_response, mock_save_metadata, mock_get):
        """Test processing of drug events data."""
        # Mock the API response
        mock_get.return_value = MockResponse(self.mock_drug_events_data, 200, {"Content-Type": "application/json"})
        
        # Process drug events data directly
        results = self.mock_drug_events_data.get("results", [])
        signals = self.plugin._process_regular_data("drug_events", results, "recent")
        
        # Check that we got 2 signals (serious % and death %)
        self.assertEqual(len(signals), 2)
        
        # Check serious outcomes percentage
        serious_signal = signals[0]
        self.assertEqual(serious_signal["name"], "fda_drug_events_recent_serious_pct")
        self.assertAlmostEqual(serious_signal["value"], 66.67, places=2)  # 2/3 events are serious
        
        # Check death outcomes percentage
        death_signal = signals[1]
        self.assertEqual(death_signal["name"], "fda_drug_events_recent_death_pct")
        self.assertAlmostEqual(death_signal["value"], 33.33, places=2)  # 1/3 events resulted in death
    
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.requests.get')
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.save_request_metadata')
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.save_api_response')
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.save_processed_data')
    def test_process_recalls_data(self, mock_save_processed, mock_save_response, mock_save_metadata, mock_get):
        """Test processing of recalls data."""
        # Mock the API response
        mock_get.return_value = MockResponse(self.mock_recalls_data, 200, {"Content-Type": "application/json"})
        
        # Process recalls data directly
        results = self.mock_recalls_data.get("results", [])
        signals = self.plugin._process_regular_data("drug_recalls", results, "recent")
        
        # Check that we got at least 4 signals (3 classification counts + voluntary percentage)
        self.assertGreaterEqual(len(signals), 4)
        
        # Find classification signals
        class_i_signal = None
        class_ii_signal = None
        class_iii_signal = None
        voluntary_signal = None
        
        for signal in signals:
            if signal["name"] == "fda_drug_recalls_recent_class_Class I":
                class_i_signal = signal
            elif signal["name"] == "fda_drug_recalls_recent_class_Class II":
                class_ii_signal = signal
            elif signal["name"] == "fda_drug_recalls_recent_class_Class III":
                class_iii_signal = signal
            elif signal["name"] == "fda_drug_recalls_recent_voluntary_pct":
                voluntary_signal = signal
        
        # Check classification counts
        self.assertIsNotNone(class_i_signal)
        self.assertEqual(class_i_signal["value"], 2.0)  # 2 Class I recalls
        
        self.assertIsNotNone(class_ii_signal)
        self.assertEqual(class_ii_signal["value"], 1.0)  # 1 Class II recall
        
        self.assertIsNotNone(class_iii_signal)
        self.assertEqual(class_iii_signal["value"], 1.0)  # 1 Class III recall
        
        # Check voluntary percentage
        self.assertIsNotNone(voluntary_signal)
        self.assertEqual(voluntary_signal["value"], 75.0)  # 3/4 recalls are voluntary
    
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.requests.get')
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.save_request_metadata')
    @patch('iris.iris_plugins_variable_ingestion.openfda_plugin.save_api_response')
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
    
    def test_healthcare_metrics_info(self):
        """Test that healthcare metrics information is provided correctly."""
        info = self.plugin.get_healthcare_metrics_info()
        
        # Check that key metrics have information
        self.assertIn("serious_outcomes_percentage", info)
        self.assertIn("death_outcomes_percentage", info)
        self.assertIn("class_I", info)
        
        # Check that each metric has the required fields
        for metric, metric_info in info.items():
            self.assertIn("description", metric_info)
            self.assertIn("significance", metric_info)


if __name__ == "__main__":
    unittest.main()