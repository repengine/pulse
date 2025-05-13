"""Open-Meteo Plugin Test Script

This script tests the Open-Meteo plugin to verify it can connect to the API
and fetch weather data (no API key required).
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
from iris.iris_plugins_variable_ingestion.open_meteo_plugin import OpenMeteoPlugin

def test_open_meteo():
    """Test the Open-Meteo plugin."""
    print("\n===== TESTING OPEN-METEO PLUGIN =====")
    
    # Initialize the plugin
    plugin = OpenMeteoPlugin()
    
    # Check if the plugin is enabled
    if not plugin.enabled:
        print("❌ Open-Meteo plugin is DISABLED.")
        assert False, "Open-Meteo plugin is DISABLED."
    
    print("✓ Open-Meteo plugin is ENABLED.")
    
    # Try to fetch signals
    try:
        print("Fetching weather data from Open-Meteo API...")
        signals = plugin.fetch_signals()
        
        if signals:
            print(f"✓ Successfully fetched {len(signals)} signals!")
            print("\nExample signals:")
            for i, signal in enumerate(signals[:5]):  # Show first 5 signals
                print(f"\nSignal {i+1}:")
                pprint(signal)
            assert True, "Successfully fetched signals!"
        else:
            print("❌ No signals returned. This is unexpected for Open-Meteo.")
            assert False, "Open-Meteo plugin is DISABLED."
            
    except Exception as e:
        print(f"❌ Error testing Open-Meteo plugin: {e}")
        assert False, "Open-Meteo plugin is DISABLED."

if __name__ == "__main__":
    test_open_meteo()