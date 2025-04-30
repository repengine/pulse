from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional

class TrustInterface(ABC):
    @abstractmethod
    def tag_forecast(self, forecast: Dict) -> Dict:
        pass

    @abstractmethod
    def confidence_gate(self, forecast: Dict, conf_threshold=0.5, fragility_threshold=0.7, risk_threshold=0.5) -> str:
        pass

    @abstractmethod
    def score_forecast(self, forecast: Dict, memory: Optional[List[Dict]] = None) -> float:
        pass

    @abstractmethod
    def check_trust_loop_integrity(self, forecasts: List[Dict]) -> List[str]:
        pass

    @abstractmethod
    def check_forecast_coherence(self, forecast_batch: List[Dict]) -> Tuple[str, List[str]]:
        pass

    @abstractmethod
    def symbolic_tag_conflicts(self, forecasts: List[Dict]) -> List[Tuple[str, str, str]]:
        pass

    @abstractmethod
    def arc_conflicts(self, forecasts: List[Dict]) -> List[Tuple[str, str, str]]:
        pass

    @abstractmethod
    def capital_conflicts(self, forecasts: List[Dict], threshold: float = 1000.0) -> List[Tuple[str, str, str]]:
        pass

    @abstractmethod
    def lineage_arc_summary(self, forecasts: List[Dict]) -> Dict:
        pass

    @abstractmethod
    def run_trust_audit(self, forecasts: List[Dict]) -> Dict:
        pass

    @abstractmethod
    def enrich_trust_metadata(self, forecast: Dict) -> Dict:
        pass

    @abstractmethod
    def apply_all(self, forecasts: List[Dict], *args, **kwargs) -> List[Dict]:
        pass