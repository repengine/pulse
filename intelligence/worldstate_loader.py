"""worldstate_loader.py
Minimal-impact loader that returns a fully-populated `WorldState`.

Phase-1 features
----------------
* Reads an optional CSV / JSON baseline   (defaults to data/baselines/default.csv).
* Falls back to a vanilla `WorldState`    if the file is missing.
* Injects variables supplied by the new   VariableIngestion layer (see below).
* Validates the result and reports gaps   via `VariableRegistry.flag_missing_variables`.

Future expansion
----------------
* Historical snapshot support (retrodiction).
* Multi-source merge strategy (baseline
  file + live API pulls + user overrides).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from simulation_engine.worldstate import WorldState
from core.variable_registry import registry  # singleton instance
from iris.variable_ingestion import ingest_live_variables  # lightweight wrapper


# ----------------------------------------------------------------------#
# Public helpers                                                        #
# ----------------------------------------------------------------------#
def load_initial_state(
    source: str | Path | None = None,
    *,
    inject_live: bool = True,
    **overrides: Dict[str, Any],
) -> WorldState:
    """Return a fresh `WorldState`, populated from a baseline file + live signals.

    Parameters
    ----------
    source : str | Path | None
        Path to CSV or JSON with `name,value` pairs.  If None or file
        missing it silently falls back to defaults.
    inject_live : bool
        When True (default) the loader calls `ingest_live_variables`
        to fetch a handful of macro & market series so the sim starts
        with *real* data straight away.
    **overrides
        Arbitrary keyword overrides forwarded to `WorldState`.
    """
    baseline_vars: Dict[str, float] = {}

    if source is None:
        source = Path("data/baselines/default.csv")
    source_path = Path(source)
    if source_path.exists():
        try:
            df = pd.read_csv(source_path) if source_path.suffix == ".csv" else pd.read_json(source_path)
            baseline_vars = {str(k): float(v) for k, v in zip(df.iloc[:, 0], df.iloc[:, 1])}
        except Exception as exc:  # noqa: BLE001
            print(f"[WS-LOADER] Failed to read baseline {source_path}: {exc}")

    # Merge overrides last (highest precedence)
    baseline_vars |= overrides.pop("variables", {})

    # Only pass valid keyword arguments to WorldState
    valid_keys = {"turn", "sim_id", "overlays", "capital", "event_log", "metadata"}
    filtered_overrides = {k: v for k, v in overrides.items() if k in valid_keys}

    # Optionally inject live variables
    live_vars = {}
    if inject_live:
        live_vars = ingest_live_variables()
        baseline_vars.update(live_vars)

    # Wrap baseline_vars in Variables if needed
    from simulation_engine.worldstate import Variables
    state = WorldState(variables=Variables(baseline_vars), **filtered_overrides)
    state.metadata["baseline_file"] = str(source_path)
    if inject_live and live_vars:
        state.metadata["live_ingested"] = list(live_vars.keys())

    # Report any missing keys registered in VariableRegistry
    if (missing := registry.flag_missing_variables(state.variables.as_dict())):
        state.log_event(f"[WS-LOADER] Missing baseline variables: {missing}")

    return state


# Place-holder for future historical snapshot logic
def load_historical_snapshot(date: str, **kwargs) -> WorldState:  # noqa: ANN001
    snapshot = load_initial_state(**kwargs)
    snapshot.metadata["historical_date"] = date
    return snapshot
