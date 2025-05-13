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

# Add to imports at the top of simulation_engine/simulator_core.py
import logging # Added
from typing import Dict, List, Any, Literal, Optional, Callable, TYPE_CHECKING # Ensure Optional is imported if not already

if TYPE_CHECKING:
    from diagnostics.shadow_model_monitor import ShadowModelMonitor as _SMM_TypeForHint
import copy

# Fallback for WorldState if it's in a different location for some setups
try:
    from simulation_engine.worldstate import WorldState
except ImportError:
    from .worldstate import WorldState # Assuming relative import might work

# Import ShadowModelMonitor and config
try:
    from diagnostics.shadow_model_monitor import ShadowModelMonitor # Added
    # SHADOW_MONITOR_CONFIG will be read by the calling script (e.g., batch_runner)
    # and an instance of ShadowModelMonitor will be passed in.
except ImportError:
    class _ShadowModelMonitorFallback:
        """Placeholder for ShadowModelMonitor if not found at runtime."""
        pass
    ShadowModelMonitor = _ShadowModelMonitorFallback # type: ignore
    # print("Warning: ShadowModelMonitor could not be imported.") # Optional warning

# Create a logger for this module
logger_module = logging.getLogger(__name__) # Added


from simulation_engine.state_mutation import decay_overlay
from simulation_engine.rule_engine import run_rules
from trust_system.forecast_episode_logger import log_episode_event  # optional
# Use relative import if possible, fallback to absolute
try:
    from symbolic_system.symbolic_state_tagger import tag_symbolic_state
except ImportError:
    tag_symbolic_state = None
    logger_module.warning("Symbolic tagging module not found. Symbolic tagging will be disabled.")

from symbolic_system.symbolic_trace_scorer import score_symbolic_trace  # Add for arc scoring
from simulation_engine.utils.simulation_trace_logger import log_simulation_trace  # updated path
from simulation_engine.rules.reverse_rule_mapper import match_rule_by_delta, get_all_rule_fingerprints       # updated path
from learning.learning import LearningEngine
from core.pulse_learning_log import log_learning_event


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

# Helper function to get a dictionary from state.variables or similar accessor
def _get_dict_from_vars(variables_accessor: Any) -> Dict[str, float]:
    raw_dict = None
    if hasattr(variables_accessor, "as_dict") and callable(variables_accessor.as_dict):
        try:
            raw_dict = variables_accessor.as_dict()
        except Exception as e:
            logger_module.error(f"Error calling as_dict() on {type(variables_accessor)}: {e}")
            return {} # Return empty on error to prevent further issues

    elif isinstance(variables_accessor, dict):
        raw_dict = variables_accessor

    if isinstance(raw_dict, dict):
        # Ensure keys are strings and values are floats
        processed_dict: Dict[str, float] = {}
        for k, v in raw_dict.items():
            try:
                processed_dict[str(k)] = float(v)
            except (ValueError, TypeError) as e:
                logger_module.warning(f"Could not convert key '{k}' or value '{v}' to str/float in _get_dict_from_vars: {e}")
        return processed_dict

    logger_module.debug(f"Variables accessor type {type(variables_accessor)} not directly convertible to Dict[str, float]. Evaluated to raw_dict type {type(raw_dict)}. Returning empty for safety.")
    return {}


