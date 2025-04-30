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
from trust_system.forecast_episode_logger import log_episode_event  # optional
# Use relative import if possible, fallback to absolute
try:
    from symbolic_system.symbolic_state_tagger import tag_symbolic_state
except ImportError:
    from symbolic_system.symbolic_state_tagger import tag_symbolic_state

from symbolic_system.symbolic_trace_scorer import score_symbolic_trace  # Add for arc scoring
from simulation_engine.utils.simulation_trace_logger import log_simulation_trace  # updated path
from simulation_engine.rules.reverse_rule_mapper import match_rule_by_delta, get_all_rule_fingerprints       # updated path
from learning.learning import LearningEngine
from core.pulse_learning_log import log_learning_event

from typing import Dict, List, Any, Literal, Optional, Callable
from datetime import datetime, timezone
import json

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
    # Reset overlays
    overlays = getattr(state, 'overlays', None)
    if overlays and hasattr(overlays, "as_dict"):
        state.overlays = type(overlays)(**{k: 0.0 for k in overlays.as_dict()})
    # Reset variables
    variables = getattr(state, 'variables', None)
    if variables and hasattr(variables, "as_dict"):
        state.variables = type(variables)({k: 0.0 for k in variables.as_dict()})
    elif variables and hasattr(variables, "data"):
        state.variables = type(variables)({k: 0.0 for k in variables.data})
    # Reset capital
    capital = getattr(state, 'capital', None)
    if capital and hasattr(capital, "as_dict"):
        state.capital = type(capital)(**{k: 0.0 for k in capital.as_dict()})
    state.turn = 0
    state.event_log = []

