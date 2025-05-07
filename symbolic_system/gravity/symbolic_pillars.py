"""
symbolic_pillars.py

This module implements the concept of Symbolic Pillars - vertically stacked
data points that grow and shrink, collectively supporting the Symbolic Gravity
Fabric. These pillars represent symbolic concepts (like Hope, Despair, etc.)
and their cumulative effect influences simulation corrections.

Author: Pulse v3.5
"""

import logging
import math
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Set, Union
from datetime import datetime, timedelta
from collections import deque

from symbolic_system.symbolic_utils import symbolic_tension_score

logger = logging.getLogger(__name__)


class SymbolicPillar:
    """
    A symbolic pillar represents a vertical stack of data points that grows and
    shrinks based on incoming data. The height of the pillar (its intensity)
    influences the symbolic gravity fabric.
    
    Attributes
    ----------
    name : str
        Name of the pillar
    intensity : float
        Current intensity/height of the pillar (0.0-1.0)
    max_capacity : float
        Maximum capacity of the pillar
    data_points : List[Tuple[Any, float]]
        Stack of data points with weights
    velocity : float
        Rate of change of intensity
    last_update_time : datetime
        Time of last update
    active : bool
        Whether the pillar is active
    intensity_history : List[float]
        History of intensity values
    """
    
    def __init__(self, 
                 name: str, 
                 initial_intensity: float = 0.0,
                 max_capacity: float = 1.0):
        """
        Initialize a symbolic pillar.
        
        Parameters
        ----------
        name : str
            Name of the pillar
        initial_intensity : float, optional
            Initial intensity of the pillar, by default 0.0
        max_capacity : float, optional
            Maximum capacity of the pillar, by default 1.0
        """
        self.name = name
        self.intensity = min(max(0.0, initial_intensity), max_capacity)
        self.max_capacity = max_capacity
        self.data_points: List[Tuple[Any, float]] = []
        self.velocity = 0.0
        self.last_update_time = datetime.now()
        self.active = True
        self.intensity_history: List[float] = [self.intensity]
    
    def add_data_point(self, 
                      data_point: Any, 
                      weight: float = 1.0) -> None:
        """
        Add a data point to the pillar.
        
        Parameters
        ----------
        data_point : Any
            Data point to add
        weight : float, optional
            Weight of the data point, by default 1.0
        """
        self.data_points.append((data_point, weight))
        self._update_intensity()
    
    def _update_intensity(self) -> None:
        """
        Update the intensity based on data points.
        """
        if not self.data_points:
            return
        
        # Calculate the sum of weights
        total_weight = sum(weight for _, weight in self.data_points)
        
        # Update the intensity
        new_intensity = min(total_weight / self.max_capacity, 1.0)
        
        # Calculate velocity (rate of change)
        old_intensity = self.intensity
        self.velocity = new_intensity - old_intensity
        
        # Update intensity
        self.intensity = new_intensity
        
        # Update history
        self.intensity_history.append(self.intensity)
        
        # Cap history length to prevent memory issues
        if len(self.intensity_history) > 100:
            self.intensity_history = self.intensity_history[-100:]
        
        # Update timestamp
        self.last_update_time = datetime.now()
    
    def decay(self, decay_rate: float = 0.01) -> float:
        """
        Apply decay to the pillar intensity.
        
        Parameters
        ----------
        decay_rate : float, optional
            Decay rate per step, by default 0.01
            
        Returns
        -------
        float
            Amount decayed
        """
        old_intensity = self.intensity
        
        # Apply linear decay
        self.intensity = max(0.0, self.intensity - decay_rate)
        
        # Record in history
        self.intensity_history.append(self.intensity)
        
        # Cap history length
        if len(self.intensity_history) > 100:
            self.intensity_history = self.intensity_history[-100:]
        
        # Update velocity
        self.velocity = self.intensity - old_intensity
        
        # Return amount decayed
        return old_intensity - self.intensity
    
    def set_intensity(self, intensity: float) -> None:
        """
        Set the intensity directly.
        
        Parameters
        ----------
        intensity : float
            New intensity value
        """
        old_intensity = self.intensity
        self.intensity = min(max(0.0, intensity), self.max_capacity)
        
        # Update velocity
        self.velocity = self.intensity - old_intensity
        
        # Record in history
        self.intensity_history.append(self.intensity)
        
        # Cap history length
        if len(self.intensity_history) > 100:
            self.intensity_history = self.intensity_history[-100:]
        
        # Update timestamp
        self.last_update_time = datetime.now()
    
    def get_growth_rate(self) -> float:
        """
        Calculate the growth rate over the recent history.
        
        Returns
        -------
        float
            Growth rate (-1.0 to 1.0)
        """
        if len(self.intensity_history) < 2:
            return 0.0
        
        # Get recent history (last 5 points or all if less)
        history = self.intensity_history[-5:]
        
        if len(history) < 2:
            return 0.0
        
        # Calculate average change
        changes = [history[i] - history[i-1] for i in range(1, len(history))]
        avg_change = sum(changes) / len(changes)
        
        # Normalize to -1.0 to 1.0 range
        return min(max(-1.0, avg_change * 10), 1.0)
    
    def get_basis_value(self, time_step: Optional[int] = None) -> float:
        """
        Get the basis function value for this pillar.
        This is s_t(k) in the mathematical notation.
        
        Parameters
        ----------
        time_step : Optional[int], optional
            Time step for which to get the value, by default None
            
        Returns
        -------
        float
            Basis function value
        """
        # Compute the basis function value as the intensity, which represents
        # the cumulative effect of all stacked data points
        
        # For dynamic basis functions, we could apply different weights to 
        # data points based on recency or other factors
        if time_step is not None and len(self.intensity_history) > time_step:
            # Use historical value if requested
            return self.intensity_history[-time_step]
            
        # Use current intensity as the basis function value by default
        return self.intensity
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert pillar to dictionary for serialization.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary representation of pillar
        """
        # Include recent data points for visualization and detailed tracking
        recent_data = []
        if self.data_points:
            # Include up to 10 most recent data points
            recent_points = self.data_points[-10:]
            for data_point, weight in recent_points:
                # If data point has a string representation, use it
                if hasattr(data_point, '__str__'):
                    point_str = str(data_point)
                    # Truncate if too long
                    if len(point_str) > 50:
                        point_str = point_str[:47] + "..."
                else:
                    point_str = "Non-string data point"
                
                recent_data.append({
                    "data": point_str,
                    "weight": weight
                })
        
        # Calculate trend from growth rate
        growth_rate = self.get_growth_rate()
        trend = 1 if growth_rate > 0.1 else (-1 if growth_rate < -0.1 else 0)
        
        return {
            "name": self.name,
            "intensity": self.intensity,
            "max_capacity": self.max_capacity,
            "data_points_count": len(self.data_points),
            "velocity": self.velocity,
            "last_update_time": self.last_update_time,
            "active": self.active,
            "growth_rate": growth_rate,
            "trend": trend,
            "recent_data": recent_data,
            "height": self.intensity * 100  # Scaled height for visualization
        }


class SymbolicPillarSystem:
    """
    A system of symbolic pillars that collectively support the symbolic gravity fabric.
    
    Attributes
    ----------
    pillars : Dict[str, SymbolicPillar]
        Mapping from pillar names to pillar objects
    interaction_matrix : Dict[Tuple[str, str], float]
        Matrix of interactions between pillars
    last_update_time : datetime
        Time of last update
    config : Any
        Configuration for the system
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize a symbolic pillar system.
        
        Parameters
        ----------
        config : Optional[Any], optional
            Configuration for the system, by default None
        """
        self.pillars: Dict[str, SymbolicPillar] = {}
        self.interaction_matrix: Dict[Tuple[str, str], float] = {}
        self.last_update_time = datetime.now()
        self.config = config
        
        # Initialize from config if provided
        if config:
            self.decay_rate = config.decay_rate
            self.interaction_strength = config.interaction_strength
            
            # Set up logging
            log_level = getattr(logging, config.log_level, logging.INFO)
            logger.setLevel(log_level)
        else:
            self.decay_rate = 0.01
            self.interaction_strength = 0.1
            logger.setLevel(logging.INFO)
    
    def register_pillar(self, 
                      name: str, 
                      initial_intensity: float = 0.0,
                      max_capacity: float = 1.0) -> SymbolicPillar:
        """
        Register a new pillar.
        
        Parameters
        ----------
        name : str
            Name of the pillar
        initial_intensity : float, optional
            Initial intensity, by default 0.0
        max_capacity : float, optional
            Maximum capacity, by default 1.0
            
        Returns
        -------
        SymbolicPillar
            The created pillar
        """
        # Skip if already exists
        if name in self.pillars:
            return self.pillars[name]
        
        # Create and register new pillar
        pillar = SymbolicPillar(
            name=name,
            initial_intensity=initial_intensity,
            max_capacity=max_capacity
        )
        
        self.pillars[name] = pillar
        logger.debug(f"Registered new pillar: {name} (intensity={initial_intensity})")
        
        return pillar
    
    def has_pillar(self, name: str) -> bool:
        """
        Check if a pillar exists.
        
        Parameters
        ----------
        name : str
            Name of the pillar
            
        Returns
        -------
        bool
            Whether the pillar exists
        """
        return name in self.pillars
    
    def update_pillar(self, 
                     name: str, 
                     intensity: Optional[float] = None,
                     data_point: Optional[Any] = None,
                     weight: float = 1.0) -> None:
        """
        Update a pillar's intensity or add a data point.
        
        Parameters
        ----------
        name : str
            Name of the pillar
        intensity : Optional[float], optional
            New intensity value, by default None
        data_point : Optional[Any], optional
            Data point to add, by default None
        weight : float, optional
            Weight of the data point, by default 1.0
        """
        # Create pillar if it doesn't exist
        if name not in self.pillars:
            self.register_pillar(name)
        
        pillar = self.pillars[name]
        
        # Update intensity or add data point
        if intensity is not None:
            pillar.set_intensity(intensity)
        elif data_point is not None:
            pillar.add_data_point(data_point, weight)
    
    def step(self) -> None:
        """
        Advance the system state by one step.
        
        This applies decay and interactions between pillars.
        """
        # Apply decay to all pillars
        for pillar in self.pillars.values():
            pillar.decay(self.decay_rate)
        
        # Apply interactions
        self._apply_interactions()
        
        # Update timestamp
        self.last_update_time = datetime.now()
    
    def _apply_interactions(self) -> None:
        """
        Apply interactions between pillars.
        """
        # Skip if no interactions or no pillars
        if not self.interaction_matrix or len(self.pillars) < 2:
            return
        
        # Copy current intensities to avoid interference
        current_intensities = {name: pillar.intensity for name, pillar in self.pillars.items()}
        
        # Apply interactions
        for (name1, name2), strength in self.interaction_matrix.items():
            if name1 in self.pillars and name2 in self.pillars:
                # Skip if either pillar has zero intensity
                if current_intensities[name1] < 1e-6 or current_intensities[name2] < 1e-6:
                    continue
                
                # Calculate interaction effect
                effect = strength * min(current_intensities[name1], current_intensities[name2]) * self.interaction_strength
                
                # Apply effect
                if effect > 0:
                    # Enhancing interaction
                    self.pillars[name1].set_intensity(current_intensities[name1] + effect)
                    self.pillars[name2].set_intensity(current_intensities[name2] + effect)
                else:
                    # Opposing interaction
                    self.pillars[name1].set_intensity(current_intensities[name1] + effect)
                    self.pillars[name2].set_intensity(current_intensities[name2] + effect)
    
    def set_interaction(self, pillar1: str, pillar2: str, strength: float) -> None:
        """
        Set the interaction strength between two pillars.
        
        Parameters
        ----------
        pillar1 : str
            Name of the first pillar
        pillar2 : str
            Name of the second pillar
        strength : float
            Interaction strength (-1.0 to 1.0)
        """
        # Create pillars if they don't exist
        if pillar1 not in self.pillars:
            self.register_pillar(pillar1)
        if pillar2 not in self.pillars:
            self.register_pillar(pillar2)
        
        # Sort pillar names to ensure consistent key
        name_pair = sorted([pillar1, pillar2])
        key: Tuple[str, str] = (name_pair[0], name_pair[1])
        
        # Set interaction strength
        self.interaction_matrix[key] = min(max(-1.0, strength), 1.0)
    
    def get_basis_vector(self, time_step: Optional[int] = None) -> Dict[str, float]:
        """
        Get the basis vector of all pillars.
        
        This returns s_t in the mathematical notation from the task.
        
        Parameters
        ----------
        time_step : Optional[int], optional
            Time step for which to get the values, by default None
            
        Returns
        -------
        Dict[str, float]
            Mapping from pillar names to basis function values
        """
        return {name: pillar.get_basis_value(time_step) for name, pillar in self.pillars.items()}
    
    def get_pillar(self, name: str) -> Optional[SymbolicPillar]:
        """
        Get a pillar by name.
        
        Parameters
        ----------
        name : str
            Name of the pillar
            
        Returns
        -------
        Optional[SymbolicPillar]
            The pillar, or None if not found
        """
        return self.pillars.get(name)
    
    def get_top_pillars(self, n: int = 5) -> List[Tuple[str, SymbolicPillar]]:
        """
        Get the top N pillars by intensity.
        
        Parameters
        ----------
        n : int, optional
            Number of pillars to return, by default 5
            
        Returns
        -------
        List[Tuple[str, SymbolicPillar]]
            List of (name, pillar) pairs, sorted by intensity
        """
        return sorted(
            self.pillars.items(),
            key=lambda x: x[1].intensity,
            reverse=True
        )[:n]
    
    def get_dominant_pillars(self, threshold: float = 0.5) -> List[Tuple[str, SymbolicPillar]]:
        """
        Get pillars with intensity above a threshold.
        
        Parameters
        ----------
        threshold : float, optional
            Intensity threshold, by default 0.5
            
        Returns
        -------
        List[Tuple[str, SymbolicPillar]]
            List of (name, pillar) pairs
        """
        return [
            (name, pillar) for name, pillar in self.pillars.items()
            if pillar.intensity >= threshold
        ]
    
    def get_basis_support(self) -> float:
        """
        Calculate the total support provided by all pillars.
        
        Returns
        -------
        float
            Total support
        """
        return sum(pillar.intensity for pillar in self.pillars.values())
    
    def _are_opposing(self, pillar1: str, pillar2: str) -> bool:
        """
        Check if two pillars are opposing each other.
        
        Parameters
        ----------
        pillar1 : str
            Name of the first pillar
        pillar2 : str
            Name of the second pillar
            
        Returns
        -------
        bool
            Whether the pillars are opposing
        """
        name_pair = sorted([pillar1, pillar2])
        key: Tuple[str, str] = (name_pair[0], name_pair[1])
        return key in self.interaction_matrix and self.interaction_matrix[key] < 0
    
    def _are_similar(self, pillar1: str, pillar2: str) -> bool:
        """
        Check if two pillars are similar or enhancing each other.
        
        Parameters
        ----------
        pillar1 : str
            Name of the first pillar
        pillar2 : str
            Name of the second pillar
            
        Returns
        -------
        bool
            Whether the pillars are similar
        """
        name_pair = sorted([pillar1, pillar2])
        key: Tuple[str, str] = (name_pair[0], name_pair[1])
        return key in self.interaction_matrix and self.interaction_matrix[key] > 0
    
    def symbolic_tension_score(self) -> float:
        """
        Calculate the overall symbolic tension in the system.
        
        Returns
        -------
        float
            Tension score (0.0 to 1.0)
        """
        # Get current symbolic overlay values
        overlays = {name: pillar.intensity for name, pillar in self.pillars.items()}
        
        # Use symb_utils function if available
        try:
            return symbolic_tension_score(overlays)
        except ImportError:
            # Fallback implementation if imported function not available
            tension = 0.0
            
            # Check for hope/despair opposition
            if "hope" in overlays and "despair" in overlays:
                hope = overlays["hope"]
                despair = overlays["despair"]
                tension += hope * despair
            
            # Check for rage/trust opposition
            if "rage" in overlays and "trust" in overlays:
                rage = overlays["rage"]
                trust = overlays["trust"]
                tension += rage * trust
            
            # Add other known oppositions
            if "fatigue" in overlays and "hope" in overlays:
                fatigue = overlays["fatigue"]
                hope = overlays["hope"]
                tension += fatigue * hope * 0.5
            
            return min(1.0, tension)
    
    def generate_visualization_data(self) -> Dict[str, Any]:
        """
        Generate data for visualization.
        
        Returns
        -------
        Dict[str, Any]
            Visualization data
        """
        pillar_data = []
        
        # Get top pillars for visualization
        top_pillars = self.get_top_pillars(n=10)
        
        for name, pillar in top_pillars:
            # Extract recent data point history for timeline visualization
            data_history = []
            for i, (data_point, weight) in enumerate(pillar.data_points[-20:]):
                time_offset = i - len(pillar.data_points[-20:])
                data_history.append({
                    "time_offset": time_offset,
                    "weight": weight,
                    "data": str(data_point) if hasattr(data_point, "__str__") else "Data point"
                })
            
            # Calculate growth indicator (-1, 0, 1)
            growth_rate = pillar.get_growth_rate()
            growth_indicator = 1 if growth_rate > 0.1 else (-1 if growth_rate < -0.1 else 0)
            
            pillar_data.append({
                "name": name,
                "intensity": pillar.intensity,
                "velocity": pillar.velocity,
                "height": pillar.intensity * 100,  # Scale for visualization
                "data_points": len(pillar.data_points),
                "data_history": data_history,
                "growth_indicator": growth_indicator,
                "growth_rate": growth_rate
            })
        
        # Get interactions for visualization with enhanced metadata
        interactions = []
        for i, (name1, pillar1) in enumerate(top_pillars):
            for j, (name2, pillar2) in enumerate(top_pillars):
                if i < j:  # Only consider unique pairs
                    name_pair = sorted([name1, name2])
                    interaction_key: Tuple[str, str] = (name_pair[0], name_pair[1])
                    if interaction_key in self.interaction_matrix:
                        interaction = self.interaction_matrix[interaction_key]
                        if abs(interaction) > 0.01:  # Only include significant interactions
                            # Calculate interaction type
                            interaction_type = "enhancing" if interaction > 0 else "opposing"
                            if self._are_opposing(name1, name2):
                                interaction_type = "opposing"
                            elif self._are_similar(name1, name2):
                                interaction_type = "enhancing"
                                
                            interactions.append({
                                "source": name1,
                                "target": name2,
                                "strength": interaction,
                                "type": interaction_type,
                                "combined_intensity": (pillar1.intensity * pillar2.intensity) ** 0.5
                            })
        
        # Calculate fabric health metrics
        fabric_metrics = {
            "total_support": self.get_basis_support(),
            "symbolic_tension": self.symbolic_tension_score(),
            "pillar_count": len(self.pillars),
            "dominant_pillar_count": len(self.get_dominant_pillars()),
            "average_intensity": sum(p.intensity for p in self.pillars.values()) / max(1, len(self.pillars)),
            "fabric_stability": 1.0 - self.symbolic_tension_score()  # Higher is more stable
        }
        
        return {
            "pillars": pillar_data,
            "interactions": interactions,
            "fabric_metrics": fabric_metrics,
            "visualization_timestamp": datetime.now().isoformat()
        }
    
    def as_dict(self) -> Dict[str, float]:
        """
        Get a dictionary of pillar intensities.
        
        This method provides a simple mapping from pillar names to intensities,
        suitable for use with the residual gravity engine.
        
        Returns
        -------
        Dict[str, float]
            Mapping from pillar names to intensities
        """
        return {name: pillar.intensity for name, pillar in self.pillars.items()}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the pillar system to a dictionary for serialization.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary representation
        """
        return {
            "pillars": {name: pillar.to_dict() for name, pillar in self.pillars.items()},
            "interactions": {f"{k[0]}|{k[1]}": v for k, v in self.interaction_matrix.items()},
            "last_update_time": self.last_update_time.isoformat(),
            "decay_rate": self.decay_rate,
            "interaction_strength": self.interaction_strength,
            "metrics": {
                "total_support": self.get_basis_support(),
                "symbolic_tension": self.symbolic_tension_score(),
                "pillar_count": len(self.pillars),
                "dominant_pillars": len(self.get_dominant_pillars())
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], config: Optional[Any] = None) -> 'SymbolicPillarSystem':
        """
        Create a pillar system from a dictionary.
        
        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary representation
        config : Optional[Any], optional
            Configuration, by default None
            
        Returns
        -------
        SymbolicPillarSystem
            Created pillar system
        """
        system = cls(config=config)
        
        # Load pillars
        for name, pillar_data in data.get("pillars", {}).items():
            intensity = pillar_data.get("intensity", 0.0)
            max_capacity = pillar_data.get("max_capacity", 1.0)
            system.register_pillar(name, intensity, max_capacity)
        
        # Load interactions
        for key_str, value in data.get("interactions", {}).items():
            parts = key_str.split("|")
            if len(parts) == 2:
                system.set_interaction(parts[0], parts[1], value)
        
        # Set properties
        system.decay_rate = data.get("decay_rate", 0.01)
        system.interaction_strength = data.get("interaction_strength", 0.1)
        
        return system


if __name__ == "__main__":
    # Example usage
    system = SymbolicPillarSystem()
    
    # Register some pillars
    system.register_pillar("hope", 0.7)
    system.register_pillar("despair", 0.3)
    system.register_pillar("rage", 0.5)
    
    # Set interactions
    system.set_interaction("hope", "despair", -0.5)  # Opposing
    system.set_interaction("hope", "rage", -0.3)     # Opposing
    
    # Step forward
    system.step()
    
    # Get basis vector
    basis = system.get_basis_vector()
    print("Basis vector:", basis)
    
    # Get visualization data
    vis_data = system.generate_visualization_data()
    
    # Import visualization utilities if available
    try:
        from symbolic_system.gravity.visualization import visualize_gravity_fabric
        result = visualize_gravity_fabric(vis_data)
        print(result)
    except ImportError:
        print("Visualization utilities not available")
        print("Fabric metrics:", vis_data["fabric_metrics"])