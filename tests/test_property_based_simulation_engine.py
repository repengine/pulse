# test_property_based_engine.py
"""
Property-based tests for engine.worldstate using hypothesis.
"""

from hypothesis import given, strategies as st
from engine.worldstate import WorldState


def is_valid_state(state: WorldState) -> bool:
    # Example: overlays must be between 0 and 1
    overlays = state.overlays.as_dict()
    return all(0.0 <= v <= 1.0 for v in overlays.values())


@given(turn=st.integers(min_value=0, max_value=1000))
def test_turn_increments_property(turn):
    state = WorldState(turn=turn)
    state.advance_turn()  # Updated to match the correct method name
    assert state.turn == turn + 1


@given(
    hope=st.floats(min_value=0, max_value=1),
    despair=st.floats(min_value=0, max_value=1),
    rage=st.floats(min_value=0, max_value=1),
    fatigue=st.floats(min_value=0, max_value=1),
    trust=st.floats(min_value=0, max_value=1),
)
def test_overlay_bounds(hope, despair, rage, fatigue, trust):
    from engine.worldstate import (
        SymbolicOverlays,
    )  # Updated to correct class name

    overlay = SymbolicOverlays(
        hope=hope, despair=despair, rage=rage, fatigue=fatigue, trust=trust
    )
    assert is_valid_state(WorldState(overlays=overlay))
