from typing import Dict, List, Optional, Callable
import logging

logger = logging.getLogger("pulse.trust")

class TrustEnrichmentService:
    """
    Service for enriching trust metadata on forecasts.
    Extracts enrichment logic from TrustEngine for SRP.
    """
    def __init__(self, plugins: Optional[List[Callable[[Dict], None]]] = None):
        self.plugins = plugins or []

    def register_plugin(self, plugin_fn: Callable[[Dict], None]):
        self.plugins.append(plugin_fn)

    def enrich(self, forecast: Dict, current_state: Optional[Dict] = None, memory: Optional[List[Dict]] = None,
               arc_drift: Optional[Dict[str, int]] = None, regret_log: Optional[List[Dict]] = None,
               license_enforcer=None, license_explainer=None) -> Dict:
        # Import enrichment helpers locally to avoid circular imports
        from trust_system.trust_engine import (
            _enrich_fragility, _enrich_retrodiction, _enrich_alignment,
            _enrich_attention, _enrich_regret, _enrich_license
        )
        _enrich_fragility(forecast)
        _enrich_retrodiction(forecast, current_state)
        _enrich_alignment(forecast, current_state, memory)
        _enrich_attention(forecast, arc_drift)
        _enrich_regret(forecast, regret_log)
        _enrich_license(forecast, license_enforcer, license_explainer)
        for plugin in self.plugins:
            try:
                plugin(forecast)
            except Exception as e:
                logger.warning(f"[TrustEnrich] Plugin {plugin.__name__} failed: {e}")
        return forecast