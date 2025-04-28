""" 
turn_engine.py

Controls the simulation loop at the turn level.

Responsibilities:
- Apply symbolic decay to each overlay (e.g., hope, trust, despair)
- Run causal rules via causal_rules.py (e.g., inflation → despair)
- Execute auditable causal rule engine (via rule_engine.py)
- Optionally allow custom rule injection (rule_fn)
- Increment turn and return detailed audit trail for memory or scoring

Author: Pulse v0.20
"""

from simulation_engine.worldstate import WorldState
from simulation_engine.state_mutation import decay_overlay
from simulation_engine.causal_rules import apply_causal_rules
from simulation_engine.rule_engine import run_rules
from typing import Callable, Optional, Dict
from core.path_registry import PATHS
assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

# Required imports for trace logging
from memory.trace_audit_engine import assign_trace_metadata, register_trace_to_memory
from core.pulse_config import ENABLE_TRACE_LOGGING

#imports for retrodiction snapshot injection during turns
from core.variable_accessor import set_variable
from simulation_engine.worldstate import WorldState
from simulation_engine.simulator_core import simulate_forward as RetrodictionLoader


TURN_LOG_PATH = PATHS.get("TURN_LOG_PATH", PATHS["WORLDSTATE_LOG_DIR"])

AUTO_ENFORCE = False  # Set to True to enable post-turn license enforcement

# --- quick PulseCore wrapper ---

def initialize_worldstate(start_year: Optional[int] = None, **kwargs) -> WorldState:
    """
    Lightweight factory so IntelligenceCore can bootstrap without
    importing WorldState directly.
    """
    state = WorldState(**kwargs)
    if start_year is not None:
        state.metadata["start_year"] = start_year
    return state

def run_turn(
    state: WorldState,
    rule_fn: Optional[Callable[[WorldState], None]] = None,
    decay_rate: float = 0.01,
    verbose: bool = True,
    learning_engine=None,
    injection_snapshot: Optional[Dict[str, float]] = None
) -> list[dict]:
    ...
    if injection_snapshot:
        for var, val in injection_snapshot.items():
            set_variable(state, var, val)
  
    """
    Executes one simulation turn in the Pulse engine.

    Steps:
    1. Apply symbolic decay to all overlays
    2. Execute narrative/capital effects via causal_rules
    3. Execute structured causal rules (auditable)
    4. Run optional external logic
    5. Increment turn
    6. Log state changes for traceability

    Returns:
        list: Rule audit log (rule ID, tags, deltas)
    """
    try:
        # Step 1: Symbolic decay (for each overlay variable)
        for overlay_name in state.overlays.as_dict():
            decay_overlay(state, overlay_name, rate=decay_rate)
        state.log_event("Symbolic decay applied to overlays.")
    except Exception as e:
        state.log_event(f"[ERROR] Symbolic decay failed: {e}")

    try:
        # Step 2: Apply symbolic and capital shifts (non-audited)
        apply_causal_rules(state)
        state.log_event("Causal rules applied.")
    except Exception as e:
        state.log_event(f"[ERROR] Causal rules failed: {e}")

    try:
        # Step 3: Run structured rule engine and capture audit log
        rule_execution_log = run_rules(state, verbose=verbose)
        state.log_event("Structured rule engine executed.")
    except Exception as e:
        state.log_event(f"[ERROR] Rule engine failed: {e}")
        rule_execution_log = []

    # Step 4: Optional injected logic (for testing or external simulation branches)
    if rule_fn:
        try:
            rule_fn(state)
            state.log_event("Custom rule_fn executed.")
        except Exception as e:
            state.log_event(f"[ERROR] Custom rule_fn failed: {e}")

    # Step 5: Advance the simulation
    state.advance_turn()
    state.log_event("Turn incremented.")

    
    # Optional: Post-turn license enforcement (if enabled)
    # Removed state.forecasts logic because WorldState has no 'forecasts' attribute
    # if AUTO_ENFORCE:
    #     from trust_system.license_enforcer import annotate_forecasts, filter_licensed
    #     if hasattr(state, "forecasts"):
    #         state.forecasts = annotate_forecasts(state.forecasts)
    #         state.forecasts = filter_licensed(state.forecasts)

    # Call learning hook with a snapshot of the state
    if learning_engine is not None:
        learning_engine.on_simulation_turn_end(state.snapshot())

    # Trace logging (if enabled)
    if ENABLE_TRACE_LOGGING:
        sim_input = {
            "state": state.to_dict(),  # assumes to_dict exists or serialize manually
            "decay_rate": decay_rate,
            "rule_fn": rule_fn.__name__ if rule_fn else None,
        }
        sim_output = {
            "overlays": state.overlays,
            "variables": state.variables,
            "trust": getattr(state, "trust", None),  # optional
            "forks": getattr(state, "forks", []),
        }
        trace_metadata = assign_trace_metadata(sim_input, sim_output)
        register_trace_to_memory(trace_metadata)

    return rule_execution_log


