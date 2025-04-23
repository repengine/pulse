# scheduler/symbolic_sweep_scheduler.py

"""
Symbolic Sweep Scheduler

Periodically re-tests blocked forecasts for trust recovery based on updated logic.

Features:
- Retry failed forecasts
- Reapply license pipeline
- Export recovered forecasts
- Log sweep summary to JSONL

Author: Pulse AI Engine
Version: v1.0.0
"""

import json
import os
from datetime import datetime
from typing import List, Dict
from memory.memory_repair_queue import load_blocked_memory, retry_licensing, export_recovered
from trust_system.recovered_forecast_scorer import (
    score_recovered_forecasts,
    flag_unstable_forecasts,
    summarize_repair_quality,
    export_flagged_for_revision
)


SWEEP_LOG_PATH = "logs/symbolic_sweep_log.jsonl"
BLOCKED_LOG_PATH = "logs/blocked_memory_log.jsonl"
RECOVERED_OUTPUT_PATH = "logs/sweep_recovered_forecasts.jsonl"


def run_sweep_now(export: str = RECOVERED_OUTPUT_PATH) -> Dict:
    """Run a symbolic sweep now and log results."""
    blocked = load_blocked_memory(BLOCKED_LOG_PATH)
    recovered = retry_licensing(blocked)

    for fc in recovered:
        fc["repair_source"] = "symbolic_sweep"

    export_recovered(recovered, export)
    recovered = score_recovered_forecasts(recovered)
    recovered = flag_unstable_forecasts(recovered)
    summary = summarize_repair_quality(recovered)
    print(summary)
    export_flagged_for_revision(recovered, "logs/unresolved_forecasts.jsonl")
    
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_blocked": len(blocked),
        "recovered": len(recovered),
        "output_path": export
    }

    try:
        os.makedirs(os.path.dirname(SWEEP_LOG_PATH), exist_ok=True)
        with open(SWEEP_LOG_PATH, "a") as f:
            f.write(json.dumps(result) + "\n")
        print(f"🧠 Sweep logged to {SWEEP_LOG_PATH}")
    except Exception as e:
        print(f"❌ Failed to log sweep summary: {e}")

    return result


def summarize_sweep_log(path: str = SWEEP_LOG_PATH):
    """Print summary stats of all past sweeps."""
    try:
        with open(path, "r") as f:
            entries = [json.loads(line.strip()) for line in f if line.strip()]
        print(f"📚 Symbolic Sweep History ({len(entries)} entries):")
        for r in entries[-5:]:
            print(f"- {r['timestamp']} → Recovered {r['recovered']} / {r['total_blocked']}")
    except Exception as e:
        print(f"❌ Failed to read sweep log: {e}")
