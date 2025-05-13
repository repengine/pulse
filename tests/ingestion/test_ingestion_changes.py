"""
Test script to verify ingestion changes for Nasdaq alternatives.
This tests:
1. Manual OPEC plugin for orb_price
2. Alpha Vantage for GDP
3. Removal of inaccessible Nasdaq datasets

Usage:
    python test_ingestion_changes.py
"""

import os
import sys
import json
from datetime import datetime

# Ensure the Pulse directory is in the Python path
sys.path.append(os.getcwd())

# Import the registry and plugins
from core.variable_registry import registry
from iris.iris_plugins import IrisPluginManager
from iris.iris_plugins_variable_ingestion.manual_opec_plugin import ManualOPECPlugin
from iris.iris_plugins_variable_ingestion.alpha_vantage_plugin import AlphaVantagePlugin
from iris.iris_plugins_variable_ingestion.nasdaq_plugin import nasdaq_plugin
from iris.iris_plugins_variable_ingestion.high_frequency_indicator_plugin import HighFrequencyIndicatorPlugin
from data.high_frequency_data_access import HighFrequencyDataAccess
from data.high_frequency_data_store import HighFrequencyDataStore # Import HighFrequencyDataStore
from iris.high_frequency_indicators import HighFrequencyIndicators
from iris.iris_plugins_variable_ingestion.alpha_vantage_plugin import AlphaVantagePlugin # Import again to access STOCK_SYMBOLS

def test_manual_opec_plugin():
    """Test the manual OPEC plugin for orb_price."""
    print("\n===== Testing Manual OPEC Plugin =====")
    plugin = ManualOPECPlugin()
    
    # Check if plugin is enabled
    assert plugin.enabled, "Manual OPEC plugin is not enabled. Check if data files exist."
    
    # Fetch signals from the plugin
    signals = plugin.fetch_signals()
    
    # Check if we got any signals
    assert signals, "No signals returned from Manual OPEC plugin."
    
    # Look for orb_price signals
    orb_signals = [s for s in signals if s.get("name") == "orb_price"]
    assert orb_signals, "No orb_price signals found in the result."
    
    # Print the result
    print(f"SUCCESS: Found {len(orb_signals)} orb_price signals.")
    print(f"Latest orb_price: {orb_signals[0]['value']} from {orb_signals[0]['timestamp']}")

def test_alpha_vantage_plugin():
    """Test the Alpha Vantage plugin for GDP data."""
    print("\n===== Testing Alpha Vantage Plugin =====")
    
    # Check if ALPHA_VANTAGE_KEY is set
    assert os.environ.get("ALPHA_VANTAGE_KEY"), "ALPHA_VANTAGE_KEY environment variable not set."
    
    plugin = AlphaVantagePlugin()
    
    # Check if plugin is enabled
    assert plugin.enabled, "Alpha Vantage plugin is not enabled. Check API key."
    
    # Override the economic indicator selection to force GDP retrieval
    # Save the original method
    original_fetch = plugin.fetch_signals
    
    try:
        # Mock fetch_signals to directly call _fetch_economic_data for GDP
        def mock_fetch():
            signals = []
            # Force fetch GDP
            gdp_signals = plugin._fetch_economic_data("gdp", "REAL_GDP")
            if gdp_signals:
                signals.extend(gdp_signals)
            return signals
        
        # Replace the fetch_signals method temporarily
        plugin.fetch_signals = mock_fetch
        
        # Fetch signals
        signals = plugin.fetch_signals()
        
        # Check if we got any signals
        assert signals, "No signals returned from Alpha Vantage plugin."
        
        # Look for GDP signals
        gdp_signals = [s for s in signals if s.get("name") == "gdp"]
        assert gdp_signals, "No GDP signals found in the result."
        
        # Print the result
        print(f"SUCCESS: Found GDP data.")
        print(f"Latest GDP value: {gdp_signals[0]['value']} from {gdp_signals[0]['timestamp']}")
    
    finally:
        # Restore the original method
        plugin.fetch_signals = original_fetch

def test_nasdaq_plugin():
    """Test that the Nasdaq plugin no longer attempts to fetch inaccessible datasets."""
    print("\n===== Testing Nasdaq Plugin Changes =====")
    
    # Call the Nasdaq plugin
    signals = nasdaq_plugin()
    
    # If no API key is set, the plugin should return an empty list without errors
    if not os.environ.get("NASDAQ_API_KEY"):
        assert signals == [], "Expected empty list when NASDAQ_API_KEY is not set."
        print("INFO: No NASDAQ_API_KEY set, plugin correctly returned empty list.")
    
    # If we have signals, check that they don't include any from the removed datasets
    removed_datasets = ["LBMA/GOLD", "FRED/GDP", "ODA/PALUM_USD", "OPEC/ORB", "WORLDBANK/WLD_SP_POP_TOTL"]
    for signal in signals:
        assert signal.get("dataset_id") not in removed_datasets, f"Found signal for removed dataset: {signal.get('dataset_id')}"
    
    # Check if we're seeing mock data (fallback mode)
    if signals and signals[0].get("source") == "nasdaq_dl_mock":
        print("INFO: Nasdaq plugin used mock data due to no accessible datasets.")
    
    print("SUCCESS: Nasdaq plugin no longer attempts to fetch inaccessible datasets.")

