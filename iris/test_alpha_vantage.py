"""Alpha Vantage Plugin Test Script

This script tests the Alpha Vantage plugin to verify it can connect to the API
and fetch financial data using your configured API key.
"""
import sys
import os
import logging
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add the parent directory to the path to allow importing the iris package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the plugin
from iris.iris_plugins_variable_ingestion.alpha_vantage_plugin import AlphaVantagePlugin

def test_alpha_vantage():
    """Test the Alpha Vantage plugin."""
    print("\n===== TESTING ALPHA VANTAGE PLUGIN =====")
    
    # Initialize the plugin
    plugin = AlphaVantagePlugin()
    
    # Check if the plugin is enabled (API key is set)
    if not plugin.enabled:
        print("❌ Alpha Vantage plugin is DISABLED. Make sure ALPHA_VANTAGE_KEY environment variable is set.")
        return False
    
    print("✓ Alpha Vantage plugin is ENABLED.")
    
    # Try to fetch signals
    try:
        print("Fetching data from Alpha Vantage API...")
        signals = plugin.fetch_signals()
        
        if signals:
            print(f"✓ Successfully fetched {len(signals)} signals!")
            print("\nExample signals:")
            for i, signal in enumerate(signals[:3]):  # Show first 3 signals
                print(f"\nSignal {i+1}:")
                pprint(signal)
            return True
        else:
            print("❌ No signals returned. This might be normal if there's no new data.")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Alpha Vantage plugin: {e}")
        return False

if __name__ == "__main__":
    test_alpha_vantage()