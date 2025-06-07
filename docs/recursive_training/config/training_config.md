# Module: recursive_training/config/training_config.py

## Purpose

The `training_config.py` module provides a centralized and robust mechanism for managing all configuration parameters required by the Pulse Recursive Learning training system. It defines the `TrainingConfig` dataclass, which serves as a structured container for these settings, ensuring type safety, providing default values, allowing overrides via environment variables, and enforcing validation rules.

This module is essential for ensuring that training runs are consistently and correctly configured, whether initiated manually, via automated scripts like [`run_training.py`](../run_training.md:0), or in containerized environments like AWS Batch.

## Key Components

*   **`TrainingConfig` Dataclass:**
    *   **Purpose:** A `dataclasses.dataclass(frozen=True)` that defines the schema for all training configuration parameters. Being frozen means instances are immutable after creation, promoting stability.
    *   **Attributes (Categorized):**
        *   **Basic Training Parameters:**
            *   `variables` (List[str]): List of variable names to be used in training (e.g., `["spx_close", "us_10y_yield"]`).
            *   `batch_size_days` (int): The size of each training batch in days.
            *   `start_date` (str): The start date for the training period (format: "YYYY-MM-DD").
            *   `end_date` (Optional[str]): The end date for the training period (format: "YYYY-MM-DD"). Defaults to `None` (often interpreted as today).
            *   `max_workers` (Optional[int]): Maximum number of worker processes for parallel execution.
            *   `batch_limit` (Optional[int]): Limits the number of batches processed, useful for debugging.
        *   **AWS Configuration:**
            *   `aws_region` (str): The AWS region to use (e.g., "us-east-1").
            *   `s3_data_bucket` (Optional[str]): S3 bucket name for sourcing training data.
            *   `s3_results_bucket` (Optional[str]): S3 bucket name for storing training results.
            *   `s3_data_prefix` (str): Prefix for data objects within the `s3_data_bucket`.
            *   `s3_results_prefix` (str): Prefix for results objects within the `s3_results_bucket`.
        *   **Dask Configuration:**
            *   `use_dask` (bool): Flag to enable/disable Dask for distributed computing.
            *   `dask_scheduler_address` (str): Address of the Dask scheduler (e.g., "127.0.0.1:8786").
            *   `dask_dashboard_port` (int): Port for the Dask dashboard.
            *   `dask_threads_per_worker` (int): Number of threads per Dask worker.
        *   **Output Configuration:**
            *   `output_file` (Optional[str]): Local file path to save training results JSON.
            *   `s3_output_file` (Optional[str]): Specific S3 path (s3://bucket/key) to save training results JSON, overriding default naming.
        *   **Logging Configuration:**
            *   `log_level` (str): Logging level (e.g., "INFO", "DEBUG").
            *   `log_dir` (str): Directory to store log files.
    *   **Key Methods:**
        *   `__post_init__()`: Called after `__init__`. It applies environment variable overrides and sets any computed defaults.
        *   `_apply_environment_overrides()`: Internal method to check specific environment variables (e.g., `AWS_REGION`, `S3_DATA_BUCKET`) and update corresponding attributes if the environment variables are set.
        *   `_set_defaults()`: Internal method for setting any defaults that depend on other initial values (currently minimal).
        *   `validate()`: Performs crucial validation checks on the configuration values (e.g., ensures `variables` is not empty, `batch_size_days` is positive, date formats are correct, `start_date` is before `end_date`). Raises `ValueError` if validation fails.
        *   `to_dict()`: Converts the `TrainingConfig` instance into a Python dictionary.
        *   `get_aws_batch_output_path()`: Generates a standardized S3 output path for results when running within an AWS Batch job environment, incorporating the job ID.
        *   `get_s3_output_path()`: Determines the final S3 path for results, prioritizing `s3_output_file` if set, then checking for AWS Batch environment, and finally falling back to a locally generated timestamped name.

*   **`create_training_config(**kwargs)` Function:**
    *   **Purpose:** A factory function to create and validate a `TrainingConfig` instance.
    *   **Interaction:** It instantiates `TrainingConfig` with any provided keyword arguments (overriding defaults) and then calls the `validate()` method on the new instance.
    *   **Returns:** A validated `TrainingConfig` object.

## Configuration Handling Workflow

1.  **Instantiation:** A `TrainingConfig` object is typically created in one of two ways:
    *   Directly: `config = TrainingConfig(param1=value1, ...)`
    *   Via Factory: `config = create_training_config(param1=value1, ...)` (this includes validation).
    *   By [`run_training.py`](../run_training.md:0): The `create_config_from_args()` function in `run_training.py` populates a `TrainingConfig` instance from parsed command-line arguments.
2.  **Default Values:** Attributes are initialized with their default values as defined in the dataclass.
3.  **Environment Overrides:** During `__post_init__`, the `_apply_environment_overrides()` method checks for specific environment variables (e.g., `S3_DATA_BUCKET`, `LOG_LEVEL`) and updates the corresponding attributes if these variables are set. This allows for dynamic configuration in different environments without code changes.
4.  **Validation:** The `validate()` method is called (explicitly or via `create_training_config`) to ensure the integrity and correctness of the parameters. This helps catch configuration errors early.
5.  **Usage:** The validated `TrainingConfig` object is then passed to other components of the training system, such as the `TrainingPipeline` in [`recursive_training.stages.training_stages`](../stages/training_stages.py:0), to guide their behavior.

## Usage Examples

**Creating a basic configuration:**

```python
from recursive_training.config.training_config import TrainingConfig, create_training_config

# Option 1: Direct instantiation (validation needs to be called separately)
config1 = TrainingConfig(
    variables=["gdp", "unemployment"],
    start_date="2021-01-01",
    s3_data_bucket="my-training-data-bucket"
)
try:
    config1.validate()
    print("Config1 is valid.")
except ValueError as e:
    print(f"Config1 validation error: {e}")

# Option 2: Using the factory function (includes validation)
try:
    config2 = create_training_config(
        variables=["interest_rate"],
        batch_size_days=10,
        use_dask=True,
        log_level="DEBUG"
    )
    print("Config2 created and validated successfully.")
    print(f"Config2 Dask usage: {config2.use_dask}")
except ValueError as e:
    print(f"Config2 creation error: {e}")

# Example of environment variable override (conceptual)
# Assuming os.environ["S3_DATA_BUCKET"] = "env-override-bucket"
# config_env = TrainingConfig() # s3_data_bucket would be "env-override-bucket"
```

## Relationship to Other Modules

*   **[`recursive_training.run_training`](../run_training.md:0):** This script is a primary consumer of `TrainingConfig`. Its `create_config_from_args()` function directly instantiates `TrainingConfig` based on command-line arguments.
*   **[`recursive_training.stages.training_stages.TrainingPipeline`](../stages/training_stages.py):** The `TrainingConfig` object is passed to the `TrainingPipeline`'s `execute` method, where its parameters guide the various stages of the training process (data loading, batching, model execution, etc.).
*   **Python Standard Libraries:**
    *   `os`: Used for accessing environment variables.
    *   `dataclasses`: Provides the `@dataclass` decorator for creating the `TrainingConfig` class.
    *   `datetime`: Used for date string parsing and validation.
    *   `typing`: For type hints.
    *   `logging`: For internal logging within the module.