"""
File system monitoring ingestion for Pulse (production-ready)
"""

import os
import time
import json
import shutil
import logging
import csv
from ingestion.iris_scraper import IrisScraper
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from adapters.celery_app import celery_app
from analytics.metrics import start_metrics_server
import threading

MONITOR_DIR = os.getenv("PULSE_FS_MONITOR_DIR", "data/incoming")
ARCHIVE_DIR = os.getenv("PULSE_FS_ARCHIVE_DIR", "data/ingested")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pulse.ingest_fs")


class SignalFileHandler(FileSystemEventHandler):
    def __init__(self, scraper):
        self.scraper = scraper
        os.makedirs(ARCHIVE_DIR, exist_ok=True)

    def on_created(self, event):
        if event.is_directory:
            return
        ext = os.path.splitext(event.src_path)[1].lower()
        try:
            if ext == ".json":
                with open(event.src_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    celery_app.send_task("ingest_and_score_signal", args=[data])
                    logger.info(f"Submitted to Celery from file: {event.src_path}")
            elif ext == ".csv":
                with open(event.src_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        celery_app.send_task("ingest_and_score_signal", args=[row])
                        logger.info(f"Submitted row to Celery from CSV: {row}")
            else:
                logger.warning(f"Unsupported file type: {event.src_path}")
                return
            # Move file to archive after successful ingestion
            base = os.path.basename(event.src_path)
            archive_path = os.path.join(ARCHIVE_DIR, base)
            shutil.move(event.src_path, archive_path)
            logger.info(f"Archived file to: {archive_path}")
        except Exception as e:
            logger.error(f"File ingestion error for {event.src_path}: {e}")


def monitor_directory(path=MONITOR_DIR):
    # Start Prometheus metrics server in a background thread
    threading.Thread(target=start_metrics_server, daemon=True).start()
    scraper = IrisScraper()
    event_handler = SignalFileHandler(scraper)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    logger.info(f"Monitoring directory: {path}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    monitor_directory()
