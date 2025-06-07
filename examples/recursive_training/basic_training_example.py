#!/usr/bin/env python3
"""
Basic Recursive Training Example

This script demonstrates how to set up and run a basic recursive training
process using the Pulse recursive training system. It shows the complete
workflow from configuration to execution.

Usage:
    python examples/recursive_training/basic_training_example.py

Requirements:
    - The script should be run from the project root directory
    - Ensure all dependencies are installed
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from recursive_training.config.training_config import (
    TrainingConfig,
    create_training_config,
)
from recursive_training.stages.training_stages import TrainingPipeline
from recursive_training.parallel_trainer import (
    ParallelTrainingCoordinator,
    run_parallel_retrodiction_training,
)


def create_basic_config() -> TrainingConfig:
    """Create a basic training configuration for demonstration.

    Returns:
        TrainingConfig: A configured training setup for a short demo run.
    """
    print("Creating basic training configuration...")

    # Create configuration with minimal settings for quick demo
    config = create_training_config(
        variables=["spx_close", "us_10y_yield"],
        batch_size_days=15,  # Smaller batches for faster demo
        start_date="2023-01-01",
        end_date="2023-02-28",  # Short period for demo
        max_workers=2,  # Limit workers for demo
        batch_limit=3,  # Limit batches for quick demo
        log_level="INFO",
        log_dir="logs/demo",
    )

    print(f"Configuration created:")
    print(f"  Variables: {config.variables}")
    print(f"  Training period: {config.start_date} to {config.end_date}")
    print(f"  Batch size: {config.batch_size_days} days")
    print(f"  Max workers: {config.max_workers}")
    print(f"  Batch limit: {config.batch_limit}")

    return config


def run_with_pipeline(config: TrainingConfig) -> None:
    """Demonstrate running training using the TrainingPipeline.

    Args:
        config: Training configuration to use.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Using TrainingPipeline")
    print("=" * 60)

    try:
        # Create and execute the training pipeline
        pipeline = TrainingPipeline()
        print("Executing training pipeline...")

        results = pipeline.execute(config)

        # Check results
        if results.get("training_success"):
            print("✅ Training pipeline completed successfully!")

            # Display some results
            training_results = results.get("training_results", {})
            if training_results:
                batches = training_results.get("batches", {})
                print(f"   Batches completed: {batches.get('completed', 0)}")
                print(f"   Success rate: {batches.get('success_rate', 0):.2%}")

                performance = training_results.get("performance", {})
                duration = performance.get("duration_seconds", 0)
                print(f"   Duration: {duration:.2f} seconds")
        else:
            error = results.get("training_error", "Unknown error")
            print(f"❌ Training pipeline failed: {error}")

    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")


