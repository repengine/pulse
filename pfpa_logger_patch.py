"""
PATCHED: pfpa_logger.py
Pulse Version: v0.022.2
Fix: Portable symbolic_trace_scorer import regardless of local module packaging

Usage:
Run from root, CLI, or subdir. Auto-includes trace scoring from symbolic_trace_scorer.py.
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "pulse", "symbolic_system")))

from forecast_output.forecast_age_tracker import decay_confidence_and_priority
from trust_system.retrodiction_engine import retrodict_forecast
from symbolic_system.symbolic_trace_scorer import score_symbolic_trace
from typing import Dict, List
import datetime

# In-memory archive placeholder
PFPA_ARCHIVE: List[Dict] = []

def log_forecast_to_pfpa(forecast_obj: Dict, outcome: Dict = None, status: str = "open"):
    simulated_actual = {
        "nvda": 10100,
        "msft": 9800,
        "ibit": 5300,
        "spy": 9600
    }

    retrodicted = retrodict_forecast(forecast_obj, simulated_actual)

    symbolic_trace = forecast_obj.get("forecast", {}).get("symbolic_trace", [])
    symbolic_scoring = score_symbolic_trace(symbolic_trace) if symbolic_trace else {}

    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "trace_id": forecast_obj.get("trace_id"),
        "origin_turn": forecast_obj.get("origin_turn"),
        "horizon_days": forecast_obj.get("horizon_days"),
        "fragility": forecast_obj.get("fragility"),
        "confidence": forecast_obj.get("confidence"),
        "status": forecast_obj.get("status"),
        "trust_label": forecast_obj.get("trust_label", "🟡 Unlabeled"),
        "alignment": forecast_obj.get("alignment", {}),
        "symbolic_snapshot": forecast_obj["forecast"]["symbolic_change"],
        "symbolic_score": symbolic_scoring.get("symbolic_score"),
        "arc_label": symbolic_scoring.get("arc_label"),
        "arc_certainty": symbolic_scoring.get("arc_certainty"),
        "exposure_start": forecast_obj["forecast"]["start_capital"],
        "exposure_end": forecast_obj["forecast"]["end_capital"],
        "retrodiction_score": retrodicted["retrodiction_score"],
        "symbolic_hits": retrodicted["symbolic_hits"],
        "retrodiction_hits": retrodicted["asset_hits"],
        "outcome": outcome or {},
        "status_tag": status
    }

    forecast_obj = decay_confidence_and_priority(forecast_obj)
    PFPA_ARCHIVE.append(entry)

def get_latest_forecasts(n: int = 5) -> List[Dict]:
    return PFPA_ARCHIVE[-n:]
