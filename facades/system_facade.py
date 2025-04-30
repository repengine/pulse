from service_registry import ServiceRegistry

class SystemFacade:
    @staticmethod
    def run_simulation_with_trust(state, turns=5, use_symbolism=True, return_mode="summary"):
        simulation = ServiceRegistry.get_simulation()
        trust = ServiceRegistry.get_trust()
        results = simulation.simulate_forward(state, turns=turns, use_symbolism=use_symbolism, return_mode=return_mode)
        # Enrich each result with trust metadata
        for result in results:
            trust.enrich_trust_metadata(result)
        return results

    @staticmethod
    def analyze_forecast_symbolics(forecast, upgrade_map=None):
        symbolic = ServiceRegistry.get_symbolic()
        if upgrade_map:
            upgraded = symbolic.apply_symbolic_upgrade(forecast, upgrade_map)
            trace = symbolic.generate_upgrade_trace(forecast, upgraded)
            return {"upgraded": upgraded, "trace": trace}
        else:
            return symbolic.alignment_report(forecast.get("symbolic_tag", ""), forecast.get("variables", {}))