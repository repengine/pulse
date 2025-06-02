"""Test for WikiData plugin functionality.

This test suite verifies:
1. Basic plugin initialization
2. SPARQL query construction and execution
3. Data persistence functionality
4. Processing of structured knowledge data into signals
"""

import unittest
import os
import sys
from unittest.mock import patch

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingestion.iris_plugins_variable_ingestion.wikidata_plugin import WikidataPlugin


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


class TestWikidataPlugin(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        # Create a Wikidata plugin instance
        self.plugin = WikidataPlugin()

        # Sample mock data for company info SPARQL query
        self.mock_company_data = {
            "head": {
                "vars": [
                    "companyLabel",
                    "foundingDate",
                    "employeeCount",
                    "revenueUSD",
                    "netIncomeUSD",
                    "country",
                    "industryLabel",
                    "ceoLabel",
                    "websiteLabel",
                ]
            },
            "results": {
                "bindings": [
                    {
                        "companyLabel": {
                            "type": "literal",
                            "value": "Microsoft Corporation",
                        },
                        "foundingDate": {
                            "type": "literal",
                            "value": "1975-04-04",
                            "datatype": "http://www.w3.org/2001/XMLSchema#date",
                        },
                        "employeeCount": {
                            "type": "literal",
                            "value": "181000",
                            "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                        },
                        "revenueUSD": {
                            "type": "literal",
                            "value": "168088000000",
                            "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                        },
                        "netIncomeUSD": {
                            "type": "literal",
                            "value": "61271000000",
                            "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                        },
                        "country": {
                            "type": "literal",
                            "value": "United States of America",
                        },
                        "industryLabel": {
                            "type": "literal",
                            "value": "software industry",
                        },
                        "ceoLabel": {"type": "literal", "value": "Satya Nadella"},
                    }
                ]
            },
        }

        # Sample mock data for country economic data SPARQL query
        self.mock_country_data = {
            "head": {
                "vars": [
                    "countryLabel",
                    "population",
                    "gdpUSD",
                    "gdpPerCapitaUSD",
                    "currencyLabel",
                    "inflationRate",
                    "unemploymentRate",
                    "centralBankLabel",
                ]
            },
            "results": {
                "bindings": [
                    {
                        "countryLabel": {
                            "type": "literal",
                            "value": "United States of America",
                        },
                        "population": {
                            "type": "literal",
                            "value": "331900000",
                            "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                        },
                        "gdpUSD": {
                            "type": "literal",
                            "value": "23000000000000",
                            "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                        },
                        "gdpPerCapitaUSD": {
                            "type": "literal",
                            "value": "69300",
                            "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                        },
                        "currencyLabel": {
                            "type": "literal",
                            "value": "United States dollar",
                        },
                        "inflationRate": {
                            "type": "literal",
                            "value": "3.7",
                            "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                        },
                        "unemploymentRate": {
                            "type": "literal",
                            "value": "3.8",
                            "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                        },
                    }
                ]
            },
        }

        # Sample mock data for central bank info SPARQL query
        self.mock_central_bank_data = {
            "head": {
                "vars": [
                    "centralBankLabel",
                    "foundingDate",
                    "countryLabel",
                    "currencyLabel",
                    "bankRatePercent",
                    "reservesUSD",
                    "governorLabel",
                ]
            },
            "results": {
                "bindings": [
                    {
                        "centralBankLabel": {
                            "type": "literal",
                            "value": "Federal Reserve System",
                        },
                        "foundingDate": {
                            "type": "literal",
                            "value": "1913-12-23",
                            "datatype": "http://www.w3.org/2001/XMLSchema#date",
                        },
                        "countryLabel": {
                            "type": "literal",
                            "value": "United States of America",
                        },
                        "currencyLabel": {
                            "type": "literal",
                            "value": "United States dollar",
                        },
                        "bankRatePercent": {
                            "type": "literal",
                            "value": "5.5",
                            "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                        },
                        "reservesUSD": {
                            "type": "literal",
                            "value": "3022000000000",
                            "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                        },
                    }
                ]
            },
        }

    @patch(
        "ingestion.iris_plugins_variable_ingestion.wikidata_plugin.ensure_data_directory"
    )
    def test_plugin_init(self, mock_ensure_dir):
        """Test plugin initialization."""
        plugin = WikidataPlugin()
        self.assertEqual(plugin.plugin_name, "wikidata_plugin")
        self.assertTrue(plugin.enabled)
        self.assertEqual(
            plugin.concurrency, 1
        )  # Lower concurrency due to API rate limits
        mock_ensure_dir.assert_called_once_with("wikidata")

    def test_get_query_type_for_domain(self):
        """Test query type selection based on domain."""
        # Test for known domains
        query_type = self.plugin._get_query_type_for_domain("companies")
        self.assertEqual(query_type, "company_info")

        query_type = self.plugin._get_query_type_for_domain("countries")
        self.assertEqual(query_type, "country_economic_data")

        query_type = self.plugin._get_query_type_for_domain("central_banks")
        self.assertEqual(query_type, "central_bank_info")

        query_type = self.plugin._get_query_type_for_domain("commodities")
        self.assertEqual(query_type, "commodity_info")

        # Test for unknown domain (should default to company_info)
        query_type = self.plugin._get_query_type_for_domain("unknown_domain")
        self.assertEqual(query_type, "company_info")

    @patch("ingestion.iris_plugins_variable_ingestion.wikidata_plugin.requests.get")
    @patch(
        "ingestion.iris_plugins_variable_ingestion.wikidata_plugin.save_request_metadata"
    )
    @patch(
        "ingestion.iris_plugins_variable_ingestion.wikidata_plugin.save_api_response"
    )
    def test_execute_sparql_query_company(
        self, mock_save_response, mock_save_metadata, mock_get
    ):
        """Test execution of SPARQL query for a company."""
        # Mock the API response
        mock_get.return_value = MockResponse(
            self.mock_company_data, 200, {"Content-Type": "application/json"}
        )

        # Execute the SPARQL query
        results = self.plugin._execute_sparql_query("Q219541", "company_info")

        # Check that the query was executed correctly
        self.assertTrue(mock_get.called)
        self.assertTrue(mock_save_metadata.called)
        self.assertTrue(mock_save_response.called)

        # Check that the results were processed correctly
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 1)

        # Check the processed result structure
        result = results[0]
        self.assertEqual(result["companyLabel"], "Microsoft Corporation")
        self.assertEqual(result["foundingDate"], "1975-04-04")
        self.assertEqual(result["employeeCount"], 181000.0)
        self.assertEqual(result["revenueUSD"], 168088000000.0)
        self.assertEqual(result["netIncomeUSD"], 61271000000.0)
        self.assertEqual(result["country"], "United States of America")
        self.assertEqual(result["industryLabel"], "software industry")
        self.assertEqual(result["ceoLabel"], "Satya Nadella")

    @patch("ingestion.iris_plugins_variable_ingestion.wikidata_plugin.requests.get")
    @patch(
        "ingestion.iris_plugins_variable_ingestion.wikidata_plugin.save_request_metadata"
    )
    @patch(
        "ingestion.iris_plugins_variable_ingestion.wikidata_plugin.save_api_response"
    )
    @patch(
        "ingestion.iris_plugins_variable_ingestion.wikidata_plugin.save_processed_data"
    )
    def test_process_company_results(
        self, mock_save_processed, mock_save_response, mock_save_metadata, mock_get
    ):
        """Test processing of company query results into signals."""
        # Mock the API response and execute the query
        mock_get.return_value = MockResponse(
            self.mock_company_data, 200, {"Content-Type": "application/json"}
        )
        results = self.plugin._execute_sparql_query("Q219541", "company_info")

        # Process the query results
        signals = self.plugin._process_query_results(
            "companies", "Q219541", "Microsoft", "company_info", results
        )

        # Check that we got the expected signals
        self.assertGreaterEqual(
            len(signals), 4
        )  # At least 4 signals (3 metrics + profile)

        # Find employee count signal
        employee_count_signal = None
        revenue_signal = None
        net_income_signal = None
        profile_signal = None

        for signal in signals:
            if signal["name"] == "wikidata_companies_microsoft_employee_count":
                employee_count_signal = signal
            elif signal["name"] == "wikidata_companies_microsoft_revenue":
                revenue_signal = signal
            elif signal["name"] == "wikidata_companies_microsoft_net_income":
                net_income_signal = signal
            elif signal["name"] == "wikidata_companies_microsoft_profile":
                profile_signal = signal

        # Check employee count signal
        self.assertIsNotNone(employee_count_signal)
        self.assertEqual(employee_count_signal["value"], 181000.0)
        self.assertEqual(employee_count_signal["source"], "wikidata")
        self.assertEqual(employee_count_signal["metadata"]["entity_id"], "Q219541")
        self.assertEqual(employee_count_signal["metadata"]["entity_name"], "Microsoft")
        self.assertEqual(employee_count_signal["metadata"]["domain"], "companies")
        self.assertEqual(
            employee_count_signal["metadata"]["data_type"], "employee_count"
        )
        self.assertEqual(employee_count_signal["metadata"]["unit"], "employees")

        # Check revenue signal
        self.assertIsNotNone(revenue_signal)
        self.assertEqual(revenue_signal["value"], 168088000000.0)

        # Check net income signal
        self.assertIsNotNone(net_income_signal)
        self.assertEqual(net_income_signal["value"], 61271000000.0)

        # Check profile signal
        self.assertIsNotNone(profile_signal)
        self.assertEqual(profile_signal["value"], 1.0)  # Presence indicator
        self.assertEqual(profile_signal["metadata"]["data_type"], "company_profile")
        self.assertIn("profile", profile_signal["metadata"])

        # Check that processed data was saved
        self.assertEqual(mock_save_processed.call_count, len(signals))

    @patch("ingestion.iris_plugins_variable_ingestion.wikidata_plugin.requests.get")
    @patch(
        "ingestion.iris_plugins_variable_ingestion.wikidata_plugin.save_request_metadata"
    )
    @patch(
        "ingestion.iris_plugins_variable_ingestion.wikidata_plugin.save_api_response"
    )
    @patch(
        "ingestion.iris_plugins_variable_ingestion.wikidata_plugin.save_processed_data"
    )
    def test_process_country_results(
        self, mock_save_processed, mock_save_response, mock_save_metadata, mock_get
    ):
        """Test processing of country query results into signals."""
        # Mock the API response and execute the query
        mock_get.return_value = MockResponse(
            self.mock_country_data, 200, {"Content-Type": "application/json"}
        )
        results = self.plugin._execute_sparql_query("Q30", "country_economic_data")

        # Process the query results
        signals = self.plugin._process_query_results(
            "countries", "Q30", "USA", "country_economic_data", results
        )

        # Check that we got the expected signals (5 metrics + profile)
        self.assertGreaterEqual(len(signals), 6)

        # Find specific signals
        population_signal = None
        gdp_signal = None
        inflation_signal = None
        unemployment_signal = None

        for signal in signals:
            if signal["name"] == "wikidata_countries_usa_population":
                population_signal = signal
            elif signal["name"] == "wikidata_countries_usa_gdp":
                gdp_signal = signal
            elif signal["name"] == "wikidata_countries_usa_inflation_rate":
                inflation_signal = signal
            elif signal["name"] == "wikidata_countries_usa_unemployment_rate":
                unemployment_signal = signal

        # Check population signal
        self.assertIsNotNone(population_signal)
        self.assertEqual(population_signal["value"], 331900000.0)

        # Check GDP signal
        self.assertIsNotNone(gdp_signal)
        self.assertEqual(gdp_signal["value"], 23000000000000.0)

        # Check inflation rate signal
        self.assertIsNotNone(inflation_signal)
        self.assertEqual(inflation_signal["value"], 3.7)

        # Check unemployment rate signal
        self.assertIsNotNone(unemployment_signal)
        self.assertEqual(unemployment_signal["value"], 3.8)

    @patch("ingestion.iris_plugins_variable_ingestion.wikidata_plugin.requests.get")
    @patch(
        "ingestion.iris_plugins_variable_ingestion.wikidata_plugin.save_request_metadata"
    )
    @patch(
        "ingestion.iris_plugins_variable_ingestion.wikidata_plugin.save_api_response"
    )
    def test_failed_api_call(self, mock_save_response, mock_save_metadata, mock_get):
        """Test error handling for failed API calls."""
        # Mock a failed API response
        mock_get.side_effect = Exception("API connection error")

        # Execute the SPARQL query
        results = self.plugin._execute_sparql_query("Q219541", "company_info")

        # Check that we got None for the results
        self.assertIsNone(results)

        # Verify that error handling occurred
        self.assertTrue(mock_save_metadata.called)
        self.assertEqual(mock_save_response.call_count, 0)  # No valid response to save

    @patch("random.choice")
    @patch(
        "ingestion.iris_plugins_variable_ingestion.wikidata_plugin.WikidataPlugin._execute_sparql_query"
    )
    @patch(
        "ingestion.iris_plugins_variable_ingestion.wikidata_plugin.WikidataPlugin._process_query_results"
    )
    def test_fetch_signals(
        self, mock_process_results, mock_execute_query, mock_random_choice
    ):
        """Test fetching signals workflow."""
        # Mock random.choice to return a specific entity
        mock_random_choice.return_value = {"id": "Q30", "name": "United States"}

        # Mock the SPARQL query execution
        mock_execute_query.return_value = [{"countryLabel": "United States of America"}]

        # Mock the processing of results
        mock_process_results.return_value = [
            {
                "name": "wikidata_countries_united_states_population",
                "value": 331900000.0,
            },
            {"name": "wikidata_countries_united_states_gdp", "value": 23000000000000.0},
        ]

        # Call the fetch_signals method
        signals = self.plugin.fetch_signals()

        # Check that the necessary methods were called
        self.assertTrue(mock_execute_query.called)
        self.assertTrue(mock_process_results.called)

        # Check that we got the expected signals
        self.assertEqual(len(signals), 2)

    def test_get_knowledge_domains(self):
        """Test getting knowledge domains."""
        domains = self.plugin.get_knowledge_domains()

        # Check that all expected domains are present
        self.assertIn("companies", domains)
        self.assertIn("countries", domains)
        self.assertIn("central_banks", domains)
        self.assertIn("commodities", domains)
        self.assertIn("economic_indicators", domains)

        # Check that each domain has entities
        for domain, entities in domains.items():
            self.assertGreater(len(entities), 0)

    def test_get_entity_by_name(self):
        """Test finding entity by name."""
        # Test finding a known entity
        entity = self.plugin.get_entity_by_name("Microsoft")
        self.assertIsNotNone(entity)
        self.assertEqual(entity["id"], "Q219541")
        self.assertEqual(entity["name"], "Microsoft")
        self.assertEqual(entity["domain"], "companies")

        # Test finding a known entity with case insensitivity
        entity = self.plugin.get_entity_by_name("microsoft")
        self.assertIsNotNone(entity)
        self.assertEqual(entity["id"], "Q219541")

        # Test with an unknown entity
        entity = self.plugin.get_entity_by_name("NonexistentEntity")
        self.assertIsNone(entity)


if __name__ == "__main__":
    unittest.main()
