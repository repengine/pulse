"""
active_experimentation.py

ActiveExperimentationEngine: Proposes and runs simulation experiments (parameter sweeps, counterfactuals, self-play), logs results to the learning log, and provides a CLI entry point for running experiments.
"""

import random
from datetime import datetime
from core.pulse_learning_log import log_learning_event

class ActiveExperimentationEngine:
    def __init__(self):
        pass

    def run_parameter_sweep(self, param_name, values, simulation_fn):
        results = []
        for v in values:
            result = simulation_fn(**{param_name: v})
            log_learning_event("active_experiment_param_sweep", {
                "param": param_name,
                "value": v,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            results.append((v, result))
        return results

    def run_counterfactual(self, base_state, changes, simulation_fn):
        cf_state = base_state.copy()
        cf_state.update(changes)
        result = simulation_fn(cf_state)
        log_learning_event("active_experiment_counterfactual", {
            "changes": changes,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })
        return result

    def run_self_play(self, simulation_fn, n=5):
        results = []
        for i in range(n):
            result = simulation_fn()
            log_learning_event("active_experiment_self_play", {
                "iteration": i,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            results.append(result)
        return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Active Experimentation CLI")
    parser.add_argument("--sweep", nargs=2, metavar=("param", "values"), help="Run parameter sweep: param 'v1,v2,v3'")
    parser.add_argument("--counterfactual", nargs=2, metavar=("base_state", "changes"), help="Run counterfactual: base_state changes_json")
    parser.add_argument("--self-play", type=int, default=0, help="Run N self-play simulations")
    args = parser.parse_args()
    engine = ActiveExperimentationEngine()
    def dummy_simulation_fn(**kwargs):
        return {"output": random.random(), "params": kwargs}
    if args.sweep:
        param, values = args.sweep
        values = values.split(",")
        results = engine.run_parameter_sweep(param, values, dummy_simulation_fn)
        print("Sweep results:", results)
    if args.counterfactual:
        import json
        base_state = json.loads(args.counterfactual[0])
        changes = json.loads(args.counterfactual[1])
        result = engine.run_counterfactual(base_state, changes, dummy_simulation_fn)
        print("Counterfactual result:", result)
    if args.self_play:
        results = engine.run_self_play(dummy_simulation_fn, n=args.self_play)
        print("Self-play results:", results)
