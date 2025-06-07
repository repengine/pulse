# Module: recursive_training/run_training.py

## Purpose

The `run_training.py` script serves as the primary command-line interface (CLI) and entry point for initiating and orchestrating the Pulse Recursive Learning (specifically retrodiction) training process. Its main responsibility is to set up the training environment, manage configurations, and drive the execution of the training pipeline, which consists of various stages.

This script is crucial for the system's ability to learn and adapt its internal models and rules based on new data and performance feedback derived from historical data analysis (retrodiction).

## Key Components

The script is structured around several key functions and interacts with core configuration and pipeline components:

*   **`parse_args()`**:
    *   **Purpose:** Defines and parses command-line arguments provided when the script is executed.
    *   **Interaction:** Uses the `argparse` module to handle various settings like target variables, date ranges, batch sizes, AWS S3 bucket details, Dask configuration, output paths, and logging levels.
*   **`create_config_from_args(args: argparse.Namespace)`**:
    *   **Purpose:** Translates the parsed command-line arguments into a structured `TrainingConfig` object.
    *   **Interaction:** Instantiates [`TrainingConfig`](../config/training_config.py) (from [`recursive_training.config.training_config`](recursive_training/config/training_config.py:0)) using values from the `args` namespace. This `TrainingConfig` object is then used throughout the training process.
*   **`setup_logging(config: TrainingConfig)`**:
    *   **Purpose:** Initializes the logging system for the training run.
    *   **Interaction:** Configures Python's `logging` module based on `log_level` and `log_dir` specified in the `TrainingConfig`. It sets up handlers for both console (stdout) and file-based logging.
*   **`main()`**:
    *   **Purpose:** The main execution function that orchestrates the entire training process.
    *   **Interaction:**
        1.  Calls `parse_args()` to get command-line inputs.
        2.  Calls `create_config_from_args()` to build the `TrainingConfig`.
        3.  Calls `setup_logging()` to initialize logging.
        4.  Instantiates the `TrainingPipeline` (from [`recursive_training.stages.training_stages`](recursive_training/stages/training_stages.py:0)).
        5.  Executes the pipeline using `pipeline.execute(config)`, passing the configuration.
        6.  Logs the success or failure of the training process and any relevant output information (e.g., S3 upload paths).
        7.  Returns an exit code (0 for success, 1 for failure).

## Workflow

The typical operational workflow initiated by `run_training.py` is as follows:

1.  **Invocation:** The script is executed from the command line with necessary arguments.
2.  **Argument Parsing:** `parse_args()` processes the CLI arguments.
3.  **Configuration Setup:** `create_config_from_args()` creates a `TrainingConfig` object.
4.  **Logging Initialization:** `setup_logging()` configures the logging framework.
5.  **Pipeline Initialization:** An instance of `TrainingPipeline` is created.
6.  **Pipeline Execution:** The `execute` method of the `TrainingPipeline` is called with the `TrainingConfig`. This step involves:
    *   Data loading and preparation.
    *   Batch generation.
    *   Model training/retrodiction on each batch (potentially in parallel, managed by components like [`parallel_trainer.py`](parallel_trainer.md:0) if Dask is enabled).
    *   Metrics collection.
    *   Results aggregation and saving (locally or to S3).
7.  **Result Handling:** The `main()` function checks the results from the pipeline, logs appropriate messages, and determines the exit code.

## Current Operational Status

**Operational and Fixed.**

Previously, this script suffered from a critical `NameError` originating from a missing `TrainingBatch` class definition in its dependency, [`recursive_training/parallel_trainer.py`](parallel_trainer.md:0). This error caused the script to hang indefinitely, consume excessive RAM, and fail to complete training cycles.

**Recent Fix Summary:**
*   **Issue:** `NameError` due to missing `TrainingBatch` class in [`recursive_training/parallel_trainer.py`](parallel_trainer.md:0).
*   **Fix:** The `TrainingBatch` class was defined and added to [`recursive_training/parallel_trainer.py`](parallel_trainer.md:0).
*   **Outcome:** The script is now fully operational. It successfully processes training batches, memory usage is reasonable, and the end-to-end recursive learning process can be initiated and observed.

## Usage

The `run_training.py` script is designed to be run as a command-line tool. It accepts various arguments to customize the training process.

**Command-Line Invocation:**

```bash
python recursive_training/run_training.py [OPTIONS]
```

**Key Options (see `parse_args()` in the script for a full list):**

*   `--variables`: List of variables to use for training (e.g., `spx_close us_10y_yield`).
*   `--start-date`, `--end-date`: Define the training period.
*   `--batch-size-days`: Size of each training batch.
*   `--max-workers`: For parallel processing.
*   `--s3-data-bucket`, `--s3-results-bucket`: Specify S3 locations for data and results.
*   `--use-dask`, `--dask-scheduler-address`: Configure Dask for distributed computation.
*   `--output-file`, `--s3-output-file`: Define where to save results.
*   `--log-level`, `--log-dir`: Configure logging.

**Conceptual Example:**

```bash
python recursive_training/run_training.py \
    --variables gdp_growth inflation_rate \
    --start-date 2020-01-01 \
    --end-date 2023-12-31 \
    --batch-size-days 90 \
    --use-dask \
    --dask-scheduler-address "tcp://127.0.0.1:8786" \
    --s3-data-bucket "my-pulse-data" \
    --s3-results-bucket "my-pulse-results" \
    --s3-output-file "s3://my-pulse-results/training_run_001/results.json" \
    --log-level INFO
```

For examples of how the underlying training components might be used programmatically (which `run_training.py` orchestrates), refer to example scripts such as those in `examples/recursive_training/`. Ensure all dependencies, including those for parallel execution (like Dask, if used by `parallel_trainer.py`) and data access (e.g., `boto3` for S3), are correctly installed and configured.

## Relationship to Other Modules

`run_training.py` interacts with several other key modules within the `recursive_training` package and the broader Pulse system:

*   **[`recursive_training.config.training_config.TrainingConfig`](../config/training_config.py):** This class is instantiated by `create_config_from_args()` and holds all configuration parameters for the training run. It is passed to the `TrainingPipeline`.
*   **[`recursive_training.stages.TrainingPipeline`](../stages/training_stages.py):** This is the core orchestrator of the actual training steps (data loading, preprocessing, model execution, results saving). `run_training.py` creates an instance of `TrainingPipeline` and calls its `execute` method.
*   **[`recursive_training.parallel_trainer`](parallel_trainer.md:0):** While not directly imported by `run_training.py`, the `TrainingPipeline` (and its stages) may utilize `parallel_trainer.py` if Dask is enabled via the `--use-dask` flag. `parallel_trainer.py` would then manage the distribution of training batches across Dask workers.
*   **Standard Python Libraries:**
    *   `argparse`: For parsing command-line arguments.
    *   `logging`: For application-level logging.
    *   `os`, `sys`: For system-level operations like path manipulation.
*   **External Libraries (Indirect Dependencies via Pipeline Stages):**
    *   `boto3` (or similar AWS SDK): For S3 interactions if S3 buckets are used for data/results.
    *   `dask`, `dask.distributed`: If `--use-dask` is specified, for parallel and distributed computation.
    *   `pandas`, `numpy`: Likely used extensively within the `TrainingPipeline` stages for data manipulation.