""" 
forecast_tracker.py

Tracks, scores, and validates Pulse simulation forecasts.
Forecasts are logged to /forecast_output/ if trusted, and optionally archived to memory.
Now also attaches detailed rule audit logs to each saved forecast.

Author: Pulse v0.20
"""

import os
import json
from datetime import datetime
from forecast_engine.forecast_scoring import score_forecast
from forecast_engine.forecast_memory import save_forecast_to_memory
from forecast_engine.forecast_integrity_engine import validate_forecast
from simulation_engine.worldstate import WorldState


class ForecastTracker:
    def __init__(self, log_dir="forecast_output"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def _generate_filename(self, forecast_id: str) -> str:
        safe_id = forecast_id.replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.log_dir, f"{safe_id}_{timestamp}.json")

    def record_forecast(self, forecast_id: str, state: WorldState, rule_log: list[dict], domain: str = None):
        """
        Scores, validates, and records a forecast if trusted.

        Args:
            forecast_id (str): Unique identifier
            state (WorldState): The simulation state
            rule_log (list): Executed rules + audit logs
            domain (str): Optional domain tag (e.g., 'capital', 'sports')
        """

        metadata = score_forecast(state, rule_log)
        metadata["rule_audit"] = rule_log  # <-- attach audit log

        if not validate_forecast(metadata, required_keys=["confidence", "symbolic_driver"]):
            print(f"⛔ Forecast rejected (low trust): {forecast_id}")
            return None

        filepath = self._generate_filename(forecast_id)

        data = {
            "forecast_id": forecast_id,
            "timestamp": datetime.now().isoformat(),
            "state_snapshot": state.snapshot(),
            "metadata": metadata,
            "domain": domain
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        save_forecast_to_memory(forecast_id, metadata=metadata, domain=domain)
        print(f"✅ Forecast recorded: {forecast_id}")
        return filepath

    def load_forecast(self, filepath: str) -> dict:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Forecast file not found: {filepath}")
        with open(filepath, 'r') as f:
            return json.load(f)

    def list_forecasts(self) -> list:
        return sorted([
            f for f in os.listdir(self.log_dir) if f.endswith(".json")
        ])