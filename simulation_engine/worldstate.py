"""
worldstate.py

Core world state representation for the Pulse simulation.
Contains overlays, capital exposure, variables, turn counter,
and event log for the current simulation state.

Author: Pulse v3.5
"""

import copy
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional

@dataclass
class SymbolicOverlays:
    """Symbolic overlays representing the emotional state of the simulation."""
    hope: float = 0.5
    despair: float = 0.5
    rage: float = 0.5
    fatigue: float = 0.5
    trust: float = 0.5
    
    def as_dict(self) -> Dict[str, float]:
        """Convert overlay values to a dictionary."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, float]) -> 'SymbolicOverlays':
        """Create overlays from a dictionary, with validation."""
        valid_keys = {'hope', 'despair', 'rage', 'fatigue', 'trust'}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        
        # Ensure all values are floats between 0 and 1
        for k, v in filtered_data.items():
            try:
                filtered_data[k] = max(0.0, min(1.0, float(v)))
            except (ValueError, TypeError):
                filtered_data[k] = 0.5
        
        # Set defaults for missing keys
        for key in valid_keys:
            if key not in filtered_data:
                filtered_data[key] = 0.5
                
        return SymbolicOverlays(**filtered_data)
    
    def validate(self) -> bool:
        """Validate that all overlay values are valid floats between 0 and 1."""
        try:
            for key, value in asdict(self).items():
                if not isinstance(value, float) or value < 0 or value > 1:
                    return False
            return True
        except Exception:
            return False

@dataclass
class CapitalExposure:
    """Capital exposure across different assets."""
    nvda: float = 0.0
    msft: float = 0.0
    ibit: float = 0.0
    spy: float = 0.0
    cash: float = 100000.0  # Default initial liquidity

    def as_dict(self) -> Dict[str, float]:
        """Convert capital exposure to a dictionary."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, float]) -> 'CapitalExposure':
        """Create capital exposure from a dictionary, with validation."""
        valid_keys = {'nvda', 'msft', 'ibit', 'spy', 'cash'}
        filtered_data = {}
        
        # Validate and convert values to floats
        for k, v in data.items():
            if k in valid_keys:
                try:
                    filtered_data[k] = float(v)
                except (ValueError, TypeError):
                    filtered_data[k] = 0.0
        
        # Set defaults for missing keys
        for key in valid_keys:
            if key not in filtered_data:
                filtered_data[key] = 0.0 if key != 'cash' else 100000.0
                
        return CapitalExposure(**filtered_data)
        
    def validate(self) -> bool:
        """Validate that all capital values are valid floats."""
        try:
            for key, value in asdict(self).items():
                if not isinstance(value, float):
                    return False
            return True
        except Exception:
            return False
            
    def total_exposure(self) -> float:
        """Calculate total capital exposure excluding cash."""
        data = self.as_dict()
        return sum(value for key, value in data.items() if key != 'cash')

@dataclass
class Variables:
    """Simulation variables dictionary."""
    data: Dict[str, float] = field(default_factory=dict)
    
    def as_dict(self) -> Dict[str, float]:
        """Convert variables to a dictionary."""
        return self.data.copy()
    
    def __getattr__(self, name):
        """Allow dot notation access to variables."""
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"Variable '{name}' not found")
        
    def __setattr__(self, name, value):
        """Allow dot notation assignment to variables."""
        if name == 'data':
            super().__setattr__(name, value)
        else:
            try:
                self.data[name] = float(value)
            except (ValueError, TypeError):
                self.data[name] = 0.0

