import os
import json
from tabulate import tabulate
from simulation_engine.forecasting.forecast_tracker import ForecastTracker
from utils.log_utils import get_logger

logger = get_logger(__name__)

def load_and_display_forecasts(log_dir="forecast_output", top_n=5, sort_by="confidence", domain_filter=None):
    tracker = ForecastTracker(log_dir=log_dir)
    files = tracker.list_forecasts()

    summaries = []
    for file in files:
        path = os.path.join(log_dir, file)
        try:
            data = tracker.load_forecast(path)
            meta = data.get("metadata", {})
            entry = {
                "forecast_id": data.get("forecast_id"),
                "confidence": meta.get("confidence", "-"),
                "fragility": meta.get("fragility", "-"),
                "symbolic_trigger": meta.get("symbolic_trigger", "-"),
                "timestamp": data.get("timestamp"),
                "domain": meta.get("domain", "unspecified"),
                "file": file
            }
            if domain_filter is None or entry["domain"] == domain_filter:
                summaries.append(entry)
        except Exception as e:
            logger.warning(f"Could not load {file}: {e}")

    summaries = sorted(summaries, key=lambda x: x.get(sort_by, 0), reverse=True)

    if summaries:
        try:
            avg_conf = sum(float(s["confidence"]) for s in summaries if s["confidence"] not in ("-", None)) / len(summaries)
            avg_frag = sum(float(s["fragility"]) for s in summaries if s["fragility"] not in ("-", None)) / len(summaries)
            print(f"\n📈 Summary — Total: {len(summaries)} | Avg Confidence: {avg_conf:.2f} | Avg Fragility: {avg_frag:.2f}")
        except Exception:
            pass

    print(f"\n🔎 Loaded {len(summaries)} forecasts (domain: {domain_filter or 'any'})")
    print(tabulate(summaries[:top_n], headers="keys", tablefmt="fancy_grid"))