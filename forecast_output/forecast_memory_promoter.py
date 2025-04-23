"""
forecast_memory_promotor.py

Promotes high-value forecasts to memory based on strategic utility,
confidence, and symbolic integrity.

Author: Pulse v0.26
"""

from typing import List, Dict
from output.forecast_prioritization_engine import rank_certified_forecasts
from memory.forecast_memory import ForecastMemory
from utils.log_utils import log_info

def promote_to_memory(forecasts: List[Dict], top_n: int = 10, min_conf: float = 0.6, dry_run: bool = False) -> int:
    """
    Promote top-ranked forecasts to long-term memory.

    Args:
        forecasts (List[Dict]): Raw or compressed forecast list
        top_n (int): Number of forecasts to retain
        min_conf (float): Minimum confidence required
        dry_run (bool): If True, do not actually store to memory

    Returns:
        int: Number of forecasts promoted (or would be promoted if dry_run)
    """
    if not forecasts:
        log_info("[PROMOTOR] No forecasts provided.")
        return 0

    # Step 1: Filter certified + confident
    certified = [f for f in forecasts if f.get("certified") and f.get("confidence", 0) >= min_conf]
    if not certified:
        log_info("[PROMOTOR] No forecasts passed certification/confidence gate.")
        return 0

    # Step 2: Prioritize
    top = rank_certified_forecasts(certified)[:top_n]

    # Step 3: Store in memory
    if not dry_run:
        memory = ForecastMemory()
        stored = 0
        for f in top:
            try:
                memory.store(f)
                stored += 1
            except Exception as e:
                log_info(f"[PROMOTOR] Failed to store forecast: {e}")
        log_info(f"[PROMOTOR] {stored} forecasts promoted to memory.")
        return stored
    else:
        log_info(f"[PROMOTOR] [DRY RUN] {len(top)} forecasts would be promoted to memory.")
        return len(top)

# Example usage & test
if __name__ == "__main__":
    test_batch = [
        {"confidence": 0.82, "certified": True, "arc_label": "Hope Surge", "alignment_score": 0.88},
        {"confidence": 0.75, "certified": True, "arc_label": "Stabilization", "alignment_score": 0.76},
        {"confidence": 0.42, "certified": False, "arc_label": "Collapse Risk", "alignment_score": 0.51},
    ]
    count = promote_to_memory(test_batch, dry_run=True)
    print(f"✅ {count} forecasts would be promoted (dry run)")
    count = promote_to_memory(test_batch)
    print(f"✅ {count} forecasts promoted")
