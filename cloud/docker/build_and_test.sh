#!/bin/bash
set -e

# Script to build and test the Docker containers for Pulse retrodiction training

echo "Making entrypoint script executable..."
chmod +x $(pwd)/cloud/docker/entrypoint.sh

echo "Building Docker image..."
docker build -t pulse-retrodiction-training:latest -f cloud/docker/Dockerfile .

echo "Building AWS Batch optimized image..."
docker build -t pulse-retrodiction-batch:latest -f cloud/docker/Dockerfile.aws_batch .

echo "Running container health check..."
docker run --rm pulse-retrodiction-training:latest python -c "print('Container health check successful!')"

echo "All tests passed!"
echo "------------------------------------"
echo "Available images:"
docker images | grep pulse-retrodiction

echo "------------------------------------"
echo "To run with Docker Compose:"
echo "cd cloud/docker && docker-compose up"

echo "------------------------------------"
echo "To push to ECR (replace with your AWS account ID):"
echo "aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com"
echo "docker tag pulse-retrodiction-batch:latest YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pulse-retrodiction:latest"
echo "docker push YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pulse-retrodiction:latest"