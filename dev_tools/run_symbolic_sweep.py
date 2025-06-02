# dev_tools/run_symbolic_sweep.py

from analytics.symbolic_sweep_scheduler import run_sweep_now, summarize_sweep_log
import argparse

parser = argparse.ArgumentParser(description="Pulse Symbolic Sweep CLI")
parser.add_argument("--summary", action="store_true", help="Show sweep history summary")
parser.add_argument("--now", action="store_true", help="Run sweep immediately")
args = parser.parse_args()

if args.now:
    run_sweep_now()

if args.summary:
    summarize_sweep_log()
