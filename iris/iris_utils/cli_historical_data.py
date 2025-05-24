#!/usr/bin/env python
"""iris.iris_utils.cli_historical_data
====================================

Command-line interface for working with historical time series data.
This script provides a unified interface for retrieving, transforming, storing,
and analyzing historical data for the timeline project.

Usage:
------
```
# Retrieve raw historical data
python -m iris.iris_utils.cli_historical_data retrieve --variable spx_close
python -m iris.iris_utils.cli_historical_data retrieve --priority 1

# Transform and store data in standardized format
python -m iris.iris_utils.cli_historical_data transform --variable spx_close
python -m iris.iris_utils.cli_historical_data transform --priority 1

# Verify data consistency and correctness
python -m iris.iris_utils.cli_historical_data verify --variable spx_close
python -m iris.iris_utils.cli_historical_data verify --all

# Generate reports
python -m iris.iris_utils.cli_historical_data report --coverage
python -m iris.iris_utils.cli_historical_data report --summary
```
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Import functionality from other modules
from iris.iris_utils.historical_data_retriever import (
    retrieve_historical_data,
    retrieve_priority_variables,
    load_variable_catalog,
)
from iris.iris_utils.historical_data_transformer import (
    transform_and_store_variable,
    transform_and_store_priority_variables,
    verify_transformed_data,
    generate_data_coverage_report,
)
from iris.iris_utils.historical_data_verification import (
    perform_quality_check,
    detect_anomalies,
    cross_validate_sources,
    analyze_gaps,
    generate_quality_report,
    visualize_data_quality,
)
from iris.iris_utils.historical_data_repair import (
    repair_variable_data,
    simulate_repair,
    get_repair_report,
    repair_multiple_variables,
    revert_to_original,
    compare_versions,
    get_all_versions,
)
from iris.iris_utils.world_bank_integration import (
    integrate_world_bank_data,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def handle_retrieve_command(args):
    """
    Handle the 'retrieve' command to get raw historical data.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        if args.variable:
            # Retrieve specific variable
            catalog = load_variable_catalog()
            var_info = next(
                (
                    var
                    for var in catalog["variables"]
                    if var["variable_name"] == args.variable
                ),
                None,
            )

            if var_info is None:
                logger.error(f"Variable {args.variable} not found in the catalog")
                return 1

            logger.info(f"Retrieving historical data for {args.variable}")
            result = retrieve_historical_data(
                var_info,
                years=args.years,
                end_date=None
                if not args.end_date
                else datetime.strptime(args.end_date, "%Y-%m-%d"),
            )

            if "stats" in result:
                logger.info(
                    f"Successfully retrieved {result['stats']['data_point_count']} data points"
                )
                logger.info(f"Completeness: {result['stats']['completeness_pct']:.2f}%")
            else:
                logger.error(f"Failed to retrieve data for {args.variable}")
                return 1

        elif args.priority:
            # Retrieve all variables with specified priority
            logger.info(f"Retrieving data for all priority {args.priority} variables")
            results = retrieve_priority_variables(
                priority=args.priority,
                years=args.years,
                end_date=None
                if not args.end_date
                else datetime.strptime(args.end_date, "%Y-%m-%d"),
            )

            if not results:
                logger.error(f"No results for priority {args.priority} variables")
                return 1

            successes = sum(1 for r in results.values() if "stats" in r)
            failures = len(results) - successes

            logger.info(f"Retrieved data for {len(results)} variables:")
            logger.info(f"  - Successful: {successes}")
            logger.info(f"  - Failed: {failures}")

        elif args.all:
            # Retrieve all variables
            catalog = load_variable_catalog()
            success_count = 0
            failure_count = 0

            for var_info in catalog["variables"]:
                try:
                    var_name = var_info["variable_name"]
                    logger.info(f"Retrieving data for {var_name}")

                    result = retrieve_historical_data(
                        var_info,
                        years=args.years,
                        end_date=None
                        if not args.end_date
                        else datetime.strptime(args.end_date, "%Y-%m-%d"),
                    )

                    if "stats" in result:
                        success_count += 1
                    else:
                        failure_count += 1

                except Exception as e:
                    logger.error(f"Error retrieving {var_info['variable_name']}: {e}")
                    failure_count += 1

            logger.info(
                f"Retrieved data for {success_count + failure_count} variables:"
            )
            logger.info(f"  - Successful: {success_count}")
            logger.info(f"  - Failed: {failure_count}")

        return 0

    except Exception as e:
        logger.error(f"Error in retrieve command: {e}")
        return 1


