# simulation_engine.utils.pulse_variable_forecaster.py
"""
Module: pulse_variable_forecaster.py
Purpose: Forecast future value trajectories of a selected variable using simulated rollouts.
Supports Monte Carlo projection for symbolic or capital variables over multiple horizons.

Author: Pulse AI Engine
Version: v0.5.0
"""

import argparse
import json
import os
import matplotlib.pyplot as plt
from statistics import mean
from typing import List, Dict

from simulation_engine.turn_engine import run_turn
from simulation_engine.worldstate import WorldState


def simulate_forward(variable: str, steps: int, runs: int = 10) -> Dict[str, List[float]]:
    """
    Simulate multiple futures and return the trajectory of the given variable.

    Parameters:
        variable (str): variable name to track
        steps (int): number of simulation steps to simulate
        runs (int): how many forward runs to simulate

    Returns:
        Dict with keys:
            - "trajectories": list of lists (each run's value over time)
            - "average": mean value per step
    """
    trajectories = []
    for r in range(runs):
        state = WorldState()
        run = []
        for _ in range(steps):
            run_turn(state)
            val = state.variables.get(variable, None)
            run.append(val)
        trajectories.append(run)

    # Calculate average per step
    avg = [mean([run[i] for run in trajectories if run[i] is not None]) for i in range(steps)]
    return {"trajectories": trajectories, "average": avg}


def plot_forecast(avg: List[float], all_runs: List[List[float]], var_name: str, export: str = None):
    plt.figure(figsize=(10, 5))
    for run in all_runs:
        plt.plot(run, color="gray", alpha=0.3)
    plt.plot(avg, color="blue", linewidth=2, label="Mean Forecast")
    plt.title(f"Projected Future: {var_name}")
    plt.xlabel("Step")
    plt.ylabel(var_name)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    if export:
        plt.savefig(export)
        print(f"📤 Forecast plot saved to {export}")
    else:
        plt.show()


def save_forecast_data(path: str, results: Dict[str, List[float]], var_name: str):
    with open(path, "w") as f:
        json.dump({"variable": var_name, **results}, f, indent=2)
    print(f"✅ Forecast data saved to {path}")


def main():
    parser = argparse.ArgumentParser(description="Pulse Variable Forecaster")
    parser.add_argument("--var", type=str, required=True, help="Variable name to forecast")
    parser.add_argument("--horizon", type=int, default=12, help="Steps into the future to simulate")
    parser.add_argument("--runs", type=int, default=10, help="Number of simulation runs")
    parser.add_argument("--export-data", type=str, help="Optional path to save raw forecast data (.json)")
    parser.add_argument("--export-plot", type=str, help="Optional path to save forecast plot image (.png)")
    args = parser.parse_args()

    results = simulate_forward(args.var, args.horizon, args.runs)
    plot_forecast(results["average"], results["trajectories"], args.var, export=args.export_plot)

    if args.export_data:
        save_forecast_data(args.export_data, results, var_name=args.var)


if __name__ == "__main__":
    main()
