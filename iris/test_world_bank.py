"""World Bank Plugin Test Script

This script tests the World Bank plugin to verify it can connect to the API
and fetch global economic data (no API key required).
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
from iris.iris_plugins_variable_ingestion.worldbank_plugin import WorldBankPlugin

def test_world_bank():
    """Test the World Bank plugin."""
    print("\n===== TESTING WORLD BANK PLUGIN =====")
    
    # Initialize the plugin
    plugin = WorldBankPlugin()
    
    # Check if the plugin is enabled
    if not plugin.enabled:
        print("❌ World Bank plugin is DISABLED.")
        return False
    
    print("✓ World Bank plugin is ENABLED.")
    
    # Try to fetch signals
    try:
        print("Fetching global economic data from World Bank API...")
        signals = plugin.fetch_signals()
        
        if signals:
            print(f"✓ Successfully fetched {len(signals)} signals!")
            print("\nExample signals:")
            for i, signal in enumerate(signals[:3]):  # Show first 3 signals
                print(f"\nSignal {i+1}:")
                pprint(signal)
            return True
        else:
            print("❌ No signals returned. This could be due to API rate limiting or no recent data updates.")
            return False
            
    except Exception as e:
        print(f"❌ Error testing World Bank plugin: {e}")
        return False

if __name__ == "__main__":
    test_world_bank()