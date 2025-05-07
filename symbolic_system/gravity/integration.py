"""
integration.py

Integration layer between the Symbolic Gravity system and the existing Pulse codebase.
Provides adapters and hooks for transitioning from the overlay system to the 
pillar-based gravity fabric approach.

Author: Pulse v3.5
"""

from __future__ import annotations
import logging
from typing import Dict, List, Optional, Union, Any, Callable, Tuple
import functools
import numpy as np

from simulation_engine.worldstate import WorldState
from simulation_engine.state_mutation import adjust_overlay

from symbolic_system.gravity.symbolic_pillars import SymbolicPillarSystem
from symbolic_system.gravity.residual_gravity_engine import ResidualGravityEngine
from symbolic_system.gravity.gravity_fabric import SymbolicGravityFabric
from symbolic_system.gravity.gravity_config import ResidualGravityConfig

logger = logging.getLogger(__name__)

# Global instances used for integration with existing code
_pillar_system: Optional[SymbolicPillarSystem] = None
_gravity_fabric: Optional[SymbolicGravityFabric] = None
_gravity_enabled: bool = False


def initialize_gravity_system(config: Optional[ResidualGravityConfig] = None) -> Tuple[SymbolicPillarSystem, SymbolicGravityFabric]:
    """
    Initialize the global instances of the gravity system components.
    
    Parameters
    ----------
    config : ResidualGravityConfig, optional
        Configuration for the gravity system. Uses defaults if None.
        
    Returns
    -------
    Tuple[SymbolicPillarSystem, SymbolicGravityFabric]
        The initialized pillar system and gravity fabric
    """
    global _pillar_system, _gravity_fabric, _gravity_enabled
    
    # Create the configuration if not provided
    config = config or ResidualGravityConfig()
    
    # Initialize the pillar system
    _pillar_system = SymbolicPillarSystem()
    
    # Initialize the gravity engine
    gravity_engine = ResidualGravityEngine(config=config)
    
    # Initialize the gravity fabric
    _gravity_fabric = SymbolicGravityFabric(
        pillar_system=_pillar_system,
        gravity_engine=gravity_engine,
        config=config
    )
    
    # Enable the gravity system
    _gravity_enabled = True
    
    logger.info("Symbolic Gravity system initialized")
    return _pillar_system, _gravity_fabric


def get_pillar_system() -> SymbolicPillarSystem:
    """
    Get the global pillar system instance, initializing if needed.
    
    Returns
    -------
    SymbolicPillarSystem
        The global pillar system
    """
    global _pillar_system
    if _pillar_system is None:
        initialize_gravity_system()
    return _pillar_system


def get_gravity_fabric() -> SymbolicGravityFabric:
    """
    Get the global gravity fabric instance, initializing if needed.
    
    Returns
    -------
    SymbolicGravityFabric
        The global gravity fabric
    """
    global _gravity_fabric
    if _gravity_fabric is None:
        initialize_gravity_system()
    return _gravity_fabric


def enable_gravity_system() -> None:
    """Enable the gravity system."""
    global _gravity_enabled
    _gravity_enabled = True
    logger.info("Symbolic Gravity system enabled")


def disable_gravity_system() -> None:
    """Disable the gravity system."""
    global _gravity_enabled
    _gravity_enabled = False
    logger.info("Symbolic Gravity system disabled")


def is_gravity_enabled() -> bool:
    """
    Check if the gravity system is enabled.
    
    Returns
    -------
    bool
        True if the gravity system is enabled
    """
    global _gravity_enabled
    return _gravity_enabled


def adapt_overlays_to_pillars(state: WorldState) -> None:
    """
    Adapt the current overlays in a WorldState to the pillar system.
    
    This is used during the transition period to ensure both systems
    remain synchronized. It copies overlay values to their corresponding pillars.
    
    Parameters
    ----------
    state : WorldState
        WorldState containing the overlay values
    """
    pillar_system = get_pillar_system()
    pillar_system.load_from_state(state)


