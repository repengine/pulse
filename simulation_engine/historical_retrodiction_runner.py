"""
historical_retrodiction_runner.py

Runs retrodictive simulations from a known historical state toward the present.
Compares simulated worldstates to ground-truth data and scores outcome divergence.

Used to test and evolve rules, overlays, and symbolic integrity over time.

Author: Pulse v0.35 (C-Test Enhanced)
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from simulation_engine.worldstate import WorldState
from simulation_engine.turn_engine import run_turn
from trust_system.retrodiction_engine import compute_retrodiction_error
from core.path_registry import PATHS
from memory.trace_memory import TraceMemory

TRUTH_PATH = PATHS.get("HISTORICAL_GROUND_TRUTH", "data/historical_worldstate.json")
REPLAY_LOG = PATHS.get("RETRODICTION_LOG", "logs/retrodiction_result_log.jsonl")

def load_historical_baseline(date_str: str) -> Dict[str, float]:
    try:
        with open(TRUTH_PATH, "r") as f:
            for line in f:
                entry = json.loads(line)
                if entry.get("date") == date_str:
                    return entry.get("variables", {})
    except Exception as e:
        print(f"[Retrodiction] Failed to load baseline: {e}")
    return {}

def simulate_forward(state: WorldState, steps: int = 30) -> List[Dict[str, Any]]:
    history = []
    for i in range(steps):
        run_turn(state)
        snapshot = state.snapshot()
        print(f"[Sim] Step {i+1}/{steps} | State snapshot: {snapshot.get('variables', {})}")
        history.append(snapshot)
    return history

def compare_to_actual(sim_steps: List[Dict], truth_steps: List[Dict]) -> List[Dict]:
    comparisons = []
    for sim, truth in zip(sim_steps, truth_steps):
        if not truth["variables"]:
            print(f"⚠️ Missing truth data for sim date {sim.get('date')}")
            continue
        delta = compute_retrodiction_error({"forecast": {"start_state": sim}}, truth)
        comparisons.append({
            "sim_date": sim.get("date"),
            "error_score": delta
        })
        print(f"[Compare] Error score: {delta}")
    return comparisons

def run_retrodiction_test(start_date: str, days: int = 30):
    baseline = load_historical_baseline(start_date)
    if not baseline:
        print("[Retrodiction] Baseline state not found.")
        return
    state = WorldState(**baseline)
    sim_results = simulate_forward(state, steps=days)

    # Load corresponding truth for each day
    truth_steps = []
    d0 = datetime.strptime(start_date, "%Y-%m-%d")
    for i in range(days):
        target_day = (d0 + timedelta(days=i)).strftime("%Y-%m-%d")
        truth_state = load_historical_baseline(target_day)
        truth_steps.append({"overlays": {}, "variables": truth_state})

    results = compare_to_actual(sim_results, truth_steps)

    with open(REPLAY_LOG, "a") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # Log full trace lineage
    trace_logger = TraceMemory()
    for sim in sim_results:
        trace_logger.log_trace_entry(trace_id="retrodict_sim", forecast={"confidence": None}, input_state=sim.get("variables", {}))

    print(f"✅ Retrodiction complete for {start_date} → {days}d. Results written to log.")

if __name__ == "__main__":
    run_retrodiction_test("2020-01-01", days=14)
