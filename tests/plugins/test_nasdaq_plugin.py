#!/usr/bin/env python
"""
Test Script for NASDAQ Data Link Plugin

This script tests the updated NASDAQ Data Link plugin with various datasets
to verify it correctly handles current API endpoints and formats.

Usage:
    python test_nasdaq_plugin.py
"""

import os
import json
from datetime import datetime
import logging
from ingestion.iris_plugins_variable_ingestion.nasdaq_plugin import nasdaq_plugin

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import the plugin


def main():
    # Test different dataset configurations
    test_configs = [
        # Test default dataset (should be LBMA/GOLD now)
        {"title": "Default Dataset", "env_var": None},
        # Test free tier datasets
        {"title": "LBMA Dataset", "env_var": "LBMA/GOLD"},
        {"title": "FRED Dataset", "env_var": "FRED/GDP"},
        {"title": "ODA Dataset", "env_var": "ODA/PALUM_USD"},
        {"title": "OPEC Dataset", "env_var": "OPEC/ORB"},
        # Test World Bank dataset
        {"title": "World Bank Dataset", "env_var": "WORLDBANK/WLD_SP_POP_TOTL"},
        # Test a premium dataset (might fail with 403 Forbidden)
        {"title": "Premium Dataset", "env_var": "EOD/AAPL"},
        # Test multiple datasets
        {
            "title": "Multiple Free Datasets",
            "env_var": "LBMA/GOLD,FRED/GDP,ODA/PALUM_USD",
        },
        # Test the fallback mechanism with an invalid dataset
        {"title": "Fallback Test", "env_var": "INVALID/DATASET"},
    ]

    # Save original environment variable value
    original_env = os.environ.get("NASDAQ_DL_DATASETS")

    # Run tests for each configuration
    for config in test_configs:
        print("\n" + "=" * 70)
        print(f"TEST: {config['title']}")
        print("=" * 70)

        # Set environment variable if specified
        if config["env_var"] is not None:
            os.environ["NASDAQ_DL_DATASETS"] = config["env_var"]
            print(f"Set NASDAQ_DL_DATASETS to: {config['env_var']}")
        elif "NASDAQ_DL_DATASETS" in os.environ:
            del os.environ["NASDAQ_DL_DATASETS"]
            print("Using default dataset configuration")

        # Run the plugin
        signals = nasdaq_plugin()

        # Print results
        if not signals:
            print("No signals returned. Ensure NASDAQ_API_KEY is set correctly.")
        else:
            print(f"Received {len(signals)} signals:")
            for i, signal in enumerate(signals):
                print(f"\nSignal {i + 1}:")
                # Format signal for readable output
                formatted_signal = {
                    "source": signal["source"],
                    "symbol": signal["symbol"],
                    "timestamp": signal["timestamp"],
                    "value": signal["value"],
                }
                print(json.dumps(formatted_signal, indent=2))
                print("Meta data keys:", list(signal["meta"].keys()))

    # Restore original environment variable
    if original_env is not None:
        os.environ["NASDAQ_DL_DATASETS"] = original_env
    elif "NASDAQ_DL_DATASETS" in os.environ:
        del os.environ["NASDAQ_DL_DATASETS"]

    print("\nTEST COMPLETED:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
