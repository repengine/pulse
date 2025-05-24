"""
Event Stream Manager for real-time data ingestion and processing.
Handles the ingestion of external events such as news headlines, corporate announcements,
and other time-series data that can indicate regime shifts.
"""

import json
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
import re
import time
import threading
import queue

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Priority levels for incoming events."""

    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class EventType(Enum):
    """Types of events that can be processed."""

    NEWS = "news"
    CORPORATE_ANNOUNCEMENT = "corporate_announcement"
    MARKET_MOVEMENT = "market_movement"
    ECONOMIC_INDICATOR = "economic_indicator"
    GEOPOLITICAL = "geopolitical"
    REGULATORY = "regulatory"
    CUSTOM = "custom"


class Event:
    """
    Represents a single event from an external source.
    Contains the event data, metadata, and processing information.
    """

    def __init__(
        self,
        event_id: str,
        source: str,
        event_type: EventType,
        timestamp: Union[str, datetime],
        content: str,
        entities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.MEDIUM,
    ):
        """
        Initialize an event with relevant data.

        Args:
            event_id: Unique identifier for the event
            source: Source of the event (e.g., news provider, data feed)
            event_type: Type of event (news, corporate announcement, etc.)
            timestamp: Timestamp of when the event occurred
            content: Main content of the event (headline, announcement text)
            entities: List of entities (companies, countries, etc.) related to the event
            metadata: Additional event metadata
            priority: Priority level of the event
        """
        self.event_id = event_id
        self.source = source
        self.event_type = (
            event_type if isinstance(event_type, EventType) else EventType(event_type)
        )

        # Convert timestamp to datetime if it's a string
        if isinstance(timestamp, str):
            try:
                self.timestamp = datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                )
            except ValueError:
                logger.warning(
                    f"Invalid timestamp format: {timestamp}, using current time"
                )
                self.timestamp = datetime.now()
        else:
            self.timestamp = timestamp

        self.content = content
        self.entities = entities or []
        self.metadata = metadata or {}
        self.priority = (
            priority if isinstance(priority, EventPriority) else EventPriority(priority)
        )
        self.processed = False
        self.processing_history = []

    def __str__(self):
        return f"Event({self.event_id}, {self.event_type.value}, {self.timestamp}, priority={self.priority.name})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "source": self.source,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "entities": self.entities,
            "metadata": self.metadata,
            "priority": self.priority.value,
            "processed": self.processed,
            "processing_history": self.processing_history,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create an event from a dictionary."""
        # Convert priority value to enum
        priority_value = data.get("priority", EventPriority.MEDIUM.value)
        priority = EventPriority(priority_value)

        # Convert event_type string to enum
        event_type_value = data.get("event_type", EventType.CUSTOM.value)
        event_type = EventType(event_type_value)

        event = cls(
            event_id=data.get("event_id", ""),
            source=data.get("source", ""),
            event_type=event_type,
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            content=data.get("content", ""),
            entities=data.get("entities", []),
            metadata=data.get("metadata", {}),
            priority=priority,
        )

        event.processed = data.get("processed", False)
        event.processing_history = data.get("processing_history", [])

        return event


