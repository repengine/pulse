"""
symbolic_gravity_fabric.py

The implementation of the Symbolic Gravity Fabric, which acts as a corrective layer
between the causal simulation and observed reality. The fabric is supported by
Symbolic Pillars that grow and shrink based on incoming data, collectively creating
a "gravity field" that pulls simulation predictions toward observed reality.

This module is the core of the Symbolic Gravity Theory in Pulse.

Mathematical representation:
1. Causal core: x̂_t+1 = f(x_t, u_t)
2. Reality feed: y_t+1
3. Residual field: r_t+1 = y_t+1 - x̂_t+1
4. Symbolic pillars: s_t(k) (Hope, Despair, Rage, etc.)
5. Gravity function: g_t+1 = ∑_k w_k s_t(k)
6. Corrected state: x*_t+1 = x̂_t+1 + λ g_t+1

Author: Pulse v3.5
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from datetime import datetime

from symbolic_system.gravity.engines.residual_gravity_engine import ResidualGravityEngine, GravityEngineConfig
from symbolic_system.gravity.symbolic_pillars import SymbolicPillarSystem

logger = logging.getLogger(__name__)


class SymbolicGravityFabric:
    """
    The Symbolic Gravity Fabric connects symbolic pillars to simulation corrections.
    
    This fabric creates a dynamic correction field that adapts to systemic errors
    in the causal simulation by learning correlations between symbolic pillars
    and simulation residuals. The correction is applied as a "gravity" force
    that pulls simulated values toward observed reality.
    
    Attributes
    ----------
    gravity_engine : ResidualGravityEngine
        Engine for computing gravity corrections based on symbolic pillars
    pillar_system : SymbolicPillarSystem
        System for managing symbolic pillars and their interactions
    active_variables : Set[str]
        Set of variable names that should receive gravity corrections
    """
    
    def __init__(self, 
                 gravity_engine: Optional[ResidualGravityEngine] = None,
                 pillar_system: Optional[SymbolicPillarSystem] = None,
                 config: Optional[Any] = None):
        """
        Initialize the Symbolic Gravity Fabric.
        
        Parameters
        ----------
        gravity_engine : Optional[ResidualGravityEngine], optional
            Pre-configured gravity engine, by default None
        pillar_system : Optional[SymbolicPillarSystem], optional
            Pre-configured pillar system, by default None
        config : Optional[Any], optional
            Configuration for the fabric, by default None
        """
        # Import here to avoid circular imports
        from symbolic_system.gravity.gravity_config import ResidualGravityConfig
        
        # Use provided components or create new ones
        # Create engine config if not provided directly
        if gravity_engine is None:
            engine_config = GravityEngineConfig(
                lambda_=config.lambda_ if config else None,
                regularization_strength=config.regularization if config else None,
                learning_rate=config.learning_rate if config else None,
                momentum_factor=config.momentum if config else None,
                circuit_breaker_threshold=config.circuit_breaker_threshold if config else None,
                max_correction=config.max_correction if config else None,
                enable_adaptive_lambda=config.enable_adaptive_lambda if config else None,
                enable_weight_pruning=config.enable_weight_pruning if config else None,
                weight_pruning_threshold=config.weight_pruning_threshold if config else None,
                fragility_threshold=config.fragility_threshold if config else None
            )
            # Use default values for dt and state_dimensionality
            # Create default pillar names
            default_pillar_names = ["hope", "despair", "rage", "fatigue", "trust"]
            self.gravity_engine = ResidualGravityEngine(
                config=engine_config,
                dt=1.0,  # Default placeholder
                state_dimensionality=1,  # Default placeholder
                pillar_names=default_pillar_names  # Add required parameter
            )
        else:
            self.gravity_engine = gravity_engine
        
        self.pillar_system = pillar_system or SymbolicPillarSystem(
            config=config
        )
        
        # Track which variables should receive corrections
        self.active_variables: Set[str] = set()
        
        # Initialize metrics
        self._metrics = {
            "total_corrections": 0,
            "correction_magnitudes": [],
            "last_update_time": datetime.now().isoformat(),
            "variable_efficiency": {}
        }
        
        # Initialize with default pillars if not already present
        for pillar in ["hope", "despair", "rage", "fatigue"]:
            if not self.pillar_system.has_pillar(pillar):
                self.pillar_system.register_pillar(pillar)
    
    def apply_correction(self,
                         variable_name: str,
                         sim_value: float,
                         symbol_vec: Optional[Dict[str, float]] = None
                         ) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """
        Apply gravity correction to a simulated value.
        
        This implements x*_t+1 = x̂_t+1 + λ g_t+1
        
        Parameters
        ----------
        variable_name : str
            Name of the variable to correct
        sim_value : float
            Simulated value to correct (x̂_t+1)
        symbol_vec : Optional[Dict[str, float]], optional
            Symbol vector, by default None (will use current pillar system state)
            
        Returns
        -------
        Tuple[float, float]
            (correction_amount, corrected_value)
        """
        # Skip correction if variable is not active
        if variable_name not in self.active_variables:
            return 0.0, sim_value
        
        # Get symbol vector if not provided
        if symbol_vec is None:
            symbol_vec = self.pillar_system.get_basis_vector()
        
        # Apply gravity correction
        correction, corrected = self.gravity_engine.apply_gravity_correction(
            sim_value, symbol_vec
        )
        
        # Update metrics
        self._metrics["total_corrections"] += 1
        self._metrics["correction_magnitudes"].append(abs(correction))
        self._metrics["last_update_time"] = datetime.now().isoformat()
        
        # Track efficiency per variable
        if variable_name not in self._metrics["variable_efficiency"]:
            self._metrics["variable_efficiency"][variable_name] = {
                "total": 0,
                "corrected": 0
            }
        self._metrics["variable_efficiency"][variable_name]["total"] += 1
        if abs(correction) > 1e-6:
            self._metrics["variable_efficiency"][variable_name]["corrected"] += 1
        
        return correction, corrected
    
    def bulk_apply_correction(self,
                            sim_vars: Dict[str, float],
                            symbol_vec: Optional[Dict[str, float]] = None
                            ) -> Dict[str, float]:
        """
        Apply gravity corrections to multiple variables at once.
        
        Parameters
        ----------
        sim_vars : Dict[str, float]
            Mapping from variable names to simulated values
        symbol_vec : Optional[Dict[str, float]], optional
            Symbol vector, by default None (will use current pillar system state)
            
        Returns
        -------
        Dict[str, float]
            Mapping from variable names to corrected values
        """
        # Get symbol vector if not provided
        if symbol_vec is None:
            symbol_vec = self.pillar_system.get_basis_vector()
        
        # Apply corrections to each active variable
        result = {}
        for var_name, value in sim_vars.items():
            # Only apply correction to active variables
            if var_name in self.active_variables:
                _, corrected = self.apply_correction(var_name, value, symbol_vec)
                result[var_name] = corrected
            else:
                result[var_name] = value
                
        return result
    
    def update_weights(self, 
                      residual: Dict[str, float], 
                      symbol_vec: Optional[Dict[str, float]] = None
                     ) -> None:
        """
        Update gravity weights based on residuals.
        
        Parameters
        ----------
        residual : Dict[str, float]
            Mapping from variable names to residuals (y_t+1 - x̂_t+1)
        symbol_vec : Optional[Dict[str, float]], optional
            Symbol vector, by default None (will use current pillar system state)
        """
        # Get symbol vector if not provided
        if symbol_vec is None:
            symbol_vec = self.pillar_system.get_basis_vector()
        
        # Update weights for each variable with non-zero residual
        for var_name, res_value in residual.items():
            if abs(res_value) > 1e-6:
                self.gravity_engine.update_weights(res_value, symbol_vec)
                
                # Add to active variables if not already there
                self.active_variables.add(var_name)
    
    def step(self, state: Any) -> None:
        """
        Step the fabric forward based on state updates.
        
        This allows the fabric to update its internal state based on
        the world state after a simulation step.
        
        Parameters
        ----------
        state : Any
            World state with overlays and variables
        """
        # Extract overlay intensities from state
        try:
            overlays = getattr(state, 'overlays', {})
            # Type ignore because Pylance doesn't understand dynamic attribute checking
            overlay_dict = overlays.as_dict() if hasattr(overlays, "as_dict") else overlays  # type: ignore
            
            # Update pillar intensities based on overlays
            for name, intensity in overlay_dict.items():
                if self.pillar_system.has_pillar(name):
                    self.pillar_system.update_pillar(name, intensity=intensity)
                else:
                    # Register missing pillar
                    self.pillar_system.register_pillar(name, initial_intensity=intensity)
            
            # Step the pillar system forward
            self.pillar_system.step()
        except Exception as e:
            logger.warning(f"Error in stepping gravity fabric: {e}")
    
    def register_variable(self, variable_name: str) -> None:
        """
        Register a variable to receive gravity corrections.
        
        Parameters
        ----------
        variable_name : str
            Name of the variable to register
        """
        self.active_variables.add(variable_name)
    
    def unregister_variable(self, variable_name: str) -> None:
        """
        Unregister a variable from receiving gravity corrections.
        
        Parameters
        ----------
        variable_name : str
            Name of the variable to unregister
        """
        if variable_name in self.active_variables:
            self.active_variables.remove(variable_name)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get fabric performance metrics.
        
        Returns
        -------
        Dict[str, Any]
            Performance metrics
        """
        metrics = dict(self._metrics)
        
        # Add derived metrics
        total_corr = len(metrics.get("correction_magnitudes", []))
        if total_corr > 0:
            metrics["mean_correction"] = sum(metrics["correction_magnitudes"]) / total_corr
            # Keep only the last 100 corrections for memory efficiency
            metrics["correction_magnitudes"] = metrics["correction_magnitudes"][-100:]
        else:
            metrics["mean_correction"] = 0.0
        
        # Add gravity engine metrics
        metrics["gravity_engine"] = self.gravity_engine.get_stats()
        
        # Add variable efficiency metrics
        for var, stats in metrics["variable_efficiency"].items():
            if stats["total"] > 0:
                stats["efficiency"] = stats["corrected"] / stats["total"]
            else:
                stats["efficiency"] = 0.0
        
        # Add active variable count
        metrics["active_variable_count"] = len(self.active_variables)
        
        return metrics
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """
        Get data for visualization.
        
        Returns
        -------
        Dict[str, Any]
            Visualization data
        """
        # Get pillar system visualization data
        pillar_data = self.pillar_system.generate_visualization_data()
        
        # Add gravity engine metrics
        gravity_metrics = self.gravity_engine.get_stats()
        
        # Combine into a single data structure
        return {
            "pillars": pillar_data.get("pillars", []),
            "interactions": pillar_data.get("interactions", []),
            "fabric_metrics": {
                **pillar_data.get("fabric_metrics", {}),
                "gravity_rms_weight": gravity_metrics.get("rms_weight", 0.0),
                "active_variables": len(self.active_variables),
                "mean_correction": self._metrics.get("mean_correction", 0.0)
            }
        }


