"""
Example third-party API ingestion for Pulse (Twitter via Tweepy, production-ready)
"""
import os
import logging
import time
from irldata.scraper import SignalScraper
import tweepy
from core.celery_app import celery_app
from core.metrics import start_metrics_server
import threading

# Twitter API credentials from environment
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
QUERY = os.getenv("TWITTER_QUERY", "PulseAI")
POLL_INTERVAL = int(os.getenv("TWITTER_POLL_INTERVAL", "300"))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pulse.ingest_thirdparty")

def fetch_twitter_signals():
    # Start Prometheus metrics server in a background thread
    threading.Thread(target=start_metrics_server, daemon=True).start()
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        logger.error("Twitter API credentials not set in environment.")
        return
    auth = tweepy.OAuth1UserHandler(
        TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
    )
    api = tweepy.API(auth)
    scraper = SignalScraper()
    seen_ids = set()
    logger.info(f"Polling Twitter for query '{QUERY}' every {POLL_INTERVAL}s")
    while True:
        try:
            for tweet in tweepy.Cursor(api.search_tweets, q=QUERY, lang="en", tweet_mode="extended").items(20):
                if tweet.id in seen_ids:
                    continue
                try:
                    signal_data = {
                        "name": tweet.full_text[:64],
                        "value": float(tweet.favorite_count),
                        "source": "twitter",
                        "timestamp": tweet.created_at.isoformat() if hasattr(tweet.created_at, 'isoformat') else str(tweet.created_at)
                    }
                    celery_app.send_task("ingest_and_score_signal", args=[signal_data])
                    logger.info(f"Submitted tweet to Celery: {tweet.id} | {tweet.full_text[:40]}...")
                    seen_ids.add(tweet.id)
                except Exception as e:
                    logger.error(f"Failed to submit tweet to Celery: {e}")
            time.sleep(POLL_INTERVAL)
        except tweepy.errors.TweepyException as e:
            logger.error(f"Twitter API error: {e}")
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Twitter polling stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    fetch_twitter_signals()
