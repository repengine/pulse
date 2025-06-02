"""
Tests for the TrustUpdateBuffer.

These tests verify that the buffer correctly collects, aggregates, and flushes
trust updates to the OptimizedBayesianTrustTracker.
"""

import unittest
import time
from unittest.mock import patch, MagicMock
import threading

from analytics.trust_update_buffer import TrustUpdateBuffer, get_trust_update_buffer
from analytics.optimized_trust_tracker import OptimizedBayesianTrustTracker


class TestTrustUpdateBuffer(unittest.TestCase):
    """Tests for the TrustUpdateBuffer class."""

    def setUp(self):
        """Set up test environment."""
        # Create a fresh instance with test config for each test
        self.test_config = {
            "trust_buffer_size": 100,
            "trust_flush_threshold": 10,
            "trust_auto_flush_interval_sec": 0.5,
        }
        # Ensure we don't use the singleton for tests
        TrustUpdateBuffer._instance = None
        self.buffer = TrustUpdateBuffer(self.test_config)

        # Mock the trust tracker
        self.mock_tracker = MagicMock(spec=OptimizedBayesianTrustTracker)
        self.buffer.trust_tracker = self.mock_tracker

    def test_add_update_and_manual_flush(self):
        """Test adding updates and manually flushing."""
        # Add some updates
        self.buffer.add_update("rule1", True, 1.0)
        self.buffer.add_update("rule1", False, 0.5)
        self.buffer.add_update("rule2", True, 2.0)

        # Check buffer state
        self.assertEqual(self.buffer._buffer_size, 3)
        self.assertEqual(len(self.buffer._buffer), 2)  # Two unique keys

        # Manually flush
        updates_flushed = self.buffer.flush()

        # Verify results
        self.assertEqual(updates_flushed, 3)
        self.assertEqual(self.buffer._buffer_size, 0)
        self.assertEqual(len(self.buffer._buffer), 0)

        # Verify trust tracker was called with optimized batch
        self.mock_tracker.batch_update.assert_called_once()
        # The update should contain the aggregated updates
        args = self.mock_tracker.batch_update.call_args[0][0]
        self.assertEqual(len(args), 3)  # 3 unique (key, success) combinations

    def test_auto_flush_on_threshold(self):
        """Test automatic flush when buffer size reaches threshold."""
        # Add updates just below threshold
        for i in range(self.test_config["trust_flush_threshold"] - 1):
            flushed = self.buffer.add_update(f"rule{i}", True, 1.0)
            self.assertFalse(flushed)

        # Add one more to trigger flush
        flushed = self.buffer.add_update("rule_trigger", True, 1.0)

        # Verify auto-flush occurred
        self.assertTrue(flushed)
        self.assertEqual(self.buffer._buffer_size, 0)
        self.mock_tracker.batch_update.assert_called_once()

    def test_auto_flush_on_time(self):
        """Test automatic flush after time interval."""
        # Add an update
        self.buffer.add_update("rule1", True, 1.0)

        # Mock time passing
        original_time = time.time()
        with patch("time.time") as mock_time:
            # Set time to be past the auto-flush interval
            mock_time.return_value = (
                original_time + self.test_config["trust_auto_flush_interval_sec"] + 0.1
            )

            # Add another update, should trigger time-based flush
            flushed = self.buffer.add_update("rule2", True, 1.0)

            # Verify auto-flush occurred
            self.assertTrue(flushed)
            self.assertEqual(self.buffer._buffer_size, 0)
            self.mock_tracker.batch_update.assert_called_once()

    def test_batch_updates(self):
        """Test adding multiple updates at once."""
        # Create batch of updates
        batch = [
            ("rule1", True, 1.0),
            ("rule1", False, 0.5),
            ("rule2", True, 2.0),
            ("rule3", False, 1.5),
        ]

        # Add batch
        self.buffer.add_updates_batch(batch)

        # Check buffer state
        self.assertEqual(self.buffer._buffer_size, 4)
        self.assertEqual(len(self.buffer._buffer), 3)  # Three unique keys

        # Flush and verify
        self.buffer.flush()
        self.mock_tracker.batch_update.assert_called_once()

    def test_aggregation(self):
        """Test that updates are properly aggregated."""
        # Add multiple updates for the same rule/success combination
        self.buffer.add_update("rule1", True, 1.0)
        self.buffer.add_update("rule1", True, 2.0)
        self.buffer.add_update("rule1", False, 0.5)
        self.buffer.add_update("rule1", False, 1.5)

        # Flush and capture the batch update
        self.buffer.flush()

        # Verify tracker call
        self.mock_tracker.batch_update.assert_called_once()
        args = self.mock_tracker.batch_update.call_args[0][0]

        # Look for aggregated values
        rule1_true = None
        rule1_false = None

        for key, success, weight in args:
            if key == "rule1":
                if success:
                    rule1_true = weight
                else:
                    rule1_false = weight

        # Verify aggregation
        self.assertEqual(rule1_true, 3.0)  # 1.0 + 2.0
        self.assertEqual(rule1_false, 2.0)  # 0.5 + 1.5

    def test_get_stats(self):
        """Test statistics reporting."""
        # Add some updates and flush
        self.buffer.add_update("rule1", True, 1.0)
        self.buffer.add_update("rule2", False, 0.5)
        self.buffer.flush()

        # Add more updates
        self.buffer.add_update("rule3", True, 2.0)

        # Get stats
        stats = self.buffer.get_stats()

        # Verify stats
        self.assertEqual(stats["updates_buffered"], 3)
        self.assertEqual(stats["updates_flushed"], 2)
        self.assertEqual(stats["flush_operations"], 1)
        self.assertEqual(stats["manual_flushes"], 1)
        self.assertEqual(stats["current_buffer_size"], 1)
        self.assertEqual(stats["unique_keys"], 1)

    def test_thread_safety(self):
        """Test thread safety of the buffer."""
        # Number of threads and updates per thread
        num_threads = 5
        updates_per_thread = 20

        # Function for thread to execute
        def add_updates(thread_id):
            for i in range(updates_per_thread):
                self.buffer.add_update(f"rule{thread_id}_{i}", i % 2 == 0, 1.0)

        # Create and start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=add_updates, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Flush any remaining updates
        self.buffer.flush()

        # Verify all updates were processed
        stats = self.buffer.get_stats()
        expected_updates = num_threads * updates_per_thread
        self.assertEqual(stats["updates_buffered"], expected_updates)
        self.assertEqual(stats["updates_flushed"], expected_updates)

    def test_get_singleton(self):
        """Test singleton access pattern."""
        # Get singleton instance
        buffer1 = get_trust_update_buffer(self.test_config)
        buffer2 = get_trust_update_buffer()

        # Verify same instance
        self.assertIs(buffer1, buffer2)
        self.assertIs(buffer1, TrustUpdateBuffer._instance)


if __name__ == "__main__":
    unittest.main()