def run_with_coordinator(config: TrainingConfig) -> None:
    """Demonstrate running training using ParallelTrainingCoordinator directly.

    Args:
        config: Training configuration to use.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Using ParallelTrainingCoordinator")
    print("=" * 60)

    try:
        # Create coordinator
        coordinator = ParallelTrainingCoordinator(
            max_workers=config.max_workers,
            dask_dashboard_port=8788,  # Use different port for demo
        )

        # Prepare training batches
        print("Preparing training batches...")
        start_date = datetime.strptime(config.start_date, "%Y-%m-%d")
        end_date = (
            datetime.strptime(config.end_date, "%Y-%m-%d")
            if config.end_date
            else datetime.now()
        )

        batches = coordinator.prepare_training_batches(
            variables=config.variables,
            start_time=start_date,
            end_time=end_date,
            batch_size_days=config.batch_size_days,
            batch_limit=config.batch_limit,
        )

        print(f"Created {len(batches)} training batches")

        # Define progress callback
        def progress_callback(progress_data):
            completed = progress_data.get("completed_batches", 0)
            total = progress_data.get("total_batches", 0)
            percentage = progress_data.get("completed_percentage", "0%")
            print(f"   Progress: {percentage} ({completed}/{total} batches)")

        # Start training
        print("Starting parallel training...")
        coordinator.start_training(progress_callback=progress_callback)

        # Get results summary
        results = coordinator.get_results_summary()

        print("✅ Training completed!")
        print(
            f"   Batches: {results['batches']['completed']}/{results['batches']['total']}"
        )
        print(f"   Success rate: {results['batches']['success_rate']:.2%}")
        print(f"   Duration: {results['performance']['duration_seconds']:.2f} seconds")
        print(f"   Speedup factor: {results['performance']['speedup_factor']:.2f}x")

    except Exception as e:
        print(f"❌ Coordinator execution failed: {e}")


def run_with_convenience_function(config: TrainingConfig) -> None:
    """Demonstrate using the convenience function for training.

    Args:
        config: Training configuration to use.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Using Convenience Function")
    print("=" * 60)

    try:
        # Convert config dates to datetime objects
        start_date = datetime.strptime(config.start_date, "%Y-%m-%d")
        end_date = (
            datetime.strptime(config.end_date, "%Y-%m-%d")
            if config.end_date
            else datetime.now()
        )

        # Run training using convenience function
        print("Running training with convenience function...")
        results = run_parallel_retrodiction_training(
            variables=config.variables,
            start_time=start_date,
            end_time=end_date,
            max_workers=config.max_workers,
            batch_size_days=config.batch_size_days,
            batch_limit=config.batch_limit,
            output_file="demo_results.json",
            dask_dashboard_port=8789,  # Different port for demo
        )

        print("✅ Training completed!")
        print(
            f"   Batches: {results['batches']['completed']}/{results['batches']['total']}"
        )
        print(f"   Success rate: {results['batches']['success_rate']:.2%}")
        print(f"   Duration: {results['performance']['duration_seconds']:.2f} seconds")
        print(f"   Results saved to: demo_results.json")

    except Exception as e:
        print(f"❌ Convenience function execution failed: {e}")


def demonstrate_config_validation():
    """Demonstrate configuration validation features."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Configuration Validation")
    print("=" * 60)

    print("Testing valid configuration...")
    try:
        valid_config = TrainingConfig(
            variables=["spx_close"],
            batch_size_days=30,
            start_date="2023-01-01",
            end_date="2023-12-31",
        )
        valid_config.validate()
        print("✅ Valid configuration passed validation")
    except ValueError as e:
        print(f"❌ Unexpected validation error: {e}")

    print("\nTesting invalid configurations...")

    # Test empty variables
    try:
        invalid_config = TrainingConfig(variables=[])
        invalid_config.validate()
        print("❌ Empty variables should have failed validation")
    except ValueError:
        print("✅ Empty variables correctly rejected")

    # Test invalid date format
    try:
        invalid_config = TrainingConfig(start_date="invalid-date")
        invalid_config.validate()
        print("❌ Invalid date should have failed validation")
    except ValueError:
        print("✅ Invalid date format correctly rejected")

    # Test negative batch size
    try:
        invalid_config = TrainingConfig(batch_size_days=-1)
        invalid_config.validate()
        print("❌ Negative batch size should have failed validation")
    except ValueError:
        print("✅ Negative batch size correctly rejected")


def main():
    """Main demonstration function."""
    print("Pulse Recursive Training - Basic Example")
    print("=" * 60)

    # Create basic configuration
    config = create_basic_config()

    # Demonstrate configuration validation
    demonstrate_config_validation()

    # Run different training approaches
    run_with_pipeline(config)
    run_with_coordinator(config)
    run_with_convenience_function(config)

    print("\n" + "=" * 60)
    print("Demo completed! Check the following files:")
    print("  - logs/demo/retrodiction_training.log (training logs)")
    print("  - demo_results.json (training results)")
    print("=" * 60)


if __name__ == "__main__":
    main()