def simulate_turn(
    state: WorldState,
    use_symbolism: bool = True,
    return_mode: Literal["summary", "full"] = "summary",
    logger: Optional[Callable[[str], None]] = None,
    learning_engine=None
) -> Dict[str, Any]:
    """
    Executes a single simulation turn, applying decay, rules, and capturing state changes.
    
    Args:
        state: The current world state to simulate
        use_symbolism: Whether to apply symbolic tagging to the output
        return_mode: Level of detail in the return object ('summary' or 'full')
        logger: Optional logging function
        learning_engine: Optional learning engine to apply
        
    Returns:
        Dictionary containing turn results, including overlays, deltas, and symbolic info
        
    Raises:
        ValueError: If state is invalid or return_mode is invalid
    """
    if not isinstance(state, WorldState):
        error_msg = f"Expected WorldState, got {type(state)}"
        if logger: logger(error_msg)
        raise ValueError(error_msg)
        
    if return_mode not in ["summary", "full"]:
        error_msg = f"Invalid return_mode: {return_mode}"
        if logger: logger(error_msg)
        raise ValueError(error_msg)
    
    # Validate state before simulation
    validation_errors = state.validate()
    if validation_errors:
        error_msg = f"Invalid world state: {validation_errors}"
        if logger: logger(error_msg)
        state.log_event(f"Warning: {error_msg}")

    # Store initial overlay state for comparison
    try:
        pre_overlay = _copy_overlay(getattr(state, 'overlays', {}))
    except Exception as e:
        error_msg = f"[SIM] Failed to copy initial overlays: {e}"
        if logger: logger(error_msg)
        state.log_event(error_msg)
        pre_overlay = {}

    # Apply decay to overlays
    try:
        for overlay_name, _ in state.overlays.items():
            decay_overlay(state, overlay_name)
    except Exception as e:
        error_msg = f"[SIM] Decay error: {str(e)}"
        if logger: logger(error_msg)
        state.log_event(error_msg)

    # Run simulation rules
    try:
        run_rules(state)
    except Exception as e:
        error_msg = f"[SIM] Rule engine error: {str(e)}"
        if logger: logger(error_msg)
        state.log_event(error_msg)

    # Apply learning engine if provided
    if learning_engine is not None:
        try:
            learning_engine.process_turn(state)
            if logger: logger("[SIM] Applied learning engine processing")
        except Exception as e:
            error_msg = f"[SIM] Learning engine error: {str(e)}"
            if logger: logger(error_msg)
            state.log_event(error_msg)

    # Get current overlay state
    try:
        overlays_now = _copy_overlay(getattr(state, 'overlays', {}))
    except Exception as e:
        error_msg = f"[SIM] Failed to copy final overlays: {e}"
        if logger: logger(error_msg)
        state.log_event(error_msg)
        overlays_now = {}

    # Validate overlay structure
    if not _validate_overlay(overlays_now):
        msg = "[SIM] Warning: overlays structure invalid after turn."
        if logger: logger(msg)
        state.log_event(msg)

    # Check for missing overlay keys
    missing_keys = set(pre_overlay) - set(overlays_now)
    if missing_keys:
        msg = f"[SIM] Warning: overlays missing keys after turn: {missing_keys}"
        if logger: logger(msg)
        state.log_event(msg)

    # Compute overlay deltas for each key in pre_overlay
    # Ensure overlays_now and pre_overlay are dicts for delta calculation
    ov_now = overlays_now
    if not isinstance(ov_now, dict) and hasattr(ov_now, "as_dict"):
        ov_now = ov_now.as_dict()
    pre_ov = pre_overlay
    if not isinstance(pre_ov, dict) and hasattr(pre_ov, "as_dict"):
        pre_ov = pre_ov.as_dict()
    output = {
        "turn": getattr(state, 'turn', -1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overlays": overlays_now,
        "deltas": {
            k: round(ov_now.get(k, 0.0) - pre_ov.get(k, 0.0), 3)
            for k in set(pre_ov) | set(ov_now)
        }
    }

    # Apply symbolic tagging
    if use_symbolism:
        try:
            sim_id_val = getattr(state, 'sim_id', None)
            if sim_id_val is None:
                sim_id_val = ""
            tag_result = tag_symbolic_state(
                overlays_now,
                sim_id=sim_id_val,
                turn=getattr(state, 'turn', -1)
            )
            output.update(tag_result)
        except Exception as e:
            error_msg = f"[SIM] Symbolic tagging error: {str(e)}"
            if logger: logger(error_msg)
            state.log_event(error_msg)
            output["symbolic_tag"] = "error"
            output["symbolic_score"] = 0.0

    # Add fired rules if in full mode
    if return_mode == "full":
        output["fired_rules"] = getattr(state, 'last_fired_rules', [])
        output["full_state"] = state.snapshot()

    from trust_system.trust_engine import TrustEngine
    # --- Trust enrichment ---
    engine = TrustEngine()
    output = engine.enrich_trust_metadata(output)
    # Warn if trust_label or confidence missing
    if "trust_label" not in output or "confidence" not in output:
        if logger:
            logger("[TRUST] Warning: trust_label or confidence missing from simulation output.")
    return output

def simulate_forward(
    state: WorldState,
    turns: int = 5,
    use_symbolism: bool = True,
    return_mode: Literal["summary", "full"] = "summary",
    logger: Optional[Callable[[str], None]] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    learning_engine=None,
    checkpoint_every: Optional[int] = None,
    checkpoint_path: Optional[str] = None,
    parallel: bool = False,
    retrodiction_mode: bool = False,
    retrodiction_loader: Optional[object] = None,
    injection_mode: str = "seed_then_free"
) -> List[Dict[str, Any]]:
    """
    Runs multiple turns of forward simulation, supporting both forecasting and retrodiction.

    Args:
        state (WorldState): active sim state
        turns (int): number of steps (must be positive)
        use_symbolism (bool): enable tag/memory tracking
        return_mode (str): summary/full return format
        logger (callable): optional logger for messages
        progress_callback (callable): optional progress reporter (step, total)
        learning_engine: optional learning engine for hooks
        retrodiction_mode (bool): if True, runs retrodiction with ground truth injection and comparison
        retrodiction_loader (optional): loader providing ground truth snapshots for retrodiction
        injection_mode (str): "seed_then_free" or "strict_injection" for retrodiction variable injection

    Returns:
        List of Dict per turn
    """
    if not isinstance(turns, int) or turns <= 0:
        raise ValueError("turns must be a positive integer")
    if parallel:
        raise NotImplementedError("Parallel execution is not yet supported")
    results = []
    for i in range(turns):
        # Retrodiction injection of ground truth variables if strict injection mode
        if retrodiction_mode and injection_mode == "strict_injection" and retrodiction_loader and hasattr(retrodiction_loader, "get_snapshot_by_turn"):
            snapshot = retrodiction_loader.get_snapshot_by_turn(i)
            if snapshot:
                from simulation_engine.state_mutation import update_numeric_variable, adjust_overlay, adjust_capital
                for var, val in snapshot.items():
                    # Use bounded APIs for overlays, variables, and capital
                    if hasattr(state.overlays, var):
                        adjust_overlay(state, var, val - getattr(state.overlays, var, 0.0))
                    elif hasattr(state.variables, var):
                        update_numeric_variable(state, var, val - getattr(state.variables, var, 0.0))
                    elif hasattr(state.capital, var):
                        adjust_capital(state, var, val - getattr(state.capital, var, 0.0))
                    else:
                        # fallback for unknown variable
                        try:
                            from core.variable_accessor import set_variable
                            set_variable(state, var, val)
                        except ImportError:
                            if hasattr(state.variables, "__setattr__"):
                                state.variables.__setattr__(var, val)
                            else:
                                setattr(state, var, val)
                if logger:
                    logger(f"[RETRO] Injected ground truth variables for turn {i}")
        # Simulate one turn
        turn_data = simulate_turn(state, use_symbolism=use_symbolism, return_mode=return_mode, logger=logger, learning_engine=learning_engine)
        # Retrodiction ground truth comparison and logging
        if retrodiction_mode and retrodiction_loader and hasattr(retrodiction_loader, "get_snapshot_by_turn"):
            ground_truth_snapshot = retrodiction_loader.get_snapshot_by_turn(i)
            if ground_truth_snapshot:
                # Compare overlays and variables to ground truth
                simulated_overlays = getattr(state, 'overlays', {})
                simulated_vars = getattr(state, 'variables', {})
                # Ensure simulated_overlays is a dict
                ov_dict = simulated_overlays
                if not isinstance(ov_dict, dict) and hasattr(ov_dict, "as_dict"):
                    ov_dict = ov_dict.as_dict()
                comparison = {
                    "turn": i,
                    "overlay_diff": {k: ov_dict.get(k, 0.0) - ground_truth_snapshot.get(k, 0.0) for k in ground_truth_snapshot},
                    "variable_diff": {k: simulated_vars.get(k, 0.0) - ground_truth_snapshot.get(k, 0.0) for k in ground_truth_snapshot}
                }
                # Log comparison to learning engine or episode logger
                if learning_engine:
                    try:
                        learning_engine.log_comparison(comparison)
                    except AttributeError:
                        pass
                try:
                    log_episode_event("retrodiction_comparison", comparison)
                except Exception:
                    pass
                if logger:
                    logger(f"[RETRO] Compared simulated state to ground truth for turn {i}")
                # 4 BayesianTrustTracker Hook: batch update after retrodiction comparison
                from core.bayesian_trust_tracker import bayesian_trust_tracker
                if ground_truth_snapshot and 'comparison' in locals():
                    batch_results = [(k, diff == 0.0) for k, diff in comparison["overlay_diff"].items()]
                    batch_results += [(k, diff == 0.0) for k, diff in comparison["variable_diff"].items()]
                    bayesian_trust_tracker.batch_update(batch_results)
        results.append(turn_data)
        # Checkpointing
        if checkpoint_every and checkpoint_path and (i + 1) % checkpoint_every == 0:
            try:
                snapshot = state.snapshot()
                filepath = f"{checkpoint_path}_turn_{i+1}.json"
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(snapshot, f)
                if logger: logger(f"[SIM] Checkpoint saved to {filepath}")
            except Exception as e:
                if logger: logger(f"[SIM] Checkpoint error: {e}")
        if progress_callback:
            progress_callback(i + 1, turns)
    # --- Batch trust enrichment (redundant if already done in simulate_turn, but ensures all are processed) ---
    from trust_system.trust_engine import TrustEngine
    results = TrustEngine.apply_all(results)
    # Warn if any result missing trust_label/confidence
    for r in results:
        if "trust_label" not in r or "confidence" not in r:
            if logger:
                logger("[TRUST] Warning: trust_label or confidence missing from simulation batch output.")
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
        overlays_now = state.overlays.as_dict()
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
                sim_id_val = getattr(state, 'sim_id', None)
                if sim_id_val is None:
                    sim_id_val = ""
                symbolic_tag = tag_symbolic_state(prior_overlays, sim_id=sim_id_val, turn=getattr(state, 'turn', 0) - (step + 1)).get("symbolic_tag", "N/A")
            except Exception as e:
                symbolic_tag = "error"
                if logger: logger(f"[SIM-BACK] Symbolic tag error: {e}")
        entry = {
            "step": -(step + 1),
            "overlays": prior_overlays.copy(),
            "deltas": deltas,
            "symbolic_tag": symbolic_tag,
            "matched_rules": match_rule_by_delta(deltas, get_all_rule_fingerprints())
        }
        # Reverse causal logic stub: infer prior causes
        try:
            inferred = reverse_rule_engine(state, entry["overlays"], dict(getattr(state, 'variables', {})), step + 1)
            entry["inferred_priors"] = inferred
        except Exception as e:
            if logger: logger(f"[SIM-BACK] Reverse rule error: {e}")
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
            fork.variables.__setattr__(k, v)
    fork_trace = simulate_forward(fork, turns=turns, use_symbolism=use_symbolism, return_mode=return_mode, logger=logger)
    # Compute divergence (overlay delta per turn)
    divergence = []
    for i in range(min(len(base_trace), len(fork_trace))):
        base_ov = base_trace[i]["overlays"]
        fork_ov = fork_trace[i]["overlays"]
        # Ensure fork_ov and base_ov are dicts
        fork_ov_dict = fork_ov.as_dict() if hasattr(fork_ov, "as_dict") else fork_ov
        base_ov_dict = base_ov.as_dict() if hasattr(base_ov, "as_dict") else base_ov
        delta = {k: round(fork_ov_dict.get(k, 0.0) - base_ov_dict.get(k, 0.0), 4) for k in base_ov_dict}
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
    steps: Optional[int] = None,
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
        overlays_now = state.overlays.as_dict()
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
    elif isinstance(state.overlays, dict):
        return state.overlays
    else:
        # Fallback for other cases
        try:
            result = {}
            for key in dir(state.overlays):
                if not key.startswith("_") and isinstance(getattr(state.overlays, key), (int, float)):
                    result[key] = float(getattr(state.overlays, key))
            return result
        except:
            return {}

# Stub: Log backtrace/validation results to file (suggested for diagnostics)
def log_to_file(data: dict, path: str):
    """Append a dict as JSON to a file."""
    import json
    with open(path, "a") as f:
        f.write(json.dumps(data) + "\n")

# === Reverse rule engine stub for future extension ===
def reverse_rule_engine(state: WorldState, overlays: Dict[str, float], variables: Dict[str, float], step: int = 1):
    """
    Reverse causal rule application: attempts to infer plausible prior causes (rules)
    for the observed overlay/variable deltas at a given step.

    Args:
        state: The current WorldState (not mutated)
        overlays: The overlays at this step (dict)
        variables: The variables at this step (dict)
        step: The backward step index (1 = most recent prior)

    Returns:
        Dict with:
            - rule_chains: List of possible rule chains (list of rule_id lists)
            - symbolic_tags: List of symbolic tags associated with matched rules
            - trust_scores: List of trust/confidence scores for each chain
            - suggestions: Any suggested new rules if no match found
    """
    from simulation_engine.rules.reverse_rule_engine import trace_causal_paths, get_fingerprints
    from trust_system.trust_engine import TrustEngine
    from symbolic_system.symbolic_state_tagger import tag_symbolic_state

    # Compute delta: overlays - previous overlays (approximate, since we don't have prior)
    # Here, we assume overlays is the "current" and try to explain it as a result of rules.
    # In practice, deltas should be passed in, but we use overlays as the delta for this step.
    delta = overlays.copy()

    fingerprints = get_fingerprints()
    rule_chains = trace_causal_paths(delta, fingerprints=fingerprints, max_depth=3, min_match=0.5)

    # Collect symbolic tags and trust scores for each chain
    symbolic_tags = []
    trust_scores = []
    engine = TrustEngine()
    for chain in rule_chains:
        tags = []
        trust = 0.0
        for rule_id in chain if isinstance(chain, list) else []:
            rule = next((r for r in fingerprints if r.get("rule_id") == rule_id or r.get("id") == rule_id), None)
            if rule:
                tags.extend(rule.get("symbolic_tags", []))
                # Optionally, use trust/frequency from fingerprint
                trust += rule.get("trust", 0) + rule.get("frequency", 0)
        symbolic_tags.append(list(set(tags)))
        trust_scores.append(trust)
    # Optionally, enrich with symbolic tag alignment/confidence
    symbolic_confidence = []
    for tags in symbolic_tags:
        conf = 0.0
        for tag in tags:
            try:
                # Use symbolic tagger to compute alignment/confidence if available
                conf += tag_symbolic_state({tag: 1.0}).get("symbolic_score", 0.0)
            except Exception:
                pass
        symbolic_confidence.append(conf)
    # Suggest new rules if no match found
    suggestions = []
    if not rule_chains:
        from simulation_engine.rules.reverse_rule_engine import suggest_new_rule_if_no_match
        suggestion = suggest_new_rule_if_no_match(delta, fingerprints)
        if suggestion:
            suggestions.append(suggestion)
    return {
        "rule_chains": rule_chains,
        "symbolic_tags": symbolic_tags,
        "trust_scores": trust_scores,
        "symbolic_confidence": symbolic_confidence,
        "suggestions": suggestions
    }

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