def handle_transform_command(args):
    """
    Handle the 'transform' command to transform and store data.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        if args.variable:
            # Transform specific variable
            logger.info(f"Transforming and storing data for {args.variable}")
            result = transform_and_store_variable(args.variable)

            if result.status == "success":
                logger.info(
                    f"Successfully transformed and stored {result.item_count} records"
                )
                logger.info(f"Dataset ID: {result.data_store_id}")
                if result.start_date and result.end_date:
                    logger.info(
                        f"Date range: {result.start_date.date()} to {result.end_date.date()}"
                    )
            else:
                logger.error(f"Failed to transform {args.variable}: {result.error}")
                return 1

        elif args.priority:
            # Transform all variables with specified priority
            logger.info(
                f"Transforming and storing data for all priority {args.priority} variables"
            )
            results = transform_and_store_priority_variables(args.priority)

            if not results:
                logger.error(f"No results for priority {args.priority} variables")
                return 1

            successes = sum(1 for r in results.values() if r.status == "success")
            failures = len(results) - successes

            logger.info(f"Transformed {len(results)} variables:")
            logger.info(f"  - Successful: {successes}")
            logger.info(f"  - Failed: {failures}")

        elif args.all:
            # Transform all variables
            catalog = load_variable_catalog()
            success_count = 0
            failure_count = 0

            for var_info in catalog["variables"]:
                try:
                    var_name = var_info["variable_name"]
                    logger.info(f"Transforming data for {var_name}")

                    result = transform_and_store_variable(var_name)

                    if result.status == "success":
                        success_count += 1
                    else:
                        failure_count += 1
                        logger.warning(
                            f"Failed to transform {var_name}: {result.error}"
                        )

                except Exception as e:
                    logger.error(f"Error transforming {var_info['variable_name']}: {e}")
                    failure_count += 1

            logger.info(f"Transformed {success_count + failure_count} variables:")
            logger.info(f"  - Successful: {success_count}")
            logger.info(f"  - Failed: {failure_count}")

        return 0

    except Exception as e:
        logger.error(f"Error in transform command: {e}")
        return 1


def handle_verify_command(args):
    """
    Handle the 'verify' command to verify data consistency.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        if args.variable:
            # Verify specific variable
            logger.info(f"Verifying data for {args.variable}")
            verification = verify_transformed_data(args.variable)

            if verification["status"] == "success":
                logger.info(f"Verification successful for {args.variable}")
                logger.info(f"Record count: {verification['record_count']}")
                logger.info(f"Non-null values: {verification['non_null_count']}")

                if "start_date" in verification:
                    logger.info(
                        f"Date range: {verification['start_date']} to {verification['end_date']}"
                    )
                    logger.info(f"Range in days: {verification['date_range_days']}")

            elif verification["status"] == "warning":
                logger.warning(
                    f"Verification completed with warnings for {args.variable}"
                )
                logger.warning(f"Found {verification['error_count']} data type errors")

            else:
                logger.error(
                    f"Verification failed for {args.variable}: {verification.get('error', '')}"
                )
                return 1

        elif args.all:
            # Verify all variables
            catalog = load_variable_catalog()
            success_count = 0
            warning_count = 0
            failure_count = 0

            for var_info in catalog["variables"]:
                try:
                    var_name = var_info["variable_name"]
                    logger.info(f"Verifying data for {var_name}")

                    verification = verify_transformed_data(var_name)

                    if verification["status"] == "success":
                        success_count += 1
                    elif verification["status"] == "warning":
                        warning_count += 1
                        logger.warning(
                            f"Warnings for {var_name}: {verification['error_count']} errors"
                        )
                    else:
                        failure_count += 1
                        logger.error(
                            f"Failed verification for {var_name}: {verification.get('error', '')}"
                        )

                except Exception as e:
                    logger.error(f"Error verifying {var_info['variable_name']}: {e}")
                    failure_count += 1

            logger.info(
                f"Verified {success_count + warning_count + failure_count} variables:"
            )
            logger.info(f"  - Success: {success_count}")
            logger.info(f"  - Warning: {warning_count}")
            logger.info(f"  - Failed: {failure_count}")

        return 0

    except Exception as e:
        logger.error(f"Error in verify command: {e}")
        return 1


