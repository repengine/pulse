"""Reddit API — sentiment plugin.

Connects to Reddit API for monitoring social sentiment across various topics.
Requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT environment variables.
"""

import datetime as dt
import logging
import os
import time
from typing import Dict, List, Any, Optional

import requests
from ingestion.iris_plugins import IrisPluginManager

logger = logging.getLogger(__name__)


class RedditPlugin(IrisPluginManager):
    plugin_name = "reddit_plugin"
    enabled = True  # Will be set to False if API credentials are missing
    concurrency = 2  # Limit concurrent requests

    # API endpoints
    OAUTH_URL = "https://www.reddit.com/api/v1/access_token"
    API_BASE_URL = "https://oauth.reddit.com"
    REQUEST_TIMEOUT = 10.0
    RETRY_WAIT = 1.5  # seconds between retries
    MAX_RETRIES = 2

    # Subreddits to monitor, organized by category
    SUBREDDITS = {
        "finance": [
            "investing",
            "stocks",
            "finance",
            "wallstreetbets",
            "cryptocurrency",
        ],
        "technology": [
            "technology",
            "programming",
            "cscareerquestions",
            "artificial",
            "MachineLearning",
        ],
        "politics": ["politics", "worldnews", "geopolitics", "economics"],
        "health": ["health", "medicine", "COVID19", "science"],
        "climate": ["climate", "environment", "climatechange", "renewableenergy"],
    }

    # Sentiment keywords
    POSITIVE_KEYWORDS = [
        "bullish",
        "optimistic",
        "positive",
        "growth",
        "opportunity",
        "gain",
        "profit",
        "breakthrough",
        "success",
        "innovative",
        "promising",
        "excited",
        "potential",
        "recovery",
        "advance",
        "progress",
        "improvement",
        "thrive",
        "excellent",
    ]

    NEGATIVE_KEYWORDS = [
        "bearish",
        "pessimistic",
        "negative",
        "decline",
        "risk",
        "loss",
        "crash",
        "danger",
        "recession",
        "threat",
        "failure",
        "crisis",
        "worry",
        "concern",
        "collapse",
        "downturn",
        "struggle",
        "fear",
        "terrible",
        "disaster",
    ]

    def __init__(self):
        """Initialize Reddit API plugin with OAuth credentials."""
        self.client_id = os.getenv("REDDIT_CLIENT_ID", "")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "Pulse/1.0")

        if not all([self.client_id, self.client_secret]):
            logger.warning("Reddit API credentials not set - plugin disabled")
            self.__class__.enabled = False

        self.access_token = None
        self.token_expiry = 0

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch social sentiment signals from Reddit."""
        if not self.__class__.enabled:
            return []

        signals = []
        now = dt.datetime.now()

        # Ensure we have a valid token
        if not self._ensure_access_token():
            return []

        # Rotate through categories based on the day
        category_idx = now.day % len(self.SUBREDDITS)
        category = list(self.SUBREDDITS.keys())[category_idx]
        subreddits = self.SUBREDDITS[category]

        # For each subreddit in the selected category
        for subreddit in subreddits:
            # Get hot posts from the subreddit
            posts = self._get_hot_posts(subreddit)
            if not posts:
                continue

            # Calculate sentiment scores
            sentiment_score = self._calculate_sentiment(posts)
            if sentiment_score is not None:
                signals.append(
                    {
                        "name": f"reddit_{subreddit}_sentiment",
                        "value": sentiment_score,
                        "source": "reddit",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    }
                )

            # Calculate activity level (normalized post score)
            activity_score = self._calculate_activity(posts)
            if activity_score is not None:
                signals.append(
                    {
                        "name": f"reddit_{subreddit}_activity",
                        "value": activity_score,
                        "source": "reddit",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    }
                )

            # Be nice to the API
            time.sleep(1.0)

        return signals

    def _ensure_access_token(self) -> bool:
        """Ensure we have a valid OAuth access token."""
        now = time.time()
        if not self.access_token or now >= self.token_expiry:
            return self._get_access_token()
        return True

    def _get_access_token(self) -> bool:
        """Get OAuth access token."""
        try:
            auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
            headers = {"User-Agent": self.user_agent}
            data = {"grant_type": "client_credentials"}

            resp = requests.post(
                self.OAUTH_URL,
                auth=auth,
                headers=headers,
                data=data,
                timeout=self.REQUEST_TIMEOUT,
            )
            resp.raise_for_status()

            token_data = resp.json()
            self.access_token = token_data["access_token"]
            # Set expiry a bit before the actual expiry to be safe
            self.token_expiry = time.time() + token_data["expires_in"] - 60
            return True
        except Exception as exc:
            logger.error(f"Failed to get Reddit access token: {exc}")
            return False

    def _safe_get(self, url: str, params: dict = None) -> Optional[dict]:
        """Make a safe API request with retries and error handling."""
        if not self._ensure_access_token():
            return None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": self.user_agent,
        }

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    url, headers=headers, params=params, timeout=self.REQUEST_TIMEOUT
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                logger.warning(
                    f"Reddit API request failed ({attempt + 1}/{self.MAX_RETRIES}): {exc}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
        return None

    def _get_hot_posts(self, subreddit: str, limit: int = 25) -> List[Dict]:
        """Get hot posts from a subreddit."""
        url = f"{self.API_BASE_URL}/r/{subreddit}/hot"
        params = {"limit": limit}

        response = self._safe_get(url, params)
        if not response or "data" not in response or "children" not in response["data"]:
            logger.warning(f"Failed to get posts from r/{subreddit}")
            return []

        return [post["data"] for post in response["data"]["children"]]

    def _calculate_sentiment(self, posts: List[Dict]) -> Optional[float]:
        """Calculate sentiment score from posts (-100 to 100)."""
        if not posts:
            return None

        total_score = 0

        for post in posts:
            title = post.get("title", "").lower()
            selftext = post.get("selftext", "").lower()
            content = f"{title} {selftext}"

            # Count positive and negative keywords
            positive_count = sum(
                1 for keyword in self.POSITIVE_KEYWORDS if keyword in content
            )
            negative_count = sum(
                1 for keyword in self.NEGATIVE_KEYWORDS if keyword in content
            )

            # Calculate sentiment for this post (-1 to 1)
            if positive_count == 0 and negative_count == 0:
                post_sentiment = 0
            else:
                post_sentiment = (positive_count - negative_count) / max(
                    positive_count + negative_count, 1
                )

            # Weight by post score (upvotes - downvotes)
            post_score = post.get("score", 0)
            weighted_sentiment = post_sentiment * post_score

            total_score += weighted_sentiment

        # Normalize to -100 to 100 scale
        total_upvotes = sum(post.get("score", 0) for post in posts)
        if total_upvotes == 0:
            return 0

        normalized_sentiment = (total_score / total_upvotes) * 100
        # Clamp to -100, 100 range
        return max(min(normalized_sentiment, 100), -100)

    def _calculate_activity(self, posts: List[Dict]) -> Optional[float]:
        """Calculate activity level (0 to 100)."""
        if not posts:
            return None

        # Sum up scores and comment counts
        total_score = sum(post.get("score", 0) for post in posts)
        total_comments = sum(post.get("num_comments", 0) for post in posts)

        # Basic activity score based on post scores and comments
        # Use logarithmic scale since popular subreddits can have very high scores
        activity_raw = total_score + (
            total_comments * 3
        )  # Weight comments more heavily

        # Normalize to 0-100 scale with a logarithmic transformation
        # This formula assumes typical Reddit activity levels
        if activity_raw <= 0:
            return 0

        activity_score = min(100, 20 * max(0, (activity_raw**0.5) / 50))
        return activity_score
