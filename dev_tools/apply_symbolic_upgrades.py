# tools/apply_symbolic_upgrades.py

from symbolic.symbolic_executor import rewrite_forecast_symbolics, log_symbolic_mutation
import argparse, json

parser = argparse.ArgumentParser()
parser.add_argument("--batch", required=True)
parser.add_argument("--plan", required=True)
parser.add_argument("--out", default="revised_forecasts.jsonl")

args = parser.parse_args()

with open(args.batch, "r") as f:
    forecasts = [json.loads(line) for line in f if line.strip()]

with open(args.plan, "r") as f:
    upgrade = json.load(f)

rewritten = rewrite_forecast_symbolics(forecasts, upgrade)

with open(args.out, "w") as f:
    for fc in rewritten:
        f.write(json.dumps(fc) + "\n")
        log_symbolic_mutation(fc)