class EventStreamManager:
    """
    Manages multiple event streams, handles event ingestion, filtering, and distribution.
    Supports both real-time and batch processing of events.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the event stream manager.

        Args:
            config: Configuration parameters for the manager
        """
        self.config = config or {}
        self.event_queue = queue.PriorityQueue()  # Priority queue for events
        self.event_handlers = {}  # Map event types to handlers
        self.filters = {}  # Filters to apply to incoming events
        self.sources = {}  # Configured event sources
        self.event_history = {}  # History of processed events
        self.running = False
        self.processing_thread = None
        self.max_queue_size = self.config.get("max_queue_size", 10000)
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

        # Event storage config
        self.storage_enabled = self.config.get("storage_enabled", True)
        self.storage_path = self.config.get("storage_path", "data/event_streams")

        # Initialize storage directory if enabled
        if self.storage_enabled:
            os.makedirs(self.storage_path, exist_ok=True)

        logger.info("EventStreamManager initialized")

    def register_event_handler(
        self, event_type: EventType, handler: Callable[[Event], None]
    ):
        """
        Register a handler function for a specific event type.

        Args:
            event_type: Type of event to handle
            handler: Function to call when events of this type are received
        """
        with self.lock:
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(handler)
            logger.debug(f"Registered handler for {event_type.value}")

    def add_filter(self, filter_name: str, filter_func: Callable[[Event], bool]):
        """
        Add a filter function to apply to incoming events.

        Args:
            filter_name: Name of the filter
            filter_func: Function that takes an event and returns True if the event should be processed
        """
        with self.lock:
            self.filters[filter_name] = filter_func
            logger.debug(f"Added filter: {filter_name}")

    def remove_filter(self, filter_name: str):
        """
        Remove a filter by name.

        Args:
            filter_name: Name of the filter to remove
        """
        with self.lock:
            if filter_name in self.filters:
                del self.filters[filter_name]
                logger.debug(f"Removed filter: {filter_name}")

    def configure_source(self, source_name: str, source_config: Dict[str, Any]):
        """
        Configure a new event source.

        Args:
            source_name: Name of the source
            source_config: Configuration parameters for the source
        """
        with self.lock:
            self.sources[source_name] = source_config
            logger.info(f"Configured event source: {source_name}")

    def ingest_event(self, event: Event):
        """
        Ingest a single event into the processing queue.

        Args:
            event: Event to ingest
        """
        # Apply filters to determine if event should be processed
        should_process = all(
            filter_func(event) for filter_func in self.filters.values()
        )

        if should_process:
            # Add to priority queue with priority as the first element of the tuple
            try:
                if self.event_queue.qsize() < self.max_queue_size:
                    # Use negative priority value to make higher priority events processed first
                    self.event_queue.put((-event.priority.value, time.time(), event))
                    logger.debug(f"Ingested event: {event}")

                    # Store event if storage is enabled
                    if self.storage_enabled:
                        self._store_event(event)
                else:
                    logger.warning(f"Event queue full, dropping event: {event}")
            except Exception as e:
                logger.error(f"Error ingesting event: {e}")

    def ingest_events_batch(self, events: List[Event]):
        """
        Ingest a batch of events.

        Args:
            events: List of events to ingest
        """
        for event in events:
            self.ingest_event(event)

        logger.info(f"Ingested batch of {len(events)} events")

    def _store_event(self, event: Event):
        """
        Store an event to disk.

        Args:
            event: Event to store
        """
        try:
            # Create date-based directory structure
            date_str = event.timestamp.strftime("%Y-%m-%d")
            event_type_str = event.event_type.value
            source_str = event.source.replace("/", "_")

            directory = os.path.join(
                self.storage_path, date_str, event_type_str, source_str
            )
            os.makedirs(directory, exist_ok=True)

            # Store event as JSON file
            file_path = os.path.join(directory, f"{event.event_id}.json")
            with open(file_path, "w") as f:
                json.dump(event.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error storing event: {e}")

    def _process_event(self, event: Event):
        """
        Process a single event by calling appropriate handlers.

        Args:
            event: Event to process
        """
        try:
            # Get handlers for this event type
            handlers = self.event_handlers.get(event.event_type, [])

            # Also process with general handlers (EventType.CUSTOM)
            general_handlers = self.event_handlers.get(EventType.CUSTOM, [])
            all_handlers = handlers + general_handlers

            if all_handlers:
                for handler in all_handlers:
                    handler(event)

                # Record processing in event history
                processing_record = {
                    "timestamp": datetime.now().isoformat(),
                    "handlers": [handler.__name__ for handler in all_handlers],
                }
                event.processing_history.append(processing_record)
                event.processed = True

                # Store in event history
                self.event_history[event.event_id] = event

                logger.debug(f"Processed event: {event}")
            else:
                logger.warning(f"No handlers for event type: {event.event_type}")
        except Exception as e:
            logger.error(f"Error processing event: {e}")

    def _event_processor_loop(self):
        """Background thread for processing events from the queue."""
        logger.info("Event processor thread started")

        while not self.stop_event.is_set():
            try:
                # Get an event from the queue with timeout to allow checking stop_event
                try:
                    _, _, event = self.event_queue.get(timeout=0.1)
                    self._process_event(event)
                    self.event_queue.task_done()
                except queue.Empty:
                    continue  # No events in queue, try again
            except Exception as e:
                logger.error(f"Error in event processor loop: {e}")
                time.sleep(1)  # Avoid tight loop in case of recurring errors

        logger.info("Event processor thread stopped")

    def start(self):
        """Start the event processing thread."""
        with self.lock:
            if not self.running:
                self.stop_event.clear()
                self.processing_thread = threading.Thread(
                    target=self._event_processor_loop
                )
                self.processing_thread.daemon = True
                self.processing_thread.start()
                self.running = True
                logger.info("EventStreamManager started")

    def stop(self):
        """Stop the event processing thread."""
        with self.lock:
            if self.running:
                self.stop_event.set()
                if self.processing_thread:
                    self.processing_thread.join(timeout=5.0)
                self.running = False
                logger.info("EventStreamManager stopped")

    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """
        Retrieve an event by its ID.

        Args:
            event_id: ID of the event to retrieve

        Returns:
            Event if found, None otherwise
        """
        return self.event_history.get(event_id)

    def create_mock_news_event(
        self, headline: str, source: str = "mock_source"
    ) -> Event:
        """
        Create a mock news event for testing.

        Args:
            headline: News headline
            source: Source of the news

        Returns:
            Mock Event object
        """
        import hashlib

        # Generate a deterministic ID based on the headline
        event_id = hashlib.md5(headline.encode()).hexdigest()

        # Create and return the event
        return Event(
            event_id=event_id,
            source=source,
            event_type=EventType.NEWS,
            timestamp=datetime.now(),
            content=headline,
            entities=self._extract_entities_from_headline(headline),
            metadata={"mock": True},
            priority=EventPriority.MEDIUM,
        )

    def _extract_entities_from_headline(self, headline: str) -> List[str]:
        """
        Extract potential entities from a headline using simple rules.
        In a real implementation, this would use NLP techniques.

        Args:
            headline: News headline to extract entities from

        Returns:
            List of extracted entities
        """
        # Simple extraction of uppercase sequences that might be companies or organizations
        potential_entities = re.findall(
            r"\b[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\b", headline
        )

        # Filter out common words that might be capitalized
        common_words = {
            "THE",
            "A",
            "AN",
            "AND",
            "OR",
            "BUT",
            "FOR",
            "WITH",
            "IN",
            "ON",
            "AT",
        }
        filtered_entities = [
            entity
            for entity in potential_entities
            if entity.upper() not in common_words
        ]

        return filtered_entities


# Example usage if run directly
if __name__ == "__main__":
    # Create manager
    manager = EventStreamManager()

    # Define a simple handler
    def print_news_handler(event: Event):
        print(f"NEWS: {event.content}")

    # Register the handler
    manager.register_event_handler(EventType.NEWS, print_news_handler)

    # Start processing
    manager.start()

    # Create some mock events
    events = [
        manager.create_mock_news_event("Company XYZ announces new product line"),
        manager.create_mock_news_event("Market indices fall 2% on economic concerns"),
        manager.create_mock_news_event(
            "Federal Reserve raises interest rates by 0.25%"
        ),
    ]

    # Ingest the events
    manager.ingest_events_batch(events)

    # Allow time for processing
    time.sleep(1)

    # Stop the manager
    manager.stop()
