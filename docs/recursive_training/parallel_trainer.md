# Module: recursive_training/parallel_trainer.py

## Purpose

The `parallel_trainer.py` module provides a framework for distributing and managing retrodiction training workloads in parallel across multiple CPU cores or even a distributed Dask cluster. It aims to significantly improve the performance and efficiency of the training process, especially for large datasets and complex models, by leveraging parallel computation.

Its primary role is to work in conjunction with orchestrating scripts like [`run_training.py`](run_training.md:0) to break down the overall training task into smaller, manageable batches and process them concurrently.

## Key Components

The module is built around two main classes and a Dask task function:

*   **`TrainingBatch` Class:**
    *   **Purpose:** Represents a single, self-contained unit of work for training. It encapsulates the data (defined by a time period and a set of variables), metadata, and eventually, the results for one segment of the training process.
    *   **Attributes:**
        *   `batch_id` (str): Unique identifier for the batch.
        *   `start_time` (datetime): Start datetime for the training period of this batch.
        *   `end_time` (datetime): End datetime for the training period of this batch.
        *   `variables` (List[str]): List of variable names to be processed in this batch.
        *   `processed` (bool): Flag indicating if the batch has been processed.
        *   `processing_time` (float): Time taken to process the batch in seconds.
        *   `results` (Optional[Dict[str, Any]]): Dictionary holding the outcome of the batch processing.
    *   **Interaction:** Instances of `TrainingBatch` are created by the `ParallelTrainingCoordinator` and are the fundamental units distributed to Dask workers.

*   **`ParallelTrainingCoordinator` Class:**
    *   **Purpose:** The central orchestrator for the parallel training process. It manages the lifecycle of training, from batch creation to worker coordination and result aggregation.
    *   **Key Methods:**
        *   `__init__(...)`: Initializes the coordinator, setting up configurations for Dask, data stores, metrics collectors, and trust buffers.
        *   `prepare_training_batches(...)`: Divides the overall training period and variable set into a list of `TrainingBatch` objects.
        *   `start_training(...)`: Initiates the Dask cluster (if local), submits `TrainingBatch` objects to Dask workers via `_dask_process_batch_task`, monitors progress, and collects results.
        *   `_on_batch_complete(...)`, `_on_batch_error(...)`: Callbacks to handle results from completed or failed Dask tasks.
        *   `_report_progress(...)`: Provides updates on training progress.
        *   `stop_training()`: Gracefully shuts down the training process and cancels pending Dask tasks.
        *   `get_results_summary()`: Aggregates and returns a summary of the entire training run.
        *   `save_results_to_file(...)`: Saves the detailed results summary to a JSON file.
    *   **Interaction:** This class is typically instantiated and used by higher-level scripts like [`run_training.py`](run_training.md:0). It uses Dask's `LocalCluster` and `Client` for managing parallel execution.

*   **`_dask_process_batch_task(...)` Function:**
    *   **Purpose:** This is the actual function executed by each Dask worker for a given `TrainingBatch`. It's a top-level function to avoid Dask serialization issues with instance methods.
    *   **Workflow within the task:**
        1.  Re-initializes logging for the Dask worker.
        2.  Re-hydrates the `TrainingBatch` object from serialized data.
        3.  Initializes worker-specific instances of data stores (e.g., `StreamingDataStore`, `OptimizedDataStore`, or the base `RecursiveDataStore`), `AsyncMetricsCollector`, and `TrustUpdateBuffer` based on configurations passed from the coordinator.
        4.  Loads the required data for the batch's variables and time period using the appropriate data store.
        5.  **(Placeholder Retrodiction Logic):** Currently, the actual retrodiction/training logic within this task is a placeholder that generates random success rates and trust updates. In a full implementation, this is where the core model training/evaluation for the batch would occur.
        6.  Submits metrics using the `AsyncMetricsCollector`.
        7.  Adds trust updates to the `TrustUpdateBuffer`.
        8.  Returns the batch ID and a results dictionary containing processing time, metrics, and outcomes.
    *   **Interaction:** Submitted by `ParallelTrainingCoordinator` to the Dask client for execution on workers.

## Workflow

1.  **Initialization:** An instance of `ParallelTrainingCoordinator` is created, often configured by a script like [`run_training.py`](run_training.md:0).
2.  **Batch Preparation:** The `prepare_training_batches` method is called to divide the total training task into multiple `TrainingBatch` objects.
3.  **Training Start:** The `start_training` method is invoked.
    *   A Dask `LocalCluster` (or connection to an existing Dask scheduler) is established.
    *   A Dask `Client` connects to the cluster.
    *   Each `TrainingBatch` is serialized and submitted as a Dask task (`_dask_process_batch_task`) to the client.
