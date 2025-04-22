# tools/generate_symbolic_upgrade_plan.py

from symbolic.symbolic_upgrade_planner import (
    propose_symbolic_upgrades, export_upgrade_plan
)
from symbolic.pulse_symbolic_learning_loop import learn_from_tuning_log, generate_learning_profile
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--log", required=True, help="Tuning result log")
args = parser.parse_args()

results = learn_from_tuning_log(args.log)
profile = generate_learning_profile(results)
plan = propose_symbolic_upgrades(profile)
export_upgrade_plan(plan)
