"""
Module: simulator_core.py
Pulse Version: v0.099.999
Location: pulse/simulation_engine/

Core simulation engine for Pulse. Supports turn-by-turn forward simulation
with optional symbolic logic and runtime tracing.

Usage:
    ws = WorldState()
    ws.sim_id = "demo_sim"
    output = simulate_forward(ws, turns=5, use_symbolism=True, return_mode="summary")
    for r in output:
        print(f"Turn {r['turn']} | Δ: {r['deltas']} | Tag: {r.get('symbolic_tag', '—')}")

Features:
- Symbolic logic toggle (`use_symbolism=True`)
- Tracks deltas in overlays per turn
- Logs symbolic tags + trace (optional)
- Prepares trust layer for future expansion
- Supports extended return mode ("summary", "full")
- Type annotations and input validation
- Extensible logger/callback support

Expected WorldState structure:
- overlays: Dict[str, float] (e.g., {"hope": 0.5, "despair": 0.2, ...})
- variables: Dict[str, float]
- turn: int
- events: List[str]

TODO:
- Add checkpointing (save/load state mid-run)
- Add schema validation for overlays/variables
- Add simulation hooks (pre/post turn, pre/post simulation)
- Add batch/parallel simulation support
- Add CLI entry point for simulation runs
- Add unit tests and validation utilities
- Add support for simulation seeding/reproducibility
- Add overlay/variable schema documentation and enforcement

Author: Pulse AI Engine
"""

from simulation_engine.worldstate import WorldState
from simulation_engine.state_mutation import decay_overlay
from simulation_engine.rule_engine import run_rules
from output.forecast_episode_logger import log_episode_event  # optional
# Use relative import if possible, fallback to absolute
try:
    from symbolic_system.symbolic_state_tagger import tag_symbolic_state
except ImportError:
    from main.symbolic_system.symbolic_state_tagger import tag_symbolic_state

from symbolic_system.symbolic_trace_scorer import score_symbolic_trace  # Add for arc scoring
from simulation_engine.utils.simulation_trace_logger import log_simulation_trace  # updated path
from simulation_engine.rules.reverse_rule_mapper import match_rule_by_delta       # updated path
from src.engine import LearningEngine, log_learning_event

from typing import Dict, List, Any, Literal, Optional, Callable
from datetime import datetime

def _validate_overlay(overlay: dict) -> bool:
    """Validate overlay dict: all values must be float/int and keys are non-empty strings."""
    if not isinstance(overlay, dict):
        return False
    for k, v in overlay.items():
        if not isinstance(k, str) or not k:
            return False
        if not isinstance(v, (float, int)):
            return False
    return True

def _copy_overlay(overlay: Dict[str, float]) -> Dict[str, float]:
    """Helper to copy overlay dict safely."""
    return {k: float(v) for k, v in overlay.items()}

def reset_state(state: WorldState) -> None:
    """Reset overlays, variables, turn, and events for a fresh simulation."""
    # Optionally, reset capital and log as well if present
    state.overlays = {k: 0.0 for k in getattr(state, 'overlays', {})}
    state.variables = {k: 0.0 for k in getattr(state, 'variables', {})}
    if hasattr(state, 'capital'):
        state.capital = {k: 0.0 for k in getattr(state, 'capital', {})}
    state.turn = 0
    state.events = []
    if hasattr(state, 'log'):
        state.log = []

