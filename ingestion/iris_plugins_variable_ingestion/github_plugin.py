"""GitHub REST API — technology plugin.

Connects to GitHub API for monitoring open source trends and developer activity.
Requires GITHUB_TOKEN environment variable.
See: https://docs.github.com/en/rest
"""

import datetime as dt
import logging
import os
import time
from typing import Dict, List, Any, Optional, Tuple

import requests
from ingestion.iris_plugins import IrisPluginManager

logger = logging.getLogger(__name__)


class GithubPlugin(IrisPluginManager):
    plugin_name = "github_plugin"
    enabled = True  # Will be set to False if API token is missing
    concurrency = 2  # Limit concurrent requests

    # API endpoint
    BASE_URL = "https://api.github.com"
    REQUEST_TIMEOUT = 15.0
    RETRY_WAIT = 2.0  # seconds between retries
    MAX_RETRIES = 3

    # Technology domains to track
    TECH_DOMAINS = {
        "ai": [
            "machine-learning",
            "artificial-intelligence",
            "deep-learning",
            "nlp",
            "tensorflow",
            "pytorch",
        ],
        "web": [
            "javascript",
            "typescript",
            "react",
            "vue",
            "angular",
            "node",
            "frontend",
        ],
        "backend": ["java", "python", "go", "rust", "c-sharp", "microservices", "api"],
        "mobile": ["android", "ios", "flutter", "react-native", "kotlin", "swift"],
        "cloud": [
            "kubernetes",
            "docker",
            "aws",
            "azure",
            "gcp",
            "devops",
            "serverless",
        ],
        "blockchain": [
            "blockchain",
            "web3",
            "ethereum",
            "solidity",
            "nft",
            "cryptocurrency",
        ],
        "iot": ["iot", "raspberry-pi", "arduino", "embedded", "electronics"],
    }

    # Popular repositories to monitor by domain
    DOMAIN_REPOS = {
        "ai": [
            "huggingface/transformers",
            "pytorch/pytorch",
            "tensorflow/tensorflow",
            "scikit-learn/scikit-learn",
            "microsoft/DeepSpeed",
        ],
        "web": [
            "facebook/react",
            "vuejs/vue",
            "angular/angular",
            "vercel/next.js",
            "sveltejs/svelte",
        ],
        "backend": [
            "golang/go",
            "rust-lang/rust",
            "python/cpython",
            "openjdk/jdk",
            "dotnet/runtime",
        ],
        "mobile": [
            "flutter/flutter",
            "facebook/react-native",
            "android/platform_frameworks_base",
            "apple/swift",
            "kotlin/kotlin",
        ],
    }

    def __init__(self):
        """Initialize GitHub API plugin with OAuth token."""
        self.token = os.getenv("GITHUB_TOKEN", "")
        if not self.token:
            logger.warning(
                "GITHUB_TOKEN environment variable not set - plugin disabled"
            )
            self.__class__.enabled = False

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch technology signals from GitHub API."""
        if not self.token:
            return []

        signals = []
        now = dt.datetime.now()

        # Rotate through tech domains based on the day of the month
        domain_idx = now.day % len(self.TECH_DOMAINS)
        domain_name = list(self.TECH_DOMAINS.keys())[domain_idx]
        domain_topics = self.TECH_DOMAINS[domain_name]

        # 1. Get trending repositories for the domain
        trending_repos = self._fetch_trending_repositories(domain_topics)
        if trending_repos:
            # Calculate domain popularity score based on stars in trending repos
            domain_popularity = self._calculate_domain_popularity(trending_repos)
            signals.append(
                {
                    "name": f"github_{domain_name}_popularity",
                    "value": domain_popularity,
                    "source": "github",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                }
            )

        # 2. Track specific repositories in the domain
        # Get domain-specific repos
        if domain_name in self.DOMAIN_REPOS:
            repo_signals = self._track_specific_repos(self.DOMAIN_REPOS[domain_name])
            signals.extend(repo_signals)

        # 3. Analyze activity trends for the domain
        activity_signals = self._analyze_activity_trends(domain_name, domain_topics)
        signals.extend(activity_signals)

        return signals

    def _safe_get(
        self, endpoint: str, params: Optional[dict] = None
    ) -> Tuple[Any, Any]:
        """Make a safe API request with retries and error handling."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        url = f"{self.BASE_URL}/{endpoint}"

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    url, headers=headers, params=params, timeout=self.REQUEST_TIMEOUT
                )

                # Check for rate limiting
                if resp.status_code == 403 and "X-RateLimit-Remaining" in resp.headers:
                    if int(resp.headers["X-RateLimit-Remaining"]) == 0:
                        reset_time = int(resp.headers["X-RateLimit-Reset"])
                        sleep_time = max(1, reset_time - time.time())
                        logger.warning(
                            f"GitHub API rate limit reached. Sleeping for {
                                sleep_time:.1f} seconds.")
                        time.sleep(sleep_time)
                        continue

                resp.raise_for_status()

                # For paginated results, include link header info
                pagination_info = None
                if "Link" in resp.headers:
                    pagination_info = resp.headers["Link"]

                return resp.json(), pagination_info
            except Exception as exc:
                logger.warning(
                    f"GitHub API request failed ({attempt + 1}/{self.MAX_RETRIES}): {exc}"
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
        return None, None

    def _fetch_trending_repositories(self, topics: List[str]) -> List[Dict[str, Any]]:
        """Fetch trending repositories for the given topics."""
        trending_repos = []

        # Search for repositories with the given topics
        # Use created or pushed date from the past month to focus on active repos
        for topic in topics[:3]:  # Limit to 3 topics to avoid excessive API calls
            # Search for repositories with this topic, sorted by stars
            params = {
                "q": f"topic:{topic} pushed:>1y",
                "sort": "stars",
                "order": "desc",
                "per_page": 10,
            }

            result, _ = self._safe_get("search/repositories", params)
            if result is not None and "items" in result:
                trending_repos.extend(result["items"])

            # Be nice to the API
            time.sleep(1.0)

        return trending_repos

    def _calculate_domain_popularity(self, repositories: List[Dict[str, Any]]) -> float:
        """Calculate domain popularity score based on stars and recent activity."""
        if not repositories:
            return 0.0

        total_stars = sum(repo.get("stargazers_count", 0) for repo in repositories)
        total_forks = sum(repo.get("forks_count", 0) for repo in repositories)

        # Calculate weighted score
        score = total_stars + (
            total_forks * 2
        )  # Forks indicate higher engagement than stars

        # Normalize to 0-100 scale
        # 10k stars is a very popular domain (score of 100)
        normalized_score = min(100.0, score / 100.0)
        return normalized_score

    def _track_specific_repos(self, repos: List[str]) -> List[Dict[str, Any]]:
        """Track specific important repositories."""
        signals = []

        for repo_path in repos[:3]:  # Limit to 3 repos per run
            # Get repository information
            result, _ = self._safe_get(f"repos/{repo_path}")
            if result is None:
                continue

            # Extract key metrics
            stars = result.get("stargazers_count", 0)
            forks = result.get("forks_count", 0)
            issues = result.get("open_issues_count", 0)
            name = result.get("name", "").lower()

            # Create signal for stars (popularity)
            signals.append(
                {
                    "name": f"github_repo_{name}_stars",
                    "value": stars,
                    "source": "github",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "metadata": {
                        "repo_path": repo_path,
                        "forks": forks,
                        "issues": issues,
                    },
                }
            )

            # Get recent commits to measure activity
            commits_result, _ = self._safe_get(
                f"repos/{repo_path}/commits", {"per_page": 30}
            )
            if commits_result is not None and isinstance(commits_result, list):
                # Count commits in the past 7 days
                recent_commits = 0
                seven_days_ago = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)

                for commit in commits_result:
                    if (
                        "commit" in commit
                        and "author" in commit["commit"]
                        and "date" in commit["commit"]["author"]
                    ):
                        try:
                            commit_date = dt.datetime.fromisoformat(
                                commit["commit"]["author"]["date"].replace(
                                    "Z", "+00:00"
                                )
                            )
                            if commit_date > seven_days_ago:
                                recent_commits += 1
                        except (ValueError, TypeError):
                            pass

                # Create signal for recent activity
                signals.append(
                    {
                        "name": f"github_repo_{name}_activity",
                        "value": recent_commits,
                        "source": "github",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    }
                )

            # Be nice to the API
            time.sleep(1.0)

        return signals

    def _analyze_activity_trends(
        self, domain_name: str, topics: List[str]
    ) -> List[Dict[str, Any]]:
        """Analyze activity trends for the domain."""
        signals = []

        # Get overall topic activity
        for topic in topics[:2]:  # Limit to 2 topics
            # Search for repositories created in the past 30 days
            params = {
                "q": f"topic:{topic} created:>1month",
                "sort": "stars",
                "order": "desc",
                "per_page": 30,
            }

            result, _ = self._safe_get("search/repositories", params)
            if result is not None and "total_count" in result:
                new_repo_count = result["total_count"]

                signals.append(
                    {
                        "name": f"github_{topic}_new_repos",
                        "value": min(100, new_repo_count),  # Cap at 100 to normalize
                        "source": "github_trends",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    }
                )

            # Be nice to the API
            time.sleep(1.0)

            # Get recent issues for the topic
            params = {
                "q": f"topic:{topic} is:issue created:>1week",
                "sort": "created",
                "order": "desc",
                "per_page": 30,
            }

            result, _ = self._safe_get("search/issues", params)
            if result is not None and "total_count" in result:
                new_issue_count = result["total_count"]

                signals.append(
                    {
                        "name": f"github_{topic}_new_issues",
                        "value": min(100, new_issue_count),  # Cap at 100 to normalize
                        "source": "github_trends",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    }
                )

            # Be nice to the API
            time.sleep(1.0)

        return signals
