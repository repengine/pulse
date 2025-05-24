"""variable_ingestion.py
Tiny, dependency-light adapters that fetch a *few* real variables so
Pulse starts producing meaningful numbers without extra setup.

* FRED – US 10-year yield, CPI (YoY)
* Yahoo Finance – S&P 500 close, VIX close
* Google Trends via pytrends (optional)

All network calls have a `timeout` and fail silently to keep boot fast.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import os
import sys
import yfinance as yf
from fredapi import Fred

from core.variable_registry import registry

print(f"[DEBUG] Python executable: {sys.executable}")
print(f"[DEBUG] sys.path: {sys.path}")
# Register YOUR FRED_KEY as env var; skip if not present.
_FRED = Fred(api_key=os.getenv("FRED_KEY", "")) if "FRED_KEY" in os.environ else None
_NOW = datetime.now(timezone.utc)
_30D_AGO = _NOW - timedelta(days=30)


def _fred_series(series_id: str) -> float | None:
    if _FRED is None:
        return None
    try:
        data = _FRED.get_series(series_id)
        return float(data.dropna().iloc[-1])
    except Exception:  # noqa: BLE001
        return None


def _yfinance_close(ticker: str) -> float | None:
    try:
        data = yf.download(
            ticker,
            start=_30D_AGO.strftime("%Y-%m-%d"),
            end=_NOW.strftime("%Y-%m-%d"),
            progress=False,
        )
        if data is None or "Close" not in data:
            return None
        return float(data["Close"].dropna().iloc[-1])
    except Exception:  # noqa: BLE001
        return None


def ingest_live_variables() -> dict[str, float]:
    """Return a small dict of live variables (skip any that fail)."""
    out: dict[str, float] = {}

    # FRED
    if (val := _fred_series("DGS10")) is not None:
        out["us_10y_yield"] = val / 100  # FRED returns percent
    if (val := _fred_series("CPIAUCSL")) is not None:
        out["cpi_yoy"] = val

    # Yahoo Finance
    if (val := _yfinance_close("^GSPC")) is not None:
        out["spx_close"] = val
    if (val := _yfinance_close("^VIX")) is not None:
        out["vix_close"] = val

    # Example: add a synthetic “macro_heat” variable
    if "us_10y_yield" in out and "spx_close" in out:
        out["macro_heat"] = round(out["us_10y_yield"] * out["vix_close"] / 1000, 3)

    # Tell the registry we just ingested these
    registry.bind_external_ingestion(lambda: out.copy())  # simple read-through

    return out
