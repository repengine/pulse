#!/usr/bin/env python
"""
run_causal_benchmarks.py

Executes a set of causal-only benchmark scenarios by running simulations with the
gravity mechanism disabled (using the --gravity-off flag). This allows for measuring
the performance of the purely causal components of the system without the influence
of the gravity correction.

The script:
1. Defines or loads benchmark scenarios from configuration
2. Executes each scenario using the batch_runner with gravity disabled
3. Collects key performance metrics
4. Stores results in a structured format for later analysis

Usage:
    python scripts/run_causal_benchmarks.py
    python scripts/run_causal_benchmarks.py --config benchmark_config.yaml
    python scripts/run_causal_benchmarks.py --output custom_output.jsonl
"""

import os
import sys
import json
import yaml
import argparse
import datetime
import subprocess
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.path_registry import PATHS
from engine.batch_runner import run_batch_from_config

# Default paths and configuration
DEFAULT_OUTPUT_DIR = PATHS.get(
    "CAUSAL_BENCHMARKS_OUTPUT", "forecasts/causal_only_benchmarks"
)
DEFAULT_SCENARIOS_FILE = PATHS.get(
    "CAUSAL_BENCHMARKS_CONFIG", "config/causal_benchmark_scenarios.yaml"
)
DEFAULT_OUTPUT_FILENAME = f"causal_benchmark_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

# Sample benchmark scenarios (hardcoded for initial implementation)
# These could be moved to a configuration file in the future
DEFAULT_SCENARIOS = [
    {
        "name": "baseline_1turn",
        "description": "Baseline scenario with 1 turn simulation",
        "configs": [
            {"state_overrides": {"hope": 0.6, "despair": 0.2}, "turns": 1},
            {"state_overrides": {"hope": 0.3, "despair": 0.5}, "turns": 1},
        ],
    },
    {
        "name": "extended_3turn",
        "description": "Extended scenario with 3 turn simulation",
        "configs": [
            {"state_overrides": {"hope": 0.6, "despair": 0.2}, "turns": 3},
            {"state_overrides": {"hope": 0.3, "despair": 0.5}, "turns": 3},
        ],
    },
    {
        "name": "high_volatility",
        "description": "High volatility scenario with extreme values",
        "configs": [
            {"state_overrides": {"hope": 0.9, "despair": 0.1}, "turns": 2},
            {"state_overrides": {"hope": 0.1, "despair": 0.9}, "turns": 2},
        ],
    },
]


