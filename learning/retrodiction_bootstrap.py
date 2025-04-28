'''
Retrodiction Starter Pipeline

- Pulls economic, market, environmental, technology, society, population, political variables
- Normalizes to weekly worldstate snapshots
- Outputs ready-to-load JSON for retrodiction into Pulse

Requirements:
    pip install yfinance fredapi pandas_datareader pytrends world_bank_data wikipedia-api beautifulsoup4 requests

Author: Pulse Development Project
'''

import os
import json
import time
import pandas as pd
import yfinance as yf
import pandas_datareader.data as web
from fredapi import Fred
from pytrends.request import TrendReq
import world_bank_data as wb
import wikipediaapi
import requests
from datetime import datetime

# --- Config ---
START_DATE = '2016-01-01'
END_DATE = '2023-12-31'
OUTPUT_FILE = 'worldstate_2016_2023.json'
FRED_API_KEY = os.getenv('FRED_API_KEY') or 'your_fred_api_key_here'
WORLDSTATE_TIMELINE = {}

# Initialize APIs
fred = Fred(api_key=FRED_API_KEY)
pytrends = TrendReq()
wikipedia = wikipediaapi.Wikipedia('en')

# --- Utility Functions ---
def daterange(start, end, freq='W'):
    dates = pd.date_range(start=start, end=end, freq=freq)
    return [d.strftime('%Y-%m-%d') for d in dates]

def safe_get(series, date):
    try:
        return series.loc[date]
    except KeyError:
        return None

def safe_yfinance(ticker, start, end):
    try:
        return yf.download(ticker, start=start, end=end, interval='1wk')
    except Exception as e:
        print(f"[WARN] Failed to fetch {ticker}: {e}")
        return pd.DataFrame()

# --- Data Pullers ---
def pull_fred_series(series_id):
    return fred.get_series(series_id, observation_start=START_DATE, observation_end=END_DATE)

def pull_yfinance_series(ticker):
    df = safe_yfinance(ticker, START_DATE, END_DATE)
    return df['Adj Close'] if 'Adj Close' in df.columns else pd.Series()

def pull_worldbank_indicator(indicator):
    try:
        df = wb.get_series(indicator, date=START_DATE[:4])
        return df
    except Exception as e:
        print(f"[WARN] World Bank pull failed for {indicator}: {e}")
        return pd.Series()

def pull_pytrends_term(term):
    try:
        pytrends.build_payload([term], timeframe=f"{START_DATE} {END_DATE}")
        df = pytrends.interest_over_time()
        return df[term] if term in df else pd.Series()
    except Exception as e:
        print(f"[WARN] Pytrends pull failed for {term}: {e}")
        return pd.Series()

def pull_wikipedia_events(year):
    page = wikipedia.page(f"{year}")
    if not page.exists():
        return []
    return page.text

# --- Main Worldstate Assembly ---
print("[INFO] Building worldstate...")
dates = daterange(START_DATE, END_DATE)
for date in dates:
    WORLDSTATE_TIMELINE[date] = {}

print("[INFO] Pulling economic variables...")
WORLDSTATE_TIMELINE = {
    date: {**WORLDSTATE_TIMELINE[date],
           'gdp_growth_rate': safe_get(pull_fred_series('GDP'), date),
           'inflation_rate': safe_get(pull_fred_series('CPIAUCSL'), date),
           'unemployment_rate': safe_get(pull_fred_series('UNRATE'), date)}
    for date in dates
}

print("[INFO] Pulling market variables...")
spx = pull_yfinance_series('^GSPC')
vix = pull_yfinance_series('^VIX')
gold = pull_yfinance_series('GC=F')
oil = pull_yfinance_series('CL=F')
for date in dates:
    WORLDSTATE_TIMELINE[date].update({
        'spx_index': safe_get(spx, date),
        'vix_index': safe_get(vix, date),
        'gold_price': safe_get(gold, date),
        'oil_price': safe_get(oil, date)
    })

print("[INFO] Pulling environmental variables...")
# Placeholder: Add OWID pulls or CSV loads here
for date in dates:
    WORLDSTATE_TIMELINE[date].update({
        'co2_ppm': None,
        'global_temp_anomaly': None
    })

print("[INFO] Pulling societal and tech variables...")
# Placeholder: Add World Bank, OECD indicators here
for date in dates:
    WORLDSTATE_TIMELINE[date].update({
        'education_index': None,
        'r_and_d_spending': None,
        'trust_in_science_score': None
    })

print("[INFO] Pulling population variables...")
# Placeholder: Add World Bank population pull
for date in dates:
    WORLDSTATE_TIMELINE[date].update({
        'global_population': None,
        'urbanization_rate': None
    })

print("[INFO] Pulling political variables...")
# Placeholder: Add Wikipedia scraping / Kaggle timeline loader
for date in dates:
    WORLDSTATE_TIMELINE[date].update({
        'global_democracy_index': None,
        'political_risk_events': None
    })

# --- Save ---
with open(OUTPUT_FILE, 'w') as f:
    json.dump(WORLDSTATE_TIMELINE, f, indent=2)

print(f"[SUCCESS] Worldstate saved to {OUTPUT_FILE}")

# --- CLI Runner ---
if __name__ == '__main__':
    print("\n[Runner Complete]")
    print(f"Worldstate Timeline covers {len(WORLDSTATE_TIMELINE)} snapshots.")
    print("Ready for Pulse Retrodiction Injection.")
