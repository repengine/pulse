from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SimulationInterface(ABC):
    @abstractmethod
    def reset_state(self, state: Any) -> None:
        pass

    @abstractmethod
    def simulate_turn(self, state: Any, *args, **kwargs) -> Dict:
        pass

    @abstractmethod
    def simulate_forward(self, state: Any, *args, **kwargs) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def simulate_backward(self, state: Any, *args, **kwargs) -> Dict:
        pass

    @abstractmethod
    def simulate_counterfactual(self, state: Any, *args, **kwargs) -> Dict:
        pass

    @abstractmethod
    def validate_variable_trace(self, trace: Any, *args, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_overlays_dict(self, state: Any) -> Dict[str, float]:
        pass

    @abstractmethod
    def log_to_file(self, data: dict, path: str):
        pass

    @abstractmethod
    def reverse_rule_engine(
        self,
        state: Any,
        overlays: Dict[str, float],
        variables: Dict[str, float],
        step: int = 1,
    ):
        pass
