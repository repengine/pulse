"""
analytics.trace_memory.py

Central memory graph to link simulations, forecasts, trace metadata, trust scores, and outcomes.
Acts as the knowledge backbone for replay, learning, and meta-evolution.

Author: Pulse v0.27
"""

import os
import json
from typing import Dict, Optional, List
from datetime import datetime
from engine.path_registry import PATHS

TRACE_DB_PATH = PATHS.get("TRACE_DB", "logs/trace_memory_log.jsonl")


class TraceMemory:
    """
    Logs and queries simulation trace metadata linked to forecasts and trust scores.
    """

    def __init__(self, path: Optional[str] = None):
        self.path = path or TRACE_DB_PATH
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def log_trace_entry(
        self, trace_id: str, forecast: Dict, input_state: Optional[Dict] = None
    ):
        """
        Logs a full trace-forecast-trust-memory record.
        """
        record = {
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": forecast.get("confidence"),
            "fragility": forecast.get("fragility"),
            "trust_label": forecast.get("confidence_status"),
            "arc_label": forecast.get("arc_label"),
            "certified": forecast.get("certified"),
            "forecast": forecast,
            "input_state": input_state or {},
            "symbolic_tag": forecast.get("symbolic_tag"),
            "alignment_score": forecast.get("alignment_score"),
        }
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[TraceMemory] Log error: {e}")

    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """
        Retrieves full record by trace ID.
        """
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        if rec.get("trace_id") == trace_id:
                            return rec
                    except Exception as e:
                        print(f"[TraceMemory] Skipping malformed line: {e}")
        except Exception as e:
            print(f"[TraceMemory] Retrieval error: {e}")
        return None

    def summarize_memory(self, max_entries: int = 100) -> Dict:
        """
        Returns summary stats for most recent entries.
        """
        records = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        records.append(json.loads(line))
                        if len(records) > max_entries:
                            records.pop(0)
                    except Exception as e:
                        print(f"[TraceMemory] Skipping malformed line: {e}")
        except Exception as e:
            print(f"[TraceMemory] Summarization error: {e}")
            return {}

        summary = {
            "count": len(records),
            "avg_conf": round(
                sum(r.get("confidence", 0) for r in records) / len(records), 4
            )
            if records
            else 0.0,
            "avg_fragility": round(
                sum(r.get("fragility", 0) for r in records) / len(records), 4
            )
            if records
            else 0.0,
            "certified": sum(1 for r in records if r.get("certified")),
        }
        if len(records) > 10000:
            print("[TraceMemory] Warning: trace log is very large, consider archiving.")
        return summary

    def list_trace_ids(self) -> List[str]:
        """
        Returns a list of all trace IDs in the log.
        """
        ids = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        if "trace_id" in rec:
                            ids.append(rec["trace_id"])
                    except Exception:
                        continue
        except Exception as e:
            print(f"[TraceMemory] Error listing trace IDs: {e}")
        return ids

    def delete_trace(self, trace_id: str) -> bool:
        """
        Deletes a trace by ID. Returns True if deleted, False if not found.
        """
        found = False
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(self.path, "w", encoding="utf-8") as f:
                for line in lines:
                    try:
                        rec = json.loads(line)
                        if rec.get("trace_id") == trace_id:
                            found = True
                            continue
                        f.write(json.dumps(rec) + "\n")
                    except Exception:
                        f.write(line)
        except Exception as e:
            print(f"[TraceMemory] Error deleting trace: {e}")
        return found


# === Example usage & simple test
def _test_trace_memory():
    sample_forecast = {
        "trace_id": "abc123",
        "confidence": 0.8,
        "certified": True,
        "arc_label": "Hope Surge",
        "symbolic_tag": "hope",
    }
    TM = TraceMemory()
    TM.log_trace_entry("abc123", sample_forecast, input_state={"hope": 0.5})
    result = TM.get_trace("abc123")
    print("Retrieved:", result)
    print("Summary:", TM.summarize_memory())
    ids = TM.list_trace_ids()
    print("Trace IDs:", ids)
    deleted = TM.delete_trace("abc123")
    print("Deleted:", deleted)
    assert deleted


if __name__ == "__main__":
    _test_trace_memory()