def create_default_fabric(config=None) -> SymbolicGravityFabric:
    """
    Create a default Symbolic Gravity Fabric with standard configuration.
    
    Parameters
    ----------
    config : ResidualGravityConfig, optional
        Custom configuration for the gravity fabric, by default None
    
    Returns
    -------
    SymbolicGravityFabric
        Configured fabric instance
    """
    # Import here to avoid circular imports
    from symbolic_system.gravity.gravity_config import ResidualGravityConfig
    
    # Create default config if not provided
    if config is None:
        config = ResidualGravityConfig()
    
    # Create GravityEngineConfig from ResidualGravityConfig
    engine_config = GravityEngineConfig(
        lambda_=config.lambda_,
        regularization_strength=config.regularization,
        learning_rate=config.learning_rate,
        momentum_factor=config.momentum,
        circuit_breaker_threshold=config.circuit_breaker_threshold,
        max_correction=config.max_correction,
        enable_adaptive_lambda=config.enable_adaptive_lambda,
        enable_weight_pruning=config.enable_weight_pruning,
        weight_pruning_threshold=config.weight_pruning_threshold,
        fragility_threshold=config.fragility_threshold
    )
    
    # Create engines
    # Define standard pillar names
    standard_pillar_names = ["hope", "despair", "rage", "fatigue", "trust"]
    gravity_engine = ResidualGravityEngine(
        config=engine_config,
        dt=1.0,  # Default placeholder
        state_dimensionality=1,  # Default placeholder
        pillar_names=standard_pillar_names  # Add required parameter
    )
    pillar_system = SymbolicPillarSystem(config=config)
    
    # Create and return fabric
    fabric = SymbolicGravityFabric(
        gravity_engine=gravity_engine,
        pillar_system=pillar_system,
        config=config
    )
    
    # Register default variables
    default_variables = [
        "market_price", "volatility", "interest_rate", "inflation",
        "sentiment", "liquidity", "volume", "momentum"
    ]
    
    for var in default_variables:
        fabric.register_variable(var)
    
    return fabric


if __name__ == "__main__":
    # Example usage
    fabric = create_default_fabric()
    
    # Apply corrections to some variables
    simulated = {
        "market_price": 100.0,
        "volatility": 0.2,
        "sentiment": -0.3
    }
    
    # Update pillar intensities
    fabric.pillar_system.update_pillar("hope", intensity=0.7)
    fabric.pillar_system.update_pillar("despair", intensity=0.3)
    
    # Apply corrections
    corrected = fabric.bulk_apply_correction(simulated)
    
    # Print results
    print("Simulated:", simulated)
    print("Corrected:", corrected)
    
    # Update weights with some residuals
    residuals = {
        "market_price": 5.0,  # Reality was higher than simulation
        "volatility": -0.05   # Reality was lower than simulation
    }
    
    fabric.update_weights(residuals)
    
    # Apply corrections again to see the effect
    corrected_after = fabric.bulk_apply_correction(simulated)
    
    print("Corrected (after learning):", corrected_after)
    
    # Get metrics
    metrics = fabric.get_metrics()
    print("Metrics:", metrics)