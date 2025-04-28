# === File: pulse/intelligence/simulation_executor.py ===
from __future__ import annotations
"""Pulse Simulation Executor (stable v1.3)"""
import random
import sys
import warnings
from typing import List, Dict, Optional, Any, Callable
import numpy as np
from forecast_engine.forecast_compressor import compress_mc_samples

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
        n_paths: int = 1,
        mc_seed: Optional[int] = None,
    ) -> Any:
        # Optionally seed Monte Carlo
        if mc_seed is not None:
            random.seed(mc_seed)

        mc_samples: List[Dict[str, np.ndarray]] = []

        # Run each path
        for path_idx in range(n_paths):
            ws = self.router.run_function("turn_engine", "initialize_worldstate", start_year=start_year)
            done = 0
            while done < total_turns:
                step = min(chunk_size, total_turns - done)
                for _ in range(step):
                    self.router.run_function("turn_engine", "run_turn", state=ws)
                done += step
                if on_chunk_end:
                    on_chunk_end(done)
                print(f"[Executor] 🚀 Completed {done}/{total_turns} turns (path {path_idx+1}/{n_paths})")

            # Generate forecast dict for this path
            forecast = self.router.run_function(
                "forecast_engine", "generate_forecast", state=ws
            )
            mc_samples.append(forecast)

        # Memory guard
        total_bytes = sum(sys.getsizeof(item) for item in mc_samples)
        if total_bytes > 1_000_000_000:
            warnings.warn(
                "MC samples exceed 1 GiB; proceeding with compression may be memory-intensive"
            )

        # Compress samples into mean + 90% prediction interval
        result = compress_mc_samples(mc_samples, alpha=0.9)
        return result

    # ---------------- retrodiction ----------------
    def run_retrodiction_forecast(self, start_date: str, days: int = 30):  # noqa: D401
        """Try retrodiction runner; fallback to simulator_core.simulate_forward."""
        try:
            return self.router.run_function(
                "retrodiction", "run_retrodiction_test", start_date
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

