# pulse/intelligence/intelligence_shell.py

"""
Pulse Intelligence Shell

Command-line interface for managing Pulse Intelligence Core with verb-based subcommands.
Author: Pulse Development Team
Version: 0.42
"""

import sys
import json
import argparse
from intelligence.intelligence_core import IntelligenceCore
from intelligence.function_router import FunctionRouter

class IntelligenceShell:
    verbs = {"forecast", "compress", "retrodict", "train-gpt", "status", "exit"}

    def __init__(self):
        self.core = IntelligenceCore()
        self.core.load_standard_modules()
        self.router = self.core.router

    def run_cli(self):
        parser = argparse.ArgumentParser(prog="pulse")
        subparsers = parser.add_subparsers(dest="verb", required=True, help="Available verbs")
        # forecast verb
        forecast_parser = subparsers.add_parser("forecast", help="Run forecast cycle")
        forecast_parser.add_argument("--start-year", type=int, default=2023, help="Starting year for forecast")
        forecast_parser.add_argument("--turns", type=int, default=52, help="Number of turns to forecast")
        forecast_parser.add_argument("--args", type=str, help="Override arguments as JSON object")
        # compress verb
        compress_parser = subparsers.add_parser("compress", help="Compress forecasts")
        compress_parser.add_argument("--input-file", required=True, help="Path to input forecasts file")
        compress_parser.add_argument("--output-file", required=True, help="Path to output compressed file")
        compress_parser.add_argument("--args", type=str, help="Override arguments as JSON object")
        # retrodict verb
        retrodict_parser = subparsers.add_parser("retrodict", help="Run retrodiction cycle")
        retrodict_parser.add_argument("--start-date", type=str, default="2017-01-01", help="Start date for retrodiction (YYYY-MM-DD)")
        retrodict_parser.add_argument("--days", type=int, default=30, help="Number of days to retrodict")
        retrodict_parser.add_argument("--args", type=str, help="Override arguments as JSON object")
        # train-gpt verb
        train_parser = subparsers.add_parser("train-gpt", help="Run GPT training cycle")
        train_parser.add_argument("--dataset-path", type=str, required=True, help="Path to training dataset")
        train_parser.add_argument("--epochs", type=int, default=1, help="Number of training epochs")
        train_parser.add_argument("--args", type=str, help="Override arguments as JSON object")
        # status verb
        status_parser = subparsers.add_parser("status", help="Generate status report")
        status_parser.add_argument("--args", type=str, help="Override arguments as JSON object")
        # exit verb
        subparsers.add_parser("exit", help="Exit the shell")

        args = parser.parse_args()

        # Build kwargs from explicit flags
        kwargs = {}
        for key, value in vars(args).items():
            if key in ("verb", "args") or value is None:
                continue
            kwargs[key] = value

        # Override with --args JSON if provided
        if getattr(args, "args", None):
            try:
                override = json.loads(args.args)
                if not isinstance(override, dict):
                    raise ValueError("Override --args JSON must be an object")
                kwargs.update(override)
            except Exception as e:
                error = {"error": f"Invalid --args JSON: {e}"}
                print(json.dumps(error))
                sys.exit(1)

        verb = args.verb
        if verb == "exit":
            sys.exit(0)

        try:
            result = self.router.run_function(verb, **kwargs)
            print(json.dumps({"result": result}))
            sys.exit(0)
        except Exception as e:
            error = {"error": str(e)}
            print(json.dumps(error))
            sys.exit(1)

if __name__ == "__main__":
    IntelligenceShell().run_cli()
