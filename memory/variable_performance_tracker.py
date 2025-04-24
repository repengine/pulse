"""
diagnostics.variable_performance_tracker.py

Tracks and scores the impact of individual variables on simulation outcomes,
trust scores, symbolic fragility, and long-term forecast quality.

Supports:
- Logging per-forecast variable contributions
- Aggregating trust/fragility outcomes per variable
- Drift detection and symbolic volatility analysis
- Export for audit, dashboard, and meta-learning use

Author: Pulse v0.29
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from core.path_registry import PATHS
from core.variable_registry import VARIABLE_REGISTRY
from core.pulse_learning_log import log_learning_event

LOG_PATH = PATHS.get("VARIABLE_SCORE_LOG", "logs/variable_score_log.jsonl")
SCORE_EXPORT_PATH = PATHS.get("VARIABLE_SCORE_EXPORT", "logs/variable_score_summary.json")

class VariablePerformanceTracker:
    def __init__(self):
        self.records: List[Dict] = []
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    def aggregate_from_memory(self, memory):
        """
        Optionally aggregate variable contributions from a ForecastMemory instance or list.
        """
        if hasattr(memory, "_memory"):
            forecasts = memory._memory
        else:
            forecasts = memory
        for forecast in forecasts:
            state = forecast.get("input_state", {})
            self.log_variable_contribution(forecast, state)

    def log_variable_contribution(self, forecast: Dict, state: Dict):
        """
        Logs how each variable in a forecast worldstate contributed to the outcome.
        """
        for var, val in state.items():
            if var not in VARIABLE_REGISTRY:
                continue
            self.records.append({
                "timestamp": datetime.utcnow().isoformat(),
                "variable": var,
                "value": val,
                "trace_id": forecast.get("trace_id", "unknown"),
                "confidence": forecast.get("confidence", 0),
                "fragility": forecast.get("fragility", 0),
                "certified": forecast.get("certified", False),
                "arc_label": forecast.get("arc_label"),
                "symbolic_tag": forecast.get("symbolic_tag"),
                "alignment_score": forecast.get("alignment_score"),
                "confidence_status": forecast.get("confidence_status"),
            })

        with open(LOG_PATH, "a", encoding="utf-8") as f:
            for r in self.records[-len(state):]:
                f.write(json.dumps(r) + "\n")

    def score_variable_effectiveness(self) -> Dict[str, Dict]:
        """
        Aggregates trust/fragility impact per variable.
        """
        scores = {}
        for rec in self.records:
            var = rec["variable"]
            if var not in scores:
                scores[var] = {
                    "count": 0,
                    "avg_confidence": 0.0,
                    "avg_fragility": 0.0,
                    "certified_count": 0,
                    "sum_alignment": 0.0,
                }
            scores[var]["count"] += 1
            scores[var]["avg_confidence"] += rec.get("confidence", 0)
            scores[var]["avg_fragility"] += rec.get("fragility", 0)
            scores[var]["sum_alignment"] += rec.get("alignment_score", 0)
            if rec.get("certified"):
                scores[var]["certified_count"] += 1

        for var, data in scores.items():
            c = data["count"]
            if c:
                data["avg_confidence"] = round(data["avg_confidence"] / c, 4)
                data["avg_fragility"] = round(data["avg_fragility"] / c, 4)
                data["avg_alignment"] = round(data["sum_alignment"] / c, 4)
                data["certified_ratio"] = round(data["certified_count"] / c, 4)
                del data["sum_alignment"]

        return scores

    def rank_variables_by_impact(self, key: str = "avg_confidence") -> List[str]:
        scored = self.score_variable_effectiveness()
        return sorted(scored.keys(), key=lambda k: scored[k].get(key, 0), reverse=True)

    def export_variable_scores(self, path: Optional[str] = None):
        summary = self.score_variable_effectiveness()
        export_path = path or SCORE_EXPORT_PATH
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            print(f"✅ Variable scores exported to {export_path}")
        except Exception as e:
            print(f"❌ Failed to export variable scores: {e}")

    def detect_variable_drift(self, threshold: float = 0.25) -> List[str]:
        """
        Flags variables with high fragility or low certified ratio.
        """
        outliers = []
        scores = self.score_variable_effectiveness()
        for var, stat in scores.items():
            if stat.get("avg_fragility", 0) > threshold or stat.get("certified_ratio", 1) < (1 - threshold):
                outliers.append(var)
        return outliers

    def update_performance(self, var_name, new_score):
        """
        Updates the performance of a variable and logs the learning event.
        """
        log_learning_event("memory_update", {
            "event": "variable_performance_update",
            "variable": var_name,
            "new_score": new_score,
            "timestamp": datetime.utcnow().isoformat()
        })

# === Example CLI usage
if __name__ == "__main__":
    tracker = VariablePerformanceTracker()
    dummy_forecast = {"trace_id": "vtest1", "confidence": 0.78, "fragility": 0.22, "certified": True, "arc_label": "Hope", "symbolic_tag": "hope"}
    dummy_state = {"hope": 0.6, "rage": 0.4, "vix_level": 0.28, "crypto_instability": 0.6}
    tracker.log_variable_contribution(dummy_forecast, dummy_state)
    print("Ranked variables:", tracker.rank_variables_by_impact())
    print("Drift-prone:", tracker.detect_variable_drift())
    tracker.export_variable_scores()
