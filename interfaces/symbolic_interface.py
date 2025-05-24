from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SymbolicInterface(ABC):
    @abstractmethod
    def apply_symbolic_upgrade(self, forecast: Dict, upgrade_map: Dict) -> Dict:
        pass

    @abstractmethod
    def rewrite_forecast_symbolics(
        self, forecasts: List[Dict], upgrade_plan: Dict
    ) -> List[Dict]:
        pass

    @abstractmethod
    def generate_upgrade_trace(self, original: Dict, mutated: Dict) -> Dict:
        pass

    @abstractmethod
    def log_symbolic_mutation(
        self, trace: Dict, path: str = "logs/symbolic_mutation_log.jsonl"
    ):
        pass

    @abstractmethod
    def compute_alignment(self, symbolic_tag: str, variables: Dict[str, Any]) -> float:
        pass

    @abstractmethod
    def alignment_report(self, tag: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        pass
