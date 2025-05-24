"""
Regime Detector module for identifying significant regime shifts from event streams and market data.
Uses statistical methods and pattern recognition to detect changes in market regimes,
economic cycles, or other significant shifts that should trigger retrodiction model re-evaluation.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
import threading
import json
import os
from enum import Enum

from recursive_training.regime_sensor.event_stream_manager import Event, EventType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RegimeType(Enum):
    """Types of market/economic regimes that can be detected."""

    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    VOLATILITY_SHOCK = "volatility_shock"
    RECESSION = "recession"
    EXPANSION = "expansion"
    INFLATION = "inflation"
    DEFLATION = "deflation"
    MONETARY_TIGHTENING = "monetary_tightening"
    MONETARY_EASING = "monetary_easing"
    GEOPOLITICAL_CRISIS = "geopolitical_crisis"
    CUSTOM = "custom"


class RegimeChangeEvent:
    """
    Represents a detected regime change event.
    Contains information about the old and new regimes, confidence, and supporting evidence.
    """

    def __init__(
        self,
        regime_change_id: str,
        timestamp: datetime,
        old_regime: Optional[RegimeType],
        new_regime: RegimeType,
        confidence: float,
        duration: Optional[timedelta] = None,
        supporting_evidence: Optional[List[Event]] = None,
        market_indicators: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a regime change event.

        Args:
            regime_change_id: Unique identifier for this regime change
            timestamp: When the regime change was detected
            old_regime: Previous regime (can be None if this is an initial regime)
            new_regime: New regime that has been detected
            confidence: Confidence score (0.0-1.0) for this regime change detection
            duration: Expected or historical duration of this type of regime
            supporting_evidence: List of events that support this regime change
            market_indicators: Market data indicators that support this detection
            metadata: Additional metadata about the regime change
        """
        self.regime_change_id = regime_change_id
        self.timestamp = timestamp
        self.old_regime = old_regime
        self.new_regime = new_regime
        self.confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        self.duration = duration
        self.supporting_evidence = supporting_evidence or []
        self.market_indicators = market_indicators or {}
        self.metadata = metadata or {}
        self.processed = False
        self.retrodiction_triggered = False

    def __str__(self):
        old_regime_str = self.old_regime.value if self.old_regime else "None"
        return (
            f"RegimeChange({self.regime_change_id}, {old_regime_str} -> {self.new_regime.value}, "
            f"confidence={self.confidence:.2f}, {len(self.supporting_evidence)} evidence items)"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert regime change to dictionary for serialization."""
        return {
            "regime_change_id": self.regime_change_id,
            "timestamp": self.timestamp.isoformat(),
            "old_regime": self.old_regime.value if self.old_regime else None,
            "new_regime": self.new_regime.value,
            "confidence": self.confidence,
            "duration": str(self.duration) if self.duration else None,
            "supporting_evidence": [
                event.event_id for event in self.supporting_evidence
            ],
            "market_indicators": self.market_indicators,
            "metadata": self.metadata,
            "processed": self.processed,
            "retrodiction_triggered": self.retrodiction_triggered,
        }


class RegimeDetector:
    """
    Detects regime changes by analyzing event streams and market data.
    Implements various detection algorithms and can trigger retrodiction snapshots.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the regime detector.

        Args:
            config: Configuration parameters for detector behavior
        """
        self.config = config or {}
        self.current_regime = self.config.get("initial_regime", RegimeType.EXPANSION)
        self.detection_methods = {}
        self.change_history = []
        self.handlers = []
        self.market_data = {}
        self.event_buffer = []
        self.max_buffer_size = self.config.get("max_buffer_size", 1000)
        self.min_confidence = self.config.get("min_confidence", 0.7)
        self.lock = threading.Lock()

        # Initialize default detection methods
        self._initialize_detection_methods()

        # Storage config for regime changes
        self.storage_enabled = self.config.get("storage_enabled", True)
        self.storage_path = self.config.get("storage_path", "data/regime_changes")

        # Initialize storage directory if enabled
        if self.storage_enabled:
            os.makedirs(self.storage_path, exist_ok=True)

        logger.info(
            f"RegimeDetector initialized with regime: {self.current_regime.value}"
        )

    def _initialize_detection_methods(self):
        """Register default detection methods."""
        # Register basic detection methods
        self.register_detection_method(
            "volatility_spike", self._detect_volatility_spike
        )
        self.register_detection_method("trend_reversal", self._detect_trend_reversal)
        self.register_detection_method(
            "news_sentiment", self._detect_news_sentiment_shift
        )
        self.register_detection_method(
            "economic_indicators", self._detect_economic_indicator_shift
        )

    def register_detection_method(self, method_name: str, detection_func: Callable):
        """
        Register a new detection method.

        Args:
            method_name: Name of the detection method
            detection_func: Function implementing the detection algorithm
        """
        with self.lock:
            self.detection_methods[method_name] = detection_func
            logger.debug(f"Registered detection method: {method_name}")

    def register_change_handler(self, handler: Callable[[RegimeChangeEvent], None]):
        """
        Register a handler to be called when a regime change is detected.

        Args:
            handler: Function to call with the regime change event
        """
        with self.lock:
            self.handlers.append(handler)

    def process_event(self, event: Event):
        """
        Process a single event and check for regime changes.

        Args:
            event: Event to process
        """
        with self.lock:
            # Add to buffer and trim if needed
            self.event_buffer.append(event)
            if len(self.event_buffer) > self.max_buffer_size:
                self.event_buffer = self.event_buffer[-self.max_buffer_size :]

            # Run detection methods
            self._check_for_regime_change()

    def process_events_batch(self, events: List[Event]):
        """
        Process a batch of events and check for regime changes.

        Args:
            events: List of events to process
        """
        with self.lock:
            # Add all events to buffer
            self.event_buffer.extend(events)
            if len(self.event_buffer) > self.max_buffer_size:
                self.event_buffer = self.event_buffer[-self.max_buffer_size :]

            # Run detection methods
            self._check_for_regime_change()

    def update_market_data(self, market_data: Dict[str, Any]):
        """
        Update the current market data used for regime detection.

        Args:
            market_data: Dictionary of market data (prices, indicators, etc.)
        """
        with self.lock:
            self.market_data.update(market_data)

            # Run detection methods after market data update
            self._check_for_regime_change()

    def _check_for_regime_change(self):
        """
        Run all detection methods and check for regime changes.
        If a change is detected with sufficient confidence, notify handlers.
        """
        detected_regimes = []
        confidences = []
        supporting_evidence = {}
        market_indicators = {}

        # Run each detection method
        for method_name, detection_func in self.detection_methods.items():
            try:
                result = detection_func()
                if result:
                    regime, confidence, evidence, indicators = result
                    detected_regimes.append(regime)
                    confidences.append(confidence)
                    supporting_evidence[regime] = evidence
                    market_indicators[regime] = indicators
                    logger.debug(
                        f"Method {method_name} detected {regime.value} with confidence {confidence:.2f}"
                    )
            except Exception as e:
                logger.error(f"Error in detection method {method_name}: {e}")

        # If no regimes detected, return
        if not detected_regimes:
            return

        # If multiple regimes detected, choose the one with highest confidence
        if len(detected_regimes) > 1:
            # Create list of (regime, confidence) tuples and sort by confidence
            regime_confidences = list(zip(detected_regimes, confidences))
            regime_confidences.sort(key=lambda x: x[1], reverse=True)

            # Choose the highest confidence regime
            new_regime, highest_confidence = regime_confidences[0]
        else:
            new_regime = detected_regimes[0]
            highest_confidence = confidences[0]

        # Check if confidence meets threshold and regime is different from current
        if (
            highest_confidence >= self.min_confidence
            and new_regime != self.current_regime
        ):
            # We have a regime change
            self._handle_regime_change(
                new_regime,
                highest_confidence,
                supporting_evidence.get(new_regime, []),
                market_indicators.get(new_regime, {}),
            )

    def _handle_regime_change(
        self,
        new_regime: RegimeType,
        confidence: float,
        evidence: List[Event],
        indicators: Dict[str, Any],
    ):
        """
        Handle a detected regime change.

        Args:
            new_regime: The newly detected regime
            confidence: Confidence in the detection
            evidence: Supporting evidence events
            indicators: Market indicators supporting the detection
        """
        # Create a regime change event
        change_id = f"regime_change_{len(self.change_history) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        regime_change = RegimeChangeEvent(
            regime_change_id=change_id,
            timestamp=datetime.now(),
            old_regime=self.current_regime,
            new_regime=new_regime,
            confidence=confidence,
            supporting_evidence=evidence,
            market_indicators=indicators,
            metadata={"detection_timestamp": datetime.now().isoformat()},
        )

        # Update current regime
        logger.info(
            f"Regime change detected: {self.current_regime.value} -> {new_regime.value} with confidence {confidence:.2f}"
        )
        self.current_regime = new_regime

        # Add to history
        self.change_history.append(regime_change)

        # Store if enabled
        if self.storage_enabled:
            self._store_regime_change(regime_change)

        # Notify handlers
        for handler in self.handlers:
            try:
                handler(regime_change)
            except Exception as e:
                logger.error(f"Error in regime change handler: {e}")

    def _store_regime_change(self, regime_change: RegimeChangeEvent):
        """
        Store a regime change event to disk.

        Args:
            regime_change: Regime change event to store
        """
        try:
            # Create date-based filename
            date_str = regime_change.timestamp.strftime("%Y-%m-%d")
            filename = f"{date_str}_{regime_change.regime_change_id}.json"
            file_path = os.path.join(self.storage_path, filename)

            # Store as JSON
            with open(file_path, "w") as f:
                json.dump(regime_change.to_dict(), f, indent=2)

            logger.debug(f"Stored regime change to {file_path}")
        except Exception as e:
            logger.error(f"Error storing regime change: {e}")

    def get_current_regime(self) -> RegimeType:
        """Get the current detected regime."""
        return self.current_regime

    def get_regime_history(self) -> List[RegimeChangeEvent]:
        """Get the history of regime changes."""
        return self.change_history.copy()

    # The following are placeholder detection methods.
    # In a production system, these would implement sophisticated algorithms.

    def _detect_volatility_spike(
        self,
    ) -> Optional[Tuple[RegimeType, float, List[Event], Dict[str, Any]]]:
        """
        Detect volatility spikes that could indicate a regime change.

        Returns:
            Tuple of (regime_type, confidence, supporting_events, market_indicators) or None
        """
        # This is a placeholder implementation. A real implementation would use
        # statistical measures of volatility and appropriate thresholds.

        # Check if we have volatility data
        if "volatility" not in self.market_data:
            return None

        volatility = self.market_data["volatility"]
        vix = self.market_data.get("vix", None)

        # Simple threshold-based detection
        if volatility > 30:  # Simple threshold
            confidence = min(
                1.0, volatility / 50.0
            )  # Higher volatility = higher confidence

            # Collect supporting events
            supporting_events = [
                event
                for event in self.event_buffer[-20:]  # Look at recent events
                if event.event_type
                in [
                    EventType.MARKET_MOVEMENT,
                    EventType.NEWS,
                    EventType.ECONOMIC_INDICATOR,
                ]
            ]

            # Market indicators
            indicators = {
                "volatility": volatility,
                "vix": vix,
                "detection_method": "volatility_spike",
            }

            return (
                RegimeType.VOLATILITY_SHOCK,
                confidence,
                supporting_events,
                indicators,
            )

        return None

    def _detect_trend_reversal(
        self,
    ) -> Optional[Tuple[RegimeType, float, List[Event], Dict[str, Any]]]:
        """
        Detect trend reversals in price data.

        Returns:
            Tuple of (regime_type, confidence, supporting_events, market_indicators) or None
        """
        # Check if we have price data and moving averages
        if not all(k in self.market_data for k in ["price", "sma_50", "sma_200"]):
            return None

        price = self.market_data["price"]
        sma_50 = self.market_data["sma_50"]
        sma_200 = self.market_data["sma_200"]

        # Simple moving average crossover detection
        if sma_50 > sma_200 and self.current_regime != RegimeType.BULL_MARKET:
            # Potential bull market (golden cross)
            # Confidence based on how far above the 200-day SMA the 50-day SMA is
            confidence = min(1.0, (sma_50 - sma_200) / (sma_200 * 0.05))

            supporting_events = [
                event
                for event in self.event_buffer[-30:]
                if event.event_type
                in [EventType.MARKET_MOVEMENT, EventType.CORPORATE_ANNOUNCEMENT]
            ]

            indicators = {
                "price": price,
                "sma_50": sma_50,
                "sma_200": sma_200,
                "crossover_type": "golden_cross",
                "detection_method": "trend_reversal",
            }

            return RegimeType.BULL_MARKET, confidence, supporting_events, indicators

        elif sma_50 < sma_200 and self.current_regime != RegimeType.BEAR_MARKET:
            # Potential bear market (death cross)
            # Confidence based on how far below the 200-day SMA the 50-day SMA is
            confidence = min(1.0, (sma_200 - sma_50) / (sma_200 * 0.05))

            supporting_events = [
                event
                for event in self.event_buffer[-30:]
                if event.event_type
                in [EventType.MARKET_MOVEMENT, EventType.CORPORATE_ANNOUNCEMENT]
            ]

            indicators = {
                "price": price,
                "sma_50": sma_50,
                "sma_200": sma_200,
                "crossover_type": "death_cross",
                "detection_method": "trend_reversal",
            }

            return RegimeType.BEAR_MARKET, confidence, supporting_events, indicators

        return None

    def _detect_news_sentiment_shift(
        self,
    ) -> Optional[Tuple[RegimeType, float, List[Event], Dict[str, Any]]]:
        """
        Detect shifts in news sentiment that could indicate a regime change.

        Returns:
            Tuple of (regime_type, confidence, supporting_events, market_indicators) or None
        """
        # Check if we have enough news events
        news_events = [
            event
            for event in self.event_buffer[-50:]  # Look at recent events
            if event.event_type == EventType.NEWS
        ]

        if len(news_events) < 10:
            return None

        # In a real implementation, we would perform sentiment analysis on the news content
        # For this placeholder, we'll use a simple keyword-based approach

        # Crisis keywords
        crisis_keywords = [
            "crisis",
            "crash",
            "collapse",
            "plummet",
            "disaster",
            "fear",
            "panic",
        ]
        recession_keywords = [
            "recession",
            "contraction",
            "downturn",
            "slowdown",
            "layoffs",
            "unemployment",
        ]
        expansion_keywords = [
            "growth",
            "expansion",
            "bull",
            "recovery",
            "positive",
            "upswing",
            "boom",
        ]
        inflation_keywords = [
            "inflation",
            "price increases",
            "rising prices",
            "cpi",
            "cost of living",
        ]
        monetary_keywords = [
            "fed",
            "central bank",
            "interest rate",
            "rate hike",
            "rate cut",
            "monetary policy",
        ]

        # Count keyword occurrences
        crisis_count = sum(
            1
            for event in news_events
            if any(keyword in event.content.lower() for keyword in crisis_keywords)
        )
        recession_count = sum(
            1
            for event in news_events
            if any(keyword in event.content.lower() for keyword in recession_keywords)
        )
        expansion_count = sum(
            1
            for event in news_events
            if any(keyword in event.content.lower() for keyword in expansion_keywords)
        )
        inflation_count = sum(
            1
            for event in news_events
            if any(keyword in event.content.lower() for keyword in inflation_keywords)
        )
        monetary_count = sum(
            1
            for event in news_events
            if any(keyword in event.content.lower() for keyword in monetary_keywords)
        )

        # Determine dominant theme
        counts = {
            RegimeType.GEOPOLITICAL_CRISIS: crisis_count,
            RegimeType.RECESSION: recession_count,
            RegimeType.EXPANSION: expansion_count,
            RegimeType.INFLATION: inflation_count,
        }

        # Add monetary policy regimes based on keywords
        if monetary_count > 5:
            tightening_count = sum(
                1
                for event in news_events
                if "hike" in event.content.lower() or "raise" in event.content.lower()
            )
            easing_count = sum(
                1
                for event in news_events
                if "cut" in event.content.lower() or "lower" in event.content.lower()
            )

            if tightening_count > easing_count:
                counts[RegimeType.MONETARY_TIGHTENING] = monetary_count
            else:
                counts[RegimeType.MONETARY_EASING] = monetary_count

        # Find the regime with the highest count
        if counts:
            max_regime = max(counts.items(), key=lambda x: x[1])
            regime_type, count = max_regime

            # Calculate confidence based on the proportion of events with this theme
            confidence = min(
                1.0, count / len(news_events) * 2
            )  # Scale up to make it more sensitive

            # Only consider a regime change if count and confidence are high enough
            if count >= 5 and confidence >= 0.3 and regime_type != self.current_regime:
                # Find supporting events
                supporting_events = []

                # Different approach based on regime type
                if regime_type == RegimeType.GEOPOLITICAL_CRISIS:
                    supporting_events = [
                        event
                        for event in news_events
                        if any(
                            keyword in event.content.lower()
                            for keyword in crisis_keywords
                        )
                    ]
                elif regime_type == RegimeType.RECESSION:
                    supporting_events = [
                        event
                        for event in news_events
                        if any(
                            keyword in event.content.lower()
                            for keyword in recession_keywords
                        )
                    ]
                elif regime_type == RegimeType.EXPANSION:
                    supporting_events = [
                        event
                        for event in news_events
                        if any(
                            keyword in event.content.lower()
                            for keyword in expansion_keywords
                        )
                    ]
                elif regime_type == RegimeType.INFLATION:
                    supporting_events = [
                        event
                        for event in news_events
                        if any(
                            keyword in event.content.lower()
                            for keyword in inflation_keywords
                        )
                    ]
                elif regime_type in [
                    RegimeType.MONETARY_TIGHTENING,
                    RegimeType.MONETARY_EASING,
                ]:
                    supporting_events = [
                        event
                        for event in news_events
                        if any(
                            keyword in event.content.lower()
                            for keyword in monetary_keywords
                        )
                    ]

                # Include market data if available
                indicators = {
                    "news_sentiment_score": confidence,
                    "relevant_keyword_count": count,
                    "total_news_count": len(news_events),
                    "detection_method": "news_sentiment",
                }

                return regime_type, confidence, supporting_events, indicators

        return None

    def _detect_economic_indicator_shift(
        self,
    ) -> Optional[Tuple[RegimeType, float, List[Event], Dict[str, Any]]]:
        """
        Detect shifts in economic indicators that could indicate a regime change.

        Returns:
            Tuple of (regime_type, confidence, supporting_events, market_indicators) or None
        """
        # Check if we have economic indicator data
        required_indicators = [
            "gdp_growth",
            "unemployment",
            "inflation",
            "interest_rates",
        ]
        if not all(indicator in self.market_data for indicator in required_indicators):
            return None

        gdp_growth = self.market_data["gdp_growth"]
        unemployment = self.market_data["unemployment"]
        inflation = self.market_data["inflation"]
        interest_rates = self.market_data["interest_rates"]

        # Simple rules for economic regimes

        # Check for recession
        if gdp_growth < 0 and unemployment > 5.5:
            confidence = min(1.0, (abs(gdp_growth) * 0.2 + (unemployment - 5.5) * 0.1))

            supporting_events = [
                event
                for event in self.event_buffer[-40:]
                if event.event_type == EventType.ECONOMIC_INDICATOR
            ]

            indicators = {
                "gdp_growth": gdp_growth,
                "unemployment": unemployment,
                "inflation": inflation,
                "interest_rates": interest_rates,
                "detection_method": "economic_indicators",
            }

            return RegimeType.RECESSION, confidence, supporting_events, indicators

        # Check for inflation regime
        elif inflation > 4.0:
            confidence = min(1.0, (inflation - 4.0) * 0.25)

            supporting_events = [
                event
                for event in self.event_buffer[-40:]
                if event.event_type == EventType.ECONOMIC_INDICATOR
            ]

            indicators = {
                "gdp_growth": gdp_growth,
                "unemployment": unemployment,
                "inflation": inflation,
                "interest_rates": interest_rates,
                "detection_method": "economic_indicators",
            }

            return RegimeType.INFLATION, confidence, supporting_events, indicators

        # Check for expansion
        elif gdp_growth > 2.5 and unemployment < 5.0:
            confidence = min(1.0, (gdp_growth - 2.5) * 0.2 + (5.0 - unemployment) * 0.1)

            supporting_events = [
                event
                for event in self.event_buffer[-40:]
                if event.event_type == EventType.ECONOMIC_INDICATOR
            ]

            indicators = {
                "gdp_growth": gdp_growth,
                "unemployment": unemployment,
                "inflation": inflation,
                "interest_rates": interest_rates,
                "detection_method": "economic_indicators",
            }

            return RegimeType.EXPANSION, confidence, supporting_events, indicators

        return None


# Example usage
if __name__ == "__main__":
    # Create a regime detector
    detector = RegimeDetector()

    # Define a simple handler for regime changes
    def print_regime_handler(change: RegimeChangeEvent):
        print(f"REGIME CHANGE: {change}")

    # Register the handler
    detector.register_change_handler(print_regime_handler)

    # Simulate some market data
    market_data = {
        "price": 100,
        "volatility": 35,  # High volatility
        "sma_50": 95,
        "sma_200": 105,
        "vix": 30,
        "gdp_growth": 1.5,
        "unemployment": 4.5,
        "inflation": 2.0,
        "interest_rates": 3.0,
    }

    # Update market data
    detector.update_market_data(market_data)

    # Print current regime
    print(f"Current regime: {detector.get_current_regime().value}")
