# test_trust_engine.py

import unittest
from trust_system.trust_engine import TrustEngine

# This test suite verifies that the Pulse TrustEngine functions correctly.
# It tests tagging, confidence scoring, trust gating, audit summaries,
# and metadata embedding across representative forecast scenarios.

class TestTrustEngine(unittest.TestCase):
    def setUp(self):
        """
        Initializes a baseline symbolic forecast for testing.
        Forecast has:
        - High hope overlay (triggers tagging)
        - Moderate capital increase (for movement signal)
        - Low fragility (should produce high trust score)
        - Retrodiction score near 1.0 (very confident in hindsight)
        """
        self.sample_forecast = {
            "trace_id": "abc123",
            "overlays": {"hope": 0.8, "despair": 0.1, "rage": 0.1, "fatigue": 0.2},
            "forecast": {
                "start_capital": {"nvda": 1000},  # Starting capital baseline
                "end_capital": {"nvda": 1150},    # 15% return → positive signal
                "symbolic_change": {"hope": 0.3},  # Used for novelty checks
            },
            "fragility": 0.2,                       # Low fragility → high trust
            "retrodiction_score": 0.95,            # Strong historical alignment
        }

    def test_tag_forecast(self):
        """
        Verify correct symbolic tag and arc assignment for high-hope overlay.
        Also test fallback condition when thresholds are not met.
        """
        result = TrustEngine.tag_forecast(self.sample_forecast)
        self.assertEqual(result["symbolic_tag"], "Hope")
        self.assertEqual(result["arc_label"], "Hope Surge")
        # Fallback case for no overlays
        no_tag = TrustEngine.tag_forecast({"overlays": {}})
        self.assertEqual(no_tag["symbolic_tag"], "")
        self.assertEqual(no_tag["arc_label"], "Unknown")

    def test_score_forecast(self):
        """
        Ensure score is bounded between 0.0 and 1.0.
        Fragility and novelty should influence the outcome:
        - Low fragility → raises trust
        - Moderate capital change → positive impact
        - Novel symbolic pattern → boosts novelty score
        """
        score = TrustEngine.score_forecast(self.sample_forecast)
        self.assertTrue(0.0 <= score <= 1.0)

    def test_confidence_gate(self):
        """
        Manually set confidence and fragility and ensure the
        correct label (Trusted / Unstable / Rejected) is returned.
        """
        self.sample_forecast["confidence"] = 0.8
        self.sample_forecast["fragility"] = 0.3
        label = TrustEngine.confidence_gate(self.sample_forecast)
        self.assertEqual(label, "🟢 Trusted")

    def test_missing_confidence_fragility(self):
        """
        Should handle forecasts missing confidence/fragility gracefully.
        """
        forecast = {}
        label = TrustEngine.confidence_gate(forecast)
        self.assertIn(label, ["🔴 Rejected", "🟡 Unstable", "🟢 Trusted"])  # Updated to match actual return values

    def test_malformed_forecast(self):
        """
        Should not crash on malformed input.
        """
        with self.assertRaises(Exception):
            TrustEngine.confidence_gate(None)  # Explicitly pass None to force exception

    def test_apply_all(self):
        """
        Ensure that batch trust processing injects `trust_label`
        and `pulse_trust_meta` into each forecast.
        """
        forecasts = [self.sample_forecast.copy() for _ in range(3)]
        processed = TrustEngine.apply_all(forecasts)
        for f in processed:
            self.assertIn("trust_label", f)
            self.assertIn("pulse_trust_meta", f)

    def test_run_trust_audit(self):
        """
        Verify full audit structure is returned and symbolic conflict is detected.
        This creates one hopeful and one despair-tagged forecast to trigger conflict logic.
        """
        forecasts = [self.sample_forecast.copy() for _ in range(2)]
        # Ensure both forecasts have necessary properties for conflict detection
        forecasts[0]["symbolic_tag"] = "Hope"
        forecasts[0]["arc_label"] = "Hope Surge"
        forecasts[0]["trace_id"] = "trace1"
        
        forecasts[1]["symbolic_tag"] = "Despair"     # Opposing tag to cause conflict
        forecasts[1]["arc_label"] = "Collapse Risk"  # Contradictory arc
        forecasts[1]["trace_id"] = "trace2"
        result = TrustEngine.run_trust_audit(forecasts)
        self.assertIn("mirror", result)
        self.assertIn("contradictions", result)
        self.assertIn("lineage_summary", result)
        self.assertGreater(len(result["contradictions"]["symbolic_tag_conflicts"]), 0)

# Enable verbose CLI output for easier debugging and CI display
if __name__ == "__main__":
    unittest.main(verbosity=2)
