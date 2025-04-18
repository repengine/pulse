""" 
pulse_ui_shell.py

Primary CLI interface for Pulse.
Supports:
- Core simulation
- Forecast replay & visualization
- Batch runners
- Test suites
- Auto-hooked CLI modules from pulse_hooks_config.json

Author: Pulse v0.20
"""

import argparse
import json
import os
import importlib
from simulation_engine.turn_engine import run_turn
from simulation_engine.worldstate import WorldState
from simulation_engine.utils.worldstate_io import load_worldstate_from_file as load_worldstate, save_worldstate_to_file as save_worldstate
from core.variable_registry import validate_variables
from dev_tools.rule_dev_shell import test_rules
from simulation_engine.forecasting.forecast_log_viewer import load_and_display_forecasts
from dev_tools.pulse_test_suite import test_symbolic_shift, test_capital_shift
from dev_tools.pulse_forecast_test_suite import run_forecast_validation
from simulation_engine.forecasting.forecast_batch_runner import run_batch_forecasts
from utils.log_utils import get_logger
from core.path_registry import PATHS
from core.pulse_config import MODULES_ENABLED
from core.variable_registry import VARIABLE_REGISTRY

logger = get_logger(__name__)

HOOKS_JSON = PATHS.get("HOOKS_JSON", "dev_tools/pulse_hooks_config.json")
hook_data = {"active_hooks": {}, "metadata": {}}
if os.path.exists(HOOKS_JSON):
    with open(HOOKS_JSON, "r", encoding="utf-8") as f:
        hook_data = json.load(f)

def safe_hook_import(hook_name):
    try:
        mod = importlib.import_module(hook_name)
        if hasattr(mod, "main"):
            mod.main()
        else:
            logger.warning(f"⚠️ Module '{hook_name}' found but no main() function.")
    except Exception as e:
        logger.error(f"⚠️ Failed to execute hook '{hook_name}': {e}")

def print_active_hooks():
    if hook_data["active_hooks"]:
        print("\n🧩 Available CLI Hooks:")
        for hook, enabled in hook_data["active_hooks"].items():
            if enabled:
                label = hook_data["metadata"].get(hook, {}).get("label", "hooked module")
                print(f"  --{hook:<24} {label}")

def main():
    parser = argparse.ArgumentParser(description="Pulse CLI Shell")
    parser.add_argument("--mode", type=str, default="run", help="Choose a mode: run, test, suite, batch, view, or hook name")
    parser.add_argument("--turns", type=int, default=1, help="Number of simulation turns")
    parser.add_argument("--domain", type=str, help="Forecast domain (capital, sports, etc.)")
    parser.add_argument("--top", type=int, default=5, help="Forecasts to show in view mode")
    parser.add_argument("--quiet", action="store_true", help="Suppress logs")
    parser.add_argument("--count", type=int, default=5, help="Forecasts to generate (batch mode)")
    parser.add_argument("--help_hooks", action="store_true", help="List all active CLI hooks")

    # Dynamically add hook args
    for hook, active in hook_data["active_hooks"].items():
        if active:
            label = hook_data["metadata"].get(hook, {}).get("label", "hooked module")
            category = hook_data["metadata"].get(hook, {}).get("category", "tool")
            parser.add_argument(f"--{hook}", action="store_true", help=f"[{category}] {label}")

    args = parser.parse_args()

    if args.help_hooks:
        print_active_hooks()
        return

    # Hook execution by direct flag
    for hook in hook_data["active_hooks"]:
        if getattr(args, hook, False):
            print(f"🔁 Executing CLI hook: {hook}")
            safe_hook_import(hook)
            return

    # Predefined modes
    if args.mode == "test":
        test_rules(verbose=not args.quiet)
        return

    if args.mode == "suite":
        test_symbolic_shift(turns=args.turns)
        test_capital_shift(turns=args.turns)
        run_forecast_validation()
        return

    if args.mode == "batch":
        run_batch_forecasts(count=args.count, domain=args.domain or "capital")
        return

    if args.mode == "view":
        load_and_display_forecasts(log_dir="forecast_output", top_n=args.top, domain_filter=args.domain)
        return

    # Fallback to hook by name
    if args.mode in hook_data["active_hooks"]:
        print(f"🔁 Executing --mode hook: {args.mode}")
        safe_hook_import(args.mode)
        return

    # --- Expanded: Load, Validate, Run, Save ---
    # Default: simulation
    input_path = PATHS.get("WORLDSTATE_INPUT", "simulation_engine/worldstate_input.json")
    output_path = PATHS.get("WORLDSTATE_OUTPUT", "simulation_engine/worldstate_output.json")
    print(f"🧠 Loading worldstate from {input_path}")
    state = load_worldstate(input_path)

    # Validate worldstate variables
    ESTIMATE_MISSING = MODULES_ENABLED.get("estimate_missing_variables", False)

    valid, missing, unexpected = validate_variables(state.variables)
    if not valid:
        print("⚠️ Invalid WorldState variables.")
        if missing:
            print("Missing variables:", missing)
        if unexpected:
            print("Unexpected variables:", unexpected)

        if ESTIMATE_MISSING:
            print("🧪 Estimating missing variables from defaults.")
            for var in missing:
                default = VARIABLE_REGISTRY[var]["default"]
                state.variables[var] = default
                print(f"  → {var} set to default {default}")
            # Optionally re-validate here
        else:
            return

    for _ in range(args.turns):
        rule_log = run_turn(state)
        print(f"Turn {state.turn} complete. Rules triggered: {len(rule_log)}")

    print("\nFinal snapshot:")
    print(state.snapshot())
    print("\nRecent log:")
    for line in state.get_log():
        print(f" - {line}")

    print(f"\n💾 Saving worldstate to {output_path}")
    save_worldstate(state, output_path)
    print("✅ Simulation complete.")

if __name__ == "__main__":
    main()