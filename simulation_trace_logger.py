import json
import os
from datetime import datetime

def ensure_log_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def log_simulation_trace(trace, tag="run", log_dir="logs/simulation_traces"):
    """
    Appends a simulation trace (list of dicts or dict with 'trace' key) to a .jsonl file.
    """
    ensure_log_dir(log_dir + "/dummy.txt")
    fname = f"{tag}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl"
    path = os.path.join(log_dir, fname)
    with open(path, "a", encoding="utf-8") as f:
        if isinstance(trace, dict) and "trace" in trace:
            for entry in trace["trace"]:
                f.write(json.dumps(entry) + "\n")
        elif isinstance(trace, list):
            for entry in trace:
                f.write(json.dumps(entry) + "\n")
        else:
            f.write(json.dumps(trace) + "\n")
    return path