def handle_report_command(args):
    """
    Handle the 'report' command to generate reports.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        if args.coverage:
            # Generate coverage report
            logger.info("Generating data coverage report")
            report = generate_data_coverage_report()

            if "overall_metrics" in report:
                metrics = report["overall_metrics"]
                logger.info(
                    f"Coverage statistics for {report['total_variables']} variables:"
                )
                logger.info(
                    f"Average completeness: {metrics['average_completeness']:.2f}%"
                )
                logger.info(f"Min completeness: {metrics['min_completeness']:.2f}%")
                logger.info(f"Max completeness: {metrics['max_completeness']:.2f}%")
                logger.info(
                    f"Fully complete variables (≥99%): {metrics['fully_complete_variables']}"
                )
                logger.info(
                    f"Partially complete variables (80-99%): {metrics['partially_complete_variables']}"
                )
                logger.info(
                    f"Incomplete variables (<80%): {metrics['incomplete_variables']}"
                )
            else:
                logger.warning("No coverage metrics available")

        elif args.summary:
            # Generate summary report across all variables
            from recursive_training.data.data_store import RecursiveDataStore

            logger.info("Generating summary report")

            # Get RecursiveDataStore instance
            data_store = RecursiveDataStore.get_instance()

            # Get storage summary
            storage_summary = data_store.get_storage_summary()

            logger.info("Storage summary:")
            logger.info(f"Total items: {storage_summary['total_items']}")
            logger.info(f"Total size: {storage_summary['total_size_mb']:.2f} MB")

            # Get dataset information
            datasets = data_store.get_all_datasets()
            historical_datasets = [
                ds
                for ds in datasets
                if ds.get("dataset_name", "").startswith("historical_")
            ]

            # Group by priority
            by_priority = {}
            for ds in historical_datasets:
                priority = ds.get("priority", 3)
                if priority not in by_priority:
                    by_priority[priority] = []
                by_priority[priority].append(ds)

            logger.info("Historical datasets by priority:")
            for priority, datasets in sorted(by_priority.items()):
                logger.info(f"Priority {priority}: {len(datasets)} variables")

            # Save the summary report
            summary = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "storage_summary": storage_summary,
                "datasets_by_priority": {
                    str(priority): len(datasets)
                    for priority, datasets in by_priority.items()
                },
                "total_historical_datasets": len(historical_datasets),
            }

            report_dir = Path("data/historical_timeline/reports")
            report_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            report_path = report_dir / f"{timestamp}_summary_report.json"

            with open(report_path, "w") as f:
                json.dump(summary, f, indent=2)

            logger.info(f"Saved summary report to {report_path}")

        return 0

    except Exception as e:
        logger.error(f"Error in report command: {e}")
        return 1


def handle_quality_check_command(args):
    """
    Handle the 'quality-check' command to perform comprehensive quality assessment.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        if args.variable:
            # Quality check for specific variable
            logger.info(f"Performing quality check for {args.variable}")
            result = perform_quality_check(
                args.variable,
                anomaly_method=args.anomaly_method,
                variable_type=args.variable_type,
            )

            # Display results
            logger.info(f"Quality check results for {args.variable}:")
            logger.info(
                f"Overall quality score: {result.quality_score.overall_score:.2f}"
            )
            logger.info(f"Completeness: {result.quality_score.completeness:.2f}")
            logger.info(f"Consistency: {result.quality_score.consistency:.2f}")
            logger.info(f"Anomaly-free: {result.quality_score.anomaly_free:.2f}")
            logger.info(f"Time continuity: {result.quality_score.time_continuity:.2f}")
            logger.info(f"Trend stability: {result.quality_score.trend_stability:.2f}")
            logger.info(f"Seasonality: {result.quality_score.seasonality:.2f}")

            if result.anomalies:
                logger.info(f"Detected {len(result.anomalies)} anomalies")

            if result.gaps:
                logger.info(f"Detected {len(result.gaps)} gaps")

            if result.trend_breaks:
                logger.info(f"Detected {len(result.trend_breaks)} trend breaks")

            if result.recommendations:
                logger.info("Recommendations:")
                for rec in result.recommendations:
                    logger.info(f"  - {rec}")

            # Save results to file if requested
            if args.output:
                output_file = args.output
                with open(output_file, "w") as f:
                    json.dump(result.to_dict(), f, indent=2)
                logger.info(f"Results saved to {output_file}")

            # Generate visualizations if requested
            if args.visualize:
                logger.info(f"Generating visualizations for {args.variable}")
                vis_paths = visualize_data_quality(args.variable)
                logger.info("Visualizations saved to:")
                for vis_type, path in vis_paths.items():
                    logger.info(f"  - {vis_type}: {path}")

        elif args.priority:
            # Run quality check for all variables with the specified priority
            logger.info(
                f"Performing quality check for all priority {args.priority} variables"
            )
            report = generate_quality_report(priority=args.priority)

            # Display summary
            logger.info(f"Quality report for priority {args.priority} variables:")
            stats = report["overall_statistics"]
            logger.info(f"Average overall score: {stats['average_overall_score']:.2f}")
            logger.info(f"Variables analyzed: {report['variables_analyzed']}")
            logger.info(f"Variables with gaps: {stats['variables_with_gaps']}")
            logger.info(
                f"Variables with anomalies: {stats['variables_with_anomalies']}"
            )

            # Save report to file
            output_file = (
                args.output
                if args.output
                else f"quality_report_priority_{args.priority}.json"
            )
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {output_file}")

        elif args.all:
            # Quality check for all variables
            logger.info("Performing quality check for all variables")
            report = generate_quality_report()

            # Display summary
            logger.info("Quality report for all variables:")
            stats = report["overall_statistics"]
            logger.info(f"Average overall score: {stats['average_overall_score']:.2f}")
            logger.info(f"Variables analyzed: {report['variables_analyzed']}")
            logger.info(
                f"Variables with issues: {stats['variables_with_gaps'] + stats['variables_with_anomalies']}"
            )

            # Display quality distribution
            quality_dist = stats["quality_distribution"]
            logger.info("Quality distribution:")
            logger.info(f"  - Excellent: {quality_dist['excellent']}")
            logger.info(f"  - Good: {quality_dist['good']}")
            logger.info(f"  - Fair: {quality_dist['fair']}")
            logger.info(f"  - Poor: {quality_dist['poor']}")

            # Save report to file
            output_file = args.output if args.output else "quality_report_all.json"
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {output_file}")

        return 0

    except Exception as e:
        logger.error(f"Error in quality-check command: {e}")
        return 1


