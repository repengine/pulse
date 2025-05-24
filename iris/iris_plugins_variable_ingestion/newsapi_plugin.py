"""NewsAPI — sentiment and news trend analysis plugin.

Connects to NewsAPI for monitoring global news trends and sentiment.
Requires NEWSAPI_KEY environment variable.
See: https://newsapi.org/
"""

import datetime as dt
import logging
import os
import re
import time
from collections import Counter
from typing import Dict, List, Any, Optional

import requests
from iris.iris_plugins import IrisPluginManager

logger = logging.getLogger(__name__)


class NewsapiPlugin(IrisPluginManager):
    plugin_name = "newsapi_plugin"
    enabled = True  # Will be set to False if API key is missing
    concurrency = 2  # Limit concurrent requests

    # API endpoints
    BASE_URL = "https://newsapi.org/v2"
    REQUEST_TIMEOUT = 10.0
    RETRY_WAIT = 1.5  # seconds between retries
    MAX_RETRIES = 2

    # Topic categories to monitor
    TOPICS = {
        "finance": [
            "economy",
            "finance",
            "stock market",
            "recession",
            "inflation",
            "crypto",
            "dollar",
            "fed",
        ],
        "geopolitics": [
            "diplomacy",
            "conflict",
            "war",
            "election",
            "summit",
            "treaty",
            "sanctions",
            "trade war",
        ],
        "technology": [
            "AI",
            "artificial intelligence",
            "innovation",
            "tech",
            "programming",
            "cybersecurity",
            "startup",
        ],
        "climate": [
            "climate change",
            "global warming",
            "environment",
            "renewable energy",
            "carbon",
            "pollution",
        ],
        "health": [
            "healthcare",
            "pandemic",
            "virus",
            "medicine",
            "vaccine",
            "disease",
            "epidemic",
            "public health",
        ],
    }

    # Major news sources to track
    NEWS_SOURCES = [
        "bbc-news",
        "cnn",
        "fox-news",
        "reuters",
        "associated-press",
        "bloomberg",
        "financial-times",
        "the-wall-street-journal",
        "the-economist",
        "the-washington-post",
        "al-jazeera-english",
    ]

    # Sentiment analysis keywords
    POSITIVE_KEYWORDS = [
        "growth",
        "recovery",
        "gain",
        "boost",
        "success",
        "positive",
        "improvement",
        "breakthrough",
        "advance",
        "progress",
        "optimism",
        "opportunity",
        "promising",
        "benefit",
        "prosper",
        "thrive",
        "rebound",
        "triumph",
    ]

    NEGATIVE_KEYWORDS = [
        "decline",
        "fall",
        "drop",
        "loss",
        "crisis",
        "downturn",
        "concern",
        "risk",
        "warning",
        "threat",
        "danger",
        "failure",
        "struggle",
        "conflict",
        "crash",
        "recession",
        "problem",
        "fear",
        "tension",
        "collapse",
        "disaster",
    ]

    def __init__(self):
        """Initialize NewsAPI plugin with API key."""
        self.api_key = os.getenv("NEWSAPI_KEY", "")
        if not self.api_key:
            logger.warning("NEWSAPI_KEY environment variable not set - plugin disabled")
            self.__class__.enabled = False

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch news sentiment and trends from NewsAPI."""
        if not self.api_key:
            return []

        signals = []
        now = dt.datetime.now()

        # Rotate through topics based on the day of the month
        topic_idx = now.day % len(self.TOPICS)
        topic_name = list(self.TOPICS.keys())[topic_idx]
        topic_keywords = self.TOPICS[topic_name]

        # Get top headlines for the selected topic
        headlines = self._fetch_topic_headlines(topic_name, topic_keywords)
        if not headlines:
            return signals

        # Calculate sentiment scores for the topic
        sentiment_score = self._calculate_sentiment(headlines)
        if sentiment_score is not None:
            signals.append(
                {
                    "name": f"news_{topic_name}_sentiment",
                    "value": sentiment_score,
                    "source": "newsapi",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                }
            )

        # Calculate coverage intensity (number of articles)
        coverage_score = self._calculate_coverage_intensity(headlines)
        if coverage_score is not None:
            signals.append(
                {
                    "name": f"news_{topic_name}_coverage",
                    "value": coverage_score,
                    "source": "newsapi",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                }
            )

        # Extract subtopic trends
        subtopics = self._extract_subtopic_trends(headlines, topic_keywords)
        for subtopic, score in subtopics.items():
            signals.append(
                {
                    "name": f"news_{topic_name}_{subtopic}_trend",
                    "value": score,
                    "source": "newsapi_trends",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                }
            )

        return signals

    def _safe_get(self, endpoint: str, params: dict) -> Optional[dict]:
        """Make a safe API request with retries and error handling."""
        headers = {"X-Api-Key": self.api_key}
        url = f"{self.BASE_URL}/{endpoint}"

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    url, headers=headers, params=params, timeout=self.REQUEST_TIMEOUT
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                logger.warning(
                    f"NewsAPI request failed ({attempt + 1}/{self.MAX_RETRIES}): {exc}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
        return None

    def _fetch_topic_headlines(
        self, topic_name: str, keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """Fetch headlines for a specific topic."""
        all_articles = []

        # Create a query from OR-ing the keywords
        query = " OR ".join(keywords)

        # Use top-headlines endpoint with sources
        params = {
            "q": query,
            "sources": ",".join(self.NEWS_SOURCES[:5]),  # API limits to 20 sources
            "language": "en",
            "pageSize": 100,
        }

        response = self._safe_get("top-headlines", params)
        if not response or "articles" not in response:
            # Fallback to everything endpoint if top-headlines fails
            params = {
                "q": query,
                "language": "en",
                "sortBy": "relevancy",
                "pageSize": 100,
            }
            response = self._safe_get("everything", params)

        if response and "articles" in response:
            all_articles.extend(response["articles"])

        # If we didn't get enough articles, try with the remaining sources
        if len(all_articles) < 50 and len(self.NEWS_SOURCES) > 5:
            params["sources"] = ",".join(
                self.NEWS_SOURCES[5:10]
            )  # Next batch of sources
            response = self._safe_get("top-headlines", params)
            if response and "articles" in response:
                all_articles.extend(response["articles"])

        return all_articles

    def _calculate_sentiment(self, articles: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate sentiment score from articles (-100 to 100)."""
        if not articles:
            return None

        total_score = 0
        total_articles = 0

        for article in articles:
            title = article.get("title", "").lower()
            description = (
                article.get("description", "").lower()
                if article.get("description")
                else ""
            )
            content = f"{title} {description}"

            # Count positive and negative keywords
            positive_count = sum(
                1 for keyword in self.POSITIVE_KEYWORDS if keyword in content
            )
            negative_count = sum(
                1 for keyword in self.NEGATIVE_KEYWORDS if keyword in content
            )

            # Calculate sentiment for this article (-1 to 1)
            if positive_count == 0 and negative_count == 0:
                # Neutral
                continue

            article_sentiment = (positive_count - negative_count) / max(
                positive_count + negative_count, 1
            )
            total_score += article_sentiment
            total_articles += 1

        if total_articles == 0:
            return 0

        # Normalize to -100 to 100 scale
        normalized_sentiment = (total_score / total_articles) * 100
        # Clamp to -100, 100 range
        return max(min(normalized_sentiment, 100), -100)

    def _calculate_coverage_intensity(
        self, articles: List[Dict[str, Any]]
    ) -> Optional[float]:
        """Calculate coverage intensity (0 to 100)."""
        if not articles:
            return 0

        # Base score on number of articles
        article_count = len(articles)

        # Calculate average published time (recency)
        now = dt.datetime.now(dt.timezone.utc)
        total_hours_ago = 0
        valid_dates = 0

        for article in articles:
            if "publishedAt" in article and article["publishedAt"]:
                try:
                    pub_time = dt.datetime.fromisoformat(
                        article["publishedAt"].replace("Z", "+00:00")
                    )
                    hours_ago = (now - pub_time).total_seconds() / 3600
                    total_hours_ago += hours_ago
                    valid_dates += 1
                except (ValueError, TypeError):
                    pass

        avg_hours_ago = total_hours_ago / max(valid_dates, 1)

        # Recency factor (higher for more recent news)
        recency_factor = max(0, min(1, 2 - (avg_hours_ago / 24)))

        # Calculate the final score
        # 100 articles in last 24 hours would be a perfect 100 score
        intensity_score = min(100, article_count * recency_factor)
        return intensity_score

    def _extract_subtopic_trends(
        self, articles: List[Dict[str, Any]], topic_keywords: List[str]
    ) -> Dict[str, float]:
        """Extract subtopic trends from articles."""
        if not articles:
            return {}

        # Initialize counters
        word_counter = Counter()
        bigram_counter = Counter()

        # Combine all text
        all_text = ""
        for article in articles:
            title = article.get("title", "")
            description = (
                article.get("description", "") if article.get("description") else ""
            )
            all_text += f"{title} {description} "

        # Clean text and extract words
        all_text = all_text.lower()
        # Remove special characters
        all_text = re.sub(r"[^\w\s]", " ", all_text)
        # Remove extra whitespace
        all_text = re.sub(r"\s+", " ", all_text).strip()

        # Split into words
        words = all_text.split()

        # Count single words (excluding common stopwords)
        stopwords = {
            "the",
            "and",
            "of",
            "to",
            "in",
            "a",
            "for",
            "on",
            "is",
            "that",
            "with",
            "said",
            "by",
            "as",
            "at",
            "from",
            "it",
            "was",
        }
        for word in words:
            if len(word) > 3 and word not in stopwords and word not in topic_keywords:
                word_counter[word] += 1

        # Count bigrams (pairs of words)
        for i in range(len(words) - 1):
            if words[i] not in stopwords and words[i + 1] not in stopwords:
                if len(words[i]) > 2 and len(words[i + 1]) > 2:
                    bigram = f"{words[i]}_{words[i + 1]}"
                    bigram_counter[bigram] += 1

        # Combine and normalize scores
        combined_trends = {}

        # Add top single words
        for word, count in word_counter.most_common(10):
            normalized_score = min(
                100, count * 5
            )  # Adjust multiplier based on typical counts
            combined_trends[word] = normalized_score

        # Add top bigrams
        for bigram, count in bigram_counter.most_common(5):
            normalized_score = min(
                100, count * 10
            )  # Bigrams typically have lower counts
            combined_trends[bigram] = normalized_score

        return combined_trends
