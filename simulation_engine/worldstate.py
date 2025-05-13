"""
worldstate.py

Core world state representation for the Pulse simulation.
Contains overlays, capital exposure, variables, turn counter,
and event log for the current simulation state.

This module provides functionality to create, validate, and serialize the world state,
as well as to manage symbolic overlays and capital exposure across different assets.
"""

import copy
import json
import uuid
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

@dataclass
class SymbolicOverlayMetadata:
    """Metadata for a symbolic overlay"""
    name: str
    category: str = "primary"  # primary or secondary
    parent: Optional[str] = None  # Parent overlay for hierarchical structure
    description: str = ""
    priority: float = 1.0  # Weighting priority

@dataclass
class SymbolicOverlays:
    """
    Symbolic overlays representing the emotional state of the simulation.
    
    Enhanced with:
    - Dynamic overlay discovery
    - Hierarchical primary/secondary structure
    - Metadata for each overlay
    - Relationship tracking between overlays
    """
    # Core default overlays (backwards compatible)
    hope: float = 0.5
    despair: float = 0.5
    rage: float = 0.5
    fatigue: float = 0.5
    trust: float = 0.5
    
    # Additional storage for dynamically discovered overlays
    _dynamic_overlays: Dict[str, float] = field(default_factory=dict)
    _metadata: Dict[str, SymbolicOverlayMetadata] = field(default_factory=dict)
    _relationships: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize metadata for core overlays"""
        # Initialize core overlay metadata if not already done
        if not self._metadata:
            self._metadata = {
                "hope": SymbolicOverlayMetadata(
                    name="hope", 
                    category="primary", 
                    description="Optimism about future outcomes"
                ),
                "despair": SymbolicOverlayMetadata(
                    name="despair", 
                    category="primary", 
                    description="Pessimism about future outcomes"
                ),
                "rage": SymbolicOverlayMetadata(
                    name="rage", 
                    category="primary", 
                    description="Intense negative reaction to events"
                ),
                "fatigue": SymbolicOverlayMetadata(
                    name="fatigue", 
                    category="primary", 
                    description="Diminished response to stimuli"
                ),
                "trust": SymbolicOverlayMetadata(
                    name="trust", 
                    category="primary", 
                    description="Confidence in system reliability"
                ),
            }
            
            # Initialize basic relationships
            self._relationships = {
                "hope": {"trust": 0.3, "despair": -0.5},
                "despair": {"hope": -0.5, "fatigue": 0.4},
                "rage": {"trust": -0.4},
                "fatigue": {"hope": -0.3},
                "trust": {}
            }
    
    def as_dict(self) -> Dict[str, float]:
        """Convert all overlay values to a dictionary."""
        result = {name: getattr(self, name) for name in ["hope", "despair", "rage", "fatigue", "trust"]}
        result.update(self._dynamic_overlays)
        return result

    def items(self):
        """Return all overlay items as (name, value) pairs."""
        return self.as_dict().items()
    
    def __getattr__(self, name):
        """Support dynamic overlay access via dot notation"""
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(f"Special attribute {name} not found")
            
        if name in self._dynamic_overlays:
            return self._dynamic_overlays[name]
            
        raise AttributeError(f"Overlay '{name}' not found")
    
    def __setattr__(self, name, value):
        """Support setting both core and dynamic overlays"""
        if name in {"_dynamic_overlays", "_metadata", "_relationships"}:
            super().__setattr__(name, value)
        elif name in {"hope", "despair", "rage", "fatigue", "trust"}:
            # Core overlays - use direct attribute
            super().__setattr__(name, max(0.0, min(1.0, float(value))))
        else:
            # Dynamic overlay - store in dict
            self._dynamic_overlays[name] = max(0.0, min(1.0, float(value)))
    
    @staticmethod
    def from_dict(data: Dict[str, float]) -> 'SymbolicOverlays':
        """Create overlays from a dictionary, with validation and dynamic overlay support."""
        # Create a new instance
        overlays = SymbolicOverlays()
        
        # Process all keys in the input data
        for k, v in data.items():
            try:
                v_float = max(0.0, min(1.0, float(v)))
                
                # Core overlay
                if k in {"hope", "despair", "rage", "fatigue", "trust"}:
                    setattr(overlays, k, v_float)
                # Dynamic overlay
                else:
                    overlays._dynamic_overlays[k] = v_float
            except (ValueError, TypeError):
                logger.warning(f"Invalid overlay value for '{k}': {v}. Skipping.")
        
        return overlays
    
    def validate(self) -> bool:
        """Validate that all overlay values are valid floats between 0 and 1."""
        try:
            # Check core overlays
            for key in ["hope", "despair", "rage", "fatigue", "trust"]:
                value = getattr(self, key)
                if not isinstance(value, float) or value < 0 or value > 1:
                    return False
                    
            # Check dynamic overlays
            for key, value in self._dynamic_overlays.items():
                if not isinstance(value, float) or value < 0 or value > 1:
                    return False
                    
            return True
        except Exception:
            return False
            
    def add_overlay(self, name: str, value: float = 0.5, category: str = "secondary", 
                   parent: Optional[str] = None, description: str = "", priority: float = 1.0):
        """
        Add a new dynamic overlay with metadata.
        
        Args:
            name: Name of the overlay
            value: Initial value (0.0-1.0)
            category: Category ("primary" or "secondary")
            parent: Parent overlay for hierarchical structure
            description: Description of the overlay
            priority: Priority weight
        """
        # Don't allow overriding core overlays
        if name in {"hope", "despair", "rage", "fatigue", "trust"}:
            logger.warning(f"Cannot create dynamic overlay with reserved name '{name}'")
            return False
            
        # Set the overlay value
        self._dynamic_overlays[name] = max(0.0, min(1.0, float(value)))
        
        # Store metadata
        self._metadata[name] = SymbolicOverlayMetadata(
            name=name,
            category=category,
            parent=parent,
            description=description,
            priority=priority
        )
        
        # Initialize empty relationships
        if name not in self._relationships:
            self._relationships[name] = {}
            
        return True
        
    def remove_overlay(self, name: str) -> bool:
        """
        Remove a dynamic overlay.
        
        Args:
            name: Name of the overlay to remove
            
        Returns:
            bool: True if removed, False if not found or is a core overlay
        """
        # Can't remove core overlays
        if name in {"hope", "despair", "rage", "fatigue", "trust"}:
            return False
            
        # Remove the overlay
        if name in self._dynamic_overlays:
            del self._dynamic_overlays[name]
            
            # Clean up metadata and relationships
            if name in self._metadata:
                del self._metadata[name]
                
            if name in self._relationships:
                del self._relationships[name]
                
            # Remove from other relationships
            for rel in self._relationships.values():
                if name in rel:
                    del rel[name]
                    
            return True
            
        return False
        
    def set_relationship(self, source: str, target: str, strength: float) -> bool:
        """
        Set relationship strength between two overlays.
        
        Args:
            source: Source overlay name
            target: Target overlay name
            strength: Relationship strength (-1.0 to 1.0)
            
        Returns:
            bool: True if successful, False if overlays don't exist
        """
        # Ensure both overlays exist
        if not self.has_overlay(source) or not self.has_overlay(target):
            return False
            
        # Initialize relationship dict if needed
        if source not in self._relationships:
            self._relationships[source] = {}
            
        # Set relationship strength
        self._relationships[source][target] = max(-1.0, min(1.0, float(strength)))
        return True
        
    def get_relationship(self, source: str, target: str) -> float:
        """
        Get relationship strength between two overlays.
        
        Args:
            source: Source overlay name
            target: Target overlay name
            
        Returns:
            float: Relationship strength or 0.0 if not defined
        """
        if source in self._relationships and target in self._relationships[source]:
            return self._relationships[source][target]
        return 0.0
        
    def get_primary_overlays(self) -> Dict[str, float]:
        """
        Get all primary category overlays.
        
        Returns:
            Dict mapping overlay names to values
        """
        result = {}
        
        # Add core primary overlays
        for name in ["hope", "despair", "rage", "fatigue", "trust"]:
            result[name] = getattr(self, name)
            
        # Add dynamic primary overlays
        for name, meta in self._metadata.items():
            if meta.category == "primary" and name in self._dynamic_overlays:
                result[name] = self._dynamic_overlays[name]
                
        return result
                
    def get_secondary_overlays(self) -> Dict[str, float]:
        """
        Get all secondary category overlays.
        
        Returns:
            Dict mapping overlay names to values
        """
        result = {}
        
        # Only dynamic overlays can be secondary
        for name, meta in self._metadata.items():
            if meta.category == "secondary" and name in self._dynamic_overlays:
                result[name] = self._dynamic_overlays[name]
                
        return result
                
    def get_children(self, parent_name: str) -> Dict[str, float]:
        """
        Get all child overlays of a parent.
        
        Args:
            parent_name: Name of parent overlay
            
        Returns:
            Dict mapping child overlay names to values
        """
        result = {}
        
        # First ensure parent exists
        if not self.has_overlay(parent_name):
            return result
            
        # Look for children among all overlays
        for name, meta in self._metadata.items():
            if meta.parent == parent_name:
                if name in ["hope", "despair", "rage", "fatigue", "trust"]:
                    result[name] = getattr(self, name)
                elif name in self._dynamic_overlays:
                    result[name] = self._dynamic_overlays[name]
                    
        return result
        
    def has_overlay(self, name: str) -> bool:
        """
        Check if an overlay exists.
        
        Args:
            name: Name of the overlay
            
        Returns:
            bool: True if the overlay exists
        """
        if name in ["hope", "despair", "rage", "fatigue", "trust"]:
            return True
        return name in self._dynamic_overlays
        
    def get_overlay_metadata(self, name: str) -> Optional[SymbolicOverlayMetadata]:
        """
        Get metadata for an overlay.
        
        Args:
            name: Name of the overlay
            
        Returns:
            SymbolicOverlayMetadata or None if not found
        """
        return self._metadata.get(name)
        
    def get_dominant_overlays(self, threshold: float = 0.65) -> Dict[str, float]:
        """
        Get all overlays with values above the threshold.
        
        Args:
            threshold: Minimum value to be considered dominant
            
        Returns:
            Dict of dominant overlays
        """
        result = {}
        
        # Check core overlays
        for name in ["hope", "despair", "rage", "fatigue", "trust"]:
            value = getattr(self, name)
            if value >= threshold:
                result[name] = value
                
        # Check dynamic overlays
        for name, value in self._dynamic_overlays.items():
            if value >= threshold:
                result[name] = value
                
        return result

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
                    logger.warning(f"Invalid capital value for '{k}': {v}. Using default 0.0")
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
        """Allow dot notation access to variables, but avoid recursion for magic attributes."""
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(f"Special attribute {name} not found")
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"Variable '{name}' not found")

    def get(self, key, default=None):
        """Dictionary-like get method with default value fallback."""
        return self.data.get(key, default)
        
    def __setattr__(self, name, value):
        """Allow dot notation assignment to variables."""
        if name == 'data':
            super().__setattr__(name, value)
        else:
            try:
                self.data[name] = float(value)
            except (ValueError, TypeError):
                logger.warning(f"Invalid variable value for '{name}': {value}. Using default 0.0")
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
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
            
            # Create and validate components, ensuring dicts even if fields are null
            overlays_data = data.get("overlays") or {}
            overlays = SymbolicOverlays.from_dict(overlays_data)

            capital_data = data.get("capital") or {}
            capital = CapitalExposure.from_dict(capital_data)

            variables_data = data.get("variables") or {}
            variables = Variables(variables_data)
            
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
