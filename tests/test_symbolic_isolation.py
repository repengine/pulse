"""
test_symbolic_isolation.py

Tests for verifying proper isolation between the symbolic overlay system
and retrodiction training. This ensures that symbolic processing can be
disabled during performance-critical training operations.
"""

import unittest
from unittest.mock import MagicMock
import sys
import os

# Add parent directory to path to import Pulse modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation_engine.worldstate import WorldState
from symbolic_system.context import (
    symbolic_context,
    is_symbolic_enabled,
    enter_retrodiction_mode,
)
from symbolic_system.overlays import apply_overlay_interactions
import core.pulse_config
from core.pulse_config import ENABLE_SYMBOLIC_SYSTEM, SYMBOLIC_PROCESSING_MODES
# Import CURRENT_SYSTEM_MODE indirectly to ensure we're accessing the module variable


class TestSymbolicIsolation(unittest.TestCase):
    """Tests to verify proper isolation of the symbolic system"""

    def setUp(self):
        """Set up test environment"""
        # Save original config values to restore later
        self.original_enable = ENABLE_SYMBOLIC_SYSTEM
        self.original_modes = SYMBOLIC_PROCESSING_MODES.copy()
        self.original_mode = core.pulse_config.CURRENT_SYSTEM_MODE

    def tearDown(self):
        """Clean up after tests"""
        # Restore original config values
        global ENABLE_SYMBOLIC_SYSTEM, SYMBOLIC_PROCESSING_MODES
        ENABLE_SYMBOLIC_SYSTEM = self.original_enable
        SYMBOLIC_PROCESSING_MODES = self.original_modes
        core.pulse_config.CURRENT_SYSTEM_MODE = self.original_mode

    def test_symbolic_disabled_globally(self):
        """Test that all symbolic operations are skipped when disabled globally"""
        # Need to modify the module variable directly
        import core.pulse_config

        core.pulse_config.ENABLE_SYMBOLIC_SYSTEM = False

        state = WorldState()
        initial_hope = 0.5
        state.overlays.hope = initial_hope  # Set a known value

        # These calls should be no-ops when symbolic system is disabled
        from simulation_engine.state_mutation import adjust_overlay

        adjust_overlay(state, "hope", 0.1)

        # Value should not change
        self.assertEqual(state.overlays.hope, initial_hope)

    def test_symbolic_disabled_for_retrodiction(self):
        """Test that symbolic operations are skipped during retrodiction"""
        global SYMBOLIC_PROCESSING_MODES
        SYMBOLIC_PROCESSING_MODES["retrodiction"] = False

        state = WorldState()
        initial_hope = state.overlays.hope

        # Run in retrodiction context
        with enter_retrodiction_mode():
            from simulation_engine.state_mutation import adjust_overlay

            adjust_overlay(state, "hope", 0.1)

            # Apply overlay interactions
            apply_overlay_interactions(state)

        # Value should not change in retrodiction mode
        self.assertEqual(state.overlays.hope, initial_hope)

    def test_context_manager(self):
        """Test that the context manager properly sets and restores modes"""
        original_mode = core.pulse_config.CURRENT_SYSTEM_MODE

        # Change mode within context
        with symbolic_context("retrodiction"):
            self.assertEqual(core.pulse_config.CURRENT_SYSTEM_MODE, "retrodiction")

        # Mode should be restored
        self.assertEqual(core.pulse_config.CURRENT_SYSTEM_MODE, original_mode)

    def test_explicit_override(self):
        """Test explicitly enabling symbolic processing in retrodiction mode"""
        state = WorldState()
        state.overlays.hope = 0.5

        # Normally disabled in retrodiction
        SYMBOLIC_PROCESSING_MODES["retrodiction"] = False

        # But we can override it
        with enter_retrodiction_mode(enable_symbolic=True):
            self.assertTrue(is_symbolic_enabled())

            # Symbolic operations should work
            from simulation_engine.state_mutation import adjust_overlay

            adjust_overlay(state, "hope", 0.1)

        # Value should have changed
        self.assertAlmostEqual(state.overlays.hope, 0.6)

    def test_minimal_processing_in_retrodiction(self):
        """Test that minimal processing is used in retrodiction mode when enabled"""
        state = WorldState()
        state.overlays.hope = 0.8  # Set hope high
        state.overlays.trust = 0.5  # Set trust to neutral

        # Enable symbolic in retrodiction but with minimal processing
        SYMBOLIC_PROCESSING_MODES["retrodiction"] = True

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
