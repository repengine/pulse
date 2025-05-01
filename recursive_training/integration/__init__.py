"""
Recursive Training System Integration Components

This module provides components for integrating the Recursive Training System
with Pulse's existing infrastructure. It includes adapters, controllers, and
utilities to ensure seamless interaction between systems.

Components:
- PulseAdapter: Interface between the Recursive Training System and Pulse components
- CostController: Central service for monitoring and limiting API costs
"""

from recursive_training.integration.pulse_adapter import PulseAdapter, get_pulse_adapter
from recursive_training.integration.cost_controller import (
    CostController, 
    CostStatus, 
    CostLimitException, 
    get_cost_controller
)

__all__ = [
    'PulseAdapter',
    'get_pulse_adapter',
    'CostController',
    'CostStatus',
    'CostLimitException',
    'get_cost_controller'
]