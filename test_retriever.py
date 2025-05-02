#!/usr/bin/env python
"""
Test script for historical data retriever
"""
import sys
import argparse
import datetime as dt
import json
import logging
import os
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import directly from the file
sys.path.insert(0, os.path.abspath("."))
from iris.iris_utils.historical_data_retriever import (
    load_variable_catalog,
    retrieve_historical_data,
    retrieve_priority_variables,
    create_verification_report,
    save_verification_report
)

def main():
    """Simple test harness for the historical data retriever"""
    parser = argparse.ArgumentParser(description="Test historical data retrieval")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--variable", 
        type=str,
        help="Name of a specific variable to retrieve data for"
    )
    group.add_argument(
        "--priority", 
        type=int, 
        help="Retrieve data for all variables with this priority level"
    )
    
    parser.add_argument(
        "--years", 
        type=int, 
        default=1,  # Use 1 year for testing
        help="Number of years to look back"
    )
    
    args = parser.parse_args()
    
    try:
        results = {}
        
        if args.variable:
            # Retrieve data for a specific variable
            catalog = load_variable_catalog()
            var_info = next(
                (var for var in catalog["variables"] if var["variable_name"] == args.variable),
                None
            )
            
            if var_info is None:
                logger.error(f"Variable {args.variable} not found in the catalog")
                return 1
            
            logger.info(f"Testing retrieval of {args.variable} for {args.years} year(s)...")
            result = retrieve_historical_data(
                var_info,
                years=args.years,
                rate_limit_delay=0.5
            )
            
            results[args.variable] = result
            
        elif args.priority:
            # Retrieve data for all variables with the specified priority
            logger.info(f"Testing retrieval of priority {args.priority} variables for {args.years} year(s)...")
            results = retrieve_priority_variables(
                priority=args.priority,
                years=args.years,
                rate_limit_delay=0.5
            )
        
        # Create verification report
        report = create_verification_report(results)
        report_path = save_verification_report(report)
        
        logger.info(f"Test complete. Processed {len(results)} variables:")
        logger.info(f"  - Successful retrievals: {report['successful_retrievals']}")
        logger.info(f"  - Failed retrievals: {report['failed_retrievals']}")
        
        if "overall_metrics" in report:
            logger.info(f"Average completeness: {report['overall_metrics']['average_completeness']:.2f}%")
        
        logger.info(f"Verification report saved to {report_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())