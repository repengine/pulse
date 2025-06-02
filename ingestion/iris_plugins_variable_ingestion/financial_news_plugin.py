"""Financial News Sentiment API — news analysis plugin.

Connects to financial news APIs to retrieve and analyze sentiment from
financial news articles related to markets, commodities, and specific companies.

Requires API key: Configurable to use AlphaVantage, NewsAPI, or other financial news providers
"""

import datetime as dt
import logging
import time
import os
from typing import Dict, List, Any, Optional
import json
import re

import requests
from ingestion.iris_plugins import IrisPluginManager
from ingestion.iris_utils.ingestion_persistence import (
    ensure_data_directory,
    save_request_metadata,
    save_api_response,
    save_processed_data,
)

logger = logging.getLogger(__name__)

# Source name for persistence
_SOURCE_NAME = "financial_news"


class FinancialNewsPlugin(IrisPluginManager):
    plugin_name = "financial_news_plugin"
    enabled = False  # Disabled by default until API key is provided
    concurrency = 1  # Limited concurrency due to API rate limits

    # API configuration
    ALPHAVANTAGE_BASE_URL = "https://www.alphavantage.co/query"
    NEWSAPI_BASE_URL = "https://newsapi.org/v2"
    REQUEST_TIMEOUT = 30.0
    RETRY_WAIT = 5.0  # seconds between retries
    MAX_RETRIES = 2

    # Company symbols to track
    TOP_COMPANIES = [
        "AAPL",  # Apple
        "MSFT",  # Microsoft
        "GOOGL",  # Alphabet (Google)
        "AMZN",  # Amazon
        "TSLA",  # Tesla
        "META",  # Meta (Facebook)
        "NVDA",  # NVIDIA
        "JPM",  # JPMorgan Chase
        "BAC",  # Bank of America
        "V",  # Visa
    ]

    # Market sectors to track
    SECTORS = [
        "technology",
        "healthcare",
        "financial",
        "energy",
        "consumer",
        "industrial",
        "utilities",
        "real_estate",
    ]

    # Market-moving topics
    TOPICS = [
        "inflation",
        "interest_rates",
        "fed",
        "recession",
        "unemployment",
        "gdp",
        "earnings",
        "supply_chain",
        "trade_war",
        "geopolitical",
    ]

    def __init__(self):
        """Initialize the Financial News plugin."""
        # Get API keys from environment variables
        self.alphavantage_api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
        self.newsapi_key = os.environ.get("NEWSAPI_KEY")

        # Enable plugin if at least one API key is available
        if self.alphavantage_api_key or self.newsapi_key:
            self.enabled = True
            logger.info(
                f"Financial News plugin enabled with {sum(bool(k) for k in [self.alphavantage_api_key, self.newsapi_key])} API key(s)"
            )
        else:
            logger.warning("No Financial News API keys found in environment variables")

        # Ensure data directory exists for this source
        ensure_data_directory(_SOURCE_NAME)

        # Initialize rotation counters for distributing API calls
        self._company_index = 0
        self._sector_index = 0
        self._topic_index = 0

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch financial news signals from available APIs."""
        if not self.enabled:
            logger.warning("Financial News plugin is disabled due to missing API keys")
            return []

        signals = []

        # Current timestamp
        now = dt.datetime.now(dt.timezone.utc)

        # Rotate through different signal types to spread out API calls
        hour_of_day = now.hour

        if hour_of_day % 3 == 0:  # Every 3 hours, fetch company-specific news
            # Rotate through companies to avoid hitting API limits
            company = self.TOP_COMPANIES[self._company_index]
            self._company_index = (self._company_index + 1) % len(self.TOP_COMPANIES)

            # Fetch company-specific news
            company_news = self._fetch_company_news(company)
            if company_news:
                signals.extend(self._process_company_news(company, company_news, now))

        if hour_of_day % 3 == 1:  # Every 3 hours (offset by 1), fetch sector news
            # Rotate through sectors
            sector = self.SECTORS[self._sector_index]
            self._sector_index = (self._sector_index + 1) % len(self.SECTORS)

            # Fetch sector-specific news
            sector_news = self._fetch_sector_news(sector)
            if sector_news:
                signals.extend(self._process_sector_news(sector, sector_news, now))

        if hour_of_day % 3 == 2:  # Every 3 hours (offset by 2), fetch topic news
            # Rotate through topics
            topic = self.TOPICS[self._topic_index]
            self._topic_index = (self._topic_index + 1) % len(self.TOPICS)

            # Fetch topic-specific news
            topic_news = self._fetch_topic_news(topic)
            if topic_news:
                signals.extend(self._process_topic_news(topic, topic_news, now))

        # Every 12 hours, fetch market news summary (4am and 4pm UTC)
        if (
            hour_of_day in [4, 16] and now.minute < 15
        ):  # Only in the first 15 min of those hours
            market_news = self._fetch_market_news()
            if market_news:
                signals.extend(self._process_market_news(market_news, now))

        return signals

    def _safe_get_alphavantage(
        self, function: str, params: dict, dataset_id: str
    ) -> Optional[dict]:
        """Make a safe API request to Alpha Vantage with retries and error handling."""
        if not self.alphavantage_api_key:
            logger.warning("Alpha Vantage API key not configured")
            return None

        # Add API key to parameters
        params["apikey"] = self.alphavantage_api_key
        params["function"] = function

        # Save request metadata
        save_request_metadata(
            dataset_id, params, source_name=_SOURCE_NAME, url=self.ALPHAVANTAGE_BASE_URL
        )

        # Make request with retries
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    self.ALPHAVANTAGE_BASE_URL,
                    params=params,
                    timeout=self.REQUEST_TIMEOUT,
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
                    headers=dict(resp.headers),
                )

                # Check for API error or rate limit in response
                if "Error Message" in data:
                    error_msg = data.get("Error Message", "Unknown API error")
                    logger.warning(f"Alpha Vantage API error: {error_msg}")
                    if attempt < self.MAX_RETRIES:
                        time.sleep(self.RETRY_WAIT * (attempt + 1))
                        continue
                    return None

                # Check for empty response
                if "Note" in data and "API call frequency" in data["Note"]:
                    logger.warning("Alpha Vantage rate limit reached")
                    if attempt < self.MAX_RETRIES:
                        time.sleep(self.RETRY_WAIT * (attempt + 1))
                        continue
                    return None

                return data
            except requests.exceptions.RequestException as exc:
                logger.warning(
                    f"Alpha Vantage request failed ({attempt + 1}/{self.MAX_RETRIES}): {exc}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
            except json.JSONDecodeError:
                logger.error("Failed to parse Alpha Vantage API response")
                break

        # If all attempts failed, log the error
        logger.error(
            f"Failed to fetch data from Alpha Vantage after {self.MAX_RETRIES} attempts"
        )
        return None

    def _safe_get_newsapi(
        self, endpoint: str, params: dict, dataset_id: str
    ) -> Optional[dict]:
        """Make a safe API request to NewsAPI with retries and error handling."""
        if not self.newsapi_key:
            logger.warning("NewsAPI key not configured")
            return None

        url = f"{self.NEWSAPI_BASE_URL}/{endpoint}"

        # Add API key to headers
        headers = {"X-Api-Key": self.newsapi_key, "Accept": "application/json"}

        # Save request metadata
        save_request_metadata(dataset_id, params, source_name=_SOURCE_NAME, url=url)

        # Make request with retries
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    url, headers=headers, params=params, timeout=self.REQUEST_TIMEOUT
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
                    headers=dict(resp.headers),
                )

                # Check for API error in response
                if data.get("status") != "ok":
                    error_msg = data.get("message", "Unknown API error")
                    error_code = data.get("code", "unknown")
                    logger.warning(f"NewsAPI error ({error_code}): {error_msg}")

                    # Check for rate limiting
                    if error_code == "rateLimited" and attempt < self.MAX_RETRIES:
                        time.sleep(self.RETRY_WAIT * (attempt + 1))
                        continue

                    return None

                return data
            except requests.exceptions.RequestException as exc:
                logger.warning(
                    f"NewsAPI request failed ({attempt + 1}/{self.MAX_RETRIES}): {exc}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
            except json.JSONDecodeError:
                logger.error("Failed to parse NewsAPI response")
                break

        # If all attempts failed, log the error
        logger.error(
            f"Failed to fetch data from NewsAPI after {self.MAX_RETRIES} attempts"
        )
        return None

    def _fetch_company_news(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch news articles for a specific company."""
        # Try Alpha Vantage first if configured
        if self.alphavantage_api_key:
            params = {
                "symbol": symbol,
                "limit": 10,  # Limit to 10 news items to save quota
            }

            dataset_id = f"company_news_{symbol}"
            response_data = self._safe_get_alphavantage(
                "NEWS_SENTIMENT", params, dataset_id
            )

            if response_data and "feed" in response_data:
                return response_data

        # Fall back to NewsAPI if Alpha Vantage failed or not configured
        if self.newsapi_key:
            # For NewsAPI, we need to use the company name instead of symbol
            company_names = {
                "AAPL": "Apple",
                "MSFT": "Microsoft",
                "GOOGL": "Google OR Alphabet",
                "AMZN": "Amazon",
                "TSLA": "Tesla",
                "META": "Meta OR Facebook",
                "NVDA": "NVIDIA",
                "JPM": "JPMorgan",
                "BAC": "Bank of America",
                "V": "Visa Inc",
            }

            company_name = company_names.get(symbol, symbol)

            params = {
                "q": company_name,
                "language": "en",
                "sortBy": "relevancy",
                "pageSize": 10,
            }

            dataset_id = f"company_news_{symbol}"
            response_data = self._safe_get_newsapi("everything", params, dataset_id)

            if response_data and "articles" in response_data:
                return response_data

        return None

    def _fetch_sector_news(self, sector: str) -> Optional[Dict[str, Any]]:
        """Fetch news articles for a specific market sector."""
        # Map sector to more descriptive search terms
        sector_terms = {
            "technology": "technology sector OR tech stocks OR tech companies",
            "healthcare": "healthcare sector OR medical stocks OR pharma companies OR biotech",
            "financial": "financial sector OR banking stocks OR finance companies",
            "energy": "energy sector OR oil stocks OR gas companies OR renewable energy",
            "consumer": "consumer sector OR retail stocks OR consumer goods",
            "industrial": "industrial sector OR manufacturing stocks OR industrial companies",
            "utilities": "utilities sector OR utility stocks OR utilities companies",
            "real_estate": "real estate sector OR property stocks OR REIT",
        }

        search_term = sector_terms.get(sector, sector)

        # Use NewsAPI for sector news
        if self.newsapi_key:
            params = {
                "q": search_term,
                "language": "en",
                "sortBy": "relevancy",
                "pageSize": 10,
            }

            dataset_id = f"sector_news_{sector}"
            response_data = self._safe_get_newsapi("everything", params, dataset_id)

            if response_data and "articles" in response_data:
                return response_data

        return None

    def _fetch_topic_news(self, topic: str) -> Optional[Dict[str, Any]]:
        """Fetch news articles for a specific financial topic."""
        # Map topics to more descriptive search terms
        topic_terms = {
            "inflation": "inflation OR consumer prices OR CPI",
            "interest_rates": "interest rates OR federal reserve rates OR central bank",
            "fed": "Federal Reserve OR Fed meeting OR Fed policy OR Fed chairman",
            "recession": "recession OR economic downturn OR economic slowdown",
            "unemployment": "unemployment OR jobs report OR labor market",
            "gdp": "GDP growth OR economic growth OR GDP report",
            "earnings": "earnings season OR company earnings OR quarterly results",
            "supply_chain": "supply chain OR logistics OR shipping OR container",
            "trade_war": "trade war OR tariffs OR trade dispute OR trade agreement",
            "geopolitical": "geopolitical OR political risk OR war OR conflict OR election",
        }

        search_term = topic_terms.get(topic, topic)

        # Use NewsAPI for topic news
        if self.newsapi_key:
            params = {
                "q": search_term,
                "language": "en",
                "sortBy": "relevancy",
                "pageSize": 10,
            }

            dataset_id = f"topic_news_{topic}"
            response_data = self._safe_get_newsapi("everything", params, dataset_id)

            if response_data and "articles" in response_data:
                return response_data

        return None

    def _fetch_market_news(self) -> Optional[Dict[str, Any]]:
        """Fetch general market news."""
        # Try Alpha Vantage first if configured
        if self.alphavantage_api_key:
            params = {
                "tickers": "MARKET",  # Special value for market news
                "limit": 20,  # More news items for market overview
            }

            dataset_id = "market_news"
            response_data = self._safe_get_alphavantage(
                "NEWS_SENTIMENT", params, dataset_id
            )

            if response_data and "feed" in response_data:
                return response_data

        # Fall back to NewsAPI if Alpha Vantage failed or not configured
        if self.newsapi_key:
            params = {
                "q": "stock market OR financial markets OR wall street OR nasdaq OR dow jones OR S&P 500",
                "language": "en",
                "sortBy": "relevancy",
                "pageSize": 20,
            }

            dataset_id = "market_news"
            response_data = self._safe_get_newsapi("everything", params, dataset_id)

            if response_data and "articles" in response_data:
                return response_data

        return None

    def _calculate_sentiment_score(self, text: str) -> float:
        """Simple rule-based sentiment analysis for financial news.

        This is a simplified version. In a real-world scenario, you might want to use
        a more sophisticated NLP model or service.

        Args:
            text: The text to analyze

        Returns:
            Float sentiment score from -1.0 (negative) to 1.0 (positive)
        """
        # List of positive and negative financial terms
        positive_terms = [
            "growth",
            "profit",
            "surge",
            "gain",
            "boost",
            "rally",
            "bullish",
            "outperform",
            "beat",
            "upgrade",
            "rise",
            "record",
            "jump",
            "recovery",
            "strong",
            "positive",
            "optimistic",
            "confidence",
            "upside",
        ]

        negative_terms = [
            "decline",
            "drop",
            "fall",
            "loss",
            "plunge",
            "bearish",
            "underperform",
            "miss",
            "downgrade",
            "decrease",
            "weak",
            "negative",
            "pessimistic",
            "concern",
            "risk",
            "warning",
            "crash",
            "crisis",
            "trouble",
            "downturn",
        ]

        # Normalize text
        text_lower = text.lower()

        # Count occurrences
        positive_count = sum(
            1 for term in positive_terms if re.search(rf"\b{term}\b", text_lower)
        )
        negative_count = sum(
            1 for term in negative_terms if re.search(rf"\b{term}\b", text_lower)
        )

        # Calculate sentiment score
        total_count = positive_count + negative_count
        if total_count > 0:
            return (positive_count - negative_count) / total_count

        return 0.0  # Neutral if no sentiment terms found

    def _process_company_news(
        self, symbol: str, news_data: Dict[str, Any], timestamp: dt.datetime
    ) -> List[Dict[str, Any]]:
        """Process company news data into signals.

        Args:
            symbol: Company ticker symbol
            news_data: Dictionary with news data
            timestamp: Timestamp for the signals

        Returns:
            List of signals derived from company news
        """
        signals = []
        iso_timestamp = timestamp.isoformat()

        # Process news depending on the source API
        if "feed" in news_data:  # Alpha Vantage format
            # Extract articles
            articles = news_data.get("feed", [])

            # Calculate average sentiment
            if articles:
                # Use Alpha Vantage's sentiment scores if available
                sentiment_scores = []
                for article in articles:
                    # Check if the article is relevant to this company
                    ticker_sentiments = article.get("ticker_sentiment", [])
                    for ticker_data in ticker_sentiments:
                        if ticker_data.get("ticker") == symbol:
                            score = float(ticker_data.get("ticker_sentiment_score", 0))
                            sentiment_scores.append(score)
                            break
                    else:
                        # If no specific ticker sentiment, use overall sentiment
                        if "overall_sentiment_score" in article:
                            score = float(article.get("overall_sentiment_score", 0))
                            sentiment_scores.append(score)

                # Calculate average sentiment if we have scores
                if sentiment_scores:
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

                    # Create sentiment signal
                    sentiment_signal = {
                        "name": f"news_sentiment_{symbol.lower()}",
                        "value": avg_sentiment,
                        "source": "financial_news",
                        "timestamp": iso_timestamp,
                        "metadata": {
                            "symbol": symbol,
                            "articles_count": len(articles),
                            "metric": "sentiment",
                        },
                    }

                    signals.append(sentiment_signal)

                    # Save the processed signal
                    save_processed_data(
                        f"company_sentiment_{symbol}",
                        sentiment_signal,
                        source_name=_SOURCE_NAME,
                        timestamp=iso_timestamp,
                    )

                # Create volume signal (number of articles)
                volume_signal = {
                    "name": f"news_volume_{symbol.lower()}",
                    "value": len(articles),
                    "source": "financial_news",
                    "timestamp": iso_timestamp,
                    "metadata": {"symbol": symbol, "metric": "volume"},
                }

                signals.append(volume_signal)

                # Save the processed signal
                save_processed_data(
                    f"company_news_volume_{symbol}",
                    volume_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=iso_timestamp,
                )

        elif "articles" in news_data:  # NewsAPI format
            # Extract articles
            articles = news_data.get("articles", [])

            # Calculate average sentiment
            if articles:
                # For NewsAPI, we need to calculate sentiment ourselves
                sentiment_scores = []
                for article in articles:
                    # Combine title and description for sentiment analysis
                    title = article.get("title", "")
                    description = article.get("description", "")
                    text = f"{title} {description}".strip()

                    if text:
                        score = self._calculate_sentiment_score(text)
                        sentiment_scores.append(score)

                # Calculate average sentiment if we have scores
                if sentiment_scores:
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

                    # Create sentiment signal
                    sentiment_signal = {
                        "name": f"news_sentiment_{symbol.lower()}",
                        "value": avg_sentiment,
                        "source": "financial_news",
                        "timestamp": iso_timestamp,
                        "metadata": {
                            "symbol": symbol,
                            "articles_count": len(articles),
                            "metric": "sentiment",
                        },
                    }

                    signals.append(sentiment_signal)

                    # Save the processed signal
                    save_processed_data(
                        f"company_sentiment_{symbol}",
                        sentiment_signal,
                        source_name=_SOURCE_NAME,
                        timestamp=iso_timestamp,
                    )

                # Create volume signal (number of articles)
                volume_signal = {
                    "name": f"news_volume_{symbol.lower()}",
                    "value": len(articles),
                    "source": "financial_news",
                    "timestamp": iso_timestamp,
                    "metadata": {"symbol": symbol, "metric": "volume"},
                }

                signals.append(volume_signal)

                # Save the processed signal
                save_processed_data(
                    f"company_news_volume_{symbol}",
                    volume_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=iso_timestamp,
                )

        return signals

    def _process_sector_news(
        self, sector: str, news_data: Dict[str, Any], timestamp: dt.datetime
    ) -> List[Dict[str, Any]]:
        """Process sector news data into signals."""
        signals = []
        iso_timestamp = timestamp.isoformat()

        # Process news from NewsAPI format
        if "articles" in news_data:
            # Extract articles
            articles = news_data.get("articles", [])

            # Calculate average sentiment
            if articles:
                # Calculate sentiment for each article
                sentiment_scores = []
                for article in articles:
                    # Combine title and description for sentiment analysis
                    title = article.get("title", "")
                    description = article.get("description", "")
                    text = f"{title} {description}".strip()

                    if text:
                        score = self._calculate_sentiment_score(text)
                        sentiment_scores.append(score)

                # Calculate average sentiment if we have scores
                if sentiment_scores:
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

                    # Create sentiment signal
                    sentiment_signal = {
                        "name": f"news_sentiment_sector_{sector}",
                        "value": avg_sentiment,
                        "source": "financial_news",
                        "timestamp": iso_timestamp,
                        "metadata": {
                            "sector": sector,
                            "articles_count": len(articles),
                            "metric": "sentiment",
                        },
                    }

                    signals.append(sentiment_signal)

                    # Save the processed signal
                    save_processed_data(
                        f"sector_sentiment_{sector}",
                        sentiment_signal,
                        source_name=_SOURCE_NAME,
                        timestamp=iso_timestamp,
                    )

                # Create volume signal (number of articles)
                volume_signal = {
                    "name": f"news_volume_sector_{sector}",
                    "value": len(articles),
                    "source": "financial_news",
                    "timestamp": iso_timestamp,
                    "metadata": {"sector": sector, "metric": "volume"},
                }

                signals.append(volume_signal)

                # Save the processed signal
                save_processed_data(
                    f"sector_news_volume_{sector}",
                    volume_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=iso_timestamp,
                )

        return signals

    def _process_topic_news(
        self, topic: str, news_data: Dict[str, Any], timestamp: dt.datetime
    ) -> List[Dict[str, Any]]:
        """Process topic news data into signals."""
        signals = []
        iso_timestamp = timestamp.isoformat()

        # Process news from NewsAPI format
        if "articles" in news_data:
            # Extract articles
            articles = news_data.get("articles", [])

            # Calculate average sentiment
            if articles:
                # Calculate sentiment for each article
                sentiment_scores = []
                for article in articles:
                    # Combine title and description for sentiment analysis
                    title = article.get("title", "")
                    description = article.get("description", "")
                    text = f"{title} {description}".strip()

                    if text:
                        score = self._calculate_sentiment_score(text)
                        sentiment_scores.append(score)

                # Calculate average sentiment if we have scores
                if sentiment_scores:
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

                    # Create sentiment signal
                    sentiment_signal = {
                        "name": f"news_sentiment_topic_{topic}",
                        "value": avg_sentiment,
                        "source": "financial_news",
                        "timestamp": iso_timestamp,
                        "metadata": {
                            "topic": topic,
                            "articles_count": len(articles),
                            "metric": "sentiment",
                        },
                    }

                    signals.append(sentiment_signal)

                    # Save the processed signal
                    save_processed_data(
                        f"topic_sentiment_{topic}",
                        sentiment_signal,
                        source_name=_SOURCE_NAME,
                        timestamp=iso_timestamp,
                    )

                # Create volume signal (number of articles)
                volume_signal = {
                    "name": f"news_volume_topic_{topic}",
                    "value": len(articles),
                    "source": "financial_news",
                    "timestamp": iso_timestamp,
                    "metadata": {"topic": topic, "metric": "volume"},
                }

                signals.append(volume_signal)

                # Save the processed signal
                save_processed_data(
                    f"topic_news_volume_{topic}",
                    volume_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=iso_timestamp,
                )

        return signals

    def _process_market_news(
        self, news_data: Dict[str, Any], timestamp: dt.datetime
    ) -> List[Dict[str, Any]]:
        """Process market news data into signals."""
        signals = []
        iso_timestamp = timestamp.isoformat()

        # Process news depending on the source API
        if "feed" in news_data:  # Alpha Vantage format
            # Extract articles
            articles = news_data.get("feed", [])

            # Calculate average sentiment
            if articles:
                # Use Alpha Vantage's sentiment scores if available
                sentiment_scores = []
                for article in articles:
                    if "overall_sentiment_score" in article:
                        score = float(article.get("overall_sentiment_score", 0))
                        sentiment_scores.append(score)

                # Calculate average sentiment if we have scores
                if sentiment_scores:
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

                    # Create sentiment signal
                    sentiment_signal = {
                        "name": "news_sentiment_market",
                        "value": avg_sentiment,
                        "source": "financial_news",
                        "timestamp": iso_timestamp,
                        "metadata": {
                            "articles_count": len(articles),
                            "metric": "sentiment",
                        },
                    }

                    signals.append(sentiment_signal)

                    # Save the processed signal
                    save_processed_data(
                        "market_sentiment",
                        sentiment_signal,
                        source_name=_SOURCE_NAME,
                        timestamp=iso_timestamp,
                    )

                # Create volume signal (number of articles)
                volume_signal = {
                    "name": "news_volume_market",
                    "value": len(articles),
                    "source": "financial_news",
                    "timestamp": iso_timestamp,
                    "metadata": {"metric": "volume"},
                }

                signals.append(volume_signal)

                # Save the processed signal
                save_processed_data(
                    "market_news_volume",
                    volume_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=iso_timestamp,
                )

        elif "articles" in news_data:  # NewsAPI format
            # Extract articles
            articles = news_data.get("articles", [])

            # Calculate average sentiment
            if articles:
                # For NewsAPI, we need to calculate sentiment ourselves
                sentiment_scores = []
                for article in articles:
                    # Combine title and description for sentiment analysis
                    title = article.get("title", "")
                    description = article.get("description", "")
                    text = f"{title} {description}".strip()

                    if text:
                        score = self._calculate_sentiment_score(text)
                        sentiment_scores.append(score)

                # Calculate average sentiment if we have scores
                if sentiment_scores:
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

                    # Create sentiment signal
                    sentiment_signal = {
                        "name": "news_sentiment_market",
                        "value": avg_sentiment,
                        "source": "financial_news",
                        "timestamp": iso_timestamp,
                        "metadata": {
                            "articles_count": len(articles),
                            "metric": "sentiment",
                        },
                    }

                    signals.append(sentiment_signal)

                    # Save the processed signal
                    save_processed_data(
                        "market_sentiment",
                        sentiment_signal,
                        source_name=_SOURCE_NAME,
                        timestamp=iso_timestamp,
                    )

                # Create volume signal (number of articles)
                volume_signal = {
                    "name": "news_volume_market",
                    "value": len(articles),
                    "source": "financial_news",
                    "timestamp": iso_timestamp,
                    "metadata": {"metric": "volume"},
                }

                signals.append(volume_signal)

                # Save the processed signal
                save_processed_data(
                    "market_news_volume",
                    volume_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=iso_timestamp,
                )

        return signals