def simulate_turn(
    state: WorldState,
    use_symbolism: bool = True,
    return_mode: Literal["summary", "full"] = "summary",
    logger: Optional[Callable[[str], None]] = None,
    learning_engine=None
) -> Dict[str, Any]:
    """
    Simulates one turn of state mutation:
    - Applies decay and rules
    - Optionally logs symbolic tag and memory snapshot
    - Returns trace output

    Args:
        state (WorldState): simulation object
        use_symbolism (bool): enable symbolic diagnostics
        return_mode (str): "summary" or "full"
        logger (callable): optional logger for messages
        learning_engine: optional learning engine for hooks

    Returns:
        Dict: turn log with deltas, overlays, symbolic tags
    """
    if not isinstance(state, WorldState):
        raise TypeError("state must be a WorldState instance")
    pre_overlay = _copy_overlay(getattr(state, 'overlays', {}))
    if not _validate_overlay(pre_overlay):
        raise ValueError("Invalid overlay structure before turn")
    try:
        decay_overlay(state)
    except Exception as e:
        msg = f"[SIM] Decay error: {e}"
        if logger: logger(msg)
        state.log_event(msg)
    try:
        run_rules(state)
    except Exception as e:
        msg = f"[SIM] Rule engine error: {e}"
        if logger: logger(msg)
        state.log_event(msg)

    overlays_now = getattr(state, 'overlays', {})
    if not _validate_overlay(overlays_now):
        msg = "[SIM] Warning: overlays structure invalid after turn."
        if logger: logger(msg)
        state.log_event(msg)
    missing_keys = set(pre_overlay) - set(overlays_now)
    if missing_keys:
        msg = f"[SIM] Warning: overlays missing keys after turn: {missing_keys}"
        if logger: logger(msg)
        state.log_event(msg)
    # Compute overlay deltas for each key in pre_overlay
    output = {
        "turn": getattr(state, 'turn', -1),
        "timestamp": datetime.utcnow().isoformat(),
        "overlays": _copy_overlay(overlays_now),
        "deltas": {
            k: round(overlays_now.get(k, 0.0) - pre_overlay[k], 3) for k in pre_overlay
        }
    }

    if use_symbolism:
        try:
            tag = tag_symbolic_state(overlays_now, sim_id=getattr(state, 'sim_id', None), turn=getattr(state, 'turn', -1))
            output["symbolic_tag"] = tag.get("symbolic_tag", "N/A")
            log_episode_event(overlays_now, sim_id=getattr(state, 'sim_id', None), turn=getattr(state, 'turn', -1), tag=output["symbolic_tag"])
        except Exception as e:
            msg = f"[SIM] Symbolic system error: {e}"
            if logger: logger(msg)
            state.log_event(msg)
            output["symbolic_tag"] = "error"

    if return_mode == "full":
        output["worldstate_snapshot"] = {
            "vars": dict(getattr(state, 'variables', {})),
            "overlays": _copy_overlay(overlays_now),
            "event_log": list(getattr(state, 'events', [])[-3:])  # last few entries
        }

    msg = f"[SIM] Turn {getattr(state, 'turn', -1)} complete."
    if logger: logger(msg)
    state.log_event(msg)
    state.turn = getattr(state, 'turn', 0) + 1

    if learning_engine is None:
        # Use global learning engine if not provided
        try:
            global_learning_engine = LearningEngine()
            global_learning_engine.on_simulation_turn_end(state.snapshot())
        except Exception as e:
            if logger: logger(f"[SIM] Learning engine error: {e}")
            state.log_event(f"[SIM] Learning engine error: {e}")
    else:
        try:
            learning_engine.on_simulation_turn_end(state.snapshot())
        except Exception as e:
            if logger: logger(f"[SIM] Learning engine error: {e}")
            state.log_event(f"[SIM] Learning engine error: {e}")

    return output

def simulate_forward(
    state: WorldState,
    turns: int = 5,
    use_symbolism: bool = True,
    return_mode: Literal["summary", "full"] = "summary",
    logger: Optional[Callable[[str], None]] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    learning_engine=None
) -> List[Dict[str, Any]]:
    """
    Runs multiple turns of forward simulation.

    Args:
        state (WorldState): active sim state
        turns (int): number of steps (must be positive)
        use_symbolism (bool): enable tag/memory tracking
        return_mode (str): summary/full return format
        logger (callable): optional logger for messages
        progress_callback (callable): optional progress reporter (step, total)
        learning_engine: optional learning engine for hooks

    Returns:
        List of Dict per turn
    """
    if not isinstance(turns, int) or turns <= 0:
        raise ValueError("turns must be a positive integer")
    results = []
    for i in range(turns):
        turn_data = simulate_turn(state, use_symbolism=use_symbolism, return_mode=return_mode, logger=logger, learning_engine=learning_engine)
        results.append(turn_data)
        if progress_callback:
            progress_callback(i + 1, turns)
    return results

