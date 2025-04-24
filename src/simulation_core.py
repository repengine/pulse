"""
Consolidated simulation core module: core simulation functions.
"""

from simulation_engine.worldstate import WorldState
from simulation_engine.state_mutation import decay_overlay
from simulation_engine.rule_engine import run_rules
from forecast_output.forecast_episode_logger import log_episode_event
from symbolic_system.symbolic_state_tagger import tag_symbolic_state
from symbolic_system.symbolic_trace_scorer import score_symbolic_trace
from simulation_engine.utils.simulation_trace_logger import log_simulation_trace
from simulation_engine.rules.reverse_rule_mapper import match_rule_by_delta
from typing import Dict, List, Any, Callable, Optional, Literal
from datetime import datetime
import copy

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
            "event_log": list(getattr(state, 'events', [])[-3:])
        }

    msg = f"[SIM] Turn {getattr(state, 'turn', -1)} complete."
    if logger: logger(msg)
    state.log_event(msg)
    state.turn = getattr(state, 'turn', 0) + 1

    if learning_engine is not None:
        learning_engine.on_simulation_turn_end(state.snapshot())

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
    """
    if not isinstance(turns, int) or turns <= 0:
        raise ValueError("turns must be a positive integer")
    results = []
    for i in range(turns):
        turn_data = simulate_turn(
            state,
            use_symbolism=use_symbolism,
            return_mode=return_mode,
            logger=logger,
            learning_engine=learning_engine
        )
        results.append(turn_data)
        if progress_callback:
            progress_callback(i + 1, turns)
    return results

def inverse_decay(value: float, rate: float = 0.01, floor: float = 0.0, ceil: float = 1.0) -> float:
    """
    Estimate prior value before decay step (inverse of linear decay).
    """
    return min(ceil, max(floor, value + rate))

def simulate_backward(
    state: WorldState,
    steps: int = 1,
    use_symbolism: bool = True,
    decay_rate: float = 0.01,
    logger: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Reconstruct plausible prior worldstates by inverse overlay decay and symbolic tag regression.
    """
    overlays_now = getattr(state, 'overlays', {})
    prev_overlays = _copy_overlay(overlays_now)
    trace = []
    for step in range(steps):
        prior_overlays = {k: inverse_decay(v, rate=decay_rate) for k, v in prev_overlays.items()}
        deltas = {k: round(prior_overlays[k] - prev_overlays[k], 4) for k in prior_overlays}
        tag = None
        if use_symbolism:
            try:
                tag = tag_symbolic_state(prior_overlays, sim_id=getattr(state, 'sim_id', None), turn=(getattr(state, 'turn', 0) - step -1)).get("symbolic_tag", "N/A")
            except Exception as e:
                if logger: logger(f"[SIM-BACK] Symbolic tag error: {e}")
                tag = "error"
        entry = {"step": -(step+1), "overlays": prior_overlays, "deltas": deltas, "symbolic_tag": tag}
        trace.append(entry)
        prev_overlays = prior_overlays
    arc_result = None
    if use_symbolism:
        try:
            arc_result = score_symbolic_trace([t["overlays"] for t in trace][::-1])
        except Exception as e:
            if logger: logger(f"[SIM-BACK] Arc scoring error: {e}")
    result = {"trace": trace}
    if arc_result:
        result.update(arc_result)
    return result

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
    """
    base = copy.deepcopy(base_state)
    base_trace = simulate_forward(base, turns=turns, use_symbolism=use_symbolism, return_mode=return_mode, logger=logger)
    fork = copy.deepcopy(base_state)
    for k, v in fork_vars.items():
        if hasattr(fork.variables, "as_dict"):
            fork.variables.__dict__[k] = v
        else:
            fork.variables[k] = v
    fork_trace = simulate_forward(fork, turns=turns, use_symbolism=use_symbolism, return_mode=return_mode, logger=logger)
    divergence = []
    for i in range(min(len(base_trace), len(fork_trace))):
        base_ov = base_trace[i]["overlays"]
        fork_ov = fork_trace[i]["overlays"]
        delta = {k: round(fork_ov.get(k, 0) - base_ov.get(k, 0), 4) for k in base_ov}
        divergence.append({"turn": i, "delta": delta})
    base_arc = score_symbolic_trace([t["overlays"] for t in base_trace])
    fork_arc = score_symbolic_trace([t["overlays"] for t in fork_trace])
    log_simulation_trace(base_trace, tag="base")
    log_simulation_trace(fork_trace, tag="fork")
    return {"base_trace": base_trace, "fork_trace": fork_trace, "divergence": divergence, "base_arc": base_arc, "fork_arc": fork_arc}

def get_overlays_dict(state: WorldState) -> Dict[str, float]:
    """Extract overlays as a dict from WorldState, supporting both dict and dataclass."""
    if hasattr(state.overlays, "as_dict"):
        return state.overlays.as_dict()
    return dict(state.overlays)