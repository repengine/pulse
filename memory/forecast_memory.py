"""
forecast_memory.py

Stores and retrieves recent or historical forecasts during simulation.
Supports symbolic tagging, replay, and integration with PFPA trust scoring.

Author: Pulse v3.5
"""

from typing import List, Dict, Optional


class ForecastMemory:
    """
    In-memory forecast storage layer.
    Extendable to persistent storage in v4.0+.
    """

    def __init__(self):
        self._memory: List[Dict] = []

    def store(self, forecast_obj: Dict):
        """
        Adds a forecast object to memory.
        """
        self._memory.append(forecast_obj)

    def get_recent(self, n: int = 5) -> List[Dict]:
        """
        Retrieves the N most recent forecasts.
        """
        return self._memory[-n:]

    def get_by_trace_id(self, trace_id: str) -> Optional[Dict]:
        """
        Retrieves a forecast by its unique trace ID.
        """
        for f in reversed(self._memory):
            if f.get("trace_id") == trace_id:
                return f
        return None

    def get_by_symbolic_condition(self, key: str, threshold: float = 0.5) -> List[Dict]:
        """
        Retrieves forecasts where a symbolic overlay condition was met.
        E.g., get all where Hope > 0.7 at time of forecast.
        """
        results = []
        for f in self._memory:
            symbolic = f.get("forecast", {}).get("symbolic_change", {})
            if symbolic.get(key, 0) > threshold:
                results.append(f)
        return results

    def clear(self):
        """
        Clears forecast memory (used in reset or export filtering).
        """
        self._memory.clear()
