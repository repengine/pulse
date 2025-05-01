"""
Test Forecast Generator Module

This module tests the forecast_generator.py module to ensure proper error handling
and type validation throughout the forecast generation pipeline.
"""
import pytest
from unittest.mock import patch, MagicMock
import logging
from forecast_output.forecast_generator import generate_forecast, generate_simulation_forecast

class TestForecastGenerator:
    
    def test_generate_simulation_forecast(self):
        """Test that generate_simulation_forecast returns expected format."""
        forecast = generate_simulation_forecast()
        assert isinstance(forecast, dict)
        assert "value" in forecast
        assert isinstance(forecast["value"], (int, float))

    def test_generate_forecast_with_valid_input(self):
        """Test forecast generation with valid input."""
        with patch("forecast_engine.ai_forecaster.predict") as mock_predict:
            # Mock AI forecaster response
            mock_predict.return_value = {"adjustment": 10.0}
            
            # Test with valid input features
            features = {"feature1": 1.0, "feature2": 2.0}
            forecast = generate_forecast(features)
            
            # Verify forecast structure
            assert isinstance(forecast, dict)
            assert "value" in forecast or "ensemble_forecast" in forecast
            
            # Verify AI forecaster was called with filtered features
            mock_predict.assert_called_once()
            
    def test_generate_forecast_with_invalid_input(self):
        """Test forecast generation handles invalid input gracefully."""
        with patch("forecast_engine.ai_forecaster.predict") as mock_predict:
            # Mock AI forecaster response
            mock_predict.return_value = {"adjustment": 5.0}
            
            # Test with None input
            forecast = generate_forecast(None)
            assert isinstance(forecast, dict)
            assert "value" in forecast
            
            # Test with non-dict input
            forecast = generate_forecast("not a dict")
            assert isinstance(forecast, dict)
            
            # Verify AI forecaster was still attempted to be called
            assert mock_predict.called

    def test_generate_forecast_with_non_numeric_values(self):
        """Test forecast generation handles non-numeric values gracefully."""
        with patch("forecast_engine.ai_forecaster.predict") as mock_predict:
            mock_predict.return_value = {"adjustment": 2.5}
            
            # Test with mixed numeric and non-numeric values
            features = {
                "valid": 1.0,
                "string": "not a number",
                "none": None,
                "nested": {
                    "valid": 2.0,
                    "invalid": "string"
                }
            }
            
            forecast = generate_forecast(features)
            assert isinstance(forecast, dict)
            
            # Verify filtered numeric features were passed to AI forecaster
            call_args = mock_predict.call_args[0][0]
            assert "valid" in call_args
            assert "string" not in call_args
            assert "nested_valid" in call_args
            assert "nested_invalid" not in call_args

    def test_generate_forecast_with_ai_forecaster_error(self):
        """Test forecast generation handles AI forecaster errors gracefully."""
        with patch("forecast_engine.ai_forecaster.predict") as mock_predict:
            # Simulate AI forecaster raising an exception
            mock_predict.side_effect = Exception("AI forecaster error")
            
            # Should still return a valid forecast
            features = {"feature1": 1.0}
            forecast = generate_forecast(features)
            
            assert isinstance(forecast, dict)
            assert "value" in forecast

    def test_generate_forecast_with_causal_model(self):
        """Test forecast generation with causal model."""
        # Create mock causal model
        causal_model = MagicMock()
        causal_model.parents.return_value = ["parent1", "parent2"]
        
        with patch("forecast_engine.ai_forecaster.predict") as mock_predict:
            mock_predict.return_value = {"adjustment": 1.5}
            
            # Generate forecast with causal model
            features = {"feature1": 1.0}
            forecast = generate_forecast(features, causal_model=causal_model)
            
            # Verify causal explanation is included
            assert "causal_explanation" in forecast
            assert forecast["causal_explanation"]["variable"] == "feature1"
            assert "parents" in forecast["causal_explanation"]

    def test_generate_forecast_with_causal_model_error(self):
        """Test forecast generation handles causal model errors gracefully."""
        # Create mock causal model that raises an exception
        causal_model = MagicMock()
        causal_model.parents.side_effect = Exception("Causal model error")
        
        # Should still return a valid forecast
        features = {"feature1": 1.0}
        forecast = generate_forecast(features, causal_model=causal_model)
        
        assert isinstance(forecast, dict)
        assert "causal_explanation" in forecast
        assert "error" in forecast["causal_explanation"]

    def test_generate_forecast_with_nested_dict(self):
        """Test forecast generation with deeply nested dictionaries."""
        with patch("forecast_engine.ai_forecaster.predict") as mock_predict:
            mock_predict.return_value = {"adjustment": 3.0}
            
            # Create deeply nested input dict
            features = {
                "level1": {
                    "level2": {
                        "level3": 3.0
                    },
                    "value": 1.0
                },
                "simple": 2.0
            }
            
            forecast = generate_forecast(features)
            assert isinstance(forecast, dict)
            
            # Verify flattened features were extracted
            call_args = mock_predict.call_args[0][0]
            assert "simple" in call_args
            assert "level1_value" in call_args
            # Note: current implementation only extracts one level of nesting
            # If the code is updated to handle deeper nesting, this test should be updated