def test_full_integration():
    """Test full integration with IrisPluginManager."""
    print("\n===== Testing Full Integration =====")
    
    # Create a plugin manager
    mgr = IrisPluginManager()
    
    # Register our plugins
    mgr.register_plugin(ManualOPECPlugin().fetch_signals)
    mgr.register_plugin(AlphaVantagePlugin().fetch_signals)
    mgr.register_plugin(nasdaq_plugin)
    mgr.register_plugin(HighFrequencyIndicatorPlugin().fetch_signals) # Register the new plugin
    
    # Run all plugins
    signals = mgr.run_plugins()
    
    # Print all variables retrieved
    print(f"Retrieved {len(signals)} signals from all plugins.")
    if signals:
        # Ensure variable names are strings and not None before sorting
        var_names = sorted(list(set(str(s.get("name")) for s in signals if s.get("name") is not None)))
        print(f"Variables ingested: {', '.join(var_names)}")
    
    # Check if orb_price is in the registry and has a value
    orb_in_registry = "orb_price" in registry.variables
    print(f"orb_price in registry: {orb_in_registry}")
    
    # Check if gdp is recognized by alpha_vantage
    alpha_vantage_plugin = AlphaVantagePlugin()
    gdp_in_av = "gdp" in alpha_vantage_plugin.ECONOMIC_INDICATORS
    print(f"gdp in Alpha Vantage plugin: {gdp_in_av}")
    
    assert orb_in_registry, "orb_price not found in registry after running plugins."
    assert gdp_in_av, "gdp not found in Alpha Vantage plugin's economic indicators."

def test_high_frequency_indicators():
    """Test the high-frequency indicator plugin and calculated variables."""
    print("\n===== Testing High Frequency Indicators =====")

    # Note: This test requires some high-frequency data to be present in the store
    # Run the high_frequency_ingestion.py script separately first to populate data/high_frequency_data/

    try:
        # Instantiate data store and data access
        data_store = HighFrequencyDataStore()
        data_access = HighFrequencyDataAccess(data_store) # Pass the data_store instance

        # Instantiate indicator calculator
        indicator_calculator = HighFrequencyIndicators(data_access)

        # Get the list of symbols from AlphaVantagePlugin
        symbols = AlphaVantagePlugin.STOCK_SYMBOLS.keys()

        # Get the latest indicators
        indicators = indicator_calculator.get_latest_high_frequency_indicators(list(symbols))

        # Check if we got any indicators
        assert indicators, "No high-frequency indicators returned. Ensure high_frequency_ingestion.py has been run."

        # Define expected indicator variable name patterns
        expected_patterns = [
            "hf_ma_10_",
            "hf_intraday_volume_",
            "hf_intraday_volatility_"
        ]

        # Check if expected variables are present and have numeric values
        all_found = True
        for symbol in symbols:
            for pattern in expected_patterns:
                var_name = f"{pattern}{symbol.upper()}" # Assuming symbol is uppercase in variable name
                if var_name not in indicators:
                    print(f"ERROR: Expected variable '{var_name}' not found in indicators.")
                    all_found = False
                elif not isinstance(indicators[var_name], (int, float)):
                     print(f"ERROR: Variable '{var_name}' has non-numeric value: {indicators[var_name]}")
                     all_found = False
                else:
                    print(f"SUCCESS: Found '{var_name}' with value {indicators[var_name]}")


        assert all_found, "Some expected high-frequency indicator variables were missing or non-numeric."

        print("SUCCESS: High-frequency indicator variables are present and appear valid.")

    except FileNotFoundError:
        assert False, "High-frequency data files not found. Ensure high_frequency_ingestion.py has been run."
    except Exception as e:
        assert False, f"An unexpected error occurred during high-frequency indicator test: {e}"


def main():
    print(f"===== Ingestion Test Started: {datetime.now().isoformat()} =====")
    
    # Run individual tests
    opec_result = test_manual_opec_plugin()
    alpha_vantage_result = test_alpha_vantage_plugin()
    nasdaq_result = test_nasdaq_plugin()
    hf_indicators_result = test_high_frequency_indicators() # Run the new test
    integration_result = test_full_integration()
    
    # Summarize results
    print("\n===== Test Summary =====")
    print(f"Manual OPEC Plugin: {'✅ PASS' if opec_result else '❌ FAIL'}")
    print(f"Alpha Vantage Plugin: {'✅ PASS' if alpha_vantage_result else '❌ FAIL'}")
    print(f"Nasdaq Plugin Changes: {'✅ PASS' if nasdaq_result else '❌ FAIL'}")
    print(f"High Frequency Indicators: {'✅ PASS' if hf_indicators_result else '❌ FAIL'}") # Add new test result
    print(f"Full Integration: {'✅ PASS' if integration_result else '❌ FAIL'}")

    # Overall result
    if opec_result and alpha_vantage_result and nasdaq_result and hf_indicators_result and integration_result:
        print("\n✅ ALL TESTS PASSED - Changes are working correctly!")
    else:
        print("\n❌ SOME TESTS FAILED - Review the output above for details.")
    
    print(f"===== Ingestion Test Completed: {datetime.now().isoformat()} =====")

if __name__ == "__main__":
    main()