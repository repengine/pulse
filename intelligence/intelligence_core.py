# === File: pulse/intelligence/intelligence_core.py ===
"""
Pulse Intelligence Core (stable v1.3)

Central orchestrator for Pulse simulation and learning cycles.
Manages the interaction between the Function Router, Simulation Executor,
Intelligence Observer, and Upgrade Sandbox Manager.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from intelligence.function_router import FunctionRouter
from intelligence.worldstate_loader import load_initial_state
from intelligence.simulation_executor import SimulationExecutor
from intelligence.intelligence_observer import Observer
from intelligence.upgrade_sandbox_manager import UpgradeSandboxManager
from engine.worldstate import (
    WorldState,
)  # Import WorldState for type hinting


class IntelligenceCore:
    """
    Central orchestrator for Pulse simulation & learning.

    Attributes:
        router: The FunctionRouter instance for dynamic function calls.
        executor: The SimulationExecutor instance for running simulations.
        observer: The Observer instance for monitoring and learning.
        sandbox: The UpgradeSandboxManager for handling upgrade proposals.
        last_worldstate: The last WorldState object from a simulation run, or None.
        loaded_modules: A list of names of modules loaded by the router.
    """

    def __init__(
        self,
        router: FunctionRouter,
        executor: SimulationExecutor,
        observer: Observer,
        sandbox: UpgradeSandboxManager,
    ) -> None:
        """
        Initializes the IntelligenceCore with injected dependencies.

        Args:
            router: The FunctionRouter instance for dynamic function calls.
            executor: The SimulationExecutor instance for running simulations.
            observer: The Observer instance for monitoring and learning.
            sandbox: The UpgradeSandboxManager for handling upgrade proposals.
        """
        self.router: FunctionRouter = router
        self.executor: SimulationExecutor = executor
        self.observer: Observer = observer
        self.sandbox: UpgradeSandboxManager = sandbox
        self.last_worldstate: Optional[WorldState] = None
        # This attribute is no longer directly managed here, consider removing if
        # unused.
        self.loaded_modules: List[str] = ([])

    # ------------------------------------------------------------------
    def load_standard_modules(self) -> None:
        """
        Loads the standard set of modules required for core operations.
        """
        self.router.load_modules(
            {
                "turn_engine": "engine.turn_engine",
                "causal_rules": "engine.causal_rules",
                "retrodiction": "engine.historical_retrodiction_runner",
                "forecast_engine": "forecast_engine.forecast_generator",  # Added forecast_engine
            }
        )
        self.loaded_modules = [
            "turn_engine",
            "causal_rules",
            "retrodiction",
            "forecast_engine",
        ]  # Updated list

    # ------------------------------------------------------------------
    def initialize_worldstate(
        self, source: Union[str, Path, None] = None, **overrides: Any
    ) -> WorldState:
        """
        Initializes the WorldState from a source and optional overrides.

        Args:
            source: Path to a baseline file (CSV or JSON) or None for default.
            **overrides: Arbitrary keyword overrides for the WorldState.

        Returns:
            The initialized WorldState object.
        """
        self.last_worldstate = load_initial_state(source or "default", **overrides)
        return self.last_worldstate

    @staticmethod
    def _extract_start_year(state: Union[WorldState, Dict[str, Any]]) -> int:
        """
        Extracts the start year from a WorldState object or dictionary representation.

        Args:
            state: The WorldState object or its dictionary representation.

        Returns:
            The start year, defaulting to 2023 if not found.
        """
        if isinstance(state, dict):
            return state.get("metadata", {}).get("start_year", 2023)
        # Assuming WorldState object has a metadata attribute that is a dictionary
        return getattr(state, "metadata", {}).get("start_year", 2023)

    # ------------------------------------------------------------------
    def run_forecast_cycle(
        self, turns: int = 12, *, _batch_tag: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs a complete forecast simulation cycle.

        Initializes WorldState if not already set, runs the simulation using the
        executor, updates the last WorldState, and performs a post-cycle audit.

        Args:
            turns: The total number of turns to simulate.
            _batch_tag: Optional tag for batch processing (internal use).

        Returns:
            A dictionary representing the snapshot of the final WorldState.
        """
        if self.last_worldstate is None:
            self.initialize_worldstate()
        # Ensure last_worldstate is not None before passing to _extract_start_year
        start_year: int = (
            self._extract_start_year(self.last_worldstate)
            if self.last_worldstate
            else 2023
        )
        # run_chunked_forecast returns Tuple[Optional[WorldState],
        # Union[List[Dict[str, Any]], Any]]
        ws_obj, _ = self.executor.run_chunked_forecast(
            start_year=start_year,
            total_turns=turns,
            chunk_size=turns,
        )
        self.last_worldstate = (
            ws_obj  # Assuming run_chunked_forecast returns a WorldState or similar
        )
        snapshot: Dict[str, Any] = (
            ws_obj.snapshot()
            if ws_obj is not None and hasattr(ws_obj, "snapshot")
            else {}
        )  # Ensure snapshot method exists and ws_obj is not None
        self._post_cycle_audit(snapshot)
        return snapshot

    def run_retrodiction_cycle(self, start_date: str, days: int = 90) -> Dict[str, Any]:
        """
        Runs a retrodiction cycle.

        Uses the simulation executor to run a retrodiction forecast.

        Args:
            start_date: The start date for retrodiction (YYYY-MM-DD).
            days: The number of days to retrodict.

        Returns:
            A dictionary representing the result of the retrodiction forecast,
            or an empty dictionary if the result is None.
        """
        # run_retrodiction_forecast returns Any, assuming it's a Dict[str, Any] or None
        result: Any = self.executor.run_retrodiction_forecast(start_date, days)
        return result or {}

    # ------------------------------------------------------------------
    def _post_cycle_audit(self, snapshot: Dict[str, Any]) -> None:
        """
        Performs post-cycle auditing, including symbolic divergence observation and upgrade proposals.

        Args:
            snapshot: The snapshot of the WorldState after a cycle.
        """
        # Ensure observe_symbolic_divergence expects a list of snapshots
        divergence_report: Dict[str, Any] = self.observer.observe_symbolic_divergence(
            [snapshot]
        )
        if upgrade_id := self.observer.propose_symbolic_upgrades_live(
            divergence_report
        ):
            print(f"[IntelligenceCore] 🚀 Upgrade proposal submitted: {upgrade_id}")
