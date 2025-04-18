"""
worldstate_monitor.py

Provides display and logging functions for Pulse simulation:
- Symbolic overlays
- Capital exposure
- Variable states
- Delta view vs prior state
- Optional logging to file

Author: Pulse v0.4
"""

from simulation_engine.worldstate import WorldState
from utils.log_utils import get_logger
import datetime
import os

logger = get_logger(__name__)

def display_overlay_state(state: WorldState):
    print("\n🔮 Symbolic Overlays:")
    for name, val in state.overlays.as_dict().items():
        print(f"  {name.capitalize():<8} → {val:.3f}")


def display_capital_exposure(state: WorldState):
    print("\n💰 Capital Exposure:")
    for asset, val in state.capital.as_dict().items():
        print(f"  {asset.upper():<6} → ${val:,.2f}")


def display_variable_state(state: WorldState):
    print("\n🌐 Worldstate Variables:")
    for name, val in state.variables.as_dict().items():
        print(f"  {name:<24} : {val:.3f}")


def display_deltas(state: WorldState, prev_state: WorldState):
    print("\n🔁 Overlay Change (Δ vs last turn):")
    for name, current in state.overlays.as_dict().items():
        prev = prev_state.overlays.as_dict().get(name, 0)
        delta = current - prev
        print(f"  {name:<8} → Δ {delta:+.3f}")


def display_all(state: WorldState, prev_state: WorldState = None, log: bool = False):
    stamp = f"TURN {state.turn}"
    print(f"\n=== {stamp} STATE ===")
    display_overlay_state(state)
    display_capital_exposure(state)
    display_variable_state(state)
    if prev_state:
        display_deltas(state, prev_state)
    print("=" * 35)

    if log:
        folder = os.path.join("pulse", "logs")
        os.makedirs(folder, exist_ok=True)
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
        file = os.path.join(folder, f"state_{state.turn}_{ts}.txt")
        with open(file, "w", encoding="utf-8") as f:
            f.write(f"Turn {state.turn} Worldstate Snapshot\n")
            f.write(f"Overlays: {state.overlays.as_dict()}\n")
            f.write(f"Capital : {state.capital.as_dict()}\n")
            f.write(f"Vars    : {state.variables.as_dict()}\n")
            f.write("\n")
        print(f"📁 State saved to {file}")


def run_batch_forecasts(count=5, domain="capital", min_conf=0.5, symbolic_block=None, verbose=True, export_summary=True):
    logs = []
    rejected = 0
    for i in range(count):
        forecast_id = f"forecast_{i}"
        metadata = {"confidence": 0.7}  # Example metadata
        accepted_condition = metadata.get("confidence", 0) >= min_conf and (symbolic_block is None or symbolic_block(metadata))
        if accepted_condition:
            logs.append({"forecast_id": forecast_id, "status": "accepted", "metadata": metadata})
            if verbose:
                logger.info(f"✅ Accepted [{forecast_id}] | Metadata: {metadata}")
        else:
            rejected += 1
            reason = "low_confidence" if metadata.get("confidence", 0) < min_conf else "blocked_symbolic"
            logs.append({"forecast_id": forecast_id, "status": "rejected", "reason": reason, "metadata": metadata})
            if verbose:
                logger.warning(f"⛔ Rejected [{forecast_id}] ({reason}) | Metadata: {metadata}")
    if export_summary:
        summary_file = os.path.join("pulse", "logs", "forecast_summary.txt")
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"Batch Forecast Summary\n")
            f.write(f"Total forecasts: {count}\n")
            f.write(f"Rejected: {rejected}\n")
            f.write(f"Logs: {logs}\n")
        logger.info(f"📁 Summary saved to {summary_file}")