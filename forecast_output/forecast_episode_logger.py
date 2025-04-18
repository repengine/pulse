"""
Module: forecast_episode_logger.py
Pulse Version: v0.017.0
Location: pulse/forecast_output/
Last Updated: 2025-04-17
Author: Pulse AI Engine

Description:
Logs symbolic/emotional episodes during simulation turns for narrative memory.
Used by PFPA, Trust Engine, and symbolic coherence scoring.

Inputs:
- symbolic_overlays: Dict[str, float]
- sim_id: str
- turn: int
- optional tag (label for moment)

Log Output:
- logs/forecast_episodes.jsonl
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional
from core.path_registry import PATHS

EPISODE_LOG_PATH = PATHS.get("EPISODE_LOG_PATH", "logs/forecast_episodes.jsonl")

def ensure_log_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def log_episode_event(
    overlays: Dict[str, float],
    sim_id: str,
    turn: int,
    tag: Optional[str] = None
) -> Dict:
    """
    Logs an episode based on current symbolic state at a simulation turn.
    """
    ensure_log_dir(EPISODE_LOG_PATH)

    event = {
        "simulation_id": sim_id,
        "turn": turn,
        "tag": tag or "unlabeled",
        "overlays": overlays,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "version": "v0.017.0",
            "source": "pulse/forecast_output/forecast_episode_logger.py"
        }
    }

    try:
        with open(EPISODE_LOG_PATH, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        print(f"[EpisodeLogger] Logging error: {e}")

    return event

# Example usage
if __name__ == "__main__":
    sample = {
        "hope": 0.72,
        "despair": 0.22,
        "rage": 0.33,
        "fatigue": 0.41
    }
    result = log_episode_event(sample, sim_id="sim_0425", turn=6, tag="Hope Spike")
    print("Logged episode:", result["tag"], "→ Hope:", sample["hope"])
