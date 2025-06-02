"""
S3 bucket monitoring ingestion for Pulse (production-ready)
"""

import os
import time
import json
import logging
import csv
import boto3
from adapters.celery_app import celery_app
from analytics.metrics import start_metrics_server
import threading

S3_BUCKET = os.getenv("PULSE_S3_BUCKET", "your-bucket-name")
S3_PREFIX = os.getenv("PULSE_S3_PREFIX", "")
S3_PROCESSED_PREFIX = os.getenv("PULSE_S3_PROCESSED_PREFIX", "processed/")
POLL_INTERVAL = int(os.getenv("PULSE_S3_POLL_INTERVAL", "60"))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pulse.ingest_s3")


def poll_s3():
    # Start Prometheus metrics server in a background thread
    threading.Thread(target=start_metrics_server, daemon=True).start()
    s3 = boto3.client("s3")
    seen = set()
    logger.info(f"Polling S3 bucket '{S3_BUCKET}' every {POLL_INTERVAL}s")
    while True:
        try:
            response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_PREFIX)
            for obj in response.get("Contents", []):
                key = obj["Key"]
                if key in seen or not (key.endswith(".json") or key.endswith(".csv")):
                    continue
                try:
                    file_obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
                    body = file_obj["Body"].read().decode("utf-8")
                    if key.endswith(".json"):
                        data = json.loads(body)
                        celery_app.send_task("ingest_and_score_signal", args=[data])
                        logger.info(f"Submitted to Celery from S3 JSON: {key}")
                    elif key.endswith(".csv"):
                        import io

                        reader = csv.DictReader(io.StringIO(body))
                        for row in reader:
                            celery_app.send_task("ingest_and_score_signal", args=[row])
                            logger.info(f"Submitted row to Celery from S3 CSV: {row}")
                    # Move file to processed folder
                    dest_key = S3_PROCESSED_PREFIX + os.path.basename(key)
                    s3.copy_object(
                        Bucket=S3_BUCKET,
                        CopySource={"Bucket": S3_BUCKET, "Key": key},
                        Key=dest_key,
                    )
                    s3.delete_object(Bucket=S3_BUCKET, Key=key)
                    logger.info(f"Archived S3 file to: {dest_key}")
                    seen.add(key)
                except Exception as e:
                    logger.error(f"S3 ingestion error for {key}: {e}")
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("S3 polling stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected S3 error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    poll_s3()
