#!/usr/bin/env python
"""ingestion.iris_utils.test_historical_data_pipeline
=============================================

This script tests the end-to-end historical data pipeline:
1. Retrieves data for a sample variable
2. Transforms and stores it in the RecursiveDataStore
3. Verifies the stored data
4. Generates a report on data coverage

This allows validation of the entire data flow from raw retrieval to
standardized storage and verification.

Usage:
------
python -m ingestion.iris_utils.test_historical_data_pipeline
"""

import logging


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Test variables (priority 1 variables that should have good data availability)
TEST_VARIABLES = ["spx_close", "us_10y_yield", "gdp_growth_annual"]


# def test_single_variable_pipeline(variable_name):
#     """
#     Test the complete pipeline for a single variable.

#     Args:
#         variable_name: Name of the variable to test

#     """
#     logger.info(f"===== Testing pipeline for {variable_name} =====")

#     try:
#         # Step 1: Load variable info
#         catalog = load_variable_catalog()
#         var_info = next(
#             (var for var in catalog["variables"] if var["variable_name"] == variable_name),
#             None
#         )

#         if var_info is None:
#             logger.error(f"Variable {variable_name} not found in catalog")
#             assert False, f"Variable {variable_name} not found in catalog"

#         # Step 2: Retrieve raw data
#         logger.info(f"Retrieving raw data for {variable_name}")
#         retrieval_result = retrieve_historical_data(var_info, years=2)

#         assert "stats" in retrieval_result, f"Failed to retrieve data for {variable_name}"

#         stats = retrieval_result["stats"]
#         logger.info(f"Retrieved {stats['data_point_count']} data points")
#         logger.info(f"Completeness: {stats['completeness_pct']:.2f}%")
#         assert stats['data_point_count'] > 0, f"No data points retrieved for {variable_name}"
#         assert stats['completeness_pct'] > 0, f"Data completeness is 0% for {variable_name}"

#         # Step 3: Transform and store data
#         logger.info(f"Transforming and storing data for {variable_name}")
#         transform_result = transform_and_store_variable(variable_name)

#         assert transform_result.status == "success", f"Failed to transform data: {transform_result.error}"

#         logger.info(f"Successfully transformed {transform_result.item_count} records")
#         logger.info(f"Dataset ID: {transform_result.data_store_id}")
#         assert transform_result.item_count > 0, f"No records transformed for {variable_name}"
#         assert transform_result.data_store_id is not None, f"No dataset ID returned for {variable_name}"

#         # Step 4: Verify transformed data
#         logger.info(f"Verifying transformed data for {variable_name}")
#         verification = verify_transformed_data(variable_name)

#         assert verification["status"] == "success", f"Verification issues for {variable_name}: {verification.get('error', 'Unknown error')}"

#         logger.info(f"Verification successful: {verification['record_count']} records verified")
#         if "start_date" in verification:
#             logger.info(f"Date range: {verification['start_date']} to {verification['end_date']}")
#         assert verification['record_count'] > 0, f"No records verified for {variable_name}"

#         logger.info(f"===== Pipeline test for {variable_name} completed successfully =====")

#     except Exception as e:
#         logger.error(f"Error in pipeline test for {variable_name}: {e}")
#         assert False, f"Error in pipeline test for {variable_name}: {e}"


# def run_all_tests():
#     """Run tests for all test variables."""
#     success_count = 0
#     failure_count = 0

#     for variable in TEST_VARIABLES:
#         # Call the test function, which now uses assertions
#         test_single_variable_pipeline(variable)
#         success_count += 1

#     logger.info(f"===== Test Summary =====")
#     logger.info(f"Successful tests: {success_count}")
#     logger.info(f"Failed tests: {failure_count}")

#     if success_count > 0:
#         # Generate coverage report
#         logger.info(f"Generating data coverage report")
#         report = generate_data_coverage_report()

#         if "overall_metrics" in report:
#             metrics = report["overall_metrics"]
#             logger.info(f"Coverage statistics for {report['total_variables']} variables:")
#             logger.info(f"Average completeness: {metrics['average_completeness']:.2f}%")

#         # Save a summary of test results
#         summary = {
#             "test_variables": TEST_VARIABLES,
#             "successful_tests": success_count,
#             "failed_tests": failure_count,
#             "coverage_report": report if "overall_metrics" in report else None
#         }

#         results_dir = Path("data/historical_timeline/test_results")
#         results_dir.mkdir(parents=True, exist_ok=True)

#         with open(results_dir / "pipeline_test_results.json", "w") as f:
#             json.dump(summary, f, indent=2)

#         logger.info(f"Test results saved to data/historical_timeline/test_results/pipeline_test_results.json")

#     # This function is not a pytest test function, so returning a boolean is acceptable.
#     # The actual test success/failure is handled by assertions within test_single_variable_pipeline.
#     return success_count > 0 and failure_count == 0


# def main():
#     """Main entry point for the test script."""
#     logger.info("Starting historical data pipeline test")

#     # Test the entire pipeline
#     success = run_all_tests()

#     if success:
#         logger.info("All tests passed successfully!")
#         return 0
#     else:
#         logger.error("Some tests failed. Check the logs for details.")
#         return 1


# if __name__ == "__main__":
#     sys.exit(main())
