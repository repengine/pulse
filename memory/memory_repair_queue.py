# memory/memory_repair_queue.py

"""
Memory Repair Queue

Re-evaluate discarded forecasts from blocked memory for possible recovery
after symbolic trust shift, license threshold adjustment, or operator review.

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
from typing import List, Dict, Optional
from trust_system.license_enforcer import annotate_forecasts, filter_licensed

BLOCKED_LOG_PATH = "logs/blocked_memory_log.jsonl"

def load_blocked_memory(path: str = BLOCKED_LOG_PATH) -> List[Dict]:
    """Load blocked forecasts from memory discard log."""
    try:
        with open(path, "r") as f:
            return [json.loads(line.strip()) for line in f if line.strip()]
    except Exception as e:
        print(f"❌ Failed to load blocked memory: {e}")
        return []

def filter_for_retry(forecasts: List[Dict], reasons: List[str]) -> List[Dict]:
    """Filter blocked forecasts for retry based on license status reasons."""
    return [f for f in forecasts if f.get("license_status", "") in reasons]

def retry_licensing(blocked: List[Dict]) -> List[Dict]:
    """Re-run license scoring on blocked forecasts."""
    print(f"🔁 Retesting {len(blocked)} discarded forecasts...")
    repaired = annotate_forecasts(blocked)
    return filter_licensed(repaired)

def export_recovered(forecasts: List[Dict], path: str) -> None:
    """Save recovered forecasts to a JSONL file."""
    try:
        with open(path, "w") as f:
            for fc in forecasts:
                f.write(json.dumps(fc) + "\n")
        print(f"✅ Saved {len(forecasts)} recovered forecasts to {path}")
    except Exception as e:
        print(f"❌ Export failed: {e}")
