"""
Module: symbolic_state_tagger.py
Pulse Version: v0.30.1
Last Updated: 2025-04-16
Author: Pulse AI Engine

Description:
Interprets current symbolic overlays and assigns a symbolic tag to describe the emotional state of the simulation.

Examples:
  - "Hope Rising"
  - "Collapse Risk"
  - "Symbolic Drain"
  - "Fatigue Plateau"

This module is critical for runtime narrative interpretation and supports symbolic trust scoring,
forecast compression grouping, and strategic alignment interfaces.

Inputs:
  - overlays: Dict[str, float] — must contain hope, despair, rage, fatigue (0.0–1.0)
  - sim_id: str
  - turn: int or None

Output:
  - tag object with symbolic_label, overlays, timestamp, and context metadata

Log Output:
  - logs/symbolic_state_tags.jsonl
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional
from utils.log_utils import get_logger
from core.path_registry import PATHS
from forecast_output.forecast_tags import ForecastTag, get_tag_label

logger = get_logger(__name__)

TAG_LOG_PATH = PATHS.get("SYMBOLIC_TAG_LOG", PATHS["WORLDSTATE_LOG_DIR"])

def ensure_log_dir(path: str):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except PermissionError:
        # Silently skip if we can't create the directory (prevents repeated error logs)
        return
    except Exception:
        return

def normalize_overlays(overlays: Dict[str, float]) -> Dict[str, float]:
    base = {"hope": 0.5, "despair": 0.5, "rage": 0.5, "fatigue": 0.5}
    for k in base:
        val = overlays.get(k)
        if isinstance(val, (int, float)):
            base[k] = round(float(val), 4)
    return base

def tag_symbolic_state(overlays: Dict[str, float], sim_id: str = "default", turn: Optional[int] = None) -> Dict:
    """
    Tags symbolic overlay state with a descriptive label.
    Returns structured tag data and writes to log file.
    """
    overlays = normalize_overlays(overlays)
    hope = overlays["hope"]
    despair = overlays["despair"]
    rage = overlays["rage"]
    fatigue = overlays["fatigue"]

    # Decision rules (ordered by intensity and priority)
    if hope > 0.7 and despair < 0.3 and rage < 0.4:
        tag = ForecastTag.HOPE
    elif despair > 0.7 and hope < 0.3:
        tag = ForecastTag.DESPAIR
    elif fatigue > 0.7 and rage < 0.4:
        tag = ForecastTag.FATIGUE
    elif rage > 0.65 and fatigue > 0.55:
        tag = ForecastTag.COLLAPSE_RISK
    elif all(v < 0.25 for v in [hope, despair, rage]):
        tag = ForecastTag.SYMBOLIC_DRAIN
    elif hope > 0.6 and rage > 0.6:
        tag = ForecastTag.HOPE_RAGE_CONFLICT
    elif fatigue > 0.6 and despair > 0.6:
        tag = ForecastTag.SYMBOLIC_EXHAUSTION
    else:
        tag = ForecastTag.NEUTRAL

    label = get_tag_label(tag)

    result = {
        "simulation_id": sim_id,
        "turn": turn,
        "symbolic_tag": label,
        "symbolic_tag_enum": tag.name,
        "symbolic_overlays": overlays,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "version": "v0.30.1",
            "source": "symbolic_state_tagger.py",
            "description": "Runtime symbolic state classification"
        }
    }

    ensure_log_dir(TAG_LOG_PATH)
    try:
        with open(TAG_LOG_PATH, "a") as f:
            f.write(json.dumps(result) + "\n")
    except Exception as e:
        logger.error(f"[SymbolicTagger] Logging error: {e}")

    return result

# Example usage
if __name__ == "__main__":
    example = tag_symbolic_state({
        "hope": 0.75,
        "despair": 0.2,
        "rage": 0.3,
        "fatigue": 0.25
    }, sim_id="v30_demo", turn=1)
    print(f"Symbolic Label: {example['symbolic_tag']}")
