"""
Data Module for Recursive Training

This module provides components for data ingestion, storage, and feature processing
for the recursive training system, with support for the hybrid rules approach.
"""

from recursive_training.data.data_store import RecursiveDataStore
from recursive_training.data.optimized_data_store import OptimizedDataStore
from recursive_training.data.streaming_data_store import StreamingDataStore
from recursive_training.data.s3_data_store import S3DataStore, BOTO3_AVAILABLE

__all__ = [
    "RecursiveDataStore",
    "OptimizedDataStore",
    "StreamingDataStore",
    "S3DataStore",
    "BOTO3_AVAILABLE",
]
