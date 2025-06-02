from datetime import datetime, timezone
from ingestion.variable_ingestion import ingest_live_variables


def vi_plugin():
    ts = datetime.now(timezone.utc)  # <-- keep as datetime, no isoformat()
    return [
        {
            "name": k,
            "value": v,
            "source": "variable_ingestion",
            "timestamp": ts,  # <-- datetime object
        }
        for k, v in ingest_live_variables().items()
    ]
