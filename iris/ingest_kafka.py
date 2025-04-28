"""
Kafka consumer ingestion for Pulse (production-ready)
"""
import os
import json
import logging
from iris.iris_scraper import IrisScraper
from kafka import KafkaConsumer, errors as kafka_errors
from core.celery_app import celery_app
from core.metrics import start_metrics_server
import threading

# Configurable via environment variables or defaults
KAFKA_TOPIC = os.getenv("PULSE_KAFKA_TOPIC", "pulse_signals")
KAFKA_BOOTSTRAP = os.getenv("PULSE_KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_GROUP = os.getenv("PULSE_KAFKA_GROUP", "pulse_ingest_group")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pulse.ingest_kafka")

def run_kafka_ingestion():
    # Start Prometheus metrics server in a background thread
    threading.Thread(target=start_metrics_server, daemon=True).start()
    scraper = IrisScraper()
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            group_id=KAFKA_GROUP,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            consumer_timeout_ms=10000
        )
        logger.info(f"Connected to Kafka topic '{KAFKA_TOPIC}' at {KAFKA_BOOTSTRAP}")
    except kafka_errors.NoBrokersAvailable:
        logger.error("No Kafka brokers available. Check KAFKA_BOOTSTRAP.")
        return
    except Exception as e:
        logger.error(f"Kafka connection error: {e}")
        return

    while True:
        try:
            for message in consumer:
                data = message.value
                if not isinstance(data, dict):
                    logger.warning(f"Malformed message: {data}")
                    continue
                try:
                    celery_app.send_task("ingest_and_score_signal", args=[data])
                    logger.info(f"Submitted to Celery from Kafka: {data}")
                except Exception as e:
                    logger.error(f"Failed to submit to Celery: {e}")
        except kafka_errors.KafkaError as e:
            logger.error(f"Kafka error: {e}. Reconnecting...")
            try:
                consumer.close()
            except Exception:
                pass
            import time
            time.sleep(5)
            return run_kafka_ingestion()
        except KeyboardInterrupt:
            logger.info("Kafka ingestion stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

if __name__ == '__main__':
    run_kafka_ingestion()
