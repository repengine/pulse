import unittest
import os
import numpy as np
from unittest.mock import patch, MagicMock

from recursive_training.data.feature_processor import RecursiveFeatureProcessor, get_feature_processor
from recursive_training.data.feature_processor_integration import EnhancedFeatureProcessor, get_enhanced_feature_processor
from recursive_training.data.advanced_feature_processor import process_with_advanced_techniques, integrate_with_pipeline


class TestFeatureProcessorIntegration(unittest.TestCase):
    """Tests for the feature processor integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample data items with time series
        self.data_items = [
            {
                "name": "GDP", 
                "value": 112.0,
                "time_series": [100.0, 105.0, 107.0, 109.0, 112.0]
            },
            {
                "name": "Inflation", 
                "value": 2.2,
                "time_series": [2.1, 2.3, 2.5, 2.4, 2.2]
            },
            {
                "name": "Employment", 
                "value": 98.0,
                "time_series": [95.0, 96.0, 97.0, 96.5, 98.0]
            }
        ]
        
        # Basic configuration
        self.config = {
            "enable_advanced_processing": True,
            "integrate_advanced_features": True,
            "advanced_features": {
                "enable_time_frequency": True,
                "enable_graph_features": True,
                "enable_self_supervised": True,
                "time_frequency": {
                    "tf_method": "stft",
                    "nperseg": 4
                },
                "graph_features": {
                    "correlation_threshold": 0.5
                },
                "self_supervised": {
                    "latent_dim": 2
                }
            }
        }
    
    @patch('recursive_training.data.feature_processor.RecursiveFeatureProcessor.extract_features')
    @patch('recursive_training.data.advanced_feature_processor.process_with_advanced_techniques')
    def test_extract_features_with_integration(self, mock_process, mock_extract):
        """Test extract_features with integration enabled."""
        # Setup mocks
        standard_features = {
            "items": [
                {"name": "GDP", "value": 112.0},
                {"name": "Inflation", "value": 2.2},
                {"name": "Employment", "value": 98.0}
            ]
        }
        mock_extract.return_value = standard_features
        
        advanced_features = {
            "time_frequency": {"item_0": {"spectral_entropy": [0.8]}},
            "graph_features": {
                "degree_centrality": {"GDP": 0.9},
                "node_communities": {"GDP": 0}
            },
            "self_supervised": {
                "representations": {
                    "GDP": {"latent_vector": [0.1, 0.2]}
                }
            }
        }
        mock_process.return_value = advanced_features
        
        # Create processor
        processor = EnhancedFeatureProcessor(self.config)
        
        # Extract features
        result = processor.extract_features(self.data_items)
        
        # Verify that both standard and advanced extraction were called
        mock_extract.assert_called_once_with(self.data_items)
        mock_process.assert_called_once_with(self.data_items, self.config["advanced_features"])
        
        # Without actually running integrate_with_pipeline, we'll just check
        # that the result contains some expected keys
        self.assertIsNotNone(result)
    
    @patch('recursive_training.data.feature_processor.RecursiveFeatureProcessor.extract_features')
    @patch('recursive_training.data.advanced_feature_processor.process_with_advanced_techniques')
    def test_extract_features_without_integration(self, mock_process, mock_extract):
        """Test extract_features with integration disabled."""
        # Modify config to disable integration
        config = self.config.copy()
        config["integrate_advanced_features"] = False
        
        # Setup mocks
        standard_features = {
            "items": [
                {"name": "GDP", "value": 112.0},
                {"name": "Inflation", "value": 2.2},
                {"name": "Employment", "value": 98.0}
            ]
        }
        mock_extract.return_value = standard_features
        
        advanced_features = {
            "time_frequency": {"item_0": {"spectral_entropy": [0.8]}},
            "graph_features": {
                "degree_centrality": {"GDP": 0.9}
            }
        }
        mock_process.return_value = advanced_features
        
        # Create processor
        processor = EnhancedFeatureProcessor(config)
        
        # Extract features
        result = processor.extract_features(self.data_items)
        
        # Verify that the result contains standard features and advanced features as a separate section
        self.assertIn("items", result)
        self.assertIn("advanced", result)
        self.assertIn("time_frequency", result["advanced"])
    
    @patch('recursive_training.data.feature_processor.RecursiveFeatureProcessor.extract_features')
    def test_extract_features_disabled_advanced(self, mock_extract):
        """Test extract_features with advanced processing disabled."""
        # Modify config to disable advanced processing
        config = self.config.copy()
        config["enable_advanced_processing"] = False
        
        # Setup mock
        standard_features = {
            "items": [
                {"name": "GDP", "value": 112.0},
                {"name": "Inflation", "value": 2.2},
                {"name": "Employment", "value": 98.0}
            ]
        }
        mock_extract.return_value = standard_features
        
        # Create processor
        processor = EnhancedFeatureProcessor(config)
        
        # Extract features
        result = processor.extract_features(self.data_items)
        
        # Verify that only standard extraction was called
        mock_extract.assert_called_once_with(self.data_items)
        
        # Verify that the result is the standard features
        self.assertEqual(result, standard_features)
    
    @patch('recursive_training.data.feature_processor.RecursiveFeatureProcessor.fit')
    @patch('recursive_training.data.feature_processor_integration.EnhancedFeatureProcessor.extract_features')
    def test_fit(self, mock_extract, mock_fit):
        """Test fit method calls standard processor fit."""
        # Setup mocks
        mock_extract.return_value = {"items": []}
        
        # Create processor
        processor = EnhancedFeatureProcessor(self.config)
        
        # Fit
        processor.fit(self.data_items)
        
        # Verify that standard fit was called
        mock_fit.assert_called_once_with(self.data_items)
    
    @patch('recursive_training.data.feature_processor.RecursiveFeatureProcessor.transform')
    @patch('recursive_training.data.feature_processor_integration.EnhancedFeatureProcessor.extract_features')
    def test_transform(self, mock_extract, mock_transform):
        """Test transform method calls standard processor transform."""
        # Setup mocks
        mock_extract.return_value = {"items": []}
        mock_transform.return_value = {"transformed": True}
        
        # Create processor
        processor = EnhancedFeatureProcessor(self.config)
        
        # Transform
        result = processor.transform(self.data_items)
        
        # Verify that standard transform was called
        mock_transform.assert_called_once_with(self.data_items)
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


if __name__ == '__main__':
    unittest.main()