def inverse_decay(value: float, rate: float = 0.01, floor: float = 0.0, ceil: float = 1.0) -> float:
    """
    Inverse of linear decay: estimate prior value before decay step.
    """
    # Note: This assumes linear decay and no other effects.
    return min(ceil, max(floor, value + rate))

def simulate_backward(
    state: WorldState,
    steps: int = 1,
    use_symbolism: bool = True,
    decay_rate: float = 0.01,
    logger: Optional[Callable[[str], None]] = None,
    variable_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Reconstruct plausible prior worldstates by inverse overlay decay and symbolic tag regression.

    Limitations:
        - Only overlays are reversed (no variable/capital retrodiction yet).
        - Does not reverse rules or causal effects (planned for future).
        - Assumes constant decay rate for all overlays.
        - No schema enforcement or out-of-bounds correction.

    TODO:
        - Add reverse rule engine and causal chain unwinding.
        - Add variable/capital backward simulation.
        - Add logging to file for backtrace results.
        - Add schema validation and bounds checking.

    Args:
        state (WorldState): current worldstate (will not be mutated)
        steps (int): how many steps to reconstruct backward
        use_symbolism (bool): whether to log symbolic tags/arcs
        decay_rate (float): assumed decay rate per overlay per step
        logger (callable): optional logger
        variable_names (list): variables to track (default: all overlays)

    Returns:
        Dict with:
            - trace: list of dicts (overlays, deltas, symbolic_tag, step)
            - arc_label: symbolic arc label for the whole trace
            - volatility_score: volatility/integrity score for the arc
            - arc_certainty: certainty/confidence in the arc label
    """
    import copy
    # Use overlays as dict (support both dict and dataclass)
    if hasattr(state.overlays, "as_dict"):
        overlays_now = state.overlays.as_dict()
    else:
        overlays_now = dict(state.overlays)
    trace = []
    prev_overlays = overlays_now.copy()
    symbolic_trace = []
    for step in range(steps):
        # Inverse decay for each overlay (future: add variable/capital support)
        prior_overlays = {k: inverse_decay(v, rate=decay_rate) for k, v in prev_overlays.items()}
        # Warn if any overlay is out of [0,1] bounds
        for k, v in prior_overlays.items():
            if not (0.0 <= v <= 1.0):
                if logger:
                    logger(f"[SIM-BACK] Warning: overlay '{k}' out of bounds ({v}) at step {step}")
        # Compute deltas (should be negative of forward decay)
        deltas = {k: round(prior_overlays[k] - prev_overlays[k], 4) for k in prior_overlays}
        # Symbolic tag regression (optional)
        symbolic_tag = None
        if use_symbolism:
            try:
                symbolic_tag = tag_symbolic_state(prior_overlays, sim_id=getattr(state, 'sim_id', None), turn=getattr(state, 'turn', 0) - (step + 1)).get("symbolic_tag", "N/A")
            except Exception as e:
                symbolic_tag = "error"
                if logger: logger(f"[SIM-BACK] Symbolic tag error: {e}")
        entry = {
            "step": -(step + 1),
            "overlays": prior_overlays.copy(),
            "deltas": deltas,
            "symbolic_tag": symbolic_tag
        }
        trace.append(entry)
        symbolic_trace.append(prior_overlays.copy())
        prev_overlays = prior_overlays
    # Arc scoring: analyze the full symbolic trace for arc label, volatility, certainty
    arc_label = None
    volatility_score = None
    arc_certainty = None
    if use_symbolism and symbolic_trace:
        try:
            arc_result = score_symbolic_trace(symbolic_trace[::-1])  # oldest to newest
            arc_label = arc_result.get("arc_label")
            volatility_score = arc_result.get("volatility_score") or arc_result.get("symbolic_score")
            arc_certainty = arc_result.get("arc_certainty")
        except Exception as e:
            if logger: logger(f"[SIM-BACK] Arc scoring error: {e}")
    if logger:
        logger(f"[SIM-BACK] Completed {steps} backward steps. Final overlays: {prev_overlays}")
    return {
        "trace": trace,
        "arc_label": arc_label,
        "volatility_score": volatility_score,
        "arc_certainty": arc_certainty
    }

def simulate_counterfactual(
    base_state: WorldState,
    fork_vars: Dict[str, float],
    turns: int = 5,
    use_symbolism: bool = True,
    return_mode: Literal["summary", "full"] = "summary",
    logger: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Runs a counterfactual simulation by forking variables mid-simulation and comparing to base.

    Args:
        base_state (WorldState): The starting state (will not be mutated)
        fork_vars (dict): Variables to inject/change at fork point
        turns (int): Number of turns to simulate after fork
        use_symbolism (bool): Enable symbolic tagging
        return_mode (str): "summary" or "full"
        logger (callable): Optional logger

    Returns:
        Dict with base_trace, fork_trace, divergence, arc_scores
    """
    import copy
    # Run base simulation
    base = copy.deepcopy(base_state)
    base_trace = simulate_forward(base, turns=turns, use_symbolism=use_symbolism, return_mode=return_mode, logger=logger)
    # Fork and inject variables
    fork = copy.deepcopy(base_state)
    for k, v in fork_vars.items():
        if hasattr(fork.variables, "as_dict"):
            fork.variables.__dict__[k] = v
        else:
            fork.variables[k] = v
    fork_trace = simulate_forward(fork, turns=turns, use_symbolism=use_symbolism, return_mode=return_mode, logger=logger)
    # Compute divergence (overlay delta per turn)
    divergence = []
    for i in range(min(len(base_trace), len(fork_trace))):
        base_ov = base_trace[i]["overlays"]
        fork_ov = fork_trace[i]["overlays"]
        delta = {k: round(fork_ov.get(k, 0.0) - base_ov.get(k, 0.0), 4) for k in base_ov}
        divergence.append({"turn": i, "overlay_delta": delta})
    # Arc scoring
    from symbolic_system.symbolic_trace_scorer import score_symbolic_trace
    base_arc = score_symbolic_trace([t["overlays"] for t in base_trace])
    fork_arc = score_symbolic_trace([t["overlays"] for t in fork_trace])
    result = {
        "base_trace": base_trace,
        "fork_trace": fork_trace,
        "divergence": divergence,
        "base_arc": base_arc,
        "fork_arc": fork_arc
    }
    # Optionally log traces
    log_simulation_trace(base_trace, tag="base")
    log_simulation_trace(fork_trace, tag="fork")
    return result

def validate_variable_trace(
    var_name: str,
    known_trace: List[float],
    state: WorldState,
    steps: int = None,
    decay_rate: float = 0.01,
    atol: float = 0.02,
    logger: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Validate if simulate_backward can reconstruct a known variable trace.

    Args:
        var_name (str): variable to check (must be in overlays or variables)
        known_trace (list): historical values, most recent last
        state (WorldState): current state (will not be mutated)
        steps (int): how many steps to check (default: len(known_trace)-1)
        decay_rate (float): assumed decay rate
        atol (float): absolute tolerance for match
        logger (callable): optional logger

    Returns:
        Dict: expected, reconstructed, error, match_percent
    """
    if steps is None:
        steps = len(known_trace) - 1
    # Use overlays as dict (support both dict and dataclass)
    if hasattr(state.overlays, "as_dict"):
        overlays_now = state.overlays.as_dict()
    else:
        overlays_now = dict(state.overlays)
    if var_name not in overlays_now:
        raise ValueError(f"Variable '{var_name}' not found in overlays.")
    # Rewind
    vals = [overlays_now[var_name]]
    v = overlays_now[var_name]
    for _ in range(steps):
        v = inverse_decay(v, rate=decay_rate)
        vals.append(v)
    vals = vals[:len(known_trace)]
    vals = vals[::-1]  # oldest to newest
    expected = known_trace
    reconstructed = vals
    error = [abs(a - b) for a, b in zip(expected, reconstructed)]
    match = [e <= atol for e in error]
    match_percent = 100 * sum(match) / len(match) if match else 0
    result = {
        "var": var_name,
        "expected": expected,
        "reconstructed": reconstructed,
        "error": error,
        "match_percent": round(match_percent, 2)
    }
    if logger:
        logger(f"[TRACE-VALIDATE] {var_name}: {match_percent:.1f}% match, error={error}")
    return result

# Utility: Extract overlays as dict (suggested for DRYness)
def get_overlays_dict(state: WorldState) -> Dict[str, float]:
    """Extract overlays as a dict from WorldState, supporting both dict and dataclass."""
    if hasattr(state.overlays, "as_dict"):
        return state.overlays.as_dict()
    return dict(state.overlays)

# Stub: Log backtrace/validation results to file (suggested for diagnostics)
def log_to_file(data: dict, path: str):
    """Append a dict as JSON to a file."""
    import json
    with open(path, "a") as f:
        f.write(json.dumps(data) + "\n")

# === Reverse rule engine stub for future extension ===
def reverse_rule_engine(state: WorldState, overlays: Dict[str, float], variables: Dict[str, float], step: int = 1):
    """
    Placeholder for future reverse causal rule application.
    Will attempt to infer plausible prior variable/capital state given overlays.
    """
    # TODO: Implement reverse causal logic in future milestone
    pass

def _self_test():
    """Run a short simulation and print results for validation."""
    ws = WorldState()
    ws.sim_id = "selftest"
    print("Running self-test simulation (3 turns)...")
    output = simulate_forward(ws, turns=3, use_symbolism=True, return_mode="summary")
    for r in output:
        print(f"Turn {r['turn']} | Δ: {r['deltas']} | Tag: {r.get('symbolic_tag', '—')}")
    print("Self-test complete.")

def _backward_self_test():
    ws = WorldState()
    ws.sim_id = "backward_test"
    print("Running backward simulation self-test (3 steps)...")
    result = simulate_backward(ws, steps=3, use_symbolism=True)
    for entry in result["trace"]:
        print(f"Step {entry['step']}: overlays={entry['overlays']} tag={entry['symbolic_tag']}")
    print(f"Arc label: {result['arc_label']} | Volatility: {result['volatility_score']} | Certainty: {result['arc_certainty']}")
    print("Backward self-test complete.")

# === Example usage & CLI entry point ===
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pulse Simulator Core CLI")
    parser.add_argument("--turns", type=int, default=5, help="Number of turns to simulate")
    parser.add_argument("--full", action="store_true", help="Return full worldstate snapshots")
    parser.add_argument("--selftest", action="store_true", help="Run self-test simulation")
    parser.add_argument("--backward", type=int, default=0, help="Simulate N backward steps")
    parser.add_argument("--validate-trace", nargs="+", action="append", help="Validate variable trace: var_name v1 v2 v3 ... (can be repeated)")
    parser.add_argument("--arc", action="store_true", help="Show arc label/volatility for backward sim")
    parser.add_argument("--save-backtrace", type=str, default=None, help="Path to save backward trace as JSONL")
    args = parser.parse_args()

    if args.selftest:
        _self_test()
    elif args.backward > 0:
        ws = WorldState()
        ws.sim_id = "demo_sim"
        print(f"Simulating {args.backward} backward steps from initial state...")
        result = simulate_backward(ws, steps=args.backward, use_symbolism=True)
        for entry in result["trace"]:
            print(f"Step {entry['step']}: overlays={entry['overlays']} tag={entry['symbolic_tag']}")
        if args.arc:
            print(f"Arc label: {result['arc_label']} | Volatility: {result['volatility_score']} | Certainty: {result['arc_certainty']}")
        if args.save_backtrace:
            log_to_file(result, args.save_backtrace)
            print(f"Backtrace saved to {args.save_backtrace}")
    elif args.validate_trace:
        ws = WorldState()
        ws.sim_id = "demo_sim"
        # Support multiple --validate-trace arguments for batch validation
        for trace_args in args.validate_trace:
            if len(trace_args) < 2:
                print("Each --validate-trace requires a variable name and at least one value.")
                continue
            var = trace_args[0]
            vals = [float(v) for v in trace_args[1:]]
            result = validate_variable_trace(var, vals, ws)
            print(f"Validation result for {var}: {result}")
    else:
        ws = WorldState()
        ws.sim_id = "demo_sim"
        output = simulate_forward(
            ws,
            turns=args.turns,
            use_symbolism=True,
            return_mode="full" if args.full else "summary"
        )
        for r in output:
            print(f"Turn {r['turn']} | Δ: {r['deltas']} | Tag: {r.get('symbolic_tag', '—')}")
