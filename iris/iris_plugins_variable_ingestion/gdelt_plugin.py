"""GDELT v2 REST API — geopolitical events plugin.

Connects to the GDELT (Global Database of Events, Language, and Tone) API to track
global events and media narratives. This plugin provides signals about global
conflicts, cooperation, political stability, and media attention across different
regions and topics.

GDELT API is public and does not require an API key.
Documentation: http://api.gdeltproject.org/api/v2/doc/doc.html
"""
import datetime as dt
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from urllib.parse import urlencode
import re
import random
from collections import Counter, defaultdict

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
_SOURCE_NAME = "gdelt"

class GdeltPlugin(IrisPluginManager):
    plugin_name = "gdelt_plugin"
    enabled = True     # No API key required
    concurrency = 2    # Limit concurrent requests to be nice to the API
    
    # GDELT API configuration
    EVENT_API_BASE_URL = "https://api.gdeltproject.org/api/v2/events/events"
    GKG_API_BASE_URL = "https://api.gdeltproject.org/api/v2/gkg/gkg"
    REQUEST_TIMEOUT = 30.0  # GDELT can be slow to respond
    RETRY_WAIT = 2.0  # seconds between retries
    MAX_RETRIES = 3
    
    # Regions to track (CAMEO country codes)
    REGIONS = {
        "usa": "USA",
        "chn": "CHN", 
        "rus": "RUS",
        "eur": ["DEU", "FRA", "GBR", "ITA", "ESP"],  # Major European countries
        "mena": ["IRN", "IRQ", "SAU", "SYR", "ISR", "EGY"],  # Middle East & North Africa
        "asia": ["JPN", "KOR", "IND", "IDN", "PAK"]  # Major Asian economies
    }
    
    # Event types to track based on CAMEO codes
    # Reference: http://data.gdeltproject.org/documentation/CAMEO.Manual.1.1b3.pdf
    EVENT_TYPES = {
        "conflict": list(range(100, 200)),  # Conflict events (10x)
        "cooperation": list(range(0, 100)),  # Verbal/material cooperation (0x)
        "protest": list(range(140, 150)),  # Protest events (14x)
        "coercion": list(range(170, 180)),  # Coercive actions (17x)
        "violence": list(range(180, 200)),  # Violence (18x, 19x)
        "diplomatic": list(range(40, 50))  # Diplomatic events (4x)
    }
    
    # Themes to track from GKG
    THEMES = {
        "economic": ["ECON_", "BUS_", "UNEMPLOY", "INFLATION", "MARKET"],
        "political": ["GOVT_", "ELECT_", "DEMO_", "GOV_"],
        "military": ["MIL_", "WEAPN_", "WAR_", "TERROR_"],
        "health": ["HEALTH_", "DISEASE_", "PANDEMIC", "MEDIC"],
        "tech": ["TECH_", "CYBER", "AI_", "INTERNET"],
        "climate": ["CLIMATE", "ENV_", "DISASTER_", "WARMING"]
    }

    def __init__(self):
        """Initialize the GDELT plugin."""
        # Ensure data directory exists for this source
        ensure_data_directory(_SOURCE_NAME)
        
    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch geopolitical signals from GDELT API.
        
        Returns signals related to:
        1. Event counts by type and region
        2. Tone indicators by region
        3. Media attention by theme and region
        """
        signals = []
        
        # Current timestamp
        now = dt.datetime.now(dt.timezone.utc)
        
        # Step 1: Get events data (rotates through regions to avoid overloading API)
        region_key = self._get_rotation_region()
        region_codes = self.REGIONS[region_key]
        
        # Fetch events for the selected region
        events_data = self._fetch_events_data(region_codes)
        if events_data:
            # Process events into signals
            event_signals = self._process_events_data(events_data, region_key, now)
            signals.extend(event_signals)
        
        # Step 2: Get Global Knowledge Graph data (for themes and tone)
        # Rotate through themes to avoid overloading API
        theme_key = self._get_rotation_theme()
        theme_filters = self.THEMES[theme_key]
        
        # Fetch GKG data for the selected theme
        gkg_data = self._fetch_gkg_data(theme_filters)
        if gkg_data:
            # Process GKG data into signals
            gkg_signals = self._process_gkg_data(gkg_data, theme_key, now)
            signals.extend(gkg_signals)
        
        return signals
    
    def _get_rotation_region(self) -> str:
        """Get region to use based on daily rotation."""
        day_of_month = dt.datetime.now().day
        regions = list(self.REGIONS.keys())
        return regions[day_of_month % len(regions)]
    
    def _get_rotation_theme(self) -> str:
        """Get theme to use based on daily rotation."""
        day_of_month = dt.datetime.now().day
        themes = list(self.THEMES.keys())
        return themes[(day_of_month // len(self.REGIONS)) % len(themes)]
    
    def _safe_get(self, url: str, params: dict = None, dataset_id: str = "unknown") -> Optional[str]:
        """Make a safe API request with retries and error handling."""
        # Create complete URL with parameters
        if params:
            full_url = f"{url}?{urlencode(params)}"
        else:
            full_url = url
        
        # Save request metadata
        save_request_metadata(
            dataset_id,
            params or {},
            source_name=_SOURCE_NAME,
            url=url
        )
        
        # Make request with retries
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    full_url,
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
                logger.warning(f"GDELT request failed ({attempt+1}/{self.MAX_RETRIES}): {exc}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
        
        # If all attempts failed, log the error and return None
        logger.error(f"Failed to fetch data from GDELT after {self.MAX_RETRIES} attempts")
        return None
    
    def _fetch_events_data(self, region_codes: Union[str, List[str]]) -> Optional[List[Dict[str, Any]]]:
        """Fetch events data from GDELT Event Database API.
        
        Args:
            region_codes: CAMEO country code(s) to filter events by
            
        Returns:
            List of event dictionaries or None if request failed
        """
        # Convert region_codes to list if it's a single string
        if isinstance(region_codes, str):
            region_codes = [region_codes]
        
        # Create location filter
        location_filter = " OR ".join([f"ActionGeo_CountryCode:{code}" for code in region_codes])
        
        # Build query parameters
        params = {
            "query": f"({location_filter})",
            "format": "json",
            "maxrows": 250,  # Limit to 250 events
            "timespan": "24h"  # Last 24 hours
        }
        
        # Create dataset ID for persistence
        region_str = "_".join(region_codes) if len(region_codes) <= 3 else f"{len(region_codes)}_regions"
        dataset_id = f"events_{region_str}"
        
        # Make request
        response_text = self._safe_get(self.EVENT_API_BASE_URL, params, dataset_id)
        if not response_text:
            return None
        
        try:
            # Parse response - GDELT returns JSON array directly
            import json
            events = json.loads(response_text)
            
            # Validate response structure
            if not isinstance(events, list):
                logger.error(f"Unexpected GDELT events response format: {type(events)}")
                return None
                
            return events
        except Exception as e:
            logger.error(f"Error parsing GDELT events response: {e}")
            return None
    
    def _fetch_gkg_data(self, theme_filters: List[str]) -> Optional[List[Dict[str, Any]]]:
        """Fetch data from GDELT Global Knowledge Graph API.
        
        Args:
            theme_filters: List of theme prefixes to filter by
            
        Returns:
            List of GKG dictionaries or None if request failed
        """
        # Create theme filter
        theme_filter = " OR ".join([f"theme:{theme}" for theme in theme_filters])
        
        # Build query parameters
        params = {
            "query": f"({theme_filter})",
            "format": "json",
            "maxrows": 250,  # Limit to 250 records
            "timespan": "24h"  # Last 24 hours
        }
        
        # Create dataset ID for persistence
        theme_str = "_".join(theme_filters) if len(theme_filters) <= 3 else f"{len(theme_filters)}_themes"
        dataset_id = f"gkg_{theme_str}"
        
        # Make request
        response_text = self._safe_get(self.GKG_API_BASE_URL, params, dataset_id)
        if not response_text:
            return None
        
        try:
            # Parse response - GDELT returns JSON array directly
            import json
            gkg_records = json.loads(response_text)
            
            # Validate response structure
            if not isinstance(gkg_records, list):
                logger.error(f"Unexpected GDELT GKG response format: {type(gkg_records)}")
                return None
                
            return gkg_records
        except Exception as e:
            logger.error(f"Error parsing GDELT GKG response: {e}")
            return None
    
    def _process_events_data(self, events: List[Dict[str, Any]], region_key: str, 
                           timestamp: dt.datetime) -> List[Dict[str, Any]]:
        """Process events data into signals.
        
        Args:
            events: List of event dictionaries from GDELT
            region_key: Key of the region being processed
            timestamp: Timestamp for the signals
            
        Returns:
            List of signals derived from events data
        """
        signals = []
        
        # Count events by type
        event_counts = defaultdict(int)
        event_codes = []
        avg_goldstein = 0
        num_goldstein = 0
        
        # Track unique actors involved
        actors = set()
        
        for event in events:
            try:
                # Extract event code and convert to int
                event_code = int(event.get("EventCode", "0"))
                event_codes.append(event_code)
                
                # Count by event type
                for event_type, code_range in self.EVENT_TYPES.items():
                    if event_code in code_range:
                        event_counts[event_type] += 1
                
                # Track Goldstein scale (conflict intensity from -10 to +10)
                if "GoldsteinScale" in event:
                    try:
                        goldstein = float(event["GoldsteinScale"])
                        avg_goldstein += goldstein
                        num_goldstein += 1
                    except (ValueError, TypeError):
                        pass
                
                # Track actors
                if "Actor1Code" in event and event["Actor1Code"]:
                    actors.add(event["Actor1Code"])
                if "Actor2Code" in event and event["Actor2Code"]:
                    actors.add(event["Actor2Code"])
                    
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"Error processing event: {e}")
        
        # Create signals for event counts by type
        iso_timestamp = timestamp.isoformat()
        
        # Signal 1: Event count by type
        for event_type, count in event_counts.items():
            signal = {
                "name": f"gdelt_{region_key}_{event_type}_events",
                "value": count,
                "source": "gdelt",
                "timestamp": iso_timestamp,
                "metadata": {
                    "region": region_key,
                    "event_type": event_type,
                    "sample_size": len(events)
                }
            }
            
            # Save the processed signal
            save_processed_data(
                f"events_{region_key}_{event_type}",
                signal,
                source_name=_SOURCE_NAME,
                timestamp=iso_timestamp
            )
            
            signals.append(signal)
        
        # Signal 2: Average Goldstein scale (conflict intensity)
        if num_goldstein > 0:
            avg_goldstein_value = avg_goldstein / num_goldstein
            goldstein_signal = {
                "name": f"gdelt_{region_key}_conflict_intensity",
                "value": avg_goldstein_value,
                "source": "gdelt",
                "timestamp": iso_timestamp,
                "metadata": {
                    "region": region_key,
                    "scale": "goldstein",
                    "range": "[-10,+10]",
                    "interpretation": "negative=conflict, positive=cooperation",
                    "sample_size": num_goldstein
                }
            }
            
            save_processed_data(
                f"events_{region_key}_goldstein",
                goldstein_signal,
                source_name=_SOURCE_NAME,
                timestamp=iso_timestamp
            )
            
            signals.append(goldstein_signal)
        
        # Signal 3: Actor diversity (unique actors involved)
        if actors:
            actor_signal = {
                "name": f"gdelt_{region_key}_actor_diversity",
                "value": len(actors),
                "source": "gdelt",
                "timestamp": iso_timestamp,
                "metadata": {
                    "region": region_key,
                    "interpretation": "higher=more diverse actors",
                    "sample_size": len(events)
                }
            }
            
            save_processed_data(
                f"events_{region_key}_actors",
                actor_signal,
                source_name=_SOURCE_NAME,
                timestamp=iso_timestamp
            )
            
            signals.append(actor_signal)
        
        return signals
    
    def _process_gkg_data(self, gkg_records: List[Dict[str, Any]], theme_key: str,
                        timestamp: dt.datetime) -> List[Dict[str, Any]]:
        """Process Global Knowledge Graph data into signals.
        
        Args:
            gkg_records: List of GKG dictionaries from GDELT
            theme_key: Key of the theme being processed
            timestamp: Timestamp for the signals
            
        Returns:
            List of signals derived from GKG data
        """
        signals = []
        
        # Track tones and counts
        tone_sum = 0
        tone_count = 0
        
        # Track countries mentioned
        countries = Counter()
        
        # Track themes mentioned
        themes_count = Counter()
        
        for record in gkg_records:
            try:
                # Extract document tone if available
                if "V2Tone" in record:
                    # Format is typically: tone,positive,negative,polarity,...
                    tone_parts = record["V2Tone"].split(",")
                    if len(tone_parts) > 0:
                        try:
                            tone = float(tone_parts[0])  # Overall document tone
                            tone_sum += tone
                            tone_count += 1
                        except (ValueError, TypeError):
                            pass
                
                # Extract countries mentioned
                if "V2Locations" in record and record["V2Locations"]:
                    # Extract country codes from locations
                    for location in record["V2Locations"].split(";"):
                        parts = location.split("#")
                        if len(parts) >= 3 and parts[2]:  # Country code at index 2
                            countries[parts[2]] += 1
                
                # Extract themes mentioned
                if "V2Themes" in record and record["V2Themes"]:
                    for theme in record["V2Themes"].split(";"):
                        themes_count[theme] += 1
                        
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"Error processing GKG record: {e}")
        
        # Create signals from the processed data
        iso_timestamp = timestamp.isoformat()
        
        # Signal 1: Average tone for the theme
        if tone_count > 0:
            avg_tone = tone_sum / tone_count
            tone_signal = {
                "name": f"gdelt_{theme_key}_tone",
                "value": avg_tone,
                "source": "gdelt_gkg",
                "timestamp": iso_timestamp,
                "metadata": {
                    "theme": theme_key,
                    "range": "[0,100]",
                    "interpretation": "higher=more positive tone",
                    "sample_size": tone_count
                }
            }
            
            save_processed_data(
                f"gkg_{theme_key}_tone",
                tone_signal,
                source_name=_SOURCE_NAME,
                timestamp=iso_timestamp
            )
            
            signals.append(tone_signal)
        
        # Signal 2: Media attention by region
        # Group countries by region
        region_attention = defaultdict(int)
        for country, count in countries.items():
            # Find which region this country belongs to
            for region_key, region_countries in self.REGIONS.items():
                if isinstance(region_countries, list):
                    if country in region_countries:
                        region_attention[region_key] += count
                else:
                    if country == region_countries:
                        region_attention[region_key] += count
        
        # Create attention signals for each region
        for region, attention in region_attention.items():
            attention_signal = {
                "name": f"gdelt_{theme_key}_attention_{region}",
                "value": attention,
                "source": "gdelt_gkg",
                "timestamp": iso_timestamp,
                "metadata": {
                    "theme": theme_key,
                    "region": region,
                    "interpretation": "higher=more media attention",
                    "sample_size": len(gkg_records)
                }
            }
            
            save_processed_data(
                f"gkg_{theme_key}_attention_{region}",
                attention_signal,
                source_name=_SOURCE_NAME,
                timestamp=iso_timestamp
            )
            
            signals.append(attention_signal)
        
        # Signal 3: Theme intensity (how prominently the theme appears)
        # Find themes matching our selected theme key
        theme_intensity = 0
        for theme, count in themes_count.items():
            for filter_theme in self.THEMES[theme_key]:
                if filter_theme in theme:
                    theme_intensity += count
        
        if theme_intensity > 0:
            intensity_signal = {
                "name": f"gdelt_{theme_key}_intensity",
                "value": theme_intensity,
                "source": "gdelt_gkg",
                "timestamp": iso_timestamp,
                "metadata": {
                    "theme": theme_key,
                    "interpretation": "higher=stronger theme presence",
                    "sample_size": len(gkg_records)
                }
            }
            
            save_processed_data(
                f"gkg_{theme_key}_intensity",
                intensity_signal,
                source_name=_SOURCE_NAME,
                timestamp=iso_timestamp
            )
            
            signals.append(intensity_signal)
        
        return signals
