"""
test_symbolic_isolation.py

Tests for verifying proper isolation between the symbolic overlay system
and retrodiction training. This ensures that symbolic processing can be
disabled during performance-critical training operations.
"""

import engine.pulse_config
from symbolic_system.overlays import apply_overlay_interactions
from symbolic_system.context import (
    symbolic_context,
    is_symbolic_enabled,
    enter_retrodiction_mode,
)
from engine.worldstate import WorldState
import unittest
from unittest import mock
from unittest.mock import MagicMock
import sys
import os
import importlib

# Add parent directory to path to import Pulse modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestSymbolicIsolation(unittest.TestCase):
    """Tests to verify proper isolation of the symbolic system"""

    def test_symbolic_disabled_globally(self):
        """Test that all symbolic operations are skipped when disabled globally"""
        with mock.patch("engine.pulse_config.ENABLE_SYMBOLIC_SYSTEM", False):
            # Reload modules that depend on engine.pulse_config to pick up the patched
            # value
            import symbolic_system.context
            import engine.state_mutation

            importlib.reload(symbolic_system.context)
            importlib.reload(engine.state_mutation)

            state = WorldState()
            initial_hope = 0.5
            state.overlays.hope = initial_hope  # Set a known value

            # These calls should be no-ops when symbolic system is disabled
            from engine.state_mutation import adjust_overlay

            adjust_overlay(state, "hope", 0.1)

            # Value should not change
            self.assertEqual(state.overlays.hope, initial_hope)

    def test_symbolic_disabled_for_retrodiction(self):
        """Test that symbolic operations are skipped during retrodiction"""
        with mock.patch.dict(
            "engine.pulse_config.SYMBOLIC_PROCESSING_MODES", {"retrodiction": False}
        ):
            state = WorldState()
            initial_hope = state.overlays.hope

            # Run in retrodiction context
            with enter_retrodiction_mode():
                from engine.state_mutation import adjust_overlay

                adjust_overlay(state, "hope", 0.1)

                # Apply overlay interactions
                apply_overlay_interactions(state)

            # Value should not change in retrodiction mode
            self.assertEqual(state.overlays.hope, initial_hope)

    def test_context_manager(self):
        """Test that the context manager properly sets and restores modes"""
        original_mode = (
            engine.pulse_config.CURRENT_SYSTEM_MODE
        )  # This line is not part of the patch, but needs to be updated if pulse_config is not directly imported.

        # Change mode within context
        with symbolic_context("retrodiction"):
            # This line is not part of the patch, but needs to be updated if
            # pulse_config is not directly imported.
            self.assertEqual(engine.pulse_config.CURRENT_SYSTEM_MODE, "retrodiction")

        # Mode should be restored
        # This line is not part of the patch, but needs to be updated if
        # pulse_config is not directly imported.
        self.assertEqual(engine.pulse_config.CURRENT_SYSTEM_MODE, original_mode)

    def test_explicit_override(self):
        """Test explicitly enabling symbolic processing in retrodiction mode"""
        state = WorldState()
        state.overlays.hope = 0.5

        with mock.patch(
            "engine.pulse_config.ENABLE_SYMBOLIC_SYSTEM", True
        ):  # Ensure symbolic system is enabled
            # Normally disabled in retrodiction
            with mock.patch.dict(
                "engine.pulse_config.SYMBOLIC_PROCESSING_MODES", {"retrodiction": False}
            ):
                # Reload modules that depend on engine.pulse_config to pick up the
                # patched value
                import symbolic_system.context
                import engine.state_mutation

                importlib.reload(symbolic_system.context)
                importlib.reload(engine.state_mutation)

                # But we can override it
                with enter_retrodiction_mode(enable_symbolic=True):
                    self.assertTrue(is_symbolic_enabled())

                    # Symbolic operations should work
                    from engine.state_mutation import adjust_overlay

                    adjust_overlay(state, "hope", 0.1)

                # Value should have changed
                self.assertAlmostEqual(state.overlays.hope, 0.6)

    def test_minimal_processing_in_retrodiction(self):
        """Test that minimal processing is used in retrodiction mode when enabled"""
        state = WorldState()
        state.overlays.hope = 0.8  # Set hope high
        state.overlays.trust = 0.5  # Set trust to neutral

        with mock.patch(
            "engine.pulse_config.ENABLE_SYMBOLIC_SYSTEM", True
        ):  # Ensure symbolic system is enabled
            # Enable symbolic in retrodiction but with minimal processing
            with mock.patch.dict(
                "engine.pulse_config.SYMBOLIC_PROCESSING_MODES", {"retrodiction": True}
            ):
                # Reload modules that depend on engine.pulse_config to pick up the
                # patched value
                import symbolic_system.context
                import engine.state_mutation

                importlib.reload(symbolic_system.context)
                importlib.reload(engine.state_mutation)

                # Set up mock for logging to check if it's called
                state.log_event = MagicMock()

                with enter_retrodiction_mode(enable_symbolic=True):
                    # Apply overlay interactions
                    apply_overlay_interactions(state)

                    # Trust should increase (minimal processing still does this)
                    self.assertGreater(state.overlays.trust, 0.5)

                    # But no event logging should occur in minimal mode
                    state.log_event.assert_not_called()


if __name__ == "__main__":
    unittest.main()
