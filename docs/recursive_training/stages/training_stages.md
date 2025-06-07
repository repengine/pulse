# Module: recursive_training/stages/training_stages.py

## Purpose

The `training_stages.py` module implements a modular and extensible training pipeline for the Pulse Recursive Learning system. It utilizes the Command pattern to define individual, self-contained stages for various parts of the training process, such as environment setup, data store configuration, Dask initialization, actual training execution, and results uploading.

This architectural approach promotes separation of concerns, making the pipeline easier to understand, maintain, test, and extend with new stages or modified existing ones. The `TrainingPipeline` class orchestrates the execution of these stages, including error handling and rollback capabilities for stages that support it.

## Key Components

The module is structured around an abstract base class for stages and several concrete stage implementations, all managed by a pipeline orchestrator.

*   **`TrainingStage` (Abstract Base Class):**
    *   **Purpose:** Defines the interface for all training pipeline stages. It mandates the `execute` method for performing the stage's action and `can_rollback` / `rollback` methods for cleanup or undoing operations.
    *   **Key Abstract Methods:**
        *   `execute(config: TrainingConfig, context: Dict[str, Any]) -> Dict[str, Any]`: Performs the primary logic of the stage. It takes the global `TrainingConfig` and a shared `context` dictionary (for passing data between stages) and returns the updated context.
        *   `can_rollback() -> bool`: Returns `True` if the stage supports a rollback operation, `False` otherwise.
    *   **Key Concrete Method:**
        *   `rollback(config: TrainingConfig, context: Dict[str, Any])`: Implements the rollback logic if supported. The base implementation logs a warning if called on a stage that claims to support rollback but hasn't implemented it.

*   **Concrete Stage Implementations (Subclasses of `TrainingStage`):**
    *   **`EnvironmentSetupStage`:**
        *   **Purpose:** Sets up the initial training environment.
        *   **Actions:** Adds the project root to `sys.path`, configures logging based on `TrainingConfig`, creates the log directory, and identifies if running in an AWS Batch environment, storing relevant information in the context.
        *   **Rollback:** Not supported.
    *   **`DataStoreSetupStage`:**
        *   **Purpose:** Configures and initializes data store connections, primarily for S3 if specified in the `TrainingConfig`.
        *   **Actions:** If S3 configuration is present, attempts to import and instantiate `S3DataStore` (from [`recursive_training.data.s3_data_store`](../data/s3_data_store.py:0)) and stores the instance and its configuration in the context.
        *   **Rollback:** Supported (closes the data store connection if applicable).
    *   **`DaskSetupStage`:**
        *   **Purpose:** Initializes a Dask client for distributed computing if `use_dask` is enabled in `TrainingConfig`.
        *   **Actions:** Attempts to connect to the Dask scheduler specified in the configuration and stores the Dask client instance in the context.
        *   **Rollback:** Supported (closes the Dask client connection).
    *   **`TrainingExecutionStage`:**
        *   **Purpose:** Executes the main parallel retrodiction training process.
        *   **Actions:** Determines the training date range, configures output file paths (including AWS Batch specific paths), and calls `run_parallel_retrodiction_training` (from [`recursive_training.parallel_trainer`](../parallel_trainer.py:0)) with the appropriate parameters from `TrainingConfig`. Stores results and success status in the context.
        *   **Rollback:** Not supported.
    *   **`ResultsUploadStage`:**
        *   **Purpose:** Uploads the training results (typically a JSON file) to S3 if configured and if the training was successful.
        *   **Actions:** Checks if S3 upload is necessary based on `TrainingConfig` and environment (e.g., AWS Batch). If so, uses `boto3` to upload the output file specified in the context to the S3 bucket and path derived from `TrainingConfig`.
        *   **Rollback:** Not meaningfully supported in terms of deleting an uploaded file automatically by this stage, though it logs that manual cleanup might be needed.

*   **`TrainingPipeline` Class:**
    *   **Purpose:** Orchestrates the sequential execution of a list of `TrainingStage` instances. It manages the shared `context` dictionary passed between stages and handles error recovery by attempting to roll back executed stages if a failure occurs.
    *   **Key Attributes:**
        *   `stages` (List[TrainingStage]): A list of stage instances to be executed in order.
        *   `executed_stages` (List[TrainingStage]): Keeps track of stages that have successfully executed, for rollback purposes.
        *   `context` (Dict[str, Any]): A dictionary shared across all stages to pass data and state.
    *   **Key Methods:**
        *   `__init__()`: Initializes the pipeline with a default sequence of stages.
        *   `execute(config: TrainingConfig) -> Dict[str, Any]`: Iterates through the `stages`, calling `execute()` on each. If any stage fails, it calls `_rollback_stages()` and re-raises the exception. Finally, it calls `_cleanup_stages()`.
        *   `_rollback_stages(config: TrainingConfig)`: Called on failure. Iterates through `executed_stages` in reverse order and calls `rollback()` on each stage that supports it.
        *   `_cleanup_stages(config: TrainingConfig)`: Called in a `finally` block after pipeline execution (success or failure) to ensure resources are cleaned up by calling `rollback()` on stages that support it (effectively acting as a cleanup mechanism).