4.  **Parallel Execution:** Dask workers pick up the submitted tasks. Each worker executes `_dask_process_batch_task` for its assigned batch:
    *   Loads data relevant to the batch.
    *   Performs the training/retrodiction logic for that batch.
    *   Collects metrics and trust updates.
5.  **Progress Monitoring & Result Collection:** The `ParallelTrainingCoordinator` monitors the status of Dask futures. As tasks complete, results are collected and processed by `_on_batch_complete` or errors by `_on_batch_error`. Progress is reported via a callback if provided.
6.  **Training Completion:** Once all batches are processed or training is stopped, `start_training` finalizes performance metrics.
7.  **Summary & Saving:** `get_results_summary` can be called to get an overview, and `save_results_to_file` to persist detailed results.

## Current Operational Status

**Operational and Fixed.**

The critical `TrainingBatch` class was added, resolving a `NameError` that previously prevented [`run_training.py`](run_training.md:0) from operating correctly. With this fix, the module can now support parallel training operations as intended.

## Usage

This module is primarily intended to be used by an orchestrating script, not directly from the command line. The `ParallelTrainingCoordinator` class is the main interface.

**Conceptual Usage (from another script):**

```python
from datetime import datetime
from recursive_training.parallel_trainer import ParallelTrainingCoordinator, run_parallel_retrodiction_training

# Option 1: Using the coordinator directly
coordinator_config = {
    "data_store_config": {"base_path": "/mnt/data/pulse_store"},
    "async_metrics_config": {"endpoint": "http://metrics-collector:9090"},
    # ... other configs
}
coordinator = ParallelTrainingCoordinator(
    config=coordinator_config,
    max_workers=4,
    dask_dashboard_port=8788
)

variables_to_train = ["var1", "var2"]
training_start_date = datetime(2022, 1, 1)
training_end_date = datetime(2022, 12, 31)

coordinator.prepare_training_batches(
    variables=variables_to_train,
    start_time=training_start_date,
    end_time=training_end_date,
    batch_size_days=30
)

def my_progress_callback(progress_data):
    print(f"Progress: {progress_data['completed_percentage']}")

coordinator.start_training(progress_callback=my_progress_callback)
results_summary = coordinator.get_results_summary()
coordinator.save_results_to_file("parallel_training_run_results.json")
print(results_summary)

# Option 2: Using the convenience function (shown in module's __main__)
# results = run_parallel_retrodiction_training(
#     variables=variables_to_train,
#     start_time=training_start_date,
#     end_time=training_end_date,
#     max_workers=2, # e.g., 2 workers
#     output_file="training_results_example.json"
# )
```

Refer to the `run_parallel_retrodiction_training` function and the `__main__` block within `parallel_trainer.py` for a practical example of how to instantiate and run the coordinator.

## Relationship to Other Modules

*   **[`recursive_training.run_training`](run_training.md:0):** This is the typical client/orchestrator that would use `ParallelTrainingCoordinator` to execute the training pipeline in parallel.
*   **`dask.distributed`:** Core dependency for creating local clusters (`LocalCluster`) and clients (`Client`) to manage and execute parallel tasks.
*   **[`recursive_training.data.data_store.RecursiveDataStore`](../data/data_store.py):** Base class for data storage.
*   **[`recursive_training.data.streaming_data_store.StreamingDataStore`](../data/streaming_data_store.py) (optional):** Specialized data store that can be used by workers if available and configured.
*   **[`recursive_training.data.optimized_data_store.OptimizedDataStore`](../data/optimized_data_store.py) (optional):** Another specialized data store.
*   **[`recursive_training.metrics.async_metrics_collector.AsyncMetricsCollector`](../metrics/async_metrics_collector.py):** Used by Dask workers to submit metrics asynchronously.
*   **[`recursive_training.metrics.metrics_store.MetricsStore`](../metrics/metrics_store.py):** Potentially used by the coordinator, though primary metric submission is from workers.
*   **[`analytics.trust_update_buffer.TrustUpdateBuffer`](../../analytics/trust_update_buffer.py):** Used by Dask workers to buffer trust updates before they are flushed to the main trust tracker.
*   **[`analytics.optimized_trust_tracker.optimized_bayesian_trust_tracker`](../../analytics/optimized_trust_tracker.py):** Used by the coordinator to fetch final trust scores for the results summary.
*   `memory_profiler`: Used to profile the memory usage of the Dask task function.
*   Standard Python Libraries: `datetime`, `time`, `logging`, `json`, `os`, `sys`.