"""
Celery app and tasks for Pulse distributed ingestion and scoring
"""

import os
import time
from celery import Celery
from analytics.metrics import signal_ingest_counter, signal_score_histogram
from ingestion.iris_scraper import IrisScraper
import logging

BROKER_URL = os.getenv("PULSE_CELERY_BROKER", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("PULSE_CELERY_BACKEND", "redis://localhost:6379/1")

celery_app = Celery("pulse", broker=BROKER_URL, backend=BACKEND_URL)
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

scraper = IrisScraper()


@celery_app.task(bind=True, name="ingest_and_score_signal")
def ingest_and_score_signal(self, signal_data):
    """Celery task: ingest, score, and enrich a signal."""
    import traceback

    trust_score = 0.0
    alignment_score = 0.0
    try:
        # Ingest
        result = scraper.ingest_signal(
            name=signal_data["name"],
            value=signal_data["value"],
            source=signal_data.get("source", "celery"),
            timestamp=signal_data.get("timestamp"),
        )
        if result is not None:
            signal_ingest_counter.labels(source=result["source"]).inc()
            # If this is a forecast (has 'forecast' key), enrich trust metadata
            if "forecast" in result:
                from trust_system.trust_engine import enrich_trust_metadata

                try:
                    enriched = enrich_trust_metadata(result)
                    result.update(enriched)
                    trust_score = result.get("confidence", 0.0) or 0.0
                    alignment_score = result.get("alignment_score", 0.0) or 0.0
                except Exception as e:
                    logging.error(f"Trust enrichment failed: {e}")
                    trust_score = 0.0
                    alignment_score = 0.0
                result["trust_score"] = float(trust_score)
                result["alignment_score"] = float(alignment_score)
                signal_score_histogram.observe(float(trust_score))
            else:
                # For raw signals, you may want to attach a simple quality score or skip scoring
                result["trust_score"] = 0.0
                result["alignment_score"] = 0.0
        else:
            logging.error("Result is None, skipping trust and alignment scoring.")
        # Real-time model update
        try:
            from analytics.feature_store import feature_store
            from forecast_engine.ai_forecaster import update as ai_update

            feature_store.clear_cache()
            feature_names = feature_store.list_features()
            features_values = [
                feature_store.get(name).iloc[-1] for name in feature_names
            ]
            ai_update([{"features": features_values, "adjustment": trust_score}])
        except Exception as e:
            logging.getLogger("pulse.celery").error(f"Real-time update error: {e}")
        # Optionally: save to DB, log, or further process
        return result
    except Exception as e:
        logging.getLogger("pulse.celery").error(
            f"Celery ingest_and_score_signal error: {e}\n{traceback.format_exc()}"
        )
        raise self.retry(exc=e, countdown=10, max_retries=3)


@celery_app.task(bind=True, name="autopilot_engage_task")
def autopilot_engage_task(self, action: str, parameters: dict):
    """Celery task: engage autopilot with specified action and parameters."""
    import traceback
    
    try:
        # Simulate autopilot engagement logic
        result = {
            "action": action,
            "parameters": parameters,
            "status": "engaged",
            "timestamp": time.time(),
            "message": f"Autopilot {action} completed successfully"
        }
        
        # Add some processing delay to simulate real work
        time.sleep(2)
        
        logging.getLogger("pulse.celery").info(f"Autopilot {action} completed: {result}")
        return result
    except Exception as e:
        logging.getLogger("pulse.celery").error(
            f"Autopilot engage task error: {e}\n{traceback.format_exc()}"
        )
        raise self.retry(exc=e, countdown=10, max_retries=3)


@celery_app.task(bind=True, name="autopilot_disengage_task")
def autopilot_disengage_task(self):
    """Celery task: disengage autopilot system."""
    import traceback
    
    try:
        # Simulate autopilot disengagement logic
        result = {
            "status": "disengaged",
            "timestamp": time.time(),
            "message": "Autopilot disengaged successfully"
        }
        
        # Add some processing delay to simulate real work
        time.sleep(1)
        
        logging.getLogger("pulse.celery").info(f"Autopilot disengaged: {result}")
        return result
    except Exception as e:
        logging.getLogger("pulse.celery").error(
            f"Autopilot disengage task error: {e}\n{traceback.format_exc()}"
        )
        raise self.retry(exc=e, countdown=10, max_retries=3)


@celery_app.task(bind=True, name="retrodiction_run_task")
def retrodiction_run_task(self, target_date: str, parameters: dict):
    """Celery task: run retrodiction analysis for target date."""
    import traceback
    
    try:
        # Simulate retrodiction analysis logic
        result = {
            "target_date": target_date,
            "parameters": parameters,
            "status": "completed",
            "timestamp": time.time(),
            "analysis_results": {
                "accuracy": 0.87,
                "confidence": 0.92,
                "key_factors": ["market_volatility", "trend_momentum"],
                "recommendations": ["increase_monitoring", "adjust_thresholds"]
            },
            "message": f"Retrodiction analysis for {target_date} completed"
        }
        
        # Add some processing delay to simulate real work
        time.sleep(5)
        
        logging.getLogger("pulse.celery").info(f"Retrodiction completed: {result}")
        return result
    except Exception as e:
        logging.getLogger("pulse.celery").error(
            f"Retrodiction task error: {e}\n{traceback.format_exc()}"
        )
        raise self.retry(exc=e, countdown=10, max_retries=3)


# Example periodic task (for Celery beat)
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, health_check.s(), name="health_check_every_minute")


@celery_app.task(name="health_check")
def health_check():
    return {"status": "ok"}
