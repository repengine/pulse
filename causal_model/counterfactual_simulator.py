"""
Counterfactual Simulator for retrodiction-based "what if" scenario analysis.
Extends the basic CounterfactualEngine to provide a framework for causal inference
and hypothesis testing using the ingested economic data.
"""

import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
import json
import pickle
import time

from causal_model.counterfactual_engine import CounterfactualEngine
from causal_model.structural_causal_model import StructuralCausalModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InterventionScenario:
    """
    Represents a counterfactual scenario with specific interventions on variables.
    Contains the scenario configuration, interventions, and results.
    """

    def __init__(
        self,
        scenario_id: str,
        name: str,
        description: str,
        interventions: Dict[str, Any],
        evidence: Optional[Dict[str, Any]] = None,
        target_variables: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a counterfactual scenario.

        Args:
            scenario_id: Unique identifier for this scenario
            name: Human-readable name for the scenario
            description: Detailed description of the scenario
            interventions: Dictionary of variable interventions (do-operations)
            evidence: Dictionary of observed evidence to condition on
            target_variables: List of target variables to predict
            metadata: Additional metadata about the scenario
        """
        self.scenario_id = scenario_id
        self.name = name
        self.description = description
        self.interventions = interventions
        self.evidence = evidence or {}
        self.target_variables = target_variables or []
        self.metadata = metadata or {}
        self.creation_time = datetime.now()
        self.results = {}
        self.processed = False
        self.processing_time: Optional[timedelta] = None

    def __str__(self):
        return f"Scenario({
            self.scenario_id}, '{
            self.name}', {
            len(
                self.interventions)} interventions)"

    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to dictionary for serialization."""
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "description": self.description,
            "interventions": self.interventions,
            "evidence": self.evidence,
            "target_variables": self.target_variables,
            "metadata": self.metadata,
            "creation_time": self.creation_time.isoformat(),
            "results": self.results,
            "processed": self.processed,
            "processing_time": (
                str(self.processing_time) if self.processing_time else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterventionScenario":
        """Create a scenario from a dictionary."""
        scenario = cls(
            scenario_id=data.get("scenario_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            interventions=data.get("interventions", {}),
            evidence=data.get("evidence", {}),
            target_variables=data.get("target_variables", []),
            metadata=data.get("metadata", {}),
        )

        # Parse creation time
        creation_time_str = data.get("creation_time")
        if creation_time_str:
            try:
                scenario.creation_time = datetime.fromisoformat(
                    creation_time_str.replace("Z", "+00:00")
                )
            except ValueError:
                logger.warning(f"Invalid creation_time format: {creation_time_str}")

        # Set results and processed state
        scenario.results = data.get("results", {})
        scenario.processed = data.get("processed", False)

        # Parse processing time
        processing_time_str = data.get("processing_time")
        if processing_time_str:
            try:
                hours, minutes, seconds = processing_time_str.split(":")
                scenario.processing_time = timedelta(
                    hours=int(hours), minutes=int(minutes), seconds=float(seconds)
                )
            except (ValueError, AttributeError):
                logger.warning(f"Invalid processing_time format: {processing_time_str}")

        return scenario


class CounterfactualSimulator:
    """
    Manages counterfactual simulations for retrodiction-based "what if" analysis.
    Provides utilities for defining scenarios, running simulations, and analyzing results.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the counterfactual simulator.

        Args:
            config: Configuration parameters for simulator behavior
        """
        self.config = config or {}
        self.counterfactual_engine = None
        self.scm = None
        self.scenarios = {}
        self.data_sources = {}
        self.model_registry = {}
        self.variable_metadata = {}

        # Storage config
        self.storage_enabled = self.config.get("storage_enabled", True)
        self.storage_path = self.config.get(
            "storage_path", "data/counterfactual_scenarios"
        )
        self.model_path = self.config.get("model_path", "models/causal")

        # Initialize storage directories if enabled
        if self.storage_enabled:
            os.makedirs(self.storage_path, exist_ok=True)
            os.makedirs(self.model_path, exist_ok=True)

        # Load any existing SCM if available
        self._load_scm()

        logger.info("CounterfactualSimulator initialized")

    def _load_scm(self):
        """Load the structural causal model from storage if available."""
        scm_path = os.path.join(self.model_path, "scm.pkl")
        if os.path.exists(scm_path):
            try:
                with open(scm_path, "rb") as f:
                    self.scm = pickle.load(f)
                logger.info(f"Loaded SCM from {scm_path}")

                # Initialize counterfactual engine with the loaded SCM
                self.counterfactual_engine = CounterfactualEngine(
                    scm=self.scm,
                    max_cache_size=self.config.get("max_cache_size", 1000),
                    max_workers=self.config.get("max_workers", None),
                )
            except Exception as e:
                logger.error(f"Error loading SCM: {e}")

    def register_data_source(
        self, source_name: str, data_loader: Callable[[], pd.DataFrame]
    ):
        """
        Register a data source for use in counterfactual simulations.

        Args:
            source_name: Name of the data source
            data_loader: Function that loads the data and returns a DataFrame
        """
        self.data_sources[source_name] = data_loader
        logger.info(f"Registered data source: {source_name}")

    def register_variable_metadata(self, variable_name: str, metadata: Dict[str, Any]):
        """
        Register metadata for a variable, including domain knowledge.

        Args:
            variable_name: Name of the variable
            metadata: Dictionary of metadata (units, min/max values, description, etc.)
        """
        self.variable_metadata[variable_name] = metadata
        logger.info(f"Registered metadata for variable: {variable_name}")

    def build_scm(self, data: Optional[pd.DataFrame] = None, method: str = "pc"):
        """
        Build a structural causal model from data.

        Args:
            data: DataFrame containing the data (if None, load from registered sources)
            method: Causal discovery method to use ("pc", "fci", "lingam", etc.)
        """
        if data is None:
            # Load and combine data from all registered sources
            data_frames = []
            for source_name, data_loader in self.data_sources.items():
                try:
                    df = data_loader()
                    data_frames.append(df)
                    logger.info(
                        f"Loaded data from source: {source_name}, shape: {df.shape}"
                    )
                except Exception as e:
                    logger.error(f"Error loading data from source {source_name}: {e}")

            if not data_frames:
                raise ValueError("No data available for building SCM")

            # Combine data frames (assuming they share an index, e.g., date)
            data = pd.concat(data_frames, axis=1)

        # Drop rows with NaN values
        data = data.dropna()

        # Create a new SCM
        self.scm = StructuralCausalModel()

        # Add variables to the SCM
        for column in data.columns:
            self.scm.add_variable(column)

        # In a real implementation, we would use a causal discovery algorithm
        # to learn the causal graph from data
        if method == "pc":
            logger.info("Using PC algorithm for causal discovery")
            # Placeholder for PC algorithm implementation
            # In a real system, this would call an implementation of the PC algorithm
            # to learn the causal graph structure

            # For now, we'll manually add some example edges based on domain knowledge
            for i, var1 in enumerate(data.columns):
                for j, var2 in enumerate(data.columns):
                    if i != j and np.abs(data[var1].corr(data[var2])) > 0.3:
                        # Add edge based on correlation
                        # In reality, this decision would be based on conditional independence tests
                        # Using the correct method from StructuralCausalModel
                        self.scm.add_causal_edge(var1, var2)
        elif method == "lingam":
            logger.info("Using LiNGAM algorithm for causal discovery")
            # Placeholder for LiNGAM implementation
        else:
            logger.warning(
                f"Unknown causal discovery method: {method}, using default approach"
            )

        # Save the SCM
        if self.storage_enabled:
            scm_path = os.path.join(self.model_path, "scm.pkl")
            with open(scm_path, "wb") as f:
                pickle.dump(self.scm, f)
            logger.info(f"Saved SCM to {scm_path}")

        # Initialize counterfactual engine with the new SCM
        self.counterfactual_engine = CounterfactualEngine(
            scm=self.scm,
            max_cache_size=self.config.get("max_cache_size", 1000),
            max_workers=self.config.get("max_workers", None),
        )

        return self.scm

    def create_scenario(
        self,
        name: str,
        description: str,
        interventions: Dict[str, Any],
        evidence: Optional[Dict[str, Any]] = None,
        target_variables: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> InterventionScenario:
        """
        Create a new counterfactual scenario.

        Args:
            name: Name of the scenario
            description: Description of the scenario
            interventions: Dictionary of variable interventions
            evidence: Dictionary of observed evidence
            target_variables: List of target variables to predict
            metadata: Additional metadata

        Returns:
            The created scenario
        """
        # Generate a unique ID for the scenario
        scenario_id = f"scenario_{len(self.scenarios) +
                                  1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Create the scenario
        scenario = InterventionScenario(
            scenario_id=scenario_id,
            name=name,
            description=description,
            interventions=interventions,
            evidence=evidence,
            target_variables=target_variables,
            metadata=metadata,
        )

        # Store the scenario
        self.scenarios[scenario_id] = scenario

        # Save to disk if storage is enabled
        if self.storage_enabled:
            self._save_scenario(scenario)

        logger.info(f"Created scenario: {scenario}")

        return scenario

    def run_scenario(
        self, scenario_input: Union[str, InterventionScenario]
    ) -> Dict[str, Any]:
        """
        Run a counterfactual scenario and return the results.

        Args:
            scenario_input: Scenario object or scenario ID

        Returns:
            Dictionary of simulation results
        """
        # Ensure we have an SCM and engine
        if self.scm is None or self.counterfactual_engine is None:
            raise ValueError(
                "No structural causal model available. Call build_scm() first."
            )

        # Get the scenario object if ID was provided
        scenario: InterventionScenario
        if isinstance(scenario_input, str):
            if scenario_input not in self.scenarios:
                raise ValueError(f"Scenario not found: {scenario_input}")
            scenario = self.scenarios[scenario_input]
        else:
            scenario = scenario_input

        logger.info(f"Running counterfactual scenario: {scenario}")

        start_time = time.time()

        # Run the counterfactual simulation
        try:
            # Use the counterfactual engine to predict outcomes
            cf_results = self.counterfactual_engine.predict_counterfactual(
                evidence=scenario.evidence, interventions=scenario.interventions
            )

            # Filter results to target variables if specified
            if scenario.target_variables:
                filtered_results = {
                    var: cf_results.get(var)
                    for var in scenario.target_variables
                    if var in cf_results
                }
            else:
                filtered_results = cf_results

            # Calculate processing time
            end_time = time.time()
            processing_time = timedelta(seconds=end_time - start_time)

            # Update scenario with results
            scenario.results = {
                "counterfactual_values": filtered_results,
                "complete_values": cf_results,
                "simulation_timestamp": datetime.now().isoformat(),
            }
            scenario.processed = True
            scenario.processing_time = processing_time

            # Save updated scenario
            if self.storage_enabled:
                self._save_scenario(scenario)

            logger.info(
                f"Completed counterfactual scenario in {processing_time}: {scenario}"
            )

            return scenario.results

        except Exception as e:
            logger.error(f"Error running counterfactual scenario: {e}")
            scenario.results = {"error": str(e)}
            return scenario.results

    def run_batch_scenarios(
        self, scenario_inputs: List[Union[str, InterventionScenario]]
    ) -> List[Dict[str, Any]]:
        """
        Run multiple counterfactual scenarios in batch.

        Args:
            scenarios: List of scenario objects or scenario IDs

        Returns:
            List of simulation results
        """
        # Ensure we have an SCM and engine
        if self.scm is None or self.counterfactual_engine is None:
            raise ValueError(
                "No structural causal model available. Call build_scm() first."
            )

        # Get the scenario objects if IDs were provided
        scenario_objects = []
        for scenario_input in scenario_inputs:
            if isinstance(scenario_input, str):
                if scenario_input not in self.scenarios:
                    logger.warning(f"Scenario not found, skipping: {scenario_input}")
                    continue
                scenario_objects.append(self.scenarios[scenario_input])
            else:
                scenario_objects.append(scenario_input)

        logger.info(
            f"Running batch of {len(scenario_objects)} counterfactual scenarios"
        )

        # Prepare batch queries
        batch_queries = []
        for scenario in scenario_objects:
            batch_queries.append((scenario.evidence, scenario.interventions))

        start_time = time.time()

        # Use the counterfactual engine to run batch predictions
        try:
            batch_results = self.counterfactual_engine.predict_counterfactuals_batch(
                batch_queries
            )

            results = []
            for i, (scenario, cf_result) in enumerate(
                zip(scenario_objects, batch_results)
            ):
                # Filter results to target variables if specified
                if scenario.target_variables:
                    filtered_results = {
                        var: cf_result.get(var)
                        for var in scenario.target_variables
                        if var in cf_result
                    }
                else:
                    filtered_results = cf_result

                # Update scenario with results
                scenario.results = {
                    "counterfactual_values": filtered_results,
                    "complete_values": cf_result,
                    "simulation_timestamp": datetime.now().isoformat(),
                }
                scenario.processed = True

                # Calculate processing time (shared for batch)
                end_time = time.time()
                processing_time = timedelta(seconds=(end_time - start_time))
                scenario.processing_time = processing_time

                # Save updated scenario
                if self.storage_enabled:
                    self._save_scenario(scenario)

                results.append(scenario.results)

            batch_time = time.time() - start_time
            logger.info(
                f"Completed batch of {
                    len(scenario_objects)} counterfactual scenarios in {
                    batch_time:.2f}s")

            return results

        except Exception as e:
            logger.error(f"Error running batch counterfactual scenarios: {e}")
            return [{"error": str(e)}] * len(scenario_objects)

    def compare_scenarios(
        self, scenario_ids: List[str], variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare results across multiple scenarios.

        Args:
            scenario_ids: List of scenario IDs to compare
            variables: List of variables to include in comparison (if None, use all common variables)

        Returns:
            Dictionary with comparison results
        """
        # Get scenarios
        scenarios = []
        for scenario_id in scenario_ids:
            if scenario_id not in self.scenarios:
                logger.warning(f"Scenario not found, skipping: {scenario_id}")
                continue
            scenario = self.scenarios[scenario_id]
            if not scenario.processed:
                logger.warning(f"Scenario not processed, skipping: {scenario_id}")
                continue
            scenarios.append(scenario)

        if not scenarios:
            raise ValueError("No valid scenarios to compare")

        # Determine variables to compare
        if variables is None:
            # Find common variables across all scenarios
            common_vars = set()
            for i, scenario in enumerate(scenarios):
                results = scenario.results.get("counterfactual_values", {})
                if i == 0:
                    common_vars = set(results.keys())
                else:
                    common_vars &= set(results.keys())
            variables = list(common_vars)

        # Extract values for comparison
        comparison = {
            "scenario_info": {
                scenario.scenario_id: {
                    "name": scenario.name,
                    "description": scenario.description,
                }
                for scenario in scenarios
            },
            "variables": {},
            "comparison_timestamp": datetime.now().isoformat(),
        }

        for var in variables:
            comparison["variables"][var] = {}
            for scenario in scenarios:
                results = scenario.results.get("counterfactual_values", {})
                if var in results:
                    comparison["variables"][var][scenario.scenario_id] = results[var]

        return comparison

    def _save_scenario(self, scenario: InterventionScenario):
        """
        Save a scenario to disk.

        Args:
            scenario: Scenario to save
        """
        try:
            # Create filename
            filename = f"{scenario.scenario_id}.json"
            file_path = os.path.join(self.storage_path, filename)

            # Store as JSON
            with open(file_path, "w") as f:
                json.dump(scenario.to_dict(), f, indent=2)

            logger.debug(f"Saved scenario to {file_path}")
        except Exception as e:
            logger.error(f"Error saving scenario: {e}")

    def load_scenarios(self):
        """Load all scenarios from storage."""
        if not self.storage_enabled:
            logger.warning("Storage is disabled, cannot load scenarios")
            return

        # Clear existing scenarios
        self.scenarios = {}

        # Get all JSON files in the storage directory
        scenario_files = [
            f for f in os.listdir(self.storage_path) if f.endswith(".json")
        ]

        for filename in scenario_files:
            try:
                file_path = os.path.join(self.storage_path, filename)
                with open(file_path, "r") as f:
                    scenario_data = json.load(f)

                # Create scenario from data
                scenario = InterventionScenario.from_dict(scenario_data)

                # Add to scenarios
                self.scenarios[scenario.scenario_id] = scenario

            except Exception as e:
                logger.error(f"Error loading scenario from {filename}: {e}")

        logger.info(f"Loaded {len(self.scenarios)} scenarios from storage")

    def get_scenario(self, scenario_id: str) -> Optional[InterventionScenario]:
        """
        Get a scenario by ID.

        Args:
            scenario_id: ID of the scenario to get

        Returns:
            Scenario object if found, None otherwise
        """
        return self.scenarios.get(scenario_id)

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """
        Get a list of all scenarios with basic information.

        Returns:
            List of dictionaries with scenario information
        """
        return [
            {
                "scenario_id": scenario.scenario_id,
                "name": scenario.name,
                "description": scenario.description,
                "creation_time": scenario.creation_time.isoformat(),
                "processed": scenario.processed,
                "num_interventions": len(scenario.interventions),
            }
            for scenario in self.scenarios.values()
        ]

    def delete_scenario(self, scenario_id: str) -> bool:
        """
        Delete a scenario by ID.

        Args:
            scenario_id: ID of the scenario to delete

        Returns:
            True if deleted, False otherwise
        """
        if scenario_id not in self.scenarios:
            return False

        # Remove from scenarios
        del self.scenarios[scenario_id]

        # Delete file if storage is enabled
        if self.storage_enabled:
            file_path = os.path.join(self.storage_path, f"{scenario_id}.json")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error deleting scenario file {file_path}: {e}")

        logger.info(f"Deleted scenario: {scenario_id}")
        return True


# Example usage
if __name__ == "__main__":
    # Create a simulator
    simulator = CounterfactualSimulator()

    # Create a simple SCM with a few variables
    scm = StructuralCausalModel()
    scm.add_variable("interest_rate")
    scm.add_variable("inflation")
    scm.add_variable("gdp_growth")
    scm.add_variable("unemployment")

    # Add causal relationships
    # Using the correct method from StructuralCausalModel
    scm.add_causal_edge("interest_rate", "inflation")
    scm.add_causal_edge("interest_rate", "gdp_growth")
    scm.add_causal_edge("gdp_growth", "unemployment")
    scm.add_causal_edge("inflation", "gdp_growth")

    # Initialize the engine with this SCM
    simulator.scm = scm
    simulator.counterfactual_engine = CounterfactualEngine(scm=scm)

    # Create a scenario
    scenario = simulator.create_scenario(
        name="Interest Rate Hike",
        description="Counterfactual scenario where the Fed raises interest rates by 0.5%",
        interventions={"interest_rate": 0.05},  # Intervene to set interest rate to 5%
        evidence={
            "inflation": 0.03,  # Current inflation is 3%
            "gdp_growth": 0.025,  # Current GDP growth is 2.5%
            "unemployment": 0.045,  # Current unemployment is 4.5%
        },
        target_variables=["inflation", "gdp_growth", "unemployment"],
        metadata={"source": "example"},
    )

    # Run the scenario
    results = simulator.run_scenario(scenario)

    # Print results
    print(f"Scenario: {scenario.name}")
    print(f"Results: {results}")