def handle_anomaly_detect_command(args):
    """
    Handle the 'anomaly-detect' command to detect anomalies in time series data.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        if not args.variable:
            logger.error("Variable name is required for anomaly detection")
            return 1

        logger.info(
            f"Detecting anomalies in {args.variable} using {args.method} method"
        )

        # Load the data
        from iris.iris_utils.historical_data_verification import load_processed_data

        series = load_processed_data(args.variable)

        # Detect anomalies
        anomalies = detect_anomalies(
            series,
            method=args.method,
            threshold=args.threshold,
            window_size=args.window_size,
            variable_type=args.variable_type,
        )

        # Display results
        if anomalies:
            logger.info(f"Detected {len(anomalies)} anomalies in {args.variable}")
            for i, anomaly in enumerate(
                sorted(anomalies, key=lambda a: a.severity, reverse=True)
            ):
                if i < 10:  # Show top 10 anomalies by severity
                    logger.info(
                        f"  - {anomaly.timestamp.date()}: value={anomaly.value:.4f}, "
                        + f"severity={anomaly.severity:.2f}, method={anomaly.method}"
                    )
        else:
            logger.info(f"No anomalies detected in {args.variable}")

        # Save results to file if requested
        if args.output:
            output_file = args.output
            with open(output_file, "w") as f:
                json.dump([a.to_dict() for a in anomalies], f, indent=2)
            logger.info(f"Results saved to {output_file}")

        # Generate visualization if requested
        if args.visualize:
            logger.info(
                f"Generating visualization for {args.variable} with anomalies highlighted"
            )
            vis_paths = visualize_data_quality(
                args.variable, show_gaps=False, show_trend_breaks=False
            )
            logger.info(
                f"Visualization saved to: {vis_paths.get('time_series', 'unknown')}"
            )

        return 0

    except Exception as e:
        logger.error(f"Error in anomaly-detect command: {e}")
        return 1


def handle_cross_validate_command(args):
    """
    Handle the 'cross-validate' command to compare data from different sources.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        if not args.variable:
            logger.error("Variable name is required for cross-validation")
            return 1

        logger.info(
            f"Cross-validating data for {args.variable} across different sources"
        )

        # Perform cross-validation
        result = cross_validate_sources(args.variable)

        # Display results
        if result.sources:
            logger.info(f"Cross-validation results for {args.variable}:")
            logger.info(
                f"Found {len(result.sources)} sources: {', '.join(result.sources)}"
            )

            # Show correlation matrix
            logger.info("Correlation matrix:")
            for source1 in result.sources:
                for source2 in result.sources:
                    if source1 != source2:
                        corr = result.correlation_matrix[source1][source2]
                        logger.info(f"  - {source1} vs {source2}: {corr:.3f}")

            # Show recommendation
            logger.info(f"Recommendation: {result.recommendation}")
        else:
            logger.error(f"Cross-validation failed: {result.recommendation}")

        # Save results to file if requested
        if args.output:
            output_file = args.output
            with open(output_file, "w") as f:
                json.dump(result.to_dict(), f, indent=2)
            logger.info(f"Results saved to {output_file}")

        # Generate visualization if requested
        if args.visualize and result.sources:
            logger.info(
                f"Generating cross-source comparison visualization for {args.variable}"
            )
            # The visualization function will automatically create a cross-source chart if multiple sources are available
            vis_paths = visualize_data_quality(
                args.variable,
                show_anomalies=False,
                show_gaps=False,
                show_trend_breaks=False,
            )
            logger.info(
                f"Cross-source visualization saved to: {vis_paths.get('cross_source', 'not created')}"
            )

        return 0

    except Exception as e:
        logger.error(f"Error in cross-validate command: {e}")
        return 1


