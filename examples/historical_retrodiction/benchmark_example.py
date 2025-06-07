#!/usr/bin/env python3
"""
Retrodiction Benchmark Usage Example

This script demonstrates how to use the benchmark_retrodiction module
for performance testing of historical retrodiction components.

Usage:
    python examples/historical_retrodiction/benchmark_example.py
"""

from scripts.benchmarking.benchmark_retrodiction import (
    RetrodictionBenchmark,
    run_benchmark
)
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Demonstrate retrodiction benchmark usage."""
    print("=== Retrodiction Benchmark Usage Example ===\n")

    # 1. Basic benchmark with default parameters
    print("1. Running basic benchmark with default parameters...")
    try:
        basic_results = run_benchmark()
        print(
            f"   Total benchmark time: {
                basic_results['total_benchmark_time']:.2f} seconds")
        print(f"   Components benchmarked: {len(basic_results['components'])}")
        print(f"   System info: {basic_results['system_info']['platform']}")
    except Exception as e:
        print(f"   Basic benchmark failed: {e}")

    # 2. Custom benchmark configuration
    print("\n2. Running benchmark with custom configuration...")
    custom_variables = ["spx_close", "us_10y_yield"]
    custom_results = run_benchmark(
        variables=custom_variables,
        start_date="2020-01-01",
        end_date="2020-01-08",
        batch_size_days=3,
        max_workers=2,
        output_file="custom_benchmark_results.json"
    )

    print(f"   Custom variables: {custom_variables}")
    print(f"   Total time: {custom_results['total_benchmark_time']:.2f} seconds")

    # 3. Individual component benchmarking
    print("\n3. Running individual component benchmarks...")

    # Create benchmark instance for individual testing
    benchmark = RetrodictionBenchmark(
        variables=["spx_close", "us_10y_yield"],
        start_date="2020-01-01",
        end_date="2020-01-05",
        batch_size_days=2
    )

    # Test individual components
    components = [
        ("Data Loading", benchmark.benchmark_data_loading),
        ("Causal Discovery", benchmark.benchmark_causal_discovery),
        ("Trust Updates", benchmark.benchmark_trust_updates),
        ("Curriculum Selection", benchmark.benchmark_curriculum_selection)
    ]

    for component_name, benchmark_func in components:
        try:
            result = benchmark_func()
            execution_time = result.get('execution_time', 0)
            print(f"   {component_name}: {execution_time:.3f} seconds")

            # Show component-specific metrics
            if 'num_variables' in result:
                print(f"     Variables processed: {result['num_variables']}")
            if 'num_data_points' in result:
                print(f"     Data points: {result['num_data_points']}")
            if 'num_updates' in result:
                print(f"     Trust updates: {result['num_updates']}")
            if 'num_iterations' in result:
                print(f"     Iterations: {result['num_iterations']}")

        except Exception as e:
            print(f"   {component_name}: Failed - {e}")

    # 4. Full training benchmark
    print("\n4. Running full training benchmark...")
    try:
        full_result = benchmark.benchmark_full_training()
        print(f"   Full training time: {full_result['execution_time']:.3f} seconds")

        if 'results_summary' in full_result:
            summary = full_result['results_summary']
            if 'batches' in summary:
                print(f"   Batches processed: {summary['batches']['total']}")
                print(f"   Success rate: {summary['batches']['success_rate']:.1%}")
            if 'performance' in summary:
                perf = summary['performance']
                print(f"   Speedup factor: {perf.get('speedup_factor', 'N/A')}")

    except Exception as e:
        print(f"   Full training benchmark failed: {e}")

    # 5. Benchmark results analysis
    print("\n5. Analyzing benchmark results...")

    # Get final comprehensive results
    final_results = benchmark.run_all_benchmarks()

    print(
        f"   Total execution time: {
            final_results['total_benchmark_time']:.2f} seconds")
    print(f"   Timestamp: {final_results['timestamp']}")

    # Component breakdown
    print("   Component breakdown:")
    for component, metrics in final_results['components'].items():
        if isinstance(metrics, dict) and 'execution_time' in metrics:
            print(f"     {component}: {metrics['execution_time']:.3f}s")

    # System information
    print("   System information:")
    sys_info = final_results['system_info']
    print(f"     Platform: {sys_info.get('platform', 'Unknown')}")
    print(f"     CPU count: {sys_info.get('cpu_count', 'Unknown')}")
    print(f"     Python version: {sys_info.get('python_version', 'Unknown')}")
    if 'memory_gb' in sys_info:
        print(f"     Memory: {sys_info['memory_gb']} GB")

    print("\n=== Example completed successfully! ===")
    print("Check the generated JSON files for detailed benchmark results.")


if __name__ == "__main__":
    main()
