import unittest
from forecast_engine import ai_forecaster, forecast_ensemble
from core import pulse_config

class TestAIForecaster(unittest.TestCase):
    def test_predict_default(self):
        input_features = {"sample_feature": 1}
        result = ai_forecaster.predict(input_features)
        self.assertIsInstance(result, dict)
        self.assertIn("adjustment", result)
        self.assertEqual(result["adjustment"], 0.0)

    def test_ensemble_forecast(self):
        simulation_forecast = {"value": 100.0}
        ai_forecast_data = {"adjustment": 10.0}
        # Ensure AI forecasting is enabled and weights are set for consistent testing.
        pulse_config.AI_FORECAST_ENABLED = True
        pulse_config.ENSEMBLE_WEIGHTS = {"simulation": 0.7, "ai": 0.3}
        combined = forecast_ensemble.ensemble_forecast(simulation_forecast, ai_forecast_data)
        # Expected combined value:
        # simulation_forecast = 100.0, ai_forecast adjustment = 10.0
        # Combined = 0.7 * 100.0 + 0.3 * (100.0 + 10.0) = 70.0 + 33.0 = 103.0
        self.assertIn("ensemble_forecast", combined)
        self.assertAlmostEqual(combined["ensemble_forecast"], 103.0)

    def test_train_update_no_error(self):
        # Verify that train and update functions run without error on empty data.
        try:
            ai_forecaster.train([])
            ai_forecaster.update([])
        except Exception as e:
            self.fail(f"train or update raised an exception: {e}")

if __name__ == "__main__":
    unittest.main()