"""Google Trends API — sentiment plugin.

Connects to Google Trends API (via pytrends) for monitoring search interest across topics.
No API key required, but uses the unofficial pytrends wrapper.
Requires pytrends package: pip install pytrends
"""
import datetime as dt
import logging
import time
from typing import Dict, List, Any, Optional

import requests
from iris.iris_plugins import IrisPluginManager

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    logging.warning("pytrends package not found. Install with: pip install pytrends")

logger = logging.getLogger(__name__)

class GoogleTrendsPlugin(IrisPluginManager):
    plugin_name = "google_trends_plugin"
    enabled = PYTRENDS_AVAILABLE     # Enabled if pytrends is installed
    concurrency = 1    # Limited to avoid Google throttling
    
    # Request configuration
    REQUEST_TIMEOUT = 30.0
    RETRY_WAIT = 5.0  # seconds between retries (Google Trends can be sensitive to rapid requests)
    MAX_RETRIES = 3
    
    # Topic categories and their associated keywords
    TOPIC_CATEGORIES = {
        "finance": [
            "stock market", "cryptocurrency", "inflation", "recession", 
            "interest rates", "federal reserve", "bitcoin", "tesla stock"
        ],
        "technology": [
            "artificial intelligence", "machine learning", "cybersecurity", 
            "metaverse", "blockchain", "cloud computing", "quantum computing"
        ],
        "health": [
            "covid vaccine", "pandemic", "healthcare", "mental health", 
            "telehealth", "public health", "virus outbreak"
        ],
        "climate": [
            "climate change", "renewable energy", "carbon emissions", 
            "sustainability", "global warming", "solar power", "electric vehicles"
        ],
        "geopolitics": [
            "elections", "war", "sanctions", "trade war", 
            "international relations", "summit", "military conflict"
        ]
    }
    
    # Geographic regions to consider
    GEO_REGIONS = {
        "global": "",      # Empty string means global
        "us": "US",        # United States
        "uk": "GB",        # United Kingdom
        "eu": "EU",        # European Union
        "in": "IN",        # India
        "cn": "CN",        # China
        "jp": "JP",        # Japan
        "br": "BR",        # Brazil
    }

    def __init__(self):
        """Initialize Google Trends plugin."""
        if not PYTRENDS_AVAILABLE:
            self.__class__.enabled = False
            return
            
        try:
            # Initialize the TrendReq with English language, global region
            self.pytrends = TrendReq(hl='en-US', tz=0, timeout=(5, 25), retries=2, backoff_factor=0.5)
            self.__class__.enabled = True
        except Exception as e:
            logger.error(f"Failed to initialize pytrends: {e}")
            self.__class__.enabled = False

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch search interest trends from Google Trends."""
        if not self.__class__.enabled:
            return []
            
        signals = []
        now = dt.datetime.now()
        
        # Rotate through topic categories based on the day of the month
        category_idx = now.day % len(self.TOPIC_CATEGORIES)
        category_name = list(self.TOPIC_CATEGORIES.keys())[category_idx]
        category_keywords = self.TOPIC_CATEGORIES[category_name]
        
        # Also rotate through regions
        region_idx = now.day % len(self.GEO_REGIONS)
        region_name = list(self.GEO_REGIONS.keys())[region_idx]
        region_code = self.GEO_REGIONS[region_name]
        
        # Get interest over time for up to 5 keywords in the category
        # (Google Trends limits to 5 keywords per request)
        keywords = category_keywords[:5]
        time_signals = self._get_interest_over_time(keywords, category_name, region_name, region_code)
        signals.extend(time_signals)
        
        # Delay to avoid rate limiting
        time.sleep(1.0)
        
        # Get related topics for the first keyword
        if keywords:
            related_signals = self._get_related_topics(keywords[0], category_name, region_name, region_code)
            signals.extend(related_signals)
        
        # Delay to avoid rate limiting
        time.sleep(1.0)
        
        # Get interest by region for the first keyword
        if keywords:
            geo_signals = self._get_interest_by_region(keywords[0], category_name, region_name, region_code)
            signals.extend(geo_signals)
        
        return signals

    def _get_interest_over_time(self, keywords: List[str], category: str, 
                               region_name: str, region_code: str) -> List[Dict[str, Any]]:
        """Get interest over time for the given keywords."""
        signals = []
        
        try:
            # Build payload for the request
            timeframe = "today 3-m"  # Last 90 days
            self.pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=region_code)
            
            # Get interest over time
            interest_over_time_df = self.pytrends.interest_over_time()
            
            # Skip if no data
            if interest_over_time_df.empty:
                return signals
                
            # Get the most recent data point for each keyword
            latest_data = interest_over_time_df.iloc[-1]
            
            for keyword in keywords:
                if keyword in latest_data:
                    interest_value = float(latest_data[keyword])
                    normalized_keyword = keyword.replace(" ", "_").lower()
                    
                    signals.append({
                        "name": f"gtrends_{category}_{normalized_keyword}_{region_name}",
                        "value": interest_value,
                        "source": "google_trends",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "keyword": keyword,
                            "category": category,
                            "region": region_name,
                            "relative_value": True  # Google Trends values are relative
                        }
                    })
        except Exception as e:
            logger.warning(f"Failed to get interest over time: {e}")
            
        return signals

    def _get_related_topics(self, keyword: str, category: str, 
                           region_name: str, region_code: str) -> List[Dict[str, Any]]:
        """Get related topics for a keyword."""
        signals = []
        
        try:
            # Build payload for the request
            timeframe = "today 3-m"  # Last 90 days
            self.pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=region_code)
            
            # Get related topics
            related_topics = self.pytrends.related_topics()
            
            if keyword not in related_topics:
                return signals
                
            # Process top related topics
            top_topics = related_topics[keyword].get("top", None)
            if top_topics is None or top_topics.empty:
                return signals
                
            # Get up to 5 top related topics
            for _, row in top_topics.head(5).iterrows():
                if "value" in row and "topic_title" in row:
                    topic_title = row["topic_title"]
                    interest_value = float(row["value"])
                    normalized_topic = topic_title.replace(" ", "_").lower()[:20]  # Limit length
                    
                    signals.append({
                        "name": f"gtrends_{category}_related_{normalized_topic}_{region_name}",
                        "value": interest_value,
                        "source": "google_trends_related",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "keyword": keyword,
                            "related_topic": topic_title,
                            "category": category,
                            "region": region_name
                        }
                    })
        except Exception as e:
            logger.warning(f"Failed to get related topics: {e}")
            
        return signals

    def _get_interest_by_region(self, keyword: str, category: str, 
                               region_name: str, region_code: str) -> List[Dict[str, Any]]:
        """Get interest by region for a keyword."""
        signals = []
        
        try:
            # Build payload for the request
            timeframe = "today 3-m"  # Last 90 days
            self.pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=region_code)
            
            # Get interest by region
            if region_code == "":  # Global
                # Get interest by country
                interest_by_region_df = self.pytrends.interest_by_country()
            else:
                # Get interest by region within country
                interest_by_region_df = self.pytrends.interest_by_region(resolution='COUNTRY')
            
            # Skip if no data
            if interest_by_region_df.empty:
                return signals
                
            # Normalize the keyword for signal name
            normalized_keyword = keyword.replace(" ", "_").lower()
            
            # Calculate average interest across regions
            avg_interest = interest_by_region_df[keyword].mean()
            
            signals.append({
                "name": f"gtrends_{category}_{normalized_keyword}_avg_regional_interest",
                "value": float(avg_interest),
                "source": "google_trends_regional",
                "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                "metadata": {
                    "keyword": keyword,
                    "category": category,
                    "region_scope": region_name,
                    "sample_size": len(interest_by_region_df)
                }
            })
            
            # Calculate regional variance/dispersion
            interest_variance = interest_by_region_df[keyword].var()
            
            signals.append({
                "name": f"gtrends_{category}_{normalized_keyword}_regional_variance",
                "value": float(interest_variance),
                "source": "google_trends_regional",
                "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                "metadata": {
                    "keyword": keyword,
                    "category": category,
                    "region_scope": region_name
                }
            })
            
        except Exception as e:
            logger.warning(f"Failed to get interest by region: {e}")
            
        return signals
