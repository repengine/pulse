#!/usr/bin/env python3
"""
RetrodictionLoader Usage Example

This script demonstrates how to use the RetrodictionLoader class
for loading historical snapshots in retrodiction simulations.

Usage:
    python examples/historical_retrodiction/loader_example.py
"""

from engine.historical_retrodiction_runner import (
    RetrodictionLoader,
    get_default_variable_state
)
import sys
import json
import tempfile
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def create_sample_data_file(file_path: str) -> None:
    """Create a sample historical variables JSON file for demonstration."""
    sample_data = {
        "variables": {
            "spx_close": 4200.0,
            "us_10y_yield": 4.5,
            "energy_cost": 1.2,
            "wb_gdp_growth_annual": 2.1
        },
        "snapshots": {
            "0": {
                "turn": 0,
                "timestamp": "2020-01-01T00:00:00Z",
                "variables": {
                    "spx_close": 3200.0,
                    "us_10y_yield": 1.8,
                    "energy_cost": 1.0
                }
            },
            "1": {
                "turn": 1,
                "timestamp": "2020-01-02T00:00:00Z",
                "variables": {
                    "spx_close": 3250.0,
                    "us_10y_yield": 1.9,
                    "energy_cost": 1.1
                }
            },
            "5": {
                "turn": 5,
                "timestamp": "2020-01-06T00:00:00Z",
                "variables": {
                    "spx_close": 3400.0,
                    "us_10y_yield": 2.2,
                    "energy_cost": 1.3
                }
            }
        }
    }

    with open(file_path, 'w') as f:
        json.dump(sample_data, f, indent=2)


def main():
    """Demonstrate RetrodictionLoader usage."""
    print("=== RetrodictionLoader Usage Example ===\n")

    # 1. Test get_default_variable_state function
    print("1. Testing get_default_variable_state()...")
    default_state = get_default_variable_state()
    print(f"   Default variable state: {default_state}")
    print(f"   Type: {type(default_state)}")

    # 2. Create a temporary data file for demonstration
    print("\n2. Creating sample historical data file...")
    with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False) as tmp_file:
        sample_file_path = tmp_file.name

    create_sample_data_file(sample_file_path)
    print(f"   Created sample data file: {sample_file_path}")

    try:
        # 3. Initialize RetrodictionLoader with custom path
        print("\n3. Initializing RetrodictionLoader with custom path...")
        loader = RetrodictionLoader(path=sample_file_path)
        print(f"   Loader path: {loader.path}")
        print(f"   Available snapshots: {list(loader.snapshots.keys())}")

        # 4. Retrieve snapshots by turn
        print("\n4. Retrieving snapshots by turn...")

        # Test existing turns
        for turn in [0, 1, 5]:
            snapshot = loader.get_snapshot_by_turn(turn)
            if snapshot:
                print(f"   Turn {turn}: Found snapshot with "
                      f"{len(snapshot.get('variables', {}))} variables")
                print(f"     Timestamp: {snapshot.get('timestamp', 'N/A')}")
                print(f"     Variables: {list(snapshot.get('variables', {}).keys())}")
            else:
                print(f"   Turn {turn}: No snapshot found")

        # Test non-existing turn
        missing_turn = 10
        snapshot = loader.get_snapshot_by_turn(missing_turn)
        print(f"   Turn {missing_turn}: {'Found' if snapshot else 'No'} snapshot")

        # 5. Initialize with default path (no file)
        print("\n5. Initializing RetrodictionLoader with default path...")
        default_loader = RetrodictionLoader()
        print(f"   Default path: {default_loader.path}")
        print(f"   Available snapshots: {list(default_loader.snapshots.keys())}")

        # Test snapshot retrieval with no data
        snapshot = default_loader.get_snapshot_by_turn(0)
        print(f"   Turn 0 with no data file: {'Found' if snapshot else 'No'} snapshot")

        # 6. Demonstrate error handling
        print("\n6. Demonstrating error handling...")

        # Try with non-existent file
        nonexistent_loader = RetrodictionLoader(path="/nonexistent/path.json")
        print(f"   Loader with nonexistent path: "
              f"{len(nonexistent_loader.snapshots)} snapshots loaded")

    finally:
        # Clean up temporary file
        Path(sample_file_path).unlink(missing_ok=True)
        print(f"\n   Cleaned up temporary file: {sample_file_path}")

    print("\n=== Example completed successfully! ===")


if __name__ == "__main__":
    main()
