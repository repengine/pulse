# === File: pulse/intelligence/simulation_executor.py ===
from __future__ import annotations
"""Pulse Simulation Executor (stable v1.3)"""
from typing import Any, Callable, Optional

from intelligence.function_router import FunctionRouter

class SimulationExecutor:
    def __init__(self, router: Optional[FunctionRouter] = None):
        self.router = router or FunctionRouter()

    # ---------------- forward forecast ----------------
    def run_chunked_forecast(
        self,
        start_year: int,
        total_turns: int = 312,
        chunk_size: int = 52,
        *,
        on_chunk_end: Optional[Callable[[int], None]] = None,
    ) -> Any:  # returns WorldState
        ws = self.router.run_function("turn_engine", "initialize_worldstate", start_year=start_year)
        done = 0
        while done < total_turns:
            step = min(chunk_size, total_turns - done)
            for _ in range(step):
                self.router.run_function("turn_engine", "run_turn", state=ws)
            done += step
            if on_chunk_end:
                on_chunk_end(done)
            print(f"[Executor] 🚀 Completed {done}/{total_turns} turns")
        return ws

    # ---------------- retrodiction ----------------
    def run_retrodiction_forecast(self, start_date: str, days: int = 30):  # noqa: D401
        """Try retrodiction runner; fallback to simulator_core.simulate_forward."""
        try:
            return self.router.run_function(
                "retrodiction", "run_retrodiction_test", start_date=start_date, days=days
            )
        except Exception:
            # Fallback using simulate_forward in simulator_core
            try:
                loader = self.router.run_function("retrodiction", "get_snapshot_loader", start_date, days)
            except Exception:
                loader = None
            return self.router.run_function(
                "simulation_engine.simulator_core", "simulate_forward",
                state=self.router.run_function("turn_engine", "initialize_worldstate"),
                turns=days,
                retrodiction_mode=True,
                retrodiction_loader=loader,
            )
