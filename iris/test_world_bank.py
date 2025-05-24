"""World Bank Plugin Test Script

This script tests the World Bank plugin to verify it can connect to the API
and fetch global economic data (no API key required).
"""

import sys
import os
import logging
from pprint import pprint
from iris.iris_plugins_variable_ingestion.worldbank_plugin import WorldBankPlugin

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add the parent directory to the path to allow importing the iris package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_world_bank():
    """Test the World Bank plugin."""
    print("\n===== TESTING WORLD BANK PLUGIN =====")

    # Initialize the plugin
    plugin = WorldBankPlugin()

    # Check if the plugin is enabled
    assert plugin.enabled, "World Bank plugin is DISABLED."
    print("✓ World Bank plugin is ENABLED.")

    # Try to fetch signals
    try:
        print("Fetching global economic data from World Bank API...")
        signals = plugin.fetch_signals()

        assert signals, (
            "No signals returned. This could be due to API rate limiting or no recent data updates."
        )
        assert isinstance(signals, list), (
            f"Expected a list of signals, but got {type(signals)}"
        )
        assert len(signals) > 0, "Fetched signals list is empty."

        print(f"✓ Successfully fetched {len(signals)} signals!")
        print("\nExample signals:")
        for i, signal in enumerate(signals[:3]):  # Show first 3 signals
            print(f"\nSignal {i + 1}:")
            pprint(signal)
            # Add specific assertions for signal structure if needed
            assert isinstance(signal, dict), f"Signal {i + 1} is not a dictionary."
            # Example: assert 'country' in signal and 'indicator' in signal and 'value' in signal, \
            #    f"Signal {i+1} missing required keys."

    except Exception as e:
        assert False, f"Error testing World Bank plugin: {e}"


if __name__ == "__main__":
    test_world_bank()
