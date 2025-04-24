"""
Celery app and tasks for Pulse distributed ingestion and scoring
"""
import os
from celery import Celery
from core.pulse_config import get_config
from core.metrics import signal_ingest_counter, signal_score_histogram
from irldata.scraper import SignalScraper
import logging

BROKER_URL = os.getenv("PULSE_CELERY_BROKER", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("PULSE_CELERY_BACKEND", "redis://localhost:6379/1")

celery_app = Celery("pulse", broker=BROKER_URL, backend=BACKEND_URL)
celery_app.conf.update(task_track_started=True, task_serializer="json", result_serializer="json", accept_content=["json"])

scraper = SignalScraper()

@celery_app.task(bind=True, name="ingest_and_score_signal")
def ingest_and_score_signal(self, signal_data):
    """Celery task: ingest, score, and enrich a signal."""
    import time
    import traceback
    from trust_system.trust_engine import TrustEngine
    from trust_system.alignment_index import compute_alignment_index
    try:
        # Ingest
        result = scraper.ingest_signal(
            name=signal_data["name"],
            value=signal_data["value"],
            source=signal_data.get("source", "celery"),
            timestamp=signal_data.get("timestamp")
        )
        signal_ingest_counter.labels(source=result["source"]).inc()
        # Score
        trust_score = None
        alignment_score = None
        try:
            trust_score = TrustEngine().score(result)
        except Exception:
            trust_score = None
        try:
            alignment_score = compute_alignment_index(result)["alignment_score"]
        except Exception:
            alignment_score = None
        result["trust_score"] = trust_score
        result["alignment_score"] = alignment_score
        signal_score_histogram.observe(trust_score or 0)
        # Optionally: save to DB, log, or further process
        return result
    except Exception as e:
        logging.error(f"Celery ingest_and_score_signal error: {e}\n{traceback.format_exc()}")
        raise self.retry(exc=e, countdown=10, max_retries=3)

# Example periodic task (for Celery beat)
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from datetime import timedelta
    sender.add_periodic_task(60.0, health_check.s(), name="health_check_every_minute")

@celery_app.task(name="health_check")
def health_check():
    return {"status": "ok"}
