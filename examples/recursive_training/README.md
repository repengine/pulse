# Recursive Training Examples

This directory contains practical examples demonstrating how to use the Pulse recursive training system. These examples show different approaches to configuring and running training processes.

## Examples

### 1. Basic Training Example (`basic_training_example.py`)

A comprehensive example that demonstrates:

- **Configuration Creation**: How to create and validate training configurations
- **Pipeline Execution**: Using the `TrainingPipeline` class for complete workflow management
- **Direct Coordination**: Using `ParallelTrainingCoordinator` for fine-grained control
- **Convenience Functions**: Using `run_parallel_retrodiction_training()` for simple execution
- **Validation**: Testing configuration validation with valid and invalid inputs

**Usage:**
```bash
# Run from project root
python examples/recursive_training/basic_training_example.py
```

**Key Features Demonstrated:**
- Creating training configurations with different parameters
- Running training with multiple approaches
- Progress monitoring and result interpretation
- Error handling and validation
- Output file generation

## Quick Start

### Minimal Configuration Example

```python
from recursive_training.config.training_config import create_training_config
from recursive_training.stages.training_stages import TrainingPipeline

# Create a basic configuration
config = create_training_config(
    variables=["spx_close", "us_10y_yield"],
    batch_size_days=30,
    start_date="2023-01-01",
    end_date="2023-12-31",
    max_workers=4
)

# Run training using the pipeline
pipeline = TrainingPipeline()
results = pipeline.execute(config)

# Check results
if results.get("training_success"):
    print("Training completed successfully!")
else:
    print(f"Training failed: {results.get('training_error')}")
```

### Using the Parallel Coordinator

```python
from datetime import datetime
from recursive_training.parallel_trainer import ParallelTrainingCoordinator

# Create coordinator
coordinator = ParallelTrainingCoordinator(max_workers=4)

# Prepare batches
batches = coordinator.prepare_training_batches(
    variables=["spx_close", "us_10y_yield"],
    start_time=datetime(2023, 1, 1),
    end_time=datetime(2023, 12, 31),
    batch_size_days=30
)

# Start training with progress callback
def progress_callback(data):
    print(f"Progress: {data['completed_percentage']}")

coordinator.start_training(progress_callback=progress_callback)

# Get results
results = coordinator.get_results_summary()
print(f"Success rate: {results['batches']['success_rate']:.2%}")
```

### Using the Convenience Function

```python
from datetime import datetime
from recursive_training.parallel_trainer import run_parallel_retrodiction_training

# Run training with minimal setup
results = run_parallel_retrodiction_training(
    variables=["spx_close", "us_10y_yield"],
    start_time=datetime(2023, 1, 1),
    end_time=datetime(2023, 12, 31),
    max_workers=4,
    batch_size_days=30,
    output_file="training_results.json"
)

print(f"Training completed: {results['batches']['success_rate']:.2%} success rate")
```

## Configuration Options

### Basic Parameters

- `variables`: List of variable names to train on (e.g., `["spx_close", "us_10y_yield"]`)
- `batch_size_days`: Size of each training batch in days (default: 30)
- `start_date`: Start date for training period (format: "YYYY-MM-DD")
- `end_date`: End date for training period (optional, defaults to today)
- `max_workers`: Maximum number of parallel workers (optional, defaults to CPU count - 1)

### Advanced Parameters

- `batch_limit`: Limit number of batches for testing/debugging
- `use_dask`: Enable Dask distributed computing
- `dask_scheduler_address`: Address of Dask scheduler
- `dask_dashboard_port`: Port for Dask dashboard
- `log_level`: Logging level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
- `log_dir`: Directory for log files

### AWS/S3 Parameters

- `aws_region`: AWS region for S3 operations
- `s3_data_bucket`: S3 bucket containing training data
- `s3_results_bucket`: S3 bucket for saving results
- `s3_data_prefix`: Prefix for data objects in S3
- `s3_results_prefix`: Prefix for results objects in S3

## Output and Results

### Training Results Structure

```python
{
    "batches": {
        "total": 12,
        "completed": 11,
        "failed": 1,
        "success_rate": 0.92
    },
    "variables": {
        "total": 2,
        "trust_scores": {
            "spx_close": 0.85,
            "us_10y_yield": 0.78
        }
    },
    "performance": {
        "duration_seconds": 45.2,
        "speedup_factor": 3.2,
        "estimated_sequential_time": 144.6
    }
}
```

### Log Files

Training logs are saved to the specified log directory (default: "logs/"):
- `retrodiction_training.log`: Main training log with progress and results
- Console output: Real-time progress and status updates

### Output Files

- JSON results file: Complete training results and metrics
- S3 uploads: Automatic upload to S3 if configured
- Dask dashboard: Real-time monitoring during training (if Dask is enabled)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root directory
2. **Memory Issues**: Reduce `max_workers` or `batch_size_days` for large datasets
3. **Timeout Issues**: Increase batch limits or reduce date ranges for testing
4. **S3 Errors**: Check AWS credentials and bucket permissions

### Debug Mode

Enable debug logging for detailed information:

```python
config = TrainingConfig(
    log_level="DEBUG",
    batch_limit=2  # Limit batches for debugging
)
```

### Performance Tuning

- **CPU-bound**: Increase `max_workers` up to CPU core count
- **Memory-bound**: Decrease `batch_size_days` or `max_workers`
- **I/O-bound**: Enable Dask for distributed processing
- **Network-bound**: Use S3 data stores for cloud deployments

## Next Steps

1. **Customize Variables**: Modify the `variables` list to match your data
2. **Adjust Parameters**: Tune batch sizes and worker counts for your system
3. **Add Monitoring**: Implement custom progress callbacks for monitoring
4. **Scale Up**: Use Dask and S3 for large-scale distributed training
5. **Integrate**: Incorporate training into your larger ML pipeline

For more detailed information, see the module documentation in the source files.