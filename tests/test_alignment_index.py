# tests/test_alignment_index.py

import unittest
from trust_system.alignment_index import compute_alignment_index


class TestForecastAlignmentIndex(unittest.TestCase):
    def setUp(self):
        self.base_forecast = {"trace_id": "fc_001", "confidence": 0.85}

    def test_confidence_only(self):
        result = compute_alignment_index(self.base_forecast)
        self.assertIn("alignment_score", result)
        self.assertTrue(0 <= result["alignment_score"] <= 100)
        self.assertEqual(result["forecast_id"], "fc_001")

    def test_with_all_components(self):
        result = compute_alignment_index(
            self.base_forecast,
            current_state={},  # will fallback gracefully
            arc_volatility=0.3,
            tag_match=0.9,
            memory=[],
        )
        self.assertIn("components", result)
        self.assertTrue("novelty" in result["components"])

    def test_extreme_values(self):
        forecast = {"trace_id": "fc_bad", "confidence": 0.0}
        result = compute_alignment_index(forecast, arc_volatility=1.0, tag_match=0.0)
        self.assertLess(result["alignment_score"], 60)


if __name__ == "__main__":
    unittest.main()
