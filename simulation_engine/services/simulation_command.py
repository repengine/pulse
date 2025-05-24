from abc import ABC, abstractmethod
from typing import Any


class SimulationCommand(ABC):
    @abstractmethod
    def execute(self, state: Any) -> None:
        pass


class DecayCommand(SimulationCommand):
    def execute(self, state: Any) -> None:
        from simulation_engine.state_mutation import decay_overlay

        for overlay_name, _ in state.overlays.items():
            decay_overlay(state, overlay_name)


class RuleCommand(SimulationCommand):
    def execute(self, state: Any) -> None:
        from simulation_engine.rule_engine import run_rules

        run_rules(state)


class SymbolicTagCommand(SimulationCommand):
    def execute(self, state: Any) -> None:
        try:
            from symbolic_system.symbolic_state_tagger import tag_symbolic_state

            overlays_now = (
                state.overlays.as_dict()
                if hasattr(state.overlays, "as_dict")
                else state.overlays
            )
            sim_id_val = getattr(state, "sim_id", None) or ""
            tag_result = tag_symbolic_state(
                overlays_now, sim_id=sim_id_val, turn=getattr(state, "turn", -1)
            )
            state.symbolic_tag = tag_result.get("symbolic_tag", "")
            state.arc_label = tag_result.get("arc_label", "")
        except Exception:
            state.symbolic_tag = "error"
            state.arc_label = "Unknown"