@dataclass
class WorldState:
    """
    Core world state representing the full simulation state.
    
    Attributes:
        turn: Current simulation turn (0-indexed)
        sim_id: Unique simulation identifier
        overlays: Symbolic overlays (emotions)
        capital: Capital exposure across assets
        variables: Simulation variables 
        event_log: Record of events during simulation
        metadata: Additional metadata for the simulation
    """
    turn: int = 0
    sim_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    overlays: SymbolicOverlays = field(default_factory=SymbolicOverlays)
    capital: CapitalExposure = field(default_factory=CapitalExposure)
    variables: Variables = field(default_factory=Variables)
    event_log: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate initial state after creation."""
        # Ensure correct types for core components
        if not isinstance(self.overlays, SymbolicOverlays):
            if isinstance(self.overlays, dict):
                self.overlays = SymbolicOverlays.from_dict(self.overlays)
            else:
                self.overlays = SymbolicOverlays()
                
        if not isinstance(self.capital, CapitalExposure):
            if isinstance(self.capital, dict):
                self.capital = CapitalExposure.from_dict(self.capital)
            else:
                self.capital = CapitalExposure()
                
        if not isinstance(self.variables, Variables):
            if isinstance(self.variables, dict):
                self.variables = Variables(self.variables)
            else:
                self.variables = Variables()
                
        # Ensure lists and dicts are initialized
        if not isinstance(self.event_log, list):
            self.event_log = []
            
        if not isinstance(self.metadata, dict):
            self.metadata = {}
    
    def log_event(self, message: str) -> None:
        """Add an event to the simulation log."""
        if not isinstance(message, str):
            message = str(message)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.event_log.append(f"[{timestamp}][Turn {self.turn}] {message}")
    
    def advance_turn(self) -> int:
        """
        Advance simulation to next turn.
        
        Returns:
            int: New turn number
        """
        self.turn += 1
        self.log_event(f"Turn advanced to {self.turn}")
        return self.turn
    
    def snapshot(self) -> Dict[str, Any]:
        """
        Create a complete serializable snapshot of the current state.
        
        Returns:
            Dict containing all WorldState data
        """
        return {
            "turn": self.turn,
            "sim_id": self.sim_id,
            "timestamp": datetime.utcnow().isoformat(),
            "overlays": self.overlays.as_dict(),
            "capital": self.capital.as_dict(),
            "variables": self.variables.as_dict(),
            "event_count": len(self.event_log),
            "metadata": self.metadata.copy()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Return a dictionary representation of the WorldState (alias for snapshot).
        """
        return self.snapshot()
    
    def clone(self) -> 'WorldState':
        """
        Create a deep copy of this WorldState.
        
        Returns:
            WorldState: A new instance with copied data
        """
        return copy.deepcopy(self)
        
    def validate(self) -> List[str]:
        """
        Validate the world state for consistency and data integrity.
        
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        
        # Check overlays
        if not isinstance(self.overlays, SymbolicOverlays):
            errors.append("Overlays is not a SymbolicOverlays object")
        elif not self.overlays.validate():
            errors.append("Overlays failed validation")
            
        # Check capital
        if not isinstance(self.capital, CapitalExposure):
            errors.append("Capital is not a CapitalExposure object")
        elif not self.capital.validate():
            errors.append("Capital failed validation")
            
        # Check variables
        if not isinstance(self.variables, Variables):
            errors.append("Variables is not a Variables object")
            
        # Check turn
        if not isinstance(self.turn, int) or self.turn < 0:
            errors.append(f"Invalid turn: {self.turn}")
            
        # Check sim_id
        if not isinstance(self.sim_id, str) or not self.sim_id:
            errors.append(f"Invalid sim_id: {self.sim_id}")
            
        return errors
    
    def to_json(self) -> str:
        """
        Convert WorldState to JSON string.
        
        Returns:
            JSON string representation
        """
        data = {
            "turn": self.turn,
            "sim_id": self.sim_id,
            "overlays": self.overlays.as_dict(),
            "capital": self.capital.as_dict(),
            "variables": self.variables.as_dict(),
            "event_log": self.event_log,
            "metadata": self.metadata
        }
        return json.dumps(data, indent=2)
        
    @staticmethod
    def from_json(json_str: str) -> 'WorldState':
        """
        Create WorldState from JSON string.
        
        Args:
            json_str: JSON string representation of a WorldState
            
        Returns:
            New WorldState instance
            
        Raises:
            ValueError: If JSON is invalid or missing required fields
        """
        try:
            data = json.loads(json_str)
            
            # Create and validate components
            overlays = SymbolicOverlays.from_dict(data.get("overlays", {}))
            capital = CapitalExposure.from_dict(data.get("capital", {}))
            variables = Variables(data.get("variables", {}))
            
            # Create WorldState
            state = WorldState(
                turn=data.get("turn", 0),
                sim_id=data.get("sim_id", str(uuid.uuid4())),
                overlays=overlays,
                capital=capital,
                variables=variables,
                event_log=data.get("event_log", []),
                metadata=data.get("metadata", {})
            )
            
            return state
            
        except Exception as e:
            raise ValueError(f"Failed to parse WorldState from JSON: {e}")
