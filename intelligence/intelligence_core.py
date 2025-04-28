# === File: pulse/intelligence/intelligence_core.py ===
from __future__ import annotations
"""Pulse Intelligence Core (stable v1.3)"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from intelligence.function_router import FunctionRouter
from intelligence.worldstate_loader import load_initial_state
from intelligence.simulation_executor import SimulationExecutor
from intelligence.intelligence_observer import Observer
from intelligence.upgrade_sandbox_manager import UpgradeSandboxManager

class IntelligenceCore:
    """Central orchestrator for Pulse simulation & learning."""

    def __init__(self, additional_paths: Optional[List[str]] = None):
        self.router = FunctionRouter(additional_paths)
        self.executor = SimulationExecutor(self.router)
        self.observer = Observer()
        self.sandbox = UpgradeSandboxManager()
        self.last_worldstate: Any | None = None
        self.loaded_modules: List[str] = []

    # ------------------------------------------------------------------
    def load_standard_modules(self) -> None:
        self.router.load_modules({
            "turn_engine": "simulation_engine.turn_engine",
            "causal_rules": "simulation_engine.causal_rules",
            "retrodiction": "simulation_engine.historical_retrodiction_runner",
        })
        self.loaded_modules = ["turn_engine", "causal_rules", "retrodiction"]

    # ------------------------------------------------------------------
    def initialize_worldstate(self, source: str | Path | None = None, **ov) -> Any:  # noqa: ANN001
        self.last_worldstate = load_initial_state(source or "default", **ov)
        return self.last_worldstate

    @staticmethod
    def _extract_start_year(state) -> int:  # noqa: ANN001
        if isinstance(state, dict):
            return state.get("metadata", {}).get("start_year", 2023)
        return getattr(state, "metadata", {}).get("start_year", 2023)

    # ------------------------------------------------------------------
    def run_forecast_cycle(self, turns: int = 12, *, _batch_tag: str | None = None) -> Dict[str, Any]:
        if self.last_worldstate is None:
            self.initialize_worldstate()
        ws_obj = self.executor.run_chunked_forecast(
            start_year=self._extract_start_year(self.last_worldstate),
            total_turns=turns,
            chunk_size=turns,
        )
        self.last_worldstate = ws_obj
        snapshot = ws_obj.snapshot()
        self._post_cycle_audit(snapshot)
        return snapshot

    def run_retrodiction_cycle(self, start_date: str, days: int = 90) -> Dict[str, Any]:  # noqa: D401
        return self.executor.run_retrodiction_forecast(start_date, days) or {}

    # ------------------------------------------------------------------
    def _post_cycle_audit(self, snapshot: Dict[str, Any]) -> None:  # noqa: ANN001
        if upgrade_id := self.observer.propose_symbolic_upgrades_live(
            self.observer.observe_symbolic_divergence([snapshot])
        ):
            print(f"[IntelligenceCore] 🚀 Upgrade proposal submitted: {upgrade_id}")