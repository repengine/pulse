"""
rule_dev_shell.py

Command-line tool to test individual rule sets, symbolic interactions,
and inspect resulting WorldState overlays or variables.

Author: Pulse v0.10
"""

import argparse
from engine.worldstate import WorldState
from engine.causal_rules import apply_causal_rules
from engine.rule_engine import run_rules
from utils.log_utils import get_logger
from engine.path_registry import PATHS

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

RULE_LOG_PATH = PATHS.get("RULE_LOG_PATH", PATHS["WORLDSTATE_LOG_DIR"])

logger = get_logger(__name__)


def test_rules(verbose=True):
    state = WorldState()
    print("🌐 Initial state:")
    print(state.snapshot())

    apply_causal_rules(state)
    rule_log = run_rules(state, verbose=verbose)

    print("\n🌀 After applying all rules:")
    print(state.snapshot())
    print("\n📜 Rule execution log:")
    for entry in rule_log:
        print(f"- {entry['rule_id']} ({entry['symbolic_tags']})")

    print("\n🗒️ Log trail:")
    for log in state.get_log(20):
        print(f"  • {log}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress skipped rule logs"
    )
    args = parser.parse_args()
    test_rules(verbose=not args.quiet)