def handle_repair_command(args):
    """
    Handle the 'repair' command to repair data quality issues.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        if args.variable:
            # Repair specific variable
            logger.info(f"Repairing data quality issues for {args.variable}")
            result = repair_variable_data(
                args.variable,
                variable_type=args.variable_type,
                skip_smoothing=args.skip_smoothing,
                skip_cross_source=args.skip_cross_source,
            )

            # Display results
            if result.status == "success":
                logger.info(f"Successfully repaired {args.variable}")
                logger.info(f"Total repairs made: {result.total_repairs}")
                logger.info(f"- Gap fills: {result.gap_fills}")
                logger.info(f"- Anomaly corrections: {result.anomaly_corrections}")
                logger.info(f"- Smoothing actions: {result.smoothing_actions}")
                logger.info(
                    f"- Cross-source reconciliations: {result.cross_source_actions}"
                )
                logger.info(f"Quality improvement: {result.quality_improvement:.3f}")
                logger.info(f"Version ID: {result.version_id}")
            elif result.status == "no_repairs_needed":
                logger.info(f"No repairs needed for {args.variable}")
            else:
                logger.error(f"Failed to repair {args.variable}: {result.error}")
                return 1

        elif args.priority:
            # Repair all variables with specified priority
            logger.info(
                f"Repairing data quality issues for all priority {args.priority} variables"
            )

            # Get variables with the specified priority
            from iris.iris_utils.historical_data_retriever import get_priority_variables

            priority_vars = get_priority_variables(args.priority)
            variable_names = [var["variable_name"] for var in priority_vars]

            if not variable_names:
                logger.warning(f"No variables found with priority {args.priority}")
                return 0

            # Repair all variables
            results = repair_multiple_variables(variable_names)

            # Count successes and failures
            success_count = sum(1 for r in results.values() if r.status == "success")
            no_repair_count = sum(
                1 for r in results.values() if r.status == "no_repairs_needed"
            )
            failure_count = len(results) - success_count - no_repair_count

            # Log summary
            logger.info(f"Repaired {len(results)} variables:")
            logger.info(f"  - Successfully repaired: {success_count}")
            logger.info(f"  - No repairs needed: {no_repair_count}")
            logger.info(f"  - Failed: {failure_count}")

            # Total repairs
            total_repairs = sum(
                r.total_repairs for r in results.values() if r.status == "success"
            )
            logger.info(f"Total repairs made across all variables: {total_repairs}")

        elif args.all:
            # Repair all variables
            logger.info("Repairing data quality issues for all variables")

            # Get all variables from the catalog
            from iris.iris_utils.historical_data_retriever import load_variable_catalog

            catalog = load_variable_catalog()
            variable_names = [var["variable_name"] for var in catalog["variables"]]

            # Repair all variables
            results = repair_multiple_variables(variable_names)

            # Count successes and failures
            success_count = sum(1 for r in results.values() if r.status == "success")
            no_repair_count = sum(
                1 for r in results.values() if r.status == "no_repairs_needed"
            )
            failure_count = len(results) - success_count - no_repair_count

            # Log summary
            logger.info(f"Repaired {len(results)} variables:")
            logger.info(f"  - Successfully repaired: {success_count}")
            logger.info(f"  - No repairs needed: {no_repair_count}")
            logger.info(f"  - Failed: {failure_count}")

            # Total repairs
            total_repairs = sum(
                r.total_repairs for r in results.values() if r.status == "success"
            )
            logger.info(f"Total repairs made across all variables: {total_repairs}")

        return 0

    except Exception as e:
        logger.error(f"Error in repair command: {e}")
        return 1


def handle_simulate_repair_command(args):
    """
    Handle the 'simulate-repair' command to preview repairs without applying them.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        if not args.variable:
            logger.error("Variable name is required for repair simulation")
            return 1

        logger.info(f"Simulating repairs for {args.variable}")

        # Simulate repairs
        result = simulate_repair(args.variable, variable_type=args.variable_type)

        # Display results
        if result.status == "success":
            logger.info(f"Simulated repairs for {args.variable}:")
            logger.info(f"Total potential repairs: {result.total_repairs}")
            logger.info(f"- Gap fills: {result.gap_fills}")
            logger.info(f"- Anomaly corrections: {result.anomaly_corrections}")
            logger.info(f"- Smoothing actions: {result.smoothing_actions}")
            logger.info(
                f"- Cross-source reconciliations: {result.cross_source_actions}"
            )
            logger.info(
                f"Potential quality improvement: {result.quality_improvement:.3f}"
            )
            logger.info(f"Simulation version ID: {result.version_id}")

            # Save detailed report if requested
            if args.output:
                output_file = args.output
                with open(output_file, "w") as f:
                    json.dump(result.to_dict(), f, indent=2)
                logger.info(f"Detailed simulation report saved to {output_file}")

        elif result.status == "no_repairs_needed":
            logger.info(f"No repairs needed for {args.variable}")
        else:
            logger.error(
                f"Failed to simulate repairs for {args.variable}: {result.error}"
            )
            return 1

        return 0

    except Exception as e:
        logger.error(f"Error in simulate-repair command: {e}")
        return 1


