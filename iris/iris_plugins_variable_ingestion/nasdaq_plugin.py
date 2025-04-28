"""iris.iris_plugins_variable_ingestion.nasdaq_plugin
================================================================
Nasdaq Data Link (Quandl) ingestion plugin for Pulse IRIS.

* Expects `NASDAQ_API_KEY` in environment.
* Optional `NASDAQ_DL_DATASETS` env‑var (comma‑separated, default
  "WIKI/AAPL").
* Returns a list of *signal dictionaries* matching Iris schema so it
  can be registered with `IrisPluginManager` just like
  `finance_plugins()`.

Example
-------
```python
from iris.iris_plugins import IrisPluginManager
from iris.iris_plugins_variable_ingestion.nasdaq_plugin import nasdaq_plugin

mgr = IrisPluginManager()
mgr.register_plugin(nasdaq_plugin)
print(mgr.run_plugins())
```
"""
from __future__ import annotations

import datetime as _dt
import logging
import os
from typing import List, Dict, Any, Optional

import requests  # lightweight fallback instead of nasdaq‑data‑link SDK

logger = logging.getLogger(__name__)

_API_KEY: Optional[str] = os.getenv("NASDAQ_API_KEY")
_DATASET_LIST: List[str] = [code.strip() for code in os.getenv("NASDAQ_DL_DATASETS", "WIKI/AAPL").split(",") if code]

_BASE_URL = "https://data.nasdaq.com/api/v3/datasets/{code}.json"

def nasdaq_plugin() -> List[Dict[str, Any]]:
    """Entry point expected by *IrisPluginManager* (no args → List[Dict])."""
    if not _API_KEY:
        logger.warning("[nasdaq_plugin] NASDAQ_API_KEY not set — skipping fetch")
        return []

    signals: List[Dict[str, Any]] = []
    for code in _DATASET_LIST:
        if sig := _fetch_latest(code):
            signals.append(sig)
    return signals

def _fetch_latest(code: str) -> Optional[Dict[str, Any]]:
    """Return the latest observation for *dataset* `code`.

    Format returned by NASDAQ DL REST:  `[date, open, high, low, close, volume, …]`
    """
    url = _BASE_URL.format(code=code)
    params = {"api_key": _API_KEY, "rows": 1}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        payload = resp.json()["dataset"]
        latest = payload["data"][0]
        return {
            "source": "nasdaq_dl",
            "symbol": payload["dataset_code"],
            "timestamp": _dt.datetime.strptime(latest[0], "%Y-%m-%d").isoformat(),
            "value": float(latest[4]),  # close price
            "meta": {
                "open": float(latest[1]),
                "high": float(latest[2]),
                "low": float(latest[3]),
                "volume": float(latest[5]),
            },
        }
    except Exception as exc:  # noqa: broad-except — network/API errors are mapped to log + skip
        logger.error("[nasdaq_plugin] %s fetch failed: %s", code, exc)
        return None



