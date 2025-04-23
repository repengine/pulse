import json
from typing import List, Dict, Any
from memory.forecast_memory import ForecastMemory

class ForecastMemory:
    def __init__(self):
        self._memory: List[Dict[str, Any]] = []

    def add_forecast(self, forecast: Dict[str, Any]):
        """Add a forecast to memory."""
        self._memory.append(forecast)

    def store(self, forecast: Dict[str, Any]):
        """Alias for add_forecast, for compatibility with promoter and other modules."""
        self.add_forecast(forecast)

    def get_all_forecasts(self) -> List[Dict[str, Any]]:
        """Retrieve all forecasts from memory."""
        return self._memory

    def isolate_revision_candidates(self) -> List[Dict[str, Any]]:
        """Return all forecasts marked for symbolic tuning."""
        return [f for f in self._memory if f.get("revision_candidate")]

    def export_revision_candidates(self, path: str):
        """Save revision targets for symbolic tuning loop."""
        try:
            candidates = self.isolate_revision_candidates()
            with open(path, "w") as f:
                for fc in candidates:
                    f.write(json.dumps(fc) + "\n")
            print(f"✅ Exported {len(candidates)} symbolic revision candidates to {path}")
        except Exception as e:
            print(f"❌ Failed to export revisions: {e}")

    def clear(self):
        """Clear all forecasts from memory."""
        self._memory.clear()

def _test_forecast_memory():
    mem = ForecastMemory()
    mem.add_forecast({"revision_candidate": True, "id": 1})
    mem.add_forecast({"revision_candidate": False, "id": 2})
    assert len(mem.isolate_revision_candidates()) == 1
    mem.clear()
    assert len(mem.get_all_forecasts()) == 0
    print("✅ ForecastMemory test passed.")

if __name__ == "__main__":
    _test_forecast_memory()