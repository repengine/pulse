"""
Database polling ingestion for Pulse (production-ready)
"""
import os
import time
import logging
from irldata.scraper import SignalScraper
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from core.celery_app import celery_app
from core.metrics import start_metrics_server
import threading

# Configurable via environment variables
DB_URL = os.getenv("PULSE_DB_URL", "sqlite:///pulse_signals.db")
POLL_INTERVAL = int(os.getenv("PULSE_DB_POLL_INTERVAL", "60"))
SIGNAL_QUERY = os.getenv(
    "PULSE_DB_QUERY",
    "SELECT id, name, value, source, timestamp FROM signals WHERE processed=0 ORDER BY id ASC"
)
MARK_PROCESSED_QUERY = os.getenv(
    "PULSE_DB_MARK_PROCESSED",
    "UPDATE signals SET processed=1 WHERE id=:id"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pulse.ingest_db")

def poll_database():
    # Start Prometheus metrics server in a background thread
    threading.Thread(target=start_metrics_server, daemon=True).start()
    scraper = SignalScraper()
    engine = create_engine(DB_URL)
    last_id = None
    logger.info(f"Polling database at {DB_URL} every {POLL_INTERVAL}s")
    while True:
        try:
            with engine.connect() as conn:
                result = conn.execute(text(SIGNAL_QUERY))
                rows = result.fetchall()
                for row in rows:
                    try:
                        # row: (id, name, value, source, timestamp)
                        signal_data = {
                            "name": row[1],
                            "value": row[2],
                            "source": row[3],
                            "timestamp": row[4]
                        }
                        celery_app.send_task("ingest_and_score_signal", args=[signal_data])
                        logger.info(f"Submitted to Celery from DB: {signal_data}")
                        conn.execute(text(MARK_PROCESSED_QUERY), {"id": row[0]})
                    except Exception as e:
                        logger.error(f"Failed to submit DB row to Celery: {e}")
            time.sleep(POLL_INTERVAL)
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("DB polling stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    poll_database()
