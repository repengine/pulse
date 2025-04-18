"""
forecast_memory.py

Stores and retrieves recent or historical forecasts during simulation.
Supports symbolic tagging, replay, and integration with PFPA trust scoring.

Author: Pulse v3.5
"""

import os
import json
from typing import List, Dict, Optional


class ForecastMemory:
    """
    Unified forecast storage and retrieval.
    """

    def __init__(self, persist_dir: Optional[str] = None):
        self._memory: List[Dict] = []
        self.persist_dir = persist_dir
        if persist_dir:
            self._load_from_files()

    def store(self, forecast_obj: Dict):
        """
        Adds a forecast object to memory and persists to file.
        """
        self._memory.append(forecast_obj)
        if self.persist_dir:
            self._persist_to_file(forecast_obj)

    def get_recent(self, n: int = 10, domain: Optional[str] = None) -> List[Dict]:
        """
        Retrieves the N most recent forecasts, optionally filtered by domain.
        """
        results = self._memory[-n:]
        if domain:
            results = [r for r in results if r.get("domain") == domain]
        return results

    def update_trust(self, forecast_id: str, trust_data: Dict):
        """
        Updates trust/scoring info for a forecast by ID.
        """
        for f in self._memory:
            if f.get("forecast_id") == forecast_id:
                f.update(trust_data)
                if self.persist_dir:
                    self._persist_to_file(f)
                break

    def clear(self):
        """
        Clears forecast memory (used in reset or export filtering).
        """
        self._memory = []

    def _persist_to_file(self, forecast_obj: Dict):
        """
        Persists a forecast object to a file.
        """
        if not self.persist_dir:
            return
        os.makedirs(self.persist_dir, exist_ok=True)
        forecast_id = forecast_obj.get("forecast_id", "unknown")
        path = os.path.join(self.persist_dir, f"{forecast_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(forecast_obj, f, indent=2)

    def _load_from_files(self):
        """
        Loads forecast objects from files in the persist directory.
        """
        if not os.path.isdir(self.persist_dir):
            return
        for fname in os.listdir(self.persist_dir):
            if fname.endswith(".json"):
                with open(os.path.join(self.persist_dir, fname), "r", encoding="utf-8") as f:
                    self._memory.append(json.load(f))
