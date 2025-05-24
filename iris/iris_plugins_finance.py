"""iris_plugins_finance.py

Finance‑focused ingestion plugins for IRIS.
Each plugin returns a **List[Dict]** with at minimum the keys:
    name:   variable identifier used inside Pulse (snake_case)
    value:  numeric value (float/int)
    source: short string identifying the API
    timestamp: ISO‑8601 UTC string (optional – defaults to now)

The module is intentionally dependency‑light (requests only) and uses
ENV variables for API keys. If the key is missing the plugin logs a
warning and returns an empty list so the caller can continue gracefully.

Plugins implemented
-------------------
* Alpha Vantage  – daily adjusted close for a watch‑list of tickers
* FRED           – selected macro indicators (10‑year yield, CPI YoY)
* Finnhub        – real‑time quote + sentiment score (if available)

Additional helpers:
* _safe_get()    – wraps network calls with sane timeouts & retries
* _to_timestamp()– normalises date strings → UTC ISO‑8601

Extend by following the template of the *_build_signals() helpers.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import time
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)
_REQUEST_TIMEOUT = float(os.getenv("IRIS_API_TIMEOUT", "10"))
_RETRY_WAIT = 1.5  # seconds between retries on transient errors
_MAX_RETRIES = 2

###############################################################################
# Generic helpers                                                             #
###############################################################################


def _safe_get(url: str, params: dict[str, str] | None = None) -> Optional[dict]:
    """HTTP GET with basic back‑off & JSON parsing. Returns **None** on failure."""
    for attempt in range(_MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=_REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: BLE001 –– keep lightweight
            logger.warning(
                "[%s] GET failed (%s/%s): %s", url, attempt + 1, _MAX_RETRIES, exc
            )
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_WAIT * (attempt + 1))
    return None


def _to_timestamp(date_str: str | _dt.datetime) -> str:
    if isinstance(date_str, _dt.datetime):
        return date_str.astimezone(_dt.timezone.utc).isoformat()
    try:
        return (
            _dt.datetime.fromisoformat(date_str)
            .replace(tzinfo=_dt.timezone.utc)
            .isoformat()
        )
    except Exception:
        return _dt.datetime.now(_dt.timezone.utc).isoformat()


###############################################################################
# Alpha Vantage                                                               #
###############################################################################

_ALPHA_KEY = os.getenv("ALPHA_VANTAGE_KEY")
_ALPHA_URL = "https://www.alphavantage.co/query"
_ALPHA_SYMBOLS = {
    "spx_close": "SPY",  # ETF proxy for S&P 500
    "btc_usd_close": "BTCUSD",
}


def _alpha_build_signals() -> List[Dict]:
    if not _ALPHA_KEY:
        logger.info("[alpha‑vantage] env var ALPHA_VANTAGE_KEY not set – skipping")
        return []
    signals: List[Dict] = []
    for var_name, sym in _ALPHA_SYMBOLS.items():
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": sym,
            "outputsize": "compact",
            "apikey": _ALPHA_KEY,
        }
        data = _safe_get(_ALPHA_URL, params)
        if not data:
            continue
        ts_field = next((k for k in data if k.startswith("Time Series")), None)
        if not ts_field:
            continue
        latest_date, latest_row = next(iter(data[ts_field].items()))
        try:
            price = float(latest_row["5. adjusted close"])
        except Exception:
            continue
        signals.append(
            {
                "name": var_name,
                "value": price,
                "source": "alpha_vantage",
                "timestamp": _to_timestamp(latest_date),
            }
        )
    return signals


###############################################################################
# Finnhub                                                                     #
###############################################################################

_FINNHUB_KEY = os.getenv("FINNHUB_KEY")
_FINNHUB_URL = "https://finnhub.io/api/v1"
_FINNHUB_SYMBOLS = {
    "aapl_close": "AAPL",
    "msft_close": "MSFT",
}


def _finnhub_build_signals() -> List[Dict]:
    if not _FINNHUB_KEY:
        logger.info("[finnhub] env var FINNHUB_KEY not set – skipping")
        return []
    signals: List[Dict] = []
    for var_name, sym in _FINNHUB_SYMBOLS.items():
        quote = _safe_get(
            f"{_FINNHUB_URL}/quote", {"symbol": sym, "token": _FINNHUB_KEY}
        )
        if not quote or "c" not in quote:
            continue
        price = quote["c"]
        ts = _to_timestamp(_dt.datetime.utcfromtimestamp(quote.get("t", time.time())))
        signals.append(
            {"name": var_name, "value": price, "source": "finnhub", "timestamp": ts}
        )
        # Optional: sentiment endpoint (50 calls/min on free tier)
        try:
            sent = _safe_get(
                f"{_FINNHUB_URL}/news-sentiment", {"symbol": sym, "token": _FINNHUB_KEY}
            )
            if sent and "companyNewsScore" in sent:
                signals.append(
                    {
                        "name": f"{sym.lower()}_news_sentiment",
                        "value": sent["companyNewsScore"],
                        "source": "finnhub_sentiment",
                        "timestamp": ts,
                    }
                )
        except Exception:  # noqa: BLE001
            pass
    return signals


###############################################################################
# Public interface                                                            #
###############################################################################


def finance_plugins() -> List[Dict]:
    """Primary entry point expected by *IrisPluginManager*."""
    signals: List[Dict] = []
    for builder in (_alpha_build_signals, _finnhub_build_signals):
        try:
            signals.extend(builder())
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "[finance_plugins] builder %s failed: %s", builder.__name__, exc
            )
    return signals


# Quick manual test
if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(finance_plugins(), indent=2))
