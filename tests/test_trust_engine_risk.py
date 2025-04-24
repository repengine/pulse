import unittest
from trust_system.trust_engine import compute_risk_score, TrustEngine

class TestRiskScoring(unittest.TestCase):
    def test_compute_risk_score_no_memory(self):
        forecast = {
            "forecast": {
                "start_capital": {"nvda": 100, "msft": 200, "ibit": 0, "spy": 0},
                "end_capital": {"nvda": 300, "msft": 200, "ibit": 0, "spy": 0},
                "symbolic_change": {"hope": 0.2}
            }
        }
        # Expected risk_volatility: (|300-100|)/2000 = 200/2000 = 0.1
        # With no memory, historical component = 0, and ml_adjustment = 0.1.
        # risk_score = (0.1*0.5 + 0.0*0.4 + 0.1*0.1) = 0.05 + 0.0 + 0.01 = 0.06.
        risk = compute_risk_score(forecast)
        self.assertAlmostEqual(risk, 0.06, places=2)

    def test_score_forecast_includes_risk_component(self):
        forecast = {
            "trace_id": "t1",
            "fragility": 0.2,
            "forecast": {
                "start_capital": {"nvda": 100, "msft": 200, "ibit": 50, "spy": 150},
                "end_capital": {"nvda": 300, "msft": 220, "ibit": 50, "spy": 160},
                "symbolic_change": {"hope": 0.2}
            },
            "overlays": {"hope": 0.8}
        }
        # Using an empty memory list for simplicity.
        score = TrustEngine.score_forecast(forecast, memory=[])
        # Ensure that the risk_score was computed and added to the forecast.
        self.assertIn("risk_score", forecast)
        # The final confidence should be within the configured thresholds.
        self.assertGreaterEqual(score, 0.5)
        self.assertLessEqual(score, 1.0)

    def test_confidence_gate_risk_high(self):
        # If the risk score exceeds the threshold, even with high confidence,
        # the forecast should get downgraded to "🟡 Unstable".
        forecast = {
            "confidence": 0.8,
            "fragility": 0.3,
            "risk_score": 0.8  # High risk exceeds threshold of 0.5
        }
        label = TrustEngine.confidence_gate(forecast, conf_threshold=0.5, fragility_threshold=0.7, risk_threshold=0.5)
        self.assertEqual(label, "🟡 Unstable")

    def test_confidence_gate_trusted(self):
        # With low risk, high confidence and acceptable fragility, forecast is trusted.
        forecast = {
            "confidence": 0.9,
            "fragility": 0.3,
            "risk_score": 0.2
        }
        label = TrustEngine.confidence_gate(forecast, conf_threshold=0.5, fragility_threshold=0.7, risk_threshold=0.5)
        self.assertEqual(label, "🟢 Trusted")

if __name__ == "__main__":
    unittest.main()
