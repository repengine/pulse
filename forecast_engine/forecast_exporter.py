import os
import csv
from forecast_engine.forecast_tracker import ForecastTracker
from utils.log_utils import get_logger
from engine.path_registry import PATHS

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

logger = get_logger(__name__)


def export_forecast_csv(
    output_file, log_dir=PATHS["FORECAST_HISTORY"], domain_filter=None
):
    tracker = ForecastTracker(log_dir)
    files = tracker.list_forecasts()

    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "Forecast ID",
                "Confidence",
                "Fragility",
                "Symbolic Trigger",
                "Timestamp",
                "Domain",
                "File",
            ]
        )

        for file in files:
            try:
                data = tracker.load_forecast(os.path.join(log_dir, file))
                meta = data.get("metadata", {})
                if domain_filter and meta.get("domain") != domain_filter:
                    continue
                writer.writerow(
                    [
                        data.get("forecast_id"),
                        meta.get("confidence", ""),
                        meta.get("fragility", ""),
                        meta.get("symbolic_trigger", ""),
                        data.get("timestamp"),
                        meta.get("domain", "unspecified"),
                        file,
                    ]
                )
            except Exception as e:
                logger.error(f"Failed to export {file}: {e}")


def export_forecast_markdown(
    output_file, log_dir=PATHS["FORECAST_HISTORY"], domain_filter=None
):
    tracker = ForecastTracker(log_dir)
    files = tracker.list_forecasts()

    with open(output_file, "w") as f:
        f.write("# 📊 Pulse Forecast Summary\n\n")
        for file in files:
            try:
                data = tracker.load_forecast(os.path.join(log_dir, file))
                meta = data.get("metadata", {})
                if domain_filter and meta.get("domain") != domain_filter:
                    continue
                f.write(f"## {data.get('forecast_id')}\n")
                f.write(f"- **Timestamp:** {data.get('timestamp')}\n")
                f.write(f"- **Confidence:** {meta.get('confidence', '-')}\n")
                f.write(f"- **Fragility:** {meta.get('fragility', '-')}\n")
                f.write(
                    f"- **Symbolic Trigger:** {meta.get('symbolic_trigger', '-')}\n"
                )
                f.write(f"- **Domain:** {meta.get('domain', 'unspecified')}\n")
                f.write(f"- **Source File:** `{file}`\n\n")
            except Exception as e:
                logger.error(f"Failed to export {file}: {e}")
