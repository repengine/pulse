"""
forecast_memory.py

Stores and retrieves recent or historical forecasts during simulation.
Supports symbolic tagging, replay, and integration with PFPA trust scoring.

"""

from core.path_registry import PATHS
assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

from typing import List, Dict, Optional

# 🧩 Import license enforcement utilities for use in memory/export flows
from trust_system.license_enforcer import annotate_forecasts, filter_licensed
from core.pulse_learning_log import log_learning_event
from datetime import datetime

from utils.log_utils import get_logger
logger = get_logger(__name__)

BLOCKED_MEMORY_LOG = "logs/blocked_memory_log.jsonl"

class ForecastMemory:
    """
    Unified forecast storage and retrieval.
    Supports memory limit enforcement and pruning of unused/old entries.
    """
    MAX_MEMORY_ENTRIES: int = 1000  # Default maximum number of forecasts to retain

    def __init__(self, persist_dir: Optional[str] = None, max_entries: Optional[int] = None):
        """
        Args:
            persist_dir: Directory to persist forecasts. Defaults to PATHS["FORECAST_HISTORY"].
            max_entries: Maximum number of forecasts to retain in memory.
        """
        # Ensure persist_dir is always a string path
        pd = persist_dir or PATHS["FORECAST_HISTORY"]
        self.persist_dir = str(pd)
        self._memory: List[Dict] = []
        self.max_entries = max_entries or self.MAX_MEMORY_ENTRIES
        if self.persist_dir:
            self._load_from_files()
        self._enforce_memory_limit()

    def store(self, forecast_obj: Dict) -> None:
        """
        Adds a forecast object to memory and persists to file. Prunes if over limit.

        Ensures that forecast_id is always present and is a string (UUID or fallback).
        This prevents downstream errors where a numeric ID is assumed.
        """
        import re
        import uuid
        # Type validation: Only allow dict-like objects
        if not isinstance(forecast_obj, dict):
            logger.warning(f"Attempted to store non-dictionary forecast of type {type(forecast_obj)}. Skipping.")
            return

        # Ensure numeric values are properly typed
        for numeric_field in ['confidence', 'fragility', 'priority', 'retrodiction_score']:
            if numeric_field in forecast_obj:
                val = forecast_obj[numeric_field]
                # Check if it looks like a UUID string
                uuid_like = isinstance(val, str) and re.match(r"^[0-9a-fA-F-]{32,36}$", str(val))
                if uuid_like:
                    logger.warning(f"UUID-like string in numeric field {numeric_field}: {val}. Setting to 0.0")
                    forecast_obj[numeric_field] = 0.0
                else:
                    try:
                        forecast_obj[numeric_field] = float(val) if val is not None else 0.0
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid value for {numeric_field}: {val}. Using 0.0")
                        forecast_obj[numeric_field] = 0.0

        # Ensure forecast_id is present and is a string (UUID or fallback)
        if "forecast_id" not in forecast_obj or forecast_obj["forecast_id"] is None:
            # Use trace_id if available, else fallback to "unknown"
            forecast_obj["forecast_id"] = str(forecast_obj.get("trace_id", "unknown"))
        else:
            forecast_obj["forecast_id"] = str(forecast_obj["forecast_id"])
        # PATCH: Tag drift-prone forecasts as review_only and unlicensed
        if forecast_obj.get("trust_label") == "🔴 Drift-Prone":
            forecast_obj["memory_flag"] = "review_only"
            forecast_obj["license"] = False
        logger.info(
            "[Forecast Pipeline] Storing forecast in memory: type=%s, keys=%s, sample=%s",
            type(forecast_obj),
            list(forecast_obj.keys())[:5],
            {k: forecast_obj[k] for k in list(forecast_obj.keys())[:3]}
        )
        self._memory.append(forecast_obj)
        self._enforce_memory_limit()
        if self.persist_dir:
            self._persist_to_file(forecast_obj)
        log_learning_event("memory_update", {
            "event": "forecast_stored",
            "forecast_id": forecast_obj["forecast_id"],
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_recent(self, n: int = 10, domain: Optional[str] = None) -> List[Dict]:
        """Retrieves the N most recent forecasts, optionally filtered by domain."""
        results = self._memory[-n:]
        if domain:
            results = [r for r in results if r.get("domain") == domain]
        return results

    def update_trust(self, forecast_id: str, trust_data: Dict) -> None:
        """Updates trust/scoring info for a forecast by ID."""
        for f in self._memory:
            if f.get("forecast_id") == forecast_id:
                f.update(trust_data)
                if self.persist_dir:
                    self._persist_to_file(f)
                break

    def prune(self, min_confidence: Optional[float] = None) -> int:
        """
        Prune memory entries below a confidence threshold or oldest if over limit.
        Returns the number of pruned entries.
        """
        before = len(self._memory)
        if min_confidence is not None:
            self._memory = [f for f in self._memory if float(f.get("confidence", 0)) >= min_confidence]
        self._enforce_memory_limit()
        return before - len(self._memory)

    def gate_memory_retention_by_license(self, license_loss_percent: float, threshold: float = 40.0):
        """
        Prevent memory retention if trust breaks down. Logs discarded content.

        Args:
            license_loss_percent (float): How many forecasts failed license test
            threshold (float): Block memory if over this %
        """
        import json
        if license_loss_percent > threshold:
            print(f"⚠️ Memory blocked due to license instability ({license_loss_percent:.1f}%)")
            try:
                with open(BLOCKED_MEMORY_LOG, "a") as f:
                    for entry in self._memory:
                        f.write(json.dumps(entry) + "\n")
                print(f"📤 Blocked memory logged to {BLOCKED_MEMORY_LOG}")
            except Exception as e:
                print(f"❌ Failed to log blocked memory: {e}")
            self._memory = []
        else:
            print("✅ Memory retention approved.")

    def retain_only_stable_forecasts(self):
        """Exclude unstable symbolic paths from memory retention."""
        self._memory = [
            f for f in self._memory
            if not f.get("unstable_symbolic_path")
        ]
        print(f"✅ Retained {len(self._memory)} stable forecasts in memory.")

    def retain_certified_forecasts(self):
        """Keep only forecasts marked as fully certified."""
        self._memory = [f for f in self._memory if f.get("certified") is True]
        print(f"🔒 Memory filtered: {len(self._memory)} certified forecasts retained.")

    def tag_uncertified_for_review(self):
        """Tag uncertified forecasts for review."""
        for f in self._memory:
            if not f.get("certified"):
                f["memory_flag"] = "uncertified_discard"

    def retain_cluster_lineage_leaders(self):
        """Keep only the most evolved forecast per narrative cluster."""
        from memory.cluster_mutation_tracker import (
            track_cluster_lineage,
            select_most_evolved
        )
        clusters = track_cluster_lineage(self._memory)
        leaders = select_most_evolved(clusters)
        self._memory = list(leaders.values())
        print(f"🔁 Memory compressed to most evolved forecast per cluster ({len(self._memory)} retained).")

    def _enforce_memory_limit(self) -> None:
        """Ensure memory does not exceed max_entries; prune oldest if needed."""
        if len(self._memory) > self.max_entries:
            self._memory = self._memory[-self.max_entries:]

    def _persist_to_file(self, forecast_obj: Dict) -> None:
        if not self.persist_dir:
            return
        import os, json
        # --- PATCH: Ensure overlays are serializable ---
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
        # --- END PATCH ---
        os.makedirs(self.persist_dir, exist_ok=True)
        forecast_id = forecast_obj.get("forecast_id", "unknown")
        path = os.path.join(self.persist_dir, f"{forecast_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            import json
            json.dump(forecast_obj, f, indent=2)

    def _load_from_files(self) -> None:
        import os, json
        if not os.path.isdir(self.persist_dir):
            return
        for fname in os.listdir(self.persist_dir):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(self.persist_dir, fname), "r", encoding="utf-8") as f:
                        self._memory.append(json.load(f))
                except Exception as e:
                    print(f"[ForecastMemory] Skipped corrupted file {fname}: {e}")

    def find_by_trace_id(self, trace_id: str) -> Optional[Dict]:
        """Find a forecast in memory by its trace_id or forecast_id."""
        for f in self._memory:
            if f.get("trace_id") == trace_id or f.get("forecast_id") == trace_id:
                return f
        return None
