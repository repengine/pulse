"""
Parallel Training Framework for Pulse Retrodiction

This module provides a parallel training framework that efficiently distributes
retrodiction training workloads across multiple CPU cores for improved performance.

The framework now supports Dask's distributed computing capabilities through LocalCluster
integration, providing enhanced parallel processing with the following benefits:
- Dynamic task scheduling with work stealing for better resource utilization
- Built-in diagnostics and visualization through the Dask dashboard
- Improved error handling and task tracking
- Better scalability from single machines to potential distributed deployment
"""

import os
import time
import logging
import multiprocessing as mp
from functools import partial
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
import numpy as np
from datetime import datetime, timedelta
import json
from dask.distributed import Client, LocalCluster

# Import components needed for parallel training
from recursive_training.data.data_store import RecursiveDataStore
from recursive_training.metrics.metrics_store import get_metrics_store
from recursive_training.metrics.async_metrics_collector import get_async_metrics_collector
from core.optimized_trust_tracker import optimized_bayesian_trust_tracker
from core.trust_update_buffer import get_trust_update_buffer

logger = logging.getLogger(__name__)

class TrainingBatch:
    """Represents a batch of training data that can be processed in parallel"""
    
    def __init__(self, 
                batch_id: str,
                start_time: datetime,
                end_time: datetime,
                variables: List[str],
                dataset_name: Optional[str] = None):
        """
        Initialize a training batch.
        
        Args:
            batch_id: Unique identifier for this batch
            start_time: Start of the time period for this batch
            end_time: End of the time period for this batch
            variables: List of variables to include in this batch
            dataset_name: Optional name of dataset
        """
        self.batch_id = batch_id
        self.start_time = start_time
        self.end_time = end_time
        self.variables = variables
        self.dataset_name = dataset_name
        
        # Runtime attributes
        self.processed = False
        self.processing_time = 0.0
        self.results = None
        self.error = None

