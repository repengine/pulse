"""
Module: symbolic_memory.py
Pulse Version: v0.21.1
Last Updated: 2025-04-16
Author: Pulse AI Engine

Description:
Tracks symbolic overlay states across turns in each simulation. Logs to file for downstream symbolic analysis.
Located in: main/symbolic_system/

Used by: PulseMirror, ForecastCompressor, Drift Monitor

Enhancements:
- Type validation
- Automatic log directory creation
- Version-tagged metadata
- Safe fallback logging with examples

Status: ✅ Built + Enhanced
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional
from utils.log_utils import get_logger
from core.path_registry import PATHS

logger = get_logger(__name__)

SYMBOLIC_LOG_PATH = PATHS.get("SYMBOLIC_LOG_PATH", "logs/symbolic_memory_log.jsonl")

def ensure_log_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def record_symbolic_state(turn: int, overlays: Dict[str, float], sim_id: str = "default", log_path: Optional[str] = None):
    if not isinstance(turn, int) or turn < 0:
        raise ValueError("Turn must be a non-negative integer.")
    if not isinstance(overlays, dict) or not all(isinstance(v, (int, float)) for v in overlays.values()):
        raise ValueError("Overlays must be a dictionary of floats.")

    path = log_path or PATHS["WORLDSTATE_LOG_DIR"]
    ensure_log_dir(path)

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "simulation_id": sim_id,
        "turn": turn,
        "symbolic_overlays": overlays,
        "metadata": {
            "version": "v0.21.1",
            "source": "main/symbolic_system/symbolic_memory.py"
        }
    }
    try:
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error(f"[SymbolicMemory] Error writing log: {e}")

# Example usage
if __name__ == "__main__":
    record_symbolic_state(
        turn=1,
        overlays={"hope": 0.51, "despair": 0.28, "rage": 0.12, "fatigue": 0.09},
        sim_id="sim_0425A"
    )
