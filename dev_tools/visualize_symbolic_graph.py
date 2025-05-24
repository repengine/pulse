# tools/visualize_symbolic_graph.py

from symbolic_system.symbolic_transition_graph import (
    build_symbolic_graph,
    visualize_symbolic_graph,
)
import argparse
import json


def load_forecasts(path):
    with open(path, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]


parser = argparse.ArgumentParser()
parser.add_argument("--batch", required=True)
args = parser.parse_args()

forecasts = load_forecasts(args.batch)
G = build_symbolic_graph(forecasts)
visualize_symbolic_graph(G)
