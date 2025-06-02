"""
HTTP API ingestion for Pulse using FastAPI (production-ready)
"""

import os
import logging
from ingestion.iris_scraper import IrisScraper
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from adapters.celery_app import celery_app
from analytics.metrics import start_metrics_server
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import threading

API_KEY = os.getenv("PULSE_API_KEY", "changeme")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pulse.ingest_api")

app = FastAPI()
scraper = IrisScraper()


class SignalIn(BaseModel):
    name: str
    value: float
    source: Optional[str] = "api"
    timestamp: Optional[str] = None


def get_api_key(request: Request):
    key = request.headers.get("x-api-key")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return True


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def startup_event():
    # Start Prometheus metrics server in a background thread
    threading.Thread(target=start_metrics_server, daemon=True).start()


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/ingest", dependencies=[Depends(get_api_key)])
async def ingest_signal(signal: SignalIn):
    try:
        celery_app.send_task("ingest_and_score_signal", args=[signal.dict()])
        logger.info(f"Submitted to Celery: {signal.dict()}")
        return {"status": "submitted"}
    except Exception as e:
        logger.error(f"API ingest error for signal {signal.dict()}: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error": str(e), "signal": signal.dict()},
        )


@app.post("/ingest_batch", dependencies=[Depends(get_api_key)])
async def ingest_batch(signals: List[SignalIn]):
    results = []
    for signal in signals:
        try:
            celery_app.send_task("ingest_and_score_signal", args=[signal.dict()])
            results.append({"name": signal.name, "status": "submitted"})
        except Exception as e:
            logger.error(f"Batch ingest error for signal {signal.dict()}: {e}")
            results.append(
                {
                    "name": signal.name,
                    "status": "error",
                    "error": str(e),
                    "signal": signal.dict(),
                }
            )
    return {"results": results}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
