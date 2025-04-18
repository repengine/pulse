"""
PATCHED: pulse_interactive_shell.py
Pulse Version: v0.22.4
Adds: run-batch [N] — generates and logs N forecasts

Note: To integrate, add "run-batch": cmd_run_batch to your COMMANDS dict.
"""

from typing import List
from forecast_output.forecast_batch_runner import run_forecast_batch
from simulation_engine.worldstate import WorldState

# Fallback log_interaction if used standalone
def log_interaction(command: str, result: str):
    print(f"[LOG] {command} → {result}")

def cmd_run_batch(args: List[str]):
    """Run a batch of N forecasts and summarize"""
    if len(args) != 1 or not args[0].isdigit():
        print("Usage: run-batch [N]")
        return
    batch_size = int(args[0])
    try:
        dummy_state = WorldState()
        batch = run_forecast_batch(dummy_state, batch_size=batch_size)
        print(f"✅ Batch complete. {len(batch)} forecasts generated.")
        log_interaction(f"run-batch {batch_size}", f"{len(batch)} forecasts")
    except Exception as e:
        print(f"[Shell] Batch error: {e}")
        log_interaction("run-batch", f"error: {e}")

# Optional: test hook
if __name__ == "__main__":
    cmd_run_batch(["3"])
