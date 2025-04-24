"""
Pulse CLI entrypoint: consolidated commands using argparse subcommands.
"""

import argparse
import os
import sys
import json

from simulation_engine.worldstate import WorldState
from src.simulation import simulate_forward, simulate_backward, simulate_counterfactual
from simulation_engine.rule_mutation_engine import apply_rule_mutations
from simulation_engine.batch_runner import run_batch_from_config
from simulation_engine.historical_retrodiction_runner import run_retrodiction_test
from src.ui import interactive_shell, ui_shell, ui_operator

def main():
    parser = argparse.ArgumentParser(prog="pulse", description="Pulse CLI entrypoint")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # simulate subcommand
    sim = subparsers.add_parser("simulate", help="Run simulation: forward, backward, or counterfactual")
    sim.add_argument("--mode", choices=["forward", "backward", "counterfactual"], default="forward")
    sim.add_argument("--turns", type=int, default=5, help="Number of turns for forward/counterfactual simulation")
    sim.add_argument("--steps", type=int, default=1, help="Number of steps for backward simulation")
    sim.add_argument("--decay-rate", type=float, default=0.01, help="Decay rate for backward simulation")
    sim.add_argument("--fork-vars", nargs="*", help="Fork variables for counterfactual (format var=value)")

    # mutate-rules
    subparsers.add_parser("mutate-rules", help="Apply rule mutations to top rules")

    # batch-run
    batch = subparsers.add_parser("batch-run", help="Execute a batch of simulations from config")
    batch.add_argument("config", help="Path to batch JSON config file")
    batch.add_argument("--export-path", help="Output path for saving batch results")

    # retrodict-test
    retro = subparsers.add_parser("retrodict-test", help="Run historical retrodiction test")
    retro.add_argument("start_date", help="Start date YYYY-MM-DD")
    retro.add_argument("--days", type=int, default=30, help="Number of days to simulate")

    # interactive shells
    subparsers.add_parser("interactive", help="Launch interactive shell")
    subparsers.add_parser("ui-shell", help="Launch UI shell")
    subparsers.add_parser("ui-operator", help="Launch UI operator shell")

    args = parser.parse_args()

    if args.command == "simulate":
        ws = WorldState()
        if args.mode == "forward":
            results = simulate_forward(ws, turns=args.turns)
            for r in results:
                print(r)
        elif args.mode == "backward":
            result = simulate_backward(ws, steps=args.steps, decay_rate=args.decay_rate)
            print(result)
        else:  # counterfactual
            fork_vars = {}
            if args.fork_vars:
                for fv in args.fork_vars:
                    key, val = fv.split("=", 1)
                    fork_vars[key] = float(val)
            result = simulate_counterfactual(ws, fork_vars=fork_vars, turns=args.turns)
            print(result)
        return

    if args.command == "mutate-rules":
        apply_rule_mutations()
        return

    if args.command == "batch-run":
        with open(args.config, "r") as f:
            configs = json.load(f)
        results = run_batch_from_config(configs, export_path=args.export_path)
        print(results)
        return

    if args.command == "retrodict-test":
        run_retrodiction_test(args.start_date, days=args.days)
        return

    if args.command == "interactive":
        interactive_shell()
        return

    if args.command == "ui-shell":
        ui_shell()
        return

    if args.command == "ui-operator":
        ui_operator()
        return

if __name__ == "__main__":
    main()