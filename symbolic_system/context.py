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
from typing import Optional

# Import configuration
from core.pulse_config import (
    ENABLE_SYMBOLIC_SYSTEM,
    CURRENT_SYSTEM_MODE,
    SYMBOLIC_PROCESSING_MODES
)

logger = logging.getLogger(__name__)

@contextlib.contextmanager
def symbolic_context(mode: str, enabled: Optional[bool] = None):
    """
    Context manager to temporarily set the symbolic processing mode.
    
    Args:
        mode: System mode ("simulation", "retrodiction", "analysis", "forecasting")
        enabled: Explicitly enable/disable symbolic processing, or None to use mode default
    """
    # Access the global variables that will be modified
    global CURRENT_SYSTEM_MODE
    
    # Store original values to restore later
    original_mode = CURRENT_SYSTEM_MODE
    original_setting = None
    
    if enabled is not None:
        # If explicitly enabling/disabling, store the original setting for this mode
        original_setting = SYMBOLIC_PROCESSING_MODES.get(mode)
        SYMBOLIC_PROCESSING_MODES[mode] = enabled
    
    try:
        # Set the current mode
        CURRENT_SYSTEM_MODE = mode
        logger.debug(f"Switched to mode: {mode}, symbolic processing: {is_symbolic_enabled()}")
        
        # Yield control back to the caller
        yield
        
    finally:
        # Restore original values
        CURRENT_SYSTEM_MODE = original_mode
        
        if original_setting is not None:
            SYMBOLIC_PROCESSING_MODES[mode] = original_setting
            
        logger.debug(f"Restored mode to: {CURRENT_SYSTEM_MODE}")

def is_symbolic_enabled(mode: Optional[str] = None) -> bool:
    """
    Check if symbolic processing is enabled for current or specified mode.
    
    Args:
        mode: System mode to check, or None to use current mode
        
    Returns:
        bool: True if symbolic processing is enabled, False otherwise
    """
    # First check global toggle
    if not ENABLE_SYMBOLIC_SYSTEM:
        return False
    
    # Then check mode-specific setting
    check_mode = mode or CURRENT_SYSTEM_MODE
    return SYMBOLIC_PROCESSING_MODES.get(check_mode, True)
    
def enter_retrodiction_mode(enable_symbolic: bool = False):
    """
    Convenience function to enter retrodiction mode.
    
    Args:
        enable_symbolic: Whether to enable symbolic processing in retrodiction mode
    
    Returns:
        Context manager that will restore previous mode when exiting
    """
    return symbolic_context("retrodiction", enabled=enable_symbolic)

def enter_simulation_mode(enable_symbolic: bool = True):
    """
    Convenience function to enter simulation mode.
    
    Args:
        enable_symbolic: Whether to enable symbolic processing in simulation mode
    
    Returns:
        Context manager that will restore previous mode when exiting
    """
    return symbolic_context("simulation", enabled=enable_symbolic)