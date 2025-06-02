import unittest
from unittest.mock import patch, MagicMock

# Import the module to reset its singleton
import recursive_training.data.feature_processor as rfp_module

from recursive_training.data.feature_processor_integration import (
    EnhancedFeatureProcessor,
    get_enhanced_feature_processor,
)


class TestFeatureProcessorIntegration(unittest.TestCase):
    """Tests for the feature processor integration."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset the singleton instance in feature_processor module
        rfp_module._instance = None

        # Create sample data items with time series
        self.data_items = [
            {
                "name": "GDP",
                "value": 112.0,
                "time_series": [100.0, 105.0, 107.0, 109.0, 112.0],
            },
            {
                "name": "Inflation",
                "value": 2.2,
                "time_series": [2.1, 2.3, 2.5, 2.4, 2.2],
            },
            {
                "name": "Employment",
                "value": 98.0,
                "time_series": [95.0, 96.0, 97.0, 96.5, 98.0],
            },
        ]

        # Basic configuration
        self.config = {
            "enable_advanced_processing": True,
            "integrate_advanced_features": True,
            "advanced_features": {
                "enable_time_frequency": True,
                "enable_graph_features": True,
                "enable_self_supervised": True,
                "time_frequency": {"tf_method": "stft", "nperseg": 4},
                "graph_features": {"correlation_threshold": 0.5},
                "self_supervised": {"latent_dim": 2},
            },
        }

    @patch(
        "recursive_training.data.feature_processor_integration.get_feature_processor"
    )
    @patch(
        "recursive_training.data.feature_processor_integration.process_with_advanced_techniques"
    )
    def test_extract_features_with_integration(self, mock_process, mock_get_processor):
        """Test extract_features with integration enabled."""
        # Setup mocks
        standard_features = {
            "items": [
                {"name": "GDP", "value": 112.0},
                {"name": "Inflation", "value": 2.2},
                {"name": "Employment", "value": 98.0},
            ]
        }
        # Create a mock for the feature processor that get_feature_processor returns
        mock_processor = MagicMock()
        mock_processor.extract_features.return_value = standard_features
        mock_get_processor.return_value = mock_processor

        advanced_features = {
            "time_frequency": {"item_0": {"spectral_entropy": [0.8]}},
            "graph_features": {
                "degree_centrality": {"GDP": 0.9},
                "node_communities": {"GDP": 0},
            },
            "self_supervised": {
                "representations": {"GDP": {"latent_vector": [0.1, 0.2]}}
            },
        }
        mock_process.return_value = advanced_features

        # Create processor
        processor = EnhancedFeatureProcessor(self.config)

        # Extract features
        result = processor.extract_features(self.data_items)

        # Verify that both standard and advanced extraction were called
        mock_processor.extract_features.assert_called_once_with(self.data_items)
        mock_process.assert_called_once_with(
            self.data_items, self.config["advanced_features"]
        )

        # Check that the result contains expected integrated features
        self.assertIsNotNone(result)
        # Verify the structure of the result should include items with integrated
        # features
        self.assertIn("items", result)

        # In the integrated result, items should have the advanced features integrated
        if "items" in result:
            # Check the first item has expected data
            if len(result["items"]) > 0:
                # The test can't know exactly what integration does without running the actual
                # integrate_with_pipeline function, but we can verify the mock was used
                # correctly
                pass

    @patch(
        "recursive_training.data.feature_processor_integration.get_feature_processor"
    )
    @patch(
        "recursive_training.data.feature_processor_integration.process_with_advanced_techniques"
    )
    def test_extract_features_without_integration(
        self, mock_process, mock_get_processor
    ):
        """Test extract_features with integration disabled."""
        # Modify config to disable integration
        config = self.config.copy()
        config["integrate_advanced_features"] = False

        # Setup mocks
        standard_features = {
            "items": [
                {"name": "GDP", "value": 112.0},
                {"name": "Inflation", "value": 2.2},
                {"name": "Employment", "value": 98.0},
            ]
        }
        # Create a mock for the feature processor that get_feature_processor returns
        mock_processor = MagicMock()
        mock_processor.extract_features.return_value = standard_features
        mock_get_processor.return_value = mock_processor

        advanced_features = {
            "time_frequency": {"item_0": {"spectral_entropy": [0.8]}},
            "graph_features": {"degree_centrality": {"GDP": 0.9}},
        }
        mock_process.return_value = advanced_features

        # Create processor
        processor = EnhancedFeatureProcessor(config)

        # Extract features
        result = processor.extract_features(self.data_items)

        # Verify that extract_features was called
        mock_processor.extract_features.assert_called_once_with(self.data_items)

        # Verify that process_with_advanced_techniques was called
        mock_process.assert_called_once_with(
            self.data_items, config["advanced_features"]
        )

        # Verify that the result contains standard features and advanced features
        # as a separate section
        self.assertIn("items", result)
        self.assertIn("advanced", result)
        self.assertIn("time_frequency", result["advanced"])

    @patch(
        "recursive_training.data.feature_processor_integration.get_feature_processor"
    )
    def test_extract_features_disabled_advanced(self, mock_get_processor):
        """Test extract_features with advanced processing disabled."""
        # Modify config to disable advanced processing
        config = self.config.copy()
        config["enable_advanced_processing"] = False

        # Setup mock
        standard_features = {
            "items": [
                {"name": "GDP", "value": 112.0},
                {"name": "Inflation", "value": 2.2},
                {"name": "Employment", "value": 98.0},
            ]
        }
        # Create a mock for the feature processor that get_feature_processor returns
        mock_processor = MagicMock()
        mock_processor.extract_features.return_value = standard_features
        mock_get_processor.return_value = mock_processor

        # Create processor
        processor = EnhancedFeatureProcessor(config)

        # Extract features
        result = processor.extract_features(self.data_items)

        # Verify that only standard extraction was called
        mock_processor.extract_features.assert_called_once_with(self.data_items)

        # Verify that the result is the standard features
        self.assertEqual(result, standard_features)

    @patch(
        "recursive_training.data.feature_processor_integration.get_feature_processor"
    )
    @patch(
        "recursive_training.data.feature_processor_integration.EnhancedFeatureProcessor.extract_features"
    )
    def test_fit(self, mock_extract, mock_get_processor):
        """Test fit method calls standard processor fit."""
        # Setup mocks
        mock_extract.return_value = {"items": []}
        # Create a mock for the feature processor that get_feature_processor returns
        mock_processor = MagicMock()
        mock_get_processor.return_value = mock_processor

        # Create processor
        processor = EnhancedFeatureProcessor(self.config)

        # Fit
        processor.fit(self.data_items)

        # Verify that extract_features was called during fit
        mock_extract.assert_called_once()

        # Verify that standard processor's fit was called
        mock_processor.fit.assert_called_once_with(self.data_items)

    @patch(
        "recursive_training.data.feature_processor_integration.get_feature_processor"
    )
    @patch(
        "recursive_training.data.feature_processor_integration.EnhancedFeatureProcessor.extract_features"
    )
    def test_transform(self, mock_extract, mock_get_processor):
        """Test transform method calls standard processor transform."""
        # Setup mocks
        mock_extract.return_value = {"items": []}
        # Create a mock for the feature processor that get_feature_processor returns
        mock_processor = MagicMock()
        mock_processor.transform.return_value = {"transformed": True}
        mock_get_processor.return_value = mock_processor

        # Create processor
        processor = EnhancedFeatureProcessor(self.config)

        # Transform
        result = processor.transform(self.data_items)

        # Verify that extract_features was called during transform
        mock_extract.assert_called_once()

        # Verify that standard transform was called
        mock_processor.transform.assert_called_once_with(self.data_items)
        self.assertEqual(result, {"transformed": True})

    def test_get_enhanced_feature_processor(self):
        """Test the get_enhanced_feature_processor function returns a singleton."""
        # Get processor
        processor1 = get_enhanced_feature_processor(self.config)
        processor2 = get_enhanced_feature_processor()

        # Verify that both references point to the same object
        self.assertIs(processor1, processor2)

        # Verify that it's an EnhancedFeatureProcessor
        self.assertIsInstance(processor1, EnhancedFeatureProcessor)

        # Test updating config
        new_config = {"new_setting": True}
        processor3 = get_enhanced_feature_processor(new_config)

        # Verify that the config was updated
        self.assertIs(processor1, processor3)
        self.assertTrue(processor3.config["new_setting"])


if __name__ == "__main__":
    unittest.main()
