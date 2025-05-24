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
from typing import Any, Dict, Optional

import pandas as pd

from simulation_engine.worldstate import WorldState
from core.variable_registry import registry  # singleton instance
from iris.variable_ingestion import ingest_live_variables  # lightweight wrapper
from intelligence.intelligence_config import (
    WORLDSTATE_DEFAULT_SOURCE,
    WORLDSTATE_INJECT_LIVE_DEFAULT,
)


# ----------------------------------------------------------------------#
# Public helpers                                                        #
# ----------------------------------------------------------------------#
def load_initial_state(
    source: str | Path | None = None,
    *,
    inject_live: bool = WORLDSTATE_INJECT_LIVE_DEFAULT,
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
        source = Path(WORLDSTATE_DEFAULT_SOURCE)
    source_path = Path(source)
    if source_path.exists():
        try:
            df = (
                pd.read_csv(source_path)
                if source_path.suffix == ".csv"
                else pd.read_json(source_path)
            )
            baseline_vars = {
                str(k): float(v) for k, v in zip(df.iloc[:, 0], df.iloc[:, 1])
            }
        except Exception as exc:  # noqa: BLE001
            print(f"[WS-LOADER] Failed to read baseline {source_path}: {exc}")

    # Merge overrides last (highest precedence)
    baseline_vars |= overrides.pop("variables", {})

    # Separate WorldState constructor args from other overrides like metadata
    valid_constructor_keys = {"turn", "sim_id", "overlays", "capital", "event_log"}
    constructor_args = {
        k: v for k, v in overrides.items() if k in valid_constructor_keys
    }
    metadata_override = overrides.get("metadata", {})  # Extract metadata if provided

    # Optionally inject live variables
    live_vars = {}
    if inject_live:
        live_vars = ingest_live_variables()
        baseline_vars.update(live_vars)  # Live vars can overwrite baseline

    # Create the WorldState instance explicitly passing args with refined type checks
    from simulation_engine.worldstate import (
        Variables,
        SymbolicOverlays,
        CapitalExposure,
    )  # Local import

    ws_args = {}
    turn_val = constructor_args.get("turn")
    ws_args["turn"] = int(turn_val) if isinstance(turn_val, (int, float, str)) else 0

    sim_id_val = constructor_args.get("sim_id")
    if isinstance(sim_id_val, str) and sim_id_val:
        ws_args["sim_id"] = sim_id_val
    # else: let default factory handle it

    overlays_val = constructor_args.get("overlays")
    if isinstance(overlays_val, (dict, SymbolicOverlays)):
        ws_args["overlays"] = overlays_val  # Pass dict or object, __post_init__ handles
    # else: let default factory handle it

    capital_val = constructor_args.get("capital")
    if isinstance(capital_val, (dict, CapitalExposure)):
        ws_args["capital"] = capital_val  # Pass dict or object, __post_init__ handles
    # else: let default factory handle it

    event_log_val = constructor_args.get("event_log")
    if isinstance(event_log_val, list):
        ws_args["event_log"] = event_log_val  # Pass list
    # else: let default factory handle it

    state = WorldState(variables=Variables(baseline_vars), **ws_args)

    # Set initial metadata and merge overrides
    state.metadata["baseline_file"] = str(source_path)
    if inject_live and live_vars:
        state.metadata["live_ingested"] = list(live_vars.keys())
    if metadata_override:
        state.metadata.update(metadata_override)  # Apply metadata overrides

    # Report any missing keys registered in VariableRegistry
    if missing := registry.flag_missing_variables(state.variables.as_dict()):
        state.log_event(f"[WS-LOADER] Missing baseline variables: {missing}")

    return state


# ----------------------------------------------------------------------#
# Historical Snapshot Loading                                           #
# ----------------------------------------------------------------------#


def load_historical_snapshot(
    date: str,
    snapshot_dir: str | Path = "snapshots",
    **overrides: Dict[str, Any],
) -> WorldState:
    """Return a `WorldState` populated from a historical snapshot file.

    Assumes snapshot files are named `worldstate_{date}.(csv|json)`
    within the specified `snapshot_dir`.

    Parameters
    ----------
    date : str
        The date identifier for the snapshot (e.g., "YYYY-MM-DD").
    snapshot_dir : str | Path
        Directory containing the historical snapshot files.
    **overrides
        Arbitrary keyword overrides forwarded to `WorldState`, including
        a potential 'variables' dict which takes precedence over the snapshot file.

    Returns
    -------
    WorldState
        The populated world state object.

    Raises
    ------
    FileNotFoundError
        If no snapshot file (CSV or JSON) is found for the given date.
    Exception
        If there's an error reading the snapshot file.
    """
    snapshot_path_base = Path(snapshot_dir) / f"worldstate_{date}"
    snapshot_path_csv = snapshot_path_base.with_suffix(".csv")
    snapshot_path_json = snapshot_path_base.with_suffix(".json")

    snapshot_path: Optional[Path] = None
    if snapshot_path_csv.exists():
        snapshot_path = snapshot_path_csv
    elif snapshot_path_json.exists():
        snapshot_path = snapshot_path_json
    else:
        raise FileNotFoundError(
            f"No historical snapshot found for date '{date}' at "
            f"{snapshot_path_csv} or {snapshot_path_json}"
        )

    baseline_vars: Dict[str, float] = {}
    state: Optional[WorldState] = None  # Initialize state to None

    try:
        df = (
            pd.read_csv(snapshot_path)
            if snapshot_path.suffix == ".csv"
            else pd.read_json(snapshot_path)
        )
        # Assume first column is name, second is value
        baseline_vars = {str(k): float(v) for k, v in zip(df.iloc[:, 0], df.iloc[:, 1])}

        # Variables override takes precedence
        baseline_vars |= overrides.pop("variables", {})

        # Separate WorldState constructor args from other overrides like metadata
        valid_constructor_keys = {"turn", "sim_id", "overlays", "capital", "event_log"}
        constructor_args = {
            k: v for k, v in overrides.items() if k in valid_constructor_keys
        }
        metadata_override = overrides.get(
            "metadata", {}
        )  # Extract metadata if provided

        # Create the WorldState instance explicitly passing args with refined type checks
        from simulation_engine.worldstate import (
            Variables,
            SymbolicOverlays,
            CapitalExposure,
        )  # Local import

        ws_args = {}
        turn_val = constructor_args.get("turn")
        ws_args["turn"] = (
            int(turn_val) if isinstance(turn_val, (int, float, str)) else 0
        )

        sim_id_val = constructor_args.get("sim_id")
        if isinstance(sim_id_val, str) and sim_id_val:
            ws_args["sim_id"] = sim_id_val
        # else: let default factory handle it

        overlays_val = constructor_args.get("overlays")
        if isinstance(overlays_val, (dict, SymbolicOverlays)):
            ws_args["overlays"] = (
                overlays_val  # Pass dict or object, __post_init__ handles
            )
        # else: let default factory handle it

        capital_val = constructor_args.get("capital")
        if isinstance(capital_val, (dict, CapitalExposure)):
            ws_args["capital"] = (
                capital_val  # Pass dict or object, __post_init__ handles
            )
        # else: let default factory handle it

        event_log_val = constructor_args.get("event_log")
        if isinstance(event_log_val, list):
            ws_args["event_log"] = event_log_val  # Pass list
        # else: let default factory handle it

        state = WorldState(variables=Variables(baseline_vars), **ws_args)

        # Set initial metadata and merge overrides (inside try block)
        state.metadata["baseline_file"] = str(snapshot_path)
        state.metadata["historical_date"] = date
        state.metadata["load_type"] = "historical_snapshot"
        if metadata_override:
            state.metadata.update(metadata_override)  # Apply metadata overrides

        # Report any missing keys registered in VariableRegistry (inside try block)
        # Note: This compares against the *current* registry, which might have
        # evolved since the snapshot was taken.
        if missing := registry.flag_missing_variables(state.variables.as_dict()):
            state.log_event(
                f"[WS-LOADER-HISTORICAL] Missing registered variables in snapshot: {missing}"
            )

    except Exception as exc:
        print(
            f"[WS-LOADER-HISTORICAL] Failed processing snapshot {snapshot_path}: {exc}"
        )
        # Re-raise to signal failure
        raise exc

    # If we reach here, state must have been assigned successfully
    if state is None:
        # This should theoretically not happen if exceptions are raised correctly
        raise RuntimeError("Failed to create WorldState from historical snapshot.")
    return state
