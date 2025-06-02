"""Hacker News API — technology plugin.

Connects to the Hacker News Firebase API to track top stories,
trending technologies, and tech sentiment.
No API key required. Access is completely free.
See: https://github.com/HackerNews/API
"""

import datetime as dt
import logging
import time
from typing import Dict, List, Any, Optional

import requests
from ingestion.iris_plugins import IrisPluginManager

logger = logging.getLogger(__name__)


class HackerNewsPlugin(IrisPluginManager):
    plugin_name = "hackernews_plugin"
    enabled = True  # No API key required
    concurrency = 2  # Limit concurrent requests to be nice to the API

    # API endpoints
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    REQUEST_TIMEOUT = 10.0
    RETRY_WAIT = 1.0  # seconds between retries
    MAX_RETRIES = 2

    # Technology keywords to track
    TECH_KEYWORDS = {
        "ai": [
            "ai",
            "artificial intelligence",
            "machine learning",
            "ml",
            "deep learning",
            "llm",
            "chatgpt",
            "gpt",
            "large language model",
        ],
        "crypto": [
            "crypto",
            "bitcoin",
            "ethereum",
            "blockchain",
            "web3",
            "nft",
            "defi",
            "cryptocurrency",
        ],
        "cloud": [
            "cloud",
            "aws",
            "azure",
            "gcp",
            "serverless",
            "kubernetes",
            "k8s",
            "containers",
            "docker",
        ],
        "mobile": [
            "ios",
            "android",
            "mobile",
            "app store",
            "play store",
            "swift",
            "kotlin",
        ],
        "webdev": [
            "javascript",
            "typescript",
            "react",
            "vue",
            "angular",
            "node.js",
            "nextjs",
            "frontend",
            "backend",
        ],
        "database": [
            "database",
            "sql",
            "nosql",
            "postgres",
            "mongodb",
            "mysql",
            "redis",
            "data warehouse",
            "dbt",
        ],
        "devops": [
            "devops",
            "ci/cd",
            "github actions",
            "gitlab",
            "jenkins",
            "terraform",
            "infrastructure as code",
            "iac",
        ],
        "security": [
            "security",
            "cybersecurity",
            "hack",
            "vulnerability",
            "cve",
            "exploit",
            "privacy",
            "encryption",
        ],
    }

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch technology signals from Hacker News."""
        signals = []

        # Step 1: Get top stories
        story_ids = self._fetch_top_stories()
        if not story_ids:
            return signals

        # Step 2: Analyze technology trends in stories
        signals.extend(self._analyze_tech_trends(story_ids))

        # Step 3: Get item scores for top stories
        story_scores = self._fetch_story_scores(story_ids[:30])  # Limit to top 30
        if story_scores:
            signals.append(
                {
                    "name": "hn_top_story_avg_score",
                    "value": sum(story_scores) / len(story_scores),
                    "source": "hackernews",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                }
            )

        return signals

    def _safe_get(self, url: str) -> Optional[Any]:
        """Make a safe API request with retries and error handling."""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(url, timeout=self.REQUEST_TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                logger.warning(
                    f"Hacker News API request failed ({attempt + 1}/{self.MAX_RETRIES}): {exc}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
        return None

    def _fetch_top_stories(self) -> List[int]:
        """Fetch IDs of the top 500 stories on Hacker News."""
        url = f"{self.BASE_URL}/topstories.json"
        story_ids = self._safe_get(url)
        if not isinstance(story_ids, list):
            logger.warning("Failed to fetch top stories")
            return []
        return story_ids

    def _fetch_story_scores(self, story_ids: List[int]) -> List[int]:
        """Fetch scores for the given story IDs."""
        scores = []
        for story_id in story_ids:
            url = f"{self.BASE_URL}/item/{story_id}.json"
            story = self._safe_get(url)
            if story and isinstance(story, dict) and "score" in story:
                scores.append(story["score"])
            time.sleep(0.1)  # Be nice to the API
        return scores

    def _fetch_story_details(self, story_id: int) -> Optional[Dict[str, Any]]:
        """Fetch details for a specific story."""
        url = f"{self.BASE_URL}/item/{story_id}.json"
        return self._safe_get(url)

    def _analyze_tech_trends(self, story_ids: List[int]) -> List[Dict[str, Any]]:
        """Analyze technology trends in the top stories."""
        # Initialize counters for each tech category
        topic_counts = {category: 0 for category in self.TECH_KEYWORDS}
        processed_stories = 0

        # Limit to a sample of stories for efficiency
        sample_size = min(100, len(story_ids))

        for story_id in story_ids[:sample_size]:
            story = self._fetch_story_details(story_id)
            if not story or not isinstance(story, dict):
                continue

            # Get the story title and text (if available)
            title = story.get("title", "").lower()
            text = story.get("text", "").lower()
            content = f"{title} {text}"

            # Count occurrences of tech keywords
            for category, keywords in self.TECH_KEYWORDS.items():
                if any(keyword in content for keyword in keywords):
                    topic_counts[category] += 1

            processed_stories += 1
            time.sleep(0.1)  # Be nice to the API

        # Create signals for technology trends
        signals = []
        if processed_stories > 0:
            timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
            for category, count in topic_counts.items():
                percentage = (count / processed_stories) * 100
                signals.append(
                    {
                        "name": f"hn_trend_{category}",
                        "value": percentage,
                        "source": "hackernews_trends",
                        "timestamp": timestamp,
                        "metadata": {
                            "sample_size": processed_stories,
                            "absolute_count": count,
                        },
                    }
                )

        return signals
