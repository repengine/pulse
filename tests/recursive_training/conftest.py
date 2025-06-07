"""
Pytest configuration and fixtures for recursive_training tests.

This module provides centralized fixture management and cleanup for the
recursive_training test suite, particularly for singleton instances that
can accumulate memory across test runs.
"""

import pytest
import gc
from typing import List, Any


@pytest.fixture(autouse=True, scope="function")
def cleanup_singletons():
    """
    Automatically clean up singleton instances after each test function.
    
    This fixture runs automatically for every test function and ensures
    that singleton instances are properly reset to prevent memory
    accumulation across the test suite.
    """
    # Setup phase - nothing needed
    yield
    
    # Teardown phase - clean up all known singletons
    singleton_classes = []
    
    try:
        # Import and reset all singleton classes
        from recursive_training.trust_update_buffer import TrustUpdateBuffer
        singleton_classes.append(TrustUpdateBuffer)
    except ImportError:
        pass
    
    try:
        from recursive_training.async_metrics_collector import AsyncMetricsCollector
        singleton_classes.append(AsyncMetricsCollector)
    except ImportError:
        pass
    
    try:
        from recursive_training.data.data_store import RecursiveDataStore
        singleton_classes.append(RecursiveDataStore)
    except ImportError:
        pass
    
    try:
        from recursive_training.metrics.metrics_store import MetricsStore
        singleton_classes.append(MetricsStore)
    except ImportError:
        pass
    
    try:
        from recursive_training.data.feature_processor import RecursiveFeatureProcessor
        singleton_classes.append(RecursiveFeatureProcessor)
    except ImportError:
        pass
    
    try:
        from recursive_training.rules.rule_generator import RecursiveRuleGenerator
        singleton_classes.append(RecursiveRuleGenerator)
    except ImportError:
        pass
    
    try:
        from recursive_training.rules.rule_evaluator import RecursiveRuleEvaluator
        singleton_classes.append(RecursiveRuleEvaluator)
    except ImportError:
        pass
    
    try:
        from recursive_training.rules.hybrid_adapter import HybridRuleAdapter
        singleton_classes.append(HybridRuleAdapter)
    except ImportError:
        pass
    
    try:
        from recursive_training.rules.rule_repository import RuleRepository
        singleton_classes.append(RuleRepository)
    except ImportError:
        pass
    
    try:
        from recursive_training.data.streaming_data_store import StreamingDataStore
        singleton_classes.append(StreamingDataStore)
    except ImportError:
        pass
    
    # Reset all singleton instances
    for singleton_class in singleton_classes:
        if hasattr(singleton_class, '_instance'):
            singleton_class._instance = None
    
    # Also reset any module-level singleton variables
    try:
        import recursive_training.data.feature_processor as rfp_module
        if hasattr(rfp_module, '_instance'):
            rfp_module._instance = None
    except ImportError:
        pass
    
    # Force garbage collection to free memory
    gc.collect()


@pytest.fixture(autouse=True, scope="function")
def cleanup_dask_clients():
    """
    Automatically clean up any Dask clients created during tests.
    
    This fixture ensures that any Dask clients (real or mock) are properly
    closed to prevent resource leaks.
    """
    # Setup phase - nothing needed
    yield
    
    # Teardown phase - clean up any Dask clients
    # This will be handled by the test context cleanup, but we ensure
    # any lingering references are cleared
    try:
        import dask.distributed
        # Close any active clients
        try:
            client = dask.distributed.get_client()
            if client:
                client.close()
        except (ValueError, RuntimeError):
            # No active client, which is fine
            pass
    except ImportError:
        # Dask not available, which is fine
        pass


@pytest.fixture(scope="function")
def isolated_test_environment():
    """
    Provide an isolated test environment that ensures clean state.
    
    This fixture can be explicitly requested by tests that need guaranteed
    isolation from other tests.
    """
    # Setup: ensure clean state
    yield
    # Teardown: cleanup is handled by autouse fixtures