"""
Integration module for connecting the regime-sensor fusion with retrodiction and counterfactual simulation.
Demonstrates how the event streams, regime detection, retrodiction triggering, and counterfactual
simulation can work together in the Pulse system.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Optional, Any
import json
import time

from recursive_training.regime_sensor.event_stream_manager import (
    EventStreamManager,
    Event,
    EventType,
    EventPriority,
)
from recursive_training.regime_sensor.regime_detector import (
    RegimeDetector,
    RegimeType,
    RegimeChangeEvent,
)
from recursive_training.regime_sensor.retrodiction_trigger import (
    RetrodictionTrigger,
    RetrodictionSnapshot,
    TriggerCause,
)
from causal_model.counterfactual_simulator import CounterfactualSimulator

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RetrodictionSystemIntegrator:
    """
    Integrates the regime-sensor fusion components with retrodiction training
    and counterfactual simulation. Provides a unified interface for these components
    to work together.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the integrator with all required components.

        Args:
            config: Configuration parameters for the integrator and its components
        """
        self.config = config or {}

        # Initialize components
        self.event_manager = EventStreamManager(self.config.get("event_manager_config"))
        self.regime_detector = RegimeDetector(self.config.get("regime_detector_config"))
        self.retrodiction_trigger = RetrodictionTrigger(
            self.config.get("retrodiction_trigger_config")
        )
        self.counterfactual_simulator = CounterfactualSimulator(
            self.config.get("counterfactual_simulator_config")
        )

        # Set up connections between components
        self._connect_components()

        # Storage config
        self.storage_enabled = self.config.get("storage_enabled", True)
        self.storage_path = self.config.get("storage_path", "data/retrodiction_system")

        if self.storage_enabled:
            os.makedirs(self.storage_path, exist_ok=True)

        logger.info("RetrodictionSystemIntegrator initialized")

    def _connect_components(self):
        """Set up connections and handlers between components."""
        # Connect event manager to regime detector
        self.event_manager.register_event_handler(
            EventType.NEWS, self.regime_detector.process_event
        )
        self.event_manager.register_event_handler(
            EventType.MARKET_MOVEMENT, self.regime_detector.process_event
        )
        self.event_manager.register_event_handler(
            EventType.ECONOMIC_INDICATOR, self.regime_detector.process_event
        )

        # Connect regime detector to retrodiction trigger
        self.regime_detector.register_change_handler(
            self.retrodiction_trigger.handle_regime_change
        )

        # Connect retrodiction trigger to counterfactual processing
        self.retrodiction_trigger.register_handler(self._handle_retrodiction_snapshot)

        logger.info("Component connections established")

    def _handle_retrodiction_snapshot(self, snapshot: RetrodictionSnapshot):
        """
        Handler for retrodiction snapshots that creates counterfactual scenarios.

        Args:
            snapshot: Retrodiction snapshot to process
        """
        logger.info(f"Processing retrodiction snapshot: {snapshot}")

        # If this snapshot was triggered by a regime change, create counterfactual scenarios
        if snapshot.cause == TriggerCause.REGIME_CHANGE and snapshot.regime_change:
            regime_change = snapshot.regime_change

            # Create base scenario with evidence from current state
            evidence = {}
            # In a real implementation, we would populate evidence from current data
            # For this example, we'll use placeholder values
            evidence = {
                "interest_rate": 0.0325,  # 3.25%
                "inflation": 0.028,  # 2.8%
                "gdp_growth": 0.02,  # 2.0%
                "unemployment": 0.048,  # 4.8%
            }

            # Create different scenarios based on regime type
            if regime_change.new_regime == RegimeType.MONETARY_TIGHTENING:
                # Create scenarios for different levels of interest rate hikes
                self._create_monetary_tightening_scenarios(evidence, regime_change)

            elif regime_change.new_regime == RegimeType.INFLATION:
                # Create scenarios for different inflation levels
                self._create_inflation_scenarios(evidence, regime_change)

            elif regime_change.new_regime == RegimeType.RECESSION:
                # Create scenarios for different recession severities
                self._create_recession_scenarios(evidence, regime_change)

            elif regime_change.new_regime == RegimeType.VOLATILITY_SHOCK:
                # Create scenarios for different market volatility impacts
                self._create_volatility_scenarios(evidence, regime_change)

            else:
                # Create a generic scenario based on the regime change
                self._create_generic_scenario(evidence, regime_change)

        # Store snapshot processing results
        if self.storage_enabled:
            self._store_snapshot_results(snapshot)

    def _create_monetary_tightening_scenarios(
        self, evidence: Dict[str, float], regime_change: RegimeChangeEvent
    ):
        """
        Create counterfactual scenarios for monetary tightening regimes.

        Args:
            evidence: Current economic evidence
            regime_change: The regime change event
        """
        # Create mild tightening scenario
        mild_scenario = self.counterfactual_simulator.create_scenario(
            name="Mild Monetary Tightening",
            description="Scenario with moderate interest rate increases (0.25%)",
            interventions={
                "interest_rate": evidence["interest_rate"] + 0.0025  # +0.25%
            },
            evidence=evidence,
            target_variables=["inflation", "gdp_growth", "unemployment"],
            metadata={
                "regime_change_id": regime_change.regime_change_id,
                "regime_type": regime_change.new_regime.value,
                "scenario_type": "mild_tightening",
            },
        )

        # Create strong tightening scenario
        strong_scenario = self.counterfactual_simulator.create_scenario(
            name="Strong Monetary Tightening",
            description="Scenario with aggressive interest rate increases (0.75%)",
            interventions={
                "interest_rate": evidence["interest_rate"] + 0.0075  # +0.75%
            },
            evidence=evidence,
            target_variables=["inflation", "gdp_growth", "unemployment"],
            metadata={
                "regime_change_id": regime_change.regime_change_id,
                "regime_type": regime_change.new_regime.value,
                "scenario_type": "strong_tightening",
            },
        )

        # Run scenarios
        self.counterfactual_simulator.run_batch_scenarios(
            [mild_scenario, strong_scenario]
        )

    def _create_inflation_scenarios(
        self, evidence: Dict[str, float], regime_change: RegimeChangeEvent
    ):
        """
        Create counterfactual scenarios for inflation regimes.

        Args:
            evidence: Current economic evidence
            regime_change: The regime change event
        """
        # Create moderate inflation scenario
        moderate_scenario = self.counterfactual_simulator.create_scenario(
            name="Moderate Inflation",
            description="Scenario with inflation rising to 4%",
            interventions={
                "inflation": 0.04  # 4%
            },
            evidence=evidence,
            target_variables=["interest_rate", "gdp_growth", "unemployment"],
            metadata={
                "regime_change_id": regime_change.regime_change_id,
                "regime_type": regime_change.new_regime.value,
                "scenario_type": "moderate_inflation",
            },
        )

        # Create high inflation scenario
        high_scenario = self.counterfactual_simulator.create_scenario(
            name="High Inflation",
            description="Scenario with inflation rising to 7%",
            interventions={
                "inflation": 0.07  # 7%
            },
            evidence=evidence,
            target_variables=["interest_rate", "gdp_growth", "unemployment"],
            metadata={
                "regime_change_id": regime_change.regime_change_id,
                "regime_type": regime_change.new_regime.value,
                "scenario_type": "high_inflation",
            },
        )

        # Run scenarios
        self.counterfactual_simulator.run_batch_scenarios(
            [moderate_scenario, high_scenario]
        )

    def _create_recession_scenarios(
        self, evidence: Dict[str, float], regime_change: RegimeChangeEvent
    ):
        """
        Create counterfactual scenarios for recession regimes.

        Args:
            evidence: Current economic evidence
            regime_change: The regime change event
        """
        # Create mild recession scenario
        mild_scenario = self.counterfactual_simulator.create_scenario(
            name="Mild Recession",
            description="Scenario with GDP growth declining to -0.5%",
            interventions={
                "gdp_growth": -0.005  # -0.5%
            },
            evidence=evidence,
            target_variables=["interest_rate", "inflation", "unemployment"],
            metadata={
                "regime_change_id": regime_change.regime_change_id,
                "regime_type": regime_change.new_regime.value,
                "scenario_type": "mild_recession",
            },
        )

        # Create severe recession scenario
        severe_scenario = self.counterfactual_simulator.create_scenario(
            name="Severe Recession",
            description="Scenario with GDP growth declining to -3%",
            interventions={
                "gdp_growth": -0.03  # -3%
            },
            evidence=evidence,
            target_variables=["interest_rate", "inflation", "unemployment"],
            metadata={
                "regime_change_id": regime_change.regime_change_id,
                "regime_type": regime_change.new_regime.value,
                "scenario_type": "severe_recession",
            },
        )

        # Run scenarios
        self.counterfactual_simulator.run_batch_scenarios(
            [mild_scenario, severe_scenario]
        )

    def _create_volatility_scenarios(
        self, evidence: Dict[str, float], regime_change: RegimeChangeEvent
    ):
        """
        Create counterfactual scenarios for volatility shock regimes.

        Args:
            evidence: Current economic evidence
            regime_change: The regime change event
        """
        # For this example, we'll assume we also have market volatility in our evidence
        # In a real implementation, we would have more market-related variables
        evidence_with_volatility = evidence.copy()
        evidence_with_volatility["market_volatility"] = 15  # VIX level

        # Create moderate volatility scenario
        moderate_scenario = self.counterfactual_simulator.create_scenario(
            name="Moderate Volatility Shock",
            description="Scenario with VIX rising to 25",
            interventions={"market_volatility": 25},
            evidence=evidence_with_volatility,
            target_variables=["interest_rate", "gdp_growth", "unemployment"],
            metadata={
                "regime_change_id": regime_change.regime_change_id,
                "regime_type": regime_change.new_regime.value,
                "scenario_type": "moderate_volatility",
            },
        )

        # Create severe volatility scenario
        severe_scenario = self.counterfactual_simulator.create_scenario(
            name="Severe Volatility Shock",
            description="Scenario with VIX rising to 40",
            interventions={"market_volatility": 40},
            evidence=evidence_with_volatility,
            target_variables=["interest_rate", "gdp_growth", "unemployment"],
            metadata={
                "regime_change_id": regime_change.regime_change_id,
                "regime_type": regime_change.new_regime.value,
                "scenario_type": "severe_volatility",
            },
        )

        # Run scenarios
        self.counterfactual_simulator.run_batch_scenarios(
            [moderate_scenario, severe_scenario]
        )

    def _create_generic_scenario(
        self, evidence: Dict[str, float], regime_change: RegimeChangeEvent
    ):
        """
        Create a generic counterfactual scenario for other regime types.

        Args:
            evidence: Current economic evidence
            regime_change: The regime change event
        """
        # Create a single generic scenario based on the regime type
        regime_type = regime_change.new_regime

        # Define interventions based on regime type
        interventions = {}
        if regime_type == RegimeType.MONETARY_EASING:
            interventions["interest_rate"] = evidence["interest_rate"] - 0.005  # -0.5%
        elif regime_type == RegimeType.EXPANSION:
            interventions["gdp_growth"] = evidence["gdp_growth"] + 0.01  # +1%
        elif regime_type == RegimeType.DEFLATION:
            interventions["inflation"] = -0.005  # -0.5%
        else:
            # Default intervention for unknown regimes
            interventions["gdp_growth"] = evidence["gdp_growth"] * 0.95  # 5% reduction

        # Create scenario
        scenario = self.counterfactual_simulator.create_scenario(
            name=f"{regime_type.value.title()} Scenario",
            description=f"Generic scenario for {regime_type.value} regime",
            interventions=interventions,
            evidence=evidence,
            target_variables=[
                "interest_rate",
                "inflation",
                "gdp_growth",
                "unemployment",
            ],
            metadata={
                "regime_change_id": regime_change.regime_change_id,
                "regime_type": regime_type.value,
                "scenario_type": "generic",
            },
        )

        # Run scenario
        self.counterfactual_simulator.run_scenario(scenario)

    def _store_snapshot_results(self, snapshot: RetrodictionSnapshot):
        """
        Store snapshot processing results.

        Args:
            snapshot: The processed snapshot
        """
        try:
            # Create filename
            filename = f"snapshot_results_{snapshot.snapshot_id}.json"
            file_path = os.path.join(self.storage_path, filename)

            # Get relevant counterfactual scenarios
            scenarios = []
            regime_change_id = (
                snapshot.regime_change.regime_change_id
                if snapshot.regime_change
                else None
            )
            for scenario in self.counterfactual_simulator.scenarios.values():
                if scenario.metadata.get("regime_change_id") == regime_change_id:
                    scenarios.append(scenario.to_dict())

            # Store results
            with open(file_path, "w") as f:
                json.dump(
                    {
                        "snapshot": snapshot.to_dict(),
                        "counterfactual_scenarios": scenarios,
                        "timestamp": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )

            logger.debug(f"Stored snapshot results to {file_path}")
        except Exception as e:
            logger.error(f"Error storing snapshot results: {e}")

    def start(self):
        """Start all system components."""
        logger.info("Starting retrodiction system...")

        # Start event processing
        self.event_manager.start()

        # Start retrodiction trigger
        self.retrodiction_trigger.start()

        logger.info("Retrodiction system started")

    def stop(self):
        """Stop all system components."""
        logger.info("Stopping retrodiction system...")

        # Stop components in reverse order
        self.retrodiction_trigger.stop()
        self.event_manager.stop()

        logger.info("Retrodiction system stopped")

    def ingest_economic_data(self, economic_data: Dict[str, Any]):
        """
        Ingest economic data for regime detection.

        Args:
            economic_data: Dictionary of economic indicators and their values
        """
        # Pass economic data to regime detector for processing
        self.regime_detector.update_market_data(economic_data)

    def ingest_news_event(
        self,
        headline: str,
        content: str = "",
        source: str = "news_feed",
        priority: EventPriority = EventPriority.MEDIUM,
    ):
        """
        Ingest a news event into the system.

        Args:
            headline: News headline
            content: Full news content (optional)
            source: Source of the news
            priority: Priority level for the event
        """
        # Create an event from the news
        import hashlib

        # Generate a deterministic ID based on the headline and timestamp
        timestamp = datetime.now().isoformat()
        event_id = hashlib.md5(f"{headline}|{timestamp}".encode()).hexdigest()

        event_content = headline
        if content:
            event_content = f"{headline}\n\n{content}"

        # Create the event
        event = Event(
            event_id=event_id,
            source=source,
            event_type=EventType.NEWS,
            timestamp=datetime.now(),
            content=event_content,
            entities=[],  # This would be populated by NER in a real system
            metadata={"headline": headline},
            priority=priority,
        )

        # Ingest the event
        self.event_manager.ingest_event(event)

        logger.info(f"Ingested news event: {headline}")


# Example usage
if __name__ == "__main__":
    # Create the integrator
    integrator = RetrodictionSystemIntegrator()

    # Start the system
    integrator.start()

    try:
        # Ingest some example data

        # Economic data
        economic_data = {
            "interest_rate": 0.0325,  # 3.25%
            "inflation": 0.028,  # 2.8%
            "gdp_growth": 0.02,  # 2.0%
            "unemployment": 0.048,  # 4.8%
            "volatility": 18.5,  # VIX
            "sma_50": 4800,  # S&P 500 50-day moving average
            "sma_200": 4750,  # S&P 500 200-day moving average
            "price": 4850,  # S&P 500 price
        }
        integrator.ingest_economic_data(economic_data)

        # News events
        integrator.ingest_news_event(
            "Federal Reserve signals potential rate hikes in response to inflation concerns",
            "The Federal Reserve has indicated it may need to raise interest rates faster than previously anticipated due to persistent inflation pressures.",
            priority=EventPriority.HIGH,
        )

        integrator.ingest_news_event(
            "Inflation reaches 5.4%, highest level in 13 years",
            "Consumer prices rose 5.4% in June from a year earlier, the highest 12-month rate since August 2008.",
            priority=EventPriority.HIGH,
        )

        integrator.ingest_news_event(
            "Treasury yields rise on inflation concerns",
            "The 10-year Treasury yield climbed to 3.2% as investors grow concerned about inflation persistence.",
            priority=EventPriority.MEDIUM,
        )

        # Give time for processing
        print("Processing events and detecting regimes (5 seconds)...")
        time.sleep(5)

        # Update economic data to potentially trigger a regime change
        updated_economic_data = economic_data.copy()
        updated_economic_data["inflation"] = 0.062  # Inflation jumped to 6.2%
        updated_economic_data["interest_rate"] = 0.035  # Interest rate up to 3.5%
        integrator.ingest_economic_data(updated_economic_data)

        # Give more time for processing
        print("Processing updated economic data (5 seconds)...")
        time.sleep(5)

    finally:
        # Stop the system
        integrator.stop()
