"""
Module: pulse_interactive_shell.py
Pulse Version: v0.22.2
Last Updated: 2025-04-16
Author: Pulse AI Engine

Description:
Strategist shell for Pulse interaction. Enables symbolic mutation, forecast ops, and module orchestration.

Supports:
  - run-turns [N]
  - set-overlay [name] [value]
  - show-overlays
  - load-worldstate [file]
  - show-forecast
  - compare-drift [file1 file2]
  - help
  - exit

Features:
  - Command registry structure
  - Error-safe CLI loop
  - Overlay memory inspection
  - Stub hooks for external module integration
  - JSONL interaction logging

Log Output: logs/interactive_shell_log.jsonl
"""

import json
import os
from datetime import datetime
from typing import Callable, Dict, List
from utils.log_utils import get_logger
from core.path_registry import PATHS
from core.module_registry import MODULE_REGISTRY
from core.pulse_config import DEFAULT_DECAY_RATE
from core.pulse_config import OVERLAY_NAMES

logger = get_logger(__name__)

INTERACTIVE_LOG_PATH = PATHS.get("INTERACTIVE_LOG_PATH", "logs/interactive_shell_log.jsonl")

# Use overlays from config if available
symbolic_overlays = {name: 0.5 for name in getattr(__import__('core.pulse_config'), 'OVERLAY_NAMES', ["hope", "despair", "rage", "fatigue", "trust"])}

# Ensure log dir exists
def ensure_log_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

# Structured logger
def log_interaction(command: str, result: str):
    ensure_log_dir(INTERACTIVE_LOG_PATH)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "command": command,
        "result": result,
        "metadata": {
            "version": "v0.22.2",
            "source": "pulse_interactive_shell.py"
        }
    }
    try:
        with open(INTERACTIVE_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[LOG ERROR] {e}")

# Command handlers
def cmd_help(args: List[str]):
    print("Pulse CLI Commands:")
    for name in sorted(COMMANDS):
        print(f"  {name:<20} - {COMMANDS[name].__doc__}")
    log_interaction("help", "displayed")

def cmd_show_overlays(args: List[str]):
    """Display current overlay values"""
    for k, v in symbolic_overlays.items():
        print(f"  {k:<8}: {v:.3f}")
    log_interaction("show-overlays", "ok")

def cmd_set_overlay(args: List[str]):
    """Set a symbolic overlay value"""
    if len(args) != 2:
        print("Usage: set-overlay [name] [value]")
        return
    emo, val = args[0], args[1]
    try:
        val = float(val)
        if emo not in symbolic_overlays:
            print(f"Unknown overlay: {emo}")
            log_interaction("set-overlay", "fail")
        else:
            symbolic_overlays[emo] = round(val, 4)
            print(f"{emo} = {val}")
            log_interaction("set-overlay", f"{emo} set to {val}")
    except ValueError:
        print("Invalid numeric value.")
        log_interaction("set-overlay", "error")

def cmd_run_turns(args: List[str]):
    """Run N turns of simulation (stub)"""
    if len(args) != 1 or not args[0].isdigit():
        print("Usage: run-turns [N]")
        return
    print(f"[Stub] Running {args[0]} turns...")
    log_interaction("run-turns", f"{args[0]} turns run")

def cmd_load_worldstate(args: List[str]):
    """Load a saved worldstate (stub)"""
    if not args:
        print("Usage: load-worldstate [file]")
        return
    print(f"[Stub] Loaded worldstate from {args[0]}")
    log_interaction("load-worldstate", f"{args[0]}")

def cmd_show_forecast(args: List[str]):
    """Trigger forecast generation (stub)"""
    print("[Stub] Forecast generated.")
    log_interaction("show-forecast", "run")

def cmd_compare_drift(args: List[str]):
    """Compare drift between two forecast logs"""
    if len(args) != 2:
        print("Usage: compare-drift [file1] [file2]")
        return
    print(f"[Stub] Compared {args[0]} vs {args[1]}")
    log_interaction("compare-drift", f"{args[0]} vs {args[1]}")

def cmd_exit(args: List[str]):
    """Exit the strategist shell"""
    log_interaction("exit", "shutdown")
    raise SystemExit("Goodbye.")

# Command router
COMMANDS: Dict[str, Callable[[List[str]], None]] = {
    "help": cmd_help,
    "exit": cmd_exit,
    "quit": cmd_exit,
    "show-overlays": cmd_show_overlays,
    "set-overlay": cmd_set_overlay,
    "run-turns": cmd_run_turns,
    "load-worldstate": cmd_load_worldstate,
    "show-forecast": cmd_show_forecast,
    "compare-drift": cmd_compare_drift,
}

def run_shell():
    print("🔮 Pulse Strategist Shell v0.22.2")
    print("Type 'help' for commands.")
    while True:
        try:
            raw = input("pulse> ").strip()
            if not raw:
                continue
            tokens = raw.split()
            cmd, args = tokens[0], tokens[1:]
            handler = COMMANDS.get(cmd)
            if handler:
                handler(args)
            else:
                logger.warning("Unknown command. Type 'help' to view options.")
                log_interaction(raw, "unknown")
        except KeyboardInterrupt:
            print("Interrupted. Type 'exit' to quit.")
        except SystemExit as e:
            print(e)
            break
        except Exception as e:
            logger.error(f"[ERROR] {e}")
            log_interaction("shell-error", str(e))

if __name__ == "__main__":
    run_shell()
