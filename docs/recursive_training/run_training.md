# Module: recursive_training/run_training.py

## Purpose

The `run_training.py` script is the primary entry point for orchestrating the Recursive Learning training process within the Pulse system. It is responsible for initializing the training environment, managing data pipelines, coordinating the execution of training batches (often in parallel via modules like `parallel_trainer.py`), and handling the overall lifecycle of a recursive training run.

This script is crucial for the system's ability to learn and adapt its internal models and rules based on new data and performance feedback.

## Current Operational Status

**Operational and Fixed.**

Previously, this script suffered from a critical `NameError` originating from a missing `TrainingBatch` class definition in its dependency, [`recursive_training/parallel_trainer.py`](recursive_training/parallel_trainer.py:0). This error caused the script to hang indefinitely, consume excessive RAM, and fail to complete training cycles.

**Recent Fix Summary:**
*   **Issue:** `NameError` due to missing `TrainingBatch` class in [`recursive_training/parallel_trainer.py`](recursive_training/parallel_trainer.py:0).
*   **Fix:** The `TrainingBatch` class was defined and added to [`recursive_training/parallel_trainer.py`](recursive_training/parallel_trainer.py:0).
*   **Outcome:** The script is now fully operational. It successfully processes training batches, memory usage is reasonable, and the end-to-end recursive learning process can be initiated and observed.

## Basic Usage Notes

The script is typically invoked from the command line. Specific arguments and configurations may be required to define:
*   Input data sources and parameters.
*   Training configuration (e.g., number of epochs, batch size).
*   Resource allocation for parallel processing.
*   Output locations for models, logs, and metrics.

Refer to the script's internal argument parsing (e.g., using `argparse`) or accompanying configuration files for detailed usage instructions.

**Example (Conceptual):**
```bash
python recursive_training/run_training.py --config path/to/training_config.yaml --input-data s3://my-bucket/training-data/ --output-dir /mnt/pulse_training_output/run_xyz
```

Ensure all dependencies, including those for parallel execution (like Dask, if used by `parallel_trainer.py`) and data access, are correctly installed and configured in the environment.