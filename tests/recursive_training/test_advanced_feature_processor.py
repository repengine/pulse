import unittest
from unittest.mock import patch

from recursive_training.data.advanced_feature_processor import (
    AdvancedFeatureProcessor,
    integrate_with_pipeline,
)


class TestAdvancedFeatureProcessor(unittest.TestCase):
    """Tests for the AdvancedFeatureProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample data items with time series
        self.data_items = [
            {
                "name": "GDP",
                "time_series": [100.0, 105.0, 107.0, 109.0, 112.0],
                "type": "economic",
            },
            {
                "name": "Inflation",
                "time_series": [2.1, 2.3, 2.5, 2.4, 2.2],
                "type": "economic",
            },
            {
                "name": "Employment",
                "time_series": [95.0, 96.0, 97.0, 96.5, 98.0],
                "type": "economic",
            },
        ]

        # Basic configuration
        self.config = {
            "enable_time_frequency": True,
            "enable_graph_features": True,
            "enable_self_supervised": True,
            "time_frequency": {"tf_method": "stft", "nperseg": 4},
            "graph_features": {
                "correlation_threshold": 0.5,
                "correlation_method": "pearson",
            },
            "self_supervised": {
                "latent_dim": 2,
                "framework": "simple",  # Use simple implementation for testing
            },
        }

        # Create processor
        self.processor = AdvancedFeatureProcessor(self.config)

    @patch(
        "recursive_training.data.advanced_feature_processor.apply_time_frequency_decomposition"
    )
    @patch(
        "recursive_training.data.advanced_feature_processor.apply_graph_based_features"
    )
    @patch(
        "recursive_training.data.advanced_feature_processor.apply_self_supervised_learning"
    )
    def test_process(self, mock_ssl, mock_graph, mock_tf):
        """Test the process method calls all enabled techniques."""
        # Setup mocks
        mock_tf.return_value = {"time_frequency": {"feature1": [1.0, 2.0]}}
        mock_graph.return_value = {"graph_features": {"feature2": [3.0, 4.0]}}
        mock_ssl.return_value = {"self_supervised": {"feature3": [5.0, 6.0]}}

        # Call process
        result = self.processor.process(self.data_items)

        # Verify all techniques were called
        mock_tf.assert_called_once_with(self.data_items, self.config["time_frequency"])
        mock_graph.assert_called_once_with(
            self.data_items, self.config["graph_features"]
        )
        mock_ssl.assert_called_once_with(
            self.data_items, self.config["self_supervised"]
        )

        # Verify results contain expected keys
        self.assertIn("time_frequency", result)
        self.assertIn("graph_features", result)
        self.assertIn("self_supervised", result)
        self.assertIn("metadata", result)

    def test_process_with_disabled_techniques(self):
        """Test process method with some techniques disabled."""
        # Create processor with disabled techniques
        config = self.config.copy()
        config["enable_graph_features"] = False
        config["enable_self_supervised"] = False
        processor = AdvancedFeatureProcessor(config)

        # Use patching to avoid actual computation
        with patch(
            "recursive_training.data.advanced_feature_processor.apply_time_frequency_decomposition"
        ) as mock_tf:
            mock_tf.return_value = {"time_frequency": {"feature1": [1.0, 2.0]}}

            # Call process
            result = processor.process(self.data_items)

            # Verify only time-frequency was called
            mock_tf.assert_called_once()
            self.assertIn("time_frequency", result)
            self.assertIn("metadata", result)

            # Verify metadata correctly reflects disabled techniques
            self.assertTrue(result["metadata"]["techniques_applied"]["time_frequency"])
            self.assertFalse(result["metadata"]["techniques_applied"]["graph_features"])
            self.assertFalse(
                result["metadata"]["techniques_applied"]["self_supervised"]
            )

    def test_integration_with_pipeline(self):
        """Test integration with the original feature pipeline."""
        # Create mock original features
        original_features = {
            "items": [
                {"name": "GDP", "value": 112.0},
                {"name": "Inflation", "value": 2.2},
                {"name": "Employment", "value": 98.0},
            ],
            "metadata": {"timestamp": "2025-05-02T12:00:00"},
        }

        # Create mock advanced features
        advanced_features = {
            "time_frequency": {
                "item_0": {
                    "spectral_entropy": [0.8, 0.7, 0.9],
                    "regime_shifts": [{"time_index": 2, "confidence": 0.8}],
                }
            },
            "graph_features": {
                "degree_centrality": {"GDP": 0.9, "Inflation": 0.7, "Employment": 0.8},
                "node_communities": {"GDP": 0, "Inflation": 1, "Employment": 0},
                "density": 0.7,
                "average_clustering": 0.6,
                "modularity": 0.5,
            },
            "self_supervised": {
                "representations": {
                    "GDP": {"latent_vector": [0.1, 0.2], "reconstruction_error": 0.01},
                    "Inflation": {
                        "latent_vector": [0.3, 0.4],
                        "reconstruction_error": 0.02,
                    },
                    "Employment": {
                        "latent_vector": [0.5, 0.6],
                        "reconstruction_error": 0.03,
                    },
                }
            },
        }

        # Call integration function
        integrated = integrate_with_pipeline(original_features, advanced_features)

        # Verify integration
        self.assertEqual(len(integrated["items"]), 3)

        # Check if time frequency features are integrated
        self.assertIn("spectral_entropy", integrated["items"][0])
        self.assertIn("regime_shifts", integrated["items"][0])

        # Check if graph features are integrated
        self.assertIn("degree_centrality", integrated["items"][0])
        self.assertIn("community", integrated["items"][0])

        # Check if self-supervised features are integrated
        self.assertIn("latent_representation", integrated["items"][0])
        self.assertIn("reconstruction_error", integrated["items"][0])

        # Check if graph-level metrics are added
        self.assertIn("graph_level", integrated)
        self.assertEqual(integrated["graph_level"]["density"], 0.7)

        # Check if metadata is updated
        self.assertIn("metadata", integrated)
        self.assertIn("advanced_processing", integrated["metadata"])


if __name__ == "__main__":
    unittest.main()
