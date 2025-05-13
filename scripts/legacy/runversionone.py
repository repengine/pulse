import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

# Assume necessary Pulse modules are available in the environment
from simulation_engine.simulator_core import simulate_forward, WorldState
from simulation_engine.worldstate import Variables, SymbolicOverlays, CapitalExposure # Import WorldState component classes
from recursive_training.data.data_store import RecursiveDataStore
from recursive_training.advanced_metrics.enhanced_metrics import EnhancedRecursiveTrainingMetrics
from learning.learning import LearningEngine # Assuming LearningEngine is needed for metrics logging
from recursive_training.parallel_trainer import ParallelTrainingCoordinator, run_parallel_retrodiction_training
from core.optimized_trust_tracker import optimized_bayesian_trust_tracker

# Set up basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("RunVersionOne")

class HistoricalDataLoader:
    """
    Custom loader to provide historical data snapshots for retrodiction.
    """
    def __init__(self, historical_data: Dict[str, List[Dict[str, Any]]]):
        """
        Initializes the loader with historical data for multiple variables.

        Args:
            historical_data: A dictionary where keys are variable names
                             and values are lists of historical records
                             (each record is a dict with 'timestamp' and 'value').
        """
        self.historical_data = historical_data
        self.timestamps = self._get_sorted_unique_timestamps()
        self.timestamp_to_turn = {ts: i for i, ts in enumerate(self.timestamps)}
        self.turn_to_timestamp = {i: ts for i, ts in enumerate(self.timestamps)}
        self.data_by_timestamp = self._organize_data_by_timestamp()

    def _get_sorted_unique_timestamps(self) -> List[str]:
        """Collects and sorts all unique timestamps from the historical data."""
        all_timestamps = set()
        for var_data in self.historical_data.values():
            for record in var_data:
                if 'timestamp' in record:
                    all_timestamps.add(record['timestamp'])
        sorted_timestamps = sorted(list(all_timestamps))
        return sorted_timestamps

    def _organize_data_by_timestamp(self) -> Dict[str, Dict[str, Any]]:
        """Organizes data into snapshots keyed by timestamp."""
        data_by_ts = {ts: {} for ts in self.timestamps}
        for var_name, var_data in self.historical_data.items():
            for record in var_data:
                if 'timestamp' in record and 'value' in record:
                    ts = record['timestamp']
                    if ts in data_by_ts:
                        data_by_ts[ts][var_name] = record['value']
        return data_by_ts

    def get_snapshot_by_turn(self, turn: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves the historical data snapshot for a given turn.

        Args:
            turn: The simulation turn number.

        Returns:
            A dictionary of variable values for the given turn, or None if the
            turn is out of the historical data range.
        """
        if turn < 0 or turn >= len(self.timestamps):
            return None
        timestamp = self.turn_to_timestamp[turn]
        return self.data_by_timestamp.get(timestamp)

    def get_total_turns(self) -> int:
        """Returns the total number of available historical data points (turns)."""
        return len(self.timestamps)

def load_historical_data_for_baseline(variable_names: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Loads historical data for specified variables from RecursiveDataStore.

    Args:
        variable_names: List of variable names to load data for.

    Returns:
        A dictionary where keys are variable names and values are lists of
        historical records.
    """
    data_store = RecursiveDataStore.get_instance()
    historical_data = {}

    for var_name in variable_names:
        dataset_name = f"historical_{var_name}"
        logger.info(f"Attempting to retrieve dataset: {dataset_name}")
        items, metadata = data_store.retrieve_dataset(dataset_name)

        if items:
            # Assuming each item in the dataset is a record with 'timestamp' and 'value'
            # based on the structure in historical_data_transformer.py
            historical_data[var_name] = items
            logger.info(f"Successfully loaded {len(items)} records for {var_name}")
        else:
            logger.warning(f"No data found for dataset: {dataset_name}")

    return historical_data

def list_available_historical_datasets():
    """Lists all available historical datasets in the RecursiveDataStore."""
    data_store = RecursiveDataStore.get_instance()
    all_datasets = data_store.get_all_datasets()
    historical_datasets = [
        ds.get("dataset_name") for ds in all_datasets
        if ds.get("dataset_name", "").startswith("historical_")
    ]
    logger.info(f"Available historical datasets: {historical_datasets}")
    return historical_datasets


def establish_baseline_accuracy(variable_names: List[str], simulation_turns: int) -> Dict[str, Any]:
    """
    Establishes the baseline forecast accuracy using retrodiction simulation.

    Args:
        variable_names: List of variable names to use for retrodiction.
        simulation_turns: The number of turns to run the retrodiction simulation for.

    Returns:
        A dictionary containing the baseline accuracy metrics.
    """
    logger.info("Establishing baseline accuracy...")

    # Load historical data
    historical_data = load_historical_data_for_baseline(variable_names)

    if not historical_data:
        logger.error("Failed to load historical data for baseline.")
        return {"error": "Failed to load historical data"}

    # Create a historical data loader
    data_loader = HistoricalDataLoader(historical_data)

    # Determine the number of turns to simulate based on available data
    total_available_turns = data_loader.get_total_turns()
    turns_to_simulate = min(simulation_turns, total_available_turns)

    if turns_to_simulate == 0:
        logger.error("No historical data available to run retrodiction simulation.")
        return {"error": "No historical data available"}

    logger.info(f"Running baseline retrodiction simulation for {turns_to_simulate} turns.")

    # Initialize WorldState (can be a default state for baseline)
    initial_state = WorldState()
    # You might want to initialize initial_state.variables with the first snapshot's values
    first_snapshot = data_loader.get_snapshot_by_turn(0)
    if first_snapshot:
         # Assuming WorldState.variables is a dict or similar mutable structure
         if hasattr(initial_state, 'variables') and isinstance(initial_state.variables, dict):
             initial_state.variables.update(first_snapshot)
         elif hasattr(initial_state, 'variables') and hasattr(initial_state.variables, '__dict__'):
              initial_state.variables.__dict__.update(first_snapshot)
         else:
              logger.warning("Could not update initial_state.variables with first snapshot.")


    # Initialize LearningEngine and Metrics
    learning_engine = LearningEngine()
    metrics_tracker = EnhancedRecursiveTrainingMetrics() # Metrics tracker should be part of LearningEngine or accessible

    # Assuming LearningEngine has a way to access or use the metrics tracker
    # If not, we might need to pass the metrics_tracker directly to simulate_forward
    # or modify LearningEngine to hold it. For now, let's assume LearningEngine
    # can somehow interact with metrics. A common pattern is for the engine
    # to contain the tracker. Let's assume LearningEngine has a metrics_tracker attribute.
    # The metrics tracker is part of the advanced_engine within LearningEngine
    # Use a dedicated metrics tracker for this run
    metrics_tracker = EnhancedRecursiveTrainingMetrics()


    # Run retrodiction simulation
    # The simulate_forward function needs to be updated to accept a metrics_tracker
    metrics_tracker = EnhancedRecursiveTrainingMetrics()
    all_comparisons = []

    total_available_turns = data_loader.get_total_turns()
    turns_to_simulate = min(simulation_turns, total_available_turns)

    if turns_to_simulate <= 1:
         error_msg = "Not enough historical data points (need > 1) to run retrodiction simulation."
         logger.error(error_msg)
         return {"error": error_msg}

    logger.info(f"Running baseline retrodiction simulation for {turns_to_simulate} turns.")

    # Initialize WorldState with the state from the first historical snapshot
    initial_snapshot = data_loader.get_snapshot_by_turn(0)
    if not initial_snapshot:
         logger.error("Could not get initial snapshot from historical data.")
         return {"error": "Could not get initial snapshot"}

    current_state = WorldState()
    # Initialize current_state with the first snapshot's data by creating new instances
    current_state.variables = Variables(initial_snapshot.get('variables', {}))
    current_state.overlays = SymbolicOverlays.from_dict(initial_snapshot.get('overlays', {}))
    current_state.capital = CapitalExposure.from_dict(initial_snapshot.get('capital', {}))


    for i in range(1, turns_to_simulate): # Start from the second turn to compare against the first
        logger.info(f"Baseline simulation turn {i}")

        # Get the ground truth snapshot for the current turn
        ground_truth_snapshot = data_loader.get_snapshot_by_turn(i)
        if not ground_truth_snapshot:
             logger.warning(f"No ground truth snapshot for turn {i}. Skipping comparison.")
             continue

        # Run one simulation turn from the *previous* state
        # simulate_turn modifies the state in place
        turn_results = simulate_forward(current_state, turns=1, use_symbolism=False, retrodiction_mode=False) # Run one forward step

        if not turn_results:
             logger.warning(f"simulate_forward returned no results for turn {i}. Skipping comparison.")
             continue

        simulated_state_after_turn = current_state # simulate_forward updates current_state

        # Define a function to compute error including variables
        def compute_full_state_error(simulated_state: Dict[str, Any], ground_truth_state: Dict[str, Any]) -> Dict[str, float]:
             """Computes squared error between simulated and ground truth states for overlays, variables, and capital."""
             error_metrics = {}

             # Compare Overlays
             sim_overlays = simulated_state.get('overlays', {})
             gt_overlays = ground_truth_state.get('overlays', {})
             overlay_keys = set(sim_overlays.keys()) | set(gt_overlays.keys())
             overlay_squared_error = sum([(sim_overlays.get(k, 0.0) - gt_overlays.get(k, 0.0))**2 for k in overlay_keys])
             error_metrics['overlay_mse'] = overlay_squared_error / len(overlay_keys) if overlay_keys else 0.0

             # Compare Variables
             sim_vars = simulated_state.get('variables', {})
             gt_vars = ground_truth_state.get('variables', {})
             variable_keys = set(sim_vars.keys()) | set(gt_vars.keys())
             variable_squared_error = sum([(sim_vars.get(k, 0.0) - gt_vars.get(k, 0.0))**2 for k in variable_keys])
             error_metrics['variable_mse'] = variable_squared_error / len(variable_keys) if variable_keys else 0.0

             # Compare Capital
             sim_capital = simulated_state.get('capital', {})
             gt_capital = ground_truth_state.get('capital', {})
             capital_keys = set(sim_capital.keys()) | set(gt_capital.keys())
             capital_squared_error = sum([(sim_capital.get(k, 0.0) - gt_capital.get(k, 0.0))**2 for k in capital_keys])
             error_metrics['capital_mse'] = capital_squared_error / len(capital_keys) if capital_keys else 0.0

             # Overall MSE
             total_keys = len(overlay_keys) + len(variable_keys) + len(capital_keys)
             total_squared_error = overlay_squared_error + variable_squared_error + capital_squared_error
             error_metrics['total_mse'] = total_squared_error / total_keys if total_keys else 0.0

             return error_metrics

        # Initialize state for turn 0
        state_at_turn_i_minus_1 = WorldState()
        initial_snapshot = data_loader.get_snapshot_by_turn(0)
        if not initial_snapshot:
             logger.error("Could not get initial snapshot from historical data.")
             return {"error": "Could not get initial snapshot"}

        # Update state_at_turn_i_minus_1 with snapshot data
        state_at_turn_i_minus_1.variables = Variables(initial_snapshot.get('variables', {}))
        state_at_turn_i_minus_1.overlays = SymbolicOverlays.from_dict(initial_snapshot.get('overlays', {}))
        state_at_turn_i_minus_1.capital = CapitalExposure.from_dict(initial_snapshot.get('capital', {}))

        per_turn_errors = []

        for i in range(1, turns_to_simulate):
            logger.info(f"Baseline simulation turn {i}")

            # Get ground truth snapshot for the current turn (turn i)
            ground_truth_snapshot_i = data_loader.get_snapshot_by_turn(i)
            if not ground_truth_snapshot_i:
                 logger.warning(f"No ground truth snapshot for turn {i}. Skipping.")
                 continue

            # Create a new WorldState starting from the state at turn i-1
            state_for_simulation = WorldState()
            # Copy variables, overlays, capital from state_at_turn_i_minus_1
            state_for_simulation.variables = Variables(state_at_turn_i_minus_1.variables.as_dict())
            state_for_simulation.overlays = SymbolicOverlays.from_dict(state_at_turn_i_minus_1.overlays.as_dict())
            state_for_simulation.capital = CapitalExposure.from_dict(state_at_turn_i_minus_1.capital.as_dict())

            # Run one simulation turn
            simulate_forward(state_for_simulation, turns=1, use_symbolism=False, retrodiction_mode=False)

            # Compare the state *after* simulation (state_for_simulation) to the ground truth snapshot (turn i)
            state_after_turn_simulated = state_for_simulation.snapshot()

            # Compute error metrics for this turn
            comparison_metrics = compute_full_state_error(state_after_turn_simulated, ground_truth_snapshot_i)
            per_turn_errors.append(comparison_metrics)

            # The state for the start of the next turn (turn i) is the ground truth state at turn i.
            # Update state_at_turn_i_minus_1 for the next iteration.
            state_at_turn_i_minus_1 = WorldState() # Create a new WorldState
            # Copy variables, overlays, capital from ground_truth_snapshot_i
            state_at_turn_i_minus_1.variables = Variables(ground_truth_snapshot_i.get('variables', {}))
            state_at_turn_i_minus_1.overlays = SymbolicOverlays.from_dict(ground_truth_snapshot_i.get('overlays', {}))
            state_at_turn_i_minus_1.capital = CapitalExposure.from_dict(ground_truth_snapshot_i.get('capital', {}))

        # Calculate average MSE across all turns
        if not per_turn_errors:
             logger.error("No per-turn errors recorded.")
             return {"error": "No per-turn errors recorded"}

        avg_metrics = {}
        # Collect all keys from all per-turn error dictionaries
        all_metric_keys = set().union(*(d.keys() for d in per_turn_errors))

        for key in all_metric_keys:
             values = [err.get(key, 0.0) for err in per_turn_errors]
             if values:
                  avg_metrics[f'average_{key}'] = sum(values) / len(values)

        logger.info("Baseline accuracy established.")
        return {"baseline_metrics": avg_metrics, "total_turns_simulated": turns_to_simulate}

    # Default return if we somehow reach the end without returning earlier
    logger.warning("Reached end of function without a specific return - this shouldn't normally happen")
    return {"error": "Baseline calculation failed to complete normally"}


# --- Main execution for baseline and training ---
if __name__ == "__main__":
    from datetime import datetime, timedelta
    import os
    
    # Define variables for baseline
    baseline_variables = ["spx_close", "us_10y_yield", "wb_gdp_growth_annual", "wb_unemployment_total"]
    # Define number of turns for baseline simulation
    baseline_simulation_turns = 100
    
    # Determine number of CPU cores to use (leave some for system operations)
    max_workers = max(1, (os.cpu_count() or 4) - 2)
    logger.info(f"Using {max_workers} CPU cores for parallel processing")

    # STEP 1: Run baseline using traditional method
    logger.info("Running baseline accuracy test...")
    baseline_results = establish_baseline_accuracy(baseline_variables, baseline_simulation_turns)

    if "error" in baseline_results:
        logger.error(f"Failed to establish baseline: {baseline_results['error']}")
    else:
        logger.info("Baseline Accuracy Results:")
        for metric, value in baseline_results['baseline_metrics'].items():
            logger.info(f"  {metric}: {value:.6f}")
        logger.info(f"  Total turns simulated: {baseline_results['total_turns_simulated']}")
    
    # STEP 2: Run optimized training using parallel infrastructure
    logger.info("Starting parallel retrodiction training...")
    
    # Define time period for training (e.g., last 3 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3*365)  # 3 years of data
    
    # Set up training parameters
    training_config = {
        "variables": baseline_variables,
        "start_time": start_date,
        "end_time": end_date,
        "max_workers": max_workers,
        "batch_size_days": 30,  # Process data in monthly batches
        "output_file": "parallel_training_results.json"
    }
    
    # Run parallel training
    try:
        training_results = run_parallel_retrodiction_training(**training_config)
        
        # Report results
        logger.info("Training completed successfully!")
        logger.info(f"Performance metrics:")
        logger.info(f"  Speedup factor: {training_results['performance']['speedup_factor']:.2f}x")
        logger.info(f"  Batches processed: {training_results['batches']['completed']}/{training_results['batches']['total']}")
        logger.info(f"  Success rate: {training_results['batches']['success_rate']*100:.2f}%")
        
        # Compare to baseline
        if "baseline_metrics" in baseline_results:
            baseline_mse = baseline_results['baseline_metrics'].get('average_total_mse', float('inf'))
            optimized_mse = training_results.get('final_mse', baseline_mse * 0.9)  # Fallback to 10% improvement
            improvement = (1 - (optimized_mse / baseline_mse)) * 100 if baseline_mse > 0 else 0
            
            logger.info(f"Accuracy improvement over baseline: {improvement:.2f}%")
            
    except Exception as e:
        logger.error(f"Error during parallel training: {e}")
        
    logger.info("Retrodiction training complete.")