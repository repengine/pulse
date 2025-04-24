"""
historical_retrodiction_runner.py

Runs retrodictive simulations from a known historical state toward the present.
Compares simulated worldstates to ground-truth data and scores outcome divergence.

Used to test and evolve rules, overlays, and symbolic integrity over time.

Author: Pulse v0.35 (C-Test Enhanced)
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from simulation_engine.worldstate import WorldState
from simulation_engine.turn_engine import run_turn
from learning.learning.py import compute_retrodiction_error
from core.path_registry import PATHS
from memory.trace_memory import TraceMemory
from core.variable_registry import get_default_variable_state, validate_variables
import os
import pandas as pd
HIST_PARQ_PATH = PATHS.get("HISTORICAL_GROUND_TRUTH_PARQUET", "data/historical_worldstate.parquet")

def _ensure_truth_parquet():
    if not os.path.exists(HIST_PARQ_PATH):
        try:
            df = pd.read_json(TRUTH_PATH, lines=True)
            os.makedirs(os.path.dirname(HIST_PARQ_PATH), exist_ok=True)
            df.to_parquet(HIST_PARQ_PATH, index=False)
            print("[Retrodiction] Migrated ground-truth to Parquet for performance")
        except Exception as e:
            print(f"[Retrodiction] Failed migrating to Parquet: {e}")
import os
from pathlib import Path
import concurrent.futures

CACHE_DIR = PATHS.get("RETRO_CACHE_DIR", "cache/retrodiction_snapshots")

TRUTH_PATH = PATHS.get("HISTORICAL_GROUND_TRUTH", "data/historical_worldstate.json")
REPLAY_LOG = PATHS.get("RETRODICTION_LOG", "logs/retrodiction_result_log.jsonl")

def load_historical_baseline(date_str: str) -> Dict[str, float]:
    defaults = get_default_variable_state()
    # Convert JSONL ground-truth to Parquet once
    _ensure_truth_parquet()
    # Attempt reading from Parquet for faster lookup
    if os.path.exists(HIST_PARQ_PATH):
        try:
            df = pd.read_parquet(HIST_PARQ_PATH, columns=['date', 'variables'])
            sel = df[df['date'] == date_str]
            if not sel.empty:
                vars_raw = sel.iloc[0]['variables']
                valid, missing, unexpected = validate_variables(vars_raw)
                if unexpected:
                    print(f"[Retrodiction] Unexpected variables {unexpected} for {date_str}; dropping them")
                    for k in unexpected:
                        vars_raw.pop(k, None)
                for m in missing:
                    vars_raw[m] = defaults.get(m)
                    print(f"[Retrodiction] Imputed missing variable {m} with default {defaults.get(m)}")
                return vars_raw
        except Exception as e:
            print(f"[Retrodiction] Parquet read failed: {e}")
    try:
        with open(TRUTH_PATH, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as err:
                    print(f"[Retrodiction] Skipping invalid JSON line: {err}")
                    continue
                if entry.get("date") == date_str:
                    vars_raw = entry.get("variables", {})
                    valid, missing, unexpected = validate_variables(vars_raw)
                    if unexpected:
                        print(f"[Retrodiction] Unexpected variables {unexpected} in baseline for {date_str}; dropping them")
                        for k in unexpected:
                            vars_raw.pop(k, None)
                    for m in missing:
                        vars_raw[m] = defaults.get(m)
                        print(f"[Retrodiction] Imputed missing variable {m} with default {defaults.get(m)}")
                    return vars_raw
    except Exception as e:
        print(f"[Retrodiction] Failed to load baseline: {e}")
    print(f"[Retrodiction] Baseline for {date_str} not found; returning default state")
    return defaults.copy()

def simulate_forward(state: WorldState, steps: int = 30, cache_key: Optional[str] = None) -> List[Dict[str, Any]]:
    history = []
    cache_base = Path(CACHE_DIR)
    if cache_key:
        cache_path = cache_base / cache_key
        if cache_path.exists():
            for file in sorted(cache_path.glob("*.json")):
                history.append(json.loads(file.read_text()))
            print(f"[Sim] Loaded {len(history)} cached snapshots for {cache_key}")
            return history
        else:
            cache_path.mkdir(parents=True, exist_ok=True)
    for i in range(steps):
        run_turn(state)
        snapshot = state.snapshot()
        print(f"[Sim] Step {i+1}/{steps} | State snapshot: {snapshot.get('variables', {})}")
        history.append(snapshot)
        if cache_key:
            file_path = cache_path / f"{i+1:03d}.json"
            with open(file_path, "w") as cf:
                cf.write(json.dumps(snapshot))
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
    sim_results = simulate_forward(state, steps=days, cache_key=start_date)

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

def run_retrodiction_tests(start_dates: List[str], days: int = 30, max_workers: int = 4):
    """Parallel retrodiction for multiple start dates."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_retrodiction_test, sd, days): sd for sd in start_dates}
        for future in concurrent.futures.as_completed(futures):
            sd = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[Retrodiction] Error for {sd}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Historical retrodiction runner CLI")
    parser.add_argument(
        "--start-dates",
        type=str,
        help="Comma-separated list of start dates (YYYY-MM-DD)",
        default="2020-01-01"
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Number of days to simulate",
        default=14
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="Number of parallel workers",
        default=4
    )
    args = parser.parse_args()
    dates = [d.strip() for d in args.start_dates.split(",")]
    run_retrodiction_tests(dates, days=args.days, max_workers=args.workers)
