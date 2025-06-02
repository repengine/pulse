"""NewsAPI Plugin Test With Direct Credentials

This script directly sets the NewsAPI key in the environment
before testing the plugin.
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add the parent directory to the path to allow importing the iris package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# IMPORTANT: Set your actual NewsAPI key here
# ===============================================
os.environ["NEWSAPI_KEY"] = "YOUR_NEWSAPI_KEY"  # Replace with your actual NewsAPI key
# ===============================================

# Import the plugin after setting credentials

# def test_newsapi():
#     """Test the NewsAPI plugin."""
#     print("\n===== TESTING NEWSAPI PLUGIN =====")

#     # Check if credentials are set
#     api_key = os.environ.get("NEWSAPI_KEY", "")

#     if api_key == "YOUR_NEWSAPI_KEY":
#         print("❌ ERROR: You need to edit this file and replace the placeholder with your actual NewsAPI key")
#         print("    Open the file and edit the value for NEWSAPI_KEY")
#         assert False, "ERROR: You need to edit this file and replace the placeholder with your actual NewsAPI key"

#     # Initialize the plugin
#     plugin = NewsapiPlugin()

#     # Check if the plugin is enabled (API key is set)
#     if not plugin.enabled:
#         print("❌ NewsAPI plugin is DISABLED. There's an issue with the API key.")
#         assert False, "ERROR: You need to edit this file and replace the placeholder with your actual NewsAPI key"

#     print("✓ NewsAPI plugin is ENABLED.")

#     # Try to fetch signals
#     try:
#         print("Fetching data from NewsAPI...")
#         signals = plugin.fetch_signals()

#         if signals:
#             print(f"✓ Successfully fetched {len(signals)} signals!")
#             print("\nExample signals:")
#             for i, signal in enumerate(signals[:3]):  # Show first 3 signals
#                 print(f"\nSignal {i+1}:")
#                 pprint(signal)
#             assert True, "Successfully fetched signals!"
#         else:
#             print("❌ No signals returned. This might be due to API limitations or no matching content.")
#             assert False, "ERROR: You need to edit this file and replace the placeholder with your actual NewsAPI key"

#     except Exception as e:
#         print(f"❌ Error testing NewsAPI plugin: {e}")
#         assert False, "ERROR: You need to edit this file and replace the placeholder with your actual NewsAPI key"

# if __name__ == "__main__":
#     test_newsapi()
