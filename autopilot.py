"""
autopilot.py

Pulse Autopilot: Runs simulation, retrodiction, learning, and data ingestion in an adaptive loop.
Prioritizes actions that most improve predictive accuracy.
"""
import time
import logging
from collections import deque
import signal
from threading import Event
from trust_system.trust_engine import TrustEngine
from forecast_engine.forecast_regret_engine import analyze_regret
from memory.pulse_memory_guardian import prune_memory

shutdown_event = Event()

# --- Composite metric helpers ---
def get_recent_trust():
    try:
        df = data_reader.load_forecast_outputs()
        if "confidence" in df.columns:
            return float(df["confidence"].tail(10).mean())
    except Exception:
        pass
    return None

def get_recent_regret():
    try:
        df = data_reader.load_forecast_outputs()
        if "regret" in df.columns:
            return float(df["regret"].tail(10).mean())
    except Exception:
        pass
    return None

def get_recent_volatility():
    try:
        df = data_reader.load_forecast_outputs()
        if "volatility" in df.columns:
            return float(df["volatility"].tail(10).mean())
    except Exception:
        pass
    return None

def get_composite_score():
    # Lower error/regret/volatility is better, higher trust is better
    error = get_recent_accuracy() or 1.0
    trust = get_recent_trust() or 0.0
    regret = get_recent_regret() or 1.0
    volatility = get_recent_volatility() or 1.0
    # Weighted composite: adjust as needed
    return 0.4 * (1 - error) + 0.3 * trust + 0.2 * (1 - regret) + 0.1 * (1 - volatility)

# --- Error handling and deprioritization ---
action_failures = {a: 0 for a in actions}
FAILURE_PENALTY = 0.5  # Reduce impact score by this on failure
MAX_FAILURES = 3

# --- Signal handling for graceful shutdown ---
def handle_shutdown(signum, frame):
    logger.info("Received shutdown signal. Exiting after current cycle...")
    shutdown_event.set()

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# --- Resource cleanup ---
def resource_cleanup():
    try:
        prune_memory(None, max_entries=1000, dry_run=False)
        logger.info("Memory pruned.")
    except Exception as e:
        logger.warning(f"Memory pruning failed: {e}")
    # Log rotation stub: implement as needed

# --- Extensible action registry ---
def register_action(name, func):
    actions.append(name)
    action_funcs[name] = func
    impact_history[name] = deque(maxlen=IMPACT_WINDOW)
    action_failures[name] = 0

action_funcs = {
    "simulate": lambda: run_pulse_simulation(turns=5),
    "retrodict": lambda: run_retrodiction_test(start_date="2020-01-01", days=7),
    "learn": lambda: learning_engine.run_meta_update(),
    "ingest": lambda: scraper.run_plugins(),
}

# --- Main autopilot loop (improved) ---
def autopilot_loop():
    logger.info("Starting Pulse Autopilot loop (intelligent mode, robust)...")
    prev_score = get_composite_score()
    cycle_count = 0
    while not shutdown_event.is_set():
        avg_impact = {}
        for a in actions:
            base = sum(impact_history[a])/len(impact_history[a]) if impact_history[a] else 0.0
            penalty = FAILURE_PENALTY * action_failures[a]
            avg_impact[a] = base - penalty
        action = max(avg_impact, key=avg_impact.get)
        logger.info(f"Selected action: {action} (avg impact: {avg_impact[action]:.4f}, failures: {action_failures[action]})")
        try:
            action_funcs[action]()
            action_failures[action] = 0
        except Exception as e:
            logger.error(f"Action {action} failed: {e}")
            action_failures[action] += 1
            if action_failures[action] >= MAX_FAILURES:
                logger.warning(f"Action {action} temporarily deprioritized due to repeated failures.")
        new_score = get_composite_score()
        impact = (new_score - prev_score) if (prev_score is not None and new_score is not None) else 0.0
        impact_history[action].append(impact)
        logger.info(f"Cycle complete. {action} impact: {impact:.4f}")
        prev_score = new_score
        cycle_count += 1
        if cycle_count % 10 == 0:
            resource_cleanup()
        time.sleep(CYCLE_SLEEP)

if __name__ == "__main__":
    autopilot_loop()