def load_scenarios_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load benchmark scenarios from a YAML or JSON configuration file.

    Args:
        file_path: Path to the configuration file

    Returns:
        List of scenario configurations
    """
    if not os.path.exists(file_path):
        print(
            f"Warning: Scenarios file {file_path} not found. Using default scenarios."
        )
        return DEFAULT_SCENARIOS

    try:
        with open(file_path, "r") as f:
            if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                scenarios = yaml.safe_load(f)
            else:
                scenarios = json.load(f)
        return scenarios
    except Exception as e:
        print(f"Error loading scenarios from {file_path}: {e}")
        print("Using default scenarios instead.")
        return DEFAULT_SCENARIOS


def run_scenario_programmatically(
    scenario: Dict[str, Any], output_path: str
) -> Dict[str, Any]:
    """
    Run a benchmark scenario by directly calling the Python functions.

    Args:
        scenario: Scenario configuration
        output_path: Path to save the results

    Returns:
        Dictionary containing benchmark results
    """
    scenario_name = scenario.get("name", "unnamed_scenario")
    configs = scenario.get("configs", [])

    print(f"Running scenario '{scenario_name}' programmatically...")

    # Create a unique output path for this scenario
    scenario_output = f"{output_path.rstrip('.jsonl')}_{scenario_name}.jsonl"

    try:
        # Run the batch with gravity disabled
        results = run_batch_from_config(
            configs=configs,
            export_path=scenario_output,
            gravity_enabled=False,  # Disable gravity for causal-only benchmarking
        )

        # Calculate metrics from results
        metrics = calculate_metrics(results, scenario)

        return {
            "scenario": scenario,
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": metrics,
            "result_count": len(results),
            "output_path": scenario_output,
        }
    except Exception as e:
        print(f"Error running scenario '{scenario_name}': {e}")
        return {
            "scenario": scenario,
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e),
            "output_path": scenario_output,
        }


def run_scenario_subprocess(
    scenario: Dict[str, Any], output_path: str
) -> Dict[str, Any]:
    """
    Run a benchmark scenario by spawning a subprocess that calls batch_runner.py.

    Args:
        scenario: Scenario configuration
        output_path: Path to save the results

    Returns:
        Dictionary containing benchmark results
    """
    scenario_name = scenario.get("name", "unnamed_scenario")
    configs = scenario.get("configs", [])

    print(f"Running scenario '{scenario_name}' via subprocess...")

    # Create a temporary config file for this scenario
    temp_config_path = f"temp_benchmark_config_{scenario_name}.json"
    with open(temp_config_path, "w") as f:
        json.dump(configs, f)

    # Create a unique output path for this scenario
    scenario_output = f"{output_path.rstrip('.jsonl')}_{scenario_name}.jsonl"

    try:
        # Run batch_runner.py with gravity-off flag via subprocess
        cmd = [
            sys.executable,
            "simulation_engine/batch_runner.py",
            "--gravity-off",
            f"--config={temp_config_path}",
            f"--output={scenario_output}",
        ]

        process = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Load the results to calculate metrics
        results = []
        if os.path.exists(scenario_output):
            with open(scenario_output, "r") as f:
                for line in f:
                    results.append(json.loads(line))

        # Calculate metrics from results
        metrics = calculate_metrics(results, scenario)

        # Remove temporary config file
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

        return {
            "scenario": scenario,
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": metrics,
            "stdout": process.stdout,
            "stderr": process.stderr,
            "result_count": len(results),
            "output_path": scenario_output,
        }
    except subprocess.CalledProcessError as e:
        print(f"Error running scenario '{scenario_name}' subprocess: {e}")
        # Remove temporary config file
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        return {
            "scenario": scenario,
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr,
            "output_path": scenario_output,
        }
    except Exception as e:
        print(f"Error running scenario '{scenario_name}': {e}")
        # Remove temporary config file
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        return {
            "scenario": scenario,
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e),
            "output_path": scenario_output,
        }


def calculate_metrics(
    results: List[Dict[str, Any]], scenario: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate benchmark metrics from the simulation results.

    Args:
        results: List of simulation results
        scenario: Scenario configuration

    Returns:
        Dictionary containing calculated metrics
    """
    # Initialize metrics
    metrics = {
        "accuracy": {"overall": 0.0, "by_variable": {}},
        "drift": {"overall": 0.0, "by_variable": {}},
        "forecast_count": len(results),
        "summary": {},
    }

    if not results:
        return metrics

    # Extract forecasts from results
    forecasts = []
    for result in results:
        forecast_data = result.get("forecasts", [])
        if isinstance(forecast_data, dict):
            forecast_data = [forecast_data]
        forecasts.extend(forecast_data)

    # Calculate average metrics
    if forecasts:
        # Calculate overall forecast accuracy
        accuracies = [f.get("accuracy", 0.0) for f in forecasts if "accuracy" in f]
        if accuracies:
            metrics["accuracy"]["overall"] = sum(accuracies) / len(accuracies)

        # Calculate variable-specific metrics
        all_variables = set()
        for forecast in forecasts:
            variables = forecast.get("variables", {})
            if isinstance(variables, dict):
                all_variables.update(variables.keys())

        # Calculate per-variable metrics
        for var in all_variables:
            var_accuracies = [
                f.get("variables", {}).get(var, {}).get("accuracy", 0.0)
                for f in forecasts
                if var in f.get("variables", {})
            ]

            var_drifts = [
                f.get("variables", {}).get(var, {}).get("drift", 0.0)
                for f in forecasts
                if var in f.get("variables", {})
            ]

            if var_accuracies:
                metrics["accuracy"]["by_variable"][var] = sum(var_accuracies) / len(
                    var_accuracies
                )

            if var_drifts:
                metrics["drift"]["by_variable"][var] = sum(var_drifts) / len(var_drifts)

        # Calculate overall drift
        drifts = [f.get("drift", 0.0) for f in forecasts if "drift" in f]
        if drifts:
            metrics["drift"]["overall"] = sum(drifts) / len(drifts)

    # Add summary statistics for easier reporting
    metrics["summary"] = {
        "overall_accuracy": metrics["accuracy"]["overall"],
        "overall_drift": metrics["drift"]["overall"],
        "variable_count": len(metrics["accuracy"]["by_variable"]),
        "best_variable": max(
            metrics["accuracy"]["by_variable"].items(), key=lambda x: x[1]
        )[0]
        if metrics["accuracy"]["by_variable"]
        else None,
        "worst_variable": min(
            metrics["accuracy"]["by_variable"].items(), key=lambda x: x[1]
        )[0]
        if metrics["accuracy"]["by_variable"]
        else None,
    }

    return metrics