def handle_repair_report_command(args):
    """
    Handle the 'repair-report' command to generate a report of repairs made.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        if args.variable:
            # Get report for a specific variable
            logger.info(f"Generating repair report for {args.variable}")

            if args.version:
                # Specific version
                report = get_repair_report(args.variable, args.version)
            else:
                # Latest version
                report = get_repair_report(args.variable)

            if report["status"] == "success" or "actions" in report:
                # Display summary
                logger.info(f"Repair report for {args.variable}:")
                logger.info(f"Version ID: {report.get('version_id', 'unknown')}")
                logger.info(f"Timestamp: {report.get('timestamp', 'unknown')}")
                logger.info(f"Total actions: {report.get('total_actions', 0)}")

                # Show action types
                action_types = report.get("action_types", {})
                logger.info("Action types:")
                for action_type, count in action_types.items():
                    logger.info(f"  - {action_type}: {count}")

                # Show strategies
                action_strategies = report.get("action_strategies", {})
                logger.info("Strategies used:")
                for strategy, count in action_strategies.items():
                    logger.info(f"  - {strategy}: {count}")

                # Save detailed report if requested
                if args.output:
                    output_file = args.output
                    with open(output_file, "w") as f:
                        json.dump(report, f, indent=2)
                    logger.info(f"Detailed report saved to {output_file}")

            elif report["status"] == "no_versions":
                logger.info(f"No repair versions found for {args.variable}")
            elif report["status"] == "version_not_found":
                logger.error(f"Version {args.version} not found for {args.variable}")
                return 1
            else:
                logger.warning(f"Unusual report status: {report['status']}")
                logger.warning(report.get("message", "No details available"))

        elif args.list_versions:
            # List all versions for a variable
            variable_name = args.list_versions
            logger.info(f"Listing all repair versions for {variable_name}")

            versions = get_all_versions(variable_name)

            if versions["status"] == "success":
                logger.info(
                    f"Found {len(versions['versions'])} versions for {variable_name}:"
                )

                for version in versions["versions"]:
                    logger.info(
                        f"- {version['version_id']}: {version['timestamp']} ({version['version_type']})"
                    )
                    logger.info(f"  Actions: {version['total_actions']}")

                # Save version list if requested
                if args.output:
                    output_file = args.output
                    with open(output_file, "w") as f:
                        json.dump(versions, f, indent=2)
                    logger.info(f"Version list saved to {output_file}")

            else:
                logger.info(versions.get("message", "No details available"))

        elif args.revert:
            # Revert to original state
            variable_name, version_id = args.revert, args.version

            logger.info(f"Reverting {variable_name} to original state")
            if version_id:
                logger.info(f"Using version: {version_id}")

            result = revert_to_original(variable_name, version_id)

            if result["status"] == "success":
                logger.info(f"Successfully reverted {variable_name} to original state")
                logger.info(f"From version: {result['version_id']}")
                logger.info(f"Timestamp: {result['timestamp']}")
            else:
                logger.error(
                    f"Failed to revert: {result.get('message', 'Unknown error')}"
                )
                return 1

        elif args.compare:
            # Compare versions
            variable_name, version1, version2 = (
                args.compare,
                args.version,
                args.version2,
            )

            if not version1:
                logger.error("At least one version ID is required for comparison")
                return 1

            logger.info(f"Comparing versions for {variable_name}")
            if version2:
                logger.info(f"Comparing version {version1} to {version2}")
            else:
                logger.info(f"Comparing version {version1} to latest repaired version")

            result = compare_versions(variable_name, version1, version2)

            if result["status"] == "success":
                logger.info(f"Version comparison for {variable_name}:")
                logger.info(
                    f"Version 1: {result['version_id1']} ({result['version1_type']})"
                )
                logger.info(
                    f"Version 2: {result['version_id2']} ({result['version2_type']})"
                )
                logger.info(f"Points in version 1: {result['points_in_version1']}")
                logger.info(f"Points in version 2: {result['points_in_version2']}")
                logger.info(f"Common points: {result['common_points']}")

                # Show difference statistics
                diff_stats = result.get("diff_stats", {})
                if diff_stats:
                    logger.info("Difference statistics:")
                    logger.info(
                        f"  Mean difference: {diff_stats.get('mean_difference', 0):.4f}"
                    )
                    logger.info(
                        f"  Median difference: {diff_stats.get('median_difference', 0):.4f}"
                    )
                    logger.info(
                        f"  Standard deviation: {diff_stats.get('std_difference', 0):.4f}"
                    )
                    logger.info(
                        f"  Number of differences: {diff_stats.get('num_differences', 0)}"
                    )

                # Save comparison report if requested
                if args.output:
                    output_file = args.output
                    with open(output_file, "w") as f:
                        json.dump(result, f, indent=2)
                    logger.info(f"Comparison report saved to {output_file}")

            else:
                logger.error(
                    f"Failed to compare versions: {result.get('message', 'Unknown error')}"
                )
                return 1

        else:
            logger.error(
                "Missing required arguments. Use --variable, --list-versions, --revert, or --compare."
            )
            return 1

        return 0

    except Exception as e:
        logger.error(f"Error in repair-report command: {e}")
        return 1


def handle_world_bank_command(args):
    """
    Handle the 'world-bank' command to integrate World Bank historical data.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info("Starting World Bank data integration")

        # Determine the input file
        csv_path = args.file
        zip_path = args.zip

        # Integration options
        update_catalog = not args.no_catalog_update

        # Integrate the data
        results = integrate_world_bank_data(
            csv_path=csv_path, zip_path=zip_path, update_catalog=update_catalog
        )

        # Display results
        success_count = sum(1 for r in results.values() if r.status == "success")
        error_count = sum(1 for r in results.values() if r.status == "error")
        total_records = sum(
            r.item_count for r in results.values() if r.status == "success"
        )

        logger.info("World Bank data integration complete:")
        logger.info(f"Total variables processed: {len(results)}")
        logger.info(f"Successfully integrated: {success_count}")
        logger.info(f"Failed: {error_count}")
        logger.info(f"Total records integrated: {total_records}")

        # Show details of failed variables
        if error_count > 0:
            logger.warning("Failed variables:")
            for var_name, result in results.items():
                if result.status == "error":
                    logger.warning(f"  - {var_name}: {result.error}")

        return 0

    except Exception as e:
        logger.error(f"Error in world-bank command: {e}")
        return 1


