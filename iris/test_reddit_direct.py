"""Reddit Plugin Test With Direct Credentials

This script directly sets the Reddit API credentials in the environment
before testing the plugin.
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

# IMPORTANT: Set your actual Reddit API credentials here
# ===============================================
os.environ["REDDIT_CLIENT_ID"] = "YOUR_CLIENT_ID"  # Replace with your actual client ID
os.environ["REDDIT_CLIENT_SECRET"] = "YOUR_CLIENT_SECRET"  # Replace with your actual client secret
os.environ["REDDIT_USER_AGENT"] = "Pulse/1.0"  # This can be a simple string identifying your app
# ===============================================

# Import the plugin after setting credentials
from iris.iris_plugins_variable_ingestion.reddit_plugin import RedditPlugin

def test_reddit():
    """Test the Reddit plugin."""
    print("\n===== TESTING REDDIT PLUGIN =====")
    
    # Check if credentials are set
    client_id = os.environ.get("REDDIT_CLIENT_ID", "")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "")
    
    if client_id == "YOUR_CLIENT_ID" or client_secret == "YOUR_CLIENT_SECRET":
        print("❌ ERROR: You need to edit this file and replace the placeholders with your actual Reddit credentials")
        print("    Open the file and edit the values for REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
        return False
    
    # Initialize the plugin
    plugin = RedditPlugin()
    
    # Check if the plugin is enabled (API credentials are set)
    if not plugin.enabled:
        print("❌ Reddit plugin is DISABLED. There's an issue with the credentials.")
        return False
    
    print("✓ Reddit plugin is ENABLED.")
    
    # Try to fetch signals
    try:
        print("Fetching data from Reddit API...")
        signals = plugin.fetch_signals()
        
        if signals:
            print(f"✓ Successfully fetched {len(signals)} signals!")
            print("\nExample signals:")
            for i, signal in enumerate(signals[:3]):  # Show first 3 signals
                print(f"\nSignal {i+1}:")
                pprint(signal)
            return True
        else:
            print("❌ No signals returned. This might be due to API limitations or no matching content.")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Reddit plugin: {e}")
        return False

if __name__ == "__main__":
    test_reddit()