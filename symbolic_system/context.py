"""
context.py

Context management utilities for symbolic system processing.
Provides mechanisms for temporarily setting the symbolic processing mode
and checking if symbolic processing is enabled in the current context.

This module is essential for proper isolation between symbolic processing
and retrodiction training.
"""

import contextlib
import logging
from typing import Optional, ContextManager, Iterator, Generator, Any

# Import configuration

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def symbolic_context(mode: str, enabled: Optional[bool] = None) -> Generator[None, Any, None]:
    """
    Context manager to temporarily set the symbolic processing mode.

    Args:
        mode: System mode ("simulation", "retrodiction", "analysis", "forecasting")
        enabled: Explicitly enable/disable symbolic processing, or None to use mode default
    """
    # Directly access module variables to ensure we're using the latest values
    import core.pulse_config

    # Store original values to restore later
    original_mode = core.pulse_config.CURRENT_SYSTEM_MODE
    original_setting = None

    if enabled is not None:
        # If explicitly enabling/disabling, store the original setting for this mode
        original_setting = core.pulse_config.SYMBOLIC_PROCESSING_MODES.get(mode)
        core.pulse_config.SYMBOLIC_PROCESSING_MODES[mode] = enabled

    try:
        # Set the current mode in the module directly
        core.pulse_config.CURRENT_SYSTEM_MODE = mode
        logger.debug(
            f"Switched to mode: {mode}, symbolic processing: {is_symbolic_enabled()}"
        )

        # Yield control back to the caller
        yield

    finally:
        # Restore original values directly in the module
        core.pulse_config.CURRENT_SYSTEM_MODE = original_mode

        if original_setting is not None:
            core.pulse_config.SYMBOLIC_PROCESSING_MODES[mode] = original_setting

        logger.debug(f"Restored mode to: {core.pulse_config.CURRENT_SYSTEM_MODE}")


def is_symbolic_enabled(mode: Optional[str] = None) -> bool:
    """
    Check if symbolic processing is enabled for current or specified mode.

    Args:
        mode: System mode to check, or None to use current mode

    Returns:
        bool: True if symbolic processing is enabled, False otherwise
    """
    # Get fresh values directly from the module
    import core.pulse_config

    # First check global toggle
    if not core.pulse_config.ENABLE_SYMBOLIC_SYSTEM:
        return False

    # Then check mode-specific setting
    check_mode = mode or core.pulse_config.CURRENT_SYSTEM_MODE
    return core.pulse_config.SYMBOLIC_PROCESSING_MODES.get(check_mode, True)


def enter_retrodiction_mode(enable_symbolic: bool = False) -> ContextManager[None]:
    """
    Convenience function to enter retrodiction mode.

    Args:
        enable_symbolic: Whether to enable symbolic processing in retrodiction mode

    Returns:
        Context manager that will restore previous mode when exiting
    """
    return symbolic_context("retrodiction", enabled=enable_symbolic)


def enter_simulation_mode(enable_symbolic: bool = True) -> ContextManager[None]:
    """
    Convenience function to enter simulation mode.

    Args:
        enable_symbolic: Whether to enable symbolic processing in simulation mode

    Returns:
        Context manager that will restore previous mode when exiting
    """
    return symbolic_context("simulation", enabled=enable_symbolic)
