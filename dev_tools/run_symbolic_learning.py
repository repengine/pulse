# tools/run_symbolic_learning.py

from symbolic_system.pulse_symbolic_learning_loop import (
    learn_from_tuning_log,
    generate_learning_profile,
    log_symbolic_learning,
)
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--log", required=True, help="Tuning log path")
args = parser.parse_args()

results = learn_from_tuning_log(args.log)
profile = generate_learning_profile(results)
log_symbolic_learning(profile)
