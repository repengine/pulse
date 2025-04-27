import unittest
from forecast_engine import forecast_drift_monitor

class TestForecastDriftMonitor(unittest.TestCase):
    def test_score_drift(self):
        before = {"hope": {"avg_confidence": 0.7}, "despair": {"avg_confidence": 0.3}}
        after = {"hope": {"avg_confidence": 0.5}, "despair": {"avg_confidence": 0.4}}
        result = forecast_drift_monitor.score_drift(before, after)
        self.assertIn("drift_score", result)
        self.assertIn("tag_deltas", result)
        self.assertAlmostEqual(result["drift_score"], 0.15)

    def test_adwin_kswin_import(self):
        # Only test import, not actual drift detection (river may not be installed)
        self.assertTrue(hasattr(forecast_drift_monitor, "ADWIN"))
        self.assertTrue(hasattr(forecast_drift_monitor, "KSWIN"))

if __name__ == "__main__":
    unittest.main()
