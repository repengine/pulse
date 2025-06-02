#!/usr/bin/env python
"""
Historical Timeline Data Pipeline Example
========================================

This script demonstrates the complete workflow of the historical timeline project,
Phase 3: Data Storage and Standardization.

It shows how to:
1. Retrieve raw historical data using historical_data_retriever
2. Transform the data into a standardized format using historical_data_transformer
3. Store the data in the RecursiveDataStore
4. Verify the data consistency
5. Generate reports on data coverage

This is meant as an educational example to show how the components work together.
"""

import logging
import subprocess
import sys
import time
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_command(command):
    """Run a command and log its output."""
    logger.info(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        for line in result.stdout.splitlines():
            logger.info(line)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with code {e.returncode}")
        for line in e.stdout.splitlines():
            logger.info(line)
        for line in e.stderr.splitlines():
            logger.error(line)
        return False


def main():
    """Run the complete historical timeline data pipeline."""
    # Make sure the output directories exist
    Path("data/historical_timeline/reports").mkdir(parents=True, exist_ok=True)

    logger.info("=== Historical Timeline Data Pipeline Example ===")

    # Step 1: Retrieve raw historical data for priority 1 variables
    logger.info("\n=== Step 1: Retrieving Raw Historical Data ===")
    if not run_command(
        [
            "python",
            "-m",
            "ingestion.iris_utils.cli_historical_data",
            "retrieve",
            "--priority",
            "1",
        ]
    ):
        return 1

    # Short pause to let file system operations complete
    time.sleep(1)

    # Step 2: Transform and store all priority 1 variables
    logger.info("\n=== Step 2: Transforming and Storing Data ===")
    if not run_command(
        [
            "python",
            "-m",
            "ingestion.iris_utils.cli_historical_data",
            "transform",
            "--priority",
            "1",
        ]
    ):
        return 1

    time.sleep(1)

    # Step 3: Verify data consistency for all variables
    logger.info("\n=== Step 3: Verifying Data Consistency ===")
    if not run_command(
        ["python", "-m", "ingestion.iris_utils.cli_historical_data", "verify", "--all"]
    ):
        logger.warning("Verification completed with warnings")

    time.sleep(1)

    # Step 4: Generate coverage report
    logger.info("\n=== Step 4: Generating Data Coverage Report ===")
    if not run_command(
        [
            "python",
            "-m",
            "ingestion.iris_utils.cli_historical_data",
            "report",
            "--coverage",
        ]
    ):
        return 1

    # Step 5: Generate summary report
    logger.info("\n=== Step 5: Generating Summary Report ===")
    if not run_command(
        [
            "python",
            "-m",
            "ingestion.iris_utils.cli_historical_data",
            "report",
            "--summary",
        ]
    ):
        return 1

    logger.info("\n=== Pipeline Completed Successfully ===")
    logger.info("Check the reports in data/historical_timeline/reports")

    # Advanced usage: Demonstrate individual variable processing
    logger.info("\n=== Bonus: Individual Variable Processing ===")

    # Retrieve SPX data
    logger.info("Processing SPX Close data...")
    run_command(
        [
            "python",
            "-m",
            "ingestion.iris_utils.cli_historical_data",
            "retrieve",
            "--variable",
            "spx_close",
        ]
    )

    # Transform SPX data
    run_command(
        [
            "python",
            "-m",
            "ingestion.iris_utils.cli_historical_data",
            "transform",
            "--variable",
            "spx_close",
        ]
    )

    # Verify SPX data
    run_command(
        [
            "python",
            "-m",
            "ingestion.iris_utils.cli_historical_data",
            "verify",
            "--variable",
            "spx_close",
        ]
    )

    logger.info("\n=== Example Completed ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
