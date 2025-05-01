"""Alpha Vantage API — finance plugin.

Connects to Alpha Vantage API for financial market data including:
- Daily stock prices
- Forex rates
- Crypto prices
- Economic indicators

Requires ALPHA_VANTAGE_KEY environment variable.
"""
import datetime as dt
import logging
import os
import time
from typing import Dict, List, Any, Optional

import requests
from iris.iris_plugins import IrisPluginManager

logger = logging.getLogger(__name__)

class AlphaVantagePlugin(IrisPluginManager):
    plugin_name = "alpha_vantage_plugin"
    enabled = True     # Plugin is active when API key is available
    concurrency = 2     # Limit concurrent requests to avoid rate limiting

    # Alpha Vantage API configuration
    BASE_URL = "https://www.alphavantage.co/query"
    REQUEST_TIMEOUT = 10.0
    RETRY_WAIT = 1.5  # seconds between retries
    MAX_RETRIES = 2

    # Symbol definitions: Pulse variable name → Alpha Vantage symbol
    STOCK_SYMBOLS = {
        "aapl_price": "AAPL",      # Apple Inc.
        "msft_price": "MSFT",      # Microsoft Corporation
        "googl_price": "GOOGL",    # Alphabet Inc.
        "amzn_price": "AMZN",      # Amazon.com Inc.
        "meta_price": "META",      # Meta Platforms Inc.
        "tsla_price": "TSLA",      # Tesla Inc.
        "nvda_price": "NVDA",      # NVIDIA Corporation
        "spy_price": "SPY",        # SPDR S&P 500 ETF (proxy for S&P 500)
    }
    
    CRYPTO_SYMBOLS = {
        "btc_usd": "BTCUSD",      # Bitcoin/USD
        "eth_usd": "ETHUSD",      # Ethereum/USD
        "sol_usd": "SOLUSD",      # Solana/USD
    }
    
    FOREX_SYMBOLS = {
        "eur_usd": "EURUSD",      # EUR/USD
        "usd_jpy": "USDJPY",      # USD/JPY
        "gbp_usd": "GBPUSD",      # GBP/USD
    }
    
    # Economic indicators
    ECONOMIC_INDICATORS = {
        "real_gdp": "REAL_GDP",             # Quarterly Real GDP
        "cpi": "CPI",                       # Monthly CPI
        "inflation": "INFLATION",           # Monthly Inflation
        "retail_sales": "RETAIL_SALES",     # Monthly Retail Sales
        "unemployment": "UNEMPLOYMENT",     # Monthly Unemployment
        "nonfarm_payroll": "NONFARM_PAYROLL" # Monthly Nonfarm Payroll
    }

    def __init__(self):
        """Initialize the plugin with API key from environment variables."""
        self.api_key = os.getenv("ALPHA_VANTAGE_KEY", "")
        if not self.api_key:
            logger.warning("ALPHA_VANTAGE_KEY environment variable not set - plugin disabled")
            self.__class__.enabled = False

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch financial data signals from Alpha Vantage API."""
        if not self.api_key:
            return []
            
        signals = []
        
        # Fetch stock data
        signals.extend(self._fetch_stock_data())
        
        # Fetch crypto data
        signals.extend(self._fetch_crypto_data())
        
        # Fetch forex data
        signals.extend(self._fetch_forex_data())
        
        # Fetch economic indicators (limited to prevent rate limiting)
        # Only fetch 1 economic indicator per run to stay within rate limits
        today = dt.datetime.now().day % len(self.ECONOMIC_INDICATORS)
        indicator_name = list(self.ECONOMIC_INDICATORS.keys())[today]
        indicator_symbol = self.ECONOMIC_INDICATORS[indicator_name]
        signals.extend(self._fetch_economic_data(indicator_name, indicator_symbol))
        
        return signals

    def _safe_get(self, params: dict) -> Optional[dict]:
        """Make a safe API request with retries and error handling."""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    self.BASE_URL,
                    params={**params, "apikey": self.api_key},
                    timeout=self.REQUEST_TIMEOUT
                )
                resp.raise_for_status()
                data = resp.json()
                
                # Check for API error messages
                if "Error Message" in data:
                    logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                    return None
                    
                return data
            except Exception as exc:
                logger.warning(f"Alpha Vantage request failed ({attempt+1}/{self.MAX_RETRIES}): {exc}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
        return None

    def _fetch_stock_data(self) -> List[Dict[str, Any]]:
        """Fetch daily stock price data for configured symbols."""
        signals = []
        
        # Limit to 5 symbols per run to stay within free tier rate limits
        today_symbols = {k: v for i, (k, v) in enumerate(self.STOCK_SYMBOLS.items()) if i % 5 == dt.datetime.now().day % 5}
        
        for var_name, symbol in today_symbols.items():
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
            }
            
            data = self._safe_get(params)
            if not data or "Global Quote" not in data:
                continue
                
            quote_data = data["Global Quote"]
            try:
                price = float(quote_data.get("05. price", 0))
                timestamp = quote_data.get("07. latest trading day", dt.datetime.now().strftime("%Y-%m-%d"))
                
                signals.append({
                    "name": var_name,
                    "value": price,
                    "source": "alpha_vantage",
                    "timestamp": self._to_timestamp(timestamp),
                    "metadata": {
                        "change": float(quote_data.get("09. change", 0)),
                        "change_percent": quote_data.get("10. change percent", "0%").strip("%"),
                        "volume": int(float(quote_data.get("06. volume", 0)))
                    }
                })
            except (ValueError, KeyError) as e:
                logger.error(f"Error processing stock {symbol}: {e}")
                
        return signals

    def _fetch_crypto_data(self) -> List[Dict[str, Any]]:
        """Fetch cryptocurrency price data."""
        signals = []
        
        # Limit to 2 symbols per run to stay within free tier rate limits
        today_symbols = {k: v for i, (k, v) in enumerate(self.CRYPTO_SYMBOLS.items()) 
                        if i % 2 == dt.datetime.now().day % 2}
        
        for var_name, symbol in today_symbols.items():
            params = {
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": symbol[:3],
                "to_currency": symbol[3:],
            }
            
            data = self._safe_get(params)
            if not data or "Realtime Currency Exchange Rate" not in data:
                continue
                
            rate_data = data["Realtime Currency Exchange Rate"]
            try:
                price = float(rate_data.get("5. Exchange Rate", 0))
                timestamp = rate_data.get("6. Last Refreshed", "")
                
                signals.append({
                    "name": var_name,
                    "value": price,
                    "source": "alpha_vantage_crypto",
                    "timestamp": self._to_timestamp(timestamp)
                })
            except (ValueError, KeyError) as e:
                logger.error(f"Error processing crypto {symbol}: {e}")
                
        return signals

    def _fetch_forex_data(self) -> List[Dict[str, Any]]:
        """Fetch forex exchange rate data."""
        signals = []
        
        # Limit to 1 forex pair per run to stay within free tier rate limits
        today_idx = dt.datetime.now().day % len(self.FOREX_SYMBOLS)
        pair_name = list(self.FOREX_SYMBOLS.keys())[today_idx]
        symbol = self.FOREX_SYMBOLS[pair_name]
        
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": symbol[:3],
            "to_currency": symbol[3:],
        }
        
        data = self._safe_get(params)
        if not data or "Realtime Currency Exchange Rate" not in data:
            return signals
            
        rate_data = data["Realtime Currency Exchange Rate"]
        try:
            price = float(rate_data.get("5. Exchange Rate", 0))
            timestamp = rate_data.get("6. Last Refreshed", "")
            
            signals.append({
                "name": pair_name,
                "value": price,
                "source": "alpha_vantage_forex",
                "timestamp": self._to_timestamp(timestamp)
            })
        except (ValueError, KeyError) as e:
            logger.error(f"Error processing forex {symbol}: {e}")
                
        return signals

    def _fetch_economic_data(self, indicator_name: str, indicator_code: str) -> List[Dict[str, Any]]:
        """Fetch economic indicator data."""
        signals = []
        
        # Map the indicator to the right Alpha Vantage function
        function_map = {
            "real_gdp": "REAL_GDP",
            "cpi": "CPI",
            "inflation": "INFLATION",
            "retail_sales": "RETAIL_SALES",
            "unemployment": "UNEMPLOYMENT",
            "nonfarm_payroll": "NONFARM_PAYROLL"
        }
        
        function = function_map.get(indicator_name)
        if not function:
            return signals
            
        params = {
            "function": function,
            "interval": "quarterly" if function == "REAL_GDP" else "monthly",
        }
        
        data = self._safe_get(params)
        if not data or "data" not in data:
            return signals
            
        # Get the most recent data point
        try:
            latest_data = data["data"][0]
            value = float(latest_data.get("value", 0))
            timestamp = latest_data.get("date", "")
            
            signals.append({
                "name": indicator_name,
                "value": value,
                "source": "alpha_vantage_economic",
                "timestamp": self._to_timestamp(timestamp)
            })
        except (IndexError, ValueError, KeyError) as e:
            logger.error(f"Error processing economic indicator {indicator_name}: {e}")
                
        return signals

    def _to_timestamp(self, date_str: str) -> str:
        """Convert date string to ISO-8601 UTC timestamp."""
        try:
            # Parse the date string to a datetime object
            if "T" in date_str:  # Already has time component
                dt_obj = dt.datetime.fromisoformat(date_str)
            else:  # Just a date, add time at noon
                dt_obj = dt.datetime.fromisoformat(f"{date_str}T12:00:00")
            
            # Convert to UTC timezone
            dt_obj = dt_obj.replace(tzinfo=dt.timezone.utc)
            return dt_obj.isoformat()
        except Exception:
            # Default to current time if parsing fails
            return dt.datetime.now(dt.timezone.utc).isoformat()