class ParallelTrainingCoordinator:
    """
    Coordinates parallel training jobs for retrodiction training.
    
    This class handles:
    - Splitting training data into independent batches
    - Distributing batches across multiple CPU cores using Dask LocalCluster
    - Collecting and merging results from parallel processes
    - Managing shared state and synchronization
    - Tracking progress and handling errors
    
    This implementation uses Dask's distributed computing framework with a LocalCluster
    for more efficient parallel processing, monitoring, and scaling capabilities.
    """
    
    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 max_workers: Optional[int] = None,
                 shared_memory_size_mb: int = 128,
                 dask_scheduler_port: Optional[int] = None,
                 dask_dashboard_port: Optional[int] = None,
                 dask_threads_per_worker: int = 1):
        """
        Initialize the parallel training coordinator with Dask configuration.
        
        Args:
            config: Configuration dictionary
            max_workers: Maximum number of worker processes (defaults to CPU count - 1)
            shared_memory_size_mb: Size of shared memory buffer in MB
            dask_scheduler_port: Optional port for Dask scheduler (default: auto-assign)
            dask_dashboard_port: Optional port for Dask dashboard (default: auto-assign)
            dask_threads_per_worker: Number of threads per Dask worker (default: 1)
        """
        self.config = config or {}
        self.max_workers = max_workers or max(1, (os.cpu_count() or 4) - 1)
        self.shared_memory_size = shared_memory_size_mb * 1024 * 1024  # Convert to bytes
        
        # Store Dask-specific configuration
        self.dask_scheduler_port = dask_scheduler_port
        self.dask_dashboard_port = dask_dashboard_port
        self.dask_threads_per_worker = dask_threads_per_worker
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initializing parallel training with {self.max_workers} workers")
        
        # Initialize data store and metrics components
        # Initialize data store
        try:
            # Try to use the streaming data store first for best performance
            from recursive_training.data.streaming_data_store import StreamingDataStore
            self.data_store = StreamingDataStore.get_instance()
            self.logger.info("Using StreamingDataStore for enhanced streaming performance")
        except ImportError:
            try:
                # Fall back to optimized data store if streaming is not available
                from recursive_training.data.optimized_data_store import OptimizedDataStore
                self.data_store = OptimizedDataStore.get_instance()
                self.logger.info("Using OptimizedDataStore for enhanced performance")
            except ImportError:
                # Fall back to regular data store if neither is available
                self.data_store = RecursiveDataStore.get_instance()
                self.logger.info("Using standard RecursiveDataStore")
        
        # Initialize metrics and trust components
        self.metrics_store = get_metrics_store()
        self.async_metrics = get_async_metrics_collector()
        self.trust_buffer = get_trust_update_buffer()
        self.logger.info("Using AsyncMetricsCollector and TrustUpdateBuffer for optimized performance")
        
        # State tracking
        self.batches = []
        self.running_processes = []
        self.batch_results = {}
        self.training_start_time = None
        self.training_end_time = None
        self.is_training = False
        self.total_processed = 0
        self.errors = []
        
        # Initialize thread pool for parallel data loading
        from concurrent.futures import ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Dask-related attributes
        self.dask_futures = []
        
        # Performance metrics
        self.performance_metrics = {
            "total_batches": 0,
            "completed_batches": 0,
            "failed_batches": 0,
            "total_variables": 0,
            "processing_time": 0.0,
            "speedup_factor": 0.0,
            "estimated_sequential_time": 0.0
        }
        
        # Progress tracking
        self.progress_callback = None
        
        # Register signal handlers for graceful shutdown
        self._register_signal_handlers()
    
    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown."""
        import signal
        
        def handle_signal(sig, frame):
            self.logger.warning(f"Received signal {sig}, shutting down training gracefully")
            self.stop_training()
        
        try:
            signal.signal(signal.SIGINT, handle_signal)
            signal.signal(signal.SIGTERM, handle_signal)
        except (AttributeError, ValueError):
            # Signal handling might not be available on all platforms
            pass
    
    def prepare_training_batches(self,
                               variables: List[str],
                               start_time: datetime,
                               end_time: datetime,
                               batch_size_days: int = 30,
                               overlap_days: int = 5,
                               batch_limit: Optional[int] = None,
                               preload_data: bool = True) -> List[TrainingBatch]:
        """
        Prepare batches for parallel training.
        
        Args:
            variables: List of variables to train on
            start_time: Start of the overall training period
            end_time: End of the overall training period
            batch_size_days: Size of each batch in days
            overlap_days: Overlap between consecutive batches in days
            batch_limit: Optional limit on number of batches (for testing)
            
        Returns:
            List of TrainingBatch objects
        """
        self.logger.info(f"Preparing training batches from {start_time} to {end_time}")
        
        # Validate inputs
        if not variables:
            raise ValueError("No variables specified for training")
        
        if start_time >= end_time:
            raise ValueError("Start time must be before end time")
        
        if batch_size_days <= 0:
            raise ValueError("Batch size must be positive")
        
        # Calculate time delta for batch size and overlap
        batch_delta = timedelta(days=batch_size_days)
        overlap_delta = timedelta(days=overlap_days)
        
        # Try to preload datasets if requested and streaming store is available
        if preload_data:
            try:
                from recursive_training.data.streaming_data_store import StreamingDataStore
                streaming_store = StreamingDataStore.get_instance()
                
                # Preload datasets for common variables
                self.logger.info(f"Preloading datasets for {len(variables)} variables")
                historical_datasets = [f"historical_{var}" for var in variables]
                self.executor.submit(streaming_store.preload_datasets, historical_datasets)
            except ImportError:
                # Streaming store not available
                pass
        
        # Create batches
        batches = []
        batch_start = start_time
        batch_id = 0
        
        while batch_start < end_time:
            # Calculate batch end time
            batch_end = min(batch_start + batch_delta, end_time)
            
            # Skip if this batch would be too small
            if (batch_end - batch_start).total_seconds() < 86400:  # At least 1 day
                break
            
            # Create the batch
            batch = TrainingBatch(
                batch_id=f"batch_{batch_id:04d}",
                start_time=batch_start,
                end_time=batch_end,
                variables=variables
            )
            
            batches.append(batch)
            batch_id += 1
            
            # Move to next batch start, considering overlap
            batch_start = batch_end - overlap_delta
            
            # Stop if we've reached the batch limit
            if batch_limit is not None and len(batches) >= batch_limit:
                break
        
        self.logger.info(f"Created {len(batches)} training batches")
        self.batches = batches
        self.performance_metrics["total_batches"] = len(batches)
        self.performance_metrics["total_variables"] = len(variables)
        
        return batches
    
    def start_training(self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """
        Start parallel training process using Dask LocalCluster.
        
        Args:
            progress_callback: Optional callback function for progress updates
        """
        if self.is_training:
            self.logger.warning("Training is already in progress")
            return
        
        if not self.batches:
            self.logger.error("No training batches prepared")
            raise RuntimeError("No training batches prepared. Call prepare_training_batches first.")
        
        self.training_start_time = datetime.now()
        self.is_training = True
        self.progress_callback = progress_callback
        
        self.logger.info(f"Starting parallel training with Dask LocalCluster using {len(self.batches)} batches")
        
        # Reset futures list
        self.dask_futures = []
        
        # Create a Dask local cluster with direct parameter passing
        cluster_kwargs = {}
        
        # Set required parameters
        cluster_kwargs['n_workers'] = self.max_workers
        cluster_kwargs['threads_per_worker'] = self.dask_threads_per_worker
        
        # Set optional parameters only if they're specified
        if self.dask_dashboard_port is not None:
            dashboard_address = f":{self.dask_dashboard_port}"
            cluster_kwargs['dashboard_address'] = dashboard_address
            self.logger.info(f"Setting Dask dashboard at {dashboard_address}")
            
        if self.dask_scheduler_port is not None:
            cluster_kwargs['scheduler_port'] = self.dask_scheduler_port
            
        # Create and use the cluster
        with LocalCluster(**cluster_kwargs) as cluster:
            self.logger.info(f"Dask cluster started with {self.max_workers} workers, "
                             f"{self.dask_threads_per_worker} threads per worker")
            
            with Client(cluster) as client:
                self.logger.info(f"Connected to Dask cluster at {client.dashboard_link}")
                # Store cluster information for performance metrics
                self.dask_cluster_info = {
                    'dashboard_link': client.dashboard_link,
                    'scheduler_address': str(client.scheduler_info().get('address', 'unknown')),
                    'n_workers': len(client.scheduler_info()['workers']),
                    'worker_threads': self.dask_threads_per_worker
                }
                
                # Process batches in parallel using Dask
                for batch in self.batches:
                    # Use the same signature as the previous implementation to maintain compatibility
                    future = client.submit(self._process_batch, batch)
                    self.dask_futures.append(future)
                
                # Report progress periodically while waiting
                completed = 0
                while completed < len(self.dask_futures) and self.is_training:
                    completed = sum(1 for f in self.dask_futures if f.done())
                    self._report_progress(completed)
                    time.sleep(2)  # Check progress every 2 seconds
                
                # Only process results if training wasn't stopped
                if self.is_training:
                    # Collect results
                    for i, future in enumerate(self.dask_futures):
                        if future.done():
                            try:
                                batch_id, result = future.result()
                                self._on_batch_complete((batch_id, result))
                            except Exception as e:
                                self.logger.error(f"Error processing batch {i}: {str(e)}")
                                self._on_batch_error(e)
        
        # Final processing
        self.training_end_time = datetime.now()
        self.is_training = False
        
        # Calculate final performance metrics
        total_time = (self.training_end_time - self.training_start_time).total_seconds()
        self.performance_metrics["processing_time"] = total_time
        
        if self.performance_metrics["completed_batches"] > 0:
            # Estimate sequential processing time based on completed batches
            avg_batch_time = sum(b.processing_time for b in self.batches if b.processed) / self.performance_metrics["completed_batches"]
            est_sequential_time = avg_batch_time * len(self.batches)
            self.performance_metrics["estimated_sequential_time"] = est_sequential_time
            
            if total_time > 0:
                self.performance_metrics["speedup_factor"] = est_sequential_time / total_time
        
        # Final progress report
        self._report_progress(len(self.batches))
        
        self.logger.info(f"Training completed in {total_time:.2f}s with a speedup factor of {self.performance_metrics['speedup_factor']:.2f}x")
    
    def _process_batch(self, batch: TrainingBatch) -> Tuple[str, Dict[str, Any]]:
        """
        Process a single training batch.
        This function runs in a separate process.
        
        Args:
            batch: The training batch to process
            
        Returns:
            Tuple of (batch_id, results_dict)
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing batch {batch.batch_id} (variables: {len(batch.variables)}, period: {batch.start_time} to {batch.end_time})")
            
            # Load the data for this batch
            data = self._load_batch_data(batch)
            
            # Run the retrodiction training for this batch
            results = self._run_retrodiction_on_batch(batch, data)
            
            # Store metrics for this batch
            self._store_batch_metrics(batch, results)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            return batch.batch_id, {
                "success": True,
                "processing_time": processing_time,
                "metrics": results.get("metrics", {}),
                "rules_generated": results.get("rules_generated", []),
                "trust_updates": results.get("trust_updates", {})
            }
            
        except Exception as e:
            self.logger.error(f"Error processing batch {batch.batch_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return batch.batch_id, {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "processing_time": time.time() - start_time
            }
    
    def _load_batch_data(self, batch: TrainingBatch) -> Dict[str, Any]:
        """
        Load data for a training batch.
        
        Args:
            batch: The training batch
            
        Returns:
            Dictionary containing the loaded data
        """
        # Convert timestamps to the format used in data store
        start_str = batch.start_time.isoformat()
        end_str = batch.end_time.isoformat()
        
        data = {}
        
        # Initialize flags and store references
        use_streaming = False
        use_optimized = False
        streaming_store = None
        optimized_store = None
        
        # Check if we have streaming data store available
        try:
            from recursive_training.data.streaming_data_store import StreamingDataStore
            streaming_store = StreamingDataStore.get_instance()
            use_streaming = True
        except ImportError:
            use_streaming = False
            # Try optimized data store as fallback
            try:
                from recursive_training.data.optimized_data_store import OptimizedDataStore
                optimized_store = OptimizedDataStore.get_instance()
                use_optimized = True
            except ImportError:
                self.logger.warning("Optimized data stores not available, falling back to standard implementation")
                use_optimized = False
                
        # Use the best available data loading approach
        if use_streaming:
            # Pre-load datasets that will be needed for upcoming batches for better latency
            upcoming_variables = self._get_upcoming_batch_variables(batch)
            if upcoming_variables and streaming_store is not None:
                self.logger.debug(f"Pre-loading datasets for upcoming batches: {len(upcoming_variables)} variables")
                self.executor.submit(streaming_store.preload_datasets,
                                    [f"historical_{var}" for var in upcoming_variables])
            
            # Process each variable
            for variable in batch.variables:
                dataset_name = f"historical_{variable}"
                
                # Use callback-based streaming for memory efficiency
                variable_data = []
                
                def process_chunk(chunk):
                    # Filter by timestamp if needed (should already be filtered by the store)
                    if not chunk.empty:
                        nonlocal variable_data
                        # Convert DataFrame chunk to list of dictionaries and append
                        variable_data.extend(chunk.to_dict('records'))
                
                # Process the dataset in streaming fashion with callback
                if streaming_store is not None:
                    streaming_store.retrieve_dataset_streaming(
                        dataset_name, process_chunk, start_str, end_str
                    )
                
                # Store the collected data
                data[variable] = variable_data
                
        elif use_optimized:
            # Batch retrieve using vectorized operations if optimized store is available
            # Load all variables in parallel with vectorized filtering
            dataset_futures = {}
            
            for variable in batch.variables:
                dataset_name = f"historical_{variable}"
                # Submit dataset retrieval task
                if optimized_store is not None:
                    dataset_futures[variable] = self.executor.submit(
                        optimized_store.retrieve_dataset_optimized,
                        dataset_name, start_str, end_str
                    )
            
            # Collect results from all futures
            for variable, future in dataset_futures.items():
                try:
                    df, _ = future.result()
                    if df is not None and not df.empty:
                        # Convert DataFrame to list of dictionaries for compatibility
                        data[variable] = df.to_dict('records')
                    else:
                        data[variable] = []
                except Exception as e:
                    self.logger.error(f"Error loading data for variable {variable}: {e}")
                    data[variable] = []
        else:
            # Fallback to original implementation
            for variable in batch.variables:
                dataset_name = f"historical_{variable}"
                items, metadata = self.data_store.retrieve_dataset(dataset_name)
                
                # Filter items by timestamp
                if items:
                    filtered_items = [
                        item for item in items
                        if start_str <= item.get("timestamp", "") <= end_str
                    ]
                    data[variable] = filtered_items
                else:
                    data[variable] = []
        
        return data
        
    def _get_upcoming_batch_variables(self, current_batch: TrainingBatch) -> List[str]:
        """
        Get variables from upcoming batches for prefetching.
        
        Args:
            current_batch: The current training batch
            
        Returns:
            List of variable names from upcoming batches
        """
        # Find the current batch index
        current_index = -1
        for i, batch in enumerate(self.batches):
            if batch.batch_id == current_batch.batch_id:
                current_index = i
                break
                
        if current_index == -1 or current_index >= len(self.batches) - 1:
            return []
            
        # Get variables from the next batch
        next_batch = self.batches[current_index + 1]
        return next_batch.variables
    
    def _run_retrodiction_on_batch(self, batch: TrainingBatch, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run retrodiction training on a batch of data.
        
        Args:
            batch: The training batch
            data: Loaded data for the batch
            
        Returns:
            Dictionary containing training results
        """
        # This is where the actual retrodiction logic would go
        # For demonstration, we'll create a simple placeholder
        # In a real implementation, this would use the actual simulation engine
        
        # Import here to avoid import cycles
        from simulation_engine.simulator_core import simulate_forward
        
        results = {
            "metrics": {},
            "rules_generated": [],
            "trust_updates": {}
        }
        
        # Apply optimized trust updates in batch using the trust buffer
        trust_updates = []
        for variable in batch.variables:
            # In a real implementation, this would be based on actual performance
            # For demonstration, we'll use random success rates
            import random
            success_rate = 0.7 + random.random() * 0.3  # 70-100% success rate
            success_count = int(100 * success_rate)
            failure_count = 100 - success_count
            
            # Add batch updates rather than individual updates
            for _ in range(success_count):
                trust_updates.append((variable, True, 1.0))
            for _ in range(failure_count):
                trust_updates.append((variable, False, 1.0))
            
            results["trust_updates"][variable] = {
                "success_rate": success_rate,
                "updates": success_count + failure_count
            }
        
        # Use the trust buffer to efficiently manage batch updates
        # The buffer will aggregate and optimize the updates before sending to the trust tracker
        self.trust_buffer.add_updates_batch(trust_updates)
        
        # Calculate metrics
        total_data_points = sum(len(var_data) for var_data in data.values())
        results["metrics"] = {
            "total_data_points": total_data_points,
            "variables_processed": len(batch.variables),
            "time_period_days": (batch.end_time - batch.start_time).days,
            "avg_success_rate": sum(update["success_rate"] for update in results["trust_updates"].values()) / len(batch.variables) if batch.variables else 0
        }
        
        return results
    
    def _store_batch_metrics(self, batch: TrainingBatch, results: Dict[str, Any]) -> None:
        """
        Store metrics for a training batch.
        
        Args:
            batch: The training batch
            results: Results from batch processing
        """
        # Store metrics using the async metrics collector
        # This prevents blocking the training process during metrics I/O
        self.async_metrics.submit_metric({
            "metric_type": "retrodiction_batch",
            "batch_id": batch.batch_id,
            "start_time": batch.start_time.isoformat(),
            "end_time": batch.end_time.isoformat(),
            "variables": len(batch.variables),
            "metrics": results.get("metrics", {}),
            "timestamp": datetime.now().isoformat()
        })
    
    def _on_batch_complete(self, result: Tuple[str, Dict[str, Any]]) -> None:
        """
        Callback when a batch completes successfully.
        
        Args:
            result: Tuple of (batch_id, results_dict)
        """
        batch_id, data = result
        
        # Update batch status
        for batch in self.batches:
            if batch.batch_id == batch_id:
                batch.processed = True
                batch.processing_time = data.get("processing_time", 0.0)
                batch.results = data
                break
        
        # Update metrics
        self.performance_metrics["completed_batches"] += 1
        
        # Report progress
        self._report_progress(self.performance_metrics["completed_batches"] + self.performance_metrics["failed_batches"])
    
    def _on_batch_error(self, error) -> None:
        """
        Callback when a batch fails with an error.
        
        Args:
            error: Exception object
        """
        self.logger.error(f"Batch processing error: {str(error)}")
        self.errors.append(str(error))
        
        # Update metrics
        self.performance_metrics["failed_batches"] += 1
        
        # Report progress
        self._report_progress(self.performance_metrics["completed_batches"] + self.performance_metrics["failed_batches"])
    
    def _report_progress(self, completed_batches: int) -> None:
        """
        Report training progress.
        
        Args:
            completed_batches: Number of completed batches
        """
        if not self.batches:
            return
            
        total_batches = len(self.batches)
        progress = completed_batches / total_batches
        
        # Calculate estimated time remaining
        if self.training_start_time and completed_batches > 0:
            elapsed = (datetime.now() - self.training_start_time).total_seconds()
            total_estimated = elapsed / progress if progress > 0 else 0
            remaining = total_estimated - elapsed
        else:
            elapsed = 0
            remaining = 0
        
        progress_data = {
            "progress": progress,
            "completed_batches": completed_batches,
            "total_batches": total_batches,
            "elapsed_seconds": elapsed,
            "remaining_seconds": remaining,
            "completed_percentage": f"{progress * 100:.1f}%",
            "success_rate": f"{self.performance_metrics['completed_batches'] / max(1, completed_batches) * 100:.1f}%",
            "errors": len(self.errors)
        }
        
        # Call the progress callback if provided
        if self.progress_callback:
            try:
                self.progress_callback(progress_data)
            except Exception as e:
                self.logger.error(f"Error in progress callback: {str(e)}")
        
        # Log progress
        self.logger.info(
            f"Training progress: {progress_data['completed_percentage']} "
            f"({completed_batches}/{total_batches} batches, "
            f"elapsed: {elapsed:.1f}s, "
            f"remaining: {remaining:.1f}s)"
        )
    
    def stop_training(self) -> None:
        """Stop training and clean up Dask cluster resources."""
        if not self.is_training:
            return
            
        self.logger.info("Stopping training...")
        self.is_training = False
        
        # Cancel any pending Dask futures
        if hasattr(self, 'dask_futures') and self.dask_futures:
            self.logger.info("Cancelling pending Dask tasks...")
            for future in self.dask_futures:
                if not future.done():
                    try:
                        future.cancel()
                    except Exception as e:
                        self.logger.warning(f"Error cancelling Dask future: {e}")
        
        # Flush any pending trust updates and metrics
        self.logger.info("Flushing trust update buffer...")
        updates_flushed = self.trust_buffer.flush()
        self.logger.info(f"Flushed {updates_flushed} pending trust updates")
        
        self.training_end_time = datetime.now()
    
    def get_results_summary(self) -> Dict[str, Any]:
        """
        Get a summary of training results including Dask cluster information.
        
        Returns:
            Dictionary with training results summary and Dask cluster metrics
        """
        # Calculate success rate for completed batches
        completed = self.performance_metrics["completed_batches"]
        failed = self.performance_metrics["failed_batches"]
        total = completed + failed
        success_rate = completed / total if total > 0 else 0
        
        # Get trust updates across all variables
        all_variables = set()
        for batch in self.batches:
            all_variables.update(batch.variables)
        
        # Ensure any pending trust updates are flushed before getting scores
        self.trust_buffer.flush()
        
        trust_scores = {}
        if all_variables:
            # Get trust in batch rather than individual calls
            trust_scores = optimized_bayesian_trust_tracker.get_trust_batch(list(all_variables))
        
        # Calculate training duration
        if self.training_start_time and self.training_end_time:
            duration = (self.training_end_time - self.training_start_time).total_seconds()
        else:
            duration = 0
            
        # Summary report
        summary = {
            "batches": {
                "total": len(self.batches),
                "completed": completed,
                "failed": failed,
                "success_rate": success_rate
            },
            "variables": {
                "total": len(all_variables),
                "trust_scores": trust_scores
            },
            "performance": {
                "duration_seconds": duration,
                "speedup_factor": self.performance_metrics["speedup_factor"],
                "estimated_sequential_time": self.performance_metrics["estimated_sequential_time"]
            },
            "dask_cluster": hasattr(self, 'dask_cluster_info') and self.dask_cluster_info or {
                "status": "Not used or information not available"
            },
            "errors": self.errors[:10]  # Include only first 10 errors
        }
        
        return summary
    
    def save_results_to_file(self, filepath: str) -> None:
        """
        Save training results to a JSON file.
        
        Args:
            filepath: Path to save the results
        """
        # Make sure all metrics are processed before saving results
        self.trust_buffer.flush()
        
        # Get performance metrics from our optimized components
        trust_buffer_stats = self.trust_buffer.get_stats()
        metrics_stats = self.async_metrics.get_stats()
        
        # Get summary and add optimization stats
        results = self.get_results_summary()
        results["optimization_metrics"] = {
            "trust_buffer": trust_buffer_stats,
            "async_metrics": metrics_stats
        }
        
        # Convert any non-serializable objects
        def json_serializable(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        with open(filepath, 'w') as f:
            json.dump(results, f, default=json_serializable, indent=2)
        
        self.logger.info(f"Training results saved to {filepath}")


def run_parallel_retrodiction_training(variables: List[str],
                                      start_time: datetime,
                                      end_time: datetime,
                                      max_workers: Optional[int] = None,
                                      batch_size_days: int = 30,
                                      output_file: Optional[str] = None,
                                      dask_scheduler_port: Optional[int] = None,
                                      dask_dashboard_port: Optional[int] = None,
                                      dask_threads_per_worker: int = 1) -> Dict[str, Any]:
    """
    Run parallel retrodiction training for a set of variables over a time period
    using Dask for distributed computing.
    
    Args:
        variables: List of variables to train on
        start_time: Start of the training period
        end_time: End of the training period
        max_workers: Maximum number of worker processes
        batch_size_days: Size of each batch in days
        output_file: Optional path to save results
        dask_scheduler_port: Optional port for Dask scheduler (default: auto-assign)
        dask_dashboard_port: Optional port for Dask dashboard (default: auto-assign)
        dask_threads_per_worker: Number of threads per Dask worker (default: 1)
        
    Returns:
        Dictionary with training results summary
    """
    # Initialize the parallel training coordinator with Dask configuration
    coordinator = ParallelTrainingCoordinator(
        max_workers=max_workers,
        dask_scheduler_port=dask_scheduler_port,
        dask_dashboard_port=dask_dashboard_port,
        dask_threads_per_worker=dask_threads_per_worker
    )
    
    # Prepare training batches
    coordinator.prepare_training_batches(
        variables=variables,
        start_time=start_time,
        end_time=end_time,
        batch_size_days=batch_size_days,
        preload_data=True
    )
    
    # Define a simple progress callback
    def progress_callback(progress_data):
        print(f"Training progress: {progress_data['completed_percentage']} "
              f"({progress_data['completed_batches']}/{progress_data['total_batches']} batches)")
    
    # Start training
    coordinator.start_training(progress_callback=progress_callback)
    
    # Get results
    results = coordinator.get_results_summary()
    
    # Save results if output file is provided
    if output_file:
        coordinator.save_results_to_file(output_file)
    
    return results


if __name__ == "__main__":
    # Example usage
    variables = ["spx_close", "us_10y_yield", "wb_gdp_growth_annual", "wb_unemployment_total"]
    start_time = datetime(2020, 1, 1)
    end_time = datetime(2021, 1, 1)
    
    logging.basicConfig(level=logging.INFO)
    
    results = run_parallel_retrodiction_training(
        variables=variables,
        start_time=start_time,
        end_time=end_time,
        max_workers=None,
        batch_size_days=30,
        output_file="retrodiction_training_results.json"
    )
    
    print("Training completed:")
    print(f"Speedup factor: {results['performance']['speedup_factor']:.2f}x")
    print(f"Success rate: {results['batches']['success_rate'] * 100:.2f}%")