## Workflow

1.  **Instantiation:** An instance of `TrainingPipeline` is created. By default, it's initialized with the standard sequence: `EnvironmentSetupStage`, `DataStoreSetupStage`, `DaskSetupStage`, `TrainingExecutionStage`, and `ResultsUploadStage`.
2.  **Execution Start:** The `execute(config)` method of the pipeline is called, passing in a `TrainingConfig` object.
3.  **Sequential Stage Execution:** The pipeline iterates through its list of stages:
    *   For each stage, its `execute(config, context)` method is called.
    *   The `context` dictionary is passed from one stage to the next, allowing them to share information (e.g., Dask client instance, data store configuration, output file paths).
    *   Successfully executed stages are added to the `executed_stages` list.
4.  **Error Handling & Rollback:**
    *   If any stage's `execute()` method raises an exception:
        *   The error is logged.
        *   The `_rollback_stages()` method is called, which iterates through the `executed_stages` in reverse order and calls the `rollback()` method on each stage that `can_rollback()`. This attempts to undo changes made by previous successful stages.
        *   The original exception is re-raised, halting the pipeline.
5.  **Cleanup:** Regardless of success or failure, the `_cleanup_stages()` method is called in a `finally` block. This also iterates through executed stages and calls their `rollback()` method, serving as a general resource cleanup mechanism (e.g., closing client connections).
6.  **Return Value:** If all stages complete successfully, the `execute()` method returns the final `context` dictionary containing all accumulated data and results from the pipeline run.

## Usage

The `TrainingPipeline` is typically used by an orchestrating script like [`recursive_training.run_training`](../run_training.md:0).

**Conceptual Usage (from an orchestrator):**

```python
from recursive_training.config.training_config import create_training_config
from recursive_training.stages.training_stages import TrainingPipeline
import logging

# Configure logging for the example
logging.basicConfig(level=logging.INFO)

# 1. Create a training configuration
try:
    config = create_training_config(
        variables=["var1", "var2"],
        start_date="2023-01-01",
        end_date="2023-01-31", # Short period for example
        batch_size_days=10,
        batch_limit=1, # Limit batches for example
        # Assuming S3 & Dask are not fully set up for this conceptual example
        s3_data_bucket=None, 
        use_dask=False
    )
except ValueError as e:
    print(f"Configuration error: {e}")
    exit()

# 2. Instantiate the pipeline
pipeline = TrainingPipeline()

# 3. Execute the pipeline
try:
    results_context = pipeline.execute(config)
    if results_context.get("training_success"):
        print("Training pipeline completed successfully.")
        print(f"Results: {results_context.get('training_results')}")
        if results_context.get("s3_upload_success"):
            print(f"Results uploaded to: {results_context.get('s3_upload_path')}")
    else:
        print(f"Training pipeline failed: {results_context.get('training_error')}")
except Exception as e:
    print(f"An unexpected error occurred during pipeline execution: {e}")

```

## Relationship to Other Modules

*   **[`recursive_training.config.training_config.TrainingConfig`](../config/training_config.py):** An instance of `TrainingConfig` is passed to the pipeline's `execute` method and then to each stage, providing all necessary configuration parameters.
*   **[`recursive_training.parallel_trainer`](../parallel_trainer.py):** The `TrainingExecutionStage` specifically calls `run_parallel_retrodiction_training` from this module to perform the core parallel training logic.
*   **[`recursive_training.data.s3_data_store`](../data/s3_data_store.py) (optional):** If S3 is configured, `DataStoreSetupStage` attempts to import and use `S3DataStore`.
*   **`boto3`:** Used by `ResultsUploadStage` for interacting with AWS S3 if results are to be uploaded.
*   **`dask.distributed`:** Used by `DaskSetupStage` to initialize a Dask client if Dask is enabled.
*   **Python Standard Libraries:**
    *   `abc` (Abstract Base Classes): For defining `TrainingStage`.
    *   `logging`: For logging within stages and the pipeline.
    *   `os`, `sys`, `pathlib`: For file system and path operations, particularly in `EnvironmentSetupStage`.
    *   `datetime`: For handling dates in `TrainingExecutionStage`.