"""Reddit Plugin Test Script

This script tests the Reddit plugin to verify it can connect to the API
and fetch social sentiment data using your configured API credentials.
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
from iris.iris_plugins_variable_ingestion.reddit_plugin import RedditPlugin

def test_reddit():
    """Test the Reddit plugin."""
    print("\n===== TESTING REDDIT PLUGIN =====")
    
    # Initialize the plugin
    plugin = RedditPlugin()
    
    # Check if the plugin is enabled (API credentials are set)
    assert plugin.enabled, "Reddit plugin is DISABLED. Make sure REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT environment variables are set."
    print("✓ Reddit plugin is ENABLED.")
    
    # Try to fetch signals
    try:
        print("Fetching data from Reddit API...")
        signals = plugin.fetch_signals()
        
        assert signals, "No signals returned. This might be due to API limitations or no matching content."
        assert isinstance(signals, list), f"Expected a list of signals, but got {type(signals)}"
        assert len(signals) > 0, "Fetched signals list is empty."

        print(f"✓ Successfully fetched {len(signals)} signals!")
        print("\nExample signals:")
        for i, signal in enumerate(signals[:3]):  # Show first 3 signals
            print(f"\nSignal {i+1}:")
            pprint(signal)
            # Add specific assertions for signal structure if needed
            assert isinstance(signal, dict), f"Signal {i+1} is not a dictionary."
            # Example: assert 'id' in signal, f"Signal {i+1} missing 'id' key."
            
    except Exception as e:
        assert False, f"Error testing Reddit plugin: {e}"

if __name__ == "__main__":
    test_reddit()