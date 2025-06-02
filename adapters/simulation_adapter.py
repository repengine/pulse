from interfaces.simulation_interface import SimulationInterface
from engine import simulator_core


class SimulationAdapter(SimulationInterface):
    def reset_state(self, state):
        return simulator_core.reset_state(state)

    def simulate_turn(self, state, *args, **kwargs):
        return simulator_core.simulate_turn(state, *args, **kwargs)

    def simulate_forward(self, state, *args, **kwargs):
        return simulator_core.simulate_forward(state, *args, **kwargs)

    def simulate_backward(self, state, *args, **kwargs):
        return simulator_core.simulate_backward(state, *args, **kwargs)

    def simulate_counterfactual(self, state, *args, **kwargs):
        return simulator_core.simulate_counterfactual(state, *args, **kwargs)

    def validate_variable_trace(self, trace, *args, **kwargs):
        return simulator_core.validate_variable_trace(trace, *args, **kwargs)

    def get_overlays_dict(self, state):
        return simulator_core.get_overlays_dict(state)

    def log_to_file(self, data, path):
        return simulator_core.log_to_file(data, path)

    def reverse_rule_engine(self, state, overlays, variables, step=1):
        return simulator_core.reverse_rule_engine(state, overlays, variables, step)
