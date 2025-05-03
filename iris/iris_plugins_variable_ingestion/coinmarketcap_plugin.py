"""CoinMarketCap API — cryptocurrency market data plugin.

Connects to the CoinMarketCap API to fetch cryptocurrency market data
including prices, market caps, trading volumes, and other metrics.

Requires API key: Get free API key at https://coinmarketcap.com/api/
"""
import datetime as dt
import logging
import time
import os
from typing import Dict, List, Any, Optional, Tuple, Set
import json

import requests
from iris.iris_plugins import IrisPluginManager
from iris.iris_utils.ingestion_persistence import (
    ensure_data_directory,
    save_request_metadata,
    save_api_response,
    save_processed_data
)

logger = logging.getLogger(__name__)

# Source name for persistence
_SOURCE_NAME = "coinmarketcap"

class CoinMarketCapPlugin(IrisPluginManager):
    plugin_name = "coinmarketcap_plugin"
    enabled = False    # Disabled by default until API key is provided
    concurrency = 1    # Limited concurrency due to API rate limits
    
    # CoinMarketCap API configuration
    BASE_URL = "https://pro-api.coinmarketcap.com/v1"
    REQUEST_TIMEOUT = 30.0
    RETRY_WAIT = 5.0  # seconds between retries
    MAX_RETRIES = 2
    
    # Top cryptocurrencies to track by market cap
    TOP_CRYPTOS = [
        "BTC",   # Bitcoin
        "ETH",   # Ethereum
        "USDT",  # Tether
        "BNB",   # Binance Coin
        "SOL",   # Solana
        "XRP",   # Ripple
        "USDC",  # USD Coin
        "ADA",   # Cardano
        "AVAX",  # Avalanche
        "DOGE"   # Dogecoin
    ]
    
    # Signal types to extract from the data
    SIGNAL_TYPES = [
        "price",
        "market_cap", 
        "volume_24h",
        "percent_change_24h",
        "percent_change_7d",
    ]

    def __init__(self):
        """Initialize the CoinMarketCap plugin."""
        # Get API key from environment variable
        self.api_key = os.environ.get("COINMARKETCAP_API_KEY")
        if self.api_key:
            self.enabled = True
            logger.info("CoinMarketCap plugin enabled with API key")
        else:
            logger.warning("No CoinMarketCap API key found in environment variables")
        
        # Ensure data directory exists for this source
        ensure_data_directory(_SOURCE_NAME)
    
    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch cryptocurrency market signals from CoinMarketCap API."""
        if not self.enabled or not self.api_key:
            logger.warning("CoinMarketCap plugin is disabled or missing API key")
            return []
        
        signals = []
        
        # Current timestamp
        now = dt.datetime.now(dt.timezone.utc)
        
        # Fetch latest cryptocurrency data
        crypto_data = self._fetch_latest_crypto_data()
        if not crypto_data:
            logger.warning("Failed to fetch cryptocurrency data")
            return signals
        
        # Process data into signals
        signals.extend(self._process_crypto_data(crypto_data, now))
        
        # Fetch global market metrics every 6 hours
        # (Using hour of day to avoid too frequent fetching)
        if now.hour % 6 == 0 and now.minute < 15:  # Only in the first 15 min of the hour
            global_metrics = self._fetch_global_metrics()
            if global_metrics:
                signals.extend(self._process_global_metrics(global_metrics, now))
        
        return signals
    
    def _safe_get(self, endpoint: str, params: dict, dataset_id: str) -> Optional[dict]:
        """Make a safe API request with retries and error handling."""
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Set up headers with API key
        headers = {
            "X-CMC_PRO_API_KEY": self.api_key,
            "Accept": "application/json"
        }
        
        # Save request metadata
        save_request_metadata(
            dataset_id,
            params,
            source_name=_SOURCE_NAME,
            url=url
        )
        
        # Make request with retries
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=self.REQUEST_TIMEOUT
                )
                resp.raise_for_status()
                
                # Parse JSON response
                data = resp.json()
                
                # Save successful response
                save_api_response(
                    dataset_id,
                    {"response_json": json.dumps(data)},
                    source_name=_SOURCE_NAME,
                    status_code=resp.status_code,
                    headers=dict(resp.headers)
                )
                
                # Check for API error in response
                if "status" in data and data["status"]["error_code"] != 0:
                    error_msg = data["status"].get("error_message", "Unknown API error")
                    logger.warning(f"CoinMarketCap API error: {error_msg}")
                    if attempt < self.MAX_RETRIES:
                        time.sleep(self.RETRY_WAIT * (attempt + 1))
                        continue
                    return None
                
                return data
            except requests.exceptions.RequestException as exc:
                logger.warning(f"CoinMarketCap request failed ({attempt+1}/{self.MAX_RETRIES}): {exc}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
            except json.JSONDecodeError:
                logger.error("Failed to parse CoinMarketCap API response")
                break
        
        # If all attempts failed, log the error
        logger.error(f"Failed to fetch data from CoinMarketCap after {self.MAX_RETRIES} attempts")
        return None
    
    def _fetch_latest_crypto_data(self) -> Optional[Dict[str, Any]]:
        """Fetch latest cryptocurrency data for selected cryptocurrencies."""
        # Convert array of symbols to comma-separated string
        symbols = ",".join(self.TOP_CRYPTOS)
        
        # Set up parameters
        params = {
            "symbol": symbols,
            "convert": "USD"
        }
        
        # Create dataset ID for persistence
        dataset_id = f"crypto_data_{len(self.TOP_CRYPTOS)}_currencies"
        
        # Make API request
        response_data = self._safe_get("cryptocurrency/quotes/latest", params, dataset_id)
        if not response_data or "data" not in response_data:
            return None
        
        return response_data["data"]
    
    def _fetch_global_metrics(self) -> Optional[Dict[str, Any]]:
        """Fetch global cryptocurrency market metrics."""
        # Set up parameters
        params = {
            "convert": "USD"
        }
        
        # Create dataset ID for persistence
        dataset_id = "global_metrics"
        
        # Make API request
        response_data = self._safe_get("global-metrics/quotes/latest", params, dataset_id)
        if not response_data or "data" not in response_data:
            return None
        
        return response_data["data"]
    
    def _process_crypto_data(self, crypto_data: Dict[str, Any], 
                           timestamp: dt.datetime) -> List[Dict[str, Any]]:
        """Process cryptocurrency data into signals.
        
        Args:
            crypto_data: Dictionary with cryptocurrency data
            timestamp: Timestamp for the signals
            
        Returns:
            List of signals derived from cryptocurrency data
        """
        signals = []
        
        # Create a signal for each cryptocurrency and signal type
        iso_timestamp = timestamp.isoformat()
        
        for symbol, data in crypto_data.items():
            # Skip if symbol not in our list (should not happen given our request)
            if symbol not in self.TOP_CRYPTOS:
                continue
            
            # Extract data from nested structure
            try:
                quote = data.get("quote", {}).get("USD", {})
                
                # Create signals for each metric
                if "price" in quote:
                    signals.append({
                        "name": f"crypto_{symbol.lower()}_price",
                        "value": quote["price"],
                        "source": "coinmarketcap",
                        "timestamp": iso_timestamp,
                        "metadata": {
                            "symbol": symbol,
                            "name": data.get("name", symbol),
                            "metric": "price"
                        }
                    })
                
                if "market_cap" in quote:
                    signals.append({
                        "name": f"crypto_{symbol.lower()}_market_cap",
                        "value": quote["market_cap"],
                        "source": "coinmarketcap",
                        "timestamp": iso_timestamp,
                        "metadata": {
                            "symbol": symbol,
                            "name": data.get("name", symbol),
                            "metric": "market_cap"
                        }
                    })
                
                if "volume_24h" in quote:
                    signals.append({
                        "name": f"crypto_{symbol.lower()}_volume_24h",
                        "value": quote["volume_24h"],
                        "source": "coinmarketcap",
                        "timestamp": iso_timestamp,
                        "metadata": {
                            "symbol": symbol,
                            "name": data.get("name", symbol),
                            "metric": "volume_24h"
                        }
                    })
                
                if "percent_change_24h" in quote:
                    signals.append({
                        "name": f"crypto_{symbol.lower()}_percent_change_24h",
                        "value": quote["percent_change_24h"],
                        "source": "coinmarketcap",
                        "timestamp": iso_timestamp,
                        "metadata": {
                            "symbol": symbol,
                            "name": data.get("name", symbol),
                            "metric": "percent_change_24h"
                        }
                    })
                
                if "percent_change_7d" in quote:
                    signals.append({
                        "name": f"crypto_{symbol.lower()}_percent_change_7d",
                        "value": quote["percent_change_7d"],
                        "source": "coinmarketcap",
                        "timestamp": iso_timestamp,
                        "metadata": {
                            "symbol": symbol,
                            "name": data.get("name", symbol),
                            "metric": "percent_change_7d"
                        }
                    })
                
                # Save the processed signals
                for signal_type in self.SIGNAL_TYPES:
                    if signal_type in quote:
                        signal_data = {
                            "name": f"crypto_{symbol.lower()}_{signal_type}",
                            "value": quote[signal_type],
                            "source": "coinmarketcap",
                            "timestamp": iso_timestamp,
                            "metadata": {
                                "symbol": symbol,
                                "name": data.get("name", symbol),
                                "metric": signal_type
                            }
                        }
                        
                        save_processed_data(
                            f"{symbol}_{signal_type}",
                            signal_data,
                            source_name=_SOURCE_NAME,
                            timestamp=iso_timestamp
                        )
            
            except (KeyError, TypeError) as e:
                logger.warning(f"Error processing data for {symbol}: {e}")
                continue
        
        return signals
    
    def _process_global_metrics(self, global_data: Dict[str, Any], 
                              timestamp: dt.datetime) -> List[Dict[str, Any]]:
        """Process global market metrics into signals.
        
        Args:
            global_data: Dictionary with global market metrics
            timestamp: Timestamp for the signals
            
        Returns:
            List of signals derived from global market metrics
        """
        signals = []
        
        # Create a signal for each global metric
        iso_timestamp = timestamp.isoformat()
        
        try:
            # Extract data from nested structure
            quote = global_data.get("quote", {}).get("USD", {})
            
            # Total market cap
            if "total_market_cap" in quote:
                market_cap_signal = {
                    "name": "crypto_global_market_cap",
                    "value": quote["total_market_cap"],
                    "source": "coinmarketcap",
                    "timestamp": iso_timestamp,
                    "metadata": {
                        "metric": "total_market_cap"
                    }
                }
                
                signals.append(market_cap_signal)
                
                # Save the processed signal
                save_processed_data(
                    "global_market_cap",
                    market_cap_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=iso_timestamp
                )
            
            # Total 24h volume
            if "total_volume_24h" in quote:
                volume_signal = {
                    "name": "crypto_global_volume_24h",
                    "value": quote["total_volume_24h"],
                    "source": "coinmarketcap",
                    "timestamp": iso_timestamp,
                    "metadata": {
                        "metric": "total_volume_24h"
                    }
                }
                
                signals.append(volume_signal)
                
                # Save the processed signal
                save_processed_data(
                    "global_volume_24h",
                    volume_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=iso_timestamp
                )
            
            # Bitcoin dominance
            if "btc_dominance" in quote:
                btc_dom_signal = {
                    "name": "crypto_btc_dominance",
                    "value": quote["btc_dominance"],
                    "source": "coinmarketcap",
                    "timestamp": iso_timestamp,
                    "metadata": {
                        "metric": "btc_dominance"
                    }
                }
                
                signals.append(btc_dom_signal)
                
                # Save the processed signal
                save_processed_data(
                    "btc_dominance",
                    btc_dom_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=iso_timestamp
                )
            
            # Ethereum dominance
            if "eth_dominance" in quote:
                eth_dom_signal = {
                    "name": "crypto_eth_dominance",
                    "value": quote["eth_dominance"],
                    "source": "coinmarketcap",
                    "timestamp": iso_timestamp,
                    "metadata": {
                        "metric": "eth_dominance"
                    }
                }
                
                signals.append(eth_dom_signal)
                
                # Save the processed signal
                save_processed_data(
                    "eth_dominance",
                    eth_dom_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=iso_timestamp
                )
                
        except (KeyError, TypeError) as e:
            logger.warning(f"Error processing global metrics: {e}")
        
        return signals