def run_causal_benchmarks(
    scenarios: List[Dict[str, Any]],
    output_dir: str,
    output_file: str,
    method: str = "programmatic",
) -> None:
    """
    Run all benchmark scenarios and save the results.

    Args:
        scenarios: List of scenario configurations
        output_dir: Directory to save results
        output_file: Filename for the summary results
        method: Method to run the scenarios ("programmatic" or "subprocess")
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Full path for the output file
    output_path = os.path.join(output_dir, output_file)

    all_results = []

    print(f"Running {len(scenarios)} causal benchmark scenarios...")

    for i, scenario in enumerate(scenarios):
        print(f"Scenario {i + 1}/{len(scenarios)}: {scenario.get('name', 'unnamed')}")

        if method == "subprocess":
            result = run_scenario_subprocess(scenario, output_path)
        else:  # programmatic is the default
            result = run_scenario_programmatically(scenario, output_path)

        all_results.append(result)

        # Write each result immediately in case of future errors
        with open(output_path, "a") as f:
            f.write(json.dumps(result) + "\n")

        print(f"Completed scenario {i + 1}: {scenario.get('name', 'unnamed')}")

    print(f"All benchmarks completed. Results saved to {output_path}")

    # Generate a summary report
    summary_path = os.path.join(output_dir, f"summary_{os.path.basename(output_file)}")
    with open(summary_path, "w") as f:
        summary = {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_scenarios": len(scenarios),
            "successful_scenarios": sum(1 for r in all_results if "error" not in r),
            "failed_scenarios": sum(1 for r in all_results if "error" in r),
            "scenario_summaries": [
                {
                    "name": r["scenario"].get("name", "unnamed"),
                    "success": "error" not in r,
                    "metrics": r.get("metrics", {}).get("summary", {})
                    if "metrics" in r
                    else {},
                }
                for r in all_results
            ],
        }
        json.dump(summary, f, indent=2)

    print(f"Summary report saved to {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run causal-only benchmarks with gravity disabled"
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_SCENARIOS_FILE,
        help=f"Path to benchmark scenarios configuration file (default: {DEFAULT_SCENARIOS_FILE})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_FILENAME,
        help=f"Output filename for benchmark results (default: {DEFAULT_OUTPUT_FILENAME})",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to store benchmark results (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--method",
        choices=["programmatic", "subprocess"],
        default="programmatic",
        help="Method to run benchmarks (programmatic or subprocess) (default: programmatic)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible benchmarks (default: None)",
    )

    args = parser.parse_args()

    # Set random seed if specified
    if args.seed is not None:
        import random
        import numpy as np

        random.seed(args.seed)
        np.random.seed(args.seed)

    # Load scenarios from file or use defaults
    if os.path.exists(args.config):
        scenarios = load_scenarios_from_file(args.config)
    else:
        print(f"Scenarios file not found: {args.config}")
        print("Using default benchmark scenarios")
        scenarios = DEFAULT_SCENARIOS

    # Run benchmarks
    run_causal_benchmarks(scenarios, args.output_dir, args.output, args.method)


if __name__ == "__main__":
    main()
