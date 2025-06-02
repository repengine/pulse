"""
Tests for the AsyncMetricsCollector.

These tests verify that the collector correctly processes metrics asynchronously
without blocking the main thread.
"""

import unittest
import time
import threading
from unittest.mock import patch, MagicMock

from recursive_training.metrics.async_metrics_collector import (
    AsyncMetricsCollector,
    get_async_metrics_collector,
)
from recursive_training.metrics.metrics_store import MetricsStore


class TestAsyncMetricsCollector(unittest.TestCase):
    """Tests for the AsyncMetricsCollector class."""

    def setUp(self):
        """Set up test environment."""
        # Create a fresh instance with test config for each test
        self.test_config = {
            "metrics_batch_size": 5,
            "metrics_flush_interval_sec": 0.5,
            "metrics_max_retries": 2,
            "metrics_retry_delay_sec": 0.1,
        }
        # Ensure we don't use the singleton for tests
        AsyncMetricsCollector._instance = None

        # Mock the metrics store
        self.mock_metrics_store = MagicMock(spec=MetricsStore)

        # Create and start collector with patched metrics store
        with patch(
            "recursive_training.metrics.async_metrics_collector.get_metrics_store",
            return_value=self.mock_metrics_store,
        ):
            self.collector = AsyncMetricsCollector(self.test_config)

    def tearDown(self):
        """Tear down test environment."""
        if self.collector:
            self.collector.stop(wait_for_completion=True, timeout=1.0)

    def test_submit_metric(self):
        """Test submitting a metric for processing."""
        # Submit a test metric
        metric = {"metric_type": "test", "value": 42}
        metric_id = self.collector.submit_metric(metric)

        # Verify metric ID was returned
        self.assertIsNotNone(metric_id)
        self.assertTrue(len(metric_id) > 0)

        # Wait for processing (give the background thread time to process)
        time.sleep(0.5)

        # Verify metric was stored
        self.mock_metrics_store.store_metric.assert_called()

        # The submitted metric should have timestamp and ID added
        call_args = self.mock_metrics_store.store_metric.call_args[0][0]
        self.assertEqual(call_args["metric_type"], "test")
        self.assertEqual(call_args["value"], 42)
        self.assertIn("timestamp", call_args)
        self.assertIn("id", call_args)

    def test_batch_processing(self):
        """Test that metrics are processed in batches."""
        # Submit multiple metrics
        num_metrics = self.test_config["metrics_batch_size"] * 2
        for i in range(num_metrics):
            self.collector.submit_metric({"metric_type": "test", "value": i})

        # Wait for processing
        time.sleep(1.0)

        # Verify all metrics were stored
        self.assertEqual(self.mock_metrics_store.store_metric.call_count, num_metrics)

        # Check stats
        stats = self.collector.get_stats()
        self.assertEqual(stats["metrics_submitted"], num_metrics)
        self.assertEqual(stats["metrics_processed"], num_metrics)
        self.assertGreaterEqual(stats["batches_processed"], 2)  # At least 2 batches

    def test_error_handling_and_retries(self):
        """Test error handling and retry logic."""
        # Configure mock to fail twice then succeed
        self.mock_metrics_store.store_metric.side_effect = [
            Exception("Test failure 1"),
            Exception("Test failure 2"),
            None,  # Success on third try
        ]

        # Submit a metric
        metric = {"metric_type": "test", "value": 99}
        self.collector.submit_metric(metric)

        # Wait for processing and retries
        time.sleep(1.0)

        # Verify store_metric was called the expected number of times (initial + 2
        # retries)
        self.assertEqual(self.mock_metrics_store.store_metric.call_count, 3)

        # Check stats
        stats = self.collector.get_stats()
        self.assertEqual(stats["metrics_submitted"], 1)
        self.assertEqual(stats["metrics_processed"], 1)
        self.assertEqual(stats["metrics_failed"], 0)  # It succeeded eventually

    def test_error_callback(self):
        """Test error callback mechanism."""
        # Configure mock to always fail
        self.mock_metrics_store.store_metric.side_effect = Exception(
            "Permanent failure"
        )

        # Setup error callback
        callback_called = threading.Event()
        error_message = [None]

        def error_callback(exception):
            error_message[0] = str(exception)
            callback_called.set()

        # Register callback
        self.collector.register_error_callback(error_callback)

        # Submit a metric
        metric = {"metric_type": "test", "value": 123}
        self.collector.submit_metric(metric)

        # Wait for callback to be called
        callback_result = callback_called.wait(timeout=2.0)

        # Verify callback was called with the expected error
        self.assertTrue(callback_result)
        self.assertIsNotNone(error_message[0])
        self.assertIn("Permanent failure", error_message[0])

        # Check stats
        stats = self.collector.get_stats()
        self.assertEqual(stats["metrics_failed"], 1)

    def test_stop_with_pending_metrics(self):
        """Test stopping the collector with pending metrics."""
        # Add a delay to metric storage to simulate slow processing
        self.mock_metrics_store.store_metric.side_effect = lambda x: time.sleep(0.2)

        # Submit multiple metrics
        for i in range(10):
            self.collector.submit_metric({"metric_type": "test", "value": i})

        # Stop collector with wait_for_completion=True
        start_time = time.time()
        self.collector.stop(wait_for_completion=True, timeout=3.0)
        stop_time = time.time()

        # Verify that stop waited for metrics to be processed
        self.assertGreater(stop_time - start_time, 0.2)

        # Check that metrics store was called for each metric
        self.assertGreaterEqual(self.mock_metrics_store.store_metric.call_count, 10)

    def test_non_blocking_behavior(self):
        """Test that submit_metric doesn't block the calling thread."""
        # Configure mock to be slow
        self.mock_metrics_store.store_metric.side_effect = lambda x: time.sleep(0.5)

        # Submit a metric and time it
        start_time = time.time()
        self.collector.submit_metric({"metric_type": "test", "value": 42})
        end_time = time.time()

        # Verify submission was fast (non-blocking)
        self.assertLess(end_time - start_time, 0.1)

    def test_get_singleton(self):
        """Test singleton access pattern."""
        # Get singleton instance
        collector1 = get_async_metrics_collector(self.test_config)
        collector2 = get_async_metrics_collector()

        # Verify same instance
        self.assertIs(collector1, collector2)
        self.assertIs(collector1, AsyncMetricsCollector._instance)


if __name__ == "__main__":
    unittest.main()
