# test_forecast_retrospector.py

import unittest
from forecast_retrospector import reconstruct_past_state, retrodict_error_score, retrospective_analysis_batch

class TestForecastRetrospector(unittest.TestCase):
    def setUp(self):
        self.forecast = {
            "overlays": {"hope": 0.8, "despair": 0.2, "rage": 0.1, "fatigue": 0.3},
            "forecast": {
                "start_capital": {"nvda": 1000, "msft": 1200}
            }
        }
        self.current_state = {
            "hope": 0.6,
            "despair": 0.3,
            "rage": 0.2,
            "fatigue": 0.4,
            "capital_snapshot": {"nvda": 950, "msft": 1250}
        }

    def test_reconstruct_past_state(self):
        past = reconstruct_past_state(self.forecast)
        self.assertIn("hope", past)
        self.assertIn("capital_snapshot", past)
        self.assertEqual(past["capital_snapshot"].get("nvda"), 1000)

    def test_retrodict_error_score(self):
        past = reconstruct_past_state(self.forecast)
        score = retrodict_error_score(past, self.current_state)
        self.assertTrue(0.0 <= score <= 10.0)

    def test_retrospective_analysis_batch(self):
        forecasts = [self.forecast.copy() for _ in range(3)]
        results = retrospective_analysis_batch(forecasts, self.current_state, threshold=0.5)
        for res in results:
            self.assertIn("retrodiction_error", res)
            self.assertIsInstance(res["retrodiction_error"], float)
            if res["retrodiction_error"] > 0.5:
                self.assertEqual(res.get("retrodiction_flag"), "⚠️ Symbolic misalignment")

if __name__ == '__main__':
    unittest.main(verbosity=2)
