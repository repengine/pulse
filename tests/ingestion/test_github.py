"""GitHub Plugin Test Script

This script tests the GitHub plugin to verify it can connect to the API
and fetch repository data using your configured API token.
"""

import sys
import os
import logging
from pprint import pprint
from ingestion.iris_plugins_variable_ingestion.github_plugin import GithubPlugin

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add the parent directory to the path to allow importing the iris package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_github():
    """Test the GitHub plugin."""
    print("\n===== TESTING GITHUB PLUGIN =====")

    # Initialize the plugin
    plugin = GithubPlugin()

    # Check if the plugin is enabled (API token is set)
    if not plugin.enabled:
        print(
            "❌ GitHub plugin is DISABLED. Make sure GITHUB_TOKEN environment variable is set."
        )
        assert False, (
            "GitHub plugin is DISABLED. Make sure GITHUB_TOKEN environment variable is set."
        )

    print("✓ GitHub plugin is ENABLED.")

    # Try to fetch signals
    try:
        print("Fetching data from GitHub API...")
        signals = plugin.fetch_signals()

        if signals:
            print(f"✓ Successfully fetched {len(signals)} signals!")
            print("\nExample signals:")
            for i, signal in enumerate(signals[:3]):  # Show first 3 signals
                print(f"\nSignal {i + 1}:")
                pprint(signal)
            assert True, "Successfully fetched signals!"
        else:
            print(
                "❌ No signals returned. This might be due to API limitations or no matching content."
            )
            assert False, (
                "GitHub plugin is DISABLED. Make sure GITHUB_TOKEN environment variable is set."
            )

    except Exception as e:
        print(f"❌ Error testing GitHub plugin: {e}")
        assert False, (
            "GitHub plugin is DISABLED. Make sure GITHUB_TOKEN environment variable is set."
        )


if __name__ == "__main__":
    test_github()
