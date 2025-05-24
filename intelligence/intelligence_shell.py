# pulse/intelligence/intelligence_shell.py

"""
Pulse Intelligence Shell

Command-line interface for managing Pulse Intelligence Core with verb-based subcommands.
Provides a command-line interface to interact with the Pulse Intelligence Core,
allowing users to trigger simulations, training, and status reports via verbs.

Author: Pulse Development Team
Version: 0.42
"""

import sys
import json
import argparse
from typing import Any, Dict, List, Set
from intelligence.intelligence_core import IntelligenceCore
from intelligence.function_router import FunctionRouter
from intelligence.simulation_executor import SimulationExecutor
from intelligence.intelligence_observer import Observer
from intelligence.upgrade_sandbox_manager import UpgradeSandboxManager


class IntelligenceShell:
    """
    Command-line interface for interacting with the Pulse Intelligence Core.
    """

    verbs: Set[str] = {
        "forecast",
        "compress",
        "retrodict",
        "train-gpt",
        "status",
        "exit",
    }

    def __init__(self) -> None:
        """
        Initializes the IntelligenceShell with injected dependencies for IntelligenceCore.
        """
        # Instantiate dependencies
        self.router: FunctionRouter = FunctionRouter()
        self.executor: SimulationExecutor = SimulationExecutor(self.router)
        self.observer: Observer = Observer()
        self.sandbox: UpgradeSandboxManager = UpgradeSandboxManager()

        # Inject dependencies into IntelligenceCore
        self.core: IntelligenceCore = IntelligenceCore(
            router=self.router,
            executor=self.executor,
            observer=self.observer,
            sandbox=self.sandbox,
        )
        self.core.load_standard_modules()

    def run_cli(self) -> None:
        """
        Runs the command-line interface, parsing arguments and executing the
        corresponding intelligence core function.
        """
        parser = argparse.ArgumentParser(prog="pulse")
        subparsers = parser.add_subparsers(
            dest="verb", required=True, help="Available verbs"
        )

        # forecast verb
        forecast_parser: argparse.ArgumentParser = subparsers.add_parser(
            "forecast", help="Run forecast cycle"
        )
        forecast_parser.add_argument(
            "--start-year", type=int, default=2023, help="Starting year for forecast"
        )
        forecast_parser.add_argument(
            "--turns", type=int, default=52, help="Number of turns to forecast"
        )
        forecast_parser.add_argument(
            "--args", type=str, help="Override arguments as JSON object"
        )

        # compress verb
        compress_parser: argparse.ArgumentParser = subparsers.add_parser(
            "compress", help="Compress forecasts"
        )
        compress_parser.add_argument(
            "--input-file", required=True, help="Path to input forecasts file"
        )
        compress_parser.add_argument(
            "--output-file", required=True, help="Path to output compressed file"
        )
        compress_parser.add_argument(
            "--args", type=str, help="Override arguments as JSON object"
        )

        # retrodict verb
        retrodict_parser: argparse.ArgumentParser = subparsers.add_parser(
            "retrodict", help="Run retrodiction cycle"
        )
        retrodict_parser.add_argument(
            "--start-date",
            type=str,
            default="2017-01-01",
            help="Start date for retrodiction (YYYY-MM-DD)",
        )
        retrodict_parser.add_argument(
            "--days", type=int, default=30, help="Number of days to retrodict"
        )
        retrodict_parser.add_argument(
            "--args", type=str, help="Override arguments as JSON object"
        )

        # train-gpt verb
        train_parser: argparse.ArgumentParser = subparsers.add_parser(
            "train-gpt", help="Run GPT training cycle"
        )
        train_parser.add_argument(
            "--dataset-path", type=str, required=True, help="Path to training dataset"
        )
        train_parser.add_argument(
            "--epochs", type=int, default=1, help="Number of training epochs"
        )
        train_parser.add_argument(
            "--args", type=str, help="Override arguments as JSON object"
        )

        # status verb
        status_parser: argparse.ArgumentParser = subparsers.add_parser(
            "status", help="Generate status report"
        )
        status_parser.add_argument(
            "--args", type=str, help="Override arguments as JSON object"
        )

        # exit verb
        subparsers.add_parser("exit", help="Exit the shell")

        args: argparse.Namespace = parser.parse_args()

        # Build kwargs from explicit flags
        kwargs: Dict[str, Any] = {}
        for key, value in vars(args).items():
            if key in ("verb", "args") or value is None:
                continue
            kwargs[key] = value

        # Override with --args JSON if provided
        if args.args:
            try:
                override: Dict[str, Any] = json.loads(args.args)
                if not isinstance(override, dict):
                    raise ValueError("Override --args JSON must be an object")
                kwargs.update(override)
            except Exception as e:
                error: Dict[str, str] = {"error": f"Invalid --args JSON: {e}"}
                print(json.dumps(error))
                sys.exit(1)

        verb: str = args.verb
        if verb == "exit":
            sys.exit(0)

        try:
            result: Any = self.router.run_function(verb, **kwargs)
            print(json.dumps({"result": result}))

            # After running a forecast, observe the divergence log
            if verb == "forecast":
                log_path: str = "gpt_forecast_divergence_log.jsonl"
                print(f"[IntelligenceShell] Observing divergence log at {log_path}")
                divergences: List[Dict[str, Any]] = (
                    self.core.observer.observe_simulation_outputs(log_path)
                )
                print(
                    f"[IntelligenceShell] Loaded {len(divergences)} divergence entries."
                )

            sys.exit(0)
        except Exception as e:
            error: Dict[str, str] = {"error": str(e)}
            print(json.dumps(error))
            sys.exit(1)


if __name__ == "__main__":
    IntelligenceShell().run_cli()
