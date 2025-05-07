"""
Symbolic Gravity System Module

This module implements the Symbolic Gravity Fabric system, which acts as a
corrective layer between the causal simulation and observed reality.

Key components:
- SymbolicPillars: Vertical data structures that grow/shrink based on data
- ResidualGravityEngine: Learns relationships between pillars and simulation errors
- SymbolicGravityFabric: Connects pillars to simulation to apply corrections

The system uses symbolic pillars to support a gravity fabric that corrects
forecast outputs by pulling them toward observed reality.
"""

from symbolic_system.gravity.gravity_config import ResidualGravityConfig, get_config
from symbolic_system.gravity.symbolic_pillars import SymbolicPillar, SymbolicPillarSystem
from symbolic_system.gravity.residual_gravity_engine import ResidualGravityEngine
from symbolic_system.gravity.symbolic_gravity_fabric import SymbolicGravityFabric, create_default_fabric

__all__ = [
    'ResidualGravityConfig',
    'get_config',
    'SymbolicPillar',
    'SymbolicPillarSystem',
    'ResidualGravityEngine',
    'SymbolicGravityFabric',
    'create_default_fabric'
]