"""
retrodiction_engine.py

Retrodiction engine refactored to use unified simulate_forward function with retrodiction mode.
Removes redundant manual retrodiction scoring and comparison functions.
Provides wrapper function to run retrodiction simulation and process results consistently.

Author: Pulse v0.4
"""

from typing import Dict, List, Optional, Any, Callable
from memory.forecast_memory import ForecastMemory
from utils.log_utils import get_logger
from core.path_registry import PATHS
from pathlib import Path
from simulation_engine.worldstate import WorldState

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

logger = get_logger(__name__)

forecast_memory = ForecastMemory(persist_dir=str(PATHS["FORECAST_HISTORY"]))
retrodiction_memory = ForecastMemory()

def run_retrodiction_simulation(
    initial_state: WorldState,
    turns: int,
    retrodiction_loader: Optional[object] = None,
    logger_fn: Optional[Callable[[str], None]] = None,
    injection_mode: str = "seed_then_free"
) -> List[Dict[str, Any]]:
    """
    Runs retrodiction simulation using the unified simulate_forward function in retrodiction mode.

    Args:
        initial_state (WorldState): The initial world state to simulate from.
        turns (int): Number of turns to simulate.
        retrodiction_loader (Optional[object]): Loader providing ground truth snapshots for retrodiction.
        logger_fn (Optional[Callable]): Optional logger function.
        injection_mode (str): Injection mode for retrodiction variables ("seed_then_free" or "strict_injection").

    Returns:
        List[Dict[str, Any]]: List of simulation results per turn with trust metadata.
    """
    from simulation_engine.simulator_core import simulate_forward
    results = simulate_forward(
        state=initial_state,
        turns=turns,
        retrodiction_mode=True,
        retrodiction_loader=retrodiction_loader,
        logger=logger_fn,
        injection_mode=injection_mode
    )
    return results

def save_retrodiction_results(results: List[Dict[str, Any]]) -> None:
    """
    Saves retrodiction results to persistent memory, ensuring overlays are serializable.

    Args:
        results (List[Dict[str, Any]]): Retrodiction simulation results.
    """
    def overlay_to_dict(overlay):
        if hasattr(overlay, "as_dict"):
            return overlay.as_dict()
        return dict(overlay)

    if isinstance(results, list):
        for res in results:
            if "overlays" in res:
                res["overlays"] = overlay_to_dict(res["overlays"])
            if "forks" in res:
                for fork in res["forks"]:
                    if "overlays" in fork:
                        fork["overlays"] = overlay_to_dict(fork["overlays"])
        for res in results:
            retrodiction_memory.store(res)
    elif isinstance(results, dict):
        if "overlays" in results:
            results["overlays"] = overlay_to_dict(results["overlays"])
        if "forks" in results:
            for fork in results["forks"]:
                if "overlays" in fork:
                    fork["overlays"] = overlay_to_dict(fork["overlays"])
        retrodiction_memory.store(results)

def save_forecast(forecast_obj: Dict) -> None:
    """
    Saves a forecast object to persistent memory, ensuring overlays are serializable.

    Args:
        forecast_obj (Dict): Forecast dictionary to save.
    """
    def overlay_to_dict(overlay):
        if hasattr(overlay, "as_dict"):
            return overlay.as_dict()
        return dict(overlay)

    if "overlays" in forecast_obj:
        forecast_obj["overlays"] = overlay_to_dict(forecast_obj["overlays"])
    if "forks" in forecast_obj:
        for fork in forecast_obj["forks"]:
            if "overlays" in fork:
                fork["overlays"] = overlay_to_dict(fork["overlays"])
    forecast_memory.store(forecast_obj)

# === Local test ===
def simulate_retrodiction_test():
    """
    Local test for retrodiction simulation using unified simulate_forward.
    """
    from forecast_output.pfpa_logger import pfpa_memory
    if not pfpa_memory.get_recent(1):
        logger.info("No forecasts in PFPA archive; skipping retrodiction.")
        return

    # Initialize a WorldState for simulation (stub or real)
    initial_state = WorldState()
    initial_state.sim_id = "retrodiction_test"

    # Number of turns to simulate (example: 5)
    turns = 5

    # Retrodiction loader providing ground truth snapshots (stub or real)
    retrodiction_loader = None  # Replace with actual loader if available

    results = run_retrodiction_simulation(
        initial_state=initial_state,
        turns=turns,
        retrodiction_loader=retrodiction_loader,
        logger_fn=logger.info
    )
    for r in results:
        logger.info(f"[RETRO] Turn {r['turn']} | Trust: {r.get('trust_label', 'N/A')} | Confidence: {r.get('confidence', 'N/A')}")
    save_retrodiction_results(results)

if __name__ == "__main__":
    simulate_retrodiction_test()
