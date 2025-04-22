# memory/forecast_memory_entropy.py

"""
Forecast Memory Entropy Analyzer

Measures symbolic entropy and novelty across memory:
- Detects symbolic stagnation
- Flags echo chamber effects
- Prevents redundancy in foresight

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
import math
from typing import List, Dict
from collections import Counter


def score_memory_entropy(forecasts, key: str = "arc_label") -> float:
    # Accept ForecastMemory or list
    if hasattr(forecasts, "_memory"):
        forecasts = forecasts._memory
    if not isinstance(forecasts, list):
        raise ValueError("Input forecasts must be a list")
    """
    Compute normalized entropy of arc/tag distribution.

    Returns:
        float: 0 = no diversity, 1 = max symbolic entropy
    """
    symbols = [f.get(key, "unknown") for f in forecasts]
    total = len(symbols)
    if total == 0:
        return 0.0

    counts = Counter(symbols)
    entropy = -sum((v / total) * math.log2(v / total) for v in counts.values())
    max_entropy = math.log2(len(counts)) if counts else 1
    return round(entropy / max_entropy, 3) if max_entropy > 0 else 0.0


def compare_against_memory(new_batch, memory, key: str = "arc_label") -> float:
    if hasattr(memory, "_memory"):
        memory = memory._memory
    if not isinstance(new_batch, list) or not isinstance(memory, list):
        raise ValueError("Inputs must be lists")
    """
    Compute symbolic novelty of new batch vs memory.

    Returns:
        float: 0 = all symbols already exist in memory, 1 = completely new
    """
    new_syms = set(f.get(key, "unknown") for f in new_batch)
    mem_syms = set(f.get(key, "unknown") for f in memory)
    novel = new_syms - mem_syms
    return round(len(novel) / max(len(new_syms), 1), 3)


def flag_memory_duplication(new_batch, memory, key: str = "arc_label") -> List[Dict]:
    if hasattr(memory, "_memory"):
        memory = memory._memory
    if not isinstance(new_batch, list) or not isinstance(memory, list):
        raise ValueError("Inputs must be lists")
    """
    Tag forecasts that duplicate existing memory arcs/tags.

    Returns:
        List[Dict]: forecasts with 'symbolic_duplicate': true
    """
    memory_labels = set(f.get(key, "unknown") for f in memory)
    for fc in new_batch:
        fc["symbolic_duplicate"] = fc.get(key, "unknown") in memory_labels
    return new_batch


def generate_entropy_report(forecasts, memory) -> Dict:
    if hasattr(forecasts, "_memory"):
        forecasts = forecasts._memory
    if hasattr(memory, "_memory"):
        memory = memory._memory
    """
    Generate a report of entropy and novelty metrics.

    Returns:
        Dict: Contains current entropy, new batch entropy, and symbolic novelty.
    """
    return {
        "current_entropy": score_memory_entropy(memory),
        "new_batch_entropy": score_memory_entropy(forecasts),
        "symbolic_novelty": compare_against_memory(forecasts, memory)
    }


def _test_forecast_memory_entropy():
    dummy_mem = [
        {"arc_label": "Hope Surge"},
        {"arc_label": "Collapse Risk"},
        {"arc_label": "Hope Surge"},
    ]
    dummy_new = [
        {"arc_label": "Hope Surge"},
        {"arc_label": "Fatigue Loop"},
    ]
    entropy = score_memory_entropy(dummy_mem)
    novelty = compare_against_memory(dummy_new, dummy_mem)
    flagged = flag_memory_duplication(dummy_new, dummy_mem)
    assert isinstance(entropy, float)
    assert 0.0 <= novelty <= 1.0
    assert flagged[0]["symbolic_duplicate"] is True
    assert flagged[1]["symbolic_duplicate"] is False
    print("✅ Forecast memory entropy test passed.")


if __name__ == "__main__":
    _test_forecast_memory_entropy()
