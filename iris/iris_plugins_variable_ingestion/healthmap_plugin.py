"""HealthMap RSS — health plugin.

Connects to HealthMap RSS feeds to track global disease outbreaks and health events.
HealthMap aggregates reports of disease outbreaks and health-related events from various 
sources around the world, providing real-time monitoring of emerging public health threats.

No API key required. Access is completely free through publicly available RSS feeds.
See: https://www.healthmap.org

This plugin collects data on:
- Global disease outbreak counts
- Regional health event activity
- Top disease trends
- Health alert levels by country/region
"""
import datetime as dt
import logging
import time
from typing import Dict, List, Any, Optional, Counter as CounterType
from collections import Counter
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, parse_qs

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
_SOURCE_NAME = "healthmap"

class HealthmapPlugin(IrisPluginManager):
    plugin_name = "healthmap_plugin"
    enabled = True     # No API key required
    concurrency = 2    # Limit concurrent requests to be nice to the API
    
    # HealthMap RSS configuration
    BASE_URL = "https://www.healthmap.org/rss"
    REQUEST_TIMEOUT = 15.0
    RETRY_WAIT = 1.0  # seconds between retries
    MAX_RETRIES = 2
    
    # RSS feed paths for different regions and categories
    FEEDS = {
        "global": "/healthmap.php",
        "us": "/healthmap.php?country=usa",
        "europe": "/healthmap.php?country=eur",
        "asia": "/healthmap.php?country=asia",
        "africa": "/healthmap.php?country=afr",
        "south_america": "/healthmap.php?country=sam"
    }
    
    # Categories to track
    CATEGORIES = [
        "Novel Coronavirus", "Influenza", "Measles", "Dengue", "Malaria", 
        "Ebola", "Cholera", "Tuberculosis", "Zika", "Unknown"
    ]
    
    # Mapping of regions to countries within that region (for signal generation)
    REGION_COUNTRIES = {
        "us": ["United States"],
        "europe": ["France", "Germany", "Italy", "Spain", "UK", "Poland", "Ukraine", "Netherlands", "Sweden"],
        "asia": ["China", "India", "Japan", "South Korea", "Indonesia", "Thailand", "Vietnam"],
        "africa": ["Nigeria", "South Africa", "Kenya", "Ethiopia", "Egypt", "Morocco", "Ghana"],
        "south_america": ["Brazil", "Argentina", "Colombia", "Peru", "Chile", "Venezuela"]
    }
    
    # Alert level mapping (parsed from HealthMap color codes)
    ALERT_LEVEL_MAP = {
        "red": 3,        # High alert
        "orange": 2,     # Medium alert
        "yellow": 1,     # Low alert
        "green": 0,      # Information only
    }

    def __init__(self):
        """Initialize the HealthMap plugin."""
        # Ensure data directory exists for this source
        ensure_data_directory(_SOURCE_NAME)
    
    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch health-related signals from HealthMap RSS feeds."""
        signals = []
        
        # Current timestamp
        now = dt.datetime.now(dt.timezone.utc)
        
        # Rotate through regions to avoid overloading the API
        # Using the day of the month modulo the number of feeds to select which feed to query
        region_key = self._get_rotation_region()
        feed_url = self._get_feed_url(region_key)
        
        # Fetch health events for the selected region
        events = self._fetch_health_events(feed_url, region_key)
        if not events:
            logger.warning(f"No health events found for region: {region_key}")
            return signals
        
        # Process events into signals
        signals.extend(self._process_health_events(events, region_key, now))
        
        return signals
    
    def _get_rotation_region(self) -> str:
        """Get region to use based on daily rotation."""
        day_of_month = dt.datetime.now().day
        regions = list(self.FEEDS.keys())
        return regions[day_of_month % len(regions)]
    
    def _get_feed_url(self, region_key: str) -> str:
        """Get the full feed URL for a region."""
        return f"{self.BASE_URL}{self.FEEDS[region_key]}"
    
    def _safe_get(self, url: str, dataset_id: str = "unknown") -> Optional[str]:
        """Make a safe API request with retries and error handling."""
        # Save request metadata
        save_request_metadata(
            dataset_id,
            {"url": url},
            source_name=_SOURCE_NAME,
            url=url
        )
        
        # Make request with retries
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    url,
                    timeout=self.REQUEST_TIMEOUT
                )
                resp.raise_for_status()
                
                # Save successful response
                save_api_response(
                    dataset_id,
                    {"response_text": resp.text[:10000]},  # Save first 10K chars (can be large)
                    source_name=_SOURCE_NAME,
                    status_code=resp.status_code,
                    headers=dict(resp.headers)
                )
                
                return resp.text
            except Exception as exc:
                logger.warning(f"HealthMap request failed ({attempt+1}/{self.MAX_RETRIES}): {exc}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
        
        # If all attempts failed, log the error
        logger.error(f"Failed to fetch data from HealthMap after {self.MAX_RETRIES} attempts")
        return None
    
    def _fetch_health_events(self, feed_url: str, region_key: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch health events from HealthMap RSS feed.
        
        Args:
            feed_url: URL of the RSS feed to query
            region_key: Key of the region being queried
            
        Returns:
            List of health event dictionaries or None if request failed
        """
        # Make request to RSS feed
        response_text = self._safe_get(feed_url, f"rss_{region_key}")
        if not response_text:
            return None
        
        try:
            # Parse RSS feed (XML)
            events = []
            root = ET.fromstring(response_text)
            
            # RSS structure: rss > channel > item
            channel = root.find("channel")
            if channel is None:
                logger.error("Invalid RSS feed: no channel element found")
                return None
            
            # Process each item (event)
            for item in channel.findall("item"):
                event = {}
                
                # Extract basic fields
                title_elem = item.find("title")
                event["title"] = title_elem.text if title_elem is not None else ""
                
                desc_elem = item.find("description")
                event["description"] = desc_elem.text if desc_elem is not None else ""
                
                link_elem = item.find("link")
                event["link"] = link_elem.text if link_elem is not None else ""
                
                pubdate_elem = item.find("pubDate")
                event["pub_date"] = pubdate_elem.text if pubdate_elem is not None else ""
                
                # Extract location and category from title and description
                event["location"] = self._extract_location(event["title"], event["description"])
                event["category"] = self._extract_category(event["title"], event["description"])
                
                # Extract alert level from link (color code in URL parameters)
                event["alert_level"] = self._extract_alert_level(event["link"])
                
                events.append(event)
            
            return events
            
        except ET.ParseError as e:
            logger.error(f"Error parsing HealthMap RSS feed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing HealthMap data: {e}")
            
        return None
    
    def _extract_location(self, title: str, description: str) -> str:
        """Extract location from event title and description."""
        # Location is typically at the start of the title, before the dash
        if "-" in title:
            return title.split("-")[0].strip()
        return "Unknown"
    
    def _extract_category(self, title: str, description: str) -> str:
        """Extract disease category from event title and description."""
        # Try to match known categories
        combined_text = f"{title} {description}".lower()
        
        for category in self.CATEGORIES:
            if category.lower() in combined_text:
                return category
        
        # Check for common terms that might indicate the category
        if "covid" in combined_text or "coronavirus" in combined_text:
            return "Novel Coronavirus"
        if "flu" in combined_text:
            return "Influenza"
        
        return "Unknown"
    
    def _extract_alert_level(self, link: str) -> int:
        """Extract alert level from event link."""
        try:
            # Parse URL parameters
            parsed_url = urlparse(link)
            params = parse_qs(parsed_url.query)
            
            # Check for color parameter which indicates alert level
            if "c" in params:
                color = params["c"][0].lower()
                return self.ALERT_LEVEL_MAP.get(color, 0)
        except Exception:
            pass
            
        return 0  # Default: information only
    
    def _process_health_events(self, events: List[Dict[str, Any]], region_key: str,
                             timestamp: dt.datetime) -> List[Dict[str, Any]]:
        """Process health events into signals.
        
        Args:
            events: List of health event dictionaries
            region_key: Key of the region being processed
            timestamp: Timestamp for the signals
            
        Returns:
            List of signals derived from health events
        """
        signals = []
        
        # Count events by category
        category_counts = Counter()
        for event in events:
            category_counts[event["category"]] += 1
        
        # Count events by location (country/region)
        location_counts = Counter()
        for event in events:
            location_counts[event["location"]] += 1
        
        # Calculate average alert level
        total_alert_level = sum(event["alert_level"] for event in events)
        avg_alert_level = total_alert_level / len(events) if events else 0
        
        # Create signals
        iso_timestamp = timestamp.isoformat()
        
        # Signal 1: Total event count for the region
        total_signal = {
            "name": f"healthmap_{region_key}_events_total",
            "value": len(events),
            "source": "healthmap",
            "timestamp": iso_timestamp,
            "metadata": {
                "region": region_key,
                "interpretation": "higher=more health events reported"
            }
        }
        
        save_processed_data(
            f"healthmap_{region_key}_total",
            total_signal,
            source_name=_SOURCE_NAME,
            timestamp=iso_timestamp
        )
        
        signals.append(total_signal)
        
        # Signal 2: Events by category
        for category, count in category_counts.most_common(5):  # Top 5 categories
            if not category:
                category = "unknown"
                
            # Normalize category name for signal name
            category_key = category.lower().replace(" ", "_")
            
            category_signal = {
                "name": f"healthmap_{region_key}_{category_key}_events",
                "value": count,
                "source": "healthmap",
                "timestamp": iso_timestamp,
                "metadata": {
                    "region": region_key,
                    "category": category,
                    "interpretation": "higher=more events for this disease category"
                }
            }
            
            save_processed_data(
                f"healthmap_{region_key}_{category_key}",
                category_signal,
                source_name=_SOURCE_NAME,
                timestamp=iso_timestamp
            )
            
            signals.append(category_signal)
        
        # Signal 3: Average alert level for the region
        alert_signal = {
            "name": f"healthmap_{region_key}_alert_level",
            "value": avg_alert_level,
            "source": "healthmap",
            "timestamp": iso_timestamp,
            "metadata": {
                "region": region_key,
                "range": "[0,3]",
                "interpretation": "higher=more severe health alerts"
            }
        }
        
        save_processed_data(
            f"healthmap_{region_key}_alert",
            alert_signal,
            source_name=_SOURCE_NAME,
            timestamp=iso_timestamp
        )
        
        signals.append(alert_signal)
        
        # Signal 4: Events for specific countries in the region
        if region_key in self.REGION_COUNTRIES:
            for country in self.REGION_COUNTRIES[region_key]:
                # Check if this country was mentioned in any location
                country_events = 0
                for location, count in location_counts.items():
                    if country.lower() in location.lower():
                        country_events += count
                
                if country_events > 0:
                    # Normalize country name for signal name
                    country_key = country.lower().replace(" ", "_")
                    
                    country_signal = {
                        "name": f"healthmap_{country_key}_events",
                        "value": country_events,
                        "source": "healthmap",
                        "timestamp": iso_timestamp,
                        "metadata": {
                            "country": country,
                            "region": region_key,
                            "interpretation": "higher=more health events in this country"
                        }
                    }
                    
                    save_processed_data(
                        f"healthmap_{country_key}",
                        country_signal,
                        source_name=_SOURCE_NAME,
                        timestamp=iso_timestamp
                    )
                    
                    signals.append(country_signal)
        
        return signals