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
from typing import Callable, Optional


def run_turn(
    state: WorldState,
    rule_fn: Optional[Callable[[WorldState], None]] = None,
    decay_rate: float = 0.01,
    verbose: bool = True
) -> list[dict]:
    """
    Executes one simulation turn in the Pulse engine.

    Steps:
    1. Apply symbolic decay to all overlays
    2. Execute narrative/capital effects via causal_rules
    3. Execute structured causal rules (auditable)
    4. Run optional external logic
    5. Increment turn

    Returns:
        list: Rule audit log (rule ID, tags, deltas)
    """

    # Step 1: Symbolic decay (for each overlay variable)
    for overlay_name in state.overlays.as_dict():
        decay_overlay(state, overlay_name, rate=decay_rate)

    # Step 2: Apply symbolic and capital shifts (non-audited)
    apply_causal_rules(state)

    # Step 3: Run structured rule engine and capture audit log
    rule_execution_log = run_rules(state, verbose=verbose)

    # Step 4: Optional injected logic (for testing or external simulation branches)
    if rule_fn:
        rule_fn(state)

    # Step 5: Advance the simulation
    state.increment_turn()

    return rule_execution_log