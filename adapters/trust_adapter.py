from interfaces.trust_interface import TrustInterface
from trust_system.trust_engine import TrustEngine

class TrustAdapter(TrustInterface):
    def __init__(self):
        self.engine = TrustEngine()

    def tag_forecast(self, forecast):
        return TrustEngine.tag_forecast(forecast)

    def confidence_gate(self, forecast, conf_threshold=0.5, fragility_threshold=0.7, risk_threshold=0.5):
        return TrustEngine.confidence_gate(forecast, conf_threshold, fragility_threshold, risk_threshold)

    def score_forecast(self, forecast, memory=None):
        return TrustEngine.score_forecast(forecast, memory)

    def check_trust_loop_integrity(self, forecasts):
        return TrustEngine.check_trust_loop_integrity(forecasts)

    def check_forecast_coherence(self, forecast_batch):
        return TrustEngine.check_forecast_coherence(forecast_batch)

    def symbolic_tag_conflicts(self, forecasts):
        return TrustEngine.symbolic_tag_conflicts(forecasts)

    def arc_conflicts(self, forecasts):
        return TrustEngine.arc_conflicts(forecasts)

    def capital_conflicts(self, forecasts, threshold=1000.0):
        return TrustEngine.capital_conflicts(forecasts, threshold)

    def lineage_arc_summary(self, forecasts):
        return TrustEngine.lineage_arc_summary(forecasts)

    def run_trust_audit(self, forecasts):
        return TrustEngine.run_trust_audit(forecasts)

    def enrich_trust_metadata(self, forecast):
        return self.engine.enrich_trust_metadata(forecast)

    def apply_all(self, forecasts, *args, **kwargs):
        return TrustEngine.apply_all(forecasts, *args, **kwargs)