def handle_gap_analysis_command(args):
    """
    Handle the 'gap-analysis' command to identify and report on gaps in time series.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        if not args.variable:
            logger.error("Variable name is required for gap analysis")
            return 1

        logger.info(f"Analyzing gaps in {args.variable}")

        # Perform gap analysis
        result = analyze_gaps(
            args.variable, freq=args.frequency, min_gap_size=args.min_gap_size
        )

        # Display results
        if "error" not in result:
            logger.info(f"Gap analysis results for {args.variable}:")
            logger.info(f"Total gaps: {result['total_gaps']}")
            logger.info(f"Total gap days: {result['total_gap_days']}")
            logger.info(f"Data completeness: {result['completeness']:.2%}")

            if result["gaps"]:
                logger.info("Top gaps by duration:")
                # Sort gaps by duration and show the top 5
                sorted_gaps = sorted(
                    result["gaps"], key=lambda g: g["gap_duration_days"], reverse=True
                )
                for i, gap in enumerate(sorted_gaps[:5]):
                    logger.info(
                        f"  - {gap['start_time']} to {gap['end_time']}: {gap['gap_duration_days']} days"
                    )

            logger.info(f"Recommendation: {result['recommendation']}")
        else:
            logger.error(f"Gap analysis failed: {result['error']}")

        # Save results to file if requested
        if args.output:
            output_file = args.output
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"Results saved to {output_file}")

        # Generate visualization if requested
        if args.visualize and "error" not in result:
            logger.info(f"Generating gap visualization for {args.variable}")
            vis_paths = visualize_data_quality(
                args.variable, show_anomalies=False, show_trend_breaks=False
            )
            logger.info(
                f"Visualization with gaps highlighted saved to: {vis_paths.get('time_series', 'unknown')}"
            )
            logger.info(
                f"Completeness visualization saved to: {vis_paths.get('completeness', 'not created')}"
            )

        return 0

    except Exception as e:
        logger.error(f"Error in gap-analysis command: {e}")
        return 1


def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(
        description="Command-line tool for working with historical time series data"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # 'retrieve' command
    retrieve_parser = subparsers.add_parser(
        "retrieve", help="Retrieve raw historical data"
    )
    retrieve_group = retrieve_parser.add_mutually_exclusive_group(required=True)
    retrieve_group.add_argument(
        "--variable", type=str, help="Name of variable to retrieve"
    )
    retrieve_group.add_argument(
        "--priority", type=int, help="Retrieve variables with this priority"
    )
    retrieve_group.add_argument(
        "--all", action="store_true", help="Retrieve all variables"
    )
    retrieve_parser.add_argument(
        "--years", type=int, default=5, help="Number of years of data to retrieve"
    )
    retrieve_parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")

    # 'transform' command
    transform_parser = subparsers.add_parser(
        "transform", help="Transform and store data"
    )
    transform_group = transform_parser.add_mutually_exclusive_group(required=True)
    transform_group.add_argument(
        "--variable", type=str, help="Name of variable to transform"
    )
    transform_group.add_argument(
        "--priority", type=int, help="Transform variables with this priority"
    )
    transform_group.add_argument(
        "--all", action="store_true", help="Transform all variables"
    )

    # 'verify' command
    verify_parser = subparsers.add_parser("verify", help="Verify data consistency")
    verify_group = verify_parser.add_mutually_exclusive_group(required=True)
    verify_group.add_argument("--variable", type=str, help="Name of variable to verify")
    verify_group.add_argument("--all", action="store_true", help="Verify all variables")

    # 'report' command
    report_parser = subparsers.add_parser("report", help="Generate reports")
    report_group = report_parser.add_mutually_exclusive_group(required=True)
    report_group.add_argument(
        "--coverage", action="store_true", help="Generate data coverage report"
    )
    report_group.add_argument(
        "--summary", action="store_true", help="Generate summary report"
    )

    # 'quality-check' command - NEW COMMAND
    quality_parser = subparsers.add_parser(
        "quality-check", help="Perform comprehensive quality assessment"
    )
    quality_group = quality_parser.add_mutually_exclusive_group(required=True)
    quality_group.add_argument("--variable", type=str, help="Name of variable to check")
    quality_group.add_argument(
        "--priority", type=int, help="Check variables with this priority"
    )
    quality_group.add_argument("--all", action="store_true", help="Check all variables")
    quality_parser.add_argument(
        "--anomaly-method",
        type=str,
        default="zscore",
        choices=["zscore", "iqr", "isolation_forest"],
        help="Method to use for anomaly detection",
    )
    quality_parser.add_argument(
        "--variable-type",
        type=str,
        default="raw",
        choices=["raw", "price", "percentage", "rate", "index", "count", "temperature"],
        help="Type of variable (for range validation)",
    )
    quality_parser.add_argument(
        "--output", type=str, help="Output file for results (JSON)"
    )
    quality_parser.add_argument(
        "--visualize", action="store_true", help="Generate visualizations"
    )

    # 'anomaly-detect' command - NEW COMMAND
    anomaly_parser = subparsers.add_parser(
        "anomaly-detect", help="Identify and report anomalies"
    )
    anomaly_parser.add_argument(
        "--variable", type=str, required=True, help="Name of variable to analyze"
    )
    anomaly_parser.add_argument(
        "--method",
        type=str,
        default="zscore",
        choices=["zscore", "iqr", "isolation_forest"],
        help="Anomaly detection method",
    )
    anomaly_parser.add_argument(
        "--threshold", type=float, default=3.0, help="Threshold for anomaly detection"
    )
    anomaly_parser.add_argument(
        "--window-size", type=int, help="Window size for contextual anomaly detection"
    )
    anomaly_parser.add_argument(
        "--variable-type",
        type=str,
        default="raw",
        choices=["raw", "price", "percentage", "rate", "index", "count", "temperature"],
        help="Type of variable (for range validation)",
    )
    anomaly_parser.add_argument(
        "--output", type=str, help="Output file for results (JSON)"
    )
    anomaly_parser.add_argument(
        "--visualize", action="store_true", help="Generate visualization"
    )

    # 'cross-validate' command - NEW COMMAND
    cross_parser = subparsers.add_parser(
        "cross-validate", help="Compare data from different sources"
    )
    cross_parser.add_argument(
        "--variable", type=str, required=True, help="Name of variable to cross-validate"
    )
    cross_parser.add_argument(
        "--output", type=str, help="Output file for results (JSON)"
    )
    cross_parser.add_argument(
        "--visualize", action="store_true", help="Generate visualization"
    )

    # 'gap-analysis' command - NEW COMMAND
    gap_parser = subparsers.add_parser(
        "gap-analysis", help="Identify and report on gaps in time series"
    )
    gap_parser.add_argument(
        "--variable", type=str, required=True, help="Name of variable to analyze"
    )
    gap_parser.add_argument(
        "--frequency",
        type=str,
        default="auto",
        choices=["auto", "D", "B", "W", "M"],
        help="Expected frequency of the data (D=daily, B=business, W=weekly, M=monthly)",
    )
    gap_parser.add_argument(
        "--min-gap-size",
        type=int,
        default=1,
        help="Minimum number of missing points to consider a gap",
    )
    gap_parser.add_argument("--output", type=str, help="Output file for results (JSON)")
    gap_parser.add_argument(
        "--visualize", action="store_true", help="Generate visualization"
    )

    # 'repair' command
    repair_parser = subparsers.add_parser("repair", help="Repair data quality issues")
    repair_group = repair_parser.add_mutually_exclusive_group(required=True)
    repair_group.add_argument("--variable", type=str, help="Name of variable to repair")
    repair_group.add_argument(
        "--priority", type=int, help="Repair variables with this priority"
    )
    repair_group.add_argument("--all", action="store_true", help="Repair all variables")
    repair_parser.add_argument(
        "--variable-type",
        type=str,
        default="raw",
        choices=["raw", "price", "percentage", "rate", "index", "count", "temperature"],
        help="Type of variable (for strategy selection)",
    )
    repair_parser.add_argument(
        "--skip-smoothing", action="store_true", help="Skip data smoothing step"
    )
    repair_parser.add_argument(
        "--skip-cross-source",
        action="store_true",
        help="Skip cross-source reconciliation",
    )

    # 'simulate-repair' command
    simulate_parser = subparsers.add_parser(
        "simulate-repair", help="Simulate repairs without applying them"
    )
    simulate_parser.add_argument(
        "--variable",
        type=str,
        required=True,
        help="Name of variable to simulate repairs on",
    )
    simulate_parser.add_argument(
        "--variable-type",
        type=str,
        default="raw",
        choices=["raw", "price", "percentage", "rate", "index", "count", "temperature"],
        help="Type of variable (for strategy selection)",
    )
    simulate_parser.add_argument(
        "--output", type=str, help="Output file for detailed simulation results (JSON)"
    )

    # 'repair-report' command
    report_parser = subparsers.add_parser(
        "repair-report", help="Generate a report of repairs made"
    )
    report_group = report_parser.add_mutually_exclusive_group(required=True)
    report_group.add_argument(
        "--variable", type=str, help="Name of variable to get repair report for"
    )
    report_group.add_argument(
        "--list-versions",
        type=str,
        metavar="VARIABLE",
        help="List all repair versions for a variable",
    )
    report_group.add_argument(
        "--revert",
        type=str,
        metavar="VARIABLE",
        help="Revert a variable to its original (pre-repair) state",
    )
    report_group.add_argument(
        "--compare",
        type=str,
        metavar="VARIABLE",
        help="Compare two versions of a variable",
    )
    report_parser.add_argument(
        "--version", type=str, help="Version ID for operations that need a version"
    )
    report_parser.add_argument(
        "--version2",
        type=str,
        help="Second version ID for comparison (uses latest if not provided)",
    )
    report_parser.add_argument(
        "--output", type=str, help="Output file for report (JSON)"
    )

    # 'world-bank' command - NEW COMMAND
    wb_parser = subparsers.add_parser(
        "world-bank", help="Integrate World Bank data into the historical data pipeline"
    )
    wb_input_group = wb_parser.add_mutually_exclusive_group(required=False)
    wb_input_group.add_argument("--file", type=str, help="Path to World Bank CSV file")
    wb_input_group.add_argument("--zip", type=str, help="Path to World Bank ZIP file")
    wb_parser.add_argument(
        "--no-catalog-update",
        action="store_true",
        help="Skip updating the variable catalog",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    # Handle the chosen command
    if args.command == "retrieve":
        return handle_retrieve_command(args)
    elif args.command == "transform":
        return handle_transform_command(args)
    elif args.command == "verify":
        return handle_verify_command(args)
    elif args.command == "report":
        return handle_report_command(args)
    elif args.command == "quality-check":
        return handle_quality_check_command(args)
    elif args.command == "anomaly-detect":
        return handle_anomaly_detect_command(args)
    elif args.command == "cross-validate":
        return handle_cross_validate_command(args)
    elif args.command == "gap-analysis":
        return handle_gap_analysis_command(args)
    elif args.command == "repair":
        return handle_repair_command(args)
    elif args.command == "simulate-repair":
        return handle_simulate_repair_command(args)
    elif args.command == "repair-report":
        return handle_repair_report_command(args)
    elif args.command == "world-bank":
        return handle_world_bank_command(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
