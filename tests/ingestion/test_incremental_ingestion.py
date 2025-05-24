"""
Test script to verify incremental ingestion and file writing capabilities.
This script tests:
1. Alpha Vantage plugin writing data incrementally
2. NASDAQ plugin writing data incrementally

Usage:
    python test_incremental_ingestion.py
"""

import os
import sys
import json
from datetime import datetime

# Ensure the Pulse directory is in the Python path
sys.path.append(os.getcwd())

# Import the necessary modules
# from data.high_frequency_data_store import HighFrequencyDataStore


def find_latest_jsonl_files(directory, limit=5):
    """Find and return info about the latest JSONL files in a directory."""
    result = []

    # Walk through directory recursively
    for root, dirs, files in os.walk(directory):
        # Filter for JSONL files
        jsonl_files = [f for f in files if f.endswith(".jsonl")]

        for file in jsonl_files:
            full_path = os.path.join(root, file)

            # Get file stats
            stats = os.stat(full_path)

            result.append(
                {
                    "path": full_path,
                    "size": stats.st_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    "lines": sum(1 for _ in open(full_path, "r")),
                }
            )

    # Sort by modification time (newest first) and limit
    result.sort(key=lambda x: x["modified"], reverse=True)
    return result[:limit]


def inspect_files(path, limit=3):
    """Inspect content of JSONL files by reading the first few lines."""
    result = {}

    if os.path.exists(path):
        with open(path, "r") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= limit:
                    break
                try:
                    data = json.loads(line.strip())
                    lines.append(data)
                except json.JSONDecodeError:
                    lines.append({"error": "Invalid JSON", "raw": line.strip()})

            result = {
                "file": path,
                "sample_lines": lines,
                "more_lines": True
                if limit < sum(1 for _ in open(path, "r"))
                else False,
            }

    return result


# def test_alpha_vantage_incremental():
#     """Test Alpha Vantage plugin's incremental writing capability."""
#     print("\n===== Testing Alpha Vantage Incremental Writing =====")

#     # Check if ALPHA_VANTAGE_KEY is set
#     assert os.environ.get("ALPHA_VANTAGE_KEY"), "ALPHA_VANTAGE_KEY environment variable not set. Set this variable to test the Alpha Vantage plugin."

#     plugin = AlphaVantagePlugin()

#     # Check if plugin is enabled
#     assert plugin.enabled, "Alpha Vantage plugin is not enabled. Check API key."

#     print("Fetching data from Alpha Vantage...")
#     start_time = time.time()

#     # Directory to check for incrementally written files
#     av_dir = "data/api_ingestion/alpha_vantage"

#     # Record files before API call
#     print("Checking existing files before API call...")
#     before_files = find_latest_jsonl_files(av_dir)
#     # print(f"Found {len(before_files)} JSONL files before API call")

#     # Call the plugin to fetch data
#     signals = plugin.fetch_signals()

#     # Record how long the API call took
#     elapsed = time.time() - start_time
#     print(f"API call completed in {elapsed:.2f} seconds, retrieved {len(signals)} signals")

#     # Check for new files immediately after the API call
#     print("Checking for new files immediately after API call...")
#     after_files = find_latest_jsonl_files(av_dir)

#     # Find new files
#     new_files = []
#     old_file_paths = [f["path"] for f in before_files]
#     for file in after_files:
#         if file["path"] not in old_file_paths:
#             new_files.append(file)

#     print(f"Found {len(new_files)} new JSONL files after API call")

#     # Inspect content of a few new files
#     if new_files:
#         print("\nInspecting content of new files:")
#         for file in new_files[:2]:  # Look at first 2 new files
#             file_info = inspect_files(file["path"])
#             if file_info.get("sample_lines"):
#                 print(f"\nFile: {file['path']}")
#                 print(f"Sample data points:")
#                 for i, line in enumerate(file_info["sample_lines"]):
#                     print(f"  {i+1}: Timestamp={line.get('timestamp')}, Value={line.get('value')}")

#     assert len(new_files) > 0, "No new files were created by Alpha Vantage plugin."


# def test_nasdaq_incremental():
#     """Test NASDAQ plugin's incremental writing capability."""
#     print("\n===== Testing NASDAQ Incremental Writing =====")

#     # Check if NASDAQ_API_KEY is set
#     assert os.environ.get("NASDAQ_API_KEY"), "NASDAQ_API_KEY environment variable not set. Set this variable to test the NASDAQ plugin."

#     # Directory to check for incrementally written files
#     nasdaq_dir = "data/api_ingestion/nasdaq"

#     # Record files before API call
#     print("Checking existing files before API call...")
#     before_files = find_latest_jsonl_files(nasdaq_dir)
#     # print(f"Found {len(before_files)} JSONL files before API call")

#     # Call the plugin to fetch data
#     print("Fetching data from NASDAQ...")
#     start_time = time.time()
#     signals = nasdaq_plugin()

#     # Record how long the API call took
#     elapsed = time.time() - start_time
#     print(f"API call completed in {elapsed:.2f} seconds, retrieved {len(signals)} signals")

#     # Check for new files immediately after the API call
#     print("Checking for new files immediately after API call...")
#     after_files = find_latest_jsonl_files(nasdaq_dir)

#     # Find new files
#     new_files = []
#     old_file_paths = [f["path"] for f in before_files]
#     for file in after_files:
#         if file["path"] not in old_file_paths:
#             new_files.append(file)

#     print(f"Found {len(new_files)} new JSONL files after API call")

#     # Inspect content of a few new files
#     if new_files:
#         print("\nInspecting content of new files:")
#         for file in new_files[:2]:  # Look at first 2 new files
#             file_info = inspect_files(file["path"])
#             if file_info.get("sample_lines"):
#                 print(f"\nFile: {file['path']}")
#                 print(f"Sample data points:")
#                 for i, line in enumerate(file_info["sample_lines"]):
#                     print(f"  {i+1}: Timestamp={line.get('timestamp')}, Value={line.get('value')}")

#     assert len(new_files) > 0, "No new files were created by NASDAQ plugin."


# def main():
#     """Main test function"""
#     print(f"===== Incremental Ingestion Test Started: {datetime.now().isoformat()} =====")

#     # Run tests
#     # hf_result = test_high_frequency_store() # Commented out due to missing module
#     # av_result = test_alpha_vantage_incremental()
#     # nasdaq_result = test_nasdaq_incremental()

#     # Summarize results
#     print("\n===== Test Summary =====")
#     # print(f"HighFrequencyDataStore: {'✅ PASS' if hf_result else '❌ FAIL'}") # Commented out
#     # print(f"Alpha Vantage Plugin: {'✅ PASS' if av_result else '❌ FAIL'}")
#     # print(f"NASDAQ Plugin: {'✅ PASS' if nasdaq_result else '❌ FAIL'}")

#     # Overall result
#     if (False): # Removed hf_result from condition
#         print("\n✅ INCREMENTAL INGESTION IS WORKING - Data is being written as it's ingested!")
#     else:
#         print("\n❌ SOME TESTS FAILED - Review the output above for details.")

#     print(f"===== Incremental Ingestion Test Completed: {datetime.now().isoformat()} =====")


# if __name__ == "__main__":
#     main()
