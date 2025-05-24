from interfaces.symbolic_interface import SymbolicInterface
from symbolic_system import symbolic_executor, symbolic_alignment_engine


class SymbolicAdapter(SymbolicInterface):
    def apply_symbolic_upgrade(self, forecast, upgrade_map):
        return symbolic_executor.apply_symbolic_upgrade(forecast, upgrade_map)

    def rewrite_forecast_symbolics(self, forecasts, upgrade_plan):
        return symbolic_executor.rewrite_forecast_symbolics(forecasts, upgrade_plan)

    def generate_upgrade_trace(self, original, mutated):
        return symbolic_executor.generate_upgrade_trace(original, mutated)

    def log_symbolic_mutation(self, trace, path="logs/symbolic_mutation_log.jsonl"):
        return symbolic_executor.log_symbolic_mutation(trace, path)

    def compute_alignment(self, symbolic_tag, variables):
        return symbolic_alignment_engine.compute_alignment(symbolic_tag, variables)

    def alignment_report(self, tag, variables):
        return symbolic_alignment_engine.alignment_report(tag, variables)