def adapt_pillars_to_overlays(state: WorldState) -> None:
    """
    Adapt the current pillars back to the overlay system.
    
    Used during the transition period to keep the older overlay-based
    code functional while we migrate to the pillar system.
    
    Parameters
    ----------
    state : WorldState
        WorldState to update with pillar values
    """
    pillar_system = get_pillar_system()
    pillar_values = pillar_system.as_dict()
    
    for name, value in pillar_values.items():
        current = getattr(state.overlays, name, 0.0)
        if abs(current - value) > 0.001:  # Only adjust if there's a significant difference
            adjust_overlay(state, name, value - current)


# Simulation integration hooks

def pre_simulation_hook(state: WorldState) -> None:
    """
    Hook to run before simulation step.
    
    This adapts the current overlays to the pillar system.
    
    Parameters
    ----------
    state : WorldState
        Current simulation state
    """
    if not is_gravity_enabled():
        return
    
    # Sync overlays to pillars
    adapt_overlays_to_pillars(state)


def post_simulation_hook(state: WorldState) -> None:
    """
    Hook to run after simulation step.
    
    This adapts the pillar system back to overlays and 
    applies any natural pillar interactions.
    
    Parameters
    ----------
    state : WorldState
        Current simulation state
    """
    if not is_gravity_enabled():
        return
    
    # Apply pillar interactions
    pillar_system = get_pillar_system()
    pillar_system.apply_interactions()
    
    # Sync pillars back to overlays
    adapt_pillars_to_overlays(state)


def apply_gravity_correction(variable_name: str, predicted_value: float) -> float:
    """
    Apply a gravity correction to a predicted value.
    
    Parameters
    ----------
    variable_name : str
        Name of the variable being predicted
    predicted_value : float
        Original predicted value
        
    Returns
    -------
    float
        Corrected value after applying gravity
    """
    if not is_gravity_enabled():
        return predicted_value
    
    gravity_fabric = get_gravity_fabric()
    return gravity_fabric.apply_correction(variable_name, predicted_value)


def record_prediction_residual(
    variable_name: str, 
    predicted_value: float, 
    actual_value: float
) -> None:
    """
    Record a prediction residual to update the gravity system.
    
    Parameters
    ----------
    variable_name : str
        Name of the variable
    predicted_value : float
        Predicted value from the causal model
    actual_value : float
        Actual observed value
    """
    if not is_gravity_enabled():
        return
    
    gravity_fabric = get_gravity_fabric()
    gravity_fabric.record_residual(variable_name, predicted_value, actual_value)


def gravity_correction_decorator(func: Callable) -> Callable:
    """
    Decorator to apply gravity corrections to simulation functions.
    
    Parameters
    ----------
    func : Callable
        Function to decorate
        
    Returns
    -------
    Callable
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get original prediction
        result = func(*args, **kwargs)
        
        # Skip if gravity disabled or result isn't numeric
        if not is_gravity_enabled() or not isinstance(result, (int, float)):
            return result
        
        # Determine variable name from function or kwargs
        variable_name = kwargs.get('variable_name', func.__name__)
        
        # Apply gravity correction
        corrected = apply_gravity_correction(variable_name, result)
        
        if abs(corrected - result) > 0.001:  # Only log if significant change
            logger.debug(f"Gravity correction for {variable_name}: {result:.4f} → {corrected:.4f}")
            
        return corrected
    
    return wrapper


# Diagnostic functions

def get_gravity_diagnostic_report() -> Dict[str, Any]:
    """
    Get a comprehensive diagnostic report on the gravity system.
    
    Returns
    -------
    Dict[str, Any]
        Report with metrics and diagnostics
    """
    if not is_gravity_enabled() or _gravity_fabric is None:
        return {"status": "disabled"}
    
    return _gravity_fabric.generate_diagnostic_report()


def get_pillar_values() -> Dict[str, float]:
    """
    Get the current values of all pillars.
    
    Returns
    -------
    Dict[str, float]
        Dictionary mapping pillar names to their values
    """
    if not is_gravity_enabled() or _pillar_system is None:
        return {}
    
    return _pillar_system.as_dict()