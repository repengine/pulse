#!/usr/bin/env python
"""
Historical Data Retriever CLI
=============================

This script provides a command-line interface for retrieving historical data
for variables in the historical timeline catalog.

Usage:
------
# Retrieve data for a specific variable
python retrieve_historical_data.py --variable spx_close

# Retrieve data for all priority 1 variables
python retrieve_historical_data.py --priority 1

# Retrieve data for all variables
python retrieve_historical_data.py --all

# Specify number of years to retrieve
python retrieve_historical_data.py --priority 1 --years 3

# Specify end date
python retrieve_historical_data.py --priority 1 --end-date 2025-04-30
"""

from ingestion.iris_utils.historical_data_retriever import main
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Now we can import the module

if __name__ == "__main__":
    sys.exit(main())