# Modify simulate_turn function signature
def simulate_turn(
    state: WorldState,
    use_symbolism: bool = True,
    return_mode: Literal["summary", "full"] = "summary",
    logger: Optional[Callable[[str], None]] = None,
    learning_engine=None,
    shadow_monitor_instance: Optional['_SMM_TypeForHint'] = None,
    gravity_enabled: bool = True,
    gravity_config: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Executes a single simulation turn, applying decay, rules, and capturing state changes.

    Args:
        state: The current world state to simulate
        use_symbolism: Whether to apply symbolic tagging to the output
        return_mode: Level of detail in the return object ('summary' or 'full')
        logger: Optional logging function
        learning_engine: Optional learning engine to apply
        shadow_monitor_instance: Optional ShadowModelMonitor instance
        gravity_enabled (bool): Whether gravity correction is enabled (default: True)
        gravity_config: Optional configuration for the gravity engine

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

    # --- Shadow Monitor: Capture initial variable state for critical variables ---
    pre_variables_critical: Dict[str, float] = {}
    if shadow_monitor_instance and shadow_monitor_instance.critical_variables: # Added block
        try:
            initial_vars_dict = _get_dict_from_vars(state.variables)
            if initial_vars_dict:
                 pre_variables_critical = {
                    var: float(initial_vars_dict.get(var, 0.0))
                    for var in shadow_monitor_instance.critical_variables
                }
            else:
                logger_module.debug("Shadow Monitor: Could not get initial_vars_dict for pre_variables_critical.")
        except Exception as e:
            logger_module.error(f"Shadow Monitor: Error capturing pre_variables_critical: {e}")


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

    # Apply symbolic gravity correction if available and enabled
    # Container for gravity correction details (for explainability)
    gravity_correction_details = {}
    
    if gravity_enabled: # Added check for gravity_enabled
        try:
            # Import here to avoid circular imports
            from symbolic_system.gravity.symbolic_gravity_fabric import create_default_fabric

            # Get predicted values from state variables
            sim_vars = getattr(state, 'variables', {})
            # Use type ignore for dynamic attribute access
            # sim_vars_dict = sim_vars.as_dict() if hasattr(sim_vars, "as_dict") else (sim_vars if isinstance(sim_vars, dict) else _get_dict_from_vars(sim_vars))
            # Simplified access:
            if hasattr(sim_vars, "as_dict") and callable(sim_vars.as_dict): # type: ignore
                sim_vars_dict = _get_dict_from_vars(sim_vars) # Use our helper to ensure Dict[str, float]
            elif isinstance(sim_vars, dict):
                sim_vars_dict = _get_dict_from_vars(sim_vars) # Use our helper
            else:
                sim_vars_dict = _get_dict_from_vars(sim_vars) # Fallback to helper which handles other types or logs # type: ignore

            # Get symbolic pillar values
            symbolic_vec = getattr(state, 'overlays', {})
            # Use type ignore for dynamic attribute access
            # symbolic_vec_dict = symbolic_vec.as_dict() if hasattr(symbolic_vec, "as_dict") else (symbolic_vec if isinstance(symbolic_vec, dict) else {})
            # Simplified access:
            if hasattr(symbolic_vec, "as_dict") and callable(symbolic_vec.as_dict): # type: ignore
                symbolic_vec_dict = _get_dict_from_vars(symbolic_vec) # Use helper, assuming overlays are also numeric
            elif isinstance(symbolic_vec, dict):
                symbolic_vec_dict = _get_dict_from_vars(symbolic_vec) # Use helper
            else:
                # Overlays might be structured differently, if not dict or as_dict, might need specific handling
                # For now, assume it can be processed by _get_dict_from_vars or defaults to empty
                symbolic_vec_dict = _get_dict_from_vars(symbolic_vec) # type: ignore
                if not symbolic_vec_dict and symbolic_vec: # If helper failed but symbolic_vec exists
                     logger_module.warning(f"Could not convert symbolic_vec of type {type(symbolic_vec)} to dict for shadow monitor.")

            # Capture causal deltas (changes due to rules before gravity is applied)
            # This needs to be done for all variables, not just critical ones from shadow monitor
            vars_before_gravity = sim_vars_dict.copy()
            causal_deltas = {}
            
            # If we have pre-simulation variable values, calculate causal deltas
            if hasattr(state, '_pre_simulation_vars'):
                pre_sim_vars = getattr(state, '_pre_simulation_vars', {})
                for var_name, current_val in vars_before_gravity.items():
                    # Calculate causal delta as current value minus pre-simulation value
                    pre_val = pre_sim_vars.get(var_name, 0.0)
                    causal_deltas[var_name] = current_val - pre_val
            else:
                # Store initial values for next turn if not already present
                # This is first-time initialization
                setattr(state, '_pre_simulation_vars', vars_before_gravity.copy())
                
            # --- Shadow Monitor: Capture variable state before gravity and calculate causal deltas ---
            causal_deltas_monitor: Dict[str, float] = {}
            vars_before_gravity_critical: Dict[str, float] = {}
            if shadow_monitor_instance and shadow_monitor_instance.critical_variables: # Added block
                try:
                    # sim_vars_dict is the state after causal rules, before gravity
                    vars_before_gravity_critical = {
                        var: float(sim_vars_dict.get(var, 0.0))
                        for var in shadow_monitor_instance.critical_variables
                    }
                    causal_deltas_monitor = {
                        var: vars_before_gravity_critical.get(var, 0.0) - pre_variables_critical.get(var, 0.0)
                        for var in shadow_monitor_instance.critical_variables
                    }
                except Exception as e:
                    logger_module.error(f"Shadow Monitor: Error capturing vars_before_gravity_critical or calculating causal_deltas_monitor: {e}")

            # Get or create the gravity fabric with specified config if provided
            if not hasattr(state, '_gravity_fabric'):
                if gravity_config is not None:
                    state._gravity_fabric = create_default_fabric(config=gravity_config)  # type: ignore
                else:
                    state._gravity_fabric = create_default_fabric()  # type: ignore
                if logger: logger("[SIM] Created new symbolic gravity fabric")

            # Apply corrections to variables using the gravity fabric if not disabled
            # Use type ignore for dynamic property access
            corrected_vars: Dict[str, float] = sim_vars_dict # Default if gravity is skipped/fails
            
            if (not hasattr(state, '_gravity_disable') or not getattr(state, '_gravity_disable', False)) and \
               hasattr(state, '_gravity_fabric') and hasattr(getattr(state, '_gravity_fabric', None), 'bulk_apply_correction'):
                # Get the corrected values
                corrected_vars = state._gravity_fabric.bulk_apply_correction(sim_vars_dict)  # type: ignore
                
                # Calculate gravity deltas for all variables
                gravity_deltas = {}
                for var_name, corrected_val in corrected_vars.items():
                    # Calculate gravity delta as corrected value minus value before gravity
                    gravity_delta = corrected_val - vars_before_gravity.get(var_name, 0.0)
                    gravity_deltas[var_name] = gravity_delta
                    
                    # Get dominant pillars for this variable (if significant correction applied)
                    if abs(gravity_delta) > 1e-6:  # Only record significant corrections
                        # Get the top contributing pillars and their weights from the gravity fabric
                        gravity_engine = getattr(state._gravity_fabric, 'gravity_engine', None) # type: ignore
                        dominant_pillars = []
                        
                        if gravity_engine:
                            # Get top contributors from the gravity engine
                            try:
                                top_contributors = gravity_engine.get_top_contributors(n=5)
                                
                                # Process each contributing pillar
                                for pillar_name, weight in top_contributors:
                                    # Get source data points if possible
                                    source_data_points = []
                                    
                                    # Try to get pillar from the pillar system
                                    pillar_system = getattr(state._gravity_fabric, 'pillar_system', None) # type: ignore
                                    if pillar_system:
                                        pillar = pillar_system.get_pillar(pillar_name)
                                        if pillar and hasattr(pillar, 'data_points'):
                                            # Get source data points (limited to most recent/relevant)
                                            for i, (data_point, point_weight) in enumerate(pillar.data_points[-10:]):
                                                point_id = f"dp_{i}"
                                                if hasattr(data_point, 'id'):
                                                    point_id = data_point.id
                                                elif hasattr(data_point, '__str__'):
                                                    point_id = str(data_point)[:20]  # Truncate if too long
                                                
                                                # Get timestamp if available
                                                timestamp = "unknown"
                                                if hasattr(data_point, 'timestamp'):
                                                    timestamp = data_point.timestamp
                                                
                                                # Get value if available
                                                value = point_weight  # Default to weight
                                                if hasattr(data_point, 'value'):
                                                    value = data_point.value
                                                
                                                source_data_points.append({
                                                    "id": point_id,
                                                    "value": value,
                                                    "timestamp": timestamp,
                                                    "weight": point_weight
                                                })
                                    
                                    # Add pillar to dominant pillars list
                                    dominant_pillars.append({
                                        "pillar_name": pillar_name,
                                        "weight": weight,
                                        "source_data_points": source_data_points
                                    })
                            except Exception as e:
                                if logger:
                                    logger(f"[SIM] Error getting gravity contributor details: {e}")
                        
                        # Add details for this variable to the gravity correction details
                        gravity_correction_details[var_name] = {
                            "gravity_delta": gravity_delta,
                            "causal_delta": causal_deltas.get(var_name, 0.0),
                            "dominant_pillars": dominant_pillars
                        }

                # Apply the corrected values back to state
                for var_name, corrected_val in corrected_vars.items():
                    if hasattr(sim_vars, "__setattr__"):
                        sim_vars.__setattr__(var_name, corrected_val)
                    elif hasattr(sim_vars, "__setitem__"):
                        sim_vars[var_name] = corrected_val

                # Step the fabric forward to update state
                state._gravity_fabric.step(state)  # type: ignore

                if logger: logger("[SIM] Applied symbolic gravity corrections")

                # --- Shadow Monitor: Record step and check trigger ---
                if shadow_monitor_instance and shadow_monitor_instance.critical_variables: # Added block
                    try:
                        # state.variables should now reflect corrected_vars
                        # Alternatively, use corrected_vars directly if certain it contains all critical ones post-gravity
                        vars_after_gravity_dict = _get_dict_from_vars(state.variables) # Re-fetch to be sure
                        if not vars_after_gravity_dict: # Fallback to corrected_vars if _get_dict_from_vars fails
                            vars_after_gravity_dict = corrected_vars

                        vars_after_gravity_critical = {
                            var: float(vars_after_gravity_dict.get(var, 0.0))
                            for var in shadow_monitor_instance.critical_variables
                        }

                        gravity_deltas_monitor = {
                            var: vars_after_gravity_critical.get(var, 0.0) - vars_before_gravity_critical.get(var, 0.0)
                            for var in shadow_monitor_instance.critical_variables
                        }

                        shadow_monitor_instance.record_step(
                            causal_deltas=causal_deltas_monitor,
                            gravity_deltas=gravity_deltas_monitor,
                            current_step=getattr(state, 'turn', -1)
                        )

                        triggered, problematic_vars = shadow_monitor_instance.check_trigger()
                        if triggered:
                            logger_module.warning(
                                f"ShadowModelMonitor TRIGGERED at turn {getattr(state, 'turn', -1)}. "
                                f"Problematic variables: {problematic_vars}. Gravity influence exceeded threshold."
                            )
                    except Exception as e:
                        logger_module.error(f"Shadow Monitor: Error during record_step or check_trigger: {e}")
                
                # Store pre-simulation values for next turn
                setattr(state, '_pre_simulation_vars', vars_before_gravity.copy())
        except ImportError as e:
            # Gravity fabric module not available, skip correction
            if logger: logger(f"[SIM] Symbolic gravity not available: {e}")
        except Exception as e:
            error_msg = f"[SIM] Symbolic gravity error: {str(e)}"
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
    # Add gravity correction details to the output
    output["gravity_correction_details"] = gravity_correction_details
 
    # Apply symbolic tagging
    if use_symbolism and tag_symbolic_state is not None:
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
    elif use_symbolism and tag_symbolic_state is None:
        # Log that symbolic tagging is skipped due to missing module
        warning_msg = "[SIM] Symbolic tagging skipped: module not available."
        if logger: logger(warning_msg)
        state.log_event(warning_msg)
        output["symbolic_tag"] = "disabled"
        output["symbolic_score"] = 0.0

    # Add fired rules if in full mode
    if return_mode == "full":
        output["fired_rules"] = getattr(state, 'last_fired_rules', [])
        output["full_state"] = state.snapshot()

    from trust_system.trust_engine import TrustEngine
    # --- Trust enrichment ---
    engine = TrustEngine()
    # Store gravity details before potential modification by enrich_trust_metadata.
    # This is a targeted fix for GTB5-002, assuming the key might be lost
    # if enrich_trust_metadata returns a new dict object or modifies
    # the existing one by removing this key.
    _gcd_backup = output.get("gravity_correction_details")
    
    output = engine.enrich_trust_metadata(output)

    # If gravity_correction_details was backed up, restore it to ensure
    # enrich_trust_metadata did not unintentionally remove or alter it.
    # This handles cases where the key might be removed OR its value changed.
    if _gcd_backup is not None:
        output["gravity_correction_details"] = _gcd_backup
    elif "gravity_correction_details" in output and output["gravity_correction_details"] is None:
        # If it was None before and is still None, that's fine.
        # But if it became None, and there was no backup, we might want to remove the key
        # or ensure it's an empty dict if the expectation is for the key to sometimes be absent.
        # For now, if _gcd_backup is None, we assume it's okay for the key to be absent or None.
        pass
 
    # Warn if trust_label or confidence missing
    if "trust_label" not in output or "confidence" not in output:
        if logger:
            logger("[TRUST] Warning: trust_label or confidence missing from simulation output.")
    if logger: # Ensure logger is available
        if "gravity_correction_details" in output:
            logger(f"[DEBUG_GCD] Key 'gravity_correction_details' IS IN output. Value: {type(output['gravity_correction_details'])}")
            if isinstance(output['gravity_correction_details'], dict) and not output['gravity_correction_details']:
                logger(f"[DEBUG_GCD] Value is an EMPTY DICT.")
            elif output['gravity_correction_details'] is None:
                logger(f"[DEBUG_GCD] Value is None.")
            else:
                logger(f"[DEBUG_GCD] Value is present and not empty/None.")
        else:
            logger(f"[DEBUG_GCD] Key 'gravity_correction_details' IS NOT IN output.")
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
    injection_mode: str = "seed_then_free",
    shadow_monitor_instance: Optional['_SMM_TypeForHint'] = None,
    gravity_enabled: bool = True,
    gravity_config: Optional[Any] = None
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
        checkpoint_every: Optional interval for saving checkpoints
        checkpoint_path: Optional path for saving checkpoints
        parallel: Whether to run simulation turns in parallel (not yet supported)
        retrodiction_mode (bool): if True, runs retrodiction with ground truth injection and comparison
        retrodiction_loader (optional): loader providing ground truth snapshots for retrodiction
        injection_mode (str): "seed_then_free" or "strict_injection" for retrodiction variable injection
        shadow_monitor_instance: Optional ShadowModelMonitor instance
        gravity_enabled (bool): Whether gravity correction is enabled (default: True)
        gravity_config: Optional configuration for the gravity engine

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
            # Use type ignore for dynamic method access
            snapshot = retrodiction_loader.get_snapshot_by_turn(i)  # type: ignore
            if snapshot:
                from simulation_engine.state_mutation import update_numeric_variable, adjust_overlay, adjust_capital
                for var, val in snapshot.items():
                    # Use bounded APIs for overlays, variables, and capital
                    if hasattr(state.overlays, var):
                        adjust_overlay(state, var, val - getattr(state.overlays, var, 0.0))
                    elif hasattr(state.variables, var):
                        # Calculate residual for gravity learning if gravity is enabled
                        if gravity_enabled and hasattr(state, '_gravity_fabric') and hasattr(getattr(state, '_gravity_fabric', None), 'update_weights'): # Added gravity_enabled check
                            old_val = getattr(state.variables, var, 0.0)
                            residual = val - old_val
                            if abs(residual) > 1e-6:  # Only learn from meaningful residuals
                                try:
                                    # Get symbolic state vector
                                    sym_vec = getattr(state.overlays, "as_dict", lambda: {})()
                                    # Update weights based on residual
                                    # Use type ignore for dynamic attribute access
                                    state._gravity_fabric.gravity_engine.update_weights(residual, sym_vec)  # type: ignore
                                    if logger: logger(f"[SIM] Updated gravity weights (residual={residual:.4f})")
                                except Exception as e:
                                    if logger: logger(f"[SIM] Gravity weight update error: {str(e)}")

                        # Update the variable with ground truth
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
        # Simulate one turn, passing the shadow_monitor_instance and gravity_enabled
        turn_data = simulate_turn(
            state,
            use_symbolism=use_symbolism,
            return_mode=return_mode,
            logger=logger,
            learning_engine=learning_engine,
            shadow_monitor_instance=shadow_monitor_instance,
            gravity_enabled=gravity_enabled,
            gravity_config=gravity_config
        )
        # Retrodiction ground truth comparison and logging
        if retrodiction_mode and retrodiction_loader and hasattr(retrodiction_loader, "get_snapshot_by_turn"):
            # Use type ignore for dynamic method access
            ground_truth_snapshot = retrodiction_loader.get_snapshot_by_turn(i)  # type: ignore
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

def validate_variable_trace(
    var_name: str,
    known_trace: List[float],
    state: WorldState,
    decay_rate: float = 0.01,
    atol: float = 1e-2, # Absolute tolerance for float comparison
    logger: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Validates a known historical trace for a single variable by reconstructing
    a trace backward from the variable's current value in the provided WorldState
    and comparing it against the known_trace.

    Args:
        var_name (str): The name of the variable (overlay) to validate.
        known_trace (List[float]): The known historical trace (ordered oldest to newest).
                                   This trace represents values at T-N, T-N+1, ..., T-1.
        state (WorldState): The current world state, from which the value at T0 (current)
                            for var_name will be taken as the starting point for backward reconstruction.
        decay_rate (float): The assumed decay rate for inverse_decay.
        atol (float): Absolute tolerance for comparing reconstructed and known values.
        logger (Optional[Callable[[str], None]]): Optional logger.

    Returns:
        Dict[str, Any]: Validation results including expected (known_trace),
                        reconstructed trace, error, and match percentage.
    Raises:
        ValueError: If var_name is not found in state.overlays or overlays type is not convertible.
    """
    current_overlays: Dict[str, float]
    if hasattr(state.overlays, "as_dict") and callable(getattr(state.overlays, "as_dict")):
        current_overlays = state.overlays.as_dict()
    elif isinstance(state.overlays, dict):
        current_overlays = state.overlays
    else:
        try:
            current_overlays = dict(state.overlays) # type: ignore
        except (TypeError, ValueError) as e:
            msg = f"Overlays type {type(state.overlays)} not convertible to dict for trace validation: {e}"
            if logger: logger(msg)
            raise ValueError(msg) from e

    if var_name not in current_overlays:
        msg = f"Variable '{var_name}' not found in current overlays for trace validation."
        if logger: logger(msg)
        raise ValueError(msg)

    current_val_in_state = current_overlays[var_name] # This is value at T0

    num_historical_points_to_reconstruct = len(known_trace)
    reconstructed_chronological: List[float] = []
    error: List[float] = []
    match: List[bool] = []
    match_percent: float = 0.0

    if num_historical_points_to_reconstruct == 0:
        # No historical trace to compare against, so 0% match by definition.
        # Reconstructed trace is also empty.
        pass # Variables already initialized
    else:
        # Reconstruct a trace of length `num_historical_points_to_reconstruct`
        # by rewinding from `current_val_in_state`.
        # The reconstructed trace will represent [T0-N, ..., T0-1]
        
        reconstructed_backward_steps = [] # Stores [T0-1, T0-2, ..., T0-N]
        val_at_prev_step = current_val_in_state
        for _ in range(num_historical_points_to_reconstruct):
            val_at_prev_step = inverse_decay(val_at_prev_step, rate=decay_rate)
            reconstructed_backward_steps.append(val_at_prev_step)
        
        # reconstructed_backward_steps is [value at T-1, value at T-2, ..., value at T-N (relative to current_val_in_state)]
        # Reverse to get chronological order [T-N, ..., T-1]
        reconstructed_chronological = reconstructed_backward_steps[::-1]

        error = [abs(a - b) for a, b in zip(known_trace, reconstructed_chronological)]
        match = [e <= atol for e in error]
        if match: # Avoid division by zero if known_trace was empty, though handled by outer if
            match_percent = 100 * sum(match) / len(match)

    result = {
        "var": var_name,
        "expected": known_trace,
        "reconstructed": reconstructed_chronological,
        "error": error,
        "match_percent": round(match_percent, 2)
    }
    if logger:
        log_message = (f"[VALIDATE_TRACE] {var_name}: {match_percent:.1f}% match. "
                       f"Expected: {known_trace}, Reconstructed: {reconstructed_chronological}, Error: {error}")
        logger(log_message)
    return result

def simulate_backward(
    state: WorldState,
    steps: int = 1,
    use_symbolism: bool = True,
    decay_rate: float = 0.01, # Retain for signature compatibility
    logger: Optional[Callable[[str], None]] = None,
    variable_names: Optional[List[str]] = None # Retain for signature
) -> Dict[str, Any]:
    """
    Placeholder for backward simulation. The original implementation was for
    validate_variable_trace and has been moved. This function's full
    implementation (reconstructing plausible prior worldstates by inverse
    overlay decay and symbolic tag regression) is pending.

    Args:
        state (WorldState): current worldstate (will not be mutated)
        steps (int): how many steps to reconstruct backward
        use_symbolism (bool): whether to log symbolic tags/arcs
        decay_rate (float): assumed decay rate per overlay per step
        logger (callable): optional logger
        variable_names (list): variables to track (default: all overlays)

    Returns:
        Dict with placeholder structure:
            - trace: list of dicts (overlays, deltas, symbolic_tag, step)
            - arc_label: symbolic arc label for the whole trace
            - volatility_score: volatility/integrity score for the arc
            - arc_certainty: certainty/confidence in the arc label
    """
    if logger:
        logger(f"[SIMULATE_BACKWARD] Placeholder function called for {steps} steps. Full implementation pending.")

    trace_entries = []
    
    # Create a deepcopy of the state's overlays to avoid modifying the original state object
    # if we were to perform actual inverse operations on it.
    # For a placeholder, this isn't strictly necessary but good practice if it were to evolve.
    temp_overlays: Dict[str, float]
    if hasattr(state.overlays, "as_dict") and callable(getattr(state.overlays, "as_dict")):
        temp_overlays = copy.deepcopy(state.overlays.as_dict())
    elif isinstance(state.overlays, dict):
        temp_overlays = copy.deepcopy(state.overlays)
    else:
        temp_overlays = {} # Fallback for unknown overlay types

    for step_num in range(steps):
        # In a real implementation, inverse_decay and reverse_rule_engine would modify temp_overlays
        # For placeholder, we just create a dummy entry.
        # If variable_names is provided, focus on those, otherwise all in temp_overlays.
        current_step_overlays = {}
        keys_to_process = variable_names if variable_names else list(temp_overlays.keys())

        for ov_key in keys_to_process:
            if ov_key in temp_overlays:
                 # Simulate applying inverse decay for the placeholder
                temp_overlays[ov_key] = inverse_decay(temp_overlays[ov_key], rate=decay_rate)
                current_step_overlays[ov_key] = temp_overlays[ov_key]
            else:
                current_step_overlays[ov_key] = 0.0 # Default if not found

        trace_entry = {
            "step": step_num + 1, # 1-indexed backward steps
            "overlays": copy.deepcopy(current_step_overlays),
            "deltas": {}, # Placeholder
            "symbolic_tag": f"placeholder_backward_tag_step_{step_num+1}",
            "symbolic_score": 0.0,
            "rule_chains": [],
            "suggestions": []
        }
        trace_entries.append(trace_entry)

    return {
        "trace": trace_entries,
        "arc_label": "placeholder_backward_arc_label",
        "volatility_score": 0.0,
        "arc_certainty": 0.0
    }
def simulate_counterfactual(
    initial_state: WorldState,
    fork_vars: Dict[str, Any],
    turns: int,
    use_symbolism: bool = True,
    logger: Optional[Callable[[str], None]] = None,
    return_mode: Literal["summary", "full"] = "summary",
    **kwargs # Pass other arguments to simulate_forward
) -> Dict[str, Any]:
    """
    Runs a base simulation and a forked simulation with modified initial variables,
    then compares their traces.

    Args:
        initial_state (WorldState): The starting state for both simulations.
        fork_vars (Dict[str, Any]): Dictionary of variables to change for the forked simulation.
                                     Keys are variable names, values are their new initial values.
        turns (int): Number of turns to simulate for both base and fork.
        use_symbolism (bool): Whether to apply symbolic tagging.
        logger (Optional[Callable[[str], None]]): Optional logging function.
        return_mode (Literal["summary", "full"]): Detail level for simulate_forward.
        **kwargs: Additional keyword arguments to pass to simulate_forward.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - "base_trace": List of turn results from the base simulation.
            - "fork_trace": List of turn results from the forked simulation.
            - "divergence": List of dictionaries detailing overlay differences per turn.
            - "base_arc": Symbolic score of the base trace.
            - "fork_arc": Symbolic score of the forked trace.
    """
    if not isinstance(initial_state, WorldState):
        err_msg = f"Expected initial_state to be WorldState, got {type(initial_state)}"
        if logger:
            logger(err_msg)
        raise ValueError(err_msg)

    if not isinstance(fork_vars, dict):
        err_msg = f"Expected fork_vars to be a dict, got {type(fork_vars)}"
        if logger:
            logger(err_msg)
        raise ValueError(err_msg)

    # Base Trace
    base_run_state = copy.deepcopy(initial_state)
    base_trace = simulate_forward(
        base_run_state,
        turns=turns,
        use_symbolism=use_symbolism,
        return_mode=return_mode,
        logger=logger,
        **kwargs
    )

    # Forked Trace
    fork_run_state = copy.deepcopy(initial_state)
    # Apply fork_vars
    for key, value in fork_vars.items():
        # Attempt to set in overlays first
        if hasattr(fork_run_state.overlays, key):
            try:
                setattr(fork_run_state.overlays, key, float(value))
                if logger:
                    logger(f"[COUNTERFACTUAL] Forked overlay '{key}' to {value}")
            except (ValueError, TypeError) as e:
                if logger:
                    logger(f"[COUNTERFACTUAL] Error setting overlay '{key}' to {value}: {e}")
        # Then attempt to set in variables.data
        elif hasattr(fork_run_state.variables, 'data') and isinstance(fork_run_state.variables.data, dict):
            try:
                fork_run_state.variables.data[key] = float(value)
                if logger:
                    logger(f"[COUNTERFACTUAL] Forked variable '{key}' to {value}")
            except (ValueError, TypeError) as e:
                if logger:
                    logger(f"[COUNTERFACTUAL] Error setting variable '{key}' to {value}: {e}")
        else:
            if logger:
                logger(f"[COUNTERFACTUAL] Warning: Could not find where to set fork_var '{key}' in WorldState.")

    fork_trace = simulate_forward(
        fork_run_state,
        turns=turns,
        use_symbolism=use_symbolism,
        return_mode=return_mode,
        logger=logger,
        **kwargs
    )

    # Calculate Divergence
    divergence = []
    for t in range(min(len(base_trace), len(fork_trace))): # Iterate up to the length of the shorter trace
        base_turn_overlays = base_trace[t].get("overlays", {})
        fork_turn_overlays = fork_trace[t].get("overlays", {})

        # Ensure overlays are dicts for comparison
        if hasattr(base_turn_overlays, 'as_dict'):
            base_turn_overlays = base_turn_overlays.as_dict()
        if hasattr(fork_turn_overlays, 'as_dict'):
            fork_turn_overlays = fork_turn_overlays.as_dict()
        
        # Ensure all keys are present in both for consistent delta calculation, defaulting to 0.0
        all_overlay_keys = set(base_turn_overlays.keys()) | set(fork_turn_overlays.keys())
        overlay_delta_dict = {
            key: round(float(fork_turn_overlays.get(key, 0.0)) - float(base_turn_overlays.get(key, 0.0)), 3)
            for key in all_overlay_keys
        }
        
        divergence.append({
            "turn": t,
            "overlay_delta": overlay_delta_dict,
            # Potentially add variable deltas here too if needed by tests/consumers
        })

    # Score Traces
    sim_id_base = getattr(initial_state, 'sim_id', 'sim') + "_base_cf"
    sim_id_fork = getattr(initial_state, 'sim_id', 'sim') + "_fork_cf"
    
    base_arc = {}
    fork_arc = {}

    if score_symbolic_trace: # Check if function is available
        try:
            base_arc = score_symbolic_trace(base_trace)
        except Exception as e:
            if logger:
                logger(f"[COUNTERFACTUAL] Error scoring base trace: {e}")
        try:
            fork_arc = score_symbolic_trace(fork_trace)
        except Exception as e:
            if logger:
                logger(f"[COUNTERFACTUAL] Error scoring fork trace: {e}")
    elif logger:
        logger("[COUNTERFACTUAL] score_symbolic_trace not available. Skipping trace scoring.")


    # Log Traces
    if log_simulation_trace: # Check if function is available
        try:
            log_simulation_trace(base_trace, tag=f"counterfactual_base_{sim_id_base}")
        except Exception as e:
            if logger:
                logger(f"[COUNTERFACTUAL] Error logging base trace: {e}")
        try:
            log_simulation_trace(fork_trace, tag=f"counterfactual_fork_{sim_id_fork}")
        except Exception as e:
            if logger:
                logger(f"[COUNTERFACTUAL] Error logging fork trace: {e}")
    elif logger:
        logger("[COUNTERFACTUAL] log_simulation_trace not available. Skipping trace logging.")

    return {
        "base_trace": base_trace,
        "fork_trace": fork_trace,
        "divergence": divergence,
        "base_arc": base_arc,
        "fork_arc": fork_arc,
    }

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
    parser.add_argument("--gravity", choices=["on", "off", "adaptive"], default="adaptive",
                       help="Control Symbolic Gravity: 'on' to enable, 'off' to disable, 'adaptive' for dynamic adjustment")
    parser.add_argument("--explain-gravity", type=str, help="Explain gravity corrections for specified variable")
    parser.add_argument("--explain-format", choices=["text", "html", "json"], default="text",
                       help="Format for gravity explanation output (default: text)")
    args = parser.parse_args()

    # Determine gravity_enabled based on CLI argument
    gravity_enabled_cli = args.gravity != "off"

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

        # Configure gravity feature based on CLI argument
        if args.gravity == "off":
            # Disable gravity by setting _gravity_disable flag
            # Use setattr for dynamic attribute
            setattr(ws, '_gravity_disable', True)
            print("Symbolic Gravity: DISABLED")
        elif args.gravity == "on":
            # Enable gravity and make it non-adaptive
            setattr(ws, '_gravity_disable', False)
            # Initialize gravity fabric with non-adaptive config
            from symbolic_system.gravity.gravity_config import ResidualGravityConfig
            from symbolic_system.gravity.symbolic_gravity_fabric import create_default_fabric
            config = ResidualGravityConfig(enable_adaptive_lambda=False)
            # Create and attach the fabric
            setattr(ws, '_gravity_fabric', create_default_fabric(config=config))
            print("Symbolic Gravity: ENABLED (fixed strength)")
        else:  # adaptive
            # Enable gravity with adaptive strength
            setattr(ws, '_gravity_disable', False)
            print("Symbolic Gravity: ENABLED (adaptive)")

        output = simulate_forward(
            ws,
            turns=args.turns,
            use_symbolism=True,
            return_mode="full" if args.full else "summary",
            gravity_enabled=gravity_enabled_cli # Pass gravity_enabled from CLI
        )
        for r in output:
            gravity_info = ""
            if any(k.startswith("gravity_") for k in r.keys()):
                gravity_info = f" | Gravity: {r.get('gravity_magnitude', 0.0):.3f}"
            print(f"Turn {r['turn']} | Δ: {r['deltas']} | Tag: {r.get('symbolic_tag', '—')}{gravity_info}")
            
        # Handle gravity explanation if requested
        if args.explain_gravity:
            try:
                from simulation_engine.worldstate_monitor import display_gravity_correction_details
                
                print(f"\nGenerating gravity explanation for variable '{args.explain_gravity}'")
                result_path = display_gravity_correction_details(
                    trace_data=output,
                    variable_name=args.explain_gravity,
                    output_format=args.explain_format
                )
                
                if result_path and args.explain_format != "text":
                    print(f"\nGravity explanation saved to: {result_path}")
            except ImportError:
                print("Error: Could not import gravity explanation functionality.")
                print("Make sure the diagnostics module is available.")
