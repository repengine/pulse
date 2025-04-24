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

Usage:
    python pulse_ui_shell.py --mode [run|test|suite|batch|view|hook] [options]
    python pulse_ui_shell.py --help_hooks

Options:
    --mode         Choose a mode: run, test, suite, batch, view, or hook name
    --turns        Number of simulation turns
    --domain       Forecast domain (capital, sports, etc.)
    --top          Forecasts to show in view mode
    --quiet        Suppress logs
    --count        Forecasts to generate (batch mode)
    --help_hooks   List all active CLI hooks

"""
import argparse
import json
import os
import importlib
from typing import Any
from simulation_engine.turn_engine import run_turn
from simulation_engine.worldstate import WorldState
from simulation_engine.utils.worldstate_io import load_worldstate_from_file as load_worldstate, save_worldstate_to_file as save_worldstate
from core.variable_registry import validate_variables
from dev_tools.rule_dev_shell import test_rules
from forecast_engine.forecast_log_viewer import load_and_display_forecasts
from dev_tools.pulse_test_suite import test_symbolic_shift, test_capital_shift
from dev_tools.pulse_forecast_test_suite import run_forecast_validation
from forecast_engine.forecast_batch_runner import run_batch_forecasts
from utils.log_utils import get_logger
from core.path_registry import PATHS
from core.pulse_config import MODULES_ENABLED
from core.variable_registry import VARIABLE_REGISTRY
from learning.learning import retrospective_analysis_batch
from trust_system.trust_engine import TrustEngine
import core.pulse_config

logger = get_logger(__name__)

HOOKS_JSON = PATHS.get("HOOKS_JSON", "dev_tools/pulse_hooks_config.json")
hook_data = {"active_hooks": {}, "metadata": {}}
if os.path.exists(HOOKS_JSON):
    with open(HOOKS_JSON, "r", encoding="utf-8") as f:
        hook_data = json.load(f)

# --- Utility: List all available simulation domains ---
def list_domains() -> None:
    """Print all available simulation domains and their descriptions."""
    if hasattr(VARIABLE_REGISTRY, 'DOMAINS'):
        print("Available domains:")
        for d, meta in VARIABLE_REGISTRY.DOMAINS.items():
            desc = meta.get("description", "")
            print(f"  {d:<12} {desc}")
    else:
        print("Domain registry not found.")

def safe_hook_import(hook_name: str) -> None:
    """Safely import and run a CLI hook module by name."""
    try:
        mod = importlib.import_module(hook_name)
        if hasattr(mod, "main"):
            mod.main()
        else:
            logger.warning(f"⚠️ Module '{hook_name}' found but no main() function.")
    except Exception as e:
        logger.error(f"⚠️ Failed to execute hook '{hook_name}': {e}")

def print_active_hooks() -> None:
    """Print all active CLI hooks with labels."""
    if hook_data["active_hooks"]:
        print("\n🧩 Available CLI Hooks:")
        for hook, enabled in hook_data["active_hooks"].items():
            if enabled:
                label = hook_data["metadata"].get(hook, {}).get("label", "hooked module")
                print(f"  --{hook:<24} {label}")

# --- Error handling for worldstate file loading ---
def try_load_worldstate(path: str) -> Any:
    try:
        return load_worldstate(path)
    except Exception as e:
        logger.error(f"Failed to load worldstate from {path}: {e}")
        print(f"❌ Failed to load worldstate from {path}: {e}")
        return None

def compress_forecasts(forecasts, top_k=10):
    """
    Return the top_k most confident forecasts (after trust filtering).
    """
    return sorted(forecasts, key=lambda f: f.get("confidence", 0), reverse=True)[:top_k]

def toggle_symbolic_overlays():
    core.pulse_config.USE_SYMBOLIC_OVERLAYS = not core.pulse_config.USE_SYMBOLIC_OVERLAYS
    print(f"Symbolic overlays now set to: {core.pulse_config.USE_SYMBOLIC_OVERLAYS}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Pulse CLI Shell")
    parser.add_argument("--mode", type=str, default="run", help="Choose a mode: run, test, suite, batch, view, or hook name")
    parser.add_argument("--turns", type=int, default=1, help="Number of simulation turns")
    parser.add_argument("--domain", type=str, help="Forecast domain (capital, sports, etc.)")
    parser.add_argument("--top", type=int, default=5, help="Forecasts to show in view mode")
    parser.add_argument("--quiet", action="store_true", help="Suppress logs")
    parser.add_argument("--count", type=int, default=5, help="Forecasts to generate (batch mode)")
    parser.add_argument("--help_hooks", action="store_true", help="List all active CLI hooks")
    parser.add_argument("--list_domains", action="store_true", help="List all available simulation domains")
    parser.add_argument("--help", action="store_true", help="Show help for all available UI commands")
    parser.add_argument("--promote-memory", action="store_true", help="Export certified forecasts to core memory")

    # Retrodiction/trust CLI options
    parser.add_argument("--retrodict", type=str, help="Path to forecasts (.jsonl) for retrodiction scoring")
    parser.add_argument("--state", type=str, help="Path to current_state.json")
    parser.add_argument("--retrodict-output", type=str, default="retrodicted_output.jsonl", help="Where to save retrodicted forecasts")
    parser.add_argument("--retrodict-threshold", type=float, default=1.5, help="Threshold for flagging symbolic misalignment")
    parser.add_argument("--filter-trusted", action="store_true", help="Output only \U0001F7E2 Trusted forecasts")
    parser.add_argument("--trust-summary", action="store_true", help="Print trust audit summary to CLI")
    parser.add_argument("--compress-topk", type=int, default=None, help="If set, compress to top-K most confident forecasts")
    parser.add_argument("--enforce-license", action="store_true", help="Only retain or export licensed forecasts")
    parser.add_argument("--trust-only", action="store_true", help="Only save/export licensed forecasts")

    # Dynamically add hook args
    for hook, active in hook_data["active_hooks"].items():
        if active:
            label = hook_data["metadata"].get(hook, {}).get("label", "hooked module")
            category = hook_data["metadata"].get(hook, {}).get("category", "tool")
            parser.add_argument(f"--{hook}", action="store_true", help=f"[{category}] {label}")

    args = parser.parse_args()

    if args.help:
        parser.print_help()
        return

    # --- Retrodiction/Trust pipeline ---
    if args.retrodict and args.state:
        try:
            print("\U0001F501 Loading forecast batch and current state...")
            with open(args.retrodict, "r") as f:
                forecasts = [json.loads(line.strip()) for line in f if line.strip()]
            with open(args.state, "r") as f:
                current_state = json.load(f)

            # Retrodiction scoring
            scored = retrospective_analysis_batch(forecasts, current_state, threshold=args.retrodict_threshold)

            # Trust tagging/scoring/gating
            TrustEngine.apply_all(scored, current_state=current_state)

            # Optional: filter only trusted
            if args.filter_trusted:
                scored = [f for f in scored if f.get("trust_label") == "\U0001F7E2 Trusted"]

            # Optional: trust audit summary
            if args.trust_summary:
                summary = TrustEngine.run_trust_audit(scored)
                print("\n\U0001F4CA Trust Audit Summary:")
                print(json.dumps(summary, indent=2))

            # Optional: compression
            if args.compress_topk:
                scored = compress_forecasts(scored, top_k=args.compress_topk)

            # Enforce license filter if requested
            if args.enforce_license:
                from trust_system.license_enforcer import annotate_forecasts, filter_licensed
                scored = annotate_forecasts(scored)
                scored = filter_licensed(scored)

            # After forecasts are loaded:
            if args.promote_memory:
                from forecast_output.forecast_memory_promoter import select_promotable_forecasts, export_promoted
                selected = select_promotable_forecasts(scored)
                export_promoted(selected)

            # Write output
            with open(args.retrodict_output, "w") as f:
                for fc in scored:
                    f.write(json.dumps(fc) + "\n")

            print(f"\u2705 Retrodiction + trust tagging complete. Output saved to {args.retrodict_output}")
        except Exception as e:
            print(f"\u274C Error during retrodiction pipeline: {e}")
        return

    # Print available domains if requested
    if getattr(args, "list_domains", False):
        list_domains()
        return

    if args.help_hooks:
        print_active_hooks()
        return

    # Input validation for turns and count
    if args.turns < 1:
        print("⚠️ Number of simulation turns must be positive.")
        return
    if args.count < 1:
        print("⚠️ Batch count must be positive.")
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
        run_batch_forecasts(
            count=args.count,
            domain=args.domain or "capital",
            enforce_license=args.trust_only
        )
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
    state = try_load_worldstate(input_path)
    if state is None:
        return

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
    try:
        save_worldstate(state, output_path)
        print("✅ Simulation complete.")
    except Exception as e:
        logger.error(f"Failed to save worldstate: {e}")
        print(f"❌ Failed to save worldstate: {e}")

if __name__ == "__main__":
    main()