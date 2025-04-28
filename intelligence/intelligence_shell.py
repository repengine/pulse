# pulse/intelligence/intelligence_shell.py

"""
Pulse Intelligence Shell

Interactive command-line interface for managing Pulse Intelligence Core.
Allows running standard forecasts, retrodictions, and dynamic module/function execution.

Author: Pulse Development Team
Version: 0.41
"""

import json
from intelligence.intelligence_core import IntelligenceCore
from intelligence.function_router import FunctionRouter

class IntelligenceShell:
    def __init__(self):
        self.core = IntelligenceCore()
        self.core.load_standard_modules()
        self.router = self.core.router
        print("[PulseShell] ✅ Intelligence Core initialized.")

    def run(self):
        """Main command loop."""
        while True:
            try:
                command = input("[Pulse> ] ").strip()
                if not command:
                    continue
                if command == "exit":
                    print("[PulseShell] 👋 Exiting...")
                    break
                self.parse_command(command)
            except Exception as e:
                print(f"[PulseShell] ❌ Error: {e}")

    def parse_command(self, command: str) -> None:
        """Parse and dispatch user command."""
        parts = command.split()
        cmd = parts[0]

        def list_modules():
            self.core.list_modules()

        def list_functions():
            if len(parts) < 2:
                print("[PulseShell] ❗ Usage: list-functions <module>")
                return
            module_key = parts[1]
            self.core.available_functions(module_key)

        def forecast():
            start_year = int(parts[1]) if len(parts) > 1 else 2023
            turns = int(parts[2]) if len(parts) > 2 else 52
            snapshot = self.core.run_standard_forecast(start_year=start_year, turns=turns)
            print("[PulseShell] 📈 Forecast snapshot:", snapshot)

        def retrodict():
            start_date = parts[1] if len(parts) > 1 else "2017-01-01"
            days = int(parts[2]) if len(parts) > 2 else 30
            self.core.run_retrodiction_forecast(start_date=start_date, days=days)

        def load_module():
            if len(parts) < 2:
                print("[PulseShell] ❗ Usage: load-module <import_path> [alias]")
                return
            import_path = parts[1]
            alias = parts[2] if len(parts) > 2 else None
            self.router.load_module(import_path, alias=alias)
            print(f"[PulseShell] ✅ Loaded module {import_path} as {alias or import_path}")

        def run_function():
            if len(parts) < 3:
                print("[PulseShell] ❗ Usage: run-function <module> <function> [args as JSON]")
                return
            module_key = parts[1]
            function_name = parts[2]
            args_json = parts[3] if len(parts) > 3 else "{}"
            try:
                args = json.loads(args_json)
                if not isinstance(args, dict):
                    raise ValueError("Arguments must be a JSON object.")
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON for arguments.")
            result = self.router.run_function(module_key, function_name, **args)
            print(f"[PulseShell] 🔄 Function result: {result}")

        commands = {
            "list-modules": list_modules,
            "list-functions": list_functions,
            "forecast": forecast,
            "retrodict": retrodict,
            "load-module": load_module,
            "run-function": run_function,
        }

        if cmd in commands:
            commands[cmd]()
        else:
            print(f"[PulseShell] ❓ Unknown command: {cmd}")

if __name__ == "__main__":
    shell = IntelligenceShell()
    shell.run()
