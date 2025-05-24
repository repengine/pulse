"""
IngestionService
----------------
Thin OO wrapper around run_ingest.py logic so it can be:
* imported by main.py for just-in-time data
* executed as `python -m ingestion_service --once`
"""

from iris.iris_scraper import IrisScraper
from typing import Dict, List


class IngestionService:
    def __init__(self) -> None:
        self.scraper = IrisScraper()
        # auto-load all default IRIS ingestion plugins
        self.scraper.plugin_manager.autoload()

    # ── public API ────────────────────────────────────────────────────
    def ingest_once(self) -> str:
        """Hit every plugin once, export JSONL, return file path."""
        self.scraper.batch_ingest_from_plugins()
        return self.scraper.export_signal_log()

    def latest_signals(self) -> List[Dict]:
        """Return the list of Signal Dicts collected in the last run."""
        return getattr(self.scraper, "signal_log", [])


# ---------------------------------------------------------------------
# Optional CLI so you can still run:  `python -m ingestion_service --once`
if __name__ == "__main__":
    import argparse
    import sys
    import json

    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true", help="Ingest once and exit")
    args = p.parse_args()

    svc = IngestionService()
    if args.once:
        out = svc.ingest_once()
        print("✅ Signals exported to", out)
        sys.exit(0)

    # fall-back: output signals to stdout (for quick debugging)
    svc.ingest_once()
    print(json.dumps(svc.latest_signals()[:5], indent=2))
