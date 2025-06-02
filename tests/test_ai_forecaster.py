import unittest
from unittest.mock import patch, MagicMock
import torch  # Added for torch.tensor
from forecast_engine import ai_forecaster, forecast_ensemble
from engine import pulse_config


class TestAIForecaster(unittest.TestCase):
    def test_predict_default(self) -> None:
        # The 'ai_forecaster.predict' function uses a module-level '_model'.
        # We need to patch this '_model'.
        # This mock_model will simulate an instance of LSTMForecaster.
        # When _model(tensor) is called in predict(), this mock's return_value
        # will be used.

        mock_lstm_model_instance = MagicMock()
        # Configure the mock model to return a tensor that results in 0.0 after .item()
        # This is what's called by `_model(tensor)`
        mock_lstm_model_instance.return_value = torch.tensor([[0.0]])

        # Also, the _model instance needs to have an eval method that can be called.
        mock_lstm_model_instance.eval = MagicMock()

        # Patch the module-level '_model' and '_input_size' in 'forecast_engine.ai_forecaster'
        # Patch _initialize_model as a safeguard, though it shouldn't be called if _model is set
        # and _input_size matches.
        with (
            patch(
                "forecast_engine.ai_forecaster._model", mock_lstm_model_instance
            ) as _patched_model,
            patch(
                "forecast_engine.ai_forecaster._input_size", 1
            ) as _patched_input_size,
            patch(
                "forecast_engine.ai_forecaster._initialize_model", return_value=True
            ) as _mock_init_model,
        ):
            input_features = {
                "sample_feature": 1
            }  # This will result in len(features) == 1
            result = ai_forecaster.predict(input_features)

            # Assert that our mock_lstm_model_instance was called (as a function)
            mock_lstm_model_instance.assert_called_once()
            # Assert that the eval method of our mock_lstm_model_instance was called
            mock_lstm_model_instance.eval.assert_called_once()

            self.assertIsInstance(result, dict)
            self.assertIn("adjustment", result)
            self.assertEqual(
                result["adjustment"], 0.0, msg=f"Adjustment was {
                    result.get('adjustment')}, error: {
                    result.get('error')}", )
            self.assertNotIn(
                "error",
                result,
                msg=f"Prediction unexpectedly returned an error: {result.get('error')}",
            )

    def test_ensemble_forecast(self) -> None:
        simulation_forecast = {"value": 100.0}
        ai_forecast_data = {"adjustment": 10.0}
        # Ensure AI forecasting is enabled and weights are set for consistent testing.
        pulse_config.AI_FORECAST_ENABLED = True
        pulse_config.ENSEMBLE_WEIGHTS = {"simulation": 0.7, "ai": 0.3}
        combined = forecast_ensemble.ensemble_forecast(
            simulation_forecast, ai_forecast_data
        )
        # Expected combined value:
        # simulation_forecast = 100.0, ai_forecast adjustment = 10.0
        # Combined = 0.7 * 100.0 + 0.3 * (100.0 + 10.0) = 70.0 + 33.0 = 103.0
        self.assertIn("ensemble_forecast", combined)
        self.assertAlmostEqual(combined["ensemble_forecast"], 103.0)

    def test_train_update_no_error(self) -> None:
        # Verify that train and update functions run without error on empty data.
        try:
            ai_forecaster.train([])
            ai_forecaster.update([])
        except Exception as e:
            self.fail(f"train or update raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
