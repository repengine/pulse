from memory.forecast_memory import ForecastMemory
from core.path_registry import PATHS

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"


def test_store_and_retrieve():
    fm = ForecastMemory(persist_dir=PATHS["FORECAST_HISTORY"])
    test_obj = {"forecast_id": "test123", "confidence": 0.9}
    fm.store(test_obj)
    recent = fm.get_recent(1)
    assert recent and recent[0]["forecast_id"] == "test123"
