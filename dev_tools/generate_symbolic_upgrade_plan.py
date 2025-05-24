# tools/generate_symbolic_upgrade_plan.py

from symbolic_system.symbolic_upgrade_planner import (
    propose_symbolic_upgrades,
    export_upgrade_plan,
)
from symbolic_system.pulse_symbolic_learning_loop import (
    learn_from_tuning_log,
    generate_learning_profile,
)
import argparse
import os


def generate_symbolic_upgrade_plan(log_path=None):
    """
    Generate a symbolic upgrade plan from a tuning result log.
    Args:
        log_path (str): Path to the tuning result log file.
    Returns:
        dict: The generated symbolic upgrade plan, or None if error.
    """
    if log_path is None:
        raise ValueError("log_path must be provided")
    if not os.path.isfile(log_path):
        print(f"❌ Log file not found: {log_path}")
        return None
    try:
        results = learn_from_tuning_log(log_path)
        profile = generate_learning_profile(results)
        plan = propose_symbolic_upgrades(profile)
        export_upgrade_plan(plan)
        print("✅ Upgrade plan generated and exported.")
        return plan
    except Exception as e:
        print(f"❌ Failed to generate upgrade plan: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate a symbolic upgrade plan from a tuning result log."
    )
    parser.add_argument("--log", required=True, help="Tuning result log")
    args = parser.parse_args()
    generate_symbolic_upgrade_plan(args.log)


if __name__ == "__main__":
    main()
