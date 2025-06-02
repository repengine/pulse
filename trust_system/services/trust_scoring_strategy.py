from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class TrustScoringStrategy(ABC):
    @abstractmethod
    def score(self, forecast: Dict, memory: Optional[List[Dict]] = None) -> float:
        pass


class DefaultTrustScoringStrategy(TrustScoringStrategy):
    """
    Default trust scoring logic, extracted from TrustEngine.
    """

    def score(self, forecast: Dict, memory: Optional[List[Dict]] = None) -> float:
        from trust_system.trust_engine import compute_risk_score
        from engine.pulse_config import CONFIDENCE_THRESHOLD, USE_SYMBOLIC_OVERLAYS
        from symbolic_system.symbolic_utils import compute_symbolic_drift_penalty

        fcast = forecast.get("forecast", {})
        fragility = forecast.get("fragility", 1.0)
        symbolic_penalty = min(fragility, 1.0)
        capital_start = fcast.get("start_capital", {})
        capital_end = fcast.get("end_capital", {})
        movement_score = 0.0
        if capital_start and capital_end:
            delta_sum = sum(
                abs(capital_end.get(asset, 0) - capital_start.get(asset, 0))
                for asset in ["nvda", "msft", "ibit", "spy"]
            )
            movement_score = min(delta_sum / 1000.0, 1.0) if delta_sum else 0.0
        baseline_confidence = ((1.0 - symbolic_penalty) + movement_score) / 2.0

        risk_score = compute_risk_score(forecast, memory)
        forecast["risk_score"] = risk_score

        if memory:
            similarities = []
            for past in memory[-3:]:
                curr_change = fcast.get("symbolic_change", {})
                past_change = past.get("forecast", {}).get("symbolic_change", {})
                if curr_change and past_change:
                    common = set(curr_change.keys()).intersection(
                        set(past_change.keys())
                    )
                    if common:
                        diff = sum(abs(curr_change[k] - past_change[k]) for k in common)
                        sim = 1.0 - min(diff / len(common), 1.0)
                    else:
                        sim = 0.5
                else:
                    sim = 0.5
                similarities.append(sim)
            historical_consistency = sum(similarities) / len(similarities)
        else:
            historical_consistency = 1.0
        forecast["historical_consistency"] = historical_consistency

        is_duplicate = False
        if memory:
            for past in memory[-3:]:
                prev = past.get("forecast", {}).get("symbolic_change", {})
                curr = fcast.get("symbolic_change", {})
                if curr == prev:
                    is_duplicate = True
                    break
        novelty_score = 0.0 if is_duplicate else 1.0

        baseline_weight = 0.4
        risk_weight = 0.3
        historical_weight = 0.2
        novelty_weight = 0.1

        final_confidence = (
            baseline_weight * baseline_confidence
            + risk_weight * (1 - risk_score)
            + historical_weight * historical_consistency
            + novelty_weight * novelty_score
        )
        if USE_SYMBOLIC_OVERLAYS:
            final_confidence -= compute_symbolic_drift_penalty(forecast)
        final_confidence = round(
            min(max(final_confidence, CONFIDENCE_THRESHOLD), 1.0), 3
        )
        return final_confidence
