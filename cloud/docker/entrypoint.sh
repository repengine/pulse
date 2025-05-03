#!/bin/bash
set -e

# Print container information
echo "Pulse Retrodiction Training Container"
echo "--------------------------------------"
echo "Container started at: $(date)"
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"

# Function to check for S3 connectivity if using S3
check_s3_connectivity() {
    if command -v aws >/dev/null 2>&1; then
        echo "Checking S3 connectivity..."
        if aws s3 ls s3://${S3_DATA_BUCKET} >/dev/null 2>&1; then
            echo "✅ S3 data bucket '${S3_DATA_BUCKET}' is accessible"
        else
            echo "⚠️ Warning: Cannot access S3 data bucket '${S3_DATA_BUCKET}'"
            echo "Please check your AWS credentials and bucket configuration"
        fi
    fi
}

# Function to initialize Dask if running in distributed mode
initialize_dask() {
    if [[ "${USE_DASK}" == "true" ]]; then
        echo "Initializing Dask..."
        # Start Dask scheduler in the background
        dask-scheduler &
        sleep 2
        # Start Dask workers
        dask-worker --nprocs 1 --nthreads "${DASK_THREADS:-2}" --memory-limit "${DASK_MEMORY_LIMIT:-4GB}" 127.0.0.1:8786 &
        echo "✅ Dask initialized with dashboard at ${DASK_DISTRIBUTED__DASHBOARD__LINK}"
    fi
}

# Set up AWS configuration if credentials are provided
if [[ -n "${AWS_ACCESS_KEY_ID}" && -n "${AWS_SECRET_ACCESS_KEY}" ]]; then
    echo "Configuring AWS credentials..."
    mkdir -p ~/.aws
    cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF
    if [[ -n "${AWS_REGION}" ]]; then
        cat > ~/.aws/config << EOF
[default]
region = ${AWS_REGION}
EOF
    fi
    check_s3_connectivity
fi

# Initialize Dask if enabled
initialize_dask

# Handle custom run mode
if [[ "${RUN_MODE}" == "training" ]]; then
    echo "Running in training mode..."
    exec python -m recursive_training.run_training "$@"
elif [[ "${RUN_MODE}" == "batch" ]]; then
    echo "Running in batch mode..."
    exec python -m recursive_training.batch_processor "$@"
elif [[ "${RUN_MODE}" == "interactive" ]]; then
    echo "Running in interactive mode..."
    exec /bin/bash
else
    # Default: run the command provided to the container
    echo "Running custom command: $@"
    exec "